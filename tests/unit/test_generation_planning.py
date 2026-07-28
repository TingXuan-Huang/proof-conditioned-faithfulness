from __future__ import annotations

import json
import shutil
from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from pydantic import HttpUrl, ValidationError
from typer.testing import CliRunner

from proof_faithfulness.artifacts import RunArtifactStore
from proof_faithfulness.generation.budget import MissingApprovalError
from proof_faithfulness.generation.cli import generation_app
from proof_faithfulness.generation.config import (
    ConditionMatrix,
    PlanningModel,
    load_condition_matrix,
    load_planning_models,
    load_splits,
)
from proof_faithfulness.generation.planning import (
    PromptTheorem,
    build_generation_plan,
    build_repair_input,
    serialize_generation_requests,
    summarize_plan,
)
from proof_faithfulness.generation.prompts import PromptRepository
from proof_faithfulness.models import ModelCapabilities
from proof_faithfulness.models.config import (
    DecodingConfig,
    MockAdapterConfig,
    ModelConfig,
    PricingConfig,
)
from proof_faithfulness.schema import SamplingOption

PROJECT_ROOT = Path(__file__).parents[2]
CONDITIONS = PROJECT_ROOT / "configs" / "experiment" / "conditions.yaml"
SPLITS = PROJECT_ROOT / "configs" / "experiment" / "planning-splits.yaml"
MODELS = PROJECT_ROOT / "configs" / "experiment" / "planning-models.yaml"
PROMPTS = PROJECT_ROOT / "prompts"


def _theorems(count: int = 5) -> tuple[PromptTheorem, ...]:
    return tuple(
        PromptTheorem.from_text(
            theorem_id=f"fixture-{index}",
            split="pilot",
            imports=("Mathlib",),
            lean_statement=f"example : {index} = {index} := by",
            proof_a=f"Use reflexivity for A{index}.",
            proof_b=f"Use equality symmetry twice for B{index}.",
            paraphrase_a=f"Close A{index} reflexively.",
            paraphrase_b=f"Reverse B{index} twice.",
        )
        for index in range(count)
    )


def _theorems_with_ids(theorem_ids: tuple[str, ...]) -> tuple[PromptTheorem, ...]:
    return tuple(
        PromptTheorem.from_text(
            theorem_id=theorem_id,
            split="pilot",
            imports=("Mathlib",),
            lean_statement=f"example : {index} = {index} := by",
            proof_a=f"Use reflexivity for A{index}.",
            proof_b=f"Use equality symmetry twice for B{index}.",
            paraphrase_a=f"Close A{index} reflexively.",
            paraphrase_b=f"Reverse B{index} twice.",
        )
        for index, theorem_id in enumerate(theorem_ids)
    )


def _mock_model(
    *,
    proof_conditioning: bool = True,
    repair: bool = False,
    input_price: Decimal = Decimal(0),
    mock_response_text: str = "by\n  trivial",
) -> PlanningModel:
    capabilities = ModelCapabilities(
        proof_conditioning=proof_conditioning,
        deterministic_seed=True,
        local_inference=True,
        repair=repair,
        cost_reporting=True,
    )
    decoding = DecodingConfig(
        temperature=0.2,
        top_p=1.0,
        max_tokens=8192,
        seed_base=20260724,
    )
    if input_price > 0:
        backend = ModelConfig(
            key="deterministic_mock",
            category="frontier_api",
            provider="openai_compat_api",
            model_id="deterministic-mock",
            revision="mock-v1",
            base_url=HttpUrl("https://api.example.test/v1"),
            api_key_env="FRONTIER_API_KEY",
            chat_template="mock_chat_v1",
            decoding=decoding,
            concurrency=1,
            pricing_usd_per_mtok=PricingConfig(input=input_price, output=Decimal(0)),
            pipeline_commit=None,
            context_window=24576,
        )
        return PlanningModel(backend_config=backend)
    return PlanningModel(
        backend_config=MockAdapterConfig(
            model_key="deterministic_mock",
            model_id="deterministic-mock",
            model_revision="mock-v1",
            response_text=mock_response_text,
            capabilities=capabilities,
        ),
        mock_chat_template="mock_chat_v1.txt",
        mock_decoding=DecodingConfig(
            temperature=0.2,
            top_p=1.0,
            max_tokens=8192,
            seed_base=20260724,
        ),
        mock_max_input_tokens=16384,
    )


