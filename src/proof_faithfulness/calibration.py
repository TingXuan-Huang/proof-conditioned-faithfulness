"""Calibration-only backend execution and cross-stage compatibility evidence."""

from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from proof_faithfulness.artifacts import RunArtifactStore
from proof_faithfulness.evaluation.inputs import (
    EvaluationInputError,
    prepare_internal_annotation_item,
)
from proof_faithfulness.evaluation.models import EvaluationPreparationSpec
from proof_faithfulness.generation.artifacts import load_verified_response
from proof_faithfulness.generation.budget import BudgetGate
from proof_faithfulness.generation.checking import check_generation_response
from proof_faithfulness.generation.config import (
    PlanningModel,
    load_condition_matrix,
    load_planning_models,
)
from proof_faithfulness.generation.planning import (
    PlannedGeneration,
    PromptTheorem,
    build_generation_plan,
)
from proof_faithfulness.generation.prompts import PromptRepository
from proof_faithfulness.generation.run import GenerationHarness, HarnessResult
from proof_faithfulness.ids import compute_request_id
from proof_faithfulness.lean import (
    DependencyProbeError,
    LeanCandidateSpec,
    probe_dependencies,
)
from proof_faithfulness.models import (
    ChatMessage,
    ModelAdapter,
    ModelInput,
    build_adapter,
    compute_rendered_prompt_hash,
)
from proof_faithfulness.models.config import AdapterConfig, ModelConfig
from proof_faithfulness.models.openai_compat import OpenAICompatibleAdapter
from proof_faithfulness.schema import NonEmptyString


class CalibrationModel(BaseModel):
    """Immutable base for calibration inputs and reports."""

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", frozen=True)


class CalibrationFixture(CalibrationModel):
    """Clearly non-experimental theorem and proof text used for backend checks."""

    schema_version: Literal["1.0"] = "1.0"
    theorem_id: NonEmptyString
    imports: tuple[NonEmptyString, ...]
    declaration_name: NonEmptyString
    declaration: NonEmptyString
    proof_a: NonEmptyString
    proof_b: NonEmptyString
    paraphrase_a: NonEmptyString
    paraphrase_b: NonEmptyString

    def prompt_theorem(self) -> PromptTheorem:
        return PromptTheorem.from_text(
            theorem_id=self.theorem_id,
            split="calibration",
            imports=self.imports,
            lean_statement=self.declaration,
            proof_a=self.proof_a,
            proof_b=self.proof_b,
            paraphrase_a=self.paraphrase_a,
            paraphrase_b=self.paraphrase_b,
        )

    def lean_candidate_spec(self) -> LeanCandidateSpec:
        return LeanCandidateSpec.from_declaration(
            imports=self.imports,
            declaration_name=self.declaration_name,
            declaration=self.declaration,
        )


class CalibrationStage(CalibrationModel):
    status: Literal["passed", "failed", "skipped"]
    detail: NonEmptyString


class CalibrationAssessment(CalibrationModel):
    """Cross-stage result for one terminal generation response."""

    schema_version: Literal["1.0"] = "1.0"
    run_id: NonEmptyString
    request_id: NonEmptyString
    model_key: NonEmptyString
    model_id: NonEmptyString
    revision: NonEmptyString
    response_verified: bool
    response_nonempty: bool
    latency_s: float = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    output_tokens_per_second: float = Field(ge=0)
    usd_cost: Decimal = Field(ge=0)
    lean_check: CalibrationStage
    dependency_probe: CalibrationStage
    evaluation_preparation: CalibrationStage


class RuntimeMetadata(CalibrationModel):
    """Non-secret serving and hardware facts attached after backend execution."""

    schema_version: Literal["1.0"] = "1.0"
    backend_key: NonEmptyString
    model_id: NonEmptyString
    revision: NonEmptyString
    transport: Literal["vllm", "external_api", "pipeline"]
    server_software: NonEmptyString
    server_version: NonEmptyString
    hostname: NonEmptyString
    slurm_job_id: str | None = None
    gpu_name: str | None = None
    gpu_uuid: str | None = None
    gpu_memory_total_mb: int | None = Field(default=None, ge=0)
    peak_gpu_memory_mb: int | None = Field(default=None, ge=0)
    load_time_s: float | None = Field(default=None, ge=0)
    serving_configuration: tuple[NonEmptyString, ...]
    container_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    notes: tuple[str, ...] = ()


_RUNTIME_EVIDENCE_NAMES = frozenset(
    {"gpu-samples.csv", "model-info.json", "server.log", "server-argv.txt"}
)
_MAX_RUNTIME_EVIDENCE_BYTES = 64 * 1024 * 1024


def load_calibration_fixture(path: Path) -> CalibrationFixture:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"Calibration fixture must be a YAML mapping: {path}")
    return CalibrationFixture.model_validate(raw)


