"""Typer sub-application for blinded annotation and agreement workflows."""

from __future__ import annotations

import json
import os
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Any

import typer
from pydantic import ValidationError

from proof_faithfulness.artifacts import RunArtifactStore
from proof_faithfulness.evaluation.annotations import import_human_labels
from proof_faithfulness.evaluation.blinding import (
    export_blinded_bundle,
    publish_bytes_exclusive,
)
from proof_faithfulness.evaluation.inputs import (
    EvaluationInputError,
    prepare_internal_annotation_item,
)
from proof_faithfulness.evaluation.metrics import (
    binary_agreement,
    edge_agreement,
    multilabel_agreement,
    nominal_agreement,
)
from proof_faithfulness.evaluation.models import (
    EvaluationPreparationSpec,
    HumanLabel,
    ImportedHumanLabel,
    InternalAnnotationItem,
)
from proof_faithfulness.generation.planning import PlannedGeneration

app = typer.Typer(help="Export blinded packets and validate independent annotations.")


@app.command("prepare")
def prepare_command(
    contexts_path: Annotated[
        Path,
        typer.Option("--contexts", help="Request-bound evaluation context JSONL."),
    ],
    outputs_root: Annotated[
        Path,
        typer.Option("--outputs-root", help="Root containing the generation run."),
    ],
    run_id: Annotated[str, typer.Option("--run-id", help="Generation run identifier.")],
    output_path: Annotated[
        Path,
        typer.Option("--output", help="New internal annotation-item JSONL path."),
    ],
) -> None:
    """Prepares accepted generated proofs for later blinded export."""
    store = RunArtifactStore(outputs_root, run_id)
    try:
        planned = _load_planned_inputs(store)
        specs = _load_preparation_specs(contexts_path)
        unknown = set(specs) - set(planned)
        if unknown:
            raise ValueError(f"Evaluation contexts reference unknown requests: {sorted(unknown)}")
        items = tuple(
            prepare_internal_annotation_item(
                store=store,
                model_input=planned[request_id].model_input,
                spec=specs[request_id],
            )
            for request_id in sorted(specs)
        )
        payload = b"".join(_canonical_json_bytes(item.model_dump(mode="json")) for item in items)
        publish_bytes_exclusive(output_path, payload)
    except (EvaluationInputError, OSError, ValidationError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"prepared_items={len(items)}")


@app.command("export")
def export_command(
    input_path: Annotated[Path, typer.Option("--input", help="Internal item JSONL.")],
    output_dir: Annotated[Path, typer.Option("--output", help="Public packet directory.")],
    mapping_path: Annotated[
        Path,
        typer.Option("--mapping", help="Private identity-map path outside the packet."),
    ],
    key_env: Annotated[
        str,
        typer.Option(help="Environment variable containing the blinding key."),
    ] = "PROOF_FAITHFULNESS_BLINDING_KEY",
) -> None:
    """Exports an immutable packet after scanning for sensitive metadata."""
    key = os.environ.get(key_env)
    if key is None:
        raise typer.BadParameter(f"Missing blinding-key environment variable: {key_env}")
    items = _load_internal_items(input_path)
    blinded = export_blinded_bundle(items, output_dir, mapping_path, key.encode("utf-8"))
    typer.echo(f"exported_items={len(blinded)}")


@app.command("import-labels")
def import_labels_command(
    input_paths: Annotated[
        list[Path],
        typer.Option("--input", help="Independent human-label JSONL; repeat as needed."),
    ],
    mapping_path: Annotated[Path, typer.Option("--mapping", help="Private identity map.")],
    bundle_dir: Annotated[Path, typer.Option("--bundle", help="Exact public packet directory.")],
    output_path: Annotated[
        Path | None,
        typer.Option("--output", help="Optional resolved-label artifact."),
    ] = None,
) -> None:
    """Validates human labels and optionally writes an internal resolved artifact."""
    imported = import_human_labels(input_paths, mapping_path, bundle_dir)
    if output_path is not None:
        payload = b"".join(_canonical_json_bytes(item.model_dump(mode="json")) for item in imported)
        try:
            publish_bytes_exclusive(output_path, payload)
        except FileExistsError as error:
            raise typer.BadParameter(
                f"Resolved-label output already exists: {output_path}"
            ) from error
    typer.echo(f"imported_labels={len(imported)}")


