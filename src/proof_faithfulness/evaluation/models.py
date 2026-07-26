"""Strict contracts for candidate evidence and blinded annotations."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Hash = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
BlindId = Annotated[str, StringConstraints(pattern=r"^[a-z]{24}$")]
NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
StrategyClass = Literal["match_A", "match_B", "mixed_or_alternative", "unresolved"]
UtilizationState = Literal["used", "unused", "implicit", "unresolved"]


class EvaluationModel(BaseModel):
    """Immutable base model that rejects unknown annotation fields."""

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", frozen=True)


class SignatureRule(EvaluationModel):
    """One preregistered route signature and its literal evidence terms."""

    signature_id: NonEmptyString
    route: Literal["A", "B"]
    polarity: Literal["required", "incompatible"]
    evidence_terms: tuple[NonEmptyString, ...]
    match_mode: Literal["any", "all"] = "any"

    @model_validator(mode="after")
    def validate_evidence_terms(self) -> SignatureRule:
        if not self.evidence_terms:
            raise ValueError("A signature rule requires at least one evidence term")
        if len(set(self.evidence_terms)) != len(self.evidence_terms):
            raise ValueError(f"Evidence terms must be unique: {self.signature_id=}")
        return self


class SignatureRubric(EvaluationModel):
    """Frozen, theorem-specific rules for automatic strategy evidence."""

    rubric_version: NonEmptyString
    rules: tuple[SignatureRule, ...]
    library_lookup_terms: tuple[NonEmptyString, ...] = ()

    @model_validator(mode="after")
    def validate_rules(self) -> SignatureRubric:
        if not self.rules:
            raise ValueError("A signature rubric requires rules")
        rule_ids = tuple(rule.signature_id for rule in self.rules)
        if len(set(rule_ids)) != len(rule_ids):
            raise ValueError("Signature rule IDs must be unique")
        if len(set(self.library_lookup_terms)) != len(self.library_lookup_terms):
            raise ValueError("Library-lookup terms must be unique")
        for route in ("A", "B"):
            if not any(rule.route == route and rule.polarity == "required" for rule in self.rules):
                raise ValueError(f"Route {route} requires at least one required signature")
        return self


class SignatureHit(EvaluationModel):
    """Observed source evidence for one preregistered signature."""

    signature_id: NonEmptyString
    route: Literal["A", "B"]
    polarity: Literal["required", "incompatible"]
    matched_terms: tuple[NonEmptyString, ...]

    @model_validator(mode="after")
    def validate_matched_terms(self) -> SignatureHit:
        if not self.matched_terms:
            raise ValueError("A signature hit requires at least one matched term")
        if len(set(self.matched_terms)) != len(self.matched_terms):
            raise ValueError("Matched terms must be unique")
        return self


class SignatureExtraction(EvaluationModel):
    """Candidate evidence that always requires independent human review."""

    schema_version: Literal["1.0"] = "1.0"
    extractor_version: NonEmptyString
    source_sha256: Hash
    rubric_version: NonEmptyString
    hits: tuple[SignatureHit, ...]
    library_lookup_terms: tuple[NonEmptyString, ...] = ()
    candidate_classification: StrategyClass
    review_status: Literal["candidate_evidence_requires_human_review"] = (
        "candidate_evidence_requires_human_review"
    )


class AlignmentEvidence(EvaluationModel):
    """A possibly many-to-many informal-to-formal step alignment."""

    informal_step_ids: tuple[NonEmptyString, ...]
    formal_evidence_ids: tuple[NonEmptyString, ...] = ()
    alignment_type: Literal["one_to_one", "one_to_many", "many_to_one", "implicit"]
    utilization: UtilizationState
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_cardinality(self) -> AlignmentEvidence:
        if not self.informal_step_ids:
            raise ValueError("An alignment requires at least one informal step")
        if len(set(self.informal_step_ids)) != len(self.informal_step_ids):
            raise ValueError("Informal step IDs must be unique within an alignment")
        if len(set(self.formal_evidence_ids)) != len(self.formal_evidence_ids):
            raise ValueError("Formal evidence IDs must be unique within an alignment")
        informal_count = len(self.informal_step_ids)
        evidence_count = len(self.formal_evidence_ids)
        if self.alignment_type == "implicit":
            if evidence_count:
                raise ValueError("Implicit alignments cannot cite explicit formal evidence")
            if self.utilization != "implicit":
                raise ValueError("Implicit alignments require implicit utilization")
        elif evidence_count == 0:
            raise ValueError("Explicit alignments require formal evidence")
        elif self.alignment_type == "one_to_one" and (informal_count, evidence_count) != (1, 1):
            raise ValueError("One-to-one alignment requires one step and one evidence item")
        elif self.alignment_type == "one_to_many" and not (
            informal_count == 1 and evidence_count > 1
        ):
            raise ValueError("One-to-many alignment requires one step and multiple evidence items")
        elif self.alignment_type == "many_to_one" and not (
            informal_count > 1 and evidence_count == 1
        ):
            raise ValueError("Many-to-one alignment requires multiple steps and one evidence item")
        return self


class SensitiveMetadata(EvaluationModel):
    """Internal fields that must never cross the annotation blinding boundary."""

    model_name: NonEmptyString
    condition_key: NonEmptyString
    prompt_text: NonEmptyString
    sample_index: int = Field(ge=0)


class InternalAnnotationItem(EvaluationModel):
    """One internal annotation item before sensitive metadata is removed."""

    request_id: Hash
    theorem_id: NonEmptyString
    theorem_statement: NonEmptyString
    supplied_informal_proof: str
    generated_lean_proof: NonEmptyString
    rubric_text: NonEmptyString
    rubric_version: NonEmptyString
    extractor_version: NonEmptyString
    signature_evidence: tuple[NonEmptyString, ...]
    sensitive: SensitiveMetadata


class EvaluationPreparationSpec(EvaluationModel):
    """Trusted context needed to prepare one request for blinded evaluation."""

    request_id: Hash
    theorem_statement: NonEmptyString
    supplied_informal_proof: str
    rubric_text: NonEmptyString
    rubric_version: NonEmptyString
    extractor_version: NonEmptyString
    signature_evidence: tuple[NonEmptyString, ...]


class BlindedAnnotationItem(EvaluationModel):
    """One independently judged item with treatment identity removed."""

    schema_version: Literal["1.0"] = "1.0"
    blind_id: BlindId
    theorem_statement: NonEmptyString
    supplied_informal_proof: str
    generated_lean_proof: NonEmptyString
    rubric_text: NonEmptyString
    rubric_version: NonEmptyString
    extractor_version: NonEmptyString
    signature_evidence: tuple[NonEmptyString, ...]


class PacketManifestEntry(EvaluationModel):
    """Checksum and version identity for one blinded item file."""

    blind_id: BlindId
    file: NonEmptyString
    sha256: Hash
    rubric_version: NonEmptyString
    extractor_version: NonEmptyString


class PacketManifest(EvaluationModel):
    """Content identity for one complete public annotation packet."""

    schema_version: Literal["1.0"] = "1.0"
    packet_checksum: Hash
    private_map_commitment: Hash
    items: tuple[PacketManifestEntry, ...]
    rubric_versions: tuple[NonEmptyString, ...]
    extractor_versions: tuple[NonEmptyString, ...]

    @model_validator(mode="after")
    def validate_entries(self) -> PacketManifest:
        if not self.items:
            raise ValueError("A packet manifest requires at least one item")
        blind_ids = tuple(item.blind_id for item in self.items)
        files = tuple(item.file for item in self.items)
        if len(set(blind_ids)) != len(blind_ids) or len(set(files)) != len(files):
            raise ValueError("Packet manifest item IDs and paths must be unique")
        if tuple(sorted(set(self.rubric_versions))) != self.rubric_versions:
            raise ValueError("Packet rubric versions must be unique and sorted")
        if tuple(sorted(set(self.extractor_versions))) != self.extractor_versions:
            raise ValueError("Packet extractor versions must be unique and sorted")
        return self


class BlindMapEntry(EvaluationModel):
    """Private link between an annotation identifier and an immutable request."""

    blind_id: BlindId
    request_id: Hash
    theorem_id: NonEmptyString
    rubric_version: NonEmptyString
    extractor_version: NonEmptyString


class BlindingMap(EvaluationModel):
    """Private identity map stored outside the exported annotation bundle."""

    schema_version: Literal["1.0"] = "1.0"
    packet_checksum: Hash
    rubric_versions: tuple[NonEmptyString, ...]
    extractor_versions: tuple[NonEmptyString, ...]
    entries: tuple[BlindMapEntry, ...]


class AutomaticJudgment(EvaluationModel):
    """Blinded candidate judgment from deterministic signature evidence."""

    schema_version: Literal["1.0"] = "1.0"
    blind_id: BlindId
    packet_checksum: Hash
    rubric_version: NonEmptyString
    extractor_version: NonEmptyString
    classification: StrategyClass
    strategy_labels: tuple[NonEmptyString, ...]
    utilization: UtilizationState
    uncertain: bool = False
    review_status: Literal["candidate_evidence_requires_human_review"] = (
        "candidate_evidence_requires_human_review"
    )

    @model_validator(mode="after")
    def validate_strategy_labels(self) -> AutomaticJudgment:
        if len(set(self.strategy_labels)) != len(self.strategy_labels):
            raise ValueError("Automatic strategy labels must be unique")
        return self


class AuxiliaryJudgeOutput(EvaluationModel):
    """Structured, blinded output from an auxiliary judge."""

    schema_version: Literal["1.0"] = "1.0"
    judge_version: NonEmptyString
    blind_id: BlindId
    packet_checksum: Hash
    rubric_version: NonEmptyString
    extractor_version: NonEmptyString
    classification: StrategyClass
    strategy_labels: tuple[NonEmptyString, ...]
    utilization: UtilizationState
    alignments: tuple[AlignmentEvidence, ...] = ()
    strategy_expressibility_uncertain: bool = False
    explanation: NonEmptyString

    @model_validator(mode="after")
    def validate_strategy_labels(self) -> AuxiliaryJudgeOutput:
        if len(set(self.strategy_labels)) != len(self.strategy_labels):
            raise ValueError("Auxiliary judge strategy labels must be unique")
        return self


class DependencyEdgeLabel(EvaluationModel):
    """One directed proof-step edge supplied by an annotator."""

    predecessor_step_id: NonEmptyString
    successor_step_id: NonEmptyString

    @model_validator(mode="after")
    def reject_self_edge(self) -> DependencyEdgeLabel:
        if self.predecessor_step_id == self.successor_step_id:
            raise ValueError("A dependency edge cannot be a self-edge")
        return self


class HumanLabel(EvaluationModel):
    """One independent human label, retained verbatim through adjudication."""

    schema_version: Literal["1.0"] = "1.0"
    label_id: NonEmptyString
    blind_id: BlindId
    packet_checksum: Hash
    annotator_id: NonEmptyString
    calibration_round: NonEmptyString
    rubric_version: NonEmptyString
    extractor_version: NonEmptyString
    classification: StrategyClass
    strategy_labels: tuple[NonEmptyString, ...]
    utilization: UtilizationState
    alignments: tuple[AlignmentEvidence, ...] = ()
    dependency_edges: tuple[DependencyEdgeLabel, ...] = ()
    strategy_expressibility_uncertain: bool = False
    explanation: NonEmptyString

    @model_validator(mode="after")
    def validate_label_sets(self) -> HumanLabel:
        if len(set(self.strategy_labels)) != len(self.strategy_labels):
            raise ValueError("Strategy labels must be unique")
        alignment_keys = tuple(alignment.model_dump_json() for alignment in self.alignments)
        if len(set(alignment_keys)) != len(alignment_keys):
            raise ValueError("Human step alignments must be unique")
        edges = tuple(
            (edge.predecessor_step_id, edge.successor_step_id) for edge in self.dependency_edges
        )
        if len(set(edges)) != len(edges):
            raise ValueError("Dependency edges must be unique")
        return self


class ImportedHumanLabel(EvaluationModel):
    """A packet-bound human label resolved without mutating its original payload."""

    request_id: Hash
    theorem_id: NonEmptyString
    packet_checksum: Hash
    rubric_version: NonEmptyString
    extractor_version: NonEmptyString
    source_path: NonEmptyString
    source_line: int = Field(gt=0)
    source_sha256: Hash
    original: HumanLabel


class DisagreementItem(EvaluationModel):
    """One item requiring independent human review or adjudication."""

    blind_id: BlindId
    label_ids: tuple[NonEmptyString, ...]
    reasons: tuple[NonEmptyString, ...]


class PreHumanReviewItem(EvaluationModel):
    """One automatic/judge comparison selected for blinded human review."""

    blind_id: BlindId
    reasons: tuple[NonEmptyString, ...]
    selection: Literal["mandatory", "random_audit"]


class AdjudicationDecision(EvaluationModel):
    """A human adjudicator's packet-bound decision citing every source label."""

    schema_version: Literal["1.0"] = "1.0"
    adjudicator_source: Literal["human"] = "human"
    decision_id: NonEmptyString
    blind_id: BlindId
    packet_checksum: Hash
    adjudicator_id: NonEmptyString
    calibration_round: NonEmptyString
    rubric_version: NonEmptyString
    extractor_version: NonEmptyString
    source_label_ids: tuple[NonEmptyString, ...]
    classification: StrategyClass
    strategy_labels: tuple[NonEmptyString, ...]
    utilization: UtilizationState
    alignments: tuple[AlignmentEvidence, ...] = ()
    dependency_edges: tuple[DependencyEdgeLabel, ...] = ()
    explanation: NonEmptyString

    @model_validator(mode="after")
    def validate_decision_sets(self) -> AdjudicationDecision:
        if not self.source_label_ids:
            raise ValueError("Adjudication must cite source labels")
        if len(set(self.source_label_ids)) != len(self.source_label_ids):
            raise ValueError("Adjudication source label IDs must be unique")
        if len(set(self.strategy_labels)) != len(self.strategy_labels):
            raise ValueError("Adjudicated strategy labels must be unique")
        alignment_keys = tuple(alignment.model_dump_json() for alignment in self.alignments)
        if len(set(alignment_keys)) != len(alignment_keys):
            raise ValueError("Adjudicated step alignments must be unique")
        edges = tuple(
            (edge.predecessor_step_id, edge.successor_step_id) for edge in self.dependency_edges
        )
        if len(set(edges)) != len(edges):
            raise ValueError("Adjudicated dependency edges must be unique")
        return self


