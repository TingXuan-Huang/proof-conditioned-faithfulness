import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import pytest

from proof_faithfulness.evaluation.annotations import (
    adjudicate_labels,
    build_calibration_report,
    build_disagreement_queue,
    build_pre_human_review_queue,
    calibration_report_sha256,
    freeze_calibration,
    select_review_queue,
)
from proof_faithfulness.evaluation.judge import (
    parse_auxiliary_judge_output,
    render_auxiliary_judge_input,
)
from proof_faithfulness.evaluation.metrics import (
    binary_agreement,
    edge_agreement,
    fleiss_kappa,
    krippendorff_alpha_nominal,
    multilabel_agreement,
    nominal_agreement,
)
from proof_faithfulness.evaluation.models import (
    AdjudicationDecision,
    AlignmentEvidence,
    AutomaticJudgment,
    AuxiliaryJudgeOutput,
    BlindedAnnotationItem,
    DependencyEdgeLabel,
    HumanFreezeApproval,
    HumanLabel,
    ImportedHumanLabel,
    SignatureRubric,
    SignatureRule,
    StrategyClass,
    UtilizationState,
)
from proof_faithfulness.evaluation.signatures import (
    classify_local_facts,
    extract_signatures,
    step_coverage,
)

FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures" / "evaluation"
PACKET_CHECKSUM = "d" * 64
RUBRIC_VERSION = "rubric-fixture-v1"
EXTRACTOR_VERSION = "extractor-fixture-v1"
CALIBRATION_ROUND = "calibration-1"


@pytest.fixture
def rubric() -> SignatureRubric:
    return SignatureRubric(
        rubric_version=RUBRIC_VERSION,
        rules=(
            SignatureRule(
                signature_id="a-induction",
                route="A",
                polarity="required",
                evidence_terms=("induction", "Nat.rec"),
            ),
            SignatureRule(
                signature_id="a-no-ring",
                route="A",
                polarity="incompatible",
                evidence_terms=("ring_nf",),
            ),
            SignatureRule(
                signature_id="b-ring",
                route="B",
                polarity="required",
                evidence_terms=("ring_nf",),
            ),
            SignatureRule(
                signature_id="b-no-induction",
                route="B",
                polarity="incompatible",
                evidence_terms=("induction", "Nat.rec"),
            ),
        ),
        library_lookup_terms=("library_shortcut",),
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("by\n  induction n with\n  | zero => simp", "match_A"),
        ("by\n  ring_nf", "match_B"),
        ("by\n  induction n <;> ring_nf", "mixed_or_alternative"),
        ("by\n  simp", "unresolved"),
        ("by\n  exact library_shortcut n", "mixed_or_alternative"),
    ],
)
def test_signature_extraction_classifies_candidate_evidence(
    rubric: SignatureRubric,
    source: str,
    expected: str,
) -> None:
    result = extract_signatures(source, rubric)
    assert result.candidate_classification == expected
    assert result.review_status == "candidate_evidence_requires_human_review"


def test_signature_extraction_ignores_comments_and_strings(rubric: SignatureRubric) -> None:
    source = 'by\n  trace "induction ring_nf"\n  /- Nat.rec -/\n  simp'
    result = extract_signatures(source, rubric)
    assert result.candidate_classification == "unresolved"
    assert result.hits == ()


def test_step_coverage_handles_one_to_many_implicit_and_unused() -> None:
    alignments = (
        _alignment("s1", ("line-2", "line-5"), "one_to_many", "used"),
        _alignment("s2", (), "implicit", "implicit"),
        _alignment("s3", ("decorative-have",), "one_to_one", "unused"),
    )
    assert step_coverage(("s1", "s2", "s3"), alignments) == pytest.approx(2 / 3)


def test_local_fact_utilization_distinguishes_used_from_decorative() -> None:
    assert classify_local_facts(("h_used", "h_decorative"), ("h_used",)) == {
        "h_used": "used",
        "h_decorative": "unused",
    }


def test_auxiliary_judge_io_is_structured_blinded_and_packet_bound() -> None:
    item = BlindedAnnotationItem(
        blind_id="a" * 24,
        theorem_statement="example : True",
        supplied_informal_proof="Truth is immediate.",
        generated_lean_proof="by trivial",
        rubric_text="Classify visible strategy evidence for Route A and Route B.",
        rubric_version=RUBRIC_VERSION,
        extractor_version=EXTRACTOR_VERSION,
        signature_evidence=("No automatic signature found.",),
    )
    rendered = render_auxiliary_judge_input(item, PACKET_CHECKSUM)
    assert b"model_name" not in rendered
    assert b"condition_key" not in rendered
    assert b"sample_index" not in rendered
    output = _judge_output(0, classification="unresolved", uncertain=True).model_dump(mode="json")
    output["blind_id"] = "a" * 24
    parsed = parse_auxiliary_judge_output(
        json.dumps(output).encode(),
        expected_blind_id="a" * 24,
        expected_packet_checksum=PACKET_CHECKSUM,
        expected_rubric_version=RUBRIC_VERSION,
        expected_extractor_version=EXTRACTOR_VERSION,
    )
    assert parsed.classification == "unresolved"