@app.command("agreement")
def agreement_command(
    first_path: Annotated[Path, typer.Option("--first", help="First annotator JSONL.")],
    second_path: Annotated[Path, typer.Option("--second", help="Second annotator JSONL.")],
    mapping_path: Annotated[Path, typer.Option("--mapping", help="Private identity map.")],
    bundle_dir: Annotated[Path, typer.Option("--bundle", help="Exact public packet directory.")],
    targets_path: Annotated[
        Path,
        typer.Option(help="Internal JSON mapping blind IDs to match_A or match_B."),
    ],
) -> None:
    """Prints all provisional S5 agreement statistics as canonical JSON."""
    imported = import_human_labels((first_path, second_path), mapping_path, bundle_dir)
    pairs = _pair_labels(imported)
    targets = _load_targets(targets_path, set(pairs))
    first = [pair[0].original for pair in pairs.values()]
    second = [pair[1].original for pair in pairs.values()]
    binary = binary_agreement(
        [label.classification == targets[label.blind_id] for label in first],
        [label.classification == targets[label.blind_id] for label in second],
    )
    multilabel = multilabel_agreement(
        [label.strategy_labels for label in first],
        [label.strategy_labels for label in second],
    )
    edges = edge_agreement(
        [_edge_set(label) for label in first],
        [_edge_set(label) for label in second],
    )
    utilization = nominal_agreement(
        [label.utilization for label in first],
        [label.utilization for label in second],
    )
    typer.echo(
        _canonical_json_bytes(
            {
                "binary_target_match": asdict(binary),
                "strategy_labels": asdict(multilabel),
                "dependency_edges": asdict(edges),
                "utilization": asdict(utilization),
            }
        ).decode("utf-8"),
        nl=False,
    )


def _load_planned_inputs(store: RunArtifactStore) -> dict[str, PlannedGeneration]:
    relative_path = "requests.jsonl"
    if not store.verified(relative_path):
        raise ValueError("Generation requests are missing or checksum-invalid")
    try:
        lines = (store.path / relative_path).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError("Generation requests are unreadable") from error
    planned: dict[str, PlannedGeneration] = {}
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            item = PlannedGeneration.model_validate_json(line)
        except ValidationError as error:
            raise ValueError(
                f"Invalid generation request at requests.jsonl:{line_number}"
            ) from error
        request_id = item.model_input.request.request_id
        if request_id in planned:
            raise ValueError(f"Duplicate generation request ID: {request_id}")
        planned[request_id] = item
    if not planned:
        raise ValueError("Generation request artifact contains no requests")
    return planned


def _load_preparation_specs(path: Path) -> dict[str, EvaluationPreparationSpec]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError(f"Unable to read evaluation contexts: {path}") from error
    specs: dict[str, EvaluationPreparationSpec] = {}
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            spec = EvaluationPreparationSpec.model_validate_json(line)
        except ValidationError as error:
            raise ValueError(f"Invalid evaluation context at {path}:{line_number}") from error
        if spec.request_id in specs:
            raise ValueError(f"Duplicate evaluation context request ID: {spec.request_id}")
        specs[spec.request_id] = spec
    if not specs:
        raise ValueError("Evaluation context artifact contains no items")
    return specs


def _load_internal_items(path: Path) -> tuple[InternalAnnotationItem, ...]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError(f"Unable to read internal annotation items: {path}") from error
    items: list[InternalAnnotationItem] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            items.append(InternalAnnotationItem.model_validate_json(line))
        except ValidationError as error:
            raise ValueError(f"Invalid internal item at {path}:{line_number}") from error
    return tuple(items)


def _pair_labels(
    imported: tuple[ImportedHumanLabel, ...],
) -> dict[str, tuple[ImportedHumanLabel, ImportedHumanLabel]]:
    grouped: defaultdict[str, list[ImportedHumanLabel]] = defaultdict(list)
    for label in imported:
        grouped[label.original.blind_id].append(label)
    pairs: dict[str, tuple[ImportedHumanLabel, ImportedHumanLabel]] = {}
    for blind_id in sorted(grouped):
        labels = sorted(grouped[blind_id], key=lambda item: item.original.annotator_id)
        if len(labels) != 2:
            raise ValueError(f"Agreement requires exactly two labels for {blind_id}")
        pairs[blind_id] = (labels[0], labels[1])
    return pairs


def _load_targets(path: Path, expected_blind_ids: set[str]) -> dict[str, str]:
    try:
        value: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Unable to load target labels: {path}") from error
    if not isinstance(value, dict) or set(value) != expected_blind_ids:
        raise ValueError("Target labels must cover exactly the agreement items")
    if any(target not in {"match_A", "match_B"} for target in value.values()):
        raise ValueError("Every target label must be match_A or match_B")
    return {str(blind_id): str(target) for blind_id, target in value.items()}


def _edge_set(label: HumanLabel) -> set[tuple[str, str]]:
    return {(edge.predecessor_step_id, edge.successor_step_id) for edge in label.dependency_edges}


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value, allow_nan=False, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        + "\n"
    ).encode("utf-8")
