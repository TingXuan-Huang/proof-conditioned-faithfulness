"""Fail-closed export of opaque, independently judged annotation bundles."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import shutil
import tempfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from proof_faithfulness.artifacts import atomic_write_bytes
from proof_faithfulness.evaluation.models import (
    BlindedAnnotationItem,
    BlindingMap,
    BlindMapEntry,
    InternalAnnotationItem,
    PacketManifest,
    PacketManifestEntry,
    SensitiveMetadata,
)

_FORBIDDEN_FIELD_NAMES = (
    "condition_key",
    "model_name",
    "prompt_text",
    "request_id",
    "sample_index",
    "theorem_id",
)
_SAMPLE_SCAN_EXEMPT_FIELDS = frozenset(
    {
        "blind_id",
        "extractor_version",
        "extractor_versions",
        "file",
        "packet_checksum",
        "private_map_commitment",
        "rubric_version",
        "rubric_versions",
        "schema_version",
        "sha256",
    }
)
_MAX_CONTROL_FILE_BYTES = 64 * 1024 * 1024


class BlindingError(RuntimeError):
    """The annotation packet could reveal experimental identity or treatment."""


def export_blinded_bundle(
    items: Iterable[InternalAnnotationItem],
    output_dir: Path,
    mapping_path: Path,
    blinding_key: bytes,
) -> tuple[BlindedAnnotationItem, ...]:
    """Publishes or recovers a blinded packet and separate private identity map.

    Existing verified halves are reused after an interrupted publication. Any existing
    content that differs from the deterministic expected bytes fails closed. The HMAC
    key is caller-owned and is never serialized.
    """
    item_list = tuple(items)
    if not item_list:
        raise ValueError("A blinded bundle requires at least one item")
    if len(blinding_key) < 16:
        raise ValueError("The blinding key must contain at least 16 bytes")
    request_ids = tuple(item.request_id for item in item_list)
    if len(set(request_ids)) != len(request_ids):
        raise ValueError("Annotation request IDs must be unique")
    _require_separate_mapping(output_dir, mapping_path)

    blinded_items: list[BlindedAnnotationItem] = []
    map_entries: list[BlindMapEntry] = []
    sensitive_by_id: dict[str, SensitiveMetadata] = {}
    for item in sorted(item_list, key=lambda value: value.request_id):
        blind_id = _blind_id(item.request_id, blinding_key)
        blinded_items.append(
            BlindedAnnotationItem(
                blind_id=blind_id,
                theorem_statement=item.theorem_statement,
                supplied_informal_proof=item.supplied_informal_proof,
                generated_lean_proof=item.generated_lean_proof,
                rubric_text=item.rubric_text,
                rubric_version=item.rubric_version,
                extractor_version=item.extractor_version,
                signature_evidence=item.signature_evidence,
            )
        )
        map_entries.append(
            BlindMapEntry(
                blind_id=blind_id,
                request_id=item.request_id,
                theorem_id=item.theorem_id,
                rubric_version=item.rubric_version,
                extractor_version=item.extractor_version,
            )
        )
        sensitive_by_id[blind_id] = item.sensitive
    blind_ids = tuple(item.blind_id for item in blinded_items)
    if len(set(blind_ids)) != len(blind_ids):
        raise BlindingError("Opaque annotation IDs collided")

    item_tuple = tuple(blinded_items)
    map_entry_tuple = tuple(map_entries)
    files, manifest = _bundle_files(item_tuple, map_entry_tuple)
    verify_blinded_content(files, sensitive_by_id.values())
    mapping = BlindingMap(
        packet_checksum=manifest.packet_checksum,
        rubric_versions=manifest.rubric_versions,
        extractor_versions=manifest.extractor_versions,
        entries=map_entry_tuple,
    )
    map_content = _canonical_json_bytes(mapping.model_dump(mode="json"))
    _publish_or_recover(
        files,
        manifest,
        mapping,
        map_content,
        output_dir,
        mapping_path,
        tuple(sensitive_by_id.values()),
    )
    return item_tuple


def verify_blinded_bundle(
    bundle_dir: Path,
    sensitive_metadata: Iterable[SensitiveMetadata] = (),
) -> PacketManifest:
    """Verifies exact packet membership, checksums, versions, and blinding."""
    files = _read_bundle_files(bundle_dir)
    verify_blinded_content(files, sensitive_metadata)
    manifest_content = files.get("manifest.json")
    if manifest_content is None:
        raise BlindingError("Blinded bundle has no manifest.json")
    try:
        manifest = PacketManifest.model_validate_json(manifest_content)
    except ValidationError as error:
        raise BlindingError("Blinded bundle manifest is invalid") from error
    expected_paths = {"manifest.json", *(entry.file for entry in manifest.items)}
    if set(files) != expected_paths:
        raise BlindingError("Blinded bundle membership does not match its manifest")
    for entry in manifest.items:
        content = files[entry.file]
        if hashlib.sha256(content).hexdigest() != entry.sha256:
            raise BlindingError(f"Blinded item checksum mismatch: {entry.file}")
        try:
            item = BlindedAnnotationItem.model_validate_json(content)
        except ValidationError as error:
            raise BlindingError(f"Blinded item is invalid: {entry.file}") from error
        if (
            item.blind_id != entry.blind_id
            or item.rubric_version != entry.rubric_version
            or item.extractor_version != entry.extractor_version
        ):
            raise BlindingError(f"Blinded item identity mismatch: {entry.file}")
    if (
        _packet_checksum(
            manifest.items,
            manifest.rubric_versions,
            manifest.extractor_versions,
            manifest.private_map_commitment,
        )
        != manifest.packet_checksum
    ):
        raise BlindingError("Blinded packet checksum mismatch")
    if tuple(sorted({entry.rubric_version for entry in manifest.items})) != (
        manifest.rubric_versions
    ):
        raise BlindingError("Blinded packet rubric versions mismatch its items")
    if tuple(sorted({entry.extractor_version for entry in manifest.items})) != (
        manifest.extractor_versions
    ):
        raise BlindingError("Blinded packet extractor versions mismatch its items")
    return manifest


def verify_blinded_content(
    files: Mapping[str, bytes],
    sensitive_metadata: Iterable[SensitiveMetadata],
) -> None:
    """Rejects forbidden fields and supplied identity canaries in names or payloads."""
    metadata = tuple(sensitive_metadata)
    searchable_parts: list[str] = []
    decoded_leaf_strings: list[str] = []
    sample_visible_values: list[str] = []
    relative_paths: list[str] = []
    for relative_path, content in files.items():
        try:
            decoded = content.decode("utf-8")
            value: Any = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise BlindingError(f"Blinded payload is not UTF-8 JSON: {relative_path}") from error
        searchable_parts.extend((relative_path, decoded))
        relative_paths.append(relative_path)
        decoded_leaf_strings.extend(_decoded_leaf_strings(value))
        sample_visible_values.extend(_sample_visible_values(value))
    searchable = "\n".join(searchable_parts).casefold()
    for field_name in _FORBIDDEN_FIELD_NAMES:
        if re.search(rf"(?<![a-z0-9_]){re.escape(field_name)}(?![a-z0-9_])", searchable):
            raise BlindingError(f"Blinded bundle contains forbidden field: {field_name}")
    for item in metadata:
        for description, value in (
            ("model name", item.model_name),
            ("condition key", item.condition_key),
            ("prompt text", item.prompt_text),
        ):
            value_folded = value.casefold()
            if any(value_folded in leaf.casefold() for leaf in decoded_leaf_strings) or any(
                value_folded in path.casefold() for path in relative_paths
            ):
                raise BlindingError(f"Blinded bundle contains {description}")
        sample_index = str(item.sample_index)
        sample_token = re.compile(rf"(?<![0-9]){re.escape(sample_index)}(?![0-9])")
        payload_sample = any(sample_token.search(value) for value in sample_visible_values)
        filename_sample = any(sample_token.search(path) for path in relative_paths)
        if payload_sample or filename_sample:
            raise BlindingError("Blinded bundle contains sample index metadata")


def load_blinding_map(path: Path) -> BlindingMap:
    """Loads and strictly validates a regular private annotation identity map."""
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"Blinding map must be a regular non-symlink file: {path}")
    if path.stat().st_size > _MAX_CONTROL_FILE_BYTES:
        raise ValueError(f"Blinding map exceeds {_MAX_CONTROL_FILE_BYTES} bytes: {path}")
    try:
        mapping = BlindingMap.model_validate_json(path.read_bytes())
    except (OSError, ValidationError) as error:
        raise ValueError(f"Unable to load blinding map: {path}") from error
    blind_ids = tuple(entry.blind_id for entry in mapping.entries)
    request_ids = tuple(entry.request_id for entry in mapping.entries)
    if len(set(blind_ids)) != len(blind_ids) or len(set(request_ids)) != len(request_ids):
        raise ValueError("Blinding map identities must be unique")
    return mapping


def compute_map_commitment(entries: tuple[BlindMapEntry, ...]) -> str:
    """Commits to private map entries without publishing their contents."""
    return hashlib.sha256(
        _canonical_json_bytes([entry.model_dump(mode="json") for entry in entries])
    ).hexdigest()


def publish_bytes_exclusive(path: Path, content: bytes) -> None:
    """Atomically publishes bytes without replacing an existing path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
            temporary_path = Path(f.name)
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.link(temporary_path, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _blind_id(request_id: str, blinding_key: bytes) -> str:
    digest = hmac.new(
        blinding_key,
        b"proof-faithfulness-annotation-v2\0" + request_id.encode("ascii"),
        hashlib.sha256,
    ).digest()
    value = int.from_bytes(digest, "big")
    characters: list[str] = []
    for _ in range(24):
        value, remainder = divmod(value, 26)
        characters.append(chr(ord("a") + remainder))
    return "".join(characters)


def _bundle_files(
    items: tuple[BlindedAnnotationItem, ...],
    map_entries: tuple[BlindMapEntry, ...],
) -> tuple[dict[str, bytes], PacketManifest]:
    files: dict[str, bytes] = {}
    entries: list[PacketManifestEntry] = []
    for item in items:
        path = f"items/item-{item.blind_id}.json"
        content = _canonical_json_bytes(item.model_dump(mode="json"))
        files[path] = content
        entries.append(
            PacketManifestEntry(
                blind_id=item.blind_id,
                file=path,
                sha256=hashlib.sha256(content).hexdigest(),
                rubric_version=item.rubric_version,
                extractor_version=item.extractor_version,
            )
        )
    entry_tuple = tuple(entries)
    rubric_versions = tuple(sorted({item.rubric_version for item in items}))
    extractor_versions = tuple(sorted({item.extractor_version for item in items}))
    private_map_commitment = compute_map_commitment(map_entries)
    manifest = PacketManifest(
        packet_checksum=_packet_checksum(
            entry_tuple,
            rubric_versions,
            extractor_versions,
            private_map_commitment,
        ),
        private_map_commitment=private_map_commitment,
        items=entry_tuple,
        rubric_versions=rubric_versions,
        extractor_versions=extractor_versions,
    )
    files["manifest.json"] = _canonical_json_bytes(manifest.model_dump(mode="json"))
    return files, manifest


def _packet_checksum(
    entries: tuple[PacketManifestEntry, ...],
    rubric_versions: tuple[str, ...],
    extractor_versions: tuple[str, ...],
    private_map_commitment: str,
) -> str:
    identity = {
        "schema_version": "1.0",
        "items": [entry.model_dump(mode="json") for entry in entries],
        "rubric_versions": list(rubric_versions),
        "extractor_versions": list(extractor_versions),
        "private_map_commitment": private_map_commitment,
    }
    return hashlib.sha256(_canonical_json_bytes(identity)).hexdigest()


def _publish_or_recover(
    files: Mapping[str, bytes],
    manifest: PacketManifest,
    mapping: BlindingMap,
    map_content: bytes,
    output_dir: Path,
    mapping_path: Path,
    sensitive_metadata: tuple[SensitiveMetadata, ...],
) -> None:
    if output_dir.exists() or output_dir.is_symlink():
        observed_files = _read_bundle_files(output_dir)
        if dict(files) != observed_files:
            raise BlindingError("Existing blinded bundle differs from expected packet")
        observed_manifest = verify_blinded_bundle(output_dir, sensitive_metadata)
        if observed_manifest != manifest:
            raise BlindingError("Existing blinded bundle has a different identity")
    else:
        _publish_bundle_directory(files, output_dir)
    if mapping_path.exists() or mapping_path.is_symlink():
        if load_blinding_map(mapping_path) != mapping:
            raise BlindingError("Existing blinding map differs from expected packet")
    else:
        publish_bytes_exclusive(mapping_path, map_content)
    observed_manifest = verify_blinded_bundle(output_dir, sensitive_metadata)
    observed_mapping = load_blinding_map(mapping_path)
    if observed_manifest.packet_checksum != observed_mapping.packet_checksum:
        raise BlindingError("Public packet and private map checksums do not match")


def _publish_bundle_directory(files: Mapping[str, bytes], output_dir: Path) -> None:
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}-", dir=output_dir.parent))
    try:
        for relative_path, content in files.items():
            atomic_write_bytes(staging_dir / relative_path, content)
        os.rename(staging_dir, output_dir)
    except BaseException:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise


