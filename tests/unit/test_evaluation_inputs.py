from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from proof_faithfulness.artifacts import RunArtifactStore
from proof_faithfulness.evaluation.blinding import export_blinded_bundle
from proof_faithfulness.evaluation.cli import app
from proof_faithfulness.evaluation.inputs import (
    EvaluationInputError,
    prepare_internal_annotation_item,
)
from proof_faithfulness.evaluation.models import EvaluationPreparationSpec
from proof_faithfulness.generation.artifacts import (
    response_relative_path,
    write_generation_response,
)
from proof_faithfulness.generation.cli import ManifestMockAdapter
from proof_faithfulness.generation.config import PlanningModel, load_condition_matrix
from proof_faithfulness.generation.planning import (
    PromptTheorem,
    build_generation_plan,
    serialize_generation_requests,
)
from proof_faithfulness.generation.prompts import PromptRepository
from proof_faithfulness.models import ModelCapabilities, ModelInput
from proof_faithfulness.models.config import DecodingConfig, MockAdapterConfig
from proof_faithfulness.schema import LeanCheckResult

PROJECT_ROOT = Path(__file__).parents[2]
THEOREM_STATEMENT = "example : True := by"
INFORMAL_PROOF = "Truth is true."


def test_preparation_derives_request_bound_item_deterministically(tmp_path: Path) -> None:
    store, model_input, spec = _prepared_fixture(tmp_path)

    first = prepare_internal_annotation_item(
        store=store,
        model_input=model_input,
        spec=spec,
    )
    second = prepare_internal_annotation_item(
        store=store,
        model_input=model_input,
        spec=spec,
    )

    assert first == second
    assert first.request_id == model_input.request.request_id
    assert first.theorem_id == model_input.request.theorem_id
    assert first.sensitive.model_name == model_input.request.model_key
    assert first.sensitive.condition_key == model_input.request.condition
    assert first.sensitive.sample_index == model_input.request.sample_index
    assert first.generated_lean_proof


