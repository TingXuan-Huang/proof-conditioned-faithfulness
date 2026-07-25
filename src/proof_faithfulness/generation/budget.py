"""Fail-closed approval verification and atomic paid-spend reservation."""

from __future__ import annotations

import json
import os
import socket
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from proof_faithfulness.artifacts import RunArtifactStore, sha256_bytes, sha256_file
from proof_faithfulness.generation.locks import exclusive_file_guard
from proof_faithfulness.generation.scheduler import slurm_job_is_active
from proof_faithfulness.schema import Hash, NonEmptyString, SchemaVersion

_LEDGER_PATH = "budget.json"
_GLOBAL_LOCK_NAME = ".PAID_BUDGET_LOCK"
_ABSOLUTE_AGGREGATE_CEILING_USD = Decimal(500)


class ApprovalError(RuntimeError):
    """Base class for machine-readable approval failures."""


class MissingApprovalError(ApprovalError):
    """Raised before transport when no matching human approval exists."""


class AmbiguousApprovalError(ApprovalError):
    """Raised when multiple approval records authorize the same run and scope."""


class BudgetAccountingError(ApprovalError):
    """Raised when a budget ledger is missing, corrupt, or inconsistent."""


class BudgetExceededError(ApprovalError):
    """Raised before transport when a run or aggregate ceiling would be exceeded."""


class BudgetContract(BaseModel):
    """Immutable base for approval, permit, and ledger records."""

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", frozen=True)


class ApprovalRecord(BudgetContract):
    """Human-owned authorization record in ``approvals/``."""

    scope: NonEmptyString
    run_ids: tuple[NonEmptyString, ...]
    requests_sha256: Hash
    request_count: int = Field(gt=0)
    max_usd: Decimal = Field(gt=0)
    approved_by: NonEmptyString
    date: date
    note: NonEmptyString

    @model_validator(mode="after")
    def validate_run_ids(self) -> ApprovalRecord:
        if len(self.run_ids) != 1:
            raise ValueError("Each approval must bind exactly one run_id and request manifest")
        return self


class PaidRequestPermit(BudgetContract):
    """Non-secret proof that one paid request has reserved budget."""

    schema_version: Literal["1.0"] = "1.0"
    run_id: NonEmptyString
    request_id: Hash
    inference_fingerprint: Hash
    scope: NonEmptyString
    approval_path: NonEmptyString
    approval_sha256: Hash
    requests_sha256: Hash
    request_count: int = Field(gt=0)
    reserved_usd: Decimal = Field(gt=0)
    issued_at: datetime


class BudgetEntry(BudgetContract):
    """One request reservation, optionally settled to provider-reported spend."""

    request_id: Hash
    inference_fingerprint: Hash
    reserved_usd: Decimal = Field(gt=0)
    spent_usd: Decimal | None = Field(default=None, ge=0)

    @property
    def committed_usd(self) -> Decimal:
        return self.reserved_usd if self.spent_usd is None else self.spent_usd


class BudgetLedger(BudgetContract):
    """Checksummed per-run spend ledger used for aggregate accounting."""

    schema_version: SchemaVersion
    run_id: NonEmptyString
    scope: NonEmptyString
    approval_path: NonEmptyString
    approval_sha256: Hash
    requests_sha256: Hash
    request_count: int = Field(gt=0)
    max_usd: Decimal = Field(gt=0)
    entries: tuple[BudgetEntry, ...] = ()

    @model_validator(mode="after")
    def reject_duplicate_requests(self) -> BudgetLedger:
        request_ids = tuple(entry.request_id for entry in self.entries)
        if len(set(request_ids)) != len(request_ids):
            raise ValueError("Budget ledger request IDs must be unique")
        return self

    @property
    def committed_usd(self) -> Decimal:
        return sum((entry.committed_usd for entry in self.entries), start=Decimal(0))


@dataclass(frozen=True)
class _PlanIdentity:
    sha256: str
    request_count: int
    paid_requests: dict[str, _PlannedPaidRequest]


