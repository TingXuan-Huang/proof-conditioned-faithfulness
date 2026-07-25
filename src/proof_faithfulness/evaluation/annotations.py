"""Auditable import, review, calibration, and adjudication workflows."""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import stat
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from proof_faithfulness.evaluation.blinding import (
    compute_map_commitment,
    load_blinding_map,
    verify_blinded_bundle,
)
from proof_faithfulness.evaluation.models import (
    AdjudicatedRecord,
    AdjudicationDecision,
    AutomaticJudgment,
    AuxiliaryJudgeOutput,
    CalibrationReport,
    DisagreementItem,
    FrozenCalibration,
    HumanFreezeApproval,
    HumanLabel,
    ImportedHumanLabel,
    PreHumanReviewItem,
)

_MAX_LABEL_FILE_BYTES = 64 * 1024 * 1024
_MAX_APPROVAL_FILE_BYTES = 1024 * 1024


def import_human_labels(
    input_paths: Iterable[Path],
    mapping_path: Path,
    bundle_dir: Path,
) -> tuple[ImportedHumanLabel, ...]:
    """Imports labels only when packet, map, and label versions match exactly."""
    paths = tuple(input_paths)
    if not paths:
        raise ValueError("At least one human-label file is required")
    manifest = verify_blinded_bundle(bundle_dir)
    mapping = load_blinding_map(mapping_path)
    if (
        mapping.packet_checksum != manifest.packet_checksum
        or mapping.rubric_versions != manifest.rubric_versions
        or mapping.extractor_versions != manifest.extractor_versions
        or compute_map_commitment(mapping.entries) != manifest.private_map_commitment
    ):
        raise ValueError("Blinding map does not belong to the supplied packet")
    manifest_by_blind_id = {entry.blind_id: entry for entry in manifest.items}
    entry_by_blind_id = {entry.blind_id: entry for entry in mapping.entries}
    if set(manifest_by_blind_id) != set(entry_by_blind_id):
        raise ValueError("Blinding map item set does not match the supplied packet")
    for blind_id, entry in entry_by_blind_id.items():
        public_entry = manifest_by_blind_id[blind_id]
        if (
            entry.rubric_version != public_entry.rubric_version
            or entry.extractor_version != public_entry.extractor_version
        ):
            raise ValueError(f"Blinding map item versions mismatch packet: {blind_id}")

    imported: list[ImportedHumanLabel] = []
    seen_label_ids: set[str] = set()
    seen_annotator_items: set[tuple[str, str]] = set()
    for path in paths:
        content = _read_regular_file(path, _MAX_LABEL_FILE_BYTES, "Human-label input")
        source_sha256 = hashlib.sha256(content).hexdigest()
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"Human-label input is not UTF-8: {path}") from error
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            label = _parse_human_label(line, path, line_number)
            entry = entry_by_blind_id.get(label.blind_id)
            if entry is None:
                raise ValueError(f"Unknown blind ID at {path}:{line_number}: {label.blind_id}")
            if (
                label.packet_checksum != mapping.packet_checksum
                or label.rubric_version != entry.rubric_version
                or label.extractor_version != entry.extractor_version
            ):
                raise ValueError(f"Label packet or tool versions mismatch at {path}:{line_number}")
            if label.label_id in seen_label_ids:
                raise ValueError(f"Duplicate human label ID: {label.label_id}")
            annotator_item = (label.annotator_id, label.blind_id)
            if annotator_item in seen_annotator_items:
                raise ValueError(
                    "An annotator supplied multiple labels for one item: "
                    f"{label.annotator_id}, {label.blind_id}"
                )
            seen_label_ids.add(label.label_id)
            seen_annotator_items.add(annotator_item)
            imported.append(
                ImportedHumanLabel(
                    request_id=entry.request_id,
                    theorem_id=entry.theorem_id,
                    packet_checksum=mapping.packet_checksum,
                    rubric_version=entry.rubric_version,
                    extractor_version=entry.extractor_version,
                    source_path=str(path),
                    source_line=line_number,
                    source_sha256=source_sha256,
                    original=label,
                )
            )
    if not imported:
        raise ValueError("Human-label inputs contained no labels")
    return tuple(
        sorted(
            imported,
            key=lambda item: (item.original.blind_id, item.original.annotator_id),
        )
    )


