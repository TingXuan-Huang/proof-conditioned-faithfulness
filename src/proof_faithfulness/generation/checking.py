"""Trusted checking of verified generation responses."""

from __future__ import annotations

import hashlib
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from proof_faithfulness.artifacts import RunArtifactStore
from proof_faithfulness.generation.artifacts import load_verified_response
from proof_faithfulness.lean.artifacts import LeanArtifactError, check_and_persist_candidate
from proof_faithfulness.lean.checker import (
    DEFAULT_MAX_HEARTBEATS,
    DEFAULT_MEMORY_LIMIT_MB,
    DEFAULT_TIMEOUT_SECONDS,
    CheckOutcome,
    LeanCandidateSpec,
    check_candidate,
)
from proof_faithfulness.models import ModelInput
from proof_faithfulness.schema import Hash, NonEmptyString


class GenerationCheckModel(BaseModel):
    """Immutable base for generation-checking inputs."""

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", frozen=True)


class GenerationCheckSpec(GenerationCheckModel):
    """Canonical Lean declaration bound to one generated request."""

    request_id: Hash
    imports: tuple[NonEmptyString, ...]
    declaration_name: NonEmptyString
    declaration: NonEmptyString

    def lean_candidate_spec(self) -> LeanCandidateSpec:
        """Build and validate the trusted S2 candidate specification."""
        return LeanCandidateSpec.from_declaration(
            imports=self.imports,
            declaration_name=self.declaration_name,
            declaration=self.declaration,
        )


def check_generation_response(
    *,
    store: RunArtifactStore,
    model_input: ModelInput,
    spec: LeanCandidateSpec,
    project_root: Path | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB,
    max_heartbeats: int = DEFAULT_MAX_HEARTBEATS,
) -> CheckOutcome:
    """Trusted-check a verified response and persist request-bound evidence."""
    _validate_spec_identity(model_input=model_input, spec=spec)
    response = load_verified_response(store=store, model_input=model_input)
    if response is None:
        raise LeanArtifactError("Generation response is missing, corrupt, or non-terminal")
    request_id = model_input.request.request_id

    def checker(candidate: str) -> CheckOutcome:
        return check_candidate(
            spec,
            candidate,
            request_id=request_id,
            project_root=project_root,
            timeout_seconds=timeout_seconds,
            memory_limit_mb=memory_limit_mb,
            max_heartbeats=max_heartbeats,
        )

    return check_and_persist_candidate(
        store=store,
        request_id=request_id,
        candidate=response.text,
        checker=checker,
    )


def _validate_spec_identity(*, model_input: ModelInput, spec: LeanCandidateSpec) -> None:
    request = model_input.request
    if spec.statement_hash != request.statement_hash:
        raise LeanArtifactError("Lean statement does not match the generation request")
    import_bytes = "".join(f"import {name}\n" for name in spec.imports).encode("utf-8")
    if hashlib.sha256(import_bytes).hexdigest() != request.import_hash:
        raise LeanArtifactError("Lean imports do not match the generation request")
