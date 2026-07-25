"""Normative GenerationResponse persistence and resume verification."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from proof_faithfulness.artifacts import ArtifactError, RunArtifactStore, sha256_bytes
from proof_faithfulness.models import AdapterResult, ModelInput
from proof_faithfulness.schema import GenerationResponse, GitCommit, Hash, NonEmptyString


class ResponseArtifactError(RuntimeError):
    """Raised when a successful adapter result cannot be persisted safely."""


class TerminalArtifactConflictError(ResponseArtifactError):
    """Raised rather than replacing an already verified terminal artifact."""


class ResponseFailureRecord(BaseModel):
    """Immutable metadata for a provider response that could not become terminal."""

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    request_id: Hash
    model_key: NonEmptyString
    revision: NonEmptyString
    attempt: int = Field(gt=0)
    error_type: NonEmptyString
    error_message: NonEmptyString
    provider_request_id: str | None = None
    raw_path: str | None = None
    raw_sha256: Hash | None = None
    raw_truncated: bool = False
    recorded_at: datetime
    harness_git_commit: GitCommit


def response_relative_path(request_id: str) -> str:
    """Returns the canonical path for a successful response artifact."""
    return f"responses/{request_id}/response.json"


def response_failure_relative_path(request_id: str, attempt: int) -> str:
    """Returns the metadata path for one non-terminal provider response."""
    return f"responses/{request_id}/failures/attempt-{attempt:04d}/failure.json"


def write_response_failure(
    *,
    store: RunArtifactStore,
    model_input: ModelInput,
    attempt: int,
    error: Exception,
    raw_response: bytes | None,
    provider_request_id: str | None,
    raw_truncated: bool,
    recorded_at: datetime,
    harness_git_commit: str,
) -> ResponseFailureRecord:
    """Persists exact received bytes and failure metadata without overwriting evidence."""
    request = model_input.request
    metadata_path = Path(response_failure_relative_path(request.request_id, attempt))
    raw_path = metadata_path.with_name("raw-response.bin") if raw_response is not None else None
    if raw_path is not None and raw_response is not None:
        _write_once(store=store, relative_path=raw_path, content=raw_response)
    message = str(error).strip() or type(error).__name__
    record = ResponseFailureRecord(
        request_id=request.request_id,
        model_key=request.model_key,
        revision=request.model_revision,
        attempt=attempt,
        error_type=type(error).__name__,
        error_message=message,
        provider_request_id=provider_request_id,
        raw_path=str(raw_path) if raw_path is not None else None,
        raw_sha256=sha256_bytes(raw_response) if raw_response is not None else None,
        raw_truncated=raw_truncated,
        recorded_at=recorded_at,
        harness_git_commit=harness_git_commit,
    )
    content = (
        json.dumps(
            record.model_dump(mode="json"),
            allow_nan=False,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )
    _write_once(store=store, relative_path=metadata_path, content=content)
    return record


def write_generation_response(
    *,
    store: RunArtifactStore,
    model_input: ModelInput,
    result: AdapterResult,
    started_at: datetime,
    completed_at: datetime,
    harness_git_commit: str,
) -> GenerationResponse:
    """Validates and atomically persists one successful model response."""
    request = model_input.request
    if result.request_id != request.request_id:
        raise ResponseArtifactError("Adapter result request_id does not match its request")
    try:
        raw = result.raw_response.decode("utf-8")
        json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ResponseArtifactError("Adapter raw response is not valid JSON") from error
    latency_s = (completed_at - started_at).total_seconds()
    response = GenerationResponse(
        schema_version="1.0",
        request_id=request.request_id,
        model_key=request.model_key,
        revision=request.model_revision,
        raw=raw,
        text=result.text,
        finish_reason=result.finish_reason,
        usage=result.token_usage,
        usd_cost=result.usd_cost,
        latency_s=latency_s,
        started_at=started_at,
        completed_at=completed_at,
        harness_git_commit=harness_git_commit,
    )
    relative_path = response_relative_path(request.request_id)
    existing = load_verified_response(store=store, model_input=model_input)
    if existing is not None:
        if existing == response:
            return existing
        raise TerminalArtifactConflictError(
            f"Refusing to replace verified response: {request.request_id}"
        )
    _quarantine_invalid_response(store=store, relative_path=relative_path)
    try:
        store.write_json(relative_path, response.model_dump(mode="json"))
    except (ArtifactError, OSError) as error:
        raise ResponseArtifactError(
            f"Unable to persist response artifact: {request.request_id}"
        ) from error
    if not store.verified(relative_path):
        raise ResponseArtifactError(f"Response checksum verification failed: {request.request_id}")
    return response


def load_verified_response(
    *,
    store: RunArtifactStore,
    model_input: ModelInput,
) -> GenerationResponse | None:
    """Returns a terminal response only if checksum, schema, and identity verify."""
    request = model_input.request
    relative_path = response_relative_path(request.request_id)
    if not store.verified(relative_path):
        return None
    path = store.path / relative_path
    try:
        response = GenerationResponse.model_validate_json(path.read_bytes())
    except (OSError, ValidationError):
        return None
    expected_identity = (request.request_id, request.model_key, request.model_revision)
    actual_identity = (response.request_id, response.model_key, response.revision)
    if not isinstance(response.raw, str):
        return None
    return response if actual_identity == expected_identity else None


def _quarantine_invalid_response(*, store: RunArtifactStore, relative_path: str) -> None:
    source = store.path / relative_path
    sidecar = source.with_name(f"{source.name}.sha256")
    if not source.exists() and not sidecar.exists():
        return
    if source.is_symlink() or sidecar.is_symlink():
        raise ResponseArtifactError("Invalid response artifact uses a symlink")
    try:
        source_bytes = source.read_bytes() if source.exists() else b""
        sidecar_bytes = sidecar.read_bytes() if sidecar.exists() else b""
    except OSError as error:
        raise ResponseArtifactError("Unable to retain invalid response artifact") from error
    digest = sha256_bytes(source_bytes + b"\0" + sidecar_bytes)
    quarantine_root = Path(relative_path).parent / "quarantine" / digest
    _write_quarantine_once(
        store=store,
        relative_path=quarantine_root / "response.json.invalid",
        content=source_bytes,
    )
    _write_quarantine_once(
        store=store,
        relative_path=quarantine_root / "recorded-checksum.txt",
        content=sidecar_bytes,
    )
    metadata = {
        "schema_version": "1.0",
        "original_path": relative_path,
        "retained_response_sha256": sha256_bytes(source_bytes),
        "retained_sidecar_sha256": sha256_bytes(sidecar_bytes),
    }
    metadata_path = quarantine_root / "metadata.json"
    metadata_target = store.path / metadata_path
    if metadata_target.exists():
        try:
            existing_metadata = json.loads(metadata_target.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ResponseArtifactError(
                "Existing response quarantine metadata is invalid"
            ) from error
        if not store.verified(metadata_path) or existing_metadata != metadata:
            raise ResponseArtifactError("Existing response quarantine metadata is inconsistent")
    else:
        store.write_json(metadata_path, metadata)


def _write_quarantine_once(
    *,
    store: RunArtifactStore,
    relative_path: Path,
    content: bytes,
) -> None:
    target = store.path / relative_path
    if target.exists():
        if not store.verified(relative_path) or target.read_bytes() != content:
            raise ResponseArtifactError("Existing response quarantine is inconsistent")
        return
    store.write_bytes(relative_path, content)


def _write_once(
    *,
    store: RunArtifactStore,
    relative_path: Path,
    content: bytes,
) -> None:
    target = store.path / relative_path
    if target.exists():
        if not store.verified(relative_path) or target.read_bytes() != content:
            raise ResponseArtifactError(f"Existing failure evidence conflicts: {relative_path}")
        return
    try:
        store.write_bytes(relative_path, content)
    except (ArtifactError, OSError) as error:
        raise ResponseArtifactError(
            f"Unable to persist response failure evidence: {relative_path}"
        ) from error
