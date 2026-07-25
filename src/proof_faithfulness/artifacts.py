"""Atomic, checksummed, immutable-on-freeze run artifact storage."""

from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import tempfile
import time
from pathlib import Path
from typing import Any


class ArtifactError(RuntimeError):
    """Base class for artifact-store failures."""


class FrozenRunError(ArtifactError):
    """Raised when code attempts to mutate a frozen run."""


class ArtifactChecksumError(ArtifactError):
    """Raised when bytes do not match their declared checksum."""


def sha256_bytes(content: bytes) -> str:
    """Returns the lowercase SHA-256 checksum of bytes."""
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    """Returns a streaming SHA-256 checksum for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_bytes(path: Path, content: bytes) -> None:
    """Atomically replaces a file using a temporary file on the same filesystem."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
            temporary_path = Path(f.name)
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


class RunArtifactStore:
    """Owns one content-addressed run directory under an outputs root."""

    _DIRECTORIES = (
        "responses",
        "lean",
        "evaluations",
        "derived",
        "reports",
    )
    _RESERVED_PATHS = frozenset(
        {".INITIALIZING", "FROZEN", "manifest.json", "manifest.json.sha256"}
    )
    _STALE_CLAIM_SECONDS = 3600

    def __init__(self, outputs_root: Path, run_id: str):
        self.outputs_root = outputs_root
        self.run_id = _validate_component(run_id, "run_id")
        self.path = outputs_root / "runs" / self.run_id

    @property
    def frozen(self) -> bool:
        """Whether this run has been permanently frozen."""
        return (self.path / "FROZEN").is_file()

    def initialize(self, *, parent_run_id: str | None = None, reason: str | None = None) -> None:
        """Creates the canonical run layout and an immutable identity manifest."""
        if parent_run_id is not None:
            _validate_component(parent_run_id, "parent_run_id")
            if not reason:
                raise ValueError("A child run requires a reason")
        if self.path.is_symlink():
            raise ArtifactError(f"Run directory must not be a symlink: {self.path}")
        manifest_path = self.path / "manifest.json"
        if manifest_path.is_symlink():
            raise ArtifactError(f"Run manifest must not be a symlink: {manifest_path}")
        if manifest_path.is_file():
            self._validate_existing_manifest(parent_run_id=parent_run_id, reason=reason)
            return
        self.path.mkdir(parents=True, exist_ok=True)
        initialization_claim = self.path / ".INITIALIZING"
        self._acquire_initialization_claim(initialization_claim)
        try:
            if manifest_path.is_file():
                self._validate_existing_manifest(parent_run_id=parent_run_id, reason=reason)
                return
            self._ensure_directories()
            manifest = {
                "schema_version": "1.0",
                "run_id": self.run_id,
                "parent_run_id": parent_run_id,
                "reason": reason,
            }
            content = _canonical_json_bytes(manifest)
            checksum = sha256_bytes(content)
            atomic_write_bytes(
                manifest_path.with_name("manifest.json.sha256"),
                f"{checksum}\n".encode("ascii"),
            )
            atomic_write_bytes(manifest_path, content)
        finally:
            initialization_claim.unlink(missing_ok=True)

    def write_bytes(
        self,
        relative_path: str | Path,
        content: bytes,
        *,
        expected_checksum: str | None = None,
    ) -> str:
        """Writes an artifact and checksum sidecar unless the run is frozen."""
        return self._write_bytes(
            relative_path,
            content,
            expected_checksum=expected_checksum,
            allow_reserved=False,
        )

    def _write_bytes(
        self,
        relative_path: str | Path,
        content: bytes,
        *,
        expected_checksum: str | None = None,
        allow_reserved: bool,
    ) -> str:
        self._ensure_mutable()
        target = self._resolve(relative_path)
        relative = target.relative_to(self.path)
        uses_checksum_namespace = any(part.endswith(".sha256") for part in relative.parts)
        if not allow_reserved and (
            str(relative) in self._RESERVED_PATHS or uses_checksum_namespace
        ):
            raise ArtifactError(f"Artifact path is reserved for store control data: {relative}")
        checksum = sha256_bytes(content)
        if expected_checksum is not None and checksum != expected_checksum:
            raise ArtifactChecksumError(
                f"Artifact content does not match expected checksum: {relative_path}"
            )
        atomic_write_bytes(target, content)
        atomic_write_bytes(target.with_name(f"{target.name}.sha256"), f"{checksum}\n".encode())
        return checksum

    def write_json(self, relative_path: str | Path, value: Any) -> str:
        """Writes canonical, newline-terminated JSON as a checksummed artifact."""
        return self._write_json(relative_path, value, allow_reserved=False)

    def _write_json(
        self,
        relative_path: str | Path,
        value: Any,
        *,
        allow_reserved: bool,
    ) -> str:
        content = _canonical_json_bytes(value)
        return self._write_bytes(relative_path, content, allow_reserved=allow_reserved)

    def verified(self, relative_path: str | Path, expected_checksum: str | None = None) -> bool:
        """Returns true only when an artifact exists and its checksum verifies."""
        target = self._resolve(relative_path)
        checksum_path = target.with_name(f"{target.name}.sha256")
        if target.is_symlink() or checksum_path.is_symlink():
            return False
        if not target.is_file() or not checksum_path.is_file():
            return False
        try:
            recorded_checksum = checksum_path.read_text(encoding="ascii").strip()
        except (OSError, UnicodeDecodeError):
            return False
        if re.fullmatch(r"[0-9a-f]{64}", recorded_checksum) is None:
            return False
        if expected_checksum is not None and recorded_checksum != expected_checksum:
            return False
        return sha256_file(target) == recorded_checksum

    def freeze(self) -> None:
        """Permanently prevents further writes to this run."""
        if self.frozen:
            return
        if not self.verified("manifest.json"):
            raise ArtifactError("Cannot freeze a run with an unverified manifest")
        atomic_write_bytes(self.path / "FROZEN", b"frozen\n")

    def create_child(self, run_id: str, *, reason: str) -> RunArtifactStore:
        """Creates a mutable child run instead of rewriting this run."""
        if not self.verified("manifest.json"):
            raise ArtifactError(f"Cannot create a child from an unverified parent: {self.run_id}")
        child = RunArtifactStore(self.outputs_root, run_id)
        child.initialize(parent_run_id=self.run_id, reason=reason)
        return child

    def _ensure_mutable(self) -> None:
        if self.frozen:
            raise FrozenRunError(f"Run is frozen and immutable: {self.run_id}")

    def _resolve(self, relative_path: str | Path) -> Path:
        path = Path(relative_path)
        if path.is_absolute() or not path.parts or ".." in path.parts:
            raise ValueError(f"Artifact path must stay within the run: {relative_path}")
        target = self.path / path
        if target == self.path:
            raise ValueError("Artifact path must name a file")
        resolved_run = self.path.resolve()
        resolved_parent = target.parent.resolve()
        if resolved_parent != resolved_run and resolved_run not in resolved_parent.parents:
            raise ValueError(f"Artifact path resolves outside the run: {relative_path}")
        return target

    def _ensure_directories(self) -> None:
        for directory in self._DIRECTORIES:
            path = self.path / directory
            if path.is_symlink() or (path.exists() and not path.is_dir()):
                raise ArtifactError(f"Canonical run path must be a directory: {path}")
            path.mkdir(parents=True, exist_ok=True)

    def _acquire_initialization_claim(self, claim: Path) -> None:
        claim_content = _canonical_json_bytes(
            {
                "hostname": socket.gethostname(),
                "pid": os.getpid(),
                "created_at_unix": time.time(),
            }
        )
        for _ in range(2):
            try:
                descriptor = os.open(claim, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError as error:
                if self._initialization_claim_is_active(claim):
                    raise ArtifactError(
                        f"Run initialization is already in progress: {self.path}"
                    ) from error
                if claim.is_dir():
                    claim.rmdir()
                else:
                    claim.unlink(missing_ok=True)
                continue
            try:
                os.write(descriptor, claim_content)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            return
        raise ArtifactError(f"Unable to acquire run initialization claim: {self.path}")

    def _initialization_claim_is_active(self, claim: Path) -> bool:
        if claim.is_dir():
            return False
        claim_age: float | None = None
        try:
            claim_age = time.time() - claim.stat().st_mtime
            owner = json.loads(claim.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return claim_age <= 60 if claim_age is not None else True
        if owner.get("hostname") != socket.gethostname():
            return claim_age <= self._STALE_CLAIM_SECONDS
        pid = owner.get("pid")
        if not isinstance(pid, int) or pid <= 0:
            return claim_age <= 60
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def _validate_existing_manifest(
        self,
        *,
        parent_run_id: str | None,
        reason: str | None,
    ) -> None:
        if not self.verified("manifest.json"):
            raise ArtifactChecksumError(f"Run manifest is unverified: {self.path}")
        manifest_path = self.path / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected_manifest = {
            "schema_version": "1.0",
            "run_id": self.run_id,
            "parent_run_id": parent_run_id,
            "reason": reason,
        }
        if manifest != expected_manifest:
            raise ArtifactError(f"Run manifest identity or lineage mismatch: {self.path}")
        self._ensure_directories()


def _validate_component(value: str, description: str) -> str:
    if not value or value in {".", ".."} or "/" in value or "\\" in value:
        raise ValueError(f"Invalid {description}: {value!r}")
    return value


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )
