from __future__ import annotations

import json
import socket
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from proof_faithfulness.artifacts import RunArtifactStore, sha256_bytes
from proof_faithfulness.generation.budget import (
    AmbiguousApprovalError,
    BudgetAccountingError,
    BudgetExceededError,
    BudgetGate,
    MissingApprovalError,
)


def _store(root: Path, run_id: str = "paid-run") -> RunArtifactStore:
    store = RunArtifactStore(root / "outputs", run_id)
    store.initialize()
    return store


def _approval(
    root: Path,
    *,
    store: RunArtifactStore,
    request_costs: dict[str, Decimal],
    inference_keys: dict[str, str] | None = None,
    max_usd: Decimal = Decimal(1),
    filename: str = "approval.json",
) -> Path:
    content = b"".join(
        (
            json.dumps(
                {
                    "max_cost_usd": str(cost),
                    "model_input": {
                        "request": {
                            "request_id": request_id,
                            "theorem_id": (
                                inference_keys[request_id]
                                if inference_keys is not None
                                else request_id
                            ),
                        }
                    },
                    "paid": True,
                },
                ensure_ascii=True,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
            + b"\n"
        )
        for request_id, cost in request_costs.items()
    )
    store.write_bytes("requests.jsonl", content)
    approvals = root / "approvals"
    approvals.mkdir(exist_ok=True)
    path = approvals / filename
    path.write_text(
        json.dumps(
            {
                "scope": "pilot-tier1",
                "run_ids": [store.run_id],
                "requests_sha256": sha256_bytes(content),
                "request_count": len(request_costs),
                "max_usd": str(max_usd),
                "approved_by": "Fixture Human",
                "date": "2026-07-25",
                "note": "Unit-test authorization only.",
            }
        ),
        encoding="utf-8",
    )
    return path


def _gate(
    root: Path,
    store: RunArtifactStore,
    *,
    aggregate: Decimal = Decimal(500),
) -> BudgetGate:
    return BudgetGate(
        store=store,
        approvals_root=root / "approvals",
        scope="pilot-tier1",
        aggregate_ceiling_usd=aggregate,
    )


def test_paid_reservation_refuses_when_approvals_directory_is_empty(tmp_path: Path) -> None:
    (tmp_path / "approvals").mkdir()
    store = _store(tmp_path)
    store.write_bytes(
        "requests.jsonl",
        b'{"max_cost_usd":"0.25","model_input":{"request":{"request_id":"'
        + b"a" * 64
        + b'"}},"paid":true}\n',
    )
    gate = _gate(tmp_path, store)
    with pytest.raises(MissingApprovalError, match="No approval matches"):
        gate.reserve(request_id="a" * 64, max_cost_usd=Decimal("0.25"))


def test_reservation_is_atomic_idempotent_and_non_secret(tmp_path: Path) -> None:
    store = _store(tmp_path)
    _approval(tmp_path, store=store, request_costs={"a" * 64: Decimal("0.25")})
    gate = _gate(tmp_path, store)
    first = gate.reserve(request_id="a" * 64, max_cost_usd=Decimal("0.25"))
    second = gate.reserve(request_id="a" * 64, max_cost_usd=Decimal("0.25"))
    assert first.request_id == second.request_id
    assert first.approval_sha256 == second.approval_sha256
    assert set(first.model_dump()) == {
        "schema_version",
        "run_id",
        "request_id",
        "inference_fingerprint",
        "scope",
        "approval_path",
        "approval_sha256",
        "requests_sha256",
        "request_count",
        "reserved_usd",
        "issued_at",
    }
    gate.verify(second)
    gate.settle(second, actual_usd=Decimal("0.1"))
    assert store.verified("budget.json")


def test_two_concurrent_reservations_cannot_both_cross_run_ceiling(tmp_path: Path) -> None:
    store = _store(tmp_path)
    _approval(
        tmp_path,
        store=store,
        request_costs={"a" * 64: Decimal("0.75"), "b" * 64: Decimal("0.75")},
    )
    gate = _gate(tmp_path, store)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(
                gate.reserve,
                request_id=request_id * 64,
                max_cost_usd=Decimal("0.75"),
            )
            for request_id in ("a", "b")
        ]
    outcomes: list[object] = []
    for future in futures:
        try:
            outcomes.append(future.result())
        except BudgetExceededError as error:
            outcomes.append(error)
    assert sum(isinstance(item, BudgetExceededError) for item in outcomes) == 1


