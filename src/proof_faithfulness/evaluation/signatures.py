"""Deterministic extraction and scoring of preregistered proof signatures."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable

from proof_faithfulness.evaluation.models import (
    AlignmentEvidence,
    SignatureExtraction,
    SignatureHit,
    SignatureRubric,
    StrategyClass,
)

EXTRACTOR_VERSION = "literal-signatures-1"


def extract_signatures(source: str, rubric: SignatureRubric) -> SignatureExtraction:
    """Extracts candidate evidence after removing comments and string literals.

    Evidence terms are preregistered rubric inputs, not regular expressions. Matching
    normalizes whitespace and applies identifier boundaries where appropriate. This
    keeps comments and arbitrary output strings from manufacturing strategy evidence.
    The resulting classification is a queueing aid that always requires human review;
    it is never an adjudication or final strategy label.
    """
    searchable_source = _normalize_source(source)
    hits: list[SignatureHit] = []
    for rule in sorted(rubric.rules, key=lambda item: item.signature_id):
        matched_terms = tuple(
            term for term in rule.evidence_terms if _contains_term(searchable_source, term)
        )
        matched = (
            bool(matched_terms)
            if rule.match_mode == "any"
            else (len(matched_terms) == len(rule.evidence_terms))
        )
        if matched:
            hits.append(
                SignatureHit(
                    signature_id=rule.signature_id,
                    route=rule.route,
                    polarity=rule.polarity,
                    matched_terms=matched_terms,
                )
            )
    library_hits = tuple(
        term
        for term in sorted(rubric.library_lookup_terms)
        if _contains_term(searchable_source, term)
    )
    classification = classify_signature_hits(rubric, hits, library_hits)
    return SignatureExtraction(
        extractor_version=EXTRACTOR_VERSION,
        source_sha256=hashlib.sha256(source.encode("utf-8")).hexdigest(),
        rubric_version=rubric.rubric_version,
        hits=tuple(hits),
        library_lookup_terms=library_hits,
        candidate_classification=classification,
    )


def classify_signature_hits(
    rubric: SignatureRubric,
    hits: Iterable[SignatureHit],
    library_lookup_terms: Iterable[str] = (),
) -> StrategyClass:
    """Classifies evidence while treating direct library lookup as alternative."""
    hit_list = tuple(hits)
    hit_ids = {hit.signature_id for hit in hit_list}
    if tuple(library_lookup_terms):
        return "mixed_or_alternative"

    required_by_route = {
        route: {
            rule.signature_id
            for rule in rubric.rules
            if rule.route == route and rule.polarity == "required"
        }
        for route in ("A", "B")
    }
    incompatible_by_route = {
        route: {
            rule.signature_id
            for rule in rubric.rules
            if rule.route == route and rule.polarity == "incompatible"
        }
        for route in ("A", "B")
    }
    complete_routes = {
        route
        for route in ("A", "B")
        if required_by_route[route] <= hit_ids
        and not incompatible_by_route[route].intersection(hit_ids)
    }
    positive_routes = {
        route for route in ("A", "B") if required_by_route[route].intersection(hit_ids)
    }
    conflicting_routes = {
        route
        for route in ("A", "B")
        if required_by_route[route].intersection(hit_ids)
        and incompatible_by_route[route].intersection(hit_ids)
    }
    if len(complete_routes) == 1 and len(positive_routes) == 1 and not conflicting_routes:
        route = next(iter(complete_routes))
        return "match_A" if route == "A" else "match_B"
    if len(positive_routes) > 1 or conflicting_routes:
        return "mixed_or_alternative"
    return "unresolved"


def step_coverage(
    strategy_essential_step_ids: Iterable[str],
    alignments: Iterable[AlignmentEvidence],
) -> float:
    """Computes coverage over unique strategy-essential steps.

    Explicit unused facts do not count as covered. An implicit alignment does count,
    because the annotation explicitly records that the mathematical step is present
    without a standalone formal span.
    """
    required = set(strategy_essential_step_ids)
    if not required:
        raise ValueError("Step coverage requires at least one strategy-essential step")
    covered = {
        step_id
        for alignment in alignments
        if alignment.utilization in {"used", "implicit"}
        for step_id in alignment.informal_step_ids
        if step_id in required
    }
    return len(covered) / len(required)


def classify_local_facts(
    introduced_fact_ids: Iterable[str],
    used_fact_ids: Iterable[str],
) -> dict[str, str]:
    """Classifies introduced local facts as used or decorative/unused."""
    introduced = tuple(introduced_fact_ids)
    if len(set(introduced)) != len(introduced):
        raise ValueError("Introduced local fact IDs must be unique")
    used = set(used_fact_ids)
    unknown = used - set(introduced)
    if unknown:
        raise ValueError(f"Used local fact IDs were not introduced: {sorted(unknown)}")
    return {fact_id: "used" if fact_id in used else "unused" for fact_id in introduced}


def _normalize_source(source: str) -> str:
    return re.sub(r"\s+", " ", _strip_comments_and_strings(source)).strip()


def _contains_term(source: str, term: str) -> bool:
    normalized_term = re.sub(r"\s+", " ", term).strip()
    prefix = r"(?<![A-Za-z0-9_'])" if _is_identifier_character(normalized_term[0]) else ""
    suffix = r"(?![A-Za-z0-9_'])" if _is_identifier_character(normalized_term[-1]) else ""
    return re.search(f"{prefix}{re.escape(normalized_term)}{suffix}", source) is not None


def _is_identifier_character(character: str) -> bool:
    return character.isalnum() or character in {"_", "'"}


def _strip_comments_and_strings(source: str) -> str:
    output: list[str] = []
    index = 0
    block_depth = 0
    in_line_comment = False
    in_string = False
    escaped = False
    while index < len(source):
        pair = source[index : index + 2]
        character = source[index]
        if in_line_comment:
            if character == "\n":
                in_line_comment = False
                output.append(character)
            else:
                output.append(" ")
            index += 1
            continue
        if block_depth:
            if pair == "/-":
                block_depth += 1
                output.extend((" ", " "))
                index += 2
            elif pair == "-/":
                block_depth -= 1
                output.extend((" ", " "))
                index += 2
            else:
                output.append("\n" if character == "\n" else " ")
                index += 1
            continue
        if in_string:
            output.append("\n" if character == "\n" else " ")
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            index += 1
            continue
        if pair == "--":
            in_line_comment = True
            output.extend((" ", " "))
            index += 2
        elif pair == "/-":
            block_depth = 1
            output.extend((" ", " "))
            index += 2
        elif character == '"':
            in_string = True
            output.append(" ")
            index += 1
        else:
            output.append(character)
            index += 1
    return "".join(output)
