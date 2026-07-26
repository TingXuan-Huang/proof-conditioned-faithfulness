"""Tests for request-bound trusted Lean checker artifact persistence."""

from pathlib import Path
from typing import Any

import pytest

from proof_faithfulness.artifacts import ArtifactError, RunArtifactStore
from proof_faithfulness.lean.artifacts import (
    LeanArtifactError,
    check_and_persist_candidate,
    load_check_outcome,
)
from proof_faithfulness.lean.checker import CheckOutcome
from proof_faithfulness.schema import LeanCheckResult

REQUEST_ID = "a" * 64
CANDIDATE = "by\n  rfl"


def test_interruption_before_terminal_check_recovers_by_rechecking(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = RunArtifactStore(tmp_path, "lean-artifact-crash")
    store.initialize()
    outcome = _successful_outcome()
    checker_calls = 0

    def checker(candidate: str) -> CheckOutcome:
        nonlocal checker_calls
        assert candidate == CANDIDATE
        checker_calls += 1
        return outcome

    original_write_json = store.write_json
    interrupt_terminal = True

    def write_json(relative_path: str | Path, value: Any) -> str:
        if interrupt_terminal and Path(relative_path) == Path("lean") / REQUEST_ID / "check.json":
            raise ArtifactError("simulated interruption before terminal write")
        return original_write_json(relative_path, value)

    monkeypatch.setattr(store, "write_json", write_json)
    with pytest.raises(LeanArtifactError, match="Unable to persist checker artifact"):
        check_and_persist_candidate(
            store=store,
            request_id=REQUEST_ID,
            candidate=CANDIDATE,
            checker=checker,
        )

    assert checker_calls == 1
    assert store.verified(f"lean/{REQUEST_ID}/check-input.json")
    assert not (store.path / "lean" / REQUEST_ID / "check.json").exists()
    assert (
        load_check_outcome(store=store, request_id=REQUEST_ID, candidate=CANDIDATE)
        is None
    )

    interrupt_terminal = False
    recovered = check_and_persist_candidate(
        store=store,
        request_id=REQUEST_ID,
        candidate=CANDIDATE,
        checker=checker,
    )

    assert checker_calls == 2
    assert recovered == outcome
    assert store.verified(f"lean/{REQUEST_ID}/check.json")
    persisted = load_check_outcome(
        store=store,
        request_id=REQUEST_ID,
        candidate=CANDIDATE,
    )
    assert persisted is not None
    assert persisted.result.failure_category == "success"
    assert persisted.stdout == outcome.stdout
    assert persisted.stderr == outcome.stderr
    assert persisted.assembled_source == outcome.assembled_source


def _successful_outcome() -> CheckOutcome:
    return CheckOutcome(
        result=LeanCheckResult(
            schema_version="1.0",
            request_id=REQUEST_ID,
            statement_hash_matches=True,
            extraction_status="success",
            parser_status="success",
            elaboration_status="success",
            exit_code=0,
            wall_time_seconds=0.01,
            declaration_name="fixtureIdentity",
            axioms=(),
            prohibited_token_findings=(),
            failure_category="success",
        ),
        stdout="",
        stderr="",
        assembled_source="theorem fixtureIdentity : True := by\n  trivial\n",
    )
