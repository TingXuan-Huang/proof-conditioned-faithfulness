"""Crash-resumable generation execution with retries, locks, and budgets."""

from __future__ import annotations

import json
import os
import random
import signal
import socket
import subprocess
import sys
import threading
import time
import uuid
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Protocol, Self, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from proof_faithfulness.artifacts import (
    FrozenRunError,
    RunArtifactStore,
    atomic_write_bytes,
    sha256_bytes,
    sha256_file,
)
from proof_faithfulness.generation.artifacts import (
    ResponseArtifactError,
    load_verified_response,
    response_relative_path,
    write_generation_response,
    write_response_failure,
)
from proof_faithfulness.generation.budget import (
    ApprovalError,
    BudgetExceededError,
    BudgetGate,
    PaidRequestPermit,
)
from proof_faithfulness.generation.locks import exclusive_file_guard
from proof_faithfulness.generation.planning import (
    PlannedGeneration,
    serialize_generation_requests,
)
from proof_faithfulness.generation.scheduler import slurm_job_is_active
from proof_faithfulness.models import AdapterError, AdapterResult, ModelAdapter, ModelInput
from proof_faithfulness.models.base import (
    AdapterResponseError,
    AdapterTransportError,
    MissingSecretError,
)
from proof_faithfulness.schema import (
    GenerationResponse,
    GitCommit,
    Hash,
    NonEmptyString,
    SchemaVersion,
)

RunStatus = Literal[
    "planned",
    "approved",
    "submitted",
    "running",
    "complete",
    "failed",
    "cancelled",
]

GIT_IDENTITY_TIMEOUT_SECONDS = 60


class HarnessError(RuntimeError):
    """Base class for generation harness failures."""


class WorkerLockError(HarnessError):
    """Raised when another live worker owns a run."""


class RunStateError(HarnessError):
    """Raised when persistent state is corrupt or a transition is illegal."""


class AdapterPermitError(HarnessError):
    """Raised when a paid adapter lacks the permit-aware entrypoint."""


class AmbiguousPaidAttemptError(AdapterPermitError):
    """Raised when retrying could duplicate a provider-accepted paid request."""


class _GracefulStop(HarnessError):
    """Internal control flow for a stop requested between transport attempts."""

    def __init__(self, retries: int) -> None:
        super().__init__("Generation stop requested")
        self.retries = retries


class HarnessContract(BaseModel):
    """Immutable base for persistent harness records."""

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", frozen=True)


class RunOwner(HarnessContract):
    """Worker identity recorded in run state and locks."""

    host: NonEmptyString
    pid: int = Field(gt=0)
    slurm_job_id: str | None = None
    started_at: datetime


class StateTransition(HarnessContract):
    """One append-only run-state transition."""

    state: RunStatus
    ts: datetime
    reason: NonEmptyString
    slurm_job_id: str | None = None


class PersistentRunState(HarnessContract):
    """Checksummed state machine for one generation run."""

    schema_version: SchemaVersion
    run_id: NonEmptyString
    state: RunStatus
    slurm_job_id: str | None
    owner: RunOwner | None
    approval: str | None
    updated_at: datetime
    history: tuple[StateTransition, ...]

    @model_validator(mode="after")
    def validate_history(self) -> PersistentRunState:
        if not self.history or self.history[-1].state != self.state:
            raise ValueError("Run-state history must end at the current state")
        for previous, current in zip(self.history, self.history[1:], strict=False):
            if current.ts < previous.ts:
                raise ValueError("Run-state history timestamps must be ordered")
        return self


class RetryPolicy(HarnessContract):
    """Bounded transport-only retry schedule."""

    max_attempts: int = Field(default=3, gt=0)
    base_delay_s: float = Field(default=0.25, ge=0)
    max_delay_s: float = Field(default=4.0, ge=0)
    jitter_fraction: float = Field(default=0.1, ge=0, le=1)

    @model_validator(mode="after")
    def validate_delays(self) -> RetryPolicy:
        if self.max_delay_s < self.base_delay_s:
            raise ValueError("max_delay_s cannot be less than base_delay_s")
        return self

    def delay_after(self, attempt: int) -> float:
        """Returns backoff after a failed one-indexed attempt."""
        delay = min(self.max_delay_s, self.base_delay_s * (2 ** (attempt - 1)))
        jitter = random.uniform(0, delay * self.jitter_fraction)
        return delay + jitter


class HarnessResult(HarnessContract):
    """Summary of one generation invocation, including resume skips."""

    processed: int = Field(ge=0)
    skipped: int = Field(ge=0)
    retries: int = Field(ge=0)
    state: RunStatus


class HarnessEnvironment(HarnessContract):
    """Run-level producer identity that must remain exact across resumes."""

    schema_version: Literal["1.0"] = "1.0"
    harness_git_commit: GitCommit
    python_version: NonEmptyString
    uv_lock_sha256: Hash
    git_identity_source: Literal["repository", "explicit"]
    worktree_dirty: bool | None
    worktree_status_sha256: Hash | None