def test_auxiliary_judge_rejects_packet_identity_mismatch() -> None:
    output = _judge_output(0).model_dump(mode="json")
    with pytest.raises(ValueError, match="packet or tool versions"):
        parse_auxiliary_judge_output(
            json.dumps(output).encode(),
            expected_blind_id=_blind_id(0),
            expected_packet_checksum="e" * 64,
            expected_rubric_version=RUBRIC_VERSION,
            expected_extractor_version=EXTRACTOR_VERSION,
        )


def test_pre_human_queue_selects_all_issues_and_ten_item_audit() -> None:
    automatic = [_automatic_output(index) for index in range(20)]
    judges = [_judge_output(index) for index in range(20)]
    judges[0] = _judge_output(0, classification="match_B")
    judges[1] = _judge_output(1, strategy_labels=("different-route",))
    judges[2] = _judge_output(2, utilization="unused")
    judges[3] = _judge_output(3, uncertain=True)
    automatic[4] = _automatic_output(4, classification="unresolved", uncertain=True)

    first = build_pre_human_review_queue(automatic, judges, seed=20260725)
    second = build_pre_human_review_queue(automatic, judges, seed=20260725)

    assert first == second
    assert len(first) == 15
    mandatory = {item.blind_id: item for item in first if item.selection == "mandatory"}
    assert set(mandatory) == {_blind_id(index) for index in range(5)}
    assert "automatic_llm_classification_disagreement" in mandatory[_blind_id(0)].reasons
    assert "automatic_llm_strategy_labels_disagreement" in mandatory[_blind_id(1)].reasons
    assert "automatic_llm_utilization_disagreement" in mandatory[_blind_id(2)].reasons


def test_disagreement_queue_compares_humans_judge_and_automatic_evidence() -> None:
    first = _imported_label(0, "ann-1", "match_A", ("induction",), "used")
    second = _imported_label(0, "ann-2", "match_B", ("algebra",), "unused")
    queue = build_disagreement_queue(
        (first, second),
        judge_outputs=(_judge_output(0),),
        automatic_outputs=(_automatic_output(0, classification="unresolved"),),
    )
    assert len(queue) == 1
    assert "strategy_classification" in queue[0].reasons
    assert "human_llm_strategy_disagreement" in queue[0].reasons
    assert "human_automatic_strategy_disagreement" in queue[0].reasons


@pytest.mark.parametrize(
    ("evidence_kind", "field", "value"),
    [
        ("automatic", "packet_checksum", "e" * 64),
        ("automatic", "rubric_version", "rubric-other"),
        ("automatic", "extractor_version", "extractor-other"),
        ("judge", "packet_checksum", "e" * 64),
        ("judge", "rubric_version", "rubric-other"),
        ("judge", "extractor_version", "extractor-other"),
    ],
)
def test_disagreement_queue_rejects_review_evidence_provenance_mismatch(
    evidence_kind: str,
    field: str,
    value: str,
) -> None:
    labels = (
        _imported_label(0, "ann-1", "match_A", ("route",), "used"),
        _imported_label(0, "ann-2", "match_A", ("route",), "used"),
    )
    with pytest.raises(ValueError, match="provenance mismatch"):
        if evidence_kind == "automatic":
            build_disagreement_queue(
                labels,
                automatic_outputs=(
                    _automatic_output(0).model_copy(update={field: value}),
                ),
            )
        else:
            build_disagreement_queue(
                labels,
                judge_outputs=(
                    _judge_output(0).model_copy(update={field: value}),
                ),
            )


def test_review_queue_includes_missing_second_labels_and_is_deterministic() -> None:
    labels = tuple(
        _imported_label(index, "ann-1", "match_A", ("route",), "used") for index in range(12)
    )
    disagreement = build_disagreement_queue(labels)
    first = select_review_queue(labels, disagreement, seed=20260725, minimum_audit=3)
    second = select_review_queue(labels, disagreement, seed=20260725, minimum_audit=3)
    assert first == second
    assert len(first) == 12


