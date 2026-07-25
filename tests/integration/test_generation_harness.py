from __future__ import annotations

import json
import multiprocessing
import os
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import HttpUrl

from proof_faithfulness.artifacts import FrozenRunError, RunArtifactStore, sha256_bytes
from proof_faithfulness.generation.artifacts import (
    ResponseArtifactError,
    response_relative_path,
    write_generation_response,
)
from proof_faithfulness.generation.budget import (
    BudgetExceededError,
    BudgetGate,
    MissingApprovalError,
    PaidRequestPermit,
)
from proof_faithfulness.generation.cli import ManifestMockAdapter
from proof_faithfulness.generation.config import PlanningModel, load_condition_matrix
from proof_faithfulness.generation.planning import (
    PlannedGeneration,
    PromptTheorem,
    build_generation_plan,
    serialize_generation_requests,
)
from proof_faithfulness.generation.prompts import PromptRepository
from proof_faithfulness.generation.run import (
    AmbiguousPaidAttemptError,
    EventLog,
    GenerationHarness,
    PaidRetryDecision,
    RetryPolicy,
    RunStateError,
    WorkerLock,
    WorkerLockError,
)
from proof_faithfulness.models import (
    AdapterResult,
    ModelCapabilities,
    ModelInput,
)
from proof_faithfulness.models.base import AdapterResponseError, AdapterTransportError
from proof_faithfulness.models.config import (
    DecodingConfig,
    MockAdapterConfig,
    ModelConfig,
    PricingConfig,
)
from proof_faithfulness.schema import TokenUsage

PROJECT_ROOT = Path(__file__).parents[2]
CONDITIONS = PROJECT_ROOT / "configs" / "experiment" / "conditions.yaml"
PROMPTS = PROJECT_ROOT / "prompts"


class CountingAdapter:
    def __init__(self, model: PlanningModel) -> None:
        self._adapter = ManifestMockAdapter(model)
        self.request_ids: list[str] = []

    @property
    def name(self) -> str:
        return self._adapter.name

    @property
    def capabilities(self) -> ModelCapabilities:
        return self._adapter.capabilities

    def generate(self, model_input: ModelInput) -> AdapterResult:
        self.request_ids.append(model_input.request.request_id)
        return self._adapter.generate(model_input)


class RetryingAdapter(CountingAdapter):
    def __init__(self, model: PlanningModel, failures: int) -> None:
        super().__init__(model)
        self._failures = failures

    def generate(self, model_input: ModelInput) -> AdapterResult:
        self.request_ids.append(model_input.request.request_id)
        if len(self.request_ids) <= self._failures:
            raise AdapterTransportError("fixture transport failure")
        return self._adapter.generate(model_input)


class PaidFixtureAdapter:
    def __init__(self, model: PlanningModel, *, failures: int = 0) -> None:
        self._model = model
        self._failures = failures
        self.request_ids: list[str] = []
        self.permits: list[PaidRequestPermit] = []

    def generate_paid(
        self,
        model_input: ModelInput,
        permit: PaidRequestPermit,
    ) -> AdapterResult:
        self.request_ids.append(model_input.request.request_id)
        self.permits.append(permit)
        if len(self.request_ids) <= self._failures:
            raise AdapterTransportError("fixture paid transport failure")
        assert model_input.request.backend_config_hash == self._model.backend_config_hash
        response = {
            "finish_reason": "stop",
            "id": f"paid-{model_input.request.request_id[:16]}",
            "text": "by\n  trivial",
        }
        return AdapterResult(
            request_id=model_input.request.request_id,
            text=response["text"],
            raw_response=(
                json.dumps(response, ensure_ascii=True, sort_keys=True).encode("utf-8") + b"\n"
            ),
            provider_request_id=response["id"],
            token_usage=TokenUsage(input_tokens=1, output_tokens=1),
            usd_cost=Decimal("0.1"),
            finish_reason="stop",
        )


class BlockingSecondAdapter(CountingAdapter):
    def __init__(self, model: PlanningModel, marker: Path) -> None:
        super().__init__(model)
        self._marker = marker

    def generate(self, model_input: ModelInput) -> AdapterResult:
        self.request_ids.append(model_input.request.request_id)
        if len(self.request_ids) == 2:
            self._marker.write_text("second request entered\n", encoding="utf-8")
            time.sleep(60)
        return self._adapter.generate(model_input)