class PaidRetryDecision(HarnessContract):
    """Provider-aware classification of one paid transport failure."""

    safe_to_retry: bool
    reason: NonEmptyString
    retry_after_s: float | None = Field(default=None, ge=0)


class TransportAttemptRecord(HarnessContract):
    """Durable state for one adapter transport attempt."""

    attempt: int = Field(gt=0)
    started_at: datetime
    finished_at: datetime | None = None
    outcome: Literal["started", "success", "transport_error", "response_error"]
    paid: bool
    retry_safe: bool = False
    detail: str | None = None

    @model_validator(mode="after")
    def validate_attempt_state(self) -> TransportAttemptRecord:
        if self.outcome == "started" and self.finished_at is not None:
            raise ValueError("A started attempt cannot already be finished")
        if self.outcome != "started" and self.finished_at is None:
            raise ValueError("A terminal attempt requires finished_at")
        if self.finished_at is not None and self.finished_at < self.started_at:
            raise ValueError("Transport attempt cannot finish before it starts")
        if self.retry_safe and self.outcome != "transport_error":
            raise ValueError("Only a transport error can be marked retry-safe")
        return self


class TransportAttemptLedger(HarnessContract):
    """Checksummed attempt history used to make paid retries fail closed."""

    schema_version: Literal["1.0"] = "1.0"
    request_id: Hash
    attempts: tuple[TransportAttemptRecord, ...] = ()

    @model_validator(mode="after")
    def validate_attempt_sequence(self) -> TransportAttemptLedger:
        expected = tuple(range(1, len(self.attempts) + 1))
        actual = tuple(attempt.attempt for attempt in self.attempts)
        if actual != expected:
            raise ValueError("Transport attempt numbers must be contiguous")
        return self


@runtime_checkable
class PaidModelAdapter(Protocol):
    """Adapter entrypoint that cannot be called without a typed budget permit."""

    def generate_paid(
        self,
        model_input: ModelInput,
        permit: PaidRequestPermit,
    ) -> AdapterResult: ...


@runtime_checkable
class PreflightModelAdapter(Protocol):
    """Adapter with a side-effect-free validation step before transport."""

    def preflight(self, model_input: ModelInput) -> None: ...


