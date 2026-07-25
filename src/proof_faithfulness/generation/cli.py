"""Typer commands for offline planning and mock generation runs."""

from __future__ import annotations

import json
from collections.abc import Callable
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from proof_faithfulness.artifacts import RunArtifactStore, sha256_bytes
from proof_faithfulness.generation.budget import BudgetGate
from proof_faithfulness.generation.config import (
    ConditionMatrix,
    PlanningModel,
    load_condition_matrix,
    load_planning_models,
    load_splits,
)
from proof_faithfulness.generation.planning import (
    PlannedGeneration,
    PlanSummary,
    serialize_generation_requests,
    summarize_plan,
)
from proof_faithfulness.generation.run import GenerationHarness, PaidModelAdapter
from proof_faithfulness.models import (
    AdapterResult,
    ModelAdapter,
    ModelCapabilities,
    ModelConfig,
    ModelInput,
    build_adapter,
)
from proof_faithfulness.models.base import (
    validate_request_identity,
    validate_sampling_recipe,
)
from proof_faithfulness.models.openai_compat import OpenAICompatibleAdapter
from proof_faithfulness.schema import TokenUsage

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONDITIONS = PROJECT_ROOT / "configs" / "experiment" / "conditions.yaml"
DEFAULT_SPLITS = PROJECT_ROOT / "configs" / "experiment" / "planning-splits.yaml"
DEFAULT_MODELS = PROJECT_ROOT / "configs" / "experiment" / "planning-models.yaml"

generation_app = typer.Typer(help="Plan and execute generation batches.")


class ManifestMockAdapter:
    """Offline adapter bound to one fully derived planning-model identity."""

    def __init__(self, model: PlanningModel) -> None:
        if model.adapter != "mock" or model.provider != "mock" or model.paid:
            raise ValueError("Offline run requires an unpaid mock planning model")
        self._model = model

    @property
    def name(self) -> str:
        return self._model.adapter

    @property
    def capabilities(self) -> ModelCapabilities:
        return self._model.capabilities

    def generate(self, model_input: ModelInput) -> AdapterResult:
        validate_request_identity(
            model_input,
            adapter_name=self.name,
            provider=self._model.provider,
            model_key=self._model.key,
            model_id=self._model.model_id,
            model_revision=self._model.revision,
            backend_config_hash=self._model.backend_config_hash,
            capabilities=self.capabilities,
        )
        decoding = self._model.decoding
        validate_sampling_recipe(
            model_input,
            temperature=decoding.temperature,
            top_p=decoding.top_p,
            max_tokens=decoding.max_tokens,
            seed_base=decoding.seed_base,
        )
        response = {
            "id": f"mock-{model_input.request.request_id[:16]}",
            "text": self._model.mock_response_text,
            "finish_reason": "stop",
        }
        raw = json.dumps(response, ensure_ascii=True, sort_keys=True).encode("utf-8") + b"\n"
        return AdapterResult(
            request_id=model_input.request.request_id,
            text=self._model.mock_response_text,
            raw_response=raw,
            provider_request_id=response["id"],
            token_usage=TokenUsage(input_tokens=0, output_tokens=0),
            usd_cost=Decimal(0),
            finish_reason="stop",
        )


@generation_app.command("plan")
def plan_command(
    tier: Annotated[int, typer.Option("--tier", min=1, max=4)] = 1,
    split: Annotated[str, typer.Option("--split")] = "pilot",
    conditions_path: Annotated[Path, typer.Option("--conditions")] = DEFAULT_CONDITIONS,
    splits_path: Annotated[Path, typer.Option("--splits")] = DEFAULT_SPLITS,
    models_path: Annotated[Path, typer.Option("--models")] = DEFAULT_MODELS,
) -> None:
    """Prints exact capability-aware counts and conservative cost estimates."""
    summary = _load_summary(
        tier=tier,
        split_name=split,
        conditions_path=conditions_path,
        splits_path=splits_path,
        models_path=models_path,
    )
    typer.echo(json.dumps(summary.model_dump(mode="json"), indent=2, sort_keys=True))


