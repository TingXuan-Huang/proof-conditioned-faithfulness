from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from proof_faithfulness.artifacts import RunArtifactStore
from proof_faithfulness.calibration import (
    assess_calibration,
    build_calibration_request,
    load_calibration_fixture,
    run_calibration_generation,
)
from proof_faithfulness.generation.budget import MissingApprovalError

PROJECT_ROOT = Path(__file__).parents[2]
CONDITIONS = PROJECT_ROOT / "configs" / "experiment" / "conditions.yaml"
PROMPTS = PROJECT_ROOT / "prompts"
FIXTURE = PROJECT_ROOT / "configs" / "calibration" / "identity.yaml"


def _write_single_mock(path: Path) -> None:
    source = yaml.safe_load(
        (PROJECT_ROOT / "configs" / "experiment" / "planning-models.yaml").read_text(
            encoding="utf-8"
        )
    )
    source["models"] = source["models"][:1]
    source["models"][0]["backend_config"]["response_text"] = (
        "by\n  simpa using Nat.add_zero n"
    )
    path.write_text(yaml.safe_dump(source, sort_keys=False), encoding="utf-8")


def test_calibration_runs_cross_stage_and_resumes(tmp_path: Path) -> None:
    models_path = tmp_path / "models.yaml"
    _write_single_mock(models_path)
    fixture = load_calibration_fixture(FIXTURE)
    planned, model = build_calibration_request(
        fixture=fixture,
        models_path=models_path,
        conditions_path=CONDITIONS,
        prompts_root=PROMPTS,
    )
    store = RunArtifactStore(tmp_path / "calibration", "calibration-mock")

    first, second = run_calibration_generation(
        planned=planned,
        model=model,
        store=store,
        approvals_root=tmp_path / "approvals",
        approval_scope="calibration-testing",
        harness_git_commit="a" * 40,
    )
    report = assess_calibration(
        fixture=fixture,
        planned=planned,
        store=store,
        project_root=PROJECT_ROOT,
    )

    assert first.processed == 1
    assert second.processed == 0
    assert second.skipped == 1
    assert report.response_verified is True
    assert report.response_nonempty is True
    assert report.lean_check.status == "passed"
    assert report.dependency_probe.status == "passed"
    assert report.evaluation_preparation.status == "passed"
    assert store.verified("reports/resume.json")
    assert store.verified("reports/assessment.json")


def test_calibration_rejects_experimental_namespace(tmp_path: Path) -> None:
    models_path = tmp_path / "models.yaml"
    _write_single_mock(models_path)
    fixture = load_calibration_fixture(FIXTURE)
    planned, model = build_calibration_request(
        fixture=fixture,
        models_path=models_path,
        conditions_path=CONDITIONS,
        prompts_root=PROMPTS,
    )
    store = RunArtifactStore(tmp_path / "pilot", "pilot-run")

    try:
        run_calibration_generation(
            planned=planned,
            model=model,
            store=store,
            approvals_root=tmp_path / "approvals",
            approval_scope="calibration-testing",
            harness_git_commit="a" * 40,
        )
    except ValueError as error:
        assert "outputs/calibration" in str(error)
    else:
        raise AssertionError("Calibration accepted an experimental namespace")


def test_meta_calibration_refuses_before_secret_or_network(tmp_path: Path) -> None:
    fixture = load_calibration_fixture(FIXTURE)
    planned, model = build_calibration_request(
        fixture=fixture,
        models_path=PROJECT_ROOT / "configs" / "calibration" / "meta_muse_spark_1_1.yaml",
        conditions_path=CONDITIONS,
        prompts_root=PROMPTS,
    )

    with pytest.raises(MissingApprovalError):
        run_calibration_generation(
            planned=planned,
            model=model,
            store=RunArtifactStore(
                tmp_path / "calibration", "calibration-meta-refusal"
            ),
            approvals_root=tmp_path / "empty-approvals",
            approval_scope="calibration-testing",
            harness_git_commit="a" * 40,
        )
