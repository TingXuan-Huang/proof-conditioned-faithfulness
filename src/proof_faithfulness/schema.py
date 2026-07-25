"""Versioned data contracts for benchmark, generation, and evaluation artifacts."""

from __future__ import annotations

from collections.abc import Hashable
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, StringConstraints, model_validator

from proof_faithfulness.ids import compute_request_id

Hash = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
GitCommit = Annotated[
    str,
    StringConstraints(pattern=r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$"),
]
NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
SchemaVersion = Annotated[str, StringConstraints(pattern=r"^[0-9]+\.[0-9]+$")]
StepRole = Literal["strategy_essential", "logically_necessary", "explanatory"]
StrategyMatch = Literal["match_A", "match_B", "mixed_or_alternative", "unresolved"]
FIXED_ALLOWED_AXIOMS = ("propext", "Classical.choice", "Quot.sound")


class ContractModel(BaseModel):
    """Base class that fails closed on unknown fields and mutation."""

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", frozen=True)


class SourceCitation(ContractModel):
    """One source used to adapt a benchmark theorem or proof."""

    title: NonEmptyString
    url: NonEmptyString
    locator: str | None = None


class SourceMetadata(ContractModel):
    """Provenance and adaptation metadata for a benchmark record."""

    citations: tuple[SourceCitation, ...]
    adaptation_notes: NonEmptyString

    @model_validator(mode="after")
    def require_citation(self) -> SourceMetadata:
        if not self.citations:
            raise ValueError("At least one source citation is required")
        return self


class ContaminationMetadata(ContractModel):
    """Estimated likelihood that a theorem/proof pair appears in training data."""

    risk: Literal["low", "medium", "high", "unknown"]
    rationale: NonEmptyString


class LeanTheoremSpec(ContractModel):
    """Exact trusted Lean statement and pinned toolchain metadata."""

    declaration_name: NonEmptyString
    declaration: NonEmptyString
    statement_hash: Hash
    imports: tuple[NonEmptyString, ...]
    import_hash: Hash
    reference_file_paths: tuple[str, ...] = ()
    lean_version: NonEmptyString
    mathlib_tag: NonEmptyString
    mathlib_commit: Hash
    expected_axioms: tuple[NonEmptyString, ...] = FIXED_ALLOWED_AXIOMS

    @model_validator(mode="after")
    def validate_imports(self) -> LeanTheoremSpec:
        if not self.imports:
            raise ValueError("At least one Lean import is required")
        if len(set(self.imports)) != len(self.imports):
            raise ValueError("Lean imports must be unique")
        if self.expected_axioms != FIXED_ALLOWED_AXIOMS:
            raise ValueError("Expected axioms must match the fixed trusted-checker policy")
        return self


class ProofStep(ContractModel):
    """One stable informal proof step and its semantic roles."""

    step_id: NonEmptyString
    text: NonEmptyString
    roles: tuple[StepRole, ...]
    predecessor_step_ids: tuple[NonEmptyString, ...] = ()

    @model_validator(mode="after")
    def validate_roles_and_predecessors(self) -> ProofStep:
        if not self.roles:
            raise ValueError("A proof step must have at least one role")
        if len(set(self.roles)) != len(self.roles):
            raise ValueError(f"Duplicate roles in {self.step_id=}")
        if len(set(self.predecessor_step_ids)) != len(self.predecessor_step_ids):
            raise ValueError(f"Duplicate predecessors in {self.step_id=}")
        if self.step_id in self.predecessor_step_ids:
            raise ValueError(f"A proof step cannot depend on itself: {self.step_id=}")
        return self


class DependencyEdge(ContractModel):
    """Directed dependency from one informal proof step to another."""

    predecessor_step_id: NonEmptyString
    successor_step_id: NonEmptyString

    @model_validator(mode="after")
    def reject_self_edge(self) -> DependencyEdge:
        if self.predecessor_step_id == self.successor_step_id:
            raise ValueError("A dependency edge cannot be a self-edge")
        return self


class MetadataEntry(ContractModel):
    """One immutable scalar metadata entry."""

    name: NonEmptyString
    value: str | int | float | bool | None


class ProofVariant(ContractModel):
    """One of the two human-curated proof strategies for a theorem."""

    proof_id: Literal["A", "B"]
    informal_proof: NonEmptyString
    paraphrase: NonEmptyString
    strategy_labels: tuple[NonEmptyString, ...]
    required_signatures: tuple[NonEmptyString, ...]
    incompatible_signatures: tuple[NonEmptyString, ...]
    acceptable_formal_refinements: tuple[str, ...] = ()
    steps: tuple[ProofStep, ...]
    dependency_edges: tuple[DependencyEdge, ...] = ()
    reference_lean_file: str | None = None
    annotator_approvals: tuple[NonEmptyString, ...] = ()
    corruption_metadata: tuple[MetadataEntry, ...] | None = None

    @model_validator(mode="after")
    def validate_strategy_and_graph(self) -> ProofVariant:
        _require_unique_nonempty(self.strategy_labels, "strategy labels")
        _require_unique_nonempty(self.required_signatures, "required signatures")
        _require_unique(self.incompatible_signatures, "incompatible signatures")
        if self.corruption_metadata is not None:
            metadata_names = tuple(entry.name for entry in self.corruption_metadata)
            _require_unique(metadata_names, "corruption metadata names")
        if set(self.required_signatures) & set(self.incompatible_signatures):
            raise ValueError("Required and incompatible signatures must be disjoint")
        if not self.steps:
            raise ValueError("A proof variant must contain at least one step")
        step_ids = [step.step_id for step in self.steps]
        if len(set(step_ids)) != len(step_ids):
            raise ValueError("Proof step IDs must be unique within a variant")
        edge_pairs = [
            (edge.predecessor_step_id, edge.successor_step_id) for edge in self.dependency_edges
        ]
        if len(set(edge_pairs)) != len(edge_pairs):
            raise ValueError("Dependency edges must be unique")
        expected_edges = {
            (predecessor, step.step_id)
            for step in self.steps
            for predecessor in step.predecessor_step_ids
        }
        if set(edge_pairs) != expected_edges:
            raise ValueError("Dependency edges must exactly match step predecessor IDs")
        _validate_acyclic_graph(set(step_ids), set(edge_pairs))
        return self


class BenchmarkRecord(ContractModel):
    """A theorem with exactly two strategy-distinct informal proof variants."""

    schema_version: SchemaVersion
    theorem_id: NonEmptyString
    domain: NonEmptyString
    difficulty: NonEmptyString
    source: SourceMetadata
    contamination: ContaminationMetadata
    informal_statement: NonEmptyString
    lean: LeanTheoremSpec
    proof_variants: tuple[ProofVariant, ProofVariant]
    split: Literal["pilot", "core", "extension"]
    status: Literal["draft", "human_approved", "frozen"]

    @model_validator(mode="after")
    def validate_variants_and_freeze(self) -> BenchmarkRecord:
        if {variant.proof_id for variant in self.proof_variants} != {"A", "B"}:
            raise ValueError("Proof variants must contain exactly IDs A and B")
        first, second = self.proof_variants
        first_signature = (
            frozenset(first.strategy_labels),
            frozenset(first.required_signatures),
            frozenset(first.incompatible_signatures),
        )
        second_signature = (
            frozenset(second.strategy_labels),
            frozenset(second.required_signatures),
            frozenset(second.incompatible_signatures),
        )
        if first_signature == second_signature:
            raise ValueError("Proof variants must not have identical strategy signatures")
        if self.status == "frozen":
            for variant in self.proof_variants:
                if variant.reference_lean_file and not variant.annotator_approvals:
                    raise ValueError("A frozen reference proof requires human approval")
                if self.split == "pilot" and not variant.reference_lean_file:
                    raise ValueError("A frozen pilot variant requires a reference Lean proof")
        return self


class BenchmarkDataset(ContractModel):
    """A collection that enforces theorem-level ID uniqueness."""

    records: tuple[BenchmarkRecord, ...]

    @model_validator(mode="after")
    def reject_duplicate_theorem_ids(self) -> BenchmarkDataset:
        theorem_ids = [record.theorem_id for record in self.records]
        if len(set(theorem_ids)) != len(theorem_ids):
            raise ValueError("Benchmark theorem IDs must be unique")
        return self


class SamplingOption(ContractModel):
    """One provider-specific scalar sampling option."""

    name: NonEmptyString
    value: str | int | float | bool | None


class SamplingParameters(ContractModel):
    """Exact model sampling settings that affect request identity."""

    temperature: float = Field(ge=0)
    top_p: float = Field(gt=0, le=1)
    max_tokens: int = Field(gt=0)
    seed: int | None = None
    extra: tuple[SamplingOption, ...] = ()

    @model_validator(mode="after")
    def validate_extra_options(self) -> SamplingParameters:
        names = tuple(option.name for option in self.extra)
        _require_unique(names, "sampling option names")
        return self


class GenerationRequest(ContractModel):
    """Immutable, fully identified model generation request."""

    schema_version: SchemaVersion
    theorem_id: NonEmptyString
    statement_hash: Hash
    import_hash: Hash
    condition: NonEmptyString
    proof_id: Literal["A", "B"] | None
    proof_hash: Hash
    prompt_name: NonEmptyString
    prompt_version: NonEmptyString
    prompt_hash: Hash
    rendered_prompt_hash: Hash
    chat_template_hash: Hash
    model_adapter: NonEmptyString
    provider: NonEmptyString
    model_key: NonEmptyString
    model_id: NonEmptyString
    model_revision: NonEmptyString
    backend_config_hash: Hash
    sampling: SamplingParameters
    sample_index: int = Field(ge=0)
    requested_seed: int | None = None
    capability_flags: tuple[NonEmptyString, ...] = ()
    request_id: Hash

    @model_validator(mode="after")
    def validate_request_id(self) -> GenerationRequest:
        expected_id = compute_request_id(
            schema_version=self.schema_version,
            theorem_id=self.theorem_id,
            statement_hash=self.statement_hash,
            import_hash=self.import_hash,
            condition=self.condition,
            proof_hash=self.proof_hash,
            prompt_hash=self.prompt_hash,
            rendered_prompt_hash=self.rendered_prompt_hash,
            chat_template_hash=self.chat_template_hash,
            model_key=self.model_key,
            model_id=self.model_id,
            model_revision=self.model_revision,
            backend_config_hash=self.backend_config_hash,
            sampling=self.sampling.model_dump(mode="json"),
            sample_index=self.sample_index,
        )
        if self.request_id != expected_id:
            raise ValueError(f"Request ID does not match request content: {self.request_id=}")
        if self.requested_seed != self.sampling.seed:
            raise ValueError("Requested seed must match the sampling seed")
        _require_unique(self.capability_flags, "capability flags")
        return self


class TransportAttempt(ContractModel):
    """One transport attempt for a request, including retry metadata."""

    attempt: int = Field(gt=0)
    started_at: datetime
    finished_at: datetime
    status: Literal["success", "timeout", "rate_limited", "transport_error"]
    detail: str | None = None

    @model_validator(mode="after")
    def validate_time_order(self) -> TransportAttempt:
        if self.finished_at < self.started_at:
            raise ValueError("Transport attempt cannot finish before it starts")
        return self


class TokenUsage(ContractModel):
    """Provider-reported token counts."""

    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)


