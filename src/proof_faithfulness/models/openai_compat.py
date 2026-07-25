"""OpenAI-compatible chat completions adapter for APIs and local vLLM."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from proof_faithfulness.models.base import (
    AdapterConfigurationError,
    AdapterResponseError,
    AdapterResult,
    AdapterTransportError,
    MissingSecretError,
    ModelCapabilities,
    ModelInput,
    validate_request_identity,
    validate_sampling_recipe,
)
from proof_faithfulness.models.config import (
    OpenAICompatibleConfig,
    PricingConfig,
    compute_adapter_config_hash,
)
from proof_faithfulness.schema import TokenUsage

_RESERVED_SAMPLING_KEYS = {
    "model",
    "messages",
    "temperature",
    "top_p",
    "max_tokens",
    "seed",
    "n",
    "best_of",
    "stream",
}


class PaidRequestBlockedError(AdapterConfigurationError):
    """Raised until the generation layer supplies a machine-checked budget permit."""


class OpenAICompatibleAdapter:
    """Synchronous smoke/pilot adapter for `/v1/chat/completions` endpoints."""

    def __init__(
        self,
        config: OpenAICompatibleConfig,
        *,
        transport: httpx.BaseTransport | None = None,
        timeout_seconds: float = 120,
        max_response_bytes: int = 16 * 1024 * 1024,
    ) -> None:
        if config.provider not in {"vllm", "openai_compat_api"}:
            raise ValueError("OpenAICompatibleAdapter requires an HTTP model provider")
        self._config = config
        self._transport = transport
        self._timeout_seconds = timeout_seconds
        self._max_response_bytes = max_response_bytes

    @property
    def name(self) -> str:
        return self._config.adapter

    @property
    def capabilities(self) -> ModelCapabilities:
        return self._config.capabilities

    def generate(self, model_input: ModelInput) -> AdapterResult:
        if self._config.category == "frontier_api":
            raise PaidRequestBlockedError(
                "Paid frontier requests are disabled until the generation budget gate is implemented"
            )
        validate_request_identity(
            model_input,
            adapter_name=self.name,
            provider=self._config.provider,
            model_key=self._config.key,
            model_id=self._config.model_id,
            model_revision=self._config.require_revision(),
            backend_config_hash=compute_adapter_config_hash(self._config),
            capabilities=self.capabilities,
        )
        request = model_input.request
        extra = {option.name: option.value for option in request.sampling.extra}
        conflicts = set(extra) & _RESERVED_SAMPLING_KEYS
        if conflicts:
            raise AdapterResponseError(
                f"Provider-specific sampling options override reserved keys: {sorted(conflicts)}"
            )
        validate_sampling_recipe(
            model_input,
            temperature=self._config.decoding.temperature,
            top_p=self._config.decoding.top_p,
            max_tokens=self._config.decoding.max_tokens,
            seed_base=self._config.decoding.seed_base,
        )
        payload: dict[str, Any] = {
            "model": self._config.model_id,
            "messages": [message.model_dump(mode="json") for message in model_input.messages],
            "temperature": request.sampling.temperature,
            "top_p": request.sampling.top_p,
            "max_tokens": request.sampling.max_tokens,
            **extra,
        }
        if request.sampling.seed is not None:
            payload["seed"] = request.sampling.seed

        headers = {"Content-Type": "application/json"}
        if self._config.api_key_env is not None:
            secret = os.environ.get(self._config.api_key_env)
            if not secret:
                raise MissingSecretError(
                    f"Required environment variable is unset: {self._config.api_key_env}"
                )
            headers["Authorization"] = f"Bearer {secret}"

        transport_error: str | None = None
        raw_response: bytes | None = None
        try:
            with (
                httpx.Client(
                    timeout=self._timeout_seconds,
                    transport=self._transport,
                ) as client,
                client.stream("POST", self._endpoint(), headers=headers, json=payload) as response,
            ):
                response.raise_for_status()
                raw_response = _read_limited_response(response, max_bytes=self._max_response_bytes)
        except httpx.HTTPStatusError as error:
            transport_error = (
                f"OpenAI-compatible endpoint returned HTTP {error.response.status_code}"
            )
        except httpx.HTTPError as error:
            transport_error = f"OpenAI-compatible request failed: {type(error).__name__}"
        if transport_error is not None:
            raise AdapterTransportError(transport_error)
        if raw_response is None:
            raise AdapterTransportError("OpenAI-compatible request returned no response body")

        try:
            body = json.loads(raw_response)
            choices = body["choices"]
            if not isinstance(choices, list) or len(choices) != 1:
                raise TypeError("choices must contain exactly one item")
            choice = choices[0]
            text = choice["message"]["content"]
            if not isinstance(text, str):
                raise TypeError("message content is not a string")
        except (KeyError, IndexError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise AdapterResponseError("Invalid OpenAI-compatible response schema") from error

        usage = _parse_usage(body.get("usage"))
        if usage is None:
            raise AdapterResponseError("Successful response is missing token usage")
        return AdapterResult(
            request_id=request.request_id,
            text=text,
            raw_response=raw_response,
            provider_request_id=_optional_string(body.get("id")),
            token_usage=usage,
            usd_cost=compute_usd_cost(usage, self._config.pricing_usd_per_mtok),
            finish_reason=_optional_string(choice.get("finish_reason")),
        )

    def _endpoint(self) -> str:
        if self._config.base_url is None:
            raise AdapterConfigurationError("HTTP model config has no base_url")
        base = str(self._config.base_url).rstrip("/")
        suffix = "/chat/completions" if base.endswith("/v1") else "/v1/chat/completions"
        return f"{base}{suffix}"


def compute_usd_cost(usage: TokenUsage, pricing: PricingConfig) -> float:
    """Compute usage cost from prices expressed in USD per million tokens."""
    return (usage.input_tokens * pricing.input + usage.output_tokens * pricing.output) / 1_000_000


def _parse_usage(raw: object) -> TokenUsage | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise AdapterResponseError("Response usage must be an object")
    try:
        return TokenUsage(
            input_tokens=raw["prompt_tokens"],
            output_tokens=raw["completion_tokens"],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise AdapterResponseError("Invalid token usage in response") from error


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _read_limited_response(response: httpx.Response, *, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_bytes():
        total += len(chunk)
        if total > max_bytes:
            raise AdapterResponseError(f"OpenAI-compatible response exceeds {max_bytes} byte limit")
        chunks.append(chunk)
    return b"".join(chunks)