def test_adjudication_preserves_rich_original_alignments() -> None:
    first = _imported_label(0, "ann-1", "match_A", ("induction",), "used")
    second = _imported_label(0, "ann-2", "match_B", ("algebra",), "unused")
    decision = AdjudicationDecision(
        decision_id="decision-1",
        blind_id=first.original.blind_id,
        packet_checksum=PACKET_CHECKSUM,
        adjudicator_id="human-adjudicator",
        calibration_round=CALIBRATION_ROUND,
        rubric_version=RUBRIC_VERSION,
        extractor_version=EXTRACTOR_VERSION,
        source_label_ids=(first.original.label_id, second.original.label_id),
        classification="unresolved",
        strategy_labels=(),
        utilization="unresolved",
        alignments=(_alignment("s1", (), "implicit", "implicit"),),
        explanation="The independent labels could not be reconciled.",
    )
    records = adjudicate_labels((first, second), (decision,))
    assert records[0].original_labels == (first, second)
    assert records[0].original_labels[0].original.alignments
    assert records[0].decision.alignments == decision.alignments


def test_auxiliary_judge_cannot_be_used_as_adjudicator() -> None:
    value = {
        "adjudicator_source": "llm_judge",
        "decision_id": "decision-1",
        "blind_id": _blind_id(0),
        "packet_checksum": PACKET_CHECKSUM,
        "adjudicator_id": "judge-fixture-v1",
        "calibration_round": CALIBRATION_ROUND,
        "rubric_version": RUBRIC_VERSION,
        "extractor_version": EXTRACTOR_VERSION,
        "source_label_ids": ["label-0-ann-1", "label-0-ann-2"],
        "classification": "unresolved",
        "strategy_labels": [],
        "utilization": "unresolved",
        "explanation": "A judge must not adjudicate its own disagreements.",
    }
    with pytest.raises(ValueError, match="human"):
        AdjudicationDecision.model_validate(value)


def test_calibration_requires_same_panel_on_every_item() -> None:
    valid = [
        _imported_label(index, annotator, "match_A", ("route",), "used")
        for index in range(5)
        for annotator in ("ann-1", "ann-2")
    ]
    report = build_calibration_report(CALIBRATION_ROUND, valid, "rubric-draft-2")
    assert report.annotator_ids == ("ann-1", "ann-2")
    assert report.packet_checksum == PACKET_CHECKSUM
    assert report.extractor_version == EXTRACTOR_VERSION

    missing = tuple(label for label in valid if label.original.label_id != "label-4-ann-2")
    with pytest.raises(ValueError, match="lacks two annotators"):
        build_calibration_report(CALIBRATION_ROUND, missing, "rubric-draft-2")

    changed_panel = valid[:-1] + [_imported_label(4, "ann-3", "match_A", ("route",), "used")]
    with pytest.raises(ValueError, match="same independent annotator panel"):
        build_calibration_report(CALIBRATION_ROUND, changed_panel, "rubric-draft-2")

    other_packet_original = valid[-1].original.model_copy(update={"packet_checksum": "e" * 64})
    mixed_packet = valid[:-1] + [
        valid[-1].model_copy(
            update={"packet_checksum": "e" * 64, "original": other_packet_original}
        )
    ]
    with pytest.raises(ValueError, match="one packet"):
        build_calibration_report(CALIBRATION_ROUND, mixed_packet, "rubric-draft-2")


def test_calibration_freeze_requires_bound_regular_human_file(tmp_path: Path) -> None:
    labels = tuple(
        _imported_label(index, annotator, "match_A", ("route",), "used")
        for index in range(5)
        for annotator in ("ann-1", "ann-2")
    )
    report = build_calibration_report(CALIBRATION_ROUND, labels, "rubric-final-1")
    approval = HumanFreezeApproval(
        approval_id="human-approval-record-17",
        decision="approve_calibration_freeze",
        approved_by="qualified-reviewer",
        approved_at=datetime(2026, 7, 25, tzinfo=UTC),
        calibration_id=CALIBRATION_ROUND,
        report_sha256=calibration_report_sha256(report),
        rubric_revision="rubric-final-1",
    )
    approval_path = tmp_path / "approval.json"
    approval_path.write_text(approval.model_dump_json(), encoding="utf-8")

    frozen = freeze_calibration(report, "rubric-final-1", approval_path)

    assert frozen.report == report
    assert frozen.report_sha256 == approval.report_sha256
    assert frozen.approval_sha256
    symlink = tmp_path / "approval-link.json"
    symlink.symlink_to(approval_path)
    with pytest.raises(PermissionError, match="non-symlink"):
        freeze_calibration(report, "rubric-final-1", symlink)