class AdjudicatedRecord(EvaluationModel):
    """An adjudication result embedding, rather than replacing, source labels."""

    schema_version: Literal["1.0"] = "1.0"
    blind_id: BlindId
    original_labels: tuple[ImportedHumanLabel, ...]
    decision: AdjudicationDecision


class CalibrationReport(EvaluationModel):
    """Five-theorem calibration summary awaiting an explicit human freeze."""

    schema_version: Literal["1.0"] = "1.0"
    calibration_id: NonEmptyString
    theorem_ids: tuple[NonEmptyString, ...]
    item_count: int = Field(gt=0)
    annotator_ids: tuple[NonEmptyString, ...]
    disagreement_count: int = Field(ge=0)
    packet_checksum: Hash
    extractor_version: NonEmptyString
    source_labels_sha256: Hash
    source_rubric_version: NonEmptyString
    proposed_rubric_revision: NonEmptyString
    state: Literal["waiting_on_human_freeze"] = "waiting_on_human_freeze"

    @model_validator(mode="after")
    def require_five_theorems(self) -> CalibrationReport:
        if len(self.theorem_ids) != 5 or len(set(self.theorem_ids)) != 5:
            raise ValueError("A calibration report requires exactly five unique theorems")
        if len(self.annotator_ids) < 2:
            raise ValueError("A calibration report requires at least two annotators")
        return self


class HumanFreezeApproval(EvaluationModel):
    """Human-owned approval file binding a report hash and rubric revision."""

    schema_version: Literal["1.0"] = "1.0"
    approval_id: NonEmptyString
    decision: Literal["approve_calibration_freeze"]
    approved_by: NonEmptyString
    approved_at: datetime
    calibration_id: NonEmptyString
    report_sha256: Hash
    rubric_revision: NonEmptyString


class FrozenCalibration(EvaluationModel):
    """A calibration rubric frozen from a verified human-owned approval file."""

    schema_version: Literal["1.0"] = "1.0"
    report: CalibrationReport
    report_sha256: Hash
    rubric_revision: NonEmptyString
    approval_path: NonEmptyString
    approval_sha256: Hash
    approval: HumanFreezeApproval