class ExtractionResult(ContractModel):
    """Mechanical extraction result without semantic repair."""

    status: Literal["success", "no_block", "multiple_blocks", "invalid_format"]
    artifact_path: str | None = None
    checksum: Hash | None = None


class GenerationResponse(ContractModel):
    """Successful response artifact written at responses/<request_id>/response.json."""

    schema_version: SchemaVersion
    request_id: Hash
    model_key: NonEmptyString
    revision: NonEmptyString
    raw: JsonValue
    text: str
    finish_reason: str | None = None
    usage: TokenUsage
    usd_cost: float = Field(ge=0)
    latency_s: float = Field(ge=0)
    started_at: datetime
    completed_at: datetime
    harness_git_commit: GitCommit

    @model_validator(mode="after")
    def validate_response_consistency(self) -> GenerationResponse:
        if self.completed_at < self.started_at:
            raise ValueError("Generation response cannot complete before it starts")
        elapsed = (self.completed_at - self.started_at).total_seconds()
        if abs(self.latency_s - elapsed) > 1e-6:
            raise ValueError("latency_s must equal completed_at minus started_at")
        return self


class LeanCheckResult(ContractModel):
    """Normalized output from the trusted Lean checking boundary."""

    schema_version: SchemaVersion
    request_id: Hash
    statement_hash_matches: bool
    extraction_status: NonEmptyString
    parser_status: NonEmptyString
    elaboration_status: NonEmptyString
    exit_code: int | None = None
    wall_time_seconds: float = Field(ge=0)
    peak_memory_mb: float | None = Field(default=None, ge=0)
    stdout_path: str | None = None
    stderr_path: str | None = None
    declaration_name: str | None = None
    axioms: tuple[str, ...] = ()
    prohibited_token_findings: tuple[str, ...] = ()
    failure_category: NonEmptyString


