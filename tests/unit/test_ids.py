"""Tests for deterministic generation request identifiers."""

import math
from collections.abc import Mapping
from typing import Any

import pytest

from proof_faithfulness.ids import canonical_json, compute_request_id


def _request_id(
    *,
    theorem_id: str = "theorem-001",
    sampling: Mapping[str, Any] | None = None,
    sample_index: int = 0,
) -> str:
    if sampling is None:
        sampling = {"temperature": 0.2, "top_p": 1.0, "max_tokens": 8192}
    return compute_request_id(
        schema_version="1.0",
        theorem_id=theorem_id,
        statement_hash="a" * 64,
        import_hash="b" * 64,
        condition="proof_a",
        proof_hash="c" * 64,
        prompt_hash="d" * 64,
        rendered_prompt_hash="f" * 64,
        chat_template_hash="e" * 64,
        model_key="model_key",
        model_id="model/name",
        model_revision="model@revision",
        backend_config_hash="9" * 64,
        sampling=sampling,
        sample_index=sample_index,
    )


def test_compute_request_id_same_input_is_byte_identical() -> None:
    assert _request_id() == _request_id()


def test_compute_request_id_changes_for_response_affecting_input() -> None:
    baseline = _request_id()
    assert _request_id(sample_index=1) != baseline
    assert _request_id(sampling={"temperature": 0.3}) != baseline


def test_compute_request_id_changes_for_prompt_content_and_model_identity() -> None:
    baseline = _request_id()
    common = {
        "schema_version": "1.0",
        "theorem_id": "theorem-001",
        "statement_hash": "a" * 64,
        "import_hash": "b" * 64,
        "condition": "proof_a",
        "proof_hash": "c" * 64,
        "prompt_hash": "d" * 64,
        "rendered_prompt_hash": "f" * 64,
        "chat_template_hash": "e" * 64,
        "model_key": "model_key",
        "model_id": "model/name",
        "model_revision": "model@revision",
        "backend_config_hash": "9" * 64,
        "sampling": {"temperature": 0.2, "top_p": 1.0, "max_tokens": 8192},
        "sample_index": 0,
    }
    assert compute_request_id(**{**common, "rendered_prompt_hash": "0" * 64}) != baseline
    assert compute_request_id(**{**common, "model_key": "other_key"}) != baseline
    assert compute_request_id(**{**common, "model_id": "other/model"}) != baseline


def test_canonical_json_ignores_mapping_order() -> None:
    assert canonical_json({"b": 2, "a": 1}) == canonical_json({"a": 1, "b": 2})


def test_compute_request_id_rejects_delimiter_collision() -> None:
    with pytest.raises(ValueError, match="delimiter"):
        _request_id(theorem_id="theorem|001")


def test_canonical_json_rejects_non_finite_float() -> None:
    with pytest.raises(ValueError, match="JSON compliant"):
        canonical_json({"temperature": math.inf})
