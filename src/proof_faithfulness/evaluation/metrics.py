"""Dependency-free, deterministic inter-annotator agreement statistics."""

from __future__ import annotations

from collections import Counter
from collections.abc import Hashable, Iterable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class BinaryAgreement:
    """Agreement measures for paired binary target-match labels."""

    item_count: int
    agreements: int
    raw_agreement: float
    gwet_ac1: float
    cohen_kappa: float
    precision: float
    recall: float
    f1: float


@dataclass(frozen=True)
class LabelScore:
    """First-rater-reference precision, recall, and F1 for one label."""

    label: str
    true_positive: int
    false_positive: int
    false_negative: int
    precision: float
    recall: float
    f1: float


@dataclass(frozen=True)
class MultiLabelAgreement:
    """Jaccard and label-wise agreement for paired label sets."""

    item_count: int
    mean_jaccard: float
    label_scores: tuple[LabelScore, ...]
    macro_precision: float
    macro_recall: float
    macro_f1: float
    micro_precision: float
    micro_recall: float
    micro_f1: float


@dataclass(frozen=True)
class EdgeAgreement:
    """Micro-averaged F1 for paired directed dependency-edge sets."""

    item_count: int
    true_positive: int
    false_positive: int
    false_negative: int
    precision: float
    recall: float
    f1: float


@dataclass(frozen=True)
class NominalAgreement:
    """Agreement measures for paired nominal utilization labels."""

    item_count: int
    raw_agreement: float
    krippendorff_alpha: float
    cohen_kappa: float


@dataclass(frozen=True)
class FleissAgreement:
    """Multi-rater Fleiss kappa and its observed/chance agreement."""

    item_count: int
    rater_count: int
    observed_agreement: float
    chance_agreement: float
    fleiss_kappa: float


def binary_agreement(
    reference_labels: Sequence[bool],
    comparison_labels: Sequence[bool],
) -> BinaryAgreement:
    """Computes raw agreement, Gwet AC1, and Cohen kappa for binary labels.

    Precision and recall treat the first rater as the reference. Gwet AC1 uses the
    pooled positive prevalence and the binary chance term ``2 * p * (1 - p)``.
    """
    pairs = _paired(reference_labels, comparison_labels)
    if any(type(value) is not bool for pair in pairs for value in pair):
        raise TypeError("Binary agreement labels must be bool values")
    item_count = len(pairs)
    agreements = sum(reference == comparison for reference, comparison in pairs)
    raw = agreements / item_count
    reference_positive = sum(reference for reference, _ in pairs)
    comparison_positive = sum(comparison for _, comparison in pairs)
    true_positive = sum(reference and comparison for reference, comparison in pairs)
    false_positive = sum(not reference and comparison for reference, comparison in pairs)
    false_negative = sum(reference and not comparison for reference, comparison in pairs)

    pooled_prevalence = (reference_positive + comparison_positive) / (2 * item_count)
    ac1_chance = 2 * pooled_prevalence * (1 - pooled_prevalence)
    gwet_ac1 = _chance_corrected(raw, ac1_chance)
    reference_prevalence = reference_positive / item_count
    comparison_prevalence = comparison_positive / item_count
    kappa_chance = reference_prevalence * comparison_prevalence + (1 - reference_prevalence) * (
        1 - comparison_prevalence
    )
    cohen_kappa = _chance_corrected(raw, kappa_chance)
    precision, recall, f1 = _precision_recall_f1(
        true_positive,
        false_positive,
        false_negative,
    )
    return BinaryAgreement(
        item_count=item_count,
        agreements=agreements,
        raw_agreement=raw,
        gwet_ac1=gwet_ac1,
        cohen_kappa=cohen_kappa,
        precision=precision,
        recall=recall,
        f1=f1,
    )


