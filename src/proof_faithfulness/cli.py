"""Command-line interface for proof-faithfulness workflows."""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Annotated

import typer
import yaml

from proof_faithfulness import __version__
from proof_faithfulness.artifacts import atomic_write_bytes
from proof_faithfulness.evaluation.cli import app as evaluation_app
from proof_faithfulness.generation.cli import generation_app
from proof_faithfulness.lean import (
    DEFAULT_MEMORY_LIMIT_MB,
    DEFAULT_WARMUP_TIMEOUT_SECONDS,
    warm_mathlib_cache,
)
from proof_faithfulness.models.config import compute_adapter_config_hash, load_adapter_config
from proof_faithfulness.schema import SCHEMA_MODELS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
app = typer.Typer(help="Build and run proof-conditioned faithfulness experiments.")
schema_app = typer.Typer(help="Inspect and export versioned data contracts.")
environment_app = typer.Typer(help="Inspect the local execution environment.")
model_app = typer.Typer(help="Inspect model and prover adapter configuration.")
app.add_typer(schema_app, name="schema")
app.add_typer(environment_app, name="env")
app.add_typer(model_app, name="model")
app.add_typer(generation_app)
app.add_typer(evaluation_app, name="evaluation")


@app.callback(invoke_without_command=True)
def main(
    version: Annotated[
        bool,
        typer.Option("--version", help="Print the package version and exit."),
    ] = False,
) -> None:
    """Handles global CLI options."""
    if version:
        typer.echo(__version__)
        raise typer.Exit()


@schema_app.command("export")
def export_schemas(
    output_dir: Annotated[
        Path,
        typer.Option(help="Directory for emitted JSON Schema files."),
    ] = Path("schemas"),
    force: Annotated[
        bool,
        typer.Option("--force", help="Replace schemas whose content has changed."),
    ] = False,
) -> None:
    """Exports the public Pydantic contracts as deterministic JSON Schema files."""
    schemas: list[tuple[Path, bytes]] = []
    for model in SCHEMA_MODELS:
        schema = model.model_json_schema()
        content = json.dumps(schema, ensure_ascii=True, indent=2, sort_keys=True).encode() + b"\n"
        output_path = output_dir / f"{model.__name__}.schema.json"
        schemas.append((output_path, content))
    _reject_changed_outputs(schemas, force=force)
    for output_path, content in schemas:
        if not output_path.exists() or output_path.read_bytes() != content:
            atomic_write_bytes(output_path, content)
        typer.echo(output_path)


@environment_app.command("doctor")
def environment_doctor(
    output: Annotated[
        Path | None,
        typer.Option(help="Optional JSON output path."),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", help="Replace a changed output file."),
    ] = False,
) -> None:
    """Reports non-secret tool and host facts used to diagnose server setup."""
    facts = {
        "schema_version": "1.0",
        "host": {
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "platform": platform.platform(),
            "python": platform.python_version(),
        },
        "tools": {
            command: _tool_version(command)
            for command in ("uv", "elan", "lean", "lake", "git", "apptainer", "sinfo")
        },
    }
    content = json.dumps(facts, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    if output is not None:
        content_bytes = content.encode("utf-8")
        _reject_changed_outputs([(output, content_bytes)], force=force)
        if not output.exists() or output.read_bytes() != content_bytes:
            atomic_write_bytes(output, content_bytes)
    typer.echo(content, nl=False)


@environment_app.command("lean-warmup")
def lean_warmup(
    project_root: Annotated[
        Path,
        typer.Option("--project-root", help="Lake project containing the pinned toolchain."),
    ] = PROJECT_ROOT,
    timeout_seconds: Annotated[
        float,
        typer.Option("--timeout-seconds", help="Separate diagnostic warm-up ceiling."),
    ] = DEFAULT_WARMUP_TIMEOUT_SECONDS,
    memory_limit_mb: Annotated[
        int,
        typer.Option("--memory-limit-mb", help="Warm-up address-space ceiling in MiB."),
    ] = DEFAULT_MEMORY_LIMIT_MB,
) -> None:
    """Loads the fixed trusted Mathlib environment before a checker batch."""
    try:
        result = warm_mathlib_cache(
            project_root=project_root,
            timeout_seconds=timeout_seconds,
            memory_limit_mb=memory_limit_mb,
        )
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(
        json.dumps(
            {
                "exit_code": result.exit_code,
                "setup_error": result.setup_error,
                "success": result.success,
                "timed_out": result.timed_out,
                "wall_time_seconds": result.wall_time_seconds,
            },
            indent=2,
            sort_keys=True,
        )
    )
    if not result.success:
        diagnostic = (result.stderr or result.stdout).strip()
        if diagnostic:
            typer.echo(diagnostic, err=True)
        raise typer.Exit(code=1)


@model_app.command("inspect")
def inspect_model_config(
    config_path: Annotated[
        Path,
        typer.Option("--config", help="YAML adapter configuration to inspect."),
    ],
) -> None:
    """Validates an adapter config and prints only non-secret identity metadata."""
    try:
        config = load_adapter_config(config_path)
    except OSError as error:
        raise typer.BadParameter(
            f"Unable to read adapter configuration: {config_path}",
            param_hint="--config",
        ) from error
    except (TypeError, ValueError, yaml.YAMLError) as error:
        # Pydantic validation errors may reproduce rejected input values, so do not
        # surface their text at a boundary intended to be safe for logs.
        raise typer.BadParameter(
            f"Invalid adapter configuration: {config_path}",
            param_hint="--config",
        ) from error

    metadata = {
        "adapter": config.adapter,
        "key": config.key,
        "provider": config.provider,
        "model_id": config.model_id,
        "revision": config.revision,
        "backend_config_hash": compute_adapter_config_hash(config),
        "capability_flags": list(config.capabilities.enabled_flags()),
        "api_key_env": config.api_key_env,
    }
    typer.echo(json.dumps(metadata, ensure_ascii=True, indent=2, sort_keys=True))


def _tool_version(command: str) -> str | None:
    executable = shutil.which(command)
    if executable is None:
        return None
    version_arguments = ["--version"]
    if command == "sinfo":
        version_arguments = ["--version"]
    try:
        result = subprocess.run(
            [executable, *version_arguments],
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"
    output = result.stdout.strip() or result.stderr.strip()
    return output.splitlines()[0] if output else f"exit {result.returncode}"


def _reject_changed_outputs(outputs: list[tuple[Path, bytes]], *, force: bool) -> None:
    if force:
        return
    changed_paths = [
        path for path, content in outputs if path.exists() and path.read_bytes() != content
    ]
    if changed_paths:
        paths = ", ".join(str(path) for path in changed_paths)
        raise typer.BadParameter(f"Refusing to replace changed output(s): {paths}; pass --force")
