"""Offline executable fixture for the prover subprocess contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--response", type=Path, required=True)
    arguments = parser.parse_args()

    request = json.loads(arguments.request.read_text(encoding="utf-8"))
    assert request["schema_version"] == "1.0"
    assert request["pipeline"] in {"proofbridge", "proofflow"}
    assert request["generation_request"]["request_id"]
    assert request["messages"]
    response = {
        "text": "by\n  trivial",
        "provider_request_id": f"{request['pipeline']}-fixture",
        "input_tokens": 12,
        "output_tokens": 3,
        "usd_cost": 0.0,
        "finish_reason": "stop",
    }
    arguments.response.write_text(
        json.dumps(response, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
