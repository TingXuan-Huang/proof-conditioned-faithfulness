"""Command-line entrypoints for isolated backend calibration runs."""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Annotated

import typer

from proof_faithfulness.artifacts import RunArtifactStore
from proof_faithfulness.calibration import (
    assess_calibration,
    attach_runtime_evidence,
    attach_runtime_metadata,
    build_calibration_request,
    load_calibration_fixture,
    run_calibration_generation,
    vllm_server_argv,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE = PROJECT_ROOT / "configs" / "calibration" / "identity.yaml"
DEFAULT_CONDITIONS = PROJECT_ROOT / "configs" / "experiment" / "conditions.yaml"
DEFAULT_PROMPTS = PROJECT_ROOT / "prompts"
DEFAULT_OUTPUTS = PROJECT_ROOT / "outputs" / "calibration"

app = typer.Typer(help="Run non-experimental real-backend compatibility checks.")


@app.command("run")
def run_command(
    models_path: Annotated[Path, typer.Option("--models")],
    run_id: Annotated[str, typer.Option("--run-id")],
    fixture_path: Annotated[Path, typer.Option("--fixture")] = DEFAULT_FIXTURE,
    conditions_path: Annotated[Path, typer.Option("--conditions")] = DEFAULT_CONDITIONS,
    prompts_root: Annotated[Path, typer.Option("--prompts-root")] = DEFAULT_PROMPTS,
    outputs_root: Annotated[Path, typer.Option("--outputs-root")] = DEFAULT_OUTPUTS,
    approvals_root: Annotated[Path, typer.Option("--approvals-root")] = Path("approvals"),
    approval_scope: Annotated[str, typer.Option("--approval-scope")] = "calibration-testing",
    aggregate_ceiling_usd: Annotated[str, typer.Option("--aggregate-ceiling-usd")] = "500",
) -> None:
    """Generate one calibration sample and verify resume without reissuing it."""
    try:
        fixture = load_calibration_fixture(fixture_path)
        planned, model = build_calibration_request(
            fixture=fixture,
            models_path=models_path,
            conditions_path=conditions_path,
            prompts_root=prompts_root,
        )
        first, second = run_calibration_generation(
            planned=planned,
            model=model,
            store=RunArtifactStore(outputs_root, run_id),
            approvals_root=approvals_root,
            approval_scope=approval_scope,
            aggregate_ceiling_usd=Decimal(aggregate_ceiling_usd),
        )
    except (InvalidOperation, OSError, TypeError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(
        json.dumps(
            {
                "request_id": planned.model_input.request.request_id,
                "first": first.model_dump(mode="json"),
                "resume": second.model_dump(mode="json"),
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("assess")
def assess_command(
    models_path: Annotated[Path, typer.Option("--models")],
    run_id: Annotated[str, typer.Option("--run-id")],
    fixture_path: Annotated[Path, typer.Option("--fixture")] = DEFAULT_FIXTURE,
    conditions_path: Annotated[Path, typer.Option("--conditions")] = DEFAULT_CONDITIONS,
    prompts_root: Annotated[Path, typer.Option("--prompts-root")] = DEFAULT_PROMPTS,
    outputs_root: Annotated[Path, typer.Option("--outputs-root")] = DEFAULT_OUTPUTS,
    project_root: Annotated[Path, typer.Option("--project-root")] = PROJECT_ROOT,
) -> None:
    """Run Lean, dependency, and evaluation preparation on a terminal response."""
    try:
        fixture = load_calibration_fixture(fixture_path)
        planned, _ = build_calibration_request(
            fixture=fixture,
            models_path=models_path,
            conditions_path=conditions_path,
            prompts_root=prompts_root,
        )
        report = assess_calibration(
            fixture=fixture,
            planned=planned,
            store=RunArtifactStore(outputs_root, run_id),
            project_root=project_root,
        )
    except (OSError, TypeError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True))


@app.command("attach-runtime")
def attach_runtime_command(
    run_id: Annotated[str, typer.Option("--run-id")],
    metadata_path: Annotated[Path, typer.Option("--metadata")],
    outputs_root: Annotated[Path, typer.Option("--outputs-root")] = DEFAULT_OUTPUTS,
) -> None:
    """Attach validated, non-secret serving and hardware metadata to a run."""
    try:
        metadata = attach_runtime_metadata(
            store=RunArtifactStore(outputs_root, run_id),
            metadata_path=metadata_path,
        )
    except (OSError, TypeError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(json.dumps(metadata.model_dump(mode="json"), indent=2, sort_keys=True))


@app.command("attach-evidence")
def attach_evidence_command(
    run_id: Annotated[str, typer.Option("--run-id")],
    evidence_path: Annotated[Path, typer.Option("--evidence")],
    name: Annotated[str, typer.Option("--name")],
    outputs_root: Annotated[Path, typer.Option("--outputs-root")] = DEFAULT_OUTPUTS,
) -> None:
    """Attach a bounded runtime log or measurement file to a calibration run."""
    try:
        checksum = attach_runtime_evidence(
            store=RunArtifactStore(outputs_root, run_id),
            evidence_path=evidence_path,
            name=name,
        )
    except (OSError, TypeError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(checksum)


@app.command("vllm-argv")
def vllm_argv_command(
    models_path: Annotated[Path, typer.Option("--models")],
) -> None:
    """Print one exact vLLM server argument per line for a SLURM launcher."""
    try:
        argv = vllm_server_argv(models_path)
    except (OSError, TypeError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo("\n".join(argv))