class SignallingAdapter(CountingAdapter):
    def generate(self, model_input: ModelInput) -> AdapterResult:
        result = super().generate(model_input)
        os.kill(os.getpid(), signal.SIGUSR1)
        return result


class SignallingTransportAdapter(CountingAdapter):
    def generate(self, model_input: ModelInput) -> AdapterResult:
        self.request_ids.append(model_input.request.request_id)
        os.kill(os.getpid(), signal.SIGUSR1)
        raise AdapterTransportError("fixture transport failure after signal")


class InvalidResponseAdapter(CountingAdapter):
    def generate(self, model_input: ModelInput) -> AdapterResult:
        result = super().generate(model_input)
        return result.model_copy(update={"raw_response": b"\xffexact-invalid-provider-bytes"})


class ProviderErrorAdapter(CountingAdapter):
    def generate(self, model_input: ModelInput) -> AdapterResult:
        self.request_ids.append(model_input.request.request_id)
        raise AdapterResponseError(
            "provider response failed validation",
            raw_response=b'{"error":"exact provider body"}\n',
            provider_request_id="provider-error-123",
        )


def _fixture_requests(
    *,
    count: int = 3,
    paid: bool = False,
    reservation: Decimal = Decimal("0.5"),
) -> tuple[tuple[PlannedGeneration, ...], PlanningModel]:
    capabilities = ModelCapabilities(
        proof_conditioning=True,
        deterministic_seed=True,
        local_inference=True,
        cost_reporting=True,
    )
    decoding = DecodingConfig(
        temperature=0.2,
        top_p=1,
        max_tokens=8192,
        seed_base=20260724,
    )
    if paid:
        model = PlanningModel(
            backend_config=ModelConfig(
                key="deterministic_paid",
                category="frontier_api",
                provider="openai_compat_api",
                model_id="deterministic-paid",
                revision="fixture-v1",
                base_url=HttpUrl("https://api.example.test/v1"),
                api_key_env="FRONTIER_API_KEY",
                chat_template="mock_chat_v1",
                decoding=decoding,
                concurrency=1,
                pricing_usd_per_mtok=PricingConfig(
                    input=reservation * Decimal(1_000_000),
                    output=Decimal(0),
                ),
                pipeline_commit=None,
                context_window=8193,
            )
        )
    else:
        model = PlanningModel(
            backend_config=MockAdapterConfig(
                model_key="deterministic_mock",
                model_id="deterministic-mock",
                model_revision="mock-v1",
                capabilities=capabilities,
            ),
            mock_chat_template="mock_chat_v1.txt",
            mock_decoding=decoding,
            mock_max_input_tokens=16384,
        )
    theorem = PromptTheorem.from_text(
        theorem_id="harness-fixture",
        split="pilot",
        imports=("Mathlib",),
        lean_statement="example : True := by",
        proof_a="Truth is immediate.",
        proof_b="Construct the unique inhabitant of True.",
        paraphrase_a="Close the goal directly.",
        paraphrase_b="Use the constructor.",
    )
    original = build_generation_plan(
        theorems=(theorem,),
        models=(model,),
        matrix=load_condition_matrix(CONDITIONS),
        tier=1,
        prompt_repository=PromptRepository(PROMPTS),
    ).requests[:count]
    return original, model


def _write_approval(
    root: Path,
    *,
    store: RunArtifactStore,
    requests: tuple[PlannedGeneration, ...],
    max_usd: Decimal,
) -> Path:
    content = serialize_generation_requests(requests)
    store.initialize()
    if not store.verified("requests.jsonl"):
        store.write_bytes("requests.jsonl", content)
    elif (store.path / "requests.jsonl").read_bytes() != content:
        raise AssertionError("Fixture request manifest changed")
    approvals = root / "approvals"
    approvals.mkdir(exist_ok=True)
    path = approvals / "pilot.json"
    path.write_text(
        json.dumps(
            {
                "scope": "pilot-tier1",
                "run_ids": [store.run_id],
                "requests_sha256": sha256_bytes(content),
                "request_count": len(requests),
                "max_usd": str(max_usd),
                "approved_by": "Fixture Human",
                "date": "2026-07-25",
                "note": "Integration-test authorization only.",
            }
        ),
        encoding="utf-8",
    )
    return path


