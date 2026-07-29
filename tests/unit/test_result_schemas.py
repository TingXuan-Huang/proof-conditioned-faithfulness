"""Tests for generation, checking, judgment, alignment, and evaluation contracts."""

import subprocess
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from proof_faithfulness.schema import (
    CounterfactualEvaluation,
    GenerationResponse,
    LeanCheckResult,
    StepAlignment,
    StrategyJudgment,
)

REQUEST_ID = "a" * 64
PROJECT_ROOT = Path(__file__).parents[2]
HARNESS_COMMIT = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, text=True
).strip()
STARTED_AT = datetime(2026, 7, 24, tzinfo=UTC)
COMPLETED_AT = STARTED_AT + timedelta(seconds=1)


def _generation_response() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "request_id": REQUEST_ID,
        "model_key": "fixture_model",
        "revision": "revision-1",
        "raw": '{"choices":[{"message":{"content":"by trivial"}}]}',
        "text": "by trivial",
        "finish_reason": "stop",
        "usage": {"input_tokens": 10, "output_tokens": 2},
        "usd_cost": Decimal(0),
        "latency_s": 1.0,
        "started_at": STARTED_AT,
        "completed_at": COMPLETED_AT,
        "harness_git_commit": HARNESS_COMMIT,
    }


def test_generation_response_accepts_consistent_result() -> None:
    response = GenerationResponse.model_validate(_generation_response())
    assert response.text == "by trivial"
    assert response.provider_request_id is None


def test_generation_response_preserves_provider_request_id() -> None:
    payload = _generation_response()
    payload["provider_request_id"] = "provider-response-123"
    response = GenerationResponse.model_validate(payload)
    assert response.provider_request_id == "provider-response-123"


def test_generation_response_rejects_blank_provider_request_id() -> None:
    payload = _generation_response()
    payload["provider_request_id"] = "  "
    with pytest.raises(ValidationError):
        GenerationResponse.model_validate(payload)


def test_generation_response_rejects_reverse_time_order() -> None:
    response = _generation_response()
    response["completed_at"] = STARTED_AT - timedelta(seconds=1)
    with pytest.raises(ValidationError, match="complete before"):
        GenerationResponse.model_validate(response)


def test_generation_response_rejects_inconsistent_latency() -> None:
    response = _generation_response()
    response["latency_s"] = 2.0
    with pytest.raises(ValidationError, match="latency_s"):
        GenerationResponse.model_validate(response)


def test_lean_check_result_accepts_normalized_failure() -> None:
    result = LeanCheckResult(
        schema_version="1.0",
        request_id=REQUEST_ID,
        statement_hash_matches=True,
        extraction_status="success",
        parser_status="failed",
        elaboration_status="not_run",
        exit_code=1,
        wall_time_seconds=0.5,
        failure_category="syntax_invalid",
    )
    assert result.failure_category == "syntax_invalid"


def test_strategy_judgment_preserves_source_identity() -> None:
    judgment = StrategyJudgment(
        schema_version="1.0",
        request_id=REQUEST_ID,
        source_type="human",
        source_id="annotator-1",
        strategy_labels=("induction",),
        classification="match_A",
        explanation="The induction signature is explicit.",
    )
    assert judgment.source_id == "annotator-1"


def test_step_alignment_requires_evidence_unless_implicit() -> None:
    with pytest.raises(ValidationError, match="requires formal evidence"):
        StepAlignment(
            schema_version="1.0",
            request_id=REQUEST_ID,
            proof_id="A",
            informal_step_ids=("a1",),
            alignment_type="one_to_one",
            confidence=1.0,
            explanation="Missing evidence should fail.",
        )


def test_counterfactual_evaluation_rejects_reversed_ambiguity_bounds() -> None:
    with pytest.raises(ValidationError, match="lower bound"):
        CounterfactualEvaluation(
            schema_version="1.0",
            request_id=REQUEST_ID,
            compiled=True,
            strategy_match="match_A",
            step_coverage=1.0,
            utilization_state="used",
            ambiguity_lower=0.8,
            ambiguity_upper=0.2,
            source_judgment_ids=("judgment-1",),
        )
