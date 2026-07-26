"""Checksummed persistence for request-bound trusted Lean checker results."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path

from pydantic import ValidationError

from proof_faithfulness.artifacts import ArtifactError, RunArtifactStore
from proof_faithfulness.lean.checker import CheckOutcome
from proof_faithfulness.schema import LeanCheckResult


class LeanArtifactError(RuntimeError):
    """Raised when trusted checker evidence is absent, corrupt, or inconsistent."""


CandidateChecker = Callable[[str], CheckOutcome]


def check_and_persist_candidate(
    *,
    store: RunArtifactStore,
    request_id: str,
    candidate: str,
    checker: CandidateChecker,
) -> CheckOutcome:
    """Run a trusted checker once, persisting or reusing immutable evidence."""
    persisted = load_check_outcome(
        store=store,
        request_id=request_id,
        candidate=candidate,
    )
    if persisted is not None:
        return persisted
    outcome = checker(candidate)
    if outcome.result.request_id != request_id:
        raise LeanArtifactError("Checker result request_id does not match the candidate")
    persist_check_outcome(
        store=store,
        request_id=request_id,
        candidate=candidate,
        outcome=outcome,
    )
    return outcome


def persist_check_outcome(
    *,
    store: RunArtifactStore,
    request_id: str,
    candidate: str,
    outcome: CheckOutcome,
) -> None:
    """Persist one request-bound checker outcome and its exact diagnostics."""
    if outcome.result.request_id != request_id:
        raise LeanArtifactError("Checker result request_id does not match the candidate")
    root = Path("lean") / request_id
    stdout_path = root / "stdout.txt"
    stderr_path = root / "stderr.txt"
    _write_verified_bytes(store, stdout_path, outcome.stdout.encode("utf-8"))
    _write_verified_bytes(store, stderr_path, outcome.stderr.encode("utf-8"))
    assembled_path: Path | None = None
    if outcome.assembled_source is not None:
        assembled_path = root / "Candidate.lean"
        _write_verified_bytes(
            store,
            assembled_path,
            outcome.assembled_source.encode("utf-8"),
        )
    result = outcome.result.model_copy(
        update={
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
        }
    )
    metadata = {
        "schema_version": "1.0",
        "request_id": request_id,
        "candidate_sha256": _sha256_text(candidate),
        "assembled_source_path": str(assembled_path) if assembled_path is not None else None,
    }
    _write_verified_json(store, root / "check-input.json", metadata)
    _write_verified_json(store, root / "check.json", result.model_dump(mode="json"))


def load_check_result(store: RunArtifactStore, request_id: str) -> LeanCheckResult:
    """Load one verified request-bound checker result."""
    relative_path = Path("lean") / request_id / "check.json"
    if not store.verified(relative_path):
        raise LeanArtifactError(f"Checker result is unverified: {request_id}")
    try:
        result = LeanCheckResult.model_validate_json((store.path / relative_path).read_bytes())
    except (OSError, ValidationError) as error:
        raise LeanArtifactError(f"Checker result is invalid: {request_id}") from error
    if result.request_id != request_id:
        raise LeanArtifactError("Persisted checker result belongs to another request")
    return result


def load_check_outcome(
    *,
    store: RunArtifactStore,
    request_id: str,
    candidate: str,
) -> CheckOutcome | None:
    """Load verified evidence, returning ``None`` only when no check has completed."""
    root = Path("lean") / request_id
    check_path = root / "check.json"
    absolute_check_path = store.path / check_path
    if not absolute_check_path.exists():
        if absolute_check_path.with_name("check.json.sha256").exists():
            raise LeanArtifactError(f"Checker result is incomplete: {request_id}")
        return None
    result = load_check_result(store, request_id)
    input_path = root / "check-input.json"
    if not store.verified(input_path):
        raise LeanArtifactError(f"Checker input identity is unverified: {request_id}")
    try:
        metadata = json.loads((store.path / input_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise LeanArtifactError(f"Checker input identity is invalid: {request_id}") from error
    expected_metadata = {
        "schema_version": "1.0",
        "request_id": request_id,
        "candidate_sha256": _sha256_text(candidate),
    }
    if not isinstance(metadata, dict) or any(
        metadata.get(key) != value for key, value in expected_metadata.items()
    ):
        raise LeanArtifactError(f"Checker input identity changed: {request_id}")
    if set(metadata) != {*expected_metadata, "assembled_source_path"}:
        raise LeanArtifactError(f"Checker input identity has unexpected fields: {request_id}")
    stdout_path = root / "stdout.txt"
    stderr_path = root / "stderr.txt"
    if result.stdout_path != str(stdout_path) or result.stderr_path != str(stderr_path):
        raise LeanArtifactError(f"Checker diagnostic paths changed: {request_id}")
    stdout = _read_verified_text(store, stdout_path)
    stderr = _read_verified_text(store, stderr_path)
    assembled_source_path = metadata.get("assembled_source_path")
    if assembled_source_path is None:
        assembled_source = None
    elif assembled_source_path == str(root / "Candidate.lean"):
        assembled_source = _read_verified_text(store, Path(assembled_source_path))
    else:
        raise LeanArtifactError(f"Checker source path changed: {request_id}")
    return CheckOutcome(
        result=result,
        stdout=stdout,
        stderr=stderr,
        assembled_source=assembled_source,
    )


def _write_verified_bytes(store: RunArtifactStore, relative_path: Path, content: bytes) -> None:
    path = store.path / relative_path
    if path.exists():
        if not store.verified(relative_path) or path.read_bytes() != content:
            raise LeanArtifactError(f"Checker artifact changed: {relative_path}")
        return
    try:
        store.write_bytes(relative_path, content)
    except (ArtifactError, OSError) as error:
        raise LeanArtifactError(f"Unable to persist checker artifact: {relative_path}") from error


def _write_verified_json(
    store: RunArtifactStore,
    relative_path: Path,
    value: dict[str, object],
) -> None:
    path = store.path / relative_path
    if path.exists():
        if not store.verified(relative_path):
            raise LeanArtifactError(f"Checker artifact is unverified: {relative_path}")
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise LeanArtifactError(f"Checker artifact is unreadable: {relative_path}") from error
        if existing != value:
            raise LeanArtifactError(f"Checker artifact changed: {relative_path}")
        return
    try:
        store.write_json(relative_path, value)
    except (ArtifactError, OSError) as error:
        raise LeanArtifactError(f"Unable to persist checker artifact: {relative_path}") from error


def _read_verified_text(store: RunArtifactStore, relative_path: Path) -> str:
    if not store.verified(relative_path):
        raise LeanArtifactError(f"Checker artifact is unverified: {relative_path}")
    try:
        return (store.path / relative_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise LeanArtifactError(f"Checker artifact is unreadable: {relative_path}") from error


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
