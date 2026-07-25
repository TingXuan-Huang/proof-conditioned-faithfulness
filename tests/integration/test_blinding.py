import hashlib
import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

import proof_faithfulness.evaluation.blinding as blinding_module
from proof_faithfulness.evaluation.annotations import import_human_labels
from proof_faithfulness.evaluation.blinding import (
    BlindingError,
    export_blinded_bundle,
    load_blinding_map,
    verify_blinded_bundle,
)
from proof_faithfulness.evaluation.cli import app
from proof_faithfulness.evaluation.models import InternalAnnotationItem, SensitiveMetadata

MODEL_CANARY = "Frontier-Model-Canary-X9"
CONDITION_CANARY = "proof_a_validity_canary_x9"
PROMPT_CANARY = "PROMPT-CANARY-X9-DO-NOT-EXPORT"
SAMPLE_INDEX = 7391
BLINDING_KEY = b"fixture-only-blinding-key-32-bytes"
RUBRIC_VERSION = "rubric-fixture-v1"
EXTRACTOR_VERSION = "extractor-fixture-v1"


def test_exported_bundle_has_no_treatment_leakage_but_keeps_semantic_routes(
    tmp_path: Path,
) -> None:
    bundle_dir = tmp_path / "public" / "packet"
    mapping_path = tmp_path / "private" / "identity-map.json"
    items = (_internal_item(), _internal_item(request_character="b", theorem="other theorem"))

    blinded_items = export_blinded_bundle(items, bundle_dir, mapping_path, BLINDING_KEY)

    corpus = _bundle_corpus(bundle_dir)
    forbidden = (
        MODEL_CANARY,
        CONDITION_CANARY,
        PROMPT_CANARY,
        str(SAMPLE_INDEX),
        "model_name",
        "condition_key",
        "prompt_text",
        "sample_index",
        "request_id",
        "theorem_id",
    )
    for value in forbidden:
        assert value.casefold() not in corpus.casefold()
    assert "Route A" in corpus
    assert "Route B" in corpus
    assert mapping_path.is_file()
    assert not mapping_path.is_relative_to(bundle_dir)
    assert len(blinded_items) == 2
    manifest = verify_blinded_bundle(bundle_dir, (item.sensitive for item in items))

    mapping = load_blinding_map(mapping_path)
    assert mapping.packet_checksum == manifest.packet_checksum
    assert {entry.request_id for entry in mapping.entries} == {"a" * 64, "b" * 64}


@pytest.mark.parametrize(
    "leaked_text",
    [MODEL_CANARY, CONDITION_CANARY, PROMPT_CANARY, f"sample-{SAMPLE_INDEX}"],
)
def test_export_fails_closed_when_payload_contains_sensitive_canary(
    tmp_path: Path,
    leaked_text: str,
) -> None:
    item = _internal_item(generated_proof=f"by\n  -- {leaked_text}\n  trivial")
    bundle_dir = tmp_path / "packet"
    mapping_path = tmp_path / "private-map.json"

    with pytest.raises(BlindingError):
        export_blinded_bundle((item,), bundle_dir, mapping_path, BLINDING_KEY)

    assert not bundle_dir.exists()
    assert not mapping_path.exists()


def test_export_rejects_bare_sample_index_value(tmp_path: Path) -> None:
    item = _internal_item(generated_proof=str(SAMPLE_INDEX))
    with pytest.raises(BlindingError, match="sample index"):
        export_blinded_bundle(
            (item,),
            tmp_path / "packet",
            tmp_path / "private-map.json",
            BLINDING_KEY,
        )


def test_export_rejects_sample_index_token_embedded_in_source_comment(tmp_path: Path) -> None:
    item = _internal_item(
        generated_proof=f"by\n  -- retained index {SAMPLE_INDEX} for diagnostics\n  trivial"
    )
    with pytest.raises(BlindingError, match="sample index"):
        export_blinded_bundle(
            (item,),
            tmp_path / "packet",
            tmp_path / "private-map.json",
            BLINDING_KEY,
        )


def test_export_detects_decoded_multiline_prompt_text(tmp_path: Path) -> None:
    multiline_prompt = "PROMPT-FIRST-LINE\nPROMPT-SECOND-LINE"
    item = _internal_item(
        generated_proof=f"by\n{multiline_prompt}\ntrivial",
        prompt_text=multiline_prompt,
    )
    with pytest.raises(BlindingError, match="prompt text"):
        export_blinded_bundle(
            (item,),
            tmp_path / "packet",
            tmp_path / "private-map.json",
            BLINDING_KEY,
        )


