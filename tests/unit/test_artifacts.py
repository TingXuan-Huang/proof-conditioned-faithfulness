"""Tests for atomic, checksummed run artifacts and freeze behavior."""

import json
import os
import socket
from pathlib import Path

import pytest

from proof_faithfulness.artifacts import (
    ArtifactChecksumError,
    ArtifactError,
    FrozenRunError,
    RunArtifactStore,
    atomic_write_bytes,
    sha256_bytes,
)


def test_run_store_initializes_canonical_layout(tmp_path: Path) -> None:
    store = RunArtifactStore(tmp_path, "run-001")
    store.initialize()
    for directory in ("responses", "lean", "evaluations", "derived", "reports"):
        assert (store.path / directory).is_dir()
    assert store.verified("manifest.json")


def test_run_store_recovers_from_interrupted_initialization(tmp_path: Path) -> None:
    store = RunArtifactStore(tmp_path, "run-001")
    (store.path / "responses").mkdir(parents=True)
    (store.path / ".INITIALIZING").write_text(
        json.dumps({"hostname": socket.gethostname(), "pid": 999_999_999}),
        encoding="utf-8",
    )
    store.initialize()
    assert store.verified("manifest.json")
    assert (store.path / "reports").is_dir()


def test_run_store_restores_missing_directory_on_idempotent_initialize(tmp_path: Path) -> None:
    store = RunArtifactStore(tmp_path, "run-001")
    store.initialize()
    (store.path / "reports").rmdir()
    store.initialize()
    assert (store.path / "reports").is_dir()


def test_run_store_rejects_existing_lineage_mismatch(tmp_path: Path) -> None:
    store = RunArtifactStore(tmp_path, "run-001")
    store.initialize()
    with pytest.raises(ArtifactError, match="lineage mismatch"):
        store.initialize(parent_run_id="different-parent", reason="Different lineage")


def test_run_store_rejects_existing_unverified_manifest(tmp_path: Path) -> None:
    store = RunArtifactStore(tmp_path, "run-001")
    store.initialize()
    manifest_path = store.path / "manifest.json"
    manifest_path.write_text(
        '{"parent_run_id":null,"reason":null,"run_id":"run-001","schema_version":"999.0"}\n',
        encoding="utf-8",
    )
    (store.path / "manifest.json.sha256").unlink()
    with pytest.raises(ArtifactChecksumError, match="unverified"):
        store.initialize()


def test_run_store_rejects_concurrent_initialization_claim(tmp_path: Path) -> None:
    store = RunArtifactStore(tmp_path, "run-001")
    store.path.mkdir(parents=True)
    (store.path / ".INITIALIZING").write_text(
        json.dumps({"hostname": socket.gethostname(), "pid": os.getpid()}),
        encoding="utf-8",
    )
    with pytest.raises(ArtifactError, match="already in progress"):
        store.initialize()


def test_run_store_writes_and_verifies_checksum(tmp_path: Path) -> None:
    store = RunArtifactStore(tmp_path, "run-001")
    store.initialize()
    checksum = store.write_bytes("responses/request-001/raw.txt", b"response")
    assert checksum == sha256_bytes(b"response")
    assert store.verified("responses/request-001/raw.txt", checksum)
    (store.path / "responses/request-001/raw.txt").write_bytes(b"tampered")
    assert not store.verified("responses/request-001/raw.txt", checksum)


def test_run_store_rejects_wrong_expected_checksum(tmp_path: Path) -> None:
    store = RunArtifactStore(tmp_path, "run-001")
    store.initialize()
    with pytest.raises(ArtifactChecksumError):
        store.write_bytes("responses/raw.txt", b"response", expected_checksum="0" * 64)
    assert not (store.path / "responses/raw.txt").exists()


@pytest.mark.parametrize(
    "relative_path",
    ["responses/raw.json.sha256", "responses/nested.sha256/value.json"],
)
def test_run_store_reserves_checksum_namespace(
    tmp_path: Path,
    relative_path: str,
) -> None:
    store = RunArtifactStore(tmp_path, "run-001")
    store.initialize()
    with pytest.raises(ArtifactError, match="reserved"):
        store.write_bytes(relative_path, b"forged")


def test_run_store_fails_closed_on_malformed_checksum(tmp_path: Path) -> None:
    store = RunArtifactStore(tmp_path, "run-001")
    store.initialize()
    store.write_bytes("responses/raw.json", b"{}")
    checksum_path = store.path / "responses/raw.json.sha256"
    checksum_path.write_bytes(b"\xff\xfe")
    assert not store.verified("responses/raw.json")


def test_frozen_run_is_immutable_and_child_is_writable(tmp_path: Path) -> None:
    store = RunArtifactStore(tmp_path, "run-001")
    store.initialize()
    store.freeze()
    with pytest.raises(FrozenRunError):
        store.write_bytes("responses/raw.txt", b"response")
    child = store.create_child("run-002", reason="Correct a checker defect")
    child.write_bytes("responses/raw.txt", b"response")
    assert child.verified("responses/raw.txt")


def test_run_store_rejects_child_from_unverified_parent(tmp_path: Path) -> None:
    store = RunArtifactStore(tmp_path, "run-001")
    with pytest.raises(ArtifactError, match="unverified parent"):
        store.create_child("run-002", reason="Parent does not exist")


def test_run_store_rejects_path_traversal(tmp_path: Path) -> None:
    store = RunArtifactStore(tmp_path, "run-001")
    store.initialize()
    with pytest.raises(ValueError, match="stay within"):
        store.write_bytes("../outside.txt", b"response")


def test_run_store_rejects_symlink_escape(tmp_path: Path) -> None:
    store = RunArtifactStore(tmp_path, "run-001")
    store.initialize()
    outside = tmp_path / "outside"
    outside.mkdir()
    (store.path / "escape").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="outside the run"):
        store.write_bytes("escape/artifact.txt", b"response")
    assert not (outside / "artifact.txt").exists()


@pytest.mark.parametrize("relative_path", ["manifest.json", "manifest.json.sha256", "FROZEN"])
def test_run_store_rejects_public_control_file_write(
    tmp_path: Path,
    relative_path: str,
) -> None:
    store = RunArtifactStore(tmp_path, "run-001")
    store.initialize()
    with pytest.raises(ArtifactError, match="reserved"):
        store.write_bytes(relative_path, b"forged")


def test_run_store_rejects_non_finite_json(tmp_path: Path) -> None:
    store = RunArtifactStore(tmp_path, "run-001")
    store.initialize()
    with pytest.raises(ValueError, match="JSON compliant"):
        store.write_json("derived/metric.json", {"value": float("nan")})


def test_atomic_write_preserves_old_target_when_replace_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "artifact.txt"
    target.write_bytes(b"old")

    def fail_replace(source: Path, destination: Path) -> None:
        del source, destination
        raise OSError("simulated replace failure")

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated"):
        atomic_write_bytes(target, b"new")
    assert target.read_bytes() == b"old"
    assert sorted(tmp_path.iterdir()) == [target]