@generation_app.command("plan-check")
def plan_check_command(
    tier: Annotated[int, typer.Option("--tier", min=1, max=4)] = 1,
    split: Annotated[str, typer.Option("--split")] = "pilot",
    conditions_path: Annotated[Path, typer.Option("--conditions")] = DEFAULT_CONDITIONS,
    splits_path: Annotated[Path, typer.Option("--splits")] = DEFAULT_SPLITS,
    models_path: Annotated[Path, typer.Option("--models")] = DEFAULT_MODELS,
    requests_path: Annotated[Path | None, typer.Option("--requests")] = None,
) -> None:
    """Validates plan cardinality, uniqueness inputs, and reported omissions."""
    summary = _load_summary(
        tier=tier,
        split_name=split,
        conditions_path=conditions_path,
        splits_path=splits_path,
        models_path=models_path,
    )
    _load_or_bad_parameter(load_condition_matrix, conditions_path, "conditions")
    models = _load_or_bad_parameter(load_planning_models, models_path, "models")
    expected_by_model = _expected_counts(
        models=models,
        theorem_count=summary.theorem_count,
        tier=tier,
    )
    actual_by_model = {model.model_key: model.requests for model in summary.models}
    if actual_by_model != expected_by_model:
        raise typer.BadParameter("Plan counts do not match the condition matrix")
    if split == "pilot":
        _validate_pilot_counts(summary=summary, models=models)
    expected_theorem_count = {"pilot": 5, "core": 30}.get(split)
    if expected_theorem_count is not None and summary.theorem_count != expected_theorem_count:
        raise typer.BadParameter(f"{split} must contain exactly {expected_theorem_count} theorems")
    tier_two_increment = {
        model.key: (30 if model.capabilities.proof_conditioning else 0) for model in models
    }
    payload = {
        "valid": True,
        "pilot_tier2_increment": tier_two_increment if split == "pilot" else None,
        "summary": summary.model_dump(mode="json"),
    }
    if requests_path is not None:
        requests = _read_requests(requests_path)
        split_config = next(item for item in load_splits(splits_path) if item.name == split)
        _validate_manifest_against_plan(
            requests=requests,
            matrix=load_condition_matrix(conditions_path),
            models=models,
            theorem_ids=split_config.theorem_ids,
            tier=tier,
        )
        canonical = serialize_generation_requests(requests)
        payload["manifest"] = {
            "request_count": len(requests),
            "requests_sha256": sha256_bytes(canonical),
        }
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


@generation_app.command("run")
def run_command(
    requests_path: Annotated[
        Path,
        typer.Option("--requests", help="JSONL of PlannedGeneration records."),
    ],
    run_id: Annotated[str, typer.Option("--run-id")],
    outputs_root: Annotated[Path, typer.Option("--outputs-root")] = Path("outputs"),
    models_path: Annotated[Path, typer.Option("--models")] = DEFAULT_MODELS,
    approvals_root: Annotated[Path, typer.Option("--approvals-root")] = Path("approvals"),
    approval_scope: Annotated[str, typer.Option("--approval-scope")] = "pilot-tier1",
    aggregate_ceiling_usd: Annotated[
        str,
        typer.Option("--aggregate-ceiling-usd"),
    ] = "500",
    allow_dirty_worktree: Annotated[
        bool,
        typer.Option("--allow-dirty-worktree"),
    ] = False,
) -> None:
    """Executes an exact request manifest through its pinned backend configs."""
    store = RunArtifactStore(outputs_root, run_id)
    try:
        requests = _read_requests(requests_path)
        models = load_planning_models(models_path)
        ceiling = Decimal(aggregate_ceiling_usd)
        budget_gate = (
            BudgetGate(
                store=store,
                approvals_root=approvals_root,
                scope=approval_scope,
                aggregate_ceiling_usd=ceiling,
            )
            if any(item.paid for item in requests)
            else None
        )
        adapters = _configured_adapters(
            requests=requests,
            models=models,
            budget_gate=budget_gate,
        )
    except (InvalidOperation, OSError, TypeError, ValueError, ValidationError) as error:
        raise typer.BadParameter(
            "Invalid request manifest or backend configuration", param_hint="--requests"
        ) from error
    result = GenerationHarness(
        store=store,
        requests=requests,
        adapters=adapters,
        budget_gate=budget_gate,
        allow_dirty_worktree=allow_dirty_worktree,
    ).run_with_signal_handlers()
    typer.echo(json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True))


def _load_summary(
    *,
    tier: int,
    split_name: str,
    conditions_path: Path,
    splits_path: Path,
    models_path: Path,
) -> PlanSummary:
    matrix = _load_or_bad_parameter(load_condition_matrix, conditions_path, "conditions")
    splits = _load_or_bad_parameter(load_splits, splits_path, "splits")
    models = _load_or_bad_parameter(load_planning_models, models_path, "models")
    split = next((candidate for candidate in splits if candidate.name == split_name), None)
    if split is None:
        raise typer.BadParameter(f"Unknown split: {split_name}", param_hint="--split")
    return summarize_plan(matrix=matrix, split=split, models=models, tier=tier)