def multilabel_agreement(
    reference_label_sets: Sequence[Iterable[str]],
    comparison_label_sets: Sequence[Iterable[str]],
) -> MultiLabelAgreement:
    """Computes mean Jaccard and per-label/micro/macro precision, recall, and F1."""
    raw_pairs = _paired(reference_label_sets, comparison_label_sets)
    pairs = tuple((set(reference), set(comparison)) for reference, comparison in raw_pairs)
    labels = sorted({label for pair in pairs for values in pair for label in values})
    jaccards = [
        len(reference & comparison) / len(reference | comparison) if reference | comparison else 1.0
        for reference, comparison in pairs
    ]
    scores: list[LabelScore] = []
    for label in labels:
        true_positive = sum(
            label in reference and label in comparison for reference, comparison in pairs
        )
        false_positive = sum(
            label not in reference and label in comparison for reference, comparison in pairs
        )
        false_negative = sum(
            label in reference and label not in comparison for reference, comparison in pairs
        )
        precision, recall, f1 = _precision_recall_f1(
            true_positive,
            false_positive,
            false_negative,
        )
        scores.append(
            LabelScore(
                label=label,
                true_positive=true_positive,
                false_positive=false_positive,
                false_negative=false_negative,
                precision=precision,
                recall=recall,
                f1=f1,
            )
        )
    if scores:
        macro_precision = sum(score.precision for score in scores) / len(scores)
        macro_recall = sum(score.recall for score in scores) / len(scores)
        macro_f1 = sum(score.f1 for score in scores) / len(scores)
    else:
        macro_precision = macro_recall = macro_f1 = 1.0
    total_true_positive = sum(score.true_positive for score in scores)
    total_false_positive = sum(score.false_positive for score in scores)
    total_false_negative = sum(score.false_negative for score in scores)
    micro_precision, micro_recall, micro_f1 = _precision_recall_f1(
        total_true_positive,
        total_false_positive,
        total_false_negative,
    )
    return MultiLabelAgreement(
        item_count=len(pairs),
        mean_jaccard=sum(jaccards) / len(jaccards),
        label_scores=tuple(scores),
        macro_precision=macro_precision,
        macro_recall=macro_recall,
        macro_f1=macro_f1,
        micro_precision=micro_precision,
        micro_recall=micro_recall,
        micro_f1=micro_f1,
    )


def edge_agreement(
    reference_edge_sets: Sequence[Iterable[tuple[str, str]]],
    comparison_edge_sets: Sequence[Iterable[tuple[str, str]]],
) -> EdgeAgreement:
    """Computes micro edge precision, recall, and F1 across paired items."""
    raw_pairs = _paired(reference_edge_sets, comparison_edge_sets)
    pairs = tuple((set(reference), set(comparison)) for reference, comparison in raw_pairs)
    true_positive = sum(len(reference & comparison) for reference, comparison in pairs)
    false_positive = sum(len(comparison - reference) for reference, comparison in pairs)
    false_negative = sum(len(reference - comparison) for reference, comparison in pairs)
    precision, recall, f1 = _precision_recall_f1(
        true_positive,
        false_positive,
        false_negative,
    )
    return EdgeAgreement(
        item_count=len(pairs),
        true_positive=true_positive,
        false_positive=false_positive,
        false_negative=false_negative,
        precision=precision,
        recall=recall,
        f1=f1,
    )


def nominal_agreement(
    reference_labels: Sequence[str | None],
    comparison_labels: Sequence[str | None],
) -> NominalAgreement:
    """Computes raw agreement, nominal Krippendorff alpha, and Cohen kappa.

    ``None`` is a missing rating; ``unresolved`` is a real nominal state. Raw agreement
    and kappa use co-rated items. Alpha uses all units through the multi-rater coincidence
    formulation, including partial units with at least two observed ratings.
    """
    all_pairs = _paired(reference_labels, comparison_labels)
    pairs = tuple(
        (reference, comparison)
        for reference, comparison in all_pairs
        if reference is not None and comparison is not None
    )
    if not pairs:
        raise ValueError("Nominal agreement requires at least one co-rated item")
    item_count = len(pairs)
    raw = sum(reference == comparison for reference, comparison in pairs) / item_count
    reference_counts = Counter(reference for reference, _ in pairs)
    comparison_counts = Counter(comparison for _, comparison in pairs)
    labels = set(reference_counts) | set(comparison_counts)
    kappa_chance = sum(
        (reference_counts[label] / item_count) * (comparison_counts[label] / item_count)
        for label in labels
    )
    cohen_kappa = _chance_corrected(raw, kappa_chance)
    krippendorff_alpha = krippendorff_alpha_nominal(
        tuple((reference, comparison) for reference, comparison in all_pairs)
    )
    return NominalAgreement(
        item_count=item_count,
        raw_agreement=raw,
        krippendorff_alpha=krippendorff_alpha,
        cohen_kappa=cohen_kappa,
    )


