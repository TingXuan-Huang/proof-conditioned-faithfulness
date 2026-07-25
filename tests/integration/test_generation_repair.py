from __future__ import annotations

import json
from pathlib import Path

import pytest

from proof_faithfulness.artifacts import RunArtifactStore
from proof_faithfulness.generation.cli import ManifestMockAdapter
from proof_faithfulness.generation.config import PlanningModel, load_condition_matrix
from proof_faithfulness.generation.planning import (
    PlannedGeneration,
    PromptTheorem,
    build_generation_plan,
)
from proof_faithfulness.generation.prompts import PromptRepository
from proof_faithfulness.generation.repair import (
    RepairTrackError,
    RepairTrackRunner,
)
from proof_faithfulness.generation.run import GenerationHarness
from proof_faithfulness.lean import CheckOutcome
from proof_faithfulness.models import AdapterResult, ModelCapabilities, ModelInput
from proof_faithfulness.models.config import DecodingConfig, MockAdapterConfig
from proof_faithfulness.schema import LeanCheckResult

PROJECT_ROOT = Path(__file__).parents[2]
CONDITIONS = PROJECT_ROOT / "configs" / "experiment" / "conditions.yaml"
PROMPTS = PROJECT_ROOT / "prompts"


class QueueAdapter:
    def __init__(self, model: PlanningModel, responses: list[str]) -> None:
        self._adapter = ManifestMockAdapter(model)
        self._responses = responses
        self.calls = 0

    @property
    def name(self) -> str:
        return self._adapter.name

    @property
    def capabilities(self) -> ModelCapabilities:
        return self._adapter.capabilities

    def generate(self, model_input: ModelInput) -> AdapterResult:
        base = self._adapter.generate(model_input)
        response = self._responses[self.calls]
        self.calls += 1
        raw = (
            json.dumps(
                {
                    "finish_reason": "stop",
                    "id": f"repair-{self.calls}",
                    "text": response,
                },
                ensure_ascii=True,
                sort_keys=True,
            ).encode("utf-8")
            + b"\n"
        )
        return base.model_copy(
            update={
                "text": response,
                "raw_response": raw,
                "provider_request_id": f"repair-{self.calls}",
            }
        )


class NoRepairAdapter(QueueAdapter):
    @property
    def capabilities(self) -> ModelCapabilities:
        return self._adapter.capabilities.model_copy(update={"repair": False})


def _fixture(tmp_path: Path) -> tuple[RunArtifactStore, PlannedGeneration, PlanningModel]:
    capabilities = ModelCapabilities(
        proof_conditioning=True,
        deterministic_seed=True,
        local_inference=True,
        repair=True,
    )
    model = PlanningModel(
        backend_config=MockAdapterConfig(
            model_key="repair_mock",
            model_id="repair-mock",
            model_revision="mock-v1",
            response_text="bad-0",
            capabilities=capabilities,
        ),
        mock_chat_template="mock_chat_v1.txt",
        mock_decoding=DecodingConfig(
            temperature=0.2,
            top_p=1,
            max_tokens=1024,
            seed_base=7,
        ),
        mock_max_input_tokens=2048,
    )
    theorem = PromptTheorem.from_text(
        theorem_id="repair-fixture",
        split="pilot",
        imports=("Mathlib",),
        lean_statement="example : True := by",
        proof_a="Close the goal.",
        proof_b="Construct True.",
        paraphrase_a="Use trivial.",
        paraphrase_b="Use the constructor.",
    )
    original = build_generation_plan(
        theorems=(theorem,),
        models=(model,),
        matrix=load_condition_matrix(CONDITIONS),
        tier=1,
        prompt_repository=PromptRepository(PROMPTS),
    ).requests[0]
    store = RunArtifactStore(tmp_path / "outputs", "repair-parent")
    GenerationHarness(
        store=store,
        requests=(original,),
        adapters={model.key: ManifestMockAdapter(model)},
        harness_git_commit="a" * 40,
    ).run()
    return store, original, model


def _outcome(
    model_input: ModelInput,
    *,
    success: bool,
    diagnostic: str = "",
    request_id: str | None = None,
) -> CheckOutcome:
    return CheckOutcome(
        result=LeanCheckResult(
            schema_version="1.0",
            request_id=request_id or model_input.request.request_id,
            statement_hash_matches=True,
            extraction_status="success",
            parser_status="success",
            elaboration_status="success" if success else "failed",
            exit_code=0 if success else 1,
            wall_time_seconds=0.01,
            axioms=(),
            prohibited_token_findings=(),
            failure_category="success" if success else "type_invalid",
        ),
        stdout="",
        stderr=diagnostic,
        assembled_source="example : True := by\n  trivial\n",
    )