def build_pre_human_review_queue(
    automatic_outputs: Iterable[AutomaticJudgment],
    judge_outputs: Iterable[AuxiliaryJudgeOutput],
    *,
    seed: int,
    audit_fraction: float = 0.25,
    minimum_audit: int = 10,
) -> tuple[PreHumanReviewItem, ...]:
    """Selects every automatic/judge issue plus a deterministic random audit."""
    if not 0 <= audit_fraction <= 1:
        raise ValueError("Audit fraction must be within [0, 1]")
    if minimum_audit < 0:
        raise ValueError("Minimum audit size cannot be negative")
    automatic = _unique_automatic(automatic_outputs)
    judges = _unique_judges(judge_outputs)
    if not automatic or set(automatic) != set(judges):
        raise ValueError("Automatic and auxiliary judgments must cover the same nonempty item set")

    mandatory: dict[str, tuple[str, ...]] = {}
    for blind_id in sorted(automatic):
        candidate = automatic[blind_id]
        judge = judges[blind_id]
        if (
            candidate.packet_checksum != judge.packet_checksum
            or candidate.rubric_version != judge.rubric_version
            or candidate.extractor_version != judge.extractor_version
        ):
            raise ValueError(f"Automatic and judge provenance mismatch: {blind_id}")
        reasons: set[str] = set()
        if candidate.classification != judge.classification:
            reasons.add("automatic_llm_classification_disagreement")
        if set(candidate.strategy_labels) != set(judge.strategy_labels):
            reasons.add("automatic_llm_strategy_labels_disagreement")
        if candidate.utilization != judge.utilization:
            reasons.add("automatic_llm_utilization_disagreement")
        if candidate.uncertain or candidate.classification == "unresolved":
            reasons.add("automatic_uncertain")
        if judge.strategy_expressibility_uncertain or judge.classification == "unresolved":
            reasons.add("llm_uncertain")
        if candidate.utilization == "unresolved" or judge.utilization == "unresolved":
            reasons.add("utilization_uncertain")
        if reasons:
            mandatory[blind_id] = tuple(sorted(reasons))

    remainder = sorted(set(automatic) - set(mandatory))
    audit_count = min(
        len(remainder),
        max(minimum_audit, math.ceil(len(remainder) * audit_fraction)),
    )
    audited = set(random.Random(seed).sample(remainder, audit_count))
    return tuple(
        PreHumanReviewItem(
            blind_id=blind_id,
            reasons=mandatory.get(blind_id, ("random_audit",)),
            selection="mandatory" if blind_id in mandatory else "random_audit",
        )
        for blind_id in sorted(set(mandatory) | audited)
    )


def build_disagreement_queue(
    labels: Iterable[ImportedHumanLabel],
    *,
    judge_outputs: Iterable[AuxiliaryJudgeOutput] = (),
    automatic_outputs: Iterable[AutomaticJudgment] = (),
) -> tuple[DisagreementItem, ...]:
    """Builds a post-label queue for human, judge, and automatic disagreements."""
    grouped = _group_labels(labels)
    judges = _unique_judges(judge_outputs)
    automatic = _unique_automatic(automatic_outputs)
    queue: list[DisagreementItem] = []
    for blind_id in sorted(grouped):
        item_labels = grouped[blind_id]
        reasons = _human_disagreement_reasons(item_labels)
        if any(label.original.strategy_expressibility_uncertain for label in item_labels):
            reasons.add("strategy_expressibility_uncertain")
        if any(label.original.classification == "unresolved" for label in item_labels):
            reasons.add("human_unresolved")
        judge = judges.get(blind_id)
        if judge is not None:
            if any(label.original.classification != judge.classification for label in item_labels):
                reasons.add("human_llm_strategy_disagreement")
            if any(
                set(label.original.strategy_labels) != set(judge.strategy_labels)
                for label in item_labels
            ):
                reasons.add("human_llm_strategy_labels_disagreement")
            if any(label.original.utilization != judge.utilization for label in item_labels):
                reasons.add("human_llm_utilization_disagreement")
            if judge.strategy_expressibility_uncertain:
                reasons.add("llm_strategy_expressibility_uncertain")
        candidate = automatic.get(blind_id)
        if candidate is not None:
            if any(
                label.original.classification != candidate.classification for label in item_labels
            ):
                reasons.add("human_automatic_strategy_disagreement")
            if any(
                set(label.original.strategy_labels) != set(candidate.strategy_labels)
                for label in item_labels
            ):
                reasons.add("human_automatic_strategy_labels_disagreement")
            if any(label.original.utilization != candidate.utilization for label in item_labels):
                reasons.add("human_automatic_utilization_disagreement")
        if reasons:
            queue.append(
                DisagreementItem(
                    blind_id=blind_id,
                    label_ids=tuple(label.original.label_id for label in item_labels),
                    reasons=tuple(sorted(reasons)),
                )
            )
    unknown = (set(judges) | set(automatic)) - set(grouped)
    if unknown:
        raise ValueError(
            f"Review evidence references items without human labels: {sorted(unknown)}"
        )
    return tuple(queue)