def build_calibration_request(
    *,
    fixture: CalibrationFixture,
    models_path: Path,
    conditions_path: Path,
    prompts_root: Path,
) -> tuple[PlannedGeneration, PlanningModel]:
    models = _load_calibration_models(models_path)
    if len(models) != 1:
        raise ValueError("A calibration model file must contain exactly one backend")
    model = models[0]
    plan = build_generation_plan(
        theorems=(fixture.prompt_theorem(),),
        models=models,
        matrix=load_condition_matrix(conditions_path),
        tier=1,
        prompt_repository=PromptRepository(prompts_root),
    )
    matches = tuple(
        item
        for item in plan.requests
        if item.model_input.request.condition == "proof_a"
        and item.model_input.request.sample_index == 0
    )
    if len(matches) != 1:
        raise ValueError("Calibration planning must select exactly proof_a/sample_index=0")
    return _apply_calibration_prompt_recipe(
        planned=matches[0],
        model=model,
        fixture=fixture,
        prompt_repository=PromptRepository(prompts_root),
    ), model


def _load_calibration_models(path: Path) -> tuple[PlanningModel, ...]:
    """Accept either a normal planning file or one standalone backend manifest."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"Calibration model config must be a YAML mapping: {path}")
    if "models" in raw:
        return load_planning_models(path)
    config = TypeAdapter(AdapterConfig).validate_python(raw)
    return (PlanningModel(backend_config=config),)


def _apply_calibration_prompt_recipe(
    *,
    planned: PlannedGeneration,
    model: PlanningModel,
    fixture: CalibrationFixture,
    prompt_repository: PromptRepository,
) -> PlannedGeneration:
    if model.model_id != "deepseek-ai/DeepSeek-Prover-V2-7B":
        return planned
    template = prompt_repository.load("deepseek_prover_v2_v1.txt")
    content = template.render(
        {
            "imports": "".join(f"import {name}\n" for name in fixture.imports).rstrip(),
            "lean_statement": fixture.declaration,
            "informal_proof": fixture.proof_a,
        }
    )
    messages = (ChatMessage(role="user", content=content),)
    original = planned.model_input.request
    identity = {
        "schema_version": original.schema_version,
        "theorem_id": original.theorem_id,
        "statement_hash": original.statement_hash,
        "import_hash": original.import_hash,
        "condition": original.condition,
        "proof_hash": original.proof_hash,
        "prompt_hash": template.sha256,
        "rendered_prompt_hash": compute_rendered_prompt_hash(messages),
        "chat_template_hash": original.chat_template_hash,
        "model_key": original.model_key,
        "model_id": original.model_id,
        "model_revision": original.model_revision,
        "backend_config_hash": original.backend_config_hash,
        "sampling": original.sampling.model_dump(mode="json"),
        "sample_index": original.sample_index,
    }
    request = original.model_copy(
        update={
            "prompt_name": "deepseek_prover_v2",
            "prompt_version": "v1",
            "prompt_hash": template.sha256,
            "rendered_prompt_hash": identity["rendered_prompt_hash"],
            "request_id": compute_request_id(**identity),
        }
    )
    return planned.model_copy(
        update={"model_input": ModelInput(request=request, messages=messages)}
    )


def run_calibration_generation(
    *,
    planned: PlannedGeneration,
    model: PlanningModel,
    store: RunArtifactStore,
    approvals_root: Path,
    approval_scope: str,
    aggregate_ceiling_usd: Decimal = Decimal(500),
    harness_git_commit: str | None = None,
) -> tuple[HarnessResult, HarnessResult]:
    """Generate once and immediately prove terminal-artifact resume is a no-op."""
    _require_calibration_namespace(store)
    budget_gate = None
    config = model.backend_config
    if isinstance(config, ModelConfig) and config.category == "frontier_api":
        budget_gate = BudgetGate(
            store=store,
            approvals_root=approvals_root,
            scope=approval_scope,
            aggregate_ceiling_usd=aggregate_ceiling_usd,
        )
        adapter: ModelAdapter = OpenAICompatibleAdapter(
            config,
            paid_permit_verifier=budget_gate.verify,
            timeout_seconds=600,
        )
    else:
        adapter = build_adapter(config)
    first = GenerationHarness(
        store=store,
        requests=(planned,),
        adapters={model.key: adapter},
        budget_gate=budget_gate,
        harness_git_commit=harness_git_commit,
    ).run()
    second = GenerationHarness(
        store=store,
        requests=(planned,),
        adapters={model.key: adapter},
        budget_gate=budget_gate,
        harness_git_commit=harness_git_commit,
    ).run()
    first_is_terminal = (first.processed, first.skipped) in {(1, 0), (0, 1)}
    second_is_verified_noop = (second.processed, second.skipped) == (0, 1)
    if not first_is_terminal or not second_is_verified_noop:
        raise RuntimeError("Calibration resume did not skip the verified terminal response")
    store.write_json(
        "reports/resume.json",
        {
            "schema_version": "1.0",
            "first": first.model_dump(mode="json"),
            "second": second.model_dump(mode="json"),
        },
    )
    return first, second


def assess_calibration(
    *,
    fixture: CalibrationFixture,
    planned: PlannedGeneration,
    store: RunArtifactStore,
    project_root: Path,
) -> CalibrationAssessment:
    """Run S2, conditional S3, and evaluation preparation for one response."""
    _require_calibration_namespace(store)
    request = planned.model_input.request
    response = load_verified_response(store=store, model_input=planned.model_input)
    if response is None:
        raise ValueError("Calibration response is absent or checksum-invalid")
    outcome = check_generation_response(
        store=store,
        model_input=planned.model_input,
        spec=fixture.lean_candidate_spec(),
        project_root=project_root,
    )
    lean_passed = outcome.result.failure_category == "success"
    lean_stage = CalibrationStage(
        status="passed" if lean_passed else "failed",
        detail=outcome.result.failure_category,
    )

    if lean_passed:
        try:
            dependency = probe_dependencies(
                fixture.lean_candidate_spec(),
                response.text,
                request_id=request.request_id,
                project_root=project_root,
            )
        except DependencyProbeError as error:
            dependency_stage = CalibrationStage(status="failed", detail=str(error))
        else:
            store.write_json(
                f"derived/dependency/{request.request_id}.json",
                asdict(dependency),
            )
            dependency_stage = CalibrationStage(
                status="passed",
                detail=dependency.classification,
            )
    else:
        dependency_stage = CalibrationStage(
            status="skipped",
            detail="trusted Lean check did not pass",
        )

    evaluation_spec = EvaluationPreparationSpec(
        request_id=request.request_id,
        theorem_statement=fixture.declaration,
        supplied_informal_proof=fixture.proof_a,
        rubric_text="Calibration-only strategy evidence; not an experimental annotation.",
        rubric_version="calibration-v1",
        extractor_version="calibration-v1",
        signature_evidence=(),
    )
    try:
        item = prepare_internal_annotation_item(
            store=store,
            model_input=planned.model_input,
            spec=evaluation_spec,
        )
    except EvaluationInputError as error:
        evaluation_stage = CalibrationStage(status="skipped", detail=str(error))
    else:
        store.write_json(
            f"evaluations/calibration/{request.request_id}.json",
            item.model_dump(mode="json"),
        )
        evaluation_stage = CalibrationStage(
            status="passed",
            detail="verified internal annotation item prepared",
        )

    throughput = response.usage.output_tokens / response.latency_s if response.latency_s else 0.0
    report = CalibrationAssessment(
        run_id=store.run_id,
        request_id=request.request_id,
        model_key=request.model_key,
        model_id=request.model_id,
        revision=request.model_revision,
        response_verified=True,
        response_nonempty=bool(response.text.strip()),
        latency_s=response.latency_s,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        output_tokens_per_second=throughput,
        usd_cost=response.usd_cost,
        lean_check=lean_stage,
        dependency_probe=dependency_stage,
        evaluation_preparation=evaluation_stage,
    )
    store.write_json("reports/assessment.json", report.model_dump(mode="json"))
    return report


def attach_runtime_metadata(*, store: RunArtifactStore, metadata_path: Path) -> RuntimeMetadata:
    _require_calibration_namespace(store)
    metadata = RuntimeMetadata.model_validate_json(metadata_path.read_bytes())
    store.write_json("reports/runtime.json", metadata.model_dump(mode="json"))
    return metadata


def attach_runtime_evidence(
    *,
    store: RunArtifactStore,
    evidence_path: Path,
    name: str,
) -> str:
    """Persist bounded, non-secret runtime evidence with a checksum sidecar."""
    _require_calibration_namespace(store)
    if name not in _RUNTIME_EVIDENCE_NAMES:
        raise ValueError(f"Unsupported runtime evidence name: {name}")
    if evidence_path.is_symlink() or not evidence_path.is_file():
        raise ValueError("Runtime evidence must be a regular non-symlink file")
    if evidence_path.stat().st_size > _MAX_RUNTIME_EVIDENCE_BYTES:
        raise ValueError("Runtime evidence exceeds the 64 MiB calibration limit")
    return store.write_bytes(f"reports/evidence/{name}", evidence_path.read_bytes())


def vllm_server_argv(models_path: Path) -> tuple[str, ...]:
    """Return the exact server arguments derived from one pinned local manifest."""
    models = _load_calibration_models(models_path)
    if len(models) != 1 or not isinstance(models[0].backend_config, ModelConfig):
        raise ValueError("A vLLM server manifest must contain one model backend")
    config = models[0].backend_config
    if config.provider != "vllm" or config.base_url is None or config.dtype is None:
        raise ValueError("A vLLM server manifest requires provider=vllm")
    if config.base_url.port is None:
        raise ValueError("A calibration vLLM base_url must pin an explicit port")
    argv = [
        "--model",
        config.model_id,
        "--revision",
        config.require_revision(),
        "--port",
        str(config.base_url.port),
        "--dtype",
        config.dtype,
    ]
    if config.quantization is not None:
        argv.extend(("--quantization", config.quantization))
    argv.extend(config.serving_args)
    return tuple(argv)


def _require_calibration_namespace(store: RunArtifactStore) -> None:
    if store.outputs_root.name != "calibration" or not store.run_id.startswith("calibration-"):
        raise ValueError(
            "Compatibility tests must use outputs/calibration and a calibration-* run ID"
        )