def _budget_gate(root: Path, store: RunArtifactStore) -> BudgetGate:
    return BudgetGate(
        store=store,
        approvals_root=root / "approvals",
        scope="pilot-tier1",
    )


def test_mock_run_writes_complete_directory_and_rerun_is_verified_noop(
    tmp_path: Path,
) -> None:
    requests, model = _fixture_requests()
    adapter = CountingAdapter(model)
    store = RunArtifactStore(tmp_path / "outputs", "mock-e2e")
    harness = GenerationHarness(
        store=store,
        requests=requests,
        adapters={model.key: adapter},
        harness_git_commit="a" * 40,
    )
    first = harness.run()
    second = harness.run()
    assert first.model_dump() == {
        "processed": 3,
        "skipped": 0,
        "retries": 0,
        "state": "complete",
    }
    assert second.processed == 0
    assert second.skipped == 3
    assert len(adapter.request_ids) == 3
    assert store.verified("state.json")
    assert store.verified("requests.jsonl")
    assert (store.path / "events.jsonl").is_file()
    assert len(list((store.path / "responses").glob("*/response.json"))) == 3


def test_resume_refuses_to_reissue_after_a_corrupt_success(tmp_path: Path) -> None:
    requests, model = _fixture_requests()
    adapter = CountingAdapter(model)
    store = RunArtifactStore(tmp_path / "outputs", "corrupt-resume")
    harness = GenerationHarness(
        store=store,
        requests=requests,
        adapters={model.key: adapter},
        harness_git_commit="a" * 40,
    )
    harness.run()
    corrupt = store.path / response_relative_path(requests[0].model_input.request.request_id)
    corrupt.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ResponseArtifactError, match="Prior provider response"):
        harness.run()
    assert len(adapter.request_ids) == 3


def test_transport_retries_reuse_identical_request_id(tmp_path: Path) -> None:
    requests, model = _fixture_requests(count=1)
    adapter = RetryingAdapter(model, failures=2)
    result = GenerationHarness(
        store=RunArtifactStore(tmp_path / "outputs", "retry-run"),
        requests=requests,
        adapters={model.key: adapter},
        retry_policy=RetryPolicy(
            max_attempts=3,
            base_delay_s=0,
            max_delay_s=0,
            jitter_fraction=0,
        ),
        sleep=lambda _: None,
        harness_git_commit="a" * 40,
    ).run()
    assert result.retries == 2
    assert len(set(adapter.request_ids)) == 1


@pytest.mark.parametrize("adapter_type", [InvalidResponseAdapter, ProviderErrorAdapter])
def test_invalid_provider_response_is_retained_and_never_retried(
    tmp_path: Path,
    adapter_type: type[CountingAdapter],
) -> None:
    requests, model = _fixture_requests(count=1)
    adapter = adapter_type(model)
    store = RunArtifactStore(tmp_path / "outputs", "invalid-provider-response")
    with pytest.raises((AdapterResponseError, ResponseArtifactError)):
        GenerationHarness(
            store=store,
            requests=requests,
            adapters={model.key: adapter},
            harness_git_commit="a" * 40,
        ).run()
    request_id = requests[0].model_input.request.request_id
    failure_root = store.path / "responses" / request_id / "failures" / "attempt-0001"
    assert (failure_root / "raw-response.bin").read_bytes() in {
        b"\xffexact-invalid-provider-bytes",
        b'{"error":"exact provider body"}\n',
    }
    assert store.verified(f"responses/{request_id}/failures/attempt-0001/raw-response.bin")
    with pytest.raises(ResponseArtifactError, match="Prior provider response"):
        GenerationHarness(
            store=store,
            requests=requests,
            adapters={model.key: adapter},
            harness_git_commit="a" * 40,
        ).run()
    assert len(adapter.request_ids) == 1