class EventLog:
    """Append-only, proof-free structured event log."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def append(
        self,
        event: str,
        *,
        request_id: str | None = None,
        detail: Mapping[str, object] | None = None,
    ) -> None:
        """Appends and fsyncs one canonical JSON event."""
        record: dict[str, object] = {
            "ts": datetime.now(UTC).isoformat(),
            "event": event,
            "detail": dict(detail or {}),
        }
        if request_id is not None:
            record["request_id"] = request_id
        content = (
            json.dumps(
                record,
                allow_nan=False,
                ensure_ascii=True,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
            + b"\n"
        )
        self._path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self._path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
        try:
            os.write(descriptor, content)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def terminal_request_ids(self) -> set[str]:
        """Returns request IDs with a durable request_end event."""
        if not self._path.exists():
            return set()
        try:
            lines = self._path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as error:
            raise RunStateError("Event log is unreadable") from error
        terminal: set[str] = set()
        for line_number, line in enumerate(lines, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise RunStateError(f"Event log line is invalid: {line_number}") from error
            if not isinstance(record, dict):
                raise RunStateError(f"Event log line is not an object: {line_number}")
            if record.get("event") == "request_end":
                request_id = record.get("request_id")
                if not isinstance(request_id, str):
                    raise RunStateError(f"request_end event has no request_id: {line_number}")
                if request_id in terminal:
                    raise RunStateError(f"Duplicate request_end event: {request_id}")
                terminal.add(request_id)
        return terminal


class WorkerLock:
    """Atomic one-worker claim with a refreshed heartbeat."""

    def __init__(
        self,
        *,
        path: Path,
        events: EventLog,
        heartbeat_interval_s: float = 60.0,
        stale_after_s: float = 600.0,
        job_is_active: Callable[[str], bool] | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        if heartbeat_interval_s <= 0:
            raise ValueError("heartbeat_interval_s must be positive")
        if stale_after_s < 600:
            raise ValueError("Worker locks require a stale threshold of at least 600 seconds")
        self._path = path
        self._events = events
        self._heartbeat_interval_s = heartbeat_interval_s
        self._stale_after_s = stale_after_s
        self._job_is_active = job_is_active or slurm_job_is_active
        self._now = now or (lambda: datetime.now(UTC))
        self._token = uuid.uuid4().hex
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self) -> Self:
        self.acquire()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        del exc_type, exc_value, traceback
        self.release()

    def acquire(self) -> None:
        """Claims the run or breaks only a demonstrably dead claim."""
        guard = self._path.with_name(f"{self._path.name}.guard")
        try:
            with exclusive_file_guard(guard, timeout_s=5):
                self._acquire_guarded()
        except TimeoutError as error:
            raise WorkerLockError("Timed out serializing stale worker-lock recovery") from error
        self._events.append("lock_acquired", detail={"pid": os.getpid()})
        self._thread = threading.Thread(
            target=self._heartbeat_loop,
            name="generation-worker-heartbeat",
            daemon=True,
        )
        self._thread.start()

    def _acquire_guarded(self) -> None:
        if self._path.is_symlink():
            raise WorkerLockError(f"Worker lock must not be a symlink: {self._path}")
        try:
            descriptor = os.open(
                self._path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
        except FileExistsError as error:
            try:
                old_owner = self._read_owner()
            except WorkerLockError:
                if not self._unreadable_lock_is_stale():
                    raise
                old_owner = {}
            if old_owner and not self._can_break(old_owner):
                raise WorkerLockError(
                    f"A live worker already owns run: {self._path.parent}"
                ) from error
            self._path.unlink()
            self._events.append("lock_broken", detail={"prior_pid": old_owner.get("pid")})
            descriptor = os.open(
                self._path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
        try:
            content = self._record_bytes()
            os.write(descriptor, content)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def _unreadable_lock_is_stale(self) -> bool:
        try:
            age_s = self._now().timestamp() - self._path.stat().st_mtime
        except OSError:
            return False
        return age_s >= self._stale_after_s

    def release(self) -> None:
        """Stops heartbeats and removes only this worker's claim."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=max(1.0, self._heartbeat_interval_s + 1.0))
        owner = self._read_owner(missing_ok=True)
        if owner.get("token") == self._token:
            self._path.unlink(missing_ok=True)
            self._events.append("lock_released", detail={"pid": os.getpid()})

    def _heartbeat_loop(self) -> None:
        while not self._stop.wait(self._heartbeat_interval_s):
            owner = self._read_owner(missing_ok=True)
            if owner.get("token") != self._token:
                return
            try:
                atomic_write_bytes(self._path, self._record_bytes())
            except OSError:
                return

    def _record_bytes(self) -> bytes:
        record = {
            "hostname": socket.gethostname(),
            "pid": os.getpid(),
            "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
            "heartbeat_at": self._now().isoformat(),
            "token": self._token,
        }
        return json.dumps(record, ensure_ascii=True, sort_keys=True).encode("ascii")

    def _read_owner(self, *, missing_ok: bool = False) -> dict[str, object]:
        try:
            raw = json.loads(self._path.read_text(encoding="ascii"))
        except FileNotFoundError:
            if missing_ok:
                return {}
            raise WorkerLockError(f"Worker lock disappeared: {self._path}") from None
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise WorkerLockError(f"Worker lock is unreadable: {self._path}") from error
        if not isinstance(raw, dict):
            raise WorkerLockError(f"Worker lock is invalid: {self._path}")
        return raw

    def _can_break(self, owner: Mapping[str, object]) -> bool:
        heartbeat = owner.get("heartbeat_at")
        if not isinstance(heartbeat, str):
            return False
        try:
            age_s = (self._now() - datetime.fromisoformat(heartbeat)).total_seconds()
        except ValueError:
            return False
        if age_s < self._stale_after_s:
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
            return self._job_is_active is not None and not self._job_is_active(job_id)
        return hostname == socket.gethostname() and isinstance(pid, int) and pid > 0