def test_aggregate_ceiling_accounts_for_other_runs(tmp_path: Path) -> None:
    first_store = _store(tmp_path, "paid-run-1")
    second_store = _store(tmp_path, "paid-run-2")
    _approval(
        tmp_path,
        store=first_store,
        request_costs={"a" * 64: Decimal("0.6")},
        filename="first.json",
    )
    _approval(
        tmp_path,
        store=second_store,
        request_costs={"b" * 64: Decimal("0.6")},
        filename="second.json",
    )
    _gate(tmp_path, first_store, aggregate=Decimal(1)).reserve(
        request_id="a" * 64,
        max_cost_usd=Decimal("0.6"),
    )
    with pytest.raises(BudgetExceededError, match="aggregate"):
        _gate(tmp_path, second_store, aggregate=Decimal(1)).reserve(
            request_id="b" * 64,
            max_cost_usd=Decimal("0.6"),
        )


def test_same_paid_request_cannot_be_reserved_in_two_runs(tmp_path: Path) -> None:
    first_store = _store(tmp_path, "paid-run-1")
    second_store = _store(tmp_path, "paid-run-2")
    request_id = "a" * 64
    _approval(
        tmp_path,
        store=first_store,
        request_costs={request_id: Decimal("0.25")},
        filename="first.json",
    )
    _approval(
        tmp_path,
        store=second_store,
        request_costs={request_id: Decimal("0.25")},
        filename="second.json",
    )
    _gate(tmp_path, first_store).reserve(
        request_id=request_id,
        max_cost_usd=Decimal("0.25"),
    )
    with pytest.raises(BudgetAccountingError, match="already reserved by run paid-run-1"):
        _gate(tmp_path, second_store).reserve(
            request_id=request_id,
            max_cost_usd=Decimal("0.25"),
        )


def test_repricing_cannot_reserve_the_same_inference_under_a_new_request_id(
    tmp_path: Path,
) -> None:
    first_store = _store(tmp_path, "repriced-run-1")
    second_store = _store(tmp_path, "repriced-run-2")
    first_id = "a" * 64
    second_id = "b" * 64
    _approval(
        tmp_path,
        store=first_store,
        request_costs={first_id: Decimal("0.25")},
        inference_keys={first_id: "same-inference"},
        filename="first.json",
    )
    _approval(
        tmp_path,
        store=second_store,
        request_costs={second_id: Decimal("0.30")},
        inference_keys={second_id: "same-inference"},
        filename="second.json",
    )
    _gate(tmp_path, first_store).reserve(
        request_id=first_id,
        max_cost_usd=Decimal("0.25"),
    )
    with pytest.raises(BudgetAccountingError, match="already reserved by run repriced-run-1"):
        _gate(tmp_path, second_store).reserve(
            request_id=second_id,
            max_cost_usd=Decimal("0.30"),
        )


def test_aggregate_ceiling_cannot_be_configured_above_500_dollars(tmp_path: Path) -> None:
    store = _store(tmp_path)
    with pytest.raises(ValueError, match="absolute \\$500 ceiling"):
        _gate(tmp_path, store, aggregate=Decimal(501))


def test_six_one_cent_reservations_exactly_reach_six_cent_ceiling(tmp_path: Path) -> None:
    store = _store(tmp_path)
    costs = {f"{index:064x}": Decimal("0.01") for index in range(6)}
    costs["f" * 64] = Decimal("0.01")
    _approval(
        tmp_path,
        store=store,
        request_costs=costs,
        max_usd=Decimal("0.06"),
    )
    gate = _gate(tmp_path, store)
    for index in range(6):
        gate.reserve(request_id=f"{index:064x}", max_cost_usd=Decimal("0.01"))
    with pytest.raises(BudgetExceededError, match="already been reached"):
        gate.reserve(request_id="f" * 64, max_cost_usd=Decimal("0.01"))
    ledger = json.loads((store.path / "budget.json").read_text(encoding="utf-8"))
    assert sum(Decimal(entry["reserved_usd"]) for entry in ledger["entries"]) == Decimal("0.06")


