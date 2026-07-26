from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from proof_faithfulness.artifacts import RunArtifactStore
from proof_faithfulness.evaluation.inputs import (
    EvaluationInputError,
    prepare_internal_annotation_item,
)
from proof_faithfulness.evaluation.models import EvaluationPreparationSpec
from proof_faithfulness.generation.artifacts import response_relative_path
from proof_faithfulness.generation.checking import (
    GenerationCheckSpec,
    check_generation_response,
)
from proof_faithfulness.generation.cli import ManifestMockAdapter, generation_app
from proof_faithfulness.generation.config import PlanningModel, load_condition_matrix
from proof_faithfulness.generation.planning import (
    PlannedGeneration,
    PromptTheorem,
    build_generation_plan,
)
from proof_faithfulness.generation.prompts import PromptRepository
from proof_faithfulness.generation.run import GenerationHarness
from proof_faithfulness.lean import FAILURE_PROHIBITED_SORRY
from proof_faithfulness.lean.artifacts import LeanArtifactError, load_check_outcome
from proof_faithfulness.models import ModelCapabilities
from proof_faithfulness.models.config import DecodingConfig, MockAdapterConfig

PROJECT_ROOT = Path(__file__).parents[2]
CONDITIONS = PROJECT_ROOT / "configs" / "experiment" / "conditions.yaml"
PROMPTS = PROJECT_ROOT / "prompts"
DECLARATION = "theorem generatedIdentity (n : Nat) : n = n"
INFORMAL_PROOF = "Use reflexivity."


def test_standard_generation_check_cli_persists_real_s2_evidence_for_evaluation(
    tmp_path: Path,
) -> None:
    store, planned, check_spec, evaluation_spec = _generated_fixture(tmp_path)
    specs_path = tmp_path / "lean-check-specs.jsonl"
    specs_path.write_text(f"{check_spec.model_dump_json()}\n", encoding="utf-8")

    result = CliRunner().invoke(
        generation_app,
        [
            "check",
            "--specs",
            str(specs_path),
            "--outputs-root",
            str(store.outputs_root),
            "--run-id",
            store.run_id,
            "--project-root",
            str(PROJECT_ROOT),
        ],
    )

    assert result.exit_code == 0, result.output
    assert '"successes": 1' in result.output
    request_id = planned.model_input.request.request_id
    assert store.verified(f"lean/{request_id}/check.json")
    persisted = load_check_outcome(
        store=store,
        request_id=request_id,
        candidate="by\n  rfl",
    )
    assert persisted is not None
    assert persisted.result.failure_category == "success"
    item = prepare_internal_annotation_item(
        store=store,
        model_input=planned.model_input,
        spec=evaluation_spec,
    )
    assert item.generated_lean_proof == "by\n  rfl"


def test_generation_check_rejects_mismatched_spec_and_corrupt_response(
    tmp_path: Path,
) -> None:
    store, planned, check_spec, _ = _generated_fixture(tmp_path)
    mismatched = check_spec.model_copy(
        update={"declaration": "theorem anotherIdentity (n : Nat) : n = n"}
    )
    with pytest.raises((LeanArtifactError, ValueError), match="declaration|statement"):
        check_generation_response(
            store=store,
            model_input=planned.model_input,
            spec=mismatched.lean_candidate_spec(),
            project_root=PROJECT_ROOT,
        )

    response_path = store.path / response_relative_path(planned.model_input.request.request_id)
    response_path.write_bytes(b"corrupt")
    with pytest.raises(LeanArtifactError, match="missing, corrupt, or non-terminal"):
        check_generation_response(
            store=store,
            model_input=planned.model_input,
            spec=check_spec.lean_candidate_spec(),
            project_root=PROJECT_ROOT,
        )


def test_failed_trusted_check_is_persisted_but_rejected_by_evaluation(
    tmp_path: Path,
) -> None:
    store, planned, check_spec, evaluation_spec = _generated_fixture(
        tmp_path,
        response_text="by sorry",
    )

    outcome = check_generation_response(
        store=store,
        model_input=planned.model_input,
        spec=check_spec.lean_candidate_spec(),
        project_root=PROJECT_ROOT,
    )

    assert outcome.result.failure_category == FAILURE_PROHIBITED_SORRY
    request_id = planned.model_input.request.request_id
    assert store.verified(f"lean/{request_id}/check.json")
    with pytest.raises(EvaluationInputError, match="not accepted: prohibited_sorry"):
        prepare_internal_annotation_item(
            store=store,
            model_input=planned.model_input,
            spec=evaluation_spec,
        )


def _generated_fixture(
    tmp_path: Path,
    *,
    response_text: str = "by\n  rfl",
) -> tuple[
    RunArtifactStore,
    PlannedGeneration,
    GenerationCheckSpec,
    EvaluationPreparationSpec,
]:
    model = PlanningModel(
        backend_config=MockAdapterConfig(
            model_key="checking-mock",
            model_id="checking-mock",
            model_revision="mock-v1",
            response_text=response_text,
            capabilities=ModelCapabilities(
                proof_conditioning=True,
                deterministic_seed=True,
                local_inference=True,
            ),
        ),
        mock_chat_template="mock_chat_v1.txt",
        mock_decoding=DecodingConfig(
            temperature=0.2,
            top_p=1,
            max_tokens=1024,
            seed_base=19,
        ),
        mock_max_input_tokens=2048,
    )
    theorem = PromptTheorem.from_text(
        theorem_id="generated-check-fixture",
        split="pilot",
        imports=("Mathlib.Data.Nat.Defs",),
        lean_statement=DECLARATION,
        proof_a=INFORMAL_PROOF,
        proof_b="Use equality induction.",
        paraphrase_a="Close by reflexivity.",
        paraphrase_b="Eliminate equality.",
    )
    plan = build_generation_plan(
        theorems=(theorem,),
        models=(model,),
        matrix=load_condition_matrix(CONDITIONS),
        tier=1,
        prompt_repository=PromptRepository(PROMPTS),
    )
    planned = next(
        item for item in plan.requests if item.model_input.request.condition == "proof_a"
    )
    store = RunArtifactStore(tmp_path / "outputs", "standard-generation-check")
    GenerationHarness(
        store=store,
        requests=(planned,),
        adapters={model.key: ManifestMockAdapter(model)},
        harness_git_commit="a" * 40,
    ).run()
    request_id = planned.model_input.request.request_id
    return (
        store,
        planned,
        GenerationCheckSpec(
            request_id=request_id,
            imports=theorem.imports,
            declaration_name="generatedIdentity",
            declaration=DECLARATION,
        ),
        EvaluationPreparationSpec(
            request_id=request_id,
            theorem_statement=DECLARATION,
            supplied_informal_proof=INFORMAL_PROOF,
            rubric_text="Classify proof strategy evidence.",
            rubric_version="rubric-v1",
            extractor_version="extractor-v1",
            signature_evidence=("reflexivity",),
        ),
    )
