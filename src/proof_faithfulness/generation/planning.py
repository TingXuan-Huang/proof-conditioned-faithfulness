"""Deterministic request enumeration and capability-aware plan summaries."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from proof_faithfulness.generation.config import (
    ConditionConfig,
    ConditionMatrix,
    PlanningModel,
    SplitPlanningConfig,
)
from proof_faithfulness.generation.prompts import (
    PromptRepository,
    render_messages,
    template_name_and_version,
)
from proof_faithfulness.ids import compute_request_id
from proof_faithfulness.models import ModelInput, compute_rendered_prompt_hash
from proof_faithfulness.schema import GenerationRequest, Hash, NonEmptyString, SamplingParameters


class PlanningContract(BaseModel):
    """Immutable base for request-plan artifacts."""

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", frozen=True)


class PromptTheorem(PlanningContract):
    """Trusted theorem text plus both promptable proof variants."""

    theorem_id: NonEmptyString
    split: NonEmptyString
    imports: tuple[NonEmptyString, ...]
    lean_statement: NonEmptyString
    statement_hash: Hash
    import_hash: Hash
    proof_a: NonEmptyString
    proof_b: NonEmptyString
    paraphrase_a: NonEmptyString
    paraphrase_b: NonEmptyString

    @model_validator(mode="after")
    def validate_imports(self) -> PromptTheorem:
        if not self.imports:
            raise ValueError("At least one Lean import is required")
        if len(set(self.imports)) != len(self.imports):
            raise ValueError("Lean imports must be unique")
        expected_statement_hash = _sha256_text(self.lean_statement)
        if self.statement_hash != expected_statement_hash:
            raise ValueError("statement_hash does not match lean_statement")
        import_bytes = "".join(f"import {name}\n" for name in self.imports).encode("utf-8")
        if self.import_hash != hashlib.sha256(import_bytes).hexdigest():
            raise ValueError("import_hash does not match imports")
        return self

    @classmethod
    def from_text(
        cls,
        *,
        theorem_id: str,
        split: str,
        imports: tuple[str, ...],
        lean_statement: str,
        proof_a: str,
        proof_b: str,
        paraphrase_a: str,
        paraphrase_b: str,
    ) -> PromptTheorem:
        """Builds a fixture theorem using raw-text SHA-256 identities."""
        import_bytes = "".join(f"import {name}\n" for name in imports).encode("utf-8")
        return cls(
            theorem_id=theorem_id,
            split=split,
            imports=imports,
            lean_statement=lean_statement,
            statement_hash=_sha256_text(lean_statement),
            import_hash=hashlib.sha256(import_bytes).hexdigest(),
            proof_a=proof_a,
            proof_b=proof_b,
            paraphrase_a=paraphrase_a,
            paraphrase_b=paraphrase_b,
        )

    def selected_proof(self, condition: ConditionConfig) -> str:
        """Returns the exact proof text named by a configured condition."""
        if condition.proof_source == "none":
            return ""
        if condition.proof_id == "A":
            return self.proof_a if condition.proof_source == "proof" else self.paraphrase_a
        if condition.proof_id == "B":
            return self.proof_b if condition.proof_source == "proof" else self.paraphrase_b
        raise ValueError(f"Condition does not bind a proof variant: {condition.key}")


class PlannedGeneration(PlanningContract):
    """One fully rendered request and its pre-request cost reservation."""

    model_input: ModelInput
    max_cost_usd: Decimal = Field(ge=0)
    paid: bool
    paid_idempotency_verified: Literal[False] = False

    @model_validator(mode="after")
    def validate_cost_classification(self) -> PlannedGeneration:
        if self.paid != (self.max_cost_usd > 0):
            raise ValueError("paid must exactly match a nonzero cost reservation")
        return self


class PlanOmission(PlanningContract):
    """One capability-based omission reported before execution."""

    model_key: NonEmptyString
    condition: NonEmptyString
    requests: int = Field(gt=0)
    reason: Literal["proof_conditioning_unsupported"]


class ModelPlanSummary(PlanningContract):
    """Per-model count and conservative cost estimate."""

    model_key: NonEmptyString
    requests: int = Field(ge=0)
    cost_estimate_usd: Decimal = Field(ge=0)


class PlanSummary(PlanningContract):
    """Human-readable pre-spend request summary."""

    schema_version: Literal["1.0"] = "1.0"
    split: NonEmptyString
    split_status: Literal["proposed", "human_approved", "frozen"]
    tier: int = Field(ge=1, le=4)
    theorem_count: int = Field(gt=0)
    models: tuple[ModelPlanSummary, ...]
    omissions: tuple[PlanOmission, ...]
    total_requests: int = Field(ge=0)
    total_cost_estimate_usd: Decimal = Field(ge=0)


class GenerationPlan(PlanningContract):
    """Ordered request list with all capability omissions retained."""

    requests: tuple[PlannedGeneration, ...]
    omissions: tuple[PlanOmission, ...]

    @model_validator(mode="after")
    def reject_duplicate_request_ids(self) -> GenerationPlan:
        request_ids = tuple(item.model_input.request.request_id for item in self.requests)
        if len(set(request_ids)) != len(request_ids):
            raise ValueError("Generation plan contains duplicate request IDs")
        return self


def summarize_plan(
    *,
    matrix: ConditionMatrix,
    split: SplitPlanningConfig,
    models: tuple[PlanningModel, ...],
    tier: int,
) -> PlanSummary:
    """Computes exact per-model request counts and every omission."""
    conditions = matrix.through_tier(tier)
    summaries: list[ModelPlanSummary] = []
    omissions: list[PlanOmission] = []
    for model in models:
        included_count = 0
        for condition in conditions:
            condition_count = split.theorem_count * matrix.samples_per_cell
            if condition.requires_proof_conditioning and not model.capabilities.proof_conditioning:
                omissions.append(
                    PlanOmission(
                        model_key=model.key,
                        condition=condition.key,
                        requests=condition_count,
                        reason="proof_conditioning_unsupported",
                    )
                )
                continue
            included_count += condition_count
        summaries.append(
            ModelPlanSummary(
                model_key=model.key,
                requests=included_count,
                cost_estimate_usd=included_count * model.maximum_request_usd(),
            )
        )
    return PlanSummary(
        split=split.name,
        split_status=split.status,
        tier=tier,
        theorem_count=split.theorem_count,
        models=tuple(summaries),
        omissions=tuple(omissions),
        total_requests=sum(model.requests for model in summaries),
        total_cost_estimate_usd=sum(
            (model.cost_estimate_usd for model in summaries),
            start=Decimal(0),
        ),
    )


def build_generation_plan(
    *,
    theorems: tuple[PromptTheorem, ...],
    models: tuple[PlanningModel, ...],
    matrix: ConditionMatrix,
    tier: int,
    prompt_repository: PromptRepository,
) -> GenerationPlan:
    """Enumerates fully identified requests in stable model/theorem/cell order."""
    if not theorems:
        raise ValueError("At least one theorem is required")
    theorem_ids = tuple(theorem.theorem_id for theorem in theorems)
    if len(set(theorem_ids)) != len(theorem_ids):
        raise ValueError("Generation-plan theorem IDs must be unique")
    splits = {theorem.split for theorem in theorems}
    if len(splits) != 1:
        raise ValueError("Generation-plan theorems must belong to one split")
    conditions = matrix.through_tier(tier)
    requests: list[PlannedGeneration] = []
    omissions: list[PlanOmission] = []
    for model in models:
        for condition in conditions:
            if condition.requires_proof_conditioning and not model.capabilities.proof_conditioning:
                omissions.append(
                    PlanOmission(
                        model_key=model.key,
                        condition=condition.key,
                        requests=len(theorems) * matrix.samples_per_cell,
                        reason="proof_conditioning_unsupported",
                    )
                )
                continue
            for theorem in theorems:
                for sample_index in range(matrix.samples_per_cell):
                    requests.append(
                        _build_request(
                            theorem=theorem,
                            model=model,
                            condition=condition,
                            sample_index=sample_index,
                            prompt_repository=prompt_repository,
                        )
                    )
    return GenerationPlan(requests=tuple(requests), omissions=tuple(omissions))


def serialize_generation_requests(requests: tuple[PlannedGeneration, ...]) -> bytes:
    """Serializes the exact canonical JSONL persisted and approved for a run."""
    if not requests:
        raise ValueError("A request manifest cannot be empty")
    return b"".join(
        (
            json.dumps(
                item.model_dump(mode="json"),
                allow_nan=False,
                ensure_ascii=True,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
            + b"\n"
        )
        for item in requests
    )


def build_repair_input(
    *,
    original: ModelInput,
    previous_candidate: str,
    compiler_diagnostic: str,
    round_index: int,
    prompt_repository: PromptRepository,
) -> ModelInput:
    """Builds one compiler-feedback request without altering the diagnostic.

    Repair is a separate track and is limited to rounds one and two. The caller
    persists each returned request through the ordinary response writer.
    """
    if round_index not in {1, 2}:
        raise ValueError("Repair round_index must be 1 or 2")
    if "repair" not in original.request.capability_flags:
        raise ValueError("The model request does not declare repair capability")
    if not compiler_diagnostic:
        raise ValueError("A repair request requires the exact compiler diagnostic")
    repair = prompt_repository.load("repair_v1.txt")
    user_text = repair.render(
        {
            "previous_candidate": previous_candidate,
            "compiler_diagnostic": compiler_diagnostic,
        }
    )
    messages = (
        original.messages[0],
        original.messages[1],
        original.messages[1].model_copy(
            update={"role": "assistant", "content": previous_candidate}
        ),
        original.messages[1].model_copy(update={"content": user_text}),
    )
    request = original.request
    identity = {
        "schema_version": request.schema_version,
        "theorem_id": request.theorem_id,
        "statement_hash": request.statement_hash,
        "import_hash": request.import_hash,
        "condition": f"{request.condition}_repair_{round_index}",
        "proof_hash": request.proof_hash,
        "prompt_hash": repair.sha256,
        "rendered_prompt_hash": compute_rendered_prompt_hash(messages),
        "chat_template_hash": request.chat_template_hash,
        "model_key": request.model_key,
        "model_id": request.model_id,
        "model_revision": request.model_revision,
        "backend_config_hash": request.backend_config_hash,
        "sampling": request.sampling.model_dump(mode="json"),
        "sample_index": request.sample_index,
    }
    repair_request = GenerationRequest.model_validate(
        {
            **request.model_dump(mode="json"),
            **identity,
            "prompt_name": "repair",
            "prompt_version": "v1",
            "request_id": compute_request_id(**identity),
        }
    )
    return ModelInput(request=repair_request, messages=messages)


def _build_request(
    *,
    theorem: PromptTheorem,
    model: PlanningModel,
    condition: ConditionConfig,
    sample_index: int,
    prompt_repository: PromptRepository,
) -> PlannedGeneration:
    proof = theorem.selected_proof(condition)
    variables = {
        "lean_statement": theorem.lean_statement,
        "imports": "".join(f"import {name}\n" for name in theorem.imports).rstrip("\n"),
        "informal_proof": proof,
    }
    messages, prompt_template = render_messages(
        repository=prompt_repository,
        system_template=condition.system_template,
        user_template=condition.user_template,
        variables=variables,
    )
    chat_template = prompt_repository.load(model.chat_template)
    prompt_name, prompt_version = template_name_and_version(condition.user_template)
    sampling = SamplingParameters(
        temperature=model.decoding.temperature,
        top_p=model.decoding.top_p,
        max_tokens=model.decoding.max_tokens,
        seed=model.decoding.seed_base + sample_index,
        extra=model.decoding.extra,
    )
    identity = {
        "schema_version": "1.0",
        "theorem_id": theorem.theorem_id,
        "statement_hash": theorem.statement_hash,
        "import_hash": theorem.import_hash,
        "condition": condition.key,
        "proof_hash": _sha256_text(proof),
        "prompt_hash": prompt_template.sha256,
        "rendered_prompt_hash": compute_rendered_prompt_hash(messages),
        "chat_template_hash": chat_template.sha256,
        "model_key": model.key,
        "model_id": model.model_id,
        "model_revision": model.revision,
        "backend_config_hash": model.backend_config_hash,
        "sampling": sampling.model_dump(mode="json"),
        "sample_index": sample_index,
    }
    request = GenerationRequest.model_validate(
        {
            **identity,
            "proof_id": condition.proof_id,
            "prompt_name": prompt_name,
            "prompt_version": prompt_version,
            "model_adapter": model.adapter,
            "provider": model.provider,
            "requested_seed": sampling.seed,
            "capability_flags": model.capabilities.enabled_flags(),
            "request_id": compute_request_id(**identity),
        }
    )
    return PlannedGeneration(
        model_input=ModelInput(request=request, messages=messages),
        max_cost_usd=model.maximum_request_usd(),
        paid=model.paid,
        paid_idempotency_verified=model.paid_idempotency_verified,
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
