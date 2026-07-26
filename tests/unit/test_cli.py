"""Tests for CLI output overwrite guardrails."""

import json
from pathlib import Path

from typer.testing import CliRunner

import proof_faithfulness.cli as cli_module
from proof_faithfulness.cli import app
from proof_faithfulness.lean import LeanWarmupResult

runner = CliRunner()


def test_top_level_generation_plan_reports_exact_tier_one_counts() -> None:
    result = runner.invoke(app, ["plan", "--tier", "1", "--split", "pilot"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert {item["model_key"]: item["requests"] for item in payload["models"]} == {
        "proof_conditioned_model": 45,
        "theorem_only_baseline": 15,
    }
    assert payload["total_requests"] == 60
    assert payload["split_status"] == "proposed"


def test_lean_warmup_uses_separate_diagnostic_timeout(
    tmp_path: Path,
    monkeypatch,
) -> None:
    observed: dict[str, object] = {}

    def warmup(**kwargs) -> LeanWarmupResult:
        observed.update(kwargs)
        return LeanWarmupResult(
            exit_code=0,
            stdout="",
            stderr="",
            wall_time_seconds=1.25,
        )

    monkeypatch.setattr(cli_module, "warm_mathlib_cache", warmup)
    result = runner.invoke(
        app,
        [
            "env",
            "lean-warmup",
            "--project-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.output) == {
        "exit_code": 0,
        "setup_error": None,
        "success": True,
        "timed_out": False,
        "wall_time_seconds": 1.25,
    }
    assert observed["project_root"] == tmp_path
    assert observed["timeout_seconds"] == 1200.0
    assert observed["memory_limit_mb"] == 4096


def test_schema_export_requires_force_for_changed_output(tmp_path: Path) -> None:
    output_dir = tmp_path / "schemas"
    first_result = runner.invoke(app, ["schema", "export", "--output-dir", str(output_dir)])
    assert first_result.exit_code == 0
    schema_path = output_dir / "BenchmarkRecord.schema.json"
    schema_path.write_text("changed\n", encoding="utf-8")

    refused_result = runner.invoke(app, ["schema", "export", "--output-dir", str(output_dir)])
    assert refused_result.exit_code == 2
    assert schema_path.read_text(encoding="utf-8") == "changed\n"
    assert "pass --force" in refused_result.output

    forced_result = runner.invoke(
        app,
        ["schema", "export", "--output-dir", str(output_dir), "--force"],
    )
    assert forced_result.exit_code == 0
    assert schema_path.read_text(encoding="utf-8").startswith("{")


def test_model_inspect_prints_non_secret_metadata_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_path = tmp_path / "frontier.yaml"
    config_path.write_text(
        """\
key: test_frontier
category: frontier_api
provider: openai_compat_api
model_id: test/model
revision: abc123
base_url: https://example.test/v1
api_key_env: TEST_PROVIDER_KEY
chat_template: test_chat_v1
decoding:
  temperature: 0.2
  top_p: 1.0
  max_tokens: 128
  seed_base: 7
concurrency: 1
pricing_usd_per_mtok: {input: 1.0, output: 2.0}
pipeline_commit: null
context_window: 4096
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("TEST_PROVIDER_KEY", "do-not-print-this-secret")

    result = runner.invoke(app, ["model", "inspect", "--config", str(config_path)])

    assert result.exit_code == 0
    metadata = json.loads(result.output)
    backend_config_hash = metadata.pop("backend_config_hash")
    assert len(backend_config_hash) == 64
    assert metadata == {
        "adapter": "openai_compatible",
        "key": "test_frontier",
        "provider": "openai_compat_api",
        "model_id": "test/model",
        "revision": "abc123",
        "capability_flags": [
            "proof_conditioning",
            "deterministic_seed",
            "cost_reporting",
        ],
        "api_key_env": "TEST_PROVIDER_KEY",
    }
    assert "do-not-print-this-secret" not in result.output


def test_model_inspect_does_not_leak_rejected_config_values(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yaml"
    secret = "do-not-print-invalid-secret"
    config_path.write_text(
        f"""\
key: test_frontier
category: frontier_api
provider: openai_compat_api
model_id: test/model
revision: abc123
base_url: https://example.test/v1
api_key_env: invalid-name
unexpected_secret: {secret}
chat_template: test_chat_v1
decoding: {{temperature: 0.2, top_p: 1.0, max_tokens: 128, seed_base: 7}}
concurrency: 1
pricing_usd_per_mtok: {{input: 1.0, output: 2.0}}
pipeline_commit: null
context_window: 4096
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["model", "inspect", "--config", str(config_path)])

    assert result.exit_code == 2
    assert "Invalid adapter configuration" in result.output
    assert secret not in result.output


def test_model_inspect_rejects_non_mapping_yaml_without_traceback(tmp_path: Path) -> None:
    config_path = tmp_path / "list.yaml"
    config_path.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

    result = runner.invoke(app, ["model", "inspect", "--config", str(config_path)])

    assert result.exit_code == 2
    assert "Invalid adapter configuration" in result.output
    assert "Traceback" not in result.output
