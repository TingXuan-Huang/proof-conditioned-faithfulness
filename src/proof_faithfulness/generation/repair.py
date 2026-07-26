"""Two-round compiler-feedback repair track with explicit run lineage."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable

from pydantic import BaseModel, ConfigDict, Field

from proof_faithfulness.artifacts import RunArtifactStore
from proof_faithfulness.generation.artifacts import load_verified_response
from proof_faithfulness.generation.budget import BudgetGate
from proof_faithfulness.generation.planning import PlannedGeneration, build_repair_input
from proof_faithfulness.generation.prompts import PromptRepository
from proof_faithfulness.generation.run import GenerationHarness, PaidModelAdapter
from proof_faithfulness.lean import FAILURE_SUCCESS, CheckOutcome
from proof_faithfulness.lean.artifacts import (
    LeanArtifactError,
    check_and_persist_candidate,
    load_check_result,
)
from proof_faithfulness.models import ModelAdapter, ModelCapabilities, ModelInput
from proof_faithfulness.schema import Hash, NonEmptyString


class RepairTrackError(RuntimeError):
    """Raised when a repair track cannot preserve its safety contract."""


class RepairContract(BaseModel):
    """Immutable base for repair-track inputs and results."""

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", frozen=True)


class RepairRoundResult(RepairContract):
    """One separately persisted compiler-feedback repair round."""

    round_index: int = Field(ge=1, le=2)
    child_run_id: NonEmptyString
    request_id: Hash
    parent_request_id: Hash
    diagnostic_sha256: Hash
    success: bool
    failure_category: NonEmptyString


class RepairTrackResult(RepairContract):
    """Result of checking the first attempt and at most two repairs."""

    root_request_id: Hash
    first_attempt_success: bool
    initial_failure_category: NonEmptyString
    repair_rounds: tuple[RepairRoundResult, ...]
    final_success: bool
    final_failure_category: NonEmptyString


class RepairTrackRunner:
    """Executes at most two repairs in child runs linked to every prior version."""

    def __init__(
        self,
        *,
        parent_store: RunArtifactStore,
        original: PlannedGeneration,
        adapter: ModelAdapter | PaidModelAdapter,
        prompt_repository: PromptRepository,
        checker: Callable[[ModelInput, str], CheckOutcome],
        budget_gate_factory: Callable[[RunArtifactStore], BudgetGate] | None = None,
        harness_git_commit: str | None = None,
    ) -> None:
        self._parent_store = parent_store
        self._original = original
        self._adapter = adapter
        self._prompt_repository = prompt_repository
        self._checker = checker
        self._budget_gate_factory = budget_gate_factory
        self._harness_git_commit = harness_git_commit

    def run(self) -> RepairTrackResult:
        """Checks the first attempt, then executes repair rounds one and two."""
        initial = load_verified_response(
            store=self._parent_store,
            model_input=self._original.model_input,
        )
        if initial is None:
            raise RepairTrackError("Repair requires a verified first-attempt response")
        outcome = self._check_and_persist(
            store=self._parent_store,
            model_input=self._original.model_input,
            candidate=initial.text,
        )
        root_request_id = initial.request_id
        if _check_succeeded(outcome):
            result = RepairTrackResult(
                root_request_id=root_request_id,
                first_attempt_success=True,
                initial_failure_category=outcome.result.failure_category,
                repair_rounds=(),
                final_success=True,
                final_failure_category=outcome.result.failure_category,
            )
            _write_verified_identity(
                self._parent_store,
                "repair-track.json",
                result.model_dump(mode="json"),
            )
            return result
        self._require_repair_capability()
        if self._original.paid and self._budget_gate_factory is None:
            raise RepairTrackError("Paid repair requires a per-child BudgetGate factory")

        previous_store = self._parent_store
        previous_input = self._original.model_input
        previous_text = initial.text
        rounds: list[RepairRoundResult] = []
        for round_index in (1, 2):
            diagnostic = _exact_diagnostic(outcome)
            if not diagnostic:
                raise RepairTrackError(
                    "Failed checker result has no compiler diagnostic; refusing blind repair"
                )
            repair_input = build_repair_input(
                original=previous_input,
                previous_candidate=previous_text,
                compiler_diagnostic=diagnostic,
                round_index=round_index,
                prompt_repository=self._prompt_repository,
            )
            child_run_id = (
                f"{self._parent_store.run_id}-repair-{root_request_id[:8]}-r{round_index}"
            )
            child_store = previous_store.create_child(
                child_run_id,
                reason=f"compiler-feedback repair round {round_index}",
            )
            lineage = {
                "schema_version": "1.0",
                "root_request_id": root_request_id,
                "parent_request_id": previous_input.request.request_id,
                "repair_request_id": repair_input.request.request_id,
                "round_index": round_index,
                "diagnostic_sha256": _sha256_text(diagnostic),
            }
            _write_verified_identity(child_store, "repair-lineage.json", lineage)
            planned = PlannedGeneration(
                model_input=repair_input,
                max_cost_usd=self._original.max_cost_usd,
                paid=self._original.paid,
                paid_idempotency_verified=self._original.paid_idempotency_verified,
            )
            budget_gate = None
            if self._budget_gate_factory is not None:
                budget_gate = self._budget_gate_factory(child_store)
            GenerationHarness(
                store=child_store,
                requests=(planned,),
                adapters={repair_input.request.model_key: self._adapter},
                budget_gate=budget_gate,
                harness_git_commit=self._harness_git_commit,
            ).run_with_signal_handlers()
            response = load_verified_response(store=child_store, model_input=repair_input)
            if response is None:
                raise RepairTrackError("Repair round did not produce a verified response")
            outcome = self._check_and_persist(
                store=child_store,
                model_input=repair_input,
                candidate=response.text,
            )
            round_result = RepairRoundResult(
                round_index=round_index,
                child_run_id=child_run_id,
                request_id=response.request_id,
                parent_request_id=previous_input.request.request_id,
                diagnostic_sha256=_sha256_text(diagnostic),
                success=_check_succeeded(outcome),
                failure_category=outcome.result.failure_category,
            )
            rounds.append(round_result)
            _write_verified_identity(
                child_store,
                "repair-round.json",
                round_result.model_dump(mode="json"),
            )
            if _check_succeeded(outcome):
                break
            previous_store = child_store
            previous_input = repair_input
            previous_text = response.text
        result = RepairTrackResult(
            root_request_id=root_request_id,
            first_attempt_success=False,
            initial_failure_category=(
                load_check_result(self._parent_store, root_request_id).failure_category
            ),
            repair_rounds=tuple(rounds),
            final_success=_check_succeeded(outcome),
            final_failure_category=outcome.result.failure_category,
        )
        _write_verified_identity(
            self._parent_store,
            "repair-track.json",
            result.model_dump(mode="json"),
        )
        return result

    def _require_repair_capability(self) -> None:
        if "repair" not in self._original.model_input.request.capability_flags:
            raise RepairTrackError("Original request does not declare repair capability")
        capabilities = getattr(self._adapter, "capabilities", None)
        if not isinstance(capabilities, ModelCapabilities) or not capabilities.repair:
            raise RepairTrackError("Configured adapter does not support compiler-feedback repair")

    def _check_and_persist(
        self,
        *,
        store: RunArtifactStore,
        model_input: ModelInput,
        candidate: str,
    ) -> CheckOutcome:
        request_id = model_input.request.request_id
        try:
            return check_and_persist_candidate(
                store=store,
                request_id=request_id,
                candidate=candidate,
                checker=lambda value: self._checker(model_input, value),
            )
        except LeanArtifactError as error:
            raise RepairTrackError(str(error)) from error


def _write_verified_identity(
    store: RunArtifactStore,
    relative_path: str,
    value: dict[str, object],
) -> None:
    path = store.path / relative_path
    if path.exists():
        if not store.verified(relative_path):
            raise RepairTrackError(f"Repair lineage is unverified: {store.run_id}")
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RepairTrackError(f"Repair lineage is unreadable: {store.run_id}") from error
        if existing != value:
            raise RepairTrackError(f"Repair lineage changed: {store.run_id}")
        return
    store.write_json(relative_path, value)



def _check_succeeded(outcome: CheckOutcome) -> bool:
    return outcome.result.failure_category == FAILURE_SUCCESS


def _exact_diagnostic(outcome: CheckOutcome) -> str:
    return f"{outcome.stdout}{outcome.stderr}"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
