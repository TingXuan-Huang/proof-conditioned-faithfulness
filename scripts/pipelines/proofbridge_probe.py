"""Fail explicitly when the pinned ProofBridge release cannot perform inference."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--response", type=Path, required=True)
    args = parser.parse_args()

    request = json.loads(args.request.read_text(encoding="utf-8"))
    if request.get("pipeline") != "proofbridge" or not request.get("messages"):
        raise ValueError("ProofBridge probe received an invalid harness request")

    evidence = {
        "schema_version": "1.0",
        "status": "incompatible",
        "reason": (
            "The pinned upstream release has no documented runnable inference entrypoint "
            "and does not publish a trained ProofBridge checkpoint."
        ),
        "request_id": request["generation_request"]["request_id"],
        "checked_paths": [
            "README.md",
            "joint_embedding/",
            "LEAN_interaction/checkLEAN.py",
        ],
    }
    print(json.dumps(evidence, ensure_ascii=True, sort_keys=True), file=sys.stderr)
    return 78


if __name__ == "__main__":
    raise SystemExit(main())
