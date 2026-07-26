"""Fast unit tests for trusted Lean process-result classification."""

from proof_faithfulness.lean import FAILURE_RESOURCE_LIMIT, FAILURE_SUCCESS
from proof_faithfulness.lean.checker import (
    DEFAULT_MEMORY_LIMIT_MB,
    LeanWarmupResult,
    _execution_outcome,
    _ExecutionResult,
    _ExtractedCandidate,
)


def test_normative_address_space_limit_is_eight_gibibytes() -> None:
    assert DEFAULT_MEMORY_LIMIT_MB == 8192


def test_resource_signal_is_not_classified_as_invalid_proof() -> None:
    extracted = _ExtractedCandidate(
        status=FAILURE_SUCCESS,
        body="by rfl",
        statement_hash_matches=True,
    )

    for exit_code in (-11, 139):
        outcome = _execution_outcome(
            request_id="a" * 64,
            extracted=extracted,
            execution=_ExecutionResult(
                exit_code=exit_code,
                stdout="",
                stderr="",
                wall_time_seconds=73.87,
            ),
            source="import Mathlib\n",
        )

        assert outcome.result.failure_category == FAILURE_RESOURCE_LIMIT
        assert outcome.result.parser_status == "unknown"
        assert outcome.result.elaboration_status == "failed"


def test_warmup_resource_signal_has_explicit_operational_category() -> None:
    result = LeanWarmupResult(
        exit_code=139,
        stdout="",
        stderr="",
        wall_time_seconds=73.87,
    )

    assert not result.success
    assert result.failure_category == FAILURE_RESOURCE_LIMIT