def test_tier_one_plan_has_hand_checked_45_plus_15_counts() -> None:
    matrix = load_condition_matrix(CONDITIONS)
    split = next(item for item in load_splits(SPLITS) if item.name == "pilot")
    summary = summarize_plan(
        matrix=matrix,
        split=split,
        models=load_planning_models(MODELS),
        tier=1,
    )

    # Hand check: 5 theorems * 3 conditions * 3 samples = 45;
    # theorem-only capability exposes 5 * 1 * 3 = 15.
    assert {model.model_key: model.requests for model in summary.models} == {
        "proof_conditioned_model": 45,
        "theorem_only_baseline": 15,
    }
    assert summary.total_requests == 60
    assert summary.total_cost_estimate_usd == Decimal(0)
    assert {(item.condition, item.requests) for item in summary.omissions} == {
        ("proof_a", 15),
        ("proof_b", 15),
    }


def test_plan_command_prints_exact_pilot_counts_and_cost() -> None:
    result = CliRunner().invoke(generation_app, ["plan", "--tier", "1", "--split", "pilot"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert [item["requests"] for item in payload["models"]] == [45, 15]
    assert Decimal(payload["total_cost_estimate_usd"]) == 0


def test_plan_check_validates_the_same_cardinality() -> None:
    result = CliRunner().invoke(
        generation_app,
        ["plan-check", "--tier", "1", "--split", "pilot"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["valid"] is True
    assert payload["summary"]["total_requests"] == 60
    assert payload["pilot_tier2_increment"] == {
        "proof_conditioned_model": 30,
        "theorem_only_baseline": 0,
    }


def test_plan_binds_provider_specific_decoding_options() -> None:
    model = _mock_model().model_copy(
        update={
            "mock_decoding": DecodingConfig(
                temperature=0.6,
                top_p=0.95,
                max_tokens=8192,
                seed_base=20260724,
                extra=(SamplingOption(name="top_k", value=20),),
            )
        }
    )
    plan = build_generation_plan(
        theorems=_theorems(count=1),
        models=(model,),
        matrix=load_condition_matrix(CONDITIONS),
        tier=1,
        prompt_repository=PromptRepository(PROMPTS),
    )

    assert plan.requests[0].model_input.request.sampling.extra == (
        SamplingOption(name="top_k", value=20),
    )


def test_plan_check_validates_the_exact_pilot_manifest(tmp_path: Path) -> None:
    split = next(item for item in load_splits(SPLITS) if item.name == "pilot")
    plan = build_generation_plan(
        theorems=_theorems_with_ids(split.theorem_ids),
        models=load_planning_models(MODELS),
        matrix=load_condition_matrix(CONDITIONS),
        tier=1,
        prompt_repository=PromptRepository(PROMPTS),
    )
    manifest = tmp_path / "requests.jsonl"
    manifest.write_bytes(serialize_generation_requests(plan.requests))
    result = CliRunner().invoke(
        generation_app,
        [
            "plan-check",
            "--tier",
            "1",
            "--split",
            "pilot",
            "--requests",
            str(manifest),
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["manifest"]["request_count"] == 60
    assert len(payload["manifest"]["requests_sha256"]) == 64


def test_plan_check_rejects_a_partial_manifest(tmp_path: Path) -> None:
    split = next(item for item in load_splits(SPLITS) if item.name == "pilot")
    plan = build_generation_plan(
        theorems=_theorems_with_ids(split.theorem_ids),
        models=load_planning_models(MODELS),
        matrix=load_condition_matrix(CONDITIONS),
        tier=1,
        prompt_repository=PromptRepository(PROMPTS),
    )
    manifest = tmp_path / "requests.jsonl"
    manifest.write_bytes(serialize_generation_requests(plan.requests[:-1]))
    result = CliRunner().invoke(
        generation_app,
        ["plan-check", "--split", "pilot", "--requests", str(manifest)],
    )
    assert result.exit_code == 2
    assert "exact configured plan" in result.output


def test_plan_check_rejects_a_29_theorem_core(tmp_path: Path) -> None:
    raw = yaml.safe_load(SPLITS.read_text(encoding="utf-8"))
    next(item for item in raw["splits"] if item["name"] == "core")["theorem_count"] = 29
    path = tmp_path / "splits.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    result = CliRunner().invoke(
        generation_app,
        ["plan-check", "--split", "core", "--splits", str(path)],
    )
    assert result.exit_code == 2
    assert "exactly 30" in result.output


def test_tier_two_adds_exactly_30_pilot_requests_to_conditioned_model() -> None:
    matrix = load_condition_matrix(CONDITIONS)
    split = next(item for item in load_splits(SPLITS) if item.name == "pilot")
    models = load_planning_models(MODELS)
    tier_one = summarize_plan(matrix=matrix, split=split, models=models, tier=1)
    tier_two = summarize_plan(matrix=matrix, split=split, models=models, tier=2)
    by_key_one = {model.model_key: model.requests for model in tier_one.models}
    by_key_two = {model.model_key: model.requests for model in tier_two.models}
    assert by_key_two["proof_conditioned_model"] - by_key_one["proof_conditioned_model"] == 30
    assert by_key_two["theorem_only_baseline"] - by_key_one["theorem_only_baseline"] == 0


@pytest.mark.parametrize("condition_index", range(9))
def test_matrix_rejects_a_change_to_every_tier_condition(condition_index: int) -> None:
    raw = yaml.safe_load(CONDITIONS.read_text(encoding="utf-8"))
    raw["conditions"][condition_index]["key"] += "_changed"
    with pytest.raises(ValidationError, match="fixed T1-T4 matrix"):
        ConditionMatrix.model_validate(raw)


def test_matrix_rejects_non_three_sample_count() -> None:
    raw = yaml.safe_load(CONDITIONS.read_text(encoding="utf-8"))
    raw["samples_per_cell"] = 2
    with pytest.raises(ValidationError, match="exactly 3 samples"):
        ConditionMatrix.model_validate(raw)


def test_request_enumeration_is_unique_and_uses_seed_recipe() -> None:
    plan = build_generation_plan(
        theorems=_theorems(),
        models=(_mock_model(),),
        matrix=load_condition_matrix(CONDITIONS),
        tier=1,
        prompt_repository=PromptRepository(PROMPTS),
    )
    request_ids = [item.model_input.request.request_id for item in plan.requests]
    assert len(request_ids) == 45
    assert len(set(request_ids)) == 45
    assert {item.model_input.request.sampling.seed for item in plan.requests} == {
        20260724,
        20260725,
        20260726,
    }


def test_prompt_theorem_rejects_tampered_source_hashes() -> None:
    payload = _theorems(1)[0].model_dump(mode="json")
    payload["statement_hash"] = "f" * 64
    with pytest.raises(ValidationError, match="statement_hash"):
        PromptTheorem.model_validate(payload)


def test_plan_rejects_duplicate_ids_and_mixed_splits() -> None:
    theorem = _theorems(1)[0]
    inputs = {
        "models": (_mock_model(),),
        "matrix": load_condition_matrix(CONDITIONS),
        "tier": 1,
        "prompt_repository": PromptRepository(PROMPTS),
    }
    with pytest.raises(ValueError, match="IDs must be unique"):
        build_generation_plan(theorems=(theorem, theorem), **inputs)
    core_theorem = theorem.model_copy(update={"theorem_id": "core-fixture", "split": "core"})
    with pytest.raises(ValueError, match="one split"):
        build_generation_plan(theorems=(theorem, core_theorem), **inputs)


def test_planning_rejects_self_asserted_paid_idempotency() -> None:
    paid = _mock_model(input_price=Decimal(1))
    payload = paid.model_dump(mode="json")
    payload["paid_idempotency_verified"] = True
    with pytest.raises(ValidationError, match="paid_idempotency_verified"):
        PlanningModel.model_validate(payload)


def test_theorem_only_prompt_never_contains_either_informal_proof() -> None:
    theorem = _theorems(1)[0]
    plan = build_generation_plan(
        theorems=(theorem,),
        models=(_mock_model(),),
        matrix=load_condition_matrix(CONDITIONS),
        tier=1,
        prompt_repository=PromptRepository(PROMPTS),
    )
    theorem_only = next(
        item for item in plan.requests if item.model_input.request.condition == "theorem_only"
    )
    rendered = "\n".join(message.content for message in theorem_only.model_input.messages)
    assert theorem.proof_a not in rendered
    assert theorem.proof_b not in rendered


def test_editing_raw_prompt_bytes_changes_request_identity(tmp_path: Path) -> None:
    prompt_copy = tmp_path / "prompts"
    shutil.copytree(PROMPTS, prompt_copy)
    inputs = {
        "theorems": _theorems(1),
        "models": (_mock_model(),),
        "matrix": load_condition_matrix(CONDITIONS),
        "tier": 1,
    }
    before = build_generation_plan(
        **inputs,
        prompt_repository=PromptRepository(prompt_copy),
    )
    theorem_template = prompt_copy / "theorem_only_v1.txt"
    theorem_template.write_text(
        theorem_template.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )
    after = build_generation_plan(
        **inputs,
        prompt_repository=PromptRepository(prompt_copy),
    )
    before_id = next(
        item.model_input.request.request_id
        for item in before.requests
        if item.model_input.request.condition == "theorem_only"
    )
    after_id = next(
        item.model_input.request.request_id
        for item in after.requests
        if item.model_input.request.condition == "theorem_only"
    )
    assert before_id != after_id


def test_inserted_lean_double_braces_are_not_parsed_as_template_syntax() -> None:
    theorem = PromptTheorem.from_text(
        theorem_id="double-braces",
        split="pilot",
        imports=("Mathlib",),
        lean_statement="example {{alpha : Type}} (x : alpha) : x = x := by",
        proof_a="Reflexivity.",
        proof_b="Use Eq.refl.",
        paraphrase_a="Immediate.",
        paraphrase_b="Construct equality.",
    )
    request = build_generation_plan(
        theorems=(theorem,),
        models=(_mock_model(),),
        matrix=load_condition_matrix(CONDITIONS),
        tier=1,
        prompt_repository=PromptRepository(PROMPTS),
    ).requests[0]
    assert "{{alpha : Type}}" in request.model_input.messages[-1].content


def test_backend_hash_and_request_id_change_with_pricing_or_config() -> None:
    theorem = _theorems(1)
    matrix = load_condition_matrix(CONDITIONS)
    repository = PromptRepository(PROMPTS)
    first_model = _mock_model(input_price=Decimal(1))
    repriced_model = _mock_model(input_price=Decimal(2))
    reconfigured_model = _mock_model(mock_response_text="by exact True.intro")
    first = build_generation_plan(
        theorems=theorem,
        models=(first_model,),
        matrix=matrix,
        tier=1,
        prompt_repository=repository,
    ).requests[0]
    repriced = build_generation_plan(
        theorems=theorem,
        models=(repriced_model,),
        matrix=matrix,
        tier=1,
        prompt_repository=repository,
    ).requests[0]
    reconfigured = build_generation_plan(
        theorems=theorem,
        models=(reconfigured_model,),
        matrix=matrix,
        tier=1,
        prompt_repository=repository,
    ).requests[0]
    assert (
        len(
            {
                first_model.backend_config_hash,
                repriced_model.backend_config_hash,
                reconfigured_model.backend_config_hash,
            }
        )
        == 3
    )
    assert (
        len(
            {
                first.model_input.request.request_id,
                repriced.model_input.request.request_id,
                reconfigured.model_input.request.request_id,
            }
        )
        == 3
    )


def test_default_planned_mock_manifest_is_runnable(tmp_path: Path) -> None:
    model = load_planning_models(MODELS)[0]
    request = build_generation_plan(
        theorems=_theorems(1),
        models=(model,),
        matrix=load_condition_matrix(CONDITIONS),
        tier=1,
        prompt_repository=PromptRepository(PROMPTS),
    ).requests[0]
    manifest = tmp_path / "requests.jsonl"
    manifest.write_text(request.model_dump_json() + "\n", encoding="utf-8")
    result = CliRunner().invoke(
        generation_app,
        [
            "run",
            "--requests",
            str(manifest),
            "--run-id",
            "default-manifest",
            "--outputs-root",
            str(tmp_path / "outputs"),
            "--allow-dirty-worktree",
        ],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["processed"] == 1


def test_cli_paid_manifest_refuses_before_secret_or_transport_without_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("FRONTIER_API_KEY", raising=False)
    model = _mock_model(input_price=Decimal(1))
    request = build_generation_plan(
        theorems=_theorems(1),
        models=(model,),
        matrix=load_condition_matrix(CONDITIONS),
        tier=1,
        prompt_repository=PromptRepository(PROMPTS),
    ).requests[0]
    manifest = tmp_path / "paid-requests.jsonl"
    manifest.write_bytes(serialize_generation_requests((request,)))
    models_path = tmp_path / "paid-models.yaml"
    models_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "models": [model.model_dump(mode="json", exclude={"backend_config_hash"})],
            }
        ),
        encoding="utf-8",
    )
    result = CliRunner().invoke(
        generation_app,
        [
            "run",
            "--requests",
            str(manifest),
            "--models",
            str(models_path),
            "--run-id",
            "paid-refusal",
            "--outputs-root",
            str(tmp_path / "outputs"),
            "--approvals-root",
            str(tmp_path / "approvals"),
            "--allow-dirty-worktree",
        ],
    )
    assert result.exit_code == 1, result.output
    assert isinstance(result.exception, MissingApprovalError)
    run = RunArtifactStore(tmp_path / "outputs", "paid-refusal")
    assert not any((run.path / "responses").glob("*/transport-attempts.json"))


def test_repair_round_keeps_exact_diagnostic_and_is_capped_at_two() -> None:
    original = (
        build_generation_plan(
            theorems=_theorems(1),
            models=(_mock_model(repair=True),),
            matrix=load_condition_matrix(CONDITIONS),
            tier=1,
            prompt_repository=PromptRepository(PROMPTS),
        )
        .requests[0]
        .model_input
    )
    diagnostic = "error: type mismatch\n  exact fixture diagnostic  "
    repaired = build_repair_input(
        original=original,
        previous_candidate="by\n  rflx",
        compiler_diagnostic=diagnostic,
        round_index=2,
        prompt_repository=PromptRepository(PROMPTS),
    )
    assert diagnostic in repaired.messages[-1].content
    assert repaired.request.condition.endswith("repair_2")
    assert repaired.request.request_id != original.request.request_id
    with pytest.raises(ValueError, match="must be 1 or 2"):
        build_repair_input(
            original=original,
            previous_candidate="by rfl",
            compiler_diagnostic=diagnostic,
            round_index=3,
            prompt_repository=PromptRepository(PROMPTS),
        )