class StrategyJudgment(ContractModel):
    """One independent strategy judgment; adjudication never replaces source labels."""

    schema_version: SchemaVersion
    request_id: Hash
    source_type: Literal["signature_extractor", "llm_judge", "human", "adjudication"]
    source_id: NonEmptyString
    strategy_labels: tuple[NonEmptyString, ...]
    classification: StrategyMatch
    explanation: NonEmptyString


class StepAlignment(ContractModel):
    """Alignment between one or more informal steps and formal evidence."""

    schema_version: SchemaVersion
    request_id: Hash
    proof_id: Literal["A", "B"]
    informal_step_ids: tuple[NonEmptyString, ...]
    formal_evidence_ids: tuple[str, ...] = ()
    alignment_type: Literal["one_to_one", "one_to_many", "many_to_one", "implicit"]
    confidence: float = Field(ge=0, le=1)
    explanation: NonEmptyString

    @model_validator(mode="after")
    def require_informal_steps(self) -> StepAlignment:
        _require_unique_nonempty(self.informal_step_ids, "informal step IDs")
        _require_unique(self.formal_evidence_ids, "formal evidence IDs")
        if self.alignment_type != "implicit" and not self.formal_evidence_ids:
            raise ValueError("An explicit alignment requires formal evidence")
        return self