def test_prepare_cli_uses_verified_run_requests_and_writes_jsonl(tmp_path: Path) -> None:
    store, model_input, spec = _prepared_fixture(tmp_path)
    contexts_path = tmp_path / "contexts.jsonl"
    contexts_path.write_text(f"{spec.model_dump_json()}\n", encoding="utf-8")
    output_path = tmp_path / "internal-items.jsonl"

    result = CliRunner().invoke(
        app,
        [
            "prepare",
            "--contexts",
            str(contexts_path),
            "--outputs-root",
            str(store.outputs_root),
            "--run-id",
            store.run_id,
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert result.output == "prepared_items=1\n"
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["request_id"] == model_input.request.request_id
    assert payload["generated_lean_proof"]


def test_theorem_only_preparation_uses_empty_proof_without_condition_metadata(
    tmp_path: Path,
) -> None:
    store, model_input, spec = _prepared_fixture(tmp_path, condition="theorem_only")

    item = prepare_internal_annotation_item(
        store=store,
        model_input=model_input,
        spec=spec,
    )

    assert model_input.request.proof_id is None
    assert item.supplied_informal_proof == ""
    bundle_dir = tmp_path / "theorem-only-bundle"
    mapping_path = tmp_path / "private" / "theorem-only-map.json"
    blinded = export_blinded_bundle(
        (item,),
        bundle_dir,
        mapping_path,
        b"fixture-blinding-key",
    )
    assert blinded[0].supplied_informal_proof == ""
    public_content = b"\n".join(
        path.read_bytes() for path in bundle_dir.rglob("*") if path.is_file()
    )
    assert model_input.request.condition.encode("utf-8") not in public_content


def test_prepare_cli_supports_theorem_only_context(tmp_path: Path) -> None:
    store, model_input, spec = _prepared_fixture(tmp_path, condition="theorem_only")
    contexts_path = tmp_path / "theorem-only-context.jsonl"
    contexts_path.write_text(f"{spec.model_dump_json()}\n", encoding="utf-8")
    output_path = tmp_path / "theorem-only-items.jsonl"

    result = CliRunner().invoke(
        app,
        [
            "prepare",
            "--contexts",
            str(contexts_path),
            "--outputs-root",
            str(store.outputs_root),
            "--run-id",
            store.run_id,
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["request_id"] == model_input.request.request_id
    assert payload["supplied_informal_proof"] == ""


def test_prepare_cli_rejects_empty_proof_conditioned_context(tmp_path: Path) -> None:
    store, _, spec = _prepared_fixture(tmp_path)
    contexts_path = tmp_path / "invalid-empty-proof.jsonl"
    invalid = spec.model_copy(update={"supplied_informal_proof": ""})
    contexts_path.write_text(f"{invalid.model_dump_json()}\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "prepare",
            "--contexts",
            str(contexts_path),
            "--outputs-root",
            str(store.outputs_root),
            "--run-id",
            store.run_id,
            "--output",
            str(tmp_path / "must-not-exist.jsonl"),
        ],
    )

    assert result.exit_code == 2
    assert "Proof-conditioned requests require a nonempty informal proof" in result.output


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("request_id", "f" * 64, "another request"),
        ("theorem_statement", "example : False := by", "Theorem statement"),
        ("supplied_informal_proof", "A different proof.", "Informal proof"),
    ],
)
def test_preparation_rejects_context_identity_mismatch(
    tmp_path: Path,
    field: str,
    value: str,
    message: str,
) -> None:
    store, model_input, spec = _prepared_fixture(tmp_path)

    with pytest.raises(EvaluationInputError, match=message):
        prepare_internal_annotation_item(
            store=store,
            model_input=model_input,
            spec=spec.model_copy(update={field: value}),
        )


def test_preparation_rejects_missing_or_corrupt_response(tmp_path: Path) -> None:
    store, model_input, spec = _prepared_fixture(tmp_path)
    response_path = store.path / response_relative_path(model_input.request.request_id)
    response_path.write_bytes(b"corrupt")

    with pytest.raises(EvaluationInputError, match="missing, corrupt, or non-terminal"):
        prepare_internal_annotation_item(
            store=store,
            model_input=model_input,
            spec=spec,
        )

    empty_store = RunArtifactStore(tmp_path, "no-response")
    empty_store.initialize()
    with pytest.raises(EvaluationInputError, match="missing, corrupt, or non-terminal"):
        prepare_internal_annotation_item(
            store=empty_store,
            model_input=model_input,
            spec=spec,
        )


def test_preparation_rejects_failed_or_unbound_lean_result(tmp_path: Path) -> None:
    store, model_input, spec = _prepared_fixture(tmp_path)
    request_id = model_input.request.request_id
    result_path = f"lean/{request_id}/check.json"
    result = LeanCheckResult.model_validate_json((store.path / result_path).read_bytes())
    store.write_json(
        result_path,
        result.model_copy(
            update={
                "elaboration_status": "failed",
                "exit_code": 1,
                "failure_category": "type_invalid",
            }
        ).model_dump(mode="json"),
    )
    with pytest.raises(EvaluationInputError, match="not accepted: type_invalid"):
        prepare_internal_annotation_item(
            store=store,
            model_input=model_input,
            spec=spec,
        )

    _write_lean_evidence(store, model_input, candidate_hash="0" * 64)
    with pytest.raises(EvaluationInputError, match="Checker input identity changed"):
        prepare_internal_annotation_item(
            store=store,
            model_input=model_input,
            spec=spec,
        )


def _prepared_fixture(
    tmp_path: Path,
    *,
    condition: str = "proof_a",
) -> tuple[RunArtifactStore, ModelInput, EvaluationPreparationSpec]:
    if condition not in {"theorem_only", "proof_a"}:
        raise ValueError(f"Unsupported fixture condition: {condition}")
    capabilities = ModelCapabilities(
        proof_conditioning=True,
        deterministic_seed=True,
        local_inference=True,
        cost_reporting=True,
    )
    model = PlanningModel(
        backend_config=MockAdapterConfig(
            model_key="evaluation-mock",
            model_id="evaluation-mock",
            model_revision="mock-v1",
            capabilities=capabilities,
        ),
        mock_chat_template="mock_chat_v1.txt",
        mock_decoding=DecodingConfig(
            temperature=0.2,
            top_p=1,
            max_tokens=8192,
            seed_base=20260724,
        ),
        mock_max_input_tokens=16384,
    )
    theorem = PromptTheorem.from_text(
        theorem_id="evaluation-fixture",
        split="pilot",
        imports=("Mathlib",),
        lean_statement=THEOREM_STATEMENT,
        proof_a=INFORMAL_PROOF,
        proof_b="Use the constructor of True.",
        paraphrase_a="Immediate.",
        paraphrase_b="Construct truth.",
    )
    plan = build_generation_plan(
        theorems=(theorem,),
        models=(model,),
        matrix=load_condition_matrix(PROJECT_ROOT / "configs" / "experiment" / "conditions.yaml"),
        tier=1,
        prompt_repository=PromptRepository(PROJECT_ROOT / "prompts"),
    )
    planned = next(
        item for item in plan.requests if item.model_input.request.condition == condition
    )
    model_input = planned.model_input
    result = ManifestMockAdapter(model).generate(model_input)
    store = RunArtifactStore(tmp_path, "evaluation-input")
    store.initialize()
    store.write_bytes("requests.jsonl", serialize_generation_requests((planned,)))
    now = datetime(2026, 7, 25, tzinfo=UTC)
    write_generation_response(
        store=store,
        model_input=model_input,
        result=result,
        started_at=now,
        completed_at=now,
        harness_git_commit="a" * 40,
    )
    _write_lean_evidence(store, model_input)
    return (
        store,
        model_input,
        EvaluationPreparationSpec(
            request_id=model_input.request.request_id,
            theorem_statement=THEOREM_STATEMENT,
            supplied_informal_proof=(
                "" if condition == "theorem_only" else INFORMAL_PROOF
            ),
            rubric_text="Classify the proof strategy.",
            rubric_version="rubric-v1",
            extractor_version="extractor-v1",
            signature_evidence=("fixture evidence",),
        ),
    )


def _write_lean_evidence(
    store: RunArtifactStore,
    model_input: ModelInput,
    *,
    candidate_hash: str | None = None,
) -> None:
    request_id = model_input.request.request_id
    response_path = store.path / response_relative_path(request_id)
    response_text = json.loads(response_path.read_text(encoding="utf-8"))["text"]
    root = Path("lean") / request_id
    stdout_path = root / "stdout.txt"
    stderr_path = root / "stderr.txt"
    source_path = root / "Candidate.lean"
    store.write_bytes(stdout_path, b"")
    store.write_bytes(stderr_path, b"")
    store.write_bytes(source_path, b"example : True := by\n  trivial\n")
    result = LeanCheckResult(
        schema_version="1.0",
        request_id=request_id,
        statement_hash_matches=True,
        extraction_status="success",
        parser_status="success",
        elaboration_status="success",
        exit_code=0,
        wall_time_seconds=0.01,
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        declaration_name="evaluation_fixture",
        axioms=("propext",),
        prohibited_token_findings=(),
        failure_category="success",
    )
    store.write_json(root / "check.json", result.model_dump(mode="json"))
    store.write_json(
        root / "check-input.json",
        {
            "schema_version": "1.0",
            "request_id": request_id,
            "candidate_sha256": candidate_hash or _sha256_text(response_text),
            "assembled_source_path": str(source_path),
        },
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