def test_paid_request_without_approval_refuses_before_adapter_call(tmp_path: Path) -> None:
    requests, model = _fixture_requests(count=1, paid=True)
    adapter = PaidFixtureAdapter(model)
    (tmp_path / "approvals").mkdir()
    store = RunArtifactStore(tmp_path / "outputs", "paid-refusal")
    with pytest.raises(MissingApprovalError):
        GenerationHarness(
            store=store,
            requests=requests,
            adapters={model.key: adapter},
            budget_gate=_budget_gate(tmp_path, store),
            harness_git_commit="a" * 40,
        ).run()
    assert adapter.request_ids == []
    state = json.loads((store.path / "state.json").read_text(encoding="utf-8"))
    assert state["state"] == "failed"


def test_paid_run_resumes_after_approval_is_added(tmp_path: Path) -> None:
    run_id = "paid-late-approval"
    requests, model = _fixture_requests(count=1, paid=True)
    adapter = PaidFixtureAdapter(model)
    (tmp_path / "approvals").mkdir()
    store = RunArtifactStore(tmp_path / "outputs", run_id)
    harness = GenerationHarness(
        store=store,
        requests=requests,
        adapters={model.key: adapter},
        budget_gate=_budget_gate(tmp_path, store),
        harness_git_commit="a" * 40,
    )
    with pytest.raises(MissingApprovalError):
        harness.run()
    _write_approval(
        tmp_path,
        store=store,
        requests=requests,
        max_usd=Decimal(1),
    )

    result = harness.run()
    assert result.state == "complete"
    assert len(adapter.request_ids) == 1


def test_ambiguous_paid_transport_failure_refuses_duplicate_attempt(tmp_path: Path) -> None:
    run_id = "paid-ambiguous"
    requests, model = _fixture_requests(count=1, paid=True)
    adapter = PaidFixtureAdapter(model, failures=1)
    store = RunArtifactStore(tmp_path / "outputs", run_id)
    _write_approval(
        tmp_path,
        store=store,
        requests=requests,
        max_usd=Decimal(1),
    )
    harness = GenerationHarness(
        store=store,
        requests=requests,
        adapters={model.key: adapter},
        budget_gate=_budget_gate(tmp_path, store),
        retry_policy=RetryPolicy(
            max_attempts=2,
            base_delay_s=0,
            max_delay_s=0,
            jitter_fraction=0,
        ),
        sleep=lambda _: None,
        harness_git_commit="a" * 40,
    )
    with pytest.raises(AmbiguousPaidAttemptError):
        harness.run()
    with pytest.raises(AmbiguousPaidAttemptError):
        harness.run()
    assert adapter.request_ids == [requests[0].model_input.request.request_id]
    attempts_path = (
        store.path
        / "responses"
        / requests[0].model_input.request.request_id
        / "transport-attempts.json"
    )
    attempts = json.loads(attempts_path.read_text(encoding="utf-8"))
    assert len(attempts["attempts"]) == 1
    assert attempts["attempts"][0]["retry_safe"] is False


def test_provider_classified_preacceptance_failure_allows_paid_retry(
    tmp_path: Path,
) -> None:
    run_id = "paid-safe-retry"
    requests, model = _fixture_requests(count=1, paid=True)
    adapter = PaidFixtureAdapter(model, failures=1)
    store = RunArtifactStore(tmp_path / "outputs", run_id)
    _write_approval(
        tmp_path,
        store=store,
        requests=requests,
        max_usd=Decimal(1),
    )
    result = GenerationHarness(
        store=store,
        requests=requests,
        adapters={model.key: adapter},
        budget_gate=_budget_gate(tmp_path, store),
        paid_retry_classifier=lambda _error, _item: PaidRetryDecision(
            safe_to_retry=True,
            reason="connection failed before request body transmission",
            retry_after_s=0,
        ),
        retry_policy=RetryPolicy(
            max_attempts=2,
            base_delay_s=0,
            max_delay_s=0,
            jitter_fraction=0,
        ),
        sleep=lambda _: None,
        harness_git_commit="a" * 40,
    ).run()
    assert result.retries == 1
    assert len(adapter.request_ids) == 2
    assert len(set(adapter.request_ids)) == 1