def test_calibration_freeze_rejects_self_attested_mismatch(tmp_path: Path) -> None:
    labels = tuple(
        _imported_label(index, annotator, "match_A", ("route",), "used")
        for index in range(5)
        for annotator in ("ann-1", "ann-2")
    )
    report = build_calibration_report(CALIBRATION_ROUND, labels, "rubric-final-1")
    approval_path = tmp_path / "approval.json"
    approval_path.write_text(
        HumanFreezeApproval(
            approval_id="wrong-approval",
            decision="approve_calibration_freeze",
            approved_by="qualified-reviewer",
            approved_at=datetime(2026, 7, 25, tzinfo=UTC),
            calibration_id=CALIBRATION_ROUND,
            report_sha256="0" * 64,
            rubric_revision="rubric-final-1",
        ).model_dump_json(),
        encoding="utf-8",
    )
    with pytest.raises(PermissionError, match="does not bind"):
        freeze_calibration(report, "rubric-final-1", approval_path)


def test_calibration_approval_cannot_replay_across_different_source_labels(
    tmp_path: Path,
) -> None:
    all_a = tuple(
        _imported_label(index, annotator, "match_A", ("route-a",), "used")
        for index in range(5)
        for annotator in ("ann-1", "ann-2")
    )
    all_b = tuple(
        _imported_label(index, annotator, "match_B", ("route-b",), "used")
        for index in range(5)
        for annotator in ("ann-1", "ann-2")
    )
    report_a = build_calibration_report(CALIBRATION_ROUND, all_a, "rubric-final-1")
    report_b = build_calibration_report(CALIBRATION_ROUND, all_b, "rubric-final-1")
    assert report_a.disagreement_count == report_b.disagreement_count == 0
    assert report_a.source_labels_sha256 != report_b.source_labels_sha256
    approval_path = tmp_path / "approval-a.json"
    approval_path.write_text(
        HumanFreezeApproval(
            approval_id="approval-for-a",
            decision="approve_calibration_freeze",
            approved_by="qualified-reviewer",
            approved_at=datetime(2026, 7, 25, tzinfo=UTC),
            calibration_id=CALIBRATION_ROUND,
            report_sha256=calibration_report_sha256(report_a),
            rubric_revision="rubric-final-1",
        ).model_dump_json(),
        encoding="utf-8",
    )

    with pytest.raises(PermissionError, match="does not bind"):
        freeze_calibration(report_b, "rubric-final-1", approval_path)


def test_agreement_statistics_match_hand_computed_ten_item_fixture() -> None:
    fixture = json.loads((FIXTURE_ROOT / "agreement_10.json").read_text(encoding="utf-8"))

    binary = binary_agreement(fixture["binary"]["reference"], fixture["binary"]["comparison"])
    for field, expected in fixture["binary"]["expected"].items():
        assert round(getattr(binary, field), 4) == expected

    multilabel = multilabel_agreement(
        fixture["multilabel"]["reference"],
        fixture["multilabel"]["comparison"],
    )
    for field, expected in fixture["multilabel"]["expected"].items():
        assert round(getattr(multilabel, field), 4) == expected

    reference_edges = [
        [tuple(edge) for edge in edge_set] for edge_set in fixture["edges"]["reference"]
    ]
    comparison_edges = [
        [tuple(edge) for edge in edge_set] for edge_set in fixture["edges"]["comparison"]
    ]
    edges = edge_agreement(reference_edges, comparison_edges)
    for field, expected in fixture["edges"]["expected"].items():
        assert round(getattr(edges, field), 4) == expected

    nominal = nominal_agreement(
        fixture["nominal"]["reference"],
        fixture["nominal"]["comparison"],
    )
    for field, expected in fixture["nominal"]["expected"].items():
        assert round(getattr(nominal, field), 4) == expected


def test_multi_rater_krippendorff_alpha_handles_missing_ratings() -> None:
    ratings = (
        ("a", "a", "a"),
        ("a", "b", None),
        ("b", "b", "a"),
        (None, "b", "b"),
    )
    assert krippendorff_alpha_nominal(ratings) == pytest.approx(0.28)


def test_krippendorff_alpha_constant_category_has_explicit_perfect_result() -> None:
    assert krippendorff_alpha_nominal((("used", "used"), ("used", None, "used"))) == 1.0