@dataclass(frozen=True)
class _PlannedPaidRequest:
    max_cost_usd: Decimal
    inference_fingerprint: str


class BudgetGate:
    """Issues permits only after an atomic approval and ceiling check."""

    def __init__(
        self,
        *,
        store: RunArtifactStore,
        approvals_root: Path,
        scope: str,
        aggregate_ceiling_usd: Decimal | str = Decimal(500),
        lock_timeout_s: float = 5.0,
        stale_after_s: float = 600.0,
        job_is_active: Callable[[str], bool] | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        aggregate_ceiling = _money(aggregate_ceiling_usd)
        if aggregate_ceiling <= 0:
            raise ValueError("aggregate_ceiling_usd must be positive")
        if aggregate_ceiling > _ABSOLUTE_AGGREGATE_CEILING_USD:
            raise ValueError("aggregate_ceiling_usd cannot exceed the absolute $500 ceiling")
        if lock_timeout_s <= 0:
            raise ValueError("lock_timeout_s must be positive")
        if stale_after_s < 600:
            raise ValueError("Budget locks require a stale threshold of at least 600 seconds")
        self._store = store
        self._approvals_root = approvals_root
        self._scope = scope
        self._aggregate_ceiling_usd = aggregate_ceiling
        self._lock_timeout_s = lock_timeout_s
        self._stale_after_s = stale_after_s
        self._job_is_active = job_is_active or slurm_job_is_active
        self._now = now or (lambda: datetime.now(UTC))

    def reserve(
        self,
        *,
        request_id: str,
        max_cost_usd: Decimal | str,
    ) -> PaidRequestPermit:
        """Atomically reserves one request's worst-case cost and returns a permit."""
        requested = _money(max_cost_usd)
        if requested <= 0:
            raise ValueError("A paid request requires a positive max_cost_usd")
        with self._global_lock():
            plan = self._load_plan_identity()
            planned = plan.paid_requests.get(request_id)
            if planned is None:
                raise BudgetAccountingError("Paid request is absent from the approved manifest")
            if planned.max_cost_usd != requested:
                raise BudgetAccountingError("Paid request reservation differs from its manifest")
            approval, approval_path, approval_sha256 = self._matching_approval()
            ledger = self._load_or_create_ledger(
                approval=approval,
                approval_path=approval_path,
                approval_sha256=approval_sha256,
                plan=plan,
            )
            self._reject_cross_run_reservation(
                request_id=request_id,
                inference_fingerprint=planned.inference_fingerprint,
            )
            existing = _find_entry(ledger, request_id)
            if existing is not None:
                if existing.spent_usd is not None:
                    raise BudgetAccountingError(f"Paid request is already settled: {request_id}")
                if existing.reserved_usd != requested:
                    raise BudgetAccountingError(f"Paid request reservation changed: {request_id}")
                return self._permit(ledger=ledger, entry=existing)
            if any(
                entry.inference_fingerprint == planned.inference_fingerprint
                for entry in ledger.entries
            ):
                raise BudgetAccountingError(
                    "Paid inference is already reserved in this run under another request_id"
                )

            if ledger.committed_usd >= ledger.max_usd:
                raise BudgetExceededError("Run approval ceiling has already been reached")
            if ledger.committed_usd + requested > ledger.max_usd:
                raise BudgetExceededError("Request would exceed the run approval ceiling")
            aggregate_committed = self._aggregate_committed_usd()
            if aggregate_committed >= self._aggregate_ceiling_usd:
                raise BudgetExceededError("Aggregate paid-request ceiling has already been reached")
            if aggregate_committed + requested > self._aggregate_ceiling_usd:
                raise BudgetExceededError("Request would exceed the aggregate paid-request ceiling")

            entry = BudgetEntry(
                request_id=request_id,
                inference_fingerprint=planned.inference_fingerprint,
                reserved_usd=requested,
            )
            ledger = ledger.model_copy(update={"entries": (*ledger.entries, entry)})
            self._write_ledger(ledger)
            return self._permit(ledger=ledger, entry=entry)

    def verify(self, permit: PaidRequestPermit) -> None:
        """Revalidates a permit immediately before every transport attempt."""
        with self._global_lock():
            self._verify_unlocked(permit)

    def settle(
        self,
        permit: PaidRequestPermit,
        *,
        actual_usd: Decimal | str,
    ) -> None:
        """Records provider-reported spend, including any over-reservation violation."""
        actual = _money(actual_usd)
        if actual < 0:
            raise ValueError("actual_usd cannot be negative")
        with self._global_lock():
            ledger, entry = self._verify_unlocked(permit, allow_settled=True)
            if entry.spent_usd is not None:
                if entry.spent_usd != actual:
                    raise BudgetAccountingError(
                        f"Settled spend changed for request: {permit.request_id}"
                    )
                _raise_if_overspent(entry)
                return
            replacement = entry.model_copy(update={"spent_usd": actual})
            entries = tuple(
                replacement if item.request_id == permit.request_id else item
                for item in ledger.entries
            )
            self._write_ledger(ledger.model_copy(update={"entries": entries}))
            _raise_if_overspent(replacement)

    def reconcile_terminal(
        self,
        *,
        request_id: str,
        actual_usd: Decimal | str,
    ) -> None:
        """Settles a response persisted just before a process interruption."""
        actual = _money(actual_usd)
        if actual < 0:
            raise ValueError("actual_usd cannot be negative")
        with self._global_lock():
            approval, approval_path, approval_sha256 = self._matching_approval()
            ledger = self._load_or_create_ledger(
                approval=approval,
                approval_path=approval_path,
                approval_sha256=approval_sha256,
                plan=self._load_plan_identity(),
            )
            entry = _find_entry(ledger, request_id)
            if entry is None:
                raise BudgetAccountingError(
                    f"Paid terminal response has no prior reservation: {request_id}"
                )
            if entry.spent_usd is not None:
                if entry.spent_usd != actual:
                    raise BudgetAccountingError(
                        f"Terminal spend differs from its ledger: {request_id}"
                    )
                _raise_if_overspent(entry)
                return
            replacement = entry.model_copy(update={"spent_usd": actual})
            entries = tuple(
                replacement if item.request_id == request_id else item for item in ledger.entries
            )
            self._write_ledger(ledger.model_copy(update={"entries": entries}))
            _raise_if_overspent(replacement)

    def _matching_approval(self) -> tuple[ApprovalRecord, Path, str]:
        root = self._approvals_root
        if not root.is_dir() or root.is_symlink():
            raise MissingApprovalError("No approvals directory is available")
        matches: list[tuple[ApprovalRecord, Path, str]] = []
        for path in sorted(root.glob("*.json")):
            if path.is_symlink() or not path.is_file():
                raise ApprovalError(f"Approval path must be a regular file: {path.name}")
            content = path.read_bytes()
            try:
                approval = ApprovalRecord.model_validate_json(content)
            except ValidationError as error:
                raise ApprovalError(f"Invalid machine-readable approval: {path.name}") from error
            if approval.scope == self._scope and self._store.run_id in approval.run_ids:
                matches.append((approval, path, sha256_bytes(content)))
        if not matches:
            raise MissingApprovalError(
                f"No approval matches run_id={self._store.run_id!r}, scope={self._scope!r}"
            )
        if len(matches) != 1:
            raise AmbiguousApprovalError(
                f"Multiple approvals match run_id={self._store.run_id!r}, scope={self._scope!r}"
            )
        return matches[0]

    def _load_or_create_ledger(
        self,
        *,
        approval: ApprovalRecord,
        approval_path: Path,
        approval_sha256: str,
        plan: _PlanIdentity,
    ) -> BudgetLedger:
        if approval.requests_sha256 != plan.sha256 or approval.request_count != plan.request_count:
            raise BudgetAccountingError("Approval does not match the finalized request manifest")
        label = f"{self._approvals_root.name}/{approval_path.name}"
        ledger = self._load_ledger()
        if ledger is None:
            return BudgetLedger(
                schema_version="1.0",
                run_id=self._store.run_id,
                scope=self._scope,
                approval_path=label,
                approval_sha256=approval_sha256,
                requests_sha256=plan.sha256,
                request_count=plan.request_count,
                max_usd=approval.max_usd,
            )
        expected = (
            self._store.run_id,
            self._scope,
            label,
            approval_sha256,
            plan.sha256,
            plan.request_count,
            approval.max_usd,
        )
        actual = (
            ledger.run_id,
            ledger.scope,
            ledger.approval_path,
            ledger.approval_sha256,
            ledger.requests_sha256,
            ledger.request_count,
            ledger.max_usd,
        )
        if actual != expected:
            raise BudgetAccountingError("Approval identity changed after budget use")
        return ledger

    def _load_ledger(self) -> BudgetLedger | None:
        path = self._store.path / _LEDGER_PATH
        if not path.exists():
            return None
        if not self._store.verified(_LEDGER_PATH):
            raise BudgetAccountingError(f"Budget ledger is unverified: {self._store.run_id}")
        try:
            return BudgetLedger.model_validate_json(path.read_bytes())
        except (OSError, ValidationError) as error:
            raise BudgetAccountingError(
                f"Budget ledger is invalid: {self._store.run_id}"
            ) from error

    def _write_ledger(self, ledger: BudgetLedger) -> None:
        self._store.write_json(_LEDGER_PATH, ledger.model_dump(mode="json"))
        if not self._store.verified(_LEDGER_PATH):
            raise BudgetAccountingError("Budget ledger failed checksum verification")

    def _load_plan_identity(self) -> _PlanIdentity:
        relative_path = "requests.jsonl"
        path = self._store.path / relative_path
        if not self._store.verified(relative_path):
            raise BudgetAccountingError("Paid work requires a finalized verified request manifest")
        paid_requests: dict[str, _PlannedPaidRequest] = {}
        paid_fingerprints: set[str] = set()
        seen_request_ids: set[str] = set()
        request_count = 0
        try:
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if not line:
                    raise BudgetAccountingError(
                        f"Request manifest contains a blank line: {line_number}"
                    )
                payload = json.loads(line)
                request_id = payload["model_input"]["request"]["request_id"]
                paid = payload["paid"]
                max_cost_usd = payload["max_cost_usd"]
                if not isinstance(request_id, str):
                    raise TypeError("request_id must be a string")
                if request_id in seen_request_ids:
                    raise BudgetAccountingError("Request manifest contains duplicate IDs")
                seen_request_ids.add(request_id)
                if paid is True:
                    planned_cost = _money(max_cost_usd)
                    if planned_cost <= 0:
                        raise BudgetAccountingError(
                            "Paid request manifest contains a nonpositive reservation"
                        )
                    fingerprint = _inference_fingerprint(payload)
                    if fingerprint in paid_fingerprints:
                        raise BudgetAccountingError(
                            "Request manifest contains a duplicate paid inference"
                        )
                    paid_fingerprints.add(fingerprint)
                    paid_requests[request_id] = _PlannedPaidRequest(
                        max_cost_usd=planned_cost,
                        inference_fingerprint=fingerprint,
                    )
                elif paid is not False:
                    raise TypeError("paid must be a boolean")
                request_count += 1
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as error:
            raise BudgetAccountingError("Request manifest cannot authorize paid work") from error
        if request_count == 0:
            raise BudgetAccountingError("Request manifest cannot be empty")
        return _PlanIdentity(
            sha256=sha256_file(path),
            request_count=request_count,
            paid_requests=paid_requests,
        )

    def _aggregate_committed_usd(self) -> Decimal:
        return sum(
            (ledger.committed_usd for _, ledger in self._aggregate_ledgers()),
            start=Decimal(0),
        )

    def _reject_cross_run_reservation(
        self,
        *,
        request_id: str,
        inference_fingerprint: str,
    ) -> None:
        for _, ledger in self._aggregate_ledgers():
            if ledger.run_id == self._store.run_id:
                continue
            duplicate = next(
                (
                    entry
                    for entry in ledger.entries
                    if entry.request_id == request_id
                    or entry.inference_fingerprint == inference_fingerprint
                ),
                None,
            )
            if duplicate is not None:
                raise BudgetAccountingError(
                    "Paid inference is already reserved by run "
                    f"{ledger.run_id}: {duplicate.request_id}"
                )

    def _aggregate_ledgers(self) -> tuple[tuple[Path, BudgetLedger], ...]:
        runs_root = self._store.outputs_root / "runs"
        if not runs_root.is_dir():
            return ()
        ledgers: list[tuple[Path, BudgetLedger]] = []
        for path in sorted(runs_root.glob(f"*/{_LEDGER_PATH}")):
            checksum_path = path.with_name(f"{path.name}.sha256")
            if path.parent.is_symlink() or path.is_symlink() or checksum_path.is_symlink():
                raise BudgetAccountingError(f"Aggregate ledger path is unsafe: {path}")
            try:
                recorded = checksum_path.read_text(encoding="ascii").strip()
            except (OSError, UnicodeDecodeError) as error:
                raise BudgetAccountingError(
                    f"Aggregate ledger has no valid checksum: {path}"
                ) from error
            if len(recorded) != 64 or sha256_file(path) != recorded:
                raise BudgetAccountingError(f"Aggregate ledger checksum failed: {path}")
            try:
                ledger = BudgetLedger.model_validate_json(path.read_bytes())
            except (OSError, ValidationError) as error:
                raise BudgetAccountingError(f"Aggregate ledger is invalid: {path}") from error
            if ledger.run_id != path.parent.name:
                raise BudgetAccountingError(f"Aggregate ledger run_id mismatches its path: {path}")
            ledgers.append((path, ledger))
        return tuple(ledgers)

    def _permit(self, *, ledger: BudgetLedger, entry: BudgetEntry) -> PaidRequestPermit:
        return PaidRequestPermit(
            run_id=ledger.run_id,
            request_id=entry.request_id,
            inference_fingerprint=entry.inference_fingerprint,
            scope=ledger.scope,
            approval_path=ledger.approval_path,
            approval_sha256=ledger.approval_sha256,
            requests_sha256=ledger.requests_sha256,
            request_count=ledger.request_count,
            reserved_usd=entry.reserved_usd,
            issued_at=self._now(),
        )

    def _verify_unlocked(
        self,
        permit: PaidRequestPermit,
        *,
        allow_settled: bool = False,
    ) -> tuple[BudgetLedger, BudgetEntry]:
        approval, approval_path, approval_sha256 = self._matching_approval()
        ledger = self._load_or_create_ledger(
            approval=approval,
            approval_path=approval_path,
            approval_sha256=approval_sha256,
            plan=self._load_plan_identity(),
        )
        expected_permit = (
            ledger.run_id,
            ledger.scope,
            ledger.approval_path,
            ledger.approval_sha256,
            ledger.requests_sha256,
            ledger.request_count,
        )
        actual_permit = (
            permit.run_id,
            permit.scope,
            permit.approval_path,
            permit.approval_sha256,
            permit.requests_sha256,
            permit.request_count,
        )
        if actual_permit != expected_permit:
            raise BudgetAccountingError("Paid request permit does not match its ledger")
        entry = _find_entry(ledger, permit.request_id)
        if entry is None or entry.reserved_usd != permit.reserved_usd:
            raise BudgetAccountingError("Paid request permit has no matching reservation")
        if entry.inference_fingerprint != permit.inference_fingerprint:
            raise BudgetAccountingError("Paid request permit fingerprint does not match")
        if entry.spent_usd is not None and not allow_settled:
            raise BudgetAccountingError("Paid request permit was already settled")
        return ledger, entry

    @contextmanager
    def _global_lock(self) -> Iterator[None]:
        guard = self._store.outputs_root / ".PAID_BUDGET_LOCK.guard"
        try:
            with (
                exclusive_file_guard(guard, timeout_s=self._lock_timeout_s),
                self._global_lock_claim(),
            ):
                yield
        except TimeoutError as error:
            raise BudgetAccountingError("Timed out acquiring the global budget guard") from error

    @contextmanager
    def _global_lock_claim(self) -> Iterator[None]:
        path = self._store.outputs_root / _GLOBAL_LOCK_NAME
        path.parent.mkdir(parents=True, exist_ok=True)
        token = uuid.uuid4().hex
        deadline = time.monotonic() + self._lock_timeout_s
        while True:
            try:
                descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError as error:
                if _breakable_budget_lock(
                    path,
                    stale_after_s=self._stale_after_s,
                    job_is_active=self._job_is_active,
                    now=self._now(),
                ):
                    path.unlink(missing_ok=True)
                    continue
                if time.monotonic() >= deadline:
                    raise BudgetAccountingError(
                        "Timed out acquiring the global budget lock"
                    ) from error
                time.sleep(0.01)
                continue
            record = json.dumps(
                {
                    "hostname": socket.gethostname(),
                    "pid": os.getpid(),
                    "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
                    "heartbeat_at": self._now().isoformat(),
                    "token": token,
                },
                ensure_ascii=True,
                sort_keys=True,
            ).encode("ascii")
            try:
                os.write(descriptor, record)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            break
        try:
            yield
        finally:
            try:
                owner = json.loads(path.read_text(encoding="ascii"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                owner = None
            if isinstance(owner, dict) and owner.get("token") == token:
                path.unlink(missing_ok=True)


def _find_entry(ledger: BudgetLedger, request_id: str) -> BudgetEntry | None:
    return next((entry for entry in ledger.entries if entry.request_id == request_id), None)


def _inference_fingerprint(payload: object) -> str:
    if not isinstance(payload, dict):
        raise TypeError("request manifest line must be an object")
    model_input = payload.get("model_input")
    if not isinstance(model_input, dict):
        raise TypeError("model_input must be an object")
    request = model_input.get("request")
    if not isinstance(request, dict):
        raise TypeError("request must be an object")
    inference_request = dict(request)
    inference_request.pop("request_id", None)
    inference_request.pop("backend_config_hash", None)
    fingerprint_input = {
        **model_input,
        "request": inference_request,
    }
    content = json.dumps(
        fingerprint_input,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256_bytes(content)


def _breakable_budget_lock(
    path: Path,
    *,
    stale_after_s: float,
    job_is_active: Callable[[str], bool] | None,
    now: datetime,
) -> bool:
    if path.is_symlink():
        raise BudgetAccountingError(f"Budget lock must not be a symlink: {path}")
    try:
        owner = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        try:
            return now.timestamp() - path.stat().st_mtime >= stale_after_s
        except OSError:
            return False
    if not isinstance(owner, dict):
        return False
    heartbeat = owner.get("heartbeat_at")
    if not isinstance(heartbeat, str):
        return False
    try:
        age_s = (now - datetime.fromisoformat(heartbeat)).total_seconds()
    except ValueError:
        return False
    if age_s < stale_after_s:
        return False
    hostname = owner.get("hostname")
    pid = owner.get("pid")
    if hostname == socket.gethostname() and isinstance(pid, int) and pid > 0:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            pass
        except PermissionError:
            return False
        else:
            return False
        return True
    job_id = owner.get("slurm_job_id")
    if isinstance(job_id, str):
        return job_is_active is not None and not job_is_active(job_id)
    return hostname == socket.gethostname()


def _money(value: Decimal | str) -> Decimal:
    try:
        money = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"Invalid USD amount: {value!r}") from error
    if not money.is_finite():
        raise ValueError("USD amounts must be finite")
    return money


def _raise_if_overspent(entry: BudgetEntry) -> None:
    if entry.spent_usd is not None and entry.spent_usd > entry.reserved_usd:
        raise BudgetAccountingError(f"Provider spend exceeded its reservation: {entry.request_id}")