def _expected_counts(
    *,
    models: tuple[PlanningModel, ...],
    theorem_count: int,
    tier: int,
) -> dict[str, int]:
    conditioned_cells = {1: 3, 2: 5, 3: 7, 4: 9}[tier]
    expected: dict[str, int] = {}
    for model in models:
        condition_count = conditioned_cells if model.capabilities.proof_conditioning else 1
        expected[model.key] = condition_count * theorem_count * 3
    return expected


def _validate_pilot_counts(
    *,
    summary: PlanSummary,
    models: tuple[PlanningModel, ...],
) -> None:
    if summary.theorem_count != 5:
        raise typer.BadParameter("Pilot planning must contain exactly five theorems")
    by_key = {entry.model_key: entry.requests for entry in summary.models}
    proof_counts = [by_key[model.key] for model in models if model.capabilities.proof_conditioning]
    baseline_counts = [
        by_key[model.key] for model in models if not model.capabilities.proof_conditioning
    ]
    expected_conditioned = {1: 45, 2: 75, 3: 105, 4: 135}[summary.tier]
    if not proof_counts or any(count != expected_conditioned for count in proof_counts):
        raise typer.BadParameter("Pilot proof-conditioned request count is invalid")
    if not baseline_counts or any(count != 15 for count in baseline_counts):
        raise typer.BadParameter("Pilot theorem-only request count is invalid")


def _read_requests(path: Path) -> tuple[PlannedGeneration, ...]:
    requests: list[PlannedGeneration] = []
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                raise ValueError(f"Blank request line: {line_number}")
            requests.append(PlannedGeneration.model_validate_json(line))
    if not requests:
        raise ValueError("Request manifest is empty")
    return tuple(requests)


def _validate_manifest_against_plan(
    *,
    requests: tuple[PlannedGeneration, ...],
    matrix: ConditionMatrix,
    models: tuple[PlanningModel, ...],
    theorem_ids: tuple[str, ...],
    tier: int,
) -> None:
    if not theorem_ids:
        raise typer.BadParameter("Manifest checking requires explicit split theorem IDs")
    models_by_key = {model.key: model for model in models}
    actual: set[tuple[str, str, str, int]] = set()
    for item in requests:
        request = item.model_input.request
        model = models_by_key.get(request.model_key)
        if model is None or request.backend_config_hash != model.backend_config_hash:
            raise typer.BadParameter("Manifest contains an unconfigured backend identity")
        if item.max_cost_usd != model.maximum_request_usd() or item.paid != model.paid:
            raise typer.BadParameter("Manifest cost reservation differs from model config")
        key = (request.model_key, request.theorem_id, request.condition, request.sample_index)
        if key in actual:
            raise typer.BadParameter("Manifest contains a duplicate experimental cell")
        actual.add(key)
    expected = {
        (model.key, theorem_id, condition.key, sample_index)
        for model in models
        for condition in matrix.through_tier(tier)
        if model.capabilities.proof_conditioning or not condition.requires_proof_conditioning
        for theorem_id in theorem_ids
        for sample_index in range(3)
    }
    if actual != expected:
        raise typer.BadParameter("Manifest does not enumerate the exact configured plan")


def _configured_adapters(
    *,
    requests: tuple[PlannedGeneration, ...],
    models: tuple[PlanningModel, ...],
    budget_gate: BudgetGate | None,
) -> dict[str, ModelAdapter | PaidModelAdapter]:
    adapters: dict[str, ModelAdapter | PaidModelAdapter] = {}
    models_by_key = {model.key: model for model in models}
    for item in requests:
        request = item.model_input.request
        if request.model_key in adapters:
            continue
        model = models_by_key.get(request.model_key)
        if model is None:
            raise ValueError(f"Request model is absent from planning config: {request.model_key}")
        if request.backend_config_hash != model.backend_config_hash:
            raise ValueError("Planning backend identity does not match the request")
        if item.max_cost_usd != model.maximum_request_usd() or item.paid != model.paid:
            raise ValueError("Planned reservation does not match the backend config")
        config = model.backend_config
        if isinstance(config, ModelConfig) and config.category == "frontier_api":
            if budget_gate is None:
                raise ValueError("Frontier API generation requires a budget gate")
            adapters[request.model_key] = OpenAICompatibleAdapter(
                config,
                paid_permit_verifier=budget_gate.verify,
            )
        else:
            adapters[request.model_key] = build_adapter(config)
    return adapters


def _load_or_bad_parameter[LoadResult](
    loader: Callable[[Path], LoadResult],
    path: Path,
    name: str,
) -> LoadResult:
    try:
        return loader(path)
    except (OSError, TypeError, ValueError) as error:
        raise typer.BadParameter(f"Invalid generation {name} configuration: {path}") from error
