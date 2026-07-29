from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from proof_faithfulness.artifacts import RunArtifactStore
from proof_faithfulness.generation.artifacts import (
    ResponseArtifactError,
    TerminalArtifactConflictError,
    load_verified_response,
    response_relative_path,
    write_generation_response,
)
from proof_faithfulness.generation.cli import ManifestMockAdapter
from proof_faithfulness.generation.config import PlanningModel, load_condition_matrix
from proof_faithfulness.generation.planning import PromptTheorem, build_generation_plan
from proof_faithfulness.generation.prompts import PromptRepository
from proof_faithfulness.models import AdapterResult, ModelCapabilities, ModelInput
from proof_faithfulness.models.config import (
    DecodingConfig,
    MockAdapterConfig,
)

PROJECT_ROOT = Path(__file__).parents[2]


def _request_and_result() -> tuple[ModelInput, AdapterResult]:
    capabilities = ModelCapabilities(
        proof_conditioning=True,
        deterministic_seed=True,
        local_inference=True,
        cost_reporting=True,
    )
    model = PlanningModel(
        backend_config=MockAdapterConfig(
            model_key="deterministic_mock",
            model_id="deterministic-mock",
            model_revision="mock-v1",
            capabilities=capabilities,
        ),
        mock_chat_template="mock_chat_v1.txt",
        mock_decoding=DecodingConfig(
            temperature=0.2,
            top_p=1,
            max_tokens=8192,
            seed_base=20260724,
        ),
        mock_max_input_tokens=16384,
    )
    theorem = PromptTheorem.from_text(
        theorem_id="artifact-fixture",
        split="pilot",
        imports=("Mathlib",),
        lean_statement="example : True := by",
        proof_a="Truth is true.",
        proof_b="Use the constructor of True.",
        paraphrase_a="Immediate.",
        paraphrase_b="Construct truth.",
    )
    item = build_generation_plan(
        theorems=(theorem,),
        models=(model,),
        matrix=load_condition_matrix(PROJECT_ROOT / "configs" / "experiment" / "conditions.yaml"),
        tier=1,
        prompt_repository=PromptRepository(PROJECT_ROOT / "prompts"),
    ).requests[0]
    return item.model_input, ManifestMockAdapter(model).generate(item.model_input)


def test_response_writer_emits_exact_contract_and_sha_sidecar(tmp_path: Path) -> None:
    model_input, result = _request_and_result()
    store = RunArtifactStore(tmp_path, "artifact-run")
    store.initialize()
    started = datetime(2026, 7, 25, tzinfo=UTC)
    completed = started + timedelta(seconds=1.25)
    response = write_generation_response(
        store=store,
        model_input=model_input,
        result=result,
        started_at=started,
        completed_at=completed,
        harness_git_commit="a" * 40,
    )
    relative = response_relative_path(response.request_id)
    payload = json.loads((store.path / relative).read_text(encoding="utf-8"))
    assert set(payload) == {
        "schema_version",
        "request_id",
        "provider_request_id",
        "model_key",
        "revision",
        "raw",
        "text",
        "finish_reason",
        "usage",
        "usd_cost",
        "latency_s",
        "started_at",
        "completed_at",
        "harness_git_commit",
    }
    assert json.loads(payload["raw"])["id"].startswith("mock-")
    assert payload["provider_request_id"] == result.provider_request_id
    assert payload["raw"] == result.raw_response.decode("utf-8")
    assert payload["latency_s"] == 1.25
    assert store.verified(relative)
    assert (store.path / f"{relative}.sha256").is_file()


def test_writer_quarantines_checksum_invalid_terminal_before_replacement(tmp_path: Path) -> None:
    model_input, result = _request_and_result()
    store = RunArtifactStore(tmp_path, "artifact-run")
    store.initialize()
    started = datetime(2026, 7, 25, tzinfo=UTC)
    response = write_generation_response(
        store=store,
        model_input=model_input,
        result=result,
        started_at=started,
        completed_at=started,
        harness_git_commit="a" * 40,
    )
    relative = response_relative_path(response.request_id)
    corrupt_bytes = b"{corrupt response bytes"
    (store.path / relative).write_bytes(corrupt_bytes)
    assert load_verified_response(store=store, model_input=model_input) is None
    write_generation_response(
        store=store,
        model_input=model_input,
        result=result,
        started_at=started,
        completed_at=started,
        harness_git_commit="a" * 40,
    )
    retained = list(
        (store.path / Path(relative).parent / "quarantine").glob("*/response.json.invalid")
    )
    assert len(retained) == 1
    assert retained[0].read_bytes() == corrupt_bytes
    assert load_verified_response(store=store, model_input=model_input) is not None


def test_response_writer_rejects_non_utf8_raw_bytes(tmp_path: Path) -> None:
    model_input, result = _request_and_result()
    store = RunArtifactStore(tmp_path, "artifact-run")
    store.initialize()
    now = datetime(2026, 7, 25, tzinfo=UTC)
    with pytest.raises(ResponseArtifactError, match="not valid JSON"):
        write_generation_response(
            store=store,
            model_input=model_input,
            result=result.model_copy(update={"raw_response": b"\xff\xfe"}),
            started_at=now,
            completed_at=now,
            harness_git_commit="a" * 40,
        )


def test_writer_never_replaces_a_different_verified_terminal(tmp_path: Path) -> None:
    model_input, result = _request_and_result()
    store = RunArtifactStore(tmp_path, "artifact-run")
    store.initialize()
    started = datetime(2026, 7, 25, tzinfo=UTC)
    write_generation_response(
        store=store,
        model_input=model_input,
        result=result,
        started_at=started,
        completed_at=started,
        harness_git_commit="a" * 40,
    )
    with pytest.raises(TerminalArtifactConflictError):
        write_generation_response(
            store=store,
            model_input=model_input,
            result=result,
            started_at=started,
            completed_at=started + timedelta(seconds=1),
            harness_git_commit="a" * 40,
        )