def test_paid_fast_path_settles_response_persisted_before_crash(tmp_path: Path) -> None:
    run_id = "paid-persisted-before-settle"
    requests, model = _fixture_requests(count=1, paid=True)
    adapter = PaidFixtureAdapter(model)
    store = RunArtifactStore(tmp_path / "outputs", run_id)
    _write_approval(
        tmp_path,
        store=store,
        requests=requests,
        max_usd=Decimal(1),
    )
    gate = _budget_gate(tmp_path, store)
    harness = GenerationHarness(
        store=store,
        requests=requests,
        adapters={model.key: adapter},
        budget_gate=gate,
        harness_git_commit="a" * 40,
    )
    harness.prepare()
    item = requests[0]
    gate.reserve(
        request_id=item.model_input.request.request_id,
        max_cost_usd=item.max_cost_usd,
    )
    raw = {
        "finish_reason": "stop",
        "id": f"paid-{item.model_input.request.request_id[:16]}",
        "text": "by\n  trivial",
    }
    billed_result = AdapterResult(
        request_id=item.model_input.request.request_id,
        text=raw["text"],
        raw_response=json.dumps(raw, sort_keys=True).encode("utf-8") + b"\n",
        provider_request_id=raw["id"],
        token_usage=TokenUsage(input_tokens=1, output_tokens=1),
        usd_cost=Decimal("0.1"),
        finish_reason="stop",
    )
    now = datetime.now(UTC)
    write_generation_response(
        store=store,
        model_input=item.model_input,
        result=billed_result,
        started_at=now,
        completed_at=now,
        harness_git_commit="a" * 40,
    )

    result = harness.run()
    assert result.processed == 0
    assert result.skipped == 1
    assert adapter.request_ids == []
    ledger = json.loads((store.path / "budget.json").read_text(encoding="utf-8"))
    assert ledger["entries"][0]["spent_usd"] == "0.1"
    events = [json.loads(line) for line in (store.path / "events.jsonl").read_text().splitlines()]
    ends = [event for event in events if event["event"] == "request_end"]
    assert len(ends) == 1
    assert ends[0]["detail"]["recovered"] is True


def test_run_budget_ceiling_halts_before_the_next_paid_call(tmp_path: Path) -> None:
    run_id = "paid-halt"
    requests, model = _fixture_requests(
        count=2,
        paid=True,
        reservation=Decimal("0.6"),
    )
    adapter = PaidFixtureAdapter(model)
    store = RunArtifactStore(tmp_path / "outputs", run_id)
    _write_approval(
        tmp_path,
        store=store,
        requests=requests,
        max_usd=Decimal("0.65"),
    )
    with pytest.raises(BudgetExceededError):
        GenerationHarness(
            store=store,
            requests=requests,
            adapters={model.key: adapter},
            budget_gate=_budget_gate(tmp_path, store),
            harness_git_commit="a" * 40,
        ).run()
    assert len(adapter.request_ids) == 1
    events = [json.loads(line) for line in (store.path / "events.jsonl").read_text().splitlines()]
    assert sum(event["event"] == "budget_halt" for event in events) == 1


def _run_until_blocked(outputs_root: str, marker_path: str) -> None:
    requests, model = _fixture_requests(count=2)
    adapter = BlockingSecondAdapter(model, Path(marker_path))
    GenerationHarness(
        store=RunArtifactStore(Path(outputs_root), "killed-run"),
        requests=requests,
        adapters={model.key: adapter},
        harness_git_commit="a" * 40,
    ).run()