def test_repair_track_runs_two_separate_children_with_exact_diagnostics(
    tmp_path: Path,
) -> None:
    store, original, model = _fixture(tmp_path)
    diagnostics = {
        "bad-0": "error: unknown tactic at line 3, column 7",
        "bad-1": "error: unsolved goals\ncase h => True",
    }
    adapter = QueueAdapter(model, ["bad-1", "good-2"])

    def checker(model_input: ModelInput, candidate: str) -> CheckOutcome:
        if candidate == "good-2":
            return _outcome(model_input, success=True)
        return _outcome(
            model_input,
            success=False,
            diagnostic=diagnostics[candidate],
        )

    result = RepairTrackRunner(
        parent_store=store,
        original=original,
        adapter=adapter,
        prompt_repository=PromptRepository(PROMPTS),
        checker=checker,
        harness_git_commit="a" * 40,
    ).run()

    assert result.final_success is True
    assert result.first_attempt_success is False
    assert adapter.calls == 2
    assert [round_result.success for round_result in result.repair_rounds] == [False, True]
    first_id, second_id = [item.child_run_id for item in result.repair_rounds]
    first = RunArtifactStore(store.outputs_root, first_id)
    second = RunArtifactStore(store.outputs_root, second_id)
    first_manifest = json.loads((first.path / "manifest.json").read_text(encoding="utf-8"))
    second_manifest = json.loads((second.path / "manifest.json").read_text(encoding="utf-8"))
    assert first_manifest["parent_run_id"] == store.run_id
    assert second_manifest["parent_run_id"] == first.run_id
    first_request = PlannedGeneration.model_validate_json(
        (first.path / "requests.jsonl").read_text(encoding="utf-8")
    )
    second_request = PlannedGeneration.model_validate_json(
        (second.path / "requests.jsonl").read_text(encoding="utf-8")
    )
    assert diagnostics["bad-0"] in first_request.model_input.messages[-1].content
    assert diagnostics["bad-1"] in second_request.model_input.messages[-1].content
    assert first.verified("repair-lineage.json")
    assert second.verified("repair-lineage.json")
    assert store.verified(f"lean/{original.model_input.request.request_id}/check.json")
    assert first.verified(f"lean/{first_request.model_input.request.request_id}/check.json")
    assert second.verified(f"lean/{second_request.model_input.request.request_id}/check.json")
    assert first.verified("repair-round.json")
    assert second.verified("repair-round.json")
    assert store.verified("repair-track.json")

    def checker_must_not_rerun(_model_input: ModelInput, _candidate: str) -> CheckOutcome:
        raise AssertionError("verified checker artifacts must be reused")

    resumed = RepairTrackRunner(
        parent_store=store,
        original=original,
        adapter=adapter,
        prompt_repository=PromptRepository(PROMPTS),
        checker=checker_must_not_rerun,
        harness_git_commit="a" * 40,
    ).run()
    assert resumed == result
    assert adapter.calls == 2


def test_repair_track_stops_after_two_failed_rounds(tmp_path: Path) -> None:
    store, original, model = _fixture(tmp_path)
    adapter = QueueAdapter(model, ["bad-1", "bad-2"])

    result = RepairTrackRunner(
        parent_store=store,
        original=original,
        adapter=adapter,
        prompt_repository=PromptRepository(PROMPTS),
        checker=lambda model_input, candidate: _outcome(
            model_input,
            success=False,
            diagnostic=f"compiler rejected exact candidate: {candidate}",
        ),
        harness_git_commit="a" * 40,
    ).run()

    assert result.final_success is False
    assert len(result.repair_rounds) == 2
    assert adapter.calls == 2


def test_repair_track_refuses_adapter_without_repair_capability(tmp_path: Path) -> None:
    store, original, model = _fixture(tmp_path)
    adapter = NoRepairAdapter(model, ["unused"])
    with pytest.raises(RepairTrackError, match="does not support"):
        RepairTrackRunner(
            parent_store=store,
            original=original,
            adapter=adapter,
            prompt_repository=PromptRepository(PROMPTS),
            checker=lambda model_input, _candidate: _outcome(
                model_input,
                success=False,
                diagnostic="error: fixture",
            ),
            harness_git_commit="a" * 40,
        ).run()
    assert adapter.calls == 0
    assert not any(store.outputs_root.glob("runs/*-repair-*-r1"))


def test_repair_track_rejects_checker_result_for_another_request(tmp_path: Path) -> None:
    store, original, model = _fixture(tmp_path)
    with pytest.raises(RepairTrackError, match="request_id"):
        RepairTrackRunner(
            parent_store=store,
            original=original,
            adapter=QueueAdapter(model, ["unused"]),
            prompt_repository=PromptRepository(PROMPTS),
            checker=lambda model_input, _candidate: _outcome(
                model_input,
                success=False,
                diagnostic="error: fixture",
                request_id="f" * 64,
            ),
            harness_git_commit="a" * 40,
        ).run()


def test_repair_track_refuses_failure_without_compiler_diagnostic(tmp_path: Path) -> None:
    store, original, model = _fixture(tmp_path)
    adapter = QueueAdapter(model, ["unused"])
    with pytest.raises(RepairTrackError, match="no compiler diagnostic"):
        RepairTrackRunner(
            parent_store=store,
            original=original,
            adapter=adapter,
            prompt_repository=PromptRepository(PROMPTS),
            checker=lambda model_input, _candidate: _outcome(
                model_input,
                success=False,
            ),
            harness_git_commit="a" * 40,
        ).run()
    assert adapter.calls == 0