class GenerationHarness:
    """Executes one deterministic request plan and resumes verified artifacts."""

    def __init__(
        self,
        *,
        store: RunArtifactStore,
        requests: tuple[PlannedGeneration, ...],
        adapters: Mapping[str, ModelAdapter | PaidModelAdapter],
        budget_gate: BudgetGate | None = None,
        retry_policy: RetryPolicy | None = None,
        sleep: Callable[[float], None] = time.sleep,
        harness_git_commit: str | None = None,
        job_is_active: Callable[[str], bool] | None = None,
        paid_retry_classifier: (
            Callable[[AdapterTransportError, PlannedGeneration], PaidRetryDecision] | None
        ) = None,
        worker_stale_after_s: float = 600.0,
        now: Callable[[], datetime] | None = None,
        allow_dirty_worktree: bool = False,
    ) -> None:
        request_ids = tuple(item.model_input.request.request_id for item in requests)
        if not requests:
            raise ValueError("GenerationHarness requires at least one request")
        if len(set(request_ids)) != len(request_ids):
            raise ValueError("Harness requests must have unique request IDs")
        self._store = store
        self._requests = requests
        self._adapters = adapters
        self._budget_gate = budget_gate
        self._retry_policy = retry_policy or RetryPolicy()
        self._sleep = sleep
        if harness_git_commit is None:
            commit, status = _current_git_identity()
            if status and not allow_dirty_worktree:
                raise HarnessError(
                    "Generation requires a clean Git worktree; use the explicit dirty override"
                )
            self._harness_git_commit = commit
            self._git_identity_source: Literal["repository", "explicit"] = "repository"
            self._worktree_dirty: bool | None = bool(status)
            self._worktree_status_sha256: str | None = sha256_bytes(status) if status else None
        else:
            self._harness_git_commit = harness_git_commit
            self._git_identity_source = "explicit"
            self._worktree_dirty = None
            self._worktree_status_sha256 = None
        self._events = EventLog(store.path / "events.jsonl")
        self._job_is_active = job_is_active
        self._paid_retry_classifier = paid_retry_classifier
        self._worker_stale_after_s = worker_stale_after_s
        self._now = now or (lambda: datetime.now(UTC))
        self._stop_requested = threading.Event()

    def prepare(self) -> None:
        """Initializes immutable plan inputs and the planned run state."""
        if self._store.frozen:
            raise FrozenRunError(f"Run is frozen and cannot be resumed: {self._store.run_id}")
        self._initialize_store_preserving_lineage()
        self._prepare_environment()
        request_content = serialize_generation_requests(self._requests)
        requests_path = self._store.path / "requests.jsonl"
        if requests_path.exists():
            if not self._store.verified("requests.jsonl"):
                raise RunStateError("Existing requests.jsonl is not checksum-verified")
            if requests_path.read_bytes() != request_content:
                raise RunStateError("Existing requests.jsonl does not match the requested plan")
        else:
            self._store.write_bytes("requests.jsonl", request_content)
        if not (self._store.path / "state.json").exists():
            now = self._now()
            slurm_job_id = os.environ.get("SLURM_JOB_ID")
            state = PersistentRunState(
                schema_version="1.0",
                run_id=self._store.run_id,
                state="planned",
                slurm_job_id=slurm_job_id,
                owner=None,
                approval=None,
                updated_at=now,
                history=(
                    StateTransition(
                        state="planned",
                        ts=now,
                        reason="plan created",
                        slurm_job_id=slurm_job_id,
                    ),
                ),
            )
            self._write_state(state)
            self._events.append("stage_transition", detail={"state": "planned"})

    def _prepare_environment(self) -> None:
        project_root = Path(__file__).resolve().parents[3]
        lock_path = project_root / "uv.lock"
        if not lock_path.is_file():
            raise RunStateError("Pinned uv.lock is missing")
        environment = HarnessEnvironment(
            harness_git_commit=self._harness_git_commit,
            python_version=sys.version,
            uv_lock_sha256=sha256_file(lock_path),
            git_identity_source=self._git_identity_source,
            worktree_dirty=self._worktree_dirty,
            worktree_status_sha256=self._worktree_status_sha256,
        )
        path = self._store.path / "environment.json"
        if path.exists():
            if not self._store.verified("environment.json"):
                raise RunStateError("Existing environment.json is not checksum-verified")
            try:
                existing = HarnessEnvironment.model_validate_json(path.read_bytes())
            except (OSError, ValidationError) as error:
                raise RunStateError("Existing environment.json is invalid") from error
            if existing != environment:
                raise RunStateError("Producer environment changed across run resume")
            return
        self._store.write_json("environment.json", environment.model_dump(mode="json"))
        if not self._store.verified("environment.json"):
            raise RunStateError("Producer environment failed checksum verification")

    def _initialize_store_preserving_lineage(self) -> None:
        manifest_path = self._store.path / "manifest.json"
        if not manifest_path.exists():
            self._store.initialize()
            return
        if not self._store.verified("manifest.json"):
            raise RunStateError("Existing run manifest is not checksum-verified")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RunStateError("Existing run manifest is unreadable") from error
        if not isinstance(manifest, dict):
            raise RunStateError("Existing run manifest is not a JSON object")
        parent_run_id = manifest.get("parent_run_id")
        reason = manifest.get("reason")
        if parent_run_id is not None and not isinstance(parent_run_id, str):
            raise RunStateError("Existing parent_run_id is invalid")
        if reason is not None and not isinstance(reason, str):
            raise RunStateError("Existing run reason is invalid")
        self._store.initialize(parent_run_id=parent_run_id, reason=reason)

    def run(self) -> HarnessResult:
        """Runs missing requests; verified terminals are never reissued."""
        self.prepare()
        verified = tuple(
            load_verified_response(store=self._store, model_input=item.model_input)
            for item in self._requests
        )
        lock = WorkerLock(
            path=self._store.path / "LOCK",
            events=self._events,
            stale_after_s=self._worker_stale_after_s,
            job_is_active=self._job_is_active,
            now=self._now,
        )
        processed = 0
        skipped = 0
        retry_count = 0
        with lock:
            terminal_events = self._events.terminal_request_ids()
            if all(response is not None for response in verified):
                for item, response in zip(self._requests, verified, strict=True):
                    if response is None:
                        raise RunStateError("Verified-response snapshot changed unexpectedly")
                    if item.paid:
                        self._require_budget_gate().reconcile_terminal(
                            request_id=response.request_id,
                            actual_usd=response.usd_cost,
                        )
                    self._reconcile_terminal_attempt(item)
                    self._record_request_end(
                        response=response,
                        terminal_events=terminal_events,
                        recovered=True,
                    )
                state = self._load_state()
                if state.state != "complete":
                    self._transition(
                        "complete",
                        reason="all terminal artifacts verified",
                        owner=None,
                    )
                return HarnessResult(
                    processed=0,
                    skipped=len(self._requests),
                    retries=0,
                    state="complete",
                )
            if self._stop_requested.is_set():
                return self._stop_result(processed=0, skipped=0, retries=0)
            owner = RunOwner(
                host=socket.gethostname(),
                pid=os.getpid(),
                slurm_job_id=os.environ.get("SLURM_JOB_ID"),
                started_at=self._now(),
            )
            preauthorized: dict[str, PaidRequestPermit] = {}
            try:
                first_paid = next(
                    (
                        item
                        for item, response in zip(self._requests, verified, strict=True)
                        if item.paid and response is None
                    ),
                    None,
                )
                if first_paid is not None:
                    permit = self._reserve_if_paid(first_paid)
                    if permit is None:
                        raise AdapterPermitError("Paid generation has no budget permit")
                    preauthorized[first_paid.model_input.request.request_id] = permit
                    state = self._load_state()
                    if state.approval is None:
                        self._transition(
                            "approved",
                            reason="machine-readable approval verified",
                            owner=None,
                        )
                        self._record_approval(permit.approval_path)
                        state = self._load_state()
                    if state.state in {"approved", "failed", "cancelled"}:
                        self._transition(
                            "submitted",
                            reason="generation worker invocation recorded",
                            owner=None,
                        )
                self._transition("running", reason="worker started or resumed", owner=owner)
                for item in self._requests:
                    if self._stop_requested.is_set():
                        return self._stop_result(
                            processed=processed,
                            skipped=skipped,
                            retries=retry_count,
                        )
                    response = load_verified_response(
                        store=self._store,
                        model_input=item.model_input,
                    )
                    if response is not None:
                        if item.paid:
                            self._require_budget_gate().reconcile_terminal(
                                request_id=response.request_id,
                                actual_usd=response.usd_cost,
                            )
                        self._reconcile_terminal_attempt(item)
                        self._record_request_end(
                            response=response,
                            terminal_events=terminal_events,
                            recovered=True,
                        )
                        skipped += 1
                        continue
                    adapter = self._adapter_for(item)
                    request_id = item.model_input.request.request_id
                    permit = preauthorized.pop(request_id, None)
                    if item.paid and permit is None:
                        permit = self._reserve_if_paid(item)
                    if permit is not None:
                        self._record_approval(permit.approval_path)
                    self._events.append(
                        "request_start",
                        request_id=item.model_input.request.request_id,
                    )
                    started_at = self._now()
                    result, retries, attempt_ledger = self._generate_with_retries(
                        item=item,
                        adapter=adapter,
                        permit=permit,
                    )
                    completed_at = self._now()
                    retry_count += retries
                    try:
                        response = write_generation_response(
                            store=self._store,
                            model_input=item.model_input,
                            result=result,
                            started_at=started_at,
                            completed_at=completed_at,
                            harness_git_commit=self._harness_git_commit,
                        )
                    except ResponseArtifactError as error:
                        self._retain_response_failure(
                            item=item,
                            ledger=attempt_ledger,
                            error=error,
                            raw_response=result.raw_response,
                            provider_request_id=result.provider_request_id,
                            raw_truncated=False,
                        )
                        self._finish_transport_attempt(
                            attempt_ledger,
                            outcome="response_error",
                            retry_safe=False,
                            detail=str(error),
                        )
                        raise
                    self._finish_transport_attempt(
                        attempt_ledger,
                        outcome="success",
                        retry_safe=False,
                        detail=None,
                    )
                    if permit is not None:
                        self._require_budget_gate().settle(
                            permit,
                            actual_usd=response.usd_cost,
                        )
                    self._record_request_end(
                        response=response,
                        terminal_events=terminal_events,
                        recovered=False,
                    )
                    processed += 1
                    if self._stop_requested.is_set():
                        return self._stop_result(
                            processed=processed,
                            skipped=skipped,
                            retries=retry_count,
                        )
            except _GracefulStop as error:
                retry_count += error.retries
                return self._stop_result(
                    processed=processed,
                    skipped=skipped,
                    retries=retry_count,
                )
            except BudgetExceededError as error:
                self._events.append("budget_halt", detail={"reason": type(error).__name__})
                self._transition("failed", reason="budget ceiling reached", owner=None)
                raise
            except ApprovalError as error:
                self._events.append("error", detail={"type": type(error).__name__})
                self._transition("failed", reason="paid request authorization failed", owner=None)
                raise
            except (
                AdapterError,
                AdapterPermitError,
                ResponseArtifactError,
                RunStateError,
            ) as error:
                self._events.append("error", detail={"type": type(error).__name__})
                self._transition("failed", reason="generation request failed", owner=None)
                raise
            self._transition("complete", reason="all terminal artifacts verified", owner=None)
        return HarnessResult(
            processed=processed,
            skipped=skipped,
            retries=retry_count,
            state="complete",
        )

    def run_with_signal_handlers(self) -> HarnessResult:
        """Runs while treating SIGUSR1 as a finish-in-flight stop request."""
        if threading.current_thread() is not threading.main_thread():
            return self.run()

        def request_stop(signal_number: int, frame: object) -> None:
            del signal_number, frame
            self._stop_requested.set()

        previous = signal.signal(signal.SIGUSR1, request_stop)
        try:
            return self.run()
        finally:
            signal.signal(signal.SIGUSR1, previous)

    def request_stop(self) -> None:
        """Requests a graceful stop after the current in-flight request."""
        self._stop_requested.set()

    def _stop_result(self, *, processed: int, skipped: int, retries: int) -> HarnessResult:
        all_verified = all(
            load_verified_response(store=self._store, model_input=item.model_input) is not None
            for item in self._requests
        )
        state: RunStatus = "complete" if all_verified else "cancelled"
        reason = "all terminal artifacts verified" if all_verified else "SIGUSR1 stop requested"
        self._transition(state, reason=reason, owner=None)
        return HarnessResult(
            processed=processed,
            skipped=skipped,
            retries=retries,
            state=state,
        )

    def _record_request_end(
        self,
        *,
        response: GenerationResponse,
        terminal_events: set[str],
        recovered: bool,
    ) -> None:
        request_id = response.request_id
        if request_id in terminal_events:
            return
        self._events.append(
            "request_end",
            request_id=request_id,
            detail={
                "usd_cost": str(response.usd_cost),
                "latency_s": response.latency_s,
                "tokens": response.usage.model_dump(mode="json"),
                "recovered": recovered,
            },
        )
        terminal_events.add(request_id)

    def _generate_with_retries(
        self,
        *,
        item: PlannedGeneration,
        adapter: ModelAdapter | PaidModelAdapter,
        permit: PaidRequestPermit | None,
    ) -> tuple[AdapterResult, int, TransportAttemptLedger]:
        request_id = item.model_input.request.request_id
        retries = 0
        paid_adapter: PaidModelAdapter | None = None
        local_adapter: ModelAdapter | None = None
        paid_permit: PaidRequestPermit | None = None
        if item.paid:
            if permit is None:
                raise AdapterPermitError("Paid generation has no budget permit")
            if not isinstance(adapter, PaidModelAdapter):
                raise AdapterPermitError(
                    "Paid adapter must implement generate_paid(model_input, permit)"
                )
            paid_adapter = adapter
            paid_permit = permit
        else:
            if not isinstance(adapter, ModelAdapter):
                raise AdapterPermitError("Local adapter does not implement ModelAdapter")
            local_adapter = adapter
        while True:
            if self._stop_requested.is_set():
                raise _GracefulStop(retries)
            self._preflight_adapter(item, adapter)
            if paid_adapter is not None:
                if paid_permit is None:
                    raise AdapterPermitError("Paid generation lost its budget permit")
                gate = self._require_budget_gate()
                gate.verify(paid_permit)

            ledger = self._begin_transport_attempt(item)
            attempt = ledger.attempts[-1].attempt
            try:
                if paid_adapter is not None and paid_permit is not None:
                    result = paid_adapter.generate_paid(item.model_input, paid_permit)
                elif local_adapter is not None:
                    result = local_adapter.generate(item.model_input)
                else:
                    raise AdapterPermitError("No validated model adapter is available")
            except MissingSecretError as error:
                self._finish_transport_attempt(
                    ledger,
                    outcome="transport_error",
                    retry_safe=True,
                    detail=(
                        "Credential disappeared after preflight; no transport was attempted: "
                        f"{type(error).__name__}"
                    ),
                )
                raise
            except AdapterResponseError as error:
                self._retain_response_failure(
                    item=item,
                    ledger=ledger,
                    error=error,
                    raw_response=error.raw_response,
                    provider_request_id=error.provider_request_id,
                    raw_truncated=error.raw_truncated,
                )
                self._finish_transport_attempt(
                    ledger,
                    outcome="response_error",
                    retry_safe=False,
                    detail=str(error),
                )
                raise
            except AdapterTransportError as error:
                raw_response = getattr(error, "raw_response", None)
                provider_request_id = getattr(error, "provider_request_id", None)
                if isinstance(raw_response, bytes):
                    self._retain_response_failure(
                        item=item,
                        ledger=ledger,
                        error=error,
                        raw_response=raw_response,
                        provider_request_id=(
                            provider_request_id if isinstance(provider_request_id, str) else None
                        ),
                        raw_truncated=False,
                    )
                decision = self._retry_decision(error=error, item=item)
                self._finish_transport_attempt(
                    ledger,
                    outcome="transport_error",
                    retry_safe=decision.safe_to_retry,
                    detail=decision.reason,
                )
                if item.paid and not decision.safe_to_retry:
                    raise AmbiguousPaidAttemptError(
                        "Paid transport outcome is ambiguous; refusing a duplicate attempt"
                    ) from error
                if attempt >= self._retry_policy.max_attempts:
                    raise
                if self._stop_requested.is_set():
                    raise _GracefulStop(retries)
                delay_s = decision.retry_after_s
                if delay_s is None:
                    delay_s = self._retry_policy.delay_after(attempt)
                self._events.append(
                    "retry",
                    request_id=request_id,
                    detail={"attempt": attempt, "delay_s": delay_s},
                )
                self._sleep(delay_s)
                retries += 1
                continue
            if result.request_id != request_id:
                error = ResponseArtifactError("Adapter changed request_id during generation")
                self._retain_response_failure(
                    item=item,
                    ledger=ledger,
                    error=error,
                    raw_response=result.raw_response,
                    provider_request_id=result.provider_request_id,
                    raw_truncated=False,
                )
                self._finish_transport_attempt(
                    ledger,
                    outcome="response_error",
                    retry_safe=False,
                    detail=str(error),
                )
                raise error
            return result, retries, ledger

    @staticmethod
    def _preflight_adapter(
        item: PlannedGeneration,
        adapter: ModelAdapter | PaidModelAdapter,
    ) -> None:
        if isinstance(adapter, PreflightModelAdapter):
            adapter.preflight(item.model_input)

    def _retry_decision(
        self,
        *,
        error: AdapterTransportError,
        item: PlannedGeneration,
    ) -> PaidRetryDecision:
        if not item.paid:
            retry_after_s = getattr(error, "retry_after_s", None)
            return PaidRetryDecision(
                safe_to_retry=True,
                reason="local transport retry",
                retry_after_s=(retry_after_s if isinstance(retry_after_s, int | float) else None),
            )
        if self._paid_retry_classifier is not None:
            return self._paid_retry_classifier(error, item)
        return PaidRetryDecision(
            safe_to_retry=False,
            reason="provider acceptance is ambiguous",
        )

    def _begin_transport_attempt(
        self,
        item: PlannedGeneration,
    ) -> TransportAttemptLedger:
        ledger = self._load_attempt_ledger(item)
        if len(ledger.attempts) >= self._retry_policy.max_attempts:
            raise AdapterTransportError("Durable transport-attempt limit has been reached")
        if ledger.attempts and ledger.attempts[-1].outcome in {"success", "response_error"}:
            raise ResponseArtifactError(
                "Prior provider response has no verified terminal artifact; refusing reissue"
            )
        if item.paid and ledger.attempts:
            previous = ledger.attempts[-1]
            retry_proven_safe = previous.outcome == "transport_error" and previous.retry_safe
            if not retry_proven_safe:
                raise AmbiguousPaidAttemptError(
                    "Prior paid attempt may have been accepted; refusing transport"
                )
        attempt = TransportAttemptRecord(
            attempt=len(ledger.attempts) + 1,
            started_at=self._now(),
            outcome="started",
            paid=item.paid,
        )
        updated = TransportAttemptLedger(
            request_id=ledger.request_id,
            attempts=(*ledger.attempts, attempt),
        )
        self._write_attempt_ledger(item, updated)
        return updated

    def _finish_transport_attempt(
        self,
        ledger: TransportAttemptLedger,
        *,
        outcome: Literal["success", "transport_error", "response_error"],
        retry_safe: bool,
        detail: str | None,
    ) -> None:
        previous = ledger.attempts[-1]
        terminal = TransportAttemptRecord(
            attempt=previous.attempt,
            started_at=previous.started_at,
            finished_at=self._now(),
            outcome=outcome,
            paid=previous.paid,
            retry_safe=retry_safe,
            detail=detail,
        )
        updated = TransportAttemptLedger(
            request_id=ledger.request_id,
            attempts=(*ledger.attempts[:-1], terminal),
        )
        item = next(
            request
            for request in self._requests
            if request.model_input.request.request_id == ledger.request_id
        )
        self._write_attempt_ledger(item, updated)

    def _retain_response_failure(
        self,
        *,
        item: PlannedGeneration,
        ledger: TransportAttemptLedger,
        error: Exception,
        raw_response: bytes | None,
        provider_request_id: str | None,
        raw_truncated: bool,
    ) -> None:
        write_response_failure(
            store=self._store,
            model_input=item.model_input,
            attempt=ledger.attempts[-1].attempt,
            error=error,
            raw_response=raw_response,
            provider_request_id=provider_request_id,
            raw_truncated=raw_truncated,
            recorded_at=self._now(),
            harness_git_commit=self._harness_git_commit,
        )

    def _load_attempt_ledger(self, item: PlannedGeneration) -> TransportAttemptLedger:
        request_id = item.model_input.request.request_id
        relative_path = self._attempt_ledger_path(request_id)
        path = self._store.path / relative_path
        if not path.exists():
            return TransportAttemptLedger(request_id=request_id)
        if not self._store.verified(relative_path):
            raise RunStateError(f"Transport attempt ledger is unverified: {request_id}")
        try:
            ledger = TransportAttemptLedger.model_validate_json(path.read_bytes())
        except (OSError, ValidationError) as error:
            raise RunStateError(f"Transport attempt ledger is invalid: {request_id}") from error
        if ledger.request_id != request_id:
            raise RunStateError("Transport attempt ledger belongs to another request")
        return ledger

    def _reconcile_terminal_attempt(self, item: PlannedGeneration) -> None:
        ledger = self._load_attempt_ledger(item)
        if not ledger.attempts or ledger.attempts[-1].outcome == "success":
            return
        if ledger.attempts[-1].outcome != "started":
            raise RunStateError("Verified terminal conflicts with its transport-attempt outcome")
        self._finish_transport_attempt(
            ledger,
            outcome="success",
            retry_safe=False,
            detail="recovered from verified terminal artifact",
        )

    def _write_attempt_ledger(
        self,
        item: PlannedGeneration,
        ledger: TransportAttemptLedger,
    ) -> None:
        relative_path = self._attempt_ledger_path(item.model_input.request.request_id)
        self._store.write_json(relative_path, ledger.model_dump(mode="json"))
        if not self._store.verified(relative_path):
            raise RunStateError("Transport attempt ledger failed checksum verification")

    @staticmethod
    def _attempt_ledger_path(request_id: str) -> str:
        response_path = Path(response_relative_path(request_id))
        return str(response_path.parent / "transport-attempts.json")

    def _adapter_for(self, item: PlannedGeneration) -> ModelAdapter | PaidModelAdapter:
        model_key = item.model_input.request.model_key
        adapter = self._adapters.get(model_key)
        if adapter is None:
            raise AdapterPermitError(f"No adapter is configured for model_key={model_key!r}")
        return adapter

    def _reserve_if_paid(self, item: PlannedGeneration) -> PaidRequestPermit | None:
        if not item.paid:
            return None
        return self._require_budget_gate().reserve(
            request_id=item.model_input.request.request_id,
            max_cost_usd=item.max_cost_usd,
        )

    def _require_budget_gate(self) -> BudgetGate:
        if self._budget_gate is None:
            raise AdapterPermitError("Paid generation requires a configured BudgetGate")
        return self._budget_gate

    def _load_state(self) -> PersistentRunState:
        if not self._store.verified("state.json"):
            raise RunStateError("Run state is missing or checksum-invalid")
        try:
            state = PersistentRunState.model_validate_json(
                (self._store.path / "state.json").read_bytes()
            )
        except (OSError, ValidationError) as error:
            raise RunStateError("Run state does not satisfy its schema") from error
        if state.run_id != self._store.run_id:
            raise RunStateError("Run state belongs to a different run_id")
        return state

    def _write_state(self, state: PersistentRunState) -> None:
        self._store.write_json("state.json", state.model_dump(mode="json"))
        if not self._store.verified("state.json"):
            raise RunStateError("Run state failed checksum verification")

    def _transition(
        self,
        state: RunStatus,
        *,
        reason: str,
        owner: RunOwner | None,
    ) -> None:
        current = self._load_state()
        if current.state == state and (
            state != "running" or owner is None or current.owner == owner
        ):
            return
        allowed: dict[RunStatus, set[RunStatus]] = {
            "planned": {"approved", "running", "failed", "cancelled", "complete"},
            "approved": {"submitted", "running", "failed", "cancelled"},
            "submitted": {"running", "failed", "cancelled"},
            "running": {"running", "complete", "failed", "cancelled"},
            "failed": {"approved", "submitted", "running", "failed"},
            "cancelled": {"submitted", "running", "complete"},
            "complete": {"running"},
        }
        if state not in allowed[current.state]:
            raise RunStateError(f"Illegal run-state transition: {current.state} -> {state}")
        now = self._now()
        current_job_id = os.environ.get("SLURM_JOB_ID")
        if current_job_id is None and owner is not None:
            current_job_id = owner.slurm_job_id
        if current_job_id is None:
            current_job_id = current.slurm_job_id
        transition = StateTransition(
            state=state,
            ts=now,
            reason=reason,
            slurm_job_id=current_job_id,
        )
        updated = current.model_copy(
            update={
                "state": state,
                "slurm_job_id": current_job_id,
                "owner": owner,
                "updated_at": now,
                "history": (*current.history, transition),
            }
        )
        self._write_state(updated)
        self._events.append("stage_transition", detail={"state": state, "reason": reason})

    def _record_approval(self, approval_path: str) -> None:
        state = self._load_state()
        if state.approval is not None and state.approval != approval_path:
            raise RunStateError("Run approval path changed after paid generation began")
        if state.approval is None:
            self._write_state(state.model_copy(update={"approval": approval_path}))


def _current_git_identity() -> tuple[str, bytes]:
    project_root = Path(__file__).resolve().parents[3]
    try:
        commit = subprocess.check_output(
            ["git", "-C", str(project_root), "rev-parse", "HEAD"],
            text=True,
            timeout=GIT_IDENTITY_TIMEOUT_SECONDS,
        ).strip()
        status = subprocess.check_output(
            ["git", "-C", str(project_root), "status", "--porcelain=v1"],
            timeout=GIT_IDENTITY_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        raise HarnessError("Unable to resolve the harness Git identity") from error
    return commit, status