def krippendorff_alpha_nominal(
    ratings_by_item: Sequence[Sequence[Hashable | None]],
) -> float:
    """Computes nominal Krippendorff alpha for any rater count with missing data.

    Each usable unit contributes coincidence counts normalized by ``m_u - 1``, where
    ``m_u`` is its number of observed ratings. Units with fewer than two ratings cannot
    contribute. When all usable ratings occupy one category, expected disagreement is
    zero; this function returns 1.0 because observed disagreement is also necessarily
    zero rather than emitting a NaN into result artifacts.
    """
    if not ratings_by_item:
        raise ValueError("Krippendorff alpha requires at least one item")
    usable: list[tuple[Hashable, ...]] = []
    for ratings in ratings_by_item:
        observed = tuple(rating for rating in ratings if rating is not None)
        if len(observed) >= 2:
            usable.append(observed)
    if not usable:
        raise ValueError("Krippendorff alpha requires an item with at least two ratings")
    coincidence_count = sum(len(ratings) for ratings in usable)
    observed_disagreement_numerator = 0.0
    pooled_counts: Counter[Hashable] = Counter()
    for ratings in usable:
        pooled_counts.update(ratings)
        unequal_ordered_pairs = sum(
            first != second
            for first_index, first in enumerate(ratings)
            for second_index, second in enumerate(ratings)
            if first_index != second_index
        )
        observed_disagreement_numerator += unequal_ordered_pairs / (len(ratings) - 1)
    observed_disagreement = observed_disagreement_numerator / coincidence_count
    expected_disagreement = sum(
        count * (coincidence_count - count) for count in pooled_counts.values()
    ) / (coincidence_count * (coincidence_count - 1))
    return _disagreement_corrected(observed_disagreement, expected_disagreement)


def fleiss_kappa(ratings_by_item: Sequence[Sequence[Hashable]]) -> FleissAgreement:
    """Computes Fleiss kappa for a fixed panel of at least two raters per item."""
    if not ratings_by_item:
        raise ValueError("Fleiss kappa requires at least one item")
    rater_count = len(ratings_by_item[0])
    if rater_count < 2:
        raise ValueError("Fleiss kappa requires at least two raters per item")
    if any(len(ratings) != rater_count for ratings in ratings_by_item):
        raise ValueError("Fleiss kappa requires the same rater count for every item")
    if any(rating is None for ratings in ratings_by_item for rating in ratings):
        raise ValueError("Fleiss kappa does not accept missing ratings")
    item_agreements: list[float] = []
    pooled_counts: Counter[Hashable] = Counter()
    for ratings in ratings_by_item:
        counts = Counter(ratings)
        pooled_counts.update(ratings)
        agreeing_ordered_pairs = sum(count * (count - 1) for count in counts.values())
        item_agreements.append(agreeing_ordered_pairs / (rater_count * (rater_count - 1)))
    item_count = len(ratings_by_item)
    observed = sum(item_agreements) / item_count
    rating_count = item_count * rater_count
    chance = sum((count / rating_count) ** 2 for count in pooled_counts.values())
    kappa = _chance_corrected(observed, chance)
    return FleissAgreement(
        item_count=item_count,
        rater_count=rater_count,
        observed_agreement=observed,
        chance_agreement=chance,
        fleiss_kappa=kappa,
    )


def _paired[Value](
    reference_values: Sequence[Value],
    comparison_values: Sequence[Value],
) -> tuple[tuple[Value, Value], ...]:
    if len(reference_values) != len(comparison_values):
        raise ValueError("Agreement inputs must have equal lengths")
    if not reference_values:
        raise ValueError("Agreement inputs cannot be empty")
    return tuple(zip(reference_values, comparison_values, strict=True))


def _precision_recall_f1(
    true_positive: int,
    false_positive: int,
    false_negative: int,
) -> tuple[float, float, float]:
    if true_positive == false_positive == false_negative == 0:
        return 1.0, 1.0, 1.0
    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative
    precision = true_positive / precision_denominator if precision_denominator else 0.0
    recall = true_positive / recall_denominator if recall_denominator else 0.0
    denominator = precision + recall
    f1 = 2 * precision * recall / denominator if denominator else 0.0
    return precision, recall, f1


def _chance_corrected(observed: float, chance: float) -> float:
    denominator = 1 - chance
    if denominator == 0:
        return 1.0 if observed == 1 else 0.0
    return (observed - chance) / denominator


def _disagreement_corrected(observed: float, expected: float) -> float:
    if expected == 0:
        return 1.0 if observed == 0 else 0.0
    return 1 - observed / expected