def _read_bundle_files(bundle_dir: Path) -> dict[str, bytes]:
    if not bundle_dir.is_dir() or bundle_dir.is_symlink():
        raise BlindingError(f"Blinded bundle is not a regular directory: {bundle_dir}")
    files: dict[str, bytes] = {}
    for path in sorted(bundle_dir.rglob("*")):
        if path.is_symlink():
            raise BlindingError(f"Blinded bundle contains a symlink: {path}")
        if path.is_file():
            files[path.relative_to(bundle_dir).as_posix()] = path.read_bytes()
    if not files:
        raise BlindingError("Blinded bundle contains no files")
    return files


def _sample_visible_values(value: Any, field_name: str | None = None) -> list[str]:
    if field_name in _SAMPLE_SCAN_EXEMPT_FIELDS:
        return []
    if isinstance(value, dict):
        return [
            visible
            for key, nested in value.items()
            for visible in _sample_visible_values(nested, str(key))
        ]
    if isinstance(value, list):
        return [visible for nested in value for visible in _sample_visible_values(nested)]
    if isinstance(value, (str, int)) and not isinstance(value, bool):
        return [str(value)]
    return []


def _decoded_leaf_strings(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [leaf for nested in value.values() for leaf in _decoded_leaf_strings(nested)]
    if isinstance(value, list):
        return [leaf for nested in value for leaf in _decoded_leaf_strings(nested)]
    if isinstance(value, str):
        return [value]
    return []


def _require_separate_mapping(output_dir: Path, mapping_path: Path) -> None:
    output = output_dir.resolve()
    mapping = mapping_path.resolve()
    if mapping == output or output in mapping.parents:
        raise ValueError("The private blinding map must be outside the exported bundle")


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value, allow_nan=False, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        + "\n"
    ).encode("utf-8")
