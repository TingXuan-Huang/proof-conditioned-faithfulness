from __future__ import annotations

import subprocess

import pytest

from proof_faithfulness.generation.scheduler import slurm_job_is_active


@pytest.mark.parametrize(
    ("stdout", "expected"),
    [
        ("COMPLETED|\n", False),
        ("CANCELLED by 1000|\n", False),
        ("FAILED|\nCOMPLETED|\n", False),
        ("RUNNING|\n", True),
        ("COMPLETING|\n", True),
        ("", True),
    ],
)
def test_slurm_liveness_requires_terminal_sacct_evidence(
    monkeypatch: pytest.MonkeyPatch,
    stdout: str,
    expected: bool,
) -> None:
    def run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=["sacct"], returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr(subprocess, "run", run)
    assert slurm_job_is_active("12345") is expected


def test_slurm_liveness_fails_closed_when_sacct_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=["sacct"], returncode=1, stdout="", stderr="error")

    monkeypatch.setattr(subprocess, "run", run)
    assert slurm_job_is_active("12345") is True