def test_process_kill_then_resume_completes_without_duplicate_terminals(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    marker = tmp_path / "second-started"
    process = multiprocessing.get_context("fork").Process(
        target=_run_until_blocked,
        args=(str(outputs_root), str(marker)),
    )
    process.start()
    deadline = time.monotonic() + 10
    while not marker.exists() and time.monotonic() < deadline:
        time.sleep(0.02)
    assert marker.exists(), "child never reached its second request"
    process.kill()
    process.join(timeout=5)
    assert not process.is_alive()

    requests, model = _fixture_requests(count=2)
    adapter = CountingAdapter(model)
    store = RunArtifactStore(outputs_root, "killed-run")
    result = GenerationHarness(
        store=store,
        requests=requests,
        adapters={model.key: adapter},
        now=lambda: datetime.now(UTC) + timedelta(minutes=11),
        harness_git_commit="a" * 40,
    ).run()
    assert result.processed == 1
    assert result.skipped == 1
    assert adapter.request_ids == [requests[1].model_input.request.request_id]
    events = [json.loads(line) for line in (store.path / "events.jsonl").read_text().splitlines()]
    terminal_ids = [event["request_id"] for event in events if event["event"] == "request_end"]
    assert len(terminal_ids) == len(set(terminal_ids)) == 2
    assert any(event["event"] == "lock_broken" for event in events)


def test_remote_stale_lock_uses_scheduler_liveness_before_breaking(tmp_path: Path) -> None:
    requests, model = _fixture_requests(count=1)
    store = RunArtifactStore(tmp_path / "outputs", "remote-lock")
    stale_now = datetime(2026, 7, 25, 12, tzinfo=UTC)
    harness = GenerationHarness(
        store=store,
        requests=requests,
        adapters={model.key: CountingAdapter(model)},
        now=lambda: stale_now,
        harness_git_commit="a" * 40,
    )
    harness.prepare()
    lock = store.path / "LOCK"
    lock.write_text(
        json.dumps(
            {
                "hostname": "remote-compute-node",
                "pid": 1234,
                "slurm_job_id": "98765",
                "heartbeat_at": (stale_now - timedelta(minutes=11)).isoformat(),
                "token": "remote-owner",
            }
        ),
        encoding="ascii",
    )

    with pytest.raises(WorkerLockError, match="live worker"):
        GenerationHarness(
            store=store,
            requests=requests,
            adapters={model.key: CountingAdapter(model)},
            job_is_active=lambda job_id: job_id == "98765",
            now=lambda: stale_now,
            harness_git_commit="a" * 40,
        ).run()

    adapter = CountingAdapter(model)
    result = GenerationHarness(
        store=store,
        requests=requests,
        adapters={model.key: adapter},
        job_is_active=lambda _job_id: False,
        now=lambda: stale_now,
        harness_git_commit="a" * 40,
    ).run()
    assert result.state == "complete"
    assert len(adapter.request_ids) == 1


def test_concurrent_stale_worker_lock_breakers_leave_one_owner(tmp_path: Path) -> None:
    run_path = tmp_path / "run"
    run_path.mkdir()
    lock_path = run_path / "LOCK"
    now = datetime(2026, 7, 25, 12, tzinfo=UTC)
    lock_path.write_text(
        json.dumps(
            {
                "hostname": "dead-remote-node",
                "pid": 9876,
                "slurm_job_id": "dead-job",
                "heartbeat_at": (now - timedelta(minutes=11)).isoformat(),
                "token": "dead",
            }
        ),
        encoding="ascii",
    )
    barrier = threading.Barrier(2)
    acquired = threading.Event()
    rejected = threading.Event()
    release = threading.Event()

    def claim() -> bool:
        worker_lock = WorkerLock(
            path=lock_path,
            events=EventLog(run_path / "events.jsonl"),
            job_is_active=lambda _job_id: False,
            now=lambda: now,
        )
        barrier.wait()
        try:
            worker_lock.acquire()
        except WorkerLockError:
            rejected.set()
            return False
        acquired.set()
        release.wait(timeout=5)
        worker_lock.release()
        return True

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(claim) for _ in range(2)]
        assert acquired.wait(timeout=5)
        assert rejected.wait(timeout=5)
        release.set()
        outcomes = [future.result(timeout=5) for future in futures]
    assert sorted(outcomes) == [False, True]
    assert not lock_path.exists()


def test_final_request_sigusr1_records_complete_not_cancelled(tmp_path: Path) -> None:
    requests, model = _fixture_requests(count=1)
    store = RunArtifactStore(tmp_path / "outputs", "signal-final")
    result = GenerationHarness(
        store=store,
        requests=requests,
        adapters={model.key: SignallingAdapter(model)},
        harness_git_commit="a" * 40,
    ).run_with_signal_handlers()
    assert result.state == "complete"
    state = json.loads((store.path / "state.json").read_text(encoding="utf-8"))
    assert state["state"] == "complete"
    assert "cancelled" not in {entry["state"] for entry in state["history"]}


