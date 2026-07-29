"""Offline adversarial tests for model and prover adapter boundaries."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

import httpx
import pytest
from pydantic import ValidationError

from proof_faithfulness.generation.budget import MissingApprovalError, PaidRequestPermit
from proof_faithfulness.ids import compute_request_id
from proof_faithfulness.models import (
    ChatMessage,
    MockAdapterConfig,
    ModelConfig,
    ModelInput,
    PipelineAdapterConfig,
    PricingConfig,
    build_adapter,
    compute_adapter_config_hash,
    compute_rendered_prompt_hash,
    load_adapter_config,
)
from proof_faithfulness.models.base import (
    AdapterConfigurationError,
    AdapterResponseError,
    AdapterTransportError,
)
from proof_faithfulness.models.openai_compat import (
    OpenAICompatibleAdapter,
    OpenAITransportError,
    PaidRequestBlockedError,
    compute_usd_cost,
)
from proof_faithfulness.models.pipeline import (
    JsonSubprocessAdapter,
    ProofBridgeAdapter,
    ProofFlowAdapter,
)
from proof_faithfulness.schema import GenerationRequest, SamplingOption, TokenUsage

PROJECT_ROOT = Path(__file__).parents[2]
PIPELINE_FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "fake_prover_pipeline.py"


def _model_config(
    *,
    key: str = "fixture_model",
    category: Literal["frontier_api", "open_weight", "prover", "pipeline"] = "open_weight",
    provider: Literal["vllm", "openai_compat_api", "proofbridge", "proofflow"] = "vllm",
    model_id: str = "fixture/model",
    revision: str | None = "revision-1",
    base_url: str | None = "http://127.0.0.1:8000/v1",
    api_key_env: str | None = None,
    pipeline_commit: str | None = None,
) -> ModelConfig:
    return ModelConfig.model_validate(
        {
            "key": key,
            "category": category,
            "provider": provider,
            "model_id": model_id,
            "revision": revision,
            "base_url": base_url,
            "api_key_env": api_key_env,
            "chat_template": "fixture_chat_v1",
            "decoding": {
                "temperature": 0.2,
                "top_p": 1.0,
                "max_tokens": 128,
                "seed_base": 7,
            },
            "concurrency": 1,
            "pricing_usd_per_mtok": {"input": 0.0, "output": 0.0},
            "pipeline_commit": pipeline_commit,
            "context_window": 4096,
            "dtype": "bfloat16" if provider == "vllm" else None,
        }
    )


def _pipeline_config(
    tmp_path: Path,
    adapter: Literal["proofbridge", "proofflow"],
    command: tuple[str, ...],
    *,
    commit: str | None = None,
    timeout_seconds: float = 10,
    max_response_bytes: int = 16 * 1024 * 1024,
    environment_names: tuple[str, ...] = (),
) -> PipelineAdapterConfig:
    checkout = tmp_path / "pipeline-checkout"
    checkout.mkdir()
    (checkout / "README.md").write_text("fixture pipeline\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=checkout, check=True)
    subprocess.run(["git", "add", "README.md"], cwd=checkout, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.test",
            "commit",
            "-q",
            "-m",
            "fixture",
        ],
        cwd=checkout,
        check=True,
    )
    actual_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=checkout, text=True
    ).strip()
    return PipelineAdapterConfig(
        model=_model_config(
            key=f"fixture_{adapter}",
            category="pipeline",
            provider=adapter,
            model_id=f"fixture/{adapter}",
            base_url=None,
            pipeline_commit=commit or actual_commit,
        ),
        command=command,
        workdir=checkout,
        scratch_dir=tmp_path / "scratch",
        timeout_seconds=timeout_seconds,
        max_response_bytes=max_response_bytes,
        environment_names=environment_names,
    )


def _model_input(
    *,
    adapter: str,
    provider: str,
    model_key: str,
    model_id: str,
    revision: str,
    backend_config_hash: str,
    temperature: float = 0.2,
    top_p: float = 1.0,
    max_tokens: int = 128,
    seed: int = 7,
    capability_flags: tuple[str, ...] = (),
    extra: tuple[dict[str, object], ...] = (),
    messages: tuple[ChatMessage, ...] | None = None,
) -> ModelInput:
    messages = messages or (
        ChatMessage(role="system", content="Return only Lean code."),
        ChatMessage(role="user", content="Prove `example : True`."),
    )
    sampling: dict[str, Any] = {
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "seed": seed,
        "extra": extra,
    }
    identity = {
        "schema_version": "1.0",
        "theorem_id": "smoke-true",
        "statement_hash": "a" * 64,
        "import_hash": "b" * 64,
        "condition": "theorem_only",
        "proof_hash": "c" * 64,
        "prompt_hash": "d" * 64,
        "rendered_prompt_hash": compute_rendered_prompt_hash(messages),
        "chat_template_hash": "e" * 64,
        "model_key": model_key,
        "model_id": model_id,
        "model_revision": revision,
        "backend_config_hash": backend_config_hash,
        "sampling": sampling,
        "sample_index": 0,
    }
    request = GenerationRequest.model_validate(
        {
            **identity,
            "proof_id": None,
            "prompt_name": "smoke",
            "prompt_version": "v1",
            "model_adapter": adapter,
            "provider": provider,
            "requested_seed": seed,
            "capability_flags": capability_flags,
            "sampling": sampling,
            "request_id": compute_request_id(**identity),
        }
    )
    return ModelInput(request=request, messages=messages)


def _input_for_model(config: ModelConfig, **overrides: object) -> ModelInput:
    values: dict[str, object] = {
        "adapter": config.adapter,
        "provider": config.provider,
        "model_key": config.key,
        "model_id": config.model_id,
        "revision": config.require_revision(),
        "backend_config_hash": compute_adapter_config_hash(config),
    }
    values.update(overrides)
    return _model_input(**values)  # type: ignore[arg-type]


def _input_for_pipeline(config: PipelineAdapterConfig) -> ModelInput:
    return _model_input(
        adapter=config.adapter,
        provider=config.provider,
        model_key=config.model_key,
        model_id=config.model_id,
        revision=config.model_revision,
        backend_config_hash=compute_adapter_config_hash(config),
    )


def _paid_permit(request_id: str) -> PaidRequestPermit:
    return PaidRequestPermit(
        run_id="paid-smoke",
        request_id=request_id,
        scope="smoke-tests",
        approval_path="approvals/smoke.json",
        approval_sha256="f" * 64,
        requests_sha256="e" * 64,
        request_count=1,
        inference_fingerprint="d" * 64,
        reserved_usd=Decimal("0.01"),
        issued_at=datetime.now(UTC),
    )


def test_mock_adapter_is_deterministic_and_protocol_compatible() -> None:
    config = MockAdapterConfig()
    model_input = _model_input(
        adapter="mock",
        provider="mock",
        model_key=config.model_key,
        model_id=config.model_id,
        revision=config.model_revision,
        backend_config_hash=compute_adapter_config_hash(config),
        capability_flags=config.capabilities.enabled_flags(),
    )
    adapter = build_adapter(config)
    assert adapter.generate(model_input) == adapter.generate(model_input)


def test_chat_message_preserves_response_affecting_whitespace() -> None:
    content = "\n  exact prompt  \n"
    message = ChatMessage(role="user", content=content)
    assert message.content == content


def test_model_input_rejects_prompt_hash_mismatch() -> None:
    config = MockAdapterConfig()
    model_input = _model_input(
        adapter="mock",
        provider="mock",
        model_key=config.model_key,
        model_id=config.model_id,
        revision=config.model_revision,
        backend_config_hash=compute_adapter_config_hash(config),
    )
    with pytest.raises(ValidationError, match="rendered_prompt_hash"):
        ModelInput(
            request=model_input.request,
            messages=(ChatMessage(role="user", content="changed"),),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [("model_key", "other_key"), ("model_id", "other/model"), ("revision", "other-rev")],
)
def test_adapter_rejects_request_identity_mismatch(field: str, value: str) -> None:
    config = MockAdapterConfig()
    values = {
        "adapter": "mock",
        "provider": "mock",
        "model_key": config.model_key,
        "model_id": config.model_id,
        "revision": config.model_revision,
        "backend_config_hash": compute_adapter_config_hash(config),
    }
    values[field] = value
    with pytest.raises(AdapterConfigurationError, match="identity does not match"):
        build_adapter(config).generate(_model_input(**values))  # type: ignore[arg-type]


def test_openai_adapter_sends_exact_payload() -> None:
    observed: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        observed["url"] = str(request.url)
        observed["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "id": "local-1",
                "choices": [{"message": {"content": "by trivial"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 4},
            },
        )

    config = _model_config()
    adapter = OpenAICompatibleAdapter(config, transport=httpx.MockTransport(handler))
    result = adapter.generate(
        _input_for_model(
            config,
            capability_flags=("local_inference",),
        )
    )
    assert observed["url"] == "http://127.0.0.1:8000/v1/chat/completions"
    assert observed["payload"] == {
        "model": "fixture/model",
        "messages": [
            {"role": "system", "content": "Return only Lean code."},
            {"role": "user", "content": "Prove `example : True`."},
        ],
        "temperature": 0.2,
        "top_p": 1.0,
        "max_tokens": 128,
        "seed": 7,
    }
    assert result.token_usage is not None
    assert result.token_usage.output_tokens == 4
    assert result.usd_cost == 0


def test_cost_calculation_matches_hand_computation() -> None:
    usage = TokenUsage(input_tokens=10, output_tokens=4)
    pricing = PricingConfig(input=Decimal(2), output=Decimal(4))
    assert compute_usd_cost(usage, pricing) == Decimal("0.000036")


def test_http_failure_is_normalized_without_retained_request() -> None:
    config = _model_config()
    adapter = OpenAICompatibleAdapter(
        config,
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                503,
                headers={"Retry-After": "2"},
                json={"id": "provider-503", "error": "busy"},
            )
        ),
    )
    with pytest.raises(OpenAITransportError, match="HTTP 503") as captured:
        adapter.generate(_input_for_model(config))
    assert captured.value.status_code == 503
    assert captured.value.retry_after_s == 2
    assert captured.value.provider_request_id == "provider-503"
    assert captured.value.raw_response is not None
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None


def test_permanent_http_error_retains_provider_body() -> None:
    config = _model_config()
    raw = b'{"id":"provider-400","error":"invalid"}'
    adapter = OpenAICompatibleAdapter(
        config,
        transport=httpx.MockTransport(lambda _: httpx.Response(400, content=raw)),
    )

    with pytest.raises(AdapterResponseError, match="HTTP 400") as captured:
        adapter.generate(_input_for_model(config))
    assert captured.value.raw_response == raw
    assert captured.value.provider_request_id == "provider-400"


@pytest.mark.parametrize("name", ["n", "best_of", "stream"])
def test_openai_adapter_rejects_cardinality_and_transport_overrides(name: str) -> None:
    config = _model_config()
    adapter = OpenAICompatibleAdapter(
        config,
        transport=httpx.MockTransport(lambda _: httpx.Response(200)),
    )
    with pytest.raises(AdapterResponseError, match="reserved keys"):
        adapter.generate(_input_for_model(config, extra=({"name": name, "value": 2},)))


def test_openai_adapter_sends_pinned_provider_sampling_option() -> None:
    base_config = _model_config()
    config = base_config.model_copy(
        update={
            "decoding": base_config.decoding.model_copy(
                update={"extra": (SamplingOption(name="top_k", value=20),)}
            )
        }
    )
    observed: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        observed.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "id": "local-extra",
                "choices": [
                    {"message": {"content": "by trivial"}, "finish_reason": "stop"}
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 4},
            },
        )

    adapter = OpenAICompatibleAdapter(config, transport=httpx.MockTransport(handler))
    result = adapter.generate(
        _input_for_model(config, extra=({"name": "top_k", "value": 20},))
    )

    assert result.text
    assert observed["top_k"] == 20


@pytest.mark.parametrize(
    ("field", "value"),
    [("temperature", 0.3), ("top_p", 0.9), ("max_tokens", 64), ("seed", 8)],
)
def test_openai_adapter_requires_exact_decoding_recipe(field: str, value: object) -> None:
    config = _model_config()
    adapter = OpenAICompatibleAdapter(
        config,
        transport=httpx.MockTransport(lambda _: pytest.fail("transport must not run")),
    )
    with pytest.raises(AdapterConfigurationError, match="pinned model recipe"):
        adapter.generate(_input_for_model(config, **{field: value}))


def test_openai_adapter_rejects_oversized_response() -> None:
    config = _model_config()
    adapter = OpenAICompatibleAdapter(
        config,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=b"123456789")),
        max_response_bytes=8,
    )
    with pytest.raises(AdapterResponseError, match="byte limit") as captured:
        adapter.generate(_input_for_model(config))
    assert captured.value.raw_response == b"12345678"
    assert captured.value.raw_truncated is True


def test_openai_adapter_rejects_multiple_choices() -> None:
    config = _model_config()
    body = {
        "choices": [
            {"message": {"content": "first"}},
            {"message": {"content": "second"}},
        ]
    }
    adapter = OpenAICompatibleAdapter(
        config,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body)),
    )
    with pytest.raises(AdapterResponseError, match="response schema") as captured:
        adapter.generate(_input_for_model(config))
    assert captured.value.raw_response is not None


def test_openai_adapter_requires_usage_on_success() -> None:
    config = _model_config()
    body = {"choices": [{"message": {"content": "by trivial"}}]}
    adapter = OpenAICompatibleAdapter(
        config,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body)),
    )
    with pytest.raises(AdapterResponseError, match="missing token usage") as captured:
        adapter.generate(_input_for_model(config))
    assert captured.value.raw_response is not None


def test_frontier_request_is_blocked_without_budget_permit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "never-retain-this-value"
    monkeypatch.setenv("TEST_PROVIDER_KEY", secret)
    config = _model_config(
        category="frontier_api",
        provider="openai_compat_api",
        base_url="https://example.test/v1",
        api_key_env="TEST_PROVIDER_KEY",
    )
    adapter = OpenAICompatibleAdapter(
        config,
        transport=httpx.MockTransport(lambda _: pytest.fail("transport must not run")),
    )
    with pytest.raises(PaidRequestBlockedError, match="budget gate") as captured:
        adapter.generate(_input_for_model(config))
    assert not isinstance(captured.value, AdapterTransportError)
    assert secret not in repr(captured.value)
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None


def test_frontier_paid_entrypoint_requires_a_configured_verifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_PROVIDER_KEY", "fixture-secret")
    config = _model_config(
        category="frontier_api",
        provider="openai_compat_api",
        base_url="https://example.test/v1",
        api_key_env="TEST_PROVIDER_KEY",
    )
    model_input = _input_for_model(config)
    adapter = OpenAICompatibleAdapter(
        config,
        transport=httpx.MockTransport(lambda _: pytest.fail("transport must not run")),
    )

    with pytest.raises(PaidRequestBlockedError, match="permit verifier"):
        adapter.generate_paid(model_input, _paid_permit(model_input.request.request_id))


def test_frontier_paid_entrypoint_revalidates_before_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_PROVIDER_KEY", "fixture-secret")
    config = _model_config(
        category="frontier_api",
        provider="openai_compat_api",
        base_url="https://example.test/v1",
        api_key_env="TEST_PROVIDER_KEY",
    )
    model_input = _input_for_model(config)
    calls: list[str] = []

    def reject(_: PaidRequestPermit) -> None:
        calls.append("verify")
        raise MissingApprovalError("fixture approval disappeared")

    def forbidden_transport(_: httpx.Request) -> httpx.Response:
        calls.append("transport")
        raise AssertionError("transport must not run")

    adapter = OpenAICompatibleAdapter(
        config,
        paid_permit_verifier=reject,
        transport=httpx.MockTransport(forbidden_transport),
    )

    with pytest.raises(MissingApprovalError, match="approval disappeared"):
        adapter.generate_paid(model_input, _paid_permit(model_input.request.request_id))
    assert calls == ["verify"]


def test_frontier_paid_entrypoint_binds_permit_and_preserves_direct_block(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_PROVIDER_KEY", "fixture-secret")
    config = _model_config(
        category="frontier_api",
        provider="openai_compat_api",
        base_url="https://example.test/v1",
        api_key_env="TEST_PROVIDER_KEY",
    )
    model_input = _input_for_model(config)
    calls: list[str] = []

    def verify(_: PaidRequestPermit) -> None:
        calls.append("verify")

    observed_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append("transport")
        observed_headers.update(request.headers)
        return httpx.Response(
            200,
            json={
                "id": "frontier-1",
                "choices": [{"message": {"content": "by trivial"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 4},
            },
        )

    adapter = OpenAICompatibleAdapter(
        config,
        paid_permit_verifier=verify,
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(PaidRequestBlockedError, match="budget gate"):
        adapter.generate(model_input)
    mismatched = _paid_permit("0" * 64)
    with pytest.raises(PaidRequestBlockedError, match="request_id"):
        adapter.generate_paid(model_input, mismatched)
    assert calls == []

    result = adapter.generate_paid(
        model_input,
        _paid_permit(model_input.request.request_id),
    )
    assert result.request_id == model_input.request.request_id
    assert calls == ["verify", "transport"]
    assert observed_headers["idempotency-key"] == model_input.request.request_id


@pytest.mark.parametrize(
    ("url", "message"),
    [
        ("http://example.test", "HTTPS"),
        ("https://user:password@example.test", "userinfo"),
        ("https://example.test/v1?tenant=x", "query or fragment"),
        ("https://example.test/v1#fragment", "query or fragment"),
    ],
)
def test_frontier_config_rejects_unsafe_urls(url: str, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        _model_config(
            category="frontier_api",
            provider="openai_compat_api",
            base_url=url,
        )


@pytest.mark.parametrize(
    ("adapter_name", "adapter_type"),
    [("proofbridge", ProofBridgeAdapter), ("proofflow", ProofFlowAdapter)],
)
def test_pipeline_subprocess_contract_smoke(
    tmp_path: Path,
    adapter_name: Literal["proofbridge", "proofflow"],
    adapter_type: type[JsonSubprocessAdapter],
) -> None:
    config = _pipeline_config(
        tmp_path,
        adapter_name,
        (
            sys.executable,
            str(PIPELINE_FIXTURE),
            "--request",
            "{request_path}",
            "--response",
            "{response_path}",
        ),
    )
    result = adapter_type(config).generate(_input_for_pipeline(config))
    assert result.provider_request_id == f"{adapter_name}-fixture"
    assert result.token_usage is not None
    assert result.token_usage.input_tokens == 12
    assert config.scratch_dir is not None
    assert list(config.scratch_dir.iterdir()) == []


def test_pipeline_rejects_partial_usage(tmp_path: Path) -> None:
    script = "import json,sys;json.dump({'text':'x','input_tokens':1},open(sys.argv[2],'w'))"
    config = _pipeline_config(
        tmp_path,
        "proofbridge",
        (sys.executable, "-c", script, "{request_path}", "{response_path}"),
    )
    with pytest.raises(AdapterResponseError, match="invalid response JSON"):
        ProofBridgeAdapter(config).generate(_input_for_pipeline(config))


def test_pipeline_requires_declared_environment(tmp_path: Path) -> None:
    config = _pipeline_config(
        tmp_path,
        "proofbridge",
        (sys.executable, "-c", "pass", "{request_path}", "{response_path}"),
        environment_names=("DEFINITELY_UNSET_PIPELINE_ENV",),
    )
    with pytest.raises(AdapterConfigurationError, match="DEFINITELY_UNSET_PIPELINE_ENV"):
        ProofBridgeAdapter(config).generate(_input_for_pipeline(config))


def test_pipeline_requires_pinned_checkout(tmp_path: Path) -> None:
    config = _pipeline_config(
        tmp_path,
        "proofbridge",
        (sys.executable, "-c", "pass", "{request_path}", "{response_path}"),
        commit="0" * 40,
    )
    with pytest.raises(AdapterConfigurationError, match="pinned commit"):
        ProofBridgeAdapter(config).generate(_input_for_pipeline(config))


def test_pipeline_requires_clean_checkout(tmp_path: Path) -> None:
    config = _pipeline_config(
        tmp_path,
        "proofbridge",
        (sys.executable, "-c", "pass", "{request_path}", "{response_path}"),
    )
    (config.workdir / "untracked.py").write_text("changed\n", encoding="utf-8")
    with pytest.raises(AdapterConfigurationError, match="not clean"):
        ProofBridgeAdapter(config).generate(_input_for_pipeline(config))


def test_pipeline_git_status_timeout_is_normalized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _pipeline_config(
        tmp_path,
        "proofbridge",
        (sys.executable, "-c", "pass", "{request_path}", "{response_path}"),
    )
    commit = config.model.pipeline_commit
    assert commit is not None

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert kwargs["timeout"] == 60
        if command[:2] == ["git", "rev-parse"]:
            return subprocess.CompletedProcess(command, 0, stdout=f"{commit}\n", stderr="")
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr("proof_faithfulness.models.pipeline.subprocess.run", fake_run)
    with pytest.raises(AdapterConfigurationError, match="Git status"):
        ProofBridgeAdapter(config).generate(_input_for_pipeline(config))


def test_pipeline_timeout_terminates_descendants(tmp_path: Path) -> None:
    marker = tmp_path / "descendant-survived"
    child = f"import pathlib,time;time.sleep(.4);pathlib.Path({str(marker)!r}).touch()"
    parent = f"import subprocess,sys,time;subprocess.Popen([sys.executable,'-c',{child!r}]);time.sleep(10)"
    config = _pipeline_config(
        tmp_path,
        "proofflow",
        (sys.executable, "-c", parent, "{request_path}", "{response_path}"),
        timeout_seconds=0.1,
    )
    with pytest.raises(AdapterTransportError, match="timed out"):
        ProofFlowAdapter(config).generate(_input_for_pipeline(config))
    time.sleep(0.5)
    assert not marker.exists()


def test_pipeline_nonzero_exit_preserves_bounded_diagnostics(tmp_path: Path) -> None:
    script = "import sys;print('probe failed',file=sys.stderr);raise SystemExit(78)"
    config = _pipeline_config(
        tmp_path,
        "proofbridge",
        (sys.executable, "-c", script, "{request_path}", "{response_path}"),
        max_response_bytes=1024,
    )
    with pytest.raises(AdapterResponseError, match="status 78") as caught:
        ProofBridgeAdapter(config).generate(_input_for_pipeline(config))
    assert caught.value.raw_response is not None
    assert b"probe failed" in caught.value.raw_response
    assert caught.value.raw_truncated is False


def test_pipeline_success_terminates_descendants(tmp_path: Path) -> None:
    marker = tmp_path / "success-descendant-survived"
    child = f"import pathlib,time;time.sleep(.4);pathlib.Path({str(marker)!r}).touch()"
    parent = (
        "import json,pathlib,subprocess,sys;"
        f"subprocess.Popen([sys.executable,'-c',{child!r}]);"
        "pathlib.Path(sys.argv[2]).write_text(json.dumps("
        "{'text':'by trivial','input_tokens':0,'output_tokens':0}))"
    )
    config = _pipeline_config(
        tmp_path,
        "proofbridge",
        (sys.executable, "-c", parent, "{request_path}", "{response_path}"),
    )
    assert ProofBridgeAdapter(config).generate(_input_for_pipeline(config)).text == "by trivial"
    time.sleep(0.5)
    assert not marker.exists()


def test_pipeline_rejects_oversized_response(tmp_path: Path) -> None:
    script = "import pathlib,sys;pathlib.Path(sys.argv[2]).write_bytes(b'x'*9)"
    config = _pipeline_config(
        tmp_path,
        "proofbridge",
        (sys.executable, "-c", script, "{request_path}", "{response_path}"),
        max_response_bytes=8,
    )
    with pytest.raises(AdapterResponseError, match="byte limit"):
        ProofBridgeAdapter(config).generate(_input_for_pipeline(config))


def test_normative_yaml_loads_with_unfrozen_revision(tmp_path: Path) -> None:
    path = tmp_path / "model.yaml"
    path.write_text(
        """\
key: deepseek_prover_v2_7b
category: prover
provider: vllm
model_id: deepseek-ai/DeepSeek-Prover-V2-7B
revision: null
base_url: http://localhost:8000/v1
api_key_env: null
chat_template: prover_deepseek_v1
decoding:
  temperature: 1.0
  top_p: 0.95
  max_tokens: 8192
  seed_base: 20260724
concurrency: 4
pricing_usd_per_mtok: {input: 0.0, output: 0.0}
pipeline_commit: null
context_window: 16384
dtype: bfloat16
""",
        encoding="utf-8",
    )
    config = load_adapter_config(path)
    assert config.key == "deepseek_prover_v2_7b"
    assert config.revision is None


def test_pipeline_config_requires_both_file_placeholders(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="response_path"):
        PipelineAdapterConfig(
            model=_model_config(
                category="pipeline",
                provider="proofbridge",
                base_url=None,
                pipeline_commit="0" * 40,
            ),
            command=("runner", "{request_path}"),
            workdir=tmp_path,
        )
