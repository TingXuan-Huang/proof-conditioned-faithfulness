"""Blinded structured I/O for an auxiliary strategy judge."""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from proof_faithfulness.evaluation.models import (
    AuxiliaryJudgeOutput,
    BlindedAnnotationItem,
)

_MAX_JUDGE_OUTPUT_BYTES = 1024 * 1024


def render_auxiliary_judge_input(
    item: BlindedAnnotationItem,
    packet_checksum: str,
) -> bytes:
    """Renders only blinded evidence; no expected route or run metadata is added."""
    payload = {
        "schema_version": "1.0",
        "blind_id": item.blind_id,
        "packet_checksum": packet_checksum,
        "theorem_statement": item.theorem_statement,
        "supplied_informal_proof": item.supplied_informal_proof,
        "generated_lean_proof": item.generated_lean_proof,
        "rubric_text": item.rubric_text,
        "rubric_version": item.rubric_version,
        "extractor_version": item.extractor_version,
        "signature_evidence": list(item.signature_evidence),
        "allowed_classifications": [
            "match_A",
            "match_B",
            "mixed_or_alternative",
            "unresolved",
        ],
        "instruction": (
            "Judge this item independently and return one JSON object matching the "
            "versioned auxiliary-judge output contract. Do not infer experimental identity."
        ),
    }
    return (
        json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def parse_auxiliary_judge_output(
    content: bytes,
    *,
    expected_blind_id: str,
    expected_packet_checksum: str,
    expected_rubric_version: str,
    expected_extractor_version: str,
) -> AuxiliaryJudgeOutput:
    """Strictly parses one judge object without Markdown extraction or repair."""
    if len(content) > _MAX_JUDGE_OUTPUT_BYTES:
        raise ValueError(f"Auxiliary judge output exceeds {_MAX_JUDGE_OUTPUT_BYTES} bytes")
    try:
        text = content.decode("utf-8")
        value: Any = json.loads(text)
        output = AuxiliaryJudgeOutput.model_validate(value)
    except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
        raise ValueError("Auxiliary judge output is not one valid contract object") from error
    if output.blind_id != expected_blind_id:
        raise ValueError("Auxiliary judge output blind ID does not match its input")
    if (
        output.packet_checksum != expected_packet_checksum
        or output.rubric_version != expected_rubric_version
        or output.extractor_version != expected_extractor_version
    ):
        raise ValueError("Auxiliary judge output packet or tool versions do not match its input")
    return output