def test_stop_requested_before_run_dispatches_no_request(tmp_path: Path) -> None:
    requests, model = _fixture_requests(count=1)
    adapter = CountingAdapter(model)
    harness = GenerationHarness(
        store=RunArtifactStore(tmp_path / "outputs", "signal-before-request"),
        requests=requests,
        adapters={model.key: adapter},
        harness_git_commit="a" * 40,
    )
    harness.request_stop()
    result = harness.run()
    assert result.state == "cancelled"
    assert result.processed == 0
    assert adapter.request_ids == []


def test_sigusr1_after_transport_error_prevents_retry(tmp_path: Path) -> None:
    requests, model = _fixture_requests(count=1)
    adapter = SignallingTransportAdapter(model)
    result = GenerationHarness(
        store=RunArtifactStore(tmp_path / "outputs", "signal-before-retry"),
        requests=requests,
        adapters={model.key: adapter},
        retry_policy=RetryPolicy(
            max_attempts=3,
            base_delay_s=0,
            max_delay_s=0,
            jitter_fraction=0,
        ),
        sleep=lambda _: None,
        harness_git_commit="a" * 40,
    ).run_with_signal_handlers()
    assert result.state == "cancelled"
    assert adapter.request_ids == [requests[0].model_input.request.request_id]


def test_cancelled_run_resumes_to_completion(tmp_path: Path) -> None:
    requests, model = _fixture_requests(count=2)
    store = RunArtifactStore(tmp_path / "outputs", "signal-resume")
    first = GenerationHarness(
        store=store,
        requests=requests,
        adapters={model.key: SignallingAdapter(model)},
        harness_git_commit="a" * 40,
    ).run_with_signal_handlers()
    assert first.state == "cancelled"
    assert first.processed == 1

    adapter = CountingAdapter(model)
    resumed = GenerationHarness(
        store=store,
        requests=requests,
        adapters={model.key: adapter},
        harness_git_commit="a" * 40,
    ).run()
    assert resumed.state == "complete"
    assert resumed.processed == 1
    assert resumed.skipped == 1


def test_frozen_run_refuses_before_event_lock_or_plan_writes(tmp_path: Path) -> None:
    requests, model = _fixture_requests(count=1)
    store = RunArtifactStore(tmp_path / "outputs", "frozen-run")
    store.initialize()
    store.freeze()
    with pytest.raises(FrozenRunError):
        GenerationHarness(
            store=store,
            requests=requests,
            adapters={model.key: CountingAdapter(model)},
            harness_git_commit="a" * 40,
        ).run()
    assert not (store.path / "events.jsonl").exists()
    assert not (store.path / "LOCK").exists()
    assert not (store.path / "requests.jsonl").exists()
    assert not (store.path / "state.json").exists()


def test_slurm_job_id_is_recorded_at_top_level_and_in_history(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SLURM_JOB_ID", "456789")
    requests, model = _fixture_requests(count=1)
    store = RunArtifactStore(tmp_path / "outputs", "slurm-state")
    GenerationHarness(
        store=store,
        requests=requests,
        adapters={model.key: CountingAdapter(model)},
        harness_git_commit="a" * 40,
    ).run()
    state = json.loads((store.path / "state.json").read_text(encoding="utf-8"))
    assert state["slurm_job_id"] == "456789"
    assert {entry["slurm_job_id"] for entry in state["history"]} == {"456789"}


def test_resume_refuses_a_different_harness_commit(tmp_path: Path) -> None:
    requests, model = _fixture_requests(count=1)
    store = RunArtifactStore(tmp_path / "outputs", "producer-mismatch")
    GenerationHarness(
        store=store,
        requests=requests,
        adapters={model.key: CountingAdapter(model)},
        harness_git_commit="a" * 40,
    ).run()
    assert store.verified("environment.json")
    with pytest.raises(RunStateError, match="Producer environment changed"):
        GenerationHarness(
            store=store,
            requests=requests,
            adapters={model.key: CountingAdapter(model)},
            harness_git_commit="b" * 40,
        ).run()
