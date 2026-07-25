"""Fail-closed SLURM job-liveness probes for stale-lock recovery."""

from __future__ import annotations

import subprocess

_TERMINAL_STATES = frozenset(
    {
        "BOOT_FAIL",
        "CANCELLED",
        "COMPLETED",
        "DEADLINE",
        "FAILED",
        "NODE_FAIL",
        "OUT_OF_MEMORY",
        "PREEMPTED",
        "REVOKED",
        "TIMEOUT",
    }
)


def slurm_job_is_active(job_id: str) -> bool:
    """Returns false only when ``sacct`` proves every allocation is terminal."""
    try:
        result = subprocess.run(
            [
                "sacct",
                "--noheader",
                "--parsable2",
                "--allocations",
                "--jobs",
                job_id,
                "--format=State",
            ],
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return True
    if result.returncode != 0:
        return True
    states = tuple(
        line.partition("|")[0].strip().split(maxsplit=1)[0].rstrip("+")
        for line in result.stdout.splitlines()
        if line.partition("|")[0].strip()
    )
    return not states or any(state not in _TERMINAL_STATES for state in states)