def test_blinding_map_cannot_be_written_inside_public_bundle(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "packet"
    with pytest.raises(ValueError, match="outside"):
        export_blinded_bundle(
            (_internal_item(),),
            bundle_dir,
            bundle_dir / "identity-map.json",
            BLINDING_KEY,
        )


def test_verifier_checks_filenames_as_well_as_payloads(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "packet"
    mapping_path = tmp_path / "private-map.json"
    item = _internal_item()
    export_blinded_bundle((item,), bundle_dir, mapping_path, BLINDING_KEY)
    source = next((bundle_dir / "items").iterdir())
    source.rename(source.with_name(f"{MODEL_CANARY}.json"))

    with pytest.raises(BlindingError, match="model name"):
        verify_blinded_bundle(bundle_dir, (item.sensitive,))


def test_export_recovers_public_only_kill_point(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle_dir = tmp_path / "packet"
    mapping_path = tmp_path / "private-map.json"
    original_publish = blinding_module.publish_bytes_exclusive

    def interrupt_map_publication(path: Path, content: bytes) -> None:
        del path, content
        raise KeyboardInterrupt("simulated kill after public packet publication")

    monkeypatch.setattr(blinding_module, "publish_bytes_exclusive", interrupt_map_publication)
    with pytest.raises(KeyboardInterrupt, match="simulated kill"):
        export_blinded_bundle(
            (_internal_item(),),
            bundle_dir,
            mapping_path,
            BLINDING_KEY,
        )
    assert bundle_dir.is_dir()
    assert not mapping_path.exists()

    monkeypatch.setattr(blinding_module, "publish_bytes_exclusive", original_publish)
    export_blinded_bundle((_internal_item(),), bundle_dir, mapping_path, BLINDING_KEY)
    assert verify_blinded_bundle(bundle_dir).packet_checksum == (
        load_blinding_map(mapping_path).packet_checksum
    )


def test_export_recovers_map_only_state(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "packet"
    mapping_path = tmp_path / "private-map.json"
    item = _internal_item()
    export_blinded_bundle((item,), bundle_dir, mapping_path, BLINDING_KEY)
    expected_map = mapping_path.read_bytes()
    shutil.rmtree(bundle_dir)

    export_blinded_bundle((item,), bundle_dir, mapping_path, BLINDING_KEY)

    assert mapping_path.read_bytes() == expected_map
    assert verify_blinded_bundle(bundle_dir).packet_checksum == (
        load_blinding_map(mapping_path).packet_checksum
    )


def test_packet_checksum_detects_tampered_item(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "packet"
    mapping_path = tmp_path / "private-map.json"
    export_blinded_bundle((_internal_item(),), bundle_dir, mapping_path, BLINDING_KEY)
    item_path = next((bundle_dir / "items").iterdir())
    item_path.write_text("{}\n", encoding="utf-8")

    with pytest.raises(BlindingError, match="checksum mismatch"):
        verify_blinded_bundle(bundle_dir)


def test_human_labels_import_only_with_exact_packet_and_tool_versions(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "packet"
    mapping_path = tmp_path / "private-map.json"
    (blinded,) = export_blinded_bundle(
        (_internal_item(),),
        bundle_dir,
        mapping_path,
        BLINDING_KEY,
    )
    manifest = verify_blinded_bundle(bundle_dir)
    label_path = tmp_path / "annotator-1.jsonl"
    label = _label_payload(blinded.blind_id, manifest.packet_checksum)
    label_path.write_text(json.dumps(label) + "\n", encoding="utf-8")

    (imported,) = import_human_labels((label_path,), mapping_path, bundle_dir)

    assert imported.request_id == "a" * 64
    assert imported.packet_checksum == manifest.packet_checksum
    assert imported.original.model_dump(mode="json") == label

    label["rubric_version"] = "wrong-rubric"
    label_path.write_text(json.dumps(label) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="versions mismatch"):
        import_human_labels((label_path,), mapping_path, bundle_dir)


def test_human_label_import_rejects_map_from_other_packet(tmp_path: Path) -> None:
    first_bundle = tmp_path / "first-packet"
    first_map = tmp_path / "first-map.json"
    (blinded,) = export_blinded_bundle(
        (_internal_item(),),
        first_bundle,
        first_map,
        BLINDING_KEY,
    )
    second_bundle = tmp_path / "second-packet"
    second_map = tmp_path / "second-map.json"
    export_blinded_bundle(
        (_internal_item(request_character="b"),),
        second_bundle,
        second_map,
        BLINDING_KEY,
    )
    first_manifest = verify_blinded_bundle(first_bundle)
    label_path = tmp_path / "label.jsonl"
    label_path.write_text(
        json.dumps(_label_payload(blinded.blind_id, first_manifest.packet_checksum)) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="does not belong"):
        import_human_labels((label_path,), second_map, first_bundle)


def test_human_label_import_rejects_private_map_entry_swap(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "packet"
    mapping_path = tmp_path / "map.json"
    (blinded,) = export_blinded_bundle(
        (_internal_item(),),
        bundle_dir,
        mapping_path,
        BLINDING_KEY,
    )
    manifest = verify_blinded_bundle(bundle_dir)
    label_path = tmp_path / "label.jsonl"
    label_path.write_text(
        json.dumps(_label_payload(blinded.blind_id, manifest.packet_checksum)) + "\n",
        encoding="utf-8",
    )
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    mapping["entries"][0]["request_id"] = "c" * 64
    mapping_path.write_text(json.dumps(mapping), encoding="utf-8")

    with pytest.raises(ValueError, match="does not belong"):
        import_human_labels((label_path,), mapping_path, bundle_dir)


def test_resolved_label_cli_publication_is_exclusive(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "packet"
    mapping_path = tmp_path / "map.json"
    (blinded,) = export_blinded_bundle(
        (_internal_item(),),
        bundle_dir,
        mapping_path,
        BLINDING_KEY,
    )
    manifest = verify_blinded_bundle(bundle_dir)
    label_path = tmp_path / "label.jsonl"
    label_path.write_text(
        json.dumps(_label_payload(blinded.blind_id, manifest.packet_checksum)) + "\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "resolved.jsonl"
    arguments = [
        "import-labels",
        "--input",
        str(label_path),
        "--mapping",
        str(mapping_path),
        "--bundle",
        str(bundle_dir),
        "--output",
        str(output_path),
    ]
    runner = CliRunner()
    first = runner.invoke(app, arguments)
    original_checksum = hashlib.sha256(output_path.read_bytes()).hexdigest()
    second = runner.invoke(app, arguments)

    assert first.exit_code == 0, first.output
    assert second.exit_code != 0
    assert "already exists" in second.output
    assert hashlib.sha256(output_path.read_bytes()).hexdigest() == original_checksum


def _internal_item(
    *,
    request_character: str = "a",
    theorem: str = "fixture theorem",
    generated_proof: str = "by\n  induction n <;> simp_all",
    prompt_text: str = PROMPT_CANARY,
) -> InternalAnnotationItem:
    return InternalAnnotationItem(
        request_id=request_character * 64,
        theorem_id=theorem.replace(" ", "-"),
        theorem_statement="theorem fixture (n : Nat) : n = n",
        supplied_informal_proof="Use induction and simplify each case.",
        generated_lean_proof=generated_proof,
        rubric_text="Route A is induction. Route B is direct algebra.",
        rubric_version=RUBRIC_VERSION,
        extractor_version=EXTRACTOR_VERSION,
        signature_evidence=("induction at line two",),
        sensitive=SensitiveMetadata(
            model_name=MODEL_CANARY,
            condition_key=CONDITION_CANARY,
            prompt_text=prompt_text,
            sample_index=SAMPLE_INDEX,
        ),
    )


def _label_payload(blind_id: str, packet_checksum: str) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "label_id": "human-label-1",
        "blind_id": blind_id,
        "packet_checksum": packet_checksum,
        "annotator_id": "annotator-1",
        "calibration_round": "calibration-1",
        "rubric_version": RUBRIC_VERSION,
        "extractor_version": EXTRACTOR_VERSION,
        "classification": "match_A",
        "strategy_labels": ["induction"],
        "utilization": "used",
        "alignments": [
            {
                "informal_step_ids": ["a1"],
                "formal_evidence_ids": ["line-two"],
                "alignment_type": "one_to_one",
                "utilization": "used",
                "confidence": 1.0,
            }
        ],
        "dependency_edges": [],
        "strategy_expressibility_uncertain": False,
        "explanation": "The proof uses the route's induction step.",
    }


def _bundle_corpus(bundle_dir: Path) -> str:
    parts: list[str] = []
    for path in sorted(bundle_dir.rglob("*")):
        parts.append(path.relative_to(bundle_dir).as_posix())
        if path.is_file():
            parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)