def select_review_queue(
    labels: Iterable[ImportedHumanLabel],
    disagreement_queue: Iterable[DisagreementItem],
    *,
    seed: int,
    audit_fraction: float = 0.25,
    minimum_audit: int = 10,
) -> tuple[str, ...]:
    """Adds a deterministic random audit to all mandatory post-label review items."""
    if not 0 <= audit_fraction <= 1:
        raise ValueError("Audit fraction must be within [0, 1]")
    if minimum_audit < 0:
        raise ValueError("Minimum audit size cannot be negative")
    grouped = _group_labels(labels)
    mandatory = {item.blind_id for item in disagreement_queue}
    unknown = mandatory - set(grouped)
    if unknown:
        raise ValueError(f"Disagreement queue contains unknown blind IDs: {sorted(unknown)}")
    candidates = sorted(set(grouped) - mandatory)
    audit_count = min(
        len(candidates),
        max(minimum_audit, math.ceil(len(candidates) * audit_fraction)),
    )
    selected = random.Random(seed).sample(candidates, audit_count)
    return tuple(sorted(mandatory | set(selected)))


def build_calibration_report(
    calibration_id: str,
    labels: Iterable[ImportedHumanLabel],
    proposed_rubric_revision: str,
) -> CalibrationReport:
    """Summarizes an exactly five-theorem, consistently double-coded round."""
    label_tuple = tuple(labels)
    grouped = _group_labels(label_tuple)
    theorem_ids = tuple(
        sorted({label.theorem_id for values in grouped.values() for label in values})
    )
    if len(theorem_ids) != 5:
        raise ValueError("Calibration requires labels from exactly five theorems")
    panel: frozenset[str] | None = None
    rubric_versions: set[str] = set()
    packet_checksums: set[str] = set()
    extractor_versions: set[str] = set()
    for blind_id, item_labels in grouped.items():
        item_panel = frozenset(label.original.annotator_id for label in item_labels)
        if len(item_panel) < 2:
            raise ValueError(f"Calibration item lacks two annotators: {blind_id}")
        if panel is None:
            panel = item_panel
        elif item_panel != panel:
            raise ValueError(
                "The same independent annotator panel must label every calibration item"
            )
        for label in item_labels:
            if label.original.calibration_round != calibration_id:
                raise ValueError(f"Calibration-round mismatch: {label.original.label_id}")
            if (
                label.original.packet_checksum != label.packet_checksum
                or label.original.rubric_version != label.rubric_version
                or label.original.extractor_version != label.extractor_version
            ):
                raise ValueError(
                    f"Imported calibration provenance mismatch: {label.original.label_id}"
                )
            rubric_versions.add(label.original.rubric_version)
            packet_checksums.add(label.packet_checksum)
            extractor_versions.add(label.extractor_version)
    if (
        panel is None
        or len(rubric_versions) != 1
        or len(packet_checksums) != 1
        or len(extractor_versions) != 1
    ):
        raise ValueError(
            "Calibration labels must use one packet, extractor, and source rubric version"
        )
    disagreement_count = len(
        build_disagreement_queue(item for values in grouped.values() for item in values)
    )
    return CalibrationReport(
        calibration_id=calibration_id,
        theorem_ids=theorem_ids,
        item_count=len(grouped),
        annotator_ids=tuple(sorted(panel)),
        disagreement_count=disagreement_count,
        packet_checksum=next(iter(packet_checksums)),
        extractor_version=next(iter(extractor_versions)),
        source_labels_sha256=_source_labels_sha256(label_tuple),
        source_rubric_version=next(iter(rubric_versions)),
        proposed_rubric_revision=proposed_rubric_revision,
    )


