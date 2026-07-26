"""Request-bound preparation of accepted model outputs for evaluation."""

from __future__ import annotations

import hashlib
import json

from proof_faithfulness.artifacts import RunArtifactStore
from proof_faithfulness.evaluation.models import (
    EvaluationPreparationSpec,
    InternalAnnotationItem,
    SensitiveMetadata,
)
from proof_faithfulness.generation.artifacts import load_verified_response
from proof_faithfulness.lean.artifacts import LeanArtifactError, load_check_outcome
from proof_faithfulness.models import ModelInput
from proof_faithfulness.schema import FIXED_ALLOWED_AXIOMS, LeanCheckResult


class EvaluationInputError(RuntimeError):
    """Raised when generation or Lean evidence is not safe to evaluate."""


def prepare_internal_annotation_item(
    *,
    store: RunArtifactStore,
    model_input: ModelInput,
    spec: EvaluationPreparationSpec,
) -> InternalAnnotationItem:
    """Build an internal annotation item from verified, accepted artifacts.

    The context must hash to the immutable generation request. The terminal response,
    Lean result, checker input identity, assembled source, and diagnostics must all have
    valid artifact-store checksums. Only a successful trusted-checker result whose
    candidate hash matches the exact response text is accepted.
    """
    request = model_input.request
    if spec.request_id != request.request_id:
        raise EvaluationInputError("Evaluation context belongs to another request")
    if _sha256_text(spec.theorem_statement) != request.statement_hash:
        raise EvaluationInputError("Theorem statement does not match the request identity")
    if request.proof_id is None:
        if spec.supplied_informal_proof != "":
            raise EvaluationInputError(
                "Theorem-only requests require an exactly empty informal proof"
            )
    elif not spec.supplied_informal_proof.strip():
        raise EvaluationInputError(
            "Proof-conditioned requests require a nonempty informal proof"
        )
    if _sha256_text(spec.supplied_informal_proof) != request.proof_hash:
        raise EvaluationInputError("Informal proof does not match the request identity")

    response = load_verified_response(store=store, model_input=model_input)
    if response is None:
        raise EvaluationInputError("Generation response is missing, corrupt, or non-terminal")
    _load_accepted_lean_result(
        store=store,
        request_id=request.request_id,
        candidate=response.text,
    )
    prompt_text = json.dumps(
        {"messages": [message.model_dump(mode="json") for message in model_input.messages]},
        allow_nan=False,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return InternalAnnotationItem(
        request_id=request.request_id,
        theorem_id=request.theorem_id,
        theorem_statement=spec.theorem_statement,
        supplied_informal_proof=spec.supplied_informal_proof,
        generated_lean_proof=response.text,
        rubric_text=spec.rubric_text,
        rubric_version=spec.rubric_version,
        extractor_version=spec.extractor_version,
        signature_evidence=spec.signature_evidence,
        sensitive=SensitiveMetadata(
            model_name=request.model_key,
            condition_key=request.condition,
            prompt_text=prompt_text,
            sample_index=request.sample_index,
        ),
    )


def _load_accepted_lean_result(
    *,
    store: RunArtifactStore,
    request_id: str,
    candidate: str,
) -> LeanCheckResult:
    try:
        outcome = load_check_outcome(
            store=store,
            request_id=request_id,
            candidate=candidate,
        )
    except LeanArtifactError as error:
        raise EvaluationInputError(str(error)) from error
    if outcome is None:
        raise EvaluationInputError("Lean result is missing or checksum-invalid")
    result = outcome.result
    if not _lean_result_accepted(result):
        raise EvaluationInputError(f"Lean result is not accepted: {result.failure_category}")
    if outcome.assembled_source is None:
        raise EvaluationInputError("Accepted Lean result has no verified assembled source")
    return result


def _lean_result_accepted(result: LeanCheckResult) -> bool:
    return (
        result.failure_category == "success"
        and result.statement_hash_matches
        and result.extraction_status == "success"
        and result.parser_status == "success"
        and result.elaboration_status == "success"
        and result.exit_code == 0
        and not result.prohibited_token_findings
        and set(result.axioms) <= set(FIXED_ALLOWED_AXIOMS)
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