def test_approval_edit_invalidates_an_issued_permit(tmp_path: Path) -> None:
    store = _store(tmp_path)
    approval = _approval(
        tmp_path,
        store=store,
        request_costs={"a" * 64: Decimal("0.25")},
    )
    gate = _gate(tmp_path, store)
    permit = gate.reserve(request_id="a" * 64, max_cost_usd=Decimal("0.25"))
    approval.write_text(approval.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(BudgetAccountingError, match="changed"):
        gate.verify(permit)


def test_approval_must_bind_the_exact_request_manifest(tmp_path: Path) -> None:
    store = _store(tmp_path)
    approval = _approval(
        tmp_path,
        store=store,
        request_costs={"a" * 64: Decimal("0.25")},
    )
    payload = json.loads(approval.read_text(encoding="utf-8"))
    payload["requests_sha256"] = "b" * 64
    approval.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(BudgetAccountingError, match="finalized request manifest"):
        _gate(tmp_path, store).reserve(
            request_id="a" * 64,
            max_cost_usd=Decimal("0.25"),
        )


def test_caller_cannot_override_the_manifest_reservation(tmp_path: Path) -> None:
    store = _store(tmp_path)
    _approval(tmp_path, store=store, request_costs={"a" * 64: Decimal("0.25")})
    with pytest.raises(BudgetAccountingError, match="differs from its manifest"):
        _gate(tmp_path, store).reserve(
            request_id="a" * 64,
            max_cost_usd=Decimal("0.20"),
        )


def test_multiple_matching_approvals_fail_closed(tmp_path: Path) -> None:
    store = _store(tmp_path)
    request_costs = {"a" * 64: Decimal("0.25")}
    _approval(tmp_path, store=store, request_costs=request_costs, filename="first.json")
    _approval(tmp_path, store=store, request_costs=request_costs, filename="second.json")
    with pytest.raises(AmbiguousApprovalError):
        _gate(tmp_path, store).reserve(
            request_id="a" * 64,
            max_cost_usd=Decimal("0.25"),
        )


def test_provider_overspend_is_recorded_before_accounting_failure(tmp_path: Path) -> None:
    store = _store(tmp_path)
    _approval(tmp_path, store=store, request_costs={"a" * 64: Decimal("0.25")})
    gate = _gate(tmp_path, store)
    permit = gate.reserve(request_id="a" * 64, max_cost_usd=Decimal("0.25"))
    with pytest.raises(BudgetAccountingError, match="exceeded its reservation"):
        gate.settle(permit, actual_usd=Decimal("0.3"))
    with pytest.raises(BudgetAccountingError, match="exceeded its reservation"):
        gate.settle(permit, actual_usd=Decimal("0.3"))
    with pytest.raises(BudgetAccountingError, match="exceeded its reservation"):
        gate.reconcile_terminal(
            request_id="a" * 64,
            actual_usd=Decimal("0.3"),
        )
    payload = json.loads((store.path / "budget.json").read_text(encoding="utf-8"))
    assert payload["entries"][0]["spent_usd"] == "0.3"


def test_stale_global_budget_lock_requires_age_and_dead_job(tmp_path: Path) -> None:
    store = _store(tmp_path)
    _approval(tmp_path, store=store, request_costs={"a" * 64: Decimal("0.25")})
    now = datetime(2026, 7, 25, 12, tzinfo=UTC)
    lock = store.outputs_root / ".PAID_BUDGET_LOCK"
    lock.write_text(
        json.dumps(
            {
                "hostname": socket.gethostname(),
                "pid": 999_999_999,
                "slurm_job_id": "12345",
                "heartbeat_at": (now - timedelta(minutes=11)).isoformat(),
                "token": "dead",
            }
        ),
        encoding="ascii",
    )
    gate = BudgetGate(
        store=store,
        approvals_root=tmp_path / "approvals",
        scope="pilot-tier1",
        job_is_active=lambda job_id: job_id == "still-running",
        now=lambda: now,
    )
    permit = gate.reserve(request_id="a" * 64, max_cost_usd=Decimal("0.25"))
    assert permit.request_id == "a" * 64
    assert not lock.exists()


def test_concurrent_stale_lock_breakers_are_serialized(tmp_path: Path) -> None:
    first_store = _store(tmp_path, "stale-breaker-1")
    second_store = _store(tmp_path, "stale-breaker-2")
    _approval(
        tmp_path,
        store=first_store,
        request_costs={"a" * 64: Decimal("0.25")},
        filename="first.json",
    )
    _approval(
        tmp_path,
        store=second_store,
        request_costs={"b" * 64: Decimal("0.25")},
        filename="second.json",
    )
    now = datetime(2026, 7, 25, 12, tzinfo=UTC)
    lock = first_store.outputs_root / ".PAID_BUDGET_LOCK"
    lock.write_text(
        json.dumps(
            {
                "hostname": socket.gethostname(),
                "pid": 999_999_999,
                "slurm_job_id": None,
                "heartbeat_at": (now - timedelta(minutes=11)).isoformat(),
                "token": "dead",
            }
        ),
        encoding="ascii",
    )
    gates = (
        BudgetGate(
            store=first_store,
            approvals_root=tmp_path / "approvals",
            scope="pilot-tier1",
            now=lambda: now,
        ),
        BudgetGate(
            store=second_store,
            approvals_root=tmp_path / "approvals",
            scope="pilot-tier1",
            now=lambda: now,
        ),
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(
                gate.reserve,
                request_id=request_id * 64,
                max_cost_usd=Decimal("0.25"),
            )
            for gate, request_id in zip(gates, ("a", "b"), strict=True)
        ]
        permits = tuple(future.result() for future in futures)
    assert {permit.request_id for permit in permits} == {"a" * 64, "b" * 64}
    assert not lock.exists()