def test_fleiss_kappa_matches_hand_computed_three_rater_fixture() -> None:
    result = fleiss_kappa(
        (
            ("a", "a", "a"),
            ("a", "a", "b"),
            ("b", "b", "b"),
            ("a", "b", "b"),
        )
    )
    assert result.observed_agreement == pytest.approx(2 / 3)
    assert result.chance_agreement == pytest.approx(1 / 2)
    assert result.fleiss_kappa == pytest.approx(1 / 3)
    assert fleiss_kappa((("same", "same"),)).fleiss_kappa == 1.0
    with pytest.raises(ValueError, match="missing ratings"):
        fleiss_kappa((("a", None),))


def test_set_metrics_handle_one_sided_and_both_empty_denominators() -> None:
    missing_prediction = multilabel_agreement((("a",),), ((),))
    assert missing_prediction.label_scores[0].precision == 0.0
    assert missing_prediction.label_scores[0].recall == 0.0
    assert missing_prediction.label_scores[0].f1 == 0.0

    spurious_prediction = multilabel_agreement(((),), (("a",),))
    assert spurious_prediction.label_scores[0].precision == 0.0
    assert spurious_prediction.label_scores[0].recall == 0.0
    assert spurious_prediction.label_scores[0].f1 == 0.0

    both_empty = multilabel_agreement(((),), ((),))
    assert both_empty.mean_jaccard == 1.0
    assert both_empty.macro_precision == 1.0
    assert both_empty.macro_recall == 1.0
    assert both_empty.macro_f1 == 1.0
    assert both_empty.micro_precision == 1.0
    assert both_empty.micro_recall == 1.0
    assert both_empty.micro_f1 == 1.0


def _imported_label(
    index: int,
    annotator: str,
    classification: StrategyClass,
    strategy_labels: tuple[str, ...],
    utilization: UtilizationState,
) -> ImportedHumanLabel:
    blind_id = _blind_id(index)
    alignment = _alignment("s1", ("formal-s1",), "one_to_one", utilization)
    label = HumanLabel(
        label_id=f"label-{index}-{annotator}",
        blind_id=blind_id,
        packet_checksum=PACKET_CHECKSUM,
        annotator_id=annotator,
        calibration_round=CALIBRATION_ROUND,
        rubric_version=RUBRIC_VERSION,
        extractor_version=EXTRACTOR_VERSION,
        classification=classification,
        strategy_labels=strategy_labels,
        utilization=utilization,
        alignments=(alignment,),
        dependency_edges=(DependencyEdgeLabel(predecessor_step_id="s1", successor_step_id="s2"),),
        explanation="Fixture label.",
    )
    return ImportedHumanLabel(
        request_id=f"{index + 1:064x}",
        theorem_id=f"theorem-{index}",
        packet_checksum=PACKET_CHECKSUM,
        rubric_version=RUBRIC_VERSION,
        extractor_version=EXTRACTOR_VERSION,
        source_path=f"labels-{annotator}.jsonl",
        source_line=index + 1,
        source_sha256="f" * 64,
        original=label,
    )


def _automatic_output(
    index: int,
    *,
    classification: StrategyClass = "match_A",
    strategy_labels: tuple[str, ...] = ("route",),
    utilization: UtilizationState = "used",
    uncertain: bool = False,
) -> AutomaticJudgment:
    return AutomaticJudgment(
        blind_id=_blind_id(index),
        packet_checksum=PACKET_CHECKSUM,
        rubric_version=RUBRIC_VERSION,
        extractor_version=EXTRACTOR_VERSION,
        classification=classification,
        strategy_labels=strategy_labels,
        utilization=utilization,
        uncertain=uncertain,
    )


def _judge_output(
    index: int,
    *,
    classification: StrategyClass = "match_A",
    strategy_labels: tuple[str, ...] = ("route",),
    utilization: UtilizationState = "used",
    uncertain: bool = False,
) -> AuxiliaryJudgeOutput:
    return AuxiliaryJudgeOutput(
        judge_version="judge-fixture-v1",
        blind_id=_blind_id(index),
        packet_checksum=PACKET_CHECKSUM,
        rubric_version=RUBRIC_VERSION,
        extractor_version=EXTRACTOR_VERSION,
        classification=classification,
        strategy_labels=strategy_labels,
        utilization=utilization,
        strategy_expressibility_uncertain=uncertain,
        explanation="Fixture judge output.",
    )


def _alignment(
    step_id: str,
    evidence_ids: tuple[str, ...],
    alignment_type: Literal["one_to_one", "one_to_many", "many_to_one", "implicit"],
    utilization: UtilizationState,
) -> AlignmentEvidence:
    return AlignmentEvidence(
        informal_step_ids=(step_id,),
        formal_evidence_ids=evidence_ids,
        alignment_type=alignment_type,
        utilization=utilization,
        confidence=1.0,
    )


def _blind_id(index: int) -> str:
    return chr(ord("a") + index) * 24