class DerivedMetric(ContractModel):
    """One named theorem- or sample-level metric."""

    name: NonEmptyString
    value: float


class CounterfactualEvaluation(ContractModel):
    """Derived sample evaluation without overwriting source judgments."""

    schema_version: SchemaVersion
    request_id: Hash
    compiled: bool
    strategy_match: StrategyMatch
    step_coverage: float = Field(ge=0, le=1)
    utilization_state: Literal["used", "partially_used", "unused", "unresolved"]
    ambiguity_lower: float = Field(ge=0, le=1)
    ambiguity_upper: float = Field(ge=0, le=1)
    source_judgment_ids: tuple[NonEmptyString, ...]
    derived_metrics: tuple[DerivedMetric, ...] = ()

    @model_validator(mode="after")
    def validate_ambiguity_bounds(self) -> CounterfactualEvaluation:
        if self.ambiguity_lower > self.ambiguity_upper:
            raise ValueError("Ambiguity lower bound must not exceed upper bound")
        if any(not 0 <= metric.value <= 1 for metric in self.derived_metrics):
            raise ValueError("Derived evaluation metrics must be within [0, 1]")
        metric_names = tuple(metric.name for metric in self.derived_metrics)
        _require_unique(metric_names, "derived metric names")
        _require_unique_nonempty(self.source_judgment_ids, "source judgment IDs")
        return self


SCHEMA_MODELS: tuple[type[ContractModel], ...] = (
    BenchmarkRecord,
    GenerationRequest,
    GenerationResponse,
    LeanCheckResult,
    StrategyJudgment,
    StepAlignment,
    CounterfactualEvaluation,
)


def _require_unique(values: tuple[Hashable, ...], description: str) -> None:
    if len(set(values)) != len(values):
        raise ValueError(f"{description.capitalize()} must be unique")


def _require_unique_nonempty(values: tuple[Hashable, ...], description: str) -> None:
    if not values:
        raise ValueError(f"At least one {description} value is required")
    _require_unique(values, description)


def _validate_acyclic_graph(
    nodes: set[str],
    edges: set[tuple[str, str]],
) -> None:
    edge_nodes = {node for edge in edges for node in edge}
    dangling_nodes = edge_nodes - nodes
    if dangling_nodes:
        raise ValueError(f"Dependency graph contains dangling step IDs: {sorted(dangling_nodes)}")
    successors: dict[str, set[str]] = {node: set() for node in nodes}
    in_degree = {node: 0 for node in nodes}
    for predecessor, successor in edges:
        successors[predecessor].add(successor)
        in_degree[successor] += 1
    ready = [node for node, degree in in_degree.items() if degree == 0]
    visited = 0
    while ready:
        node = ready.pop()
        visited += 1
        for successor in successors[node]:
            in_degree[successor] -= 1
            if in_degree[successor] == 0:
                ready.append(successor)
    if visited != len(nodes):
        raise ValueError("Dependency graph contains a cycle")