def freeze_calibration(
    report: CalibrationReport,
    rubric_revision: str,
    approval_path: Path,
) -> FrozenCalibration:
    """Freezes only from a regular, user-owned approval file bound to exact inputs."""
    content = _read_regular_file(
        approval_path,
        _MAX_APPROVAL_FILE_BYTES,
        "Calibration approval",
        require_current_user=True,
    )
    try:
        approval = HumanFreezeApproval.model_validate_json(content)
    except ValidationError as error:
        raise PermissionError("Calibration approval file is invalid") from error
    report_sha256 = _model_sha256(report.model_dump(mode="json"))
    if (
        approval.calibration_id != report.calibration_id
        or approval.report_sha256 != report_sha256
        or approval.rubric_revision != rubric_revision
    ):
        raise PermissionError("Calibration approval does not bind this report and rubric revision")
    return FrozenCalibration(
        report=report,
        report_sha256=report_sha256,
        rubric_revision=rubric_revision,
        approval_path=str(approval_path),
        approval_sha256=hashlib.sha256(content).hexdigest(),
        approval=approval,
    )


def calibration_report_sha256(report: CalibrationReport) -> str:
    """Returns the exact report hash a human approval file must bind."""
    return _model_sha256(report.model_dump(mode="json"))


def adjudicate_labels(
    labels: Iterable[ImportedHumanLabel],
    decisions: Iterable[AdjudicationDecision],
) -> tuple[AdjudicatedRecord, ...]:
    """Links human decisions to immutable rich originals without overwriting either."""
    grouped = _group_labels(labels)
    decisions_by_blind_id: dict[str, AdjudicationDecision] = {}
    decision_ids: set[str] = set()
    for decision in decisions:
        if decision.decision_id in decision_ids:
            raise ValueError(f"Duplicate adjudication decision ID: {decision.decision_id}")
        if decision.blind_id in decisions_by_blind_id:
            raise ValueError(f"Multiple adjudication decisions for item: {decision.blind_id}")
        decision_ids.add(decision.decision_id)
        decisions_by_blind_id[decision.blind_id] = decision
    if set(decisions_by_blind_id) != set(grouped):
        missing = set(grouped) - set(decisions_by_blind_id)
        unknown = set(decisions_by_blind_id) - set(grouped)
        raise ValueError(
            f"Adjudication decisions must cover exactly the supplied items: {missing=}, {unknown=}"
        )
    records: list[AdjudicatedRecord] = []
    for blind_id in sorted(grouped):
        original_labels = grouped[blind_id]
        decision = decisions_by_blind_id[blind_id]
        expected_source_ids = {label.original.label_id for label in original_labels}
        if set(decision.source_label_ids) != expected_source_ids:
            raise ValueError(
                f"Adjudication must cite every original label for {blind_id}: "
                f"{sorted(expected_source_ids)}"
            )
        for label in original_labels:
            if (
                decision.packet_checksum != label.packet_checksum
                or decision.rubric_version != label.rubric_version
                or decision.extractor_version != label.extractor_version
                or decision.calibration_round != label.original.calibration_round
            ):
                raise ValueError(f"Adjudication provenance mismatch: {blind_id}")
        records.append(
            AdjudicatedRecord(
                blind_id=blind_id,
                original_labels=original_labels,
                decision=decision,
            )
        )
    return tuple(records)


def _parse_human_label(line: str, path: Path, line_number: int) -> HumanLabel:
    try:
        value: Any = json.loads(line)
        return HumanLabel.model_validate(value)
    except (json.JSONDecodeError, ValidationError) as error:
        raise ValueError(f"Invalid human label at {path}:{line_number}") from error


