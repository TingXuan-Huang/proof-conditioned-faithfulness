"""Deterministic identifiers for generation requests."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


def canonical_json(value: Mapping[str, Any]) -> str:
    """Returns a stable JSON representation suitable for identity hashing."""
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def compute_request_id(
    *,
    schema_version: str,
    theorem_id: str,
    statement_hash: str,
    import_hash: str,
    condition: str,
    proof_hash: str,
    prompt_hash: str,
    rendered_prompt_hash: str,
    chat_template_hash: str,
    model_key: str,
    model_id: str,
    model_revision: str,
    backend_config_hash: str,
    sampling: Mapping[str, Any],
    sample_index: int,
) -> str:
    """Computes the request ID from every response-affecting input in PLAN.md S1."""
    identity_parts = (
        schema_version,
        theorem_id,
        statement_hash,
        import_hash,
        condition,
        proof_hash,
        prompt_hash,
        rendered_prompt_hash,
        chat_template_hash,
        model_key,
        model_id,
        model_revision,
        backend_config_hash,
        canonical_json(sampling),
        str(sample_index),
    )
    if any("|" in part for part in identity_parts):
        raise ValueError("Request identity values must not contain the '|' delimiter")
    identity = "|".join(identity_parts).encode("utf-8")
    return hashlib.sha256(identity).hexdigest()
