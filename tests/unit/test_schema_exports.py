"""Tests that checked-in JSON Schemas match the current Pydantic contracts."""

import json
from pathlib import Path

import pytest

from proof_faithfulness.schema import SCHEMA_MODELS, ContractModel

PROJECT_ROOT = Path(__file__).parents[2]


@pytest.mark.parametrize("model", SCHEMA_MODELS, ids=lambda model: model.__name__)
def test_emitted_schema_matches_model(model: type[ContractModel]) -> None:
    schema_path = PROJECT_ROOT / "schemas" / f"{model.__name__}.schema.json"
    expected = (
        json.dumps(
            model.model_json_schema(),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    assert schema_path.read_text(encoding="utf-8") == expected