def _group_labels(
    labels: Iterable[ImportedHumanLabel],
) -> dict[str, tuple[ImportedHumanLabel, ...]]:
    grouped_lists: defaultdict[str, list[ImportedHumanLabel]] = defaultdict(list)
    label_ids: set[str] = set()
    annotator_items: set[tuple[str, str]] = set()
    for label in labels:
        label_id = label.original.label_id
        annotator_item = (label.original.annotator_id, label.original.blind_id)
        if label_id in label_ids:
            raise ValueError(f"Duplicate human label ID: {label_id}")
        if annotator_item in annotator_items:
            raise ValueError(f"Duplicate annotator/item label: {annotator_item}")
        label_ids.add(label_id)
        annotator_items.add(annotator_item)
        grouped_lists[label.original.blind_id].append(label)
    if not grouped_lists:
        raise ValueError("At least one human label is required")
    return {
        blind_id: tuple(sorted(values, key=lambda item: item.original.annotator_id))
        for blind_id, values in grouped_lists.items()
    }


def _human_disagreement_reasons(labels: tuple[ImportedHumanLabel, ...]) -> set[str]:
    reasons: set[str] = set()
    if len(labels) < 2:
        reasons.add("missing_independent_human_label")
        return reasons
    if len({label.original.classification for label in labels}) > 1:
        reasons.add("strategy_classification")
    if len({frozenset(label.original.strategy_labels) for label in labels}) > 1:
        reasons.add("strategy_label_set")
    if len({label.original.utilization for label in labels}) > 1:
        reasons.add("utilization")
    if len({label.original.alignments for label in labels}) > 1:
        reasons.add("step_alignment")
    edge_sets = {
        frozenset(
            (edge.predecessor_step_id, edge.successor_step_id)
            for edge in label.original.dependency_edges
        )
        for label in labels
    }
    if len(edge_sets) > 1:
        reasons.add("dependency_edges")
    return reasons


def _unique_automatic(
    outputs: Iterable[AutomaticJudgment],
) -> dict[str, AutomaticJudgment]:
    by_id: dict[str, AutomaticJudgment] = {}
    for output in outputs:
        if output.blind_id in by_id:
            raise ValueError(f"Multiple automatic outputs for item: {output.blind_id}")
        by_id[output.blind_id] = output
    return by_id


def _unique_judges(
    judge_outputs: Iterable[AuxiliaryJudgeOutput],
) -> dict[str, AuxiliaryJudgeOutput]:
    outputs: dict[str, AuxiliaryJudgeOutput] = {}
    for output in judge_outputs:
        if output.blind_id in outputs:
            raise ValueError(f"Multiple auxiliary judge outputs for item: {output.blind_id}")
        outputs[output.blind_id] = output
    return outputs


def _read_regular_file(
    path: Path,
    maximum_bytes: int,
    description: str,
    *,
    require_current_user: bool = False,
) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise PermissionError(
            f"{description} must be a regular non-symlink file: {path}"
        ) from error
    with os.fdopen(descriptor, "rb") as f:
        metadata = os.fstat(f.fileno())
        if not stat.S_ISREG(metadata.st_mode):
            raise PermissionError(f"{description} must be a regular file: {path}")
        if require_current_user and metadata.st_uid != os.getuid():
            raise PermissionError(f"{description} is not owned by the current user: {path}")
        if metadata.st_size > maximum_bytes:
            raise ValueError(f"{description} exceeds {maximum_bytes} bytes: {path}")
        content = f.read(maximum_bytes + 1)
    if len(content) > maximum_bytes:
        raise ValueError(f"{description} exceeds {maximum_bytes} bytes: {path}")
    return content


def _model_sha256(value: Any) -> str:
    content = (
        json.dumps(
            value, allow_nan=False, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _source_labels_sha256(labels: tuple[ImportedHumanLabel, ...]) -> str:
    ordered = sorted(
        labels,
        key=lambda label: (
            label.original.blind_id,
            label.original.annotator_id,
            label.original.label_id,
        ),
    )
    return _model_sha256([label.model_dump(mode="json") for label in ordered])
