"""OpenAI-compatible chat completions adapter for APIs and local vLLM."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from email.utils import parsedate_to_datetime
from typing import TYPE_CHECKING, Any

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

if TYPE_CHECKING:
    from proof_faithfulness.generation.budget import PaidRequestPermit

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


class OpenAITransportError(AdapterTransportError):
    """Retryable HTTP/transport failure with bounded provider evidence."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        retry_after_s: float | None = None,
        raw_response: bytes | None = None,
        provider_request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retry_after_s = retry_after_s
        self.raw_response = raw_response
        self.provider_request_id = provider_request_id


class OpenAICompatibleAdapter:
    """Synchronous smoke/pilot adapter for `/v1/chat/completions` endpoints."""

    def __init__(
        self,
        config: OpenAICompatibleConfig,
        *,
        transport: httpx.BaseTransport | None = None,
        paid_permit_verifier: Callable[[PaidRequestPermit], None] | None = None,
        timeout_seconds: float = 120,
        max_response_bytes: int = 16 * 1024 * 1024,
    ) -> None:
        if config.provider not in {"vllm", "openai_compat_api"}:
            raise ValueError("OpenAICompatibleAdapter requires an HTTP model provider")
        self._config = config
        self._transport = transport
        self._paid_permit_verifier = paid_permit_verifier
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
                "Paid frontier requests require the generation budget gate"
            )
        return self._generate(model_input, idempotency_key=None)

    def generate_paid(
        self,
        model_input: ModelInput,
        permit: PaidRequestPermit,
    ) -> AdapterResult:
        """Runs a frontier request only through a ledger-backed permit verifier."""
        if self._config.category != "frontier_api":
            raise PaidRequestBlockedError("Paid transport is only valid for frontier adapters")
        if self._paid_permit_verifier is None:
            raise PaidRequestBlockedError(
                "Paid frontier requests require a configured budget-permit verifier"
            )
        if permit.request_id != model_input.request.request_id:
            raise PaidRequestBlockedError("Paid permit request_id does not match the request")
        self._paid_permit_verifier(permit)
        return self._generate(
            model_input,
            idempotency_key=model_input.request.request_id,
        )

    def preflight(self, model_input: ModelInput) -> None:
        """Validate request identity, sampling, endpoint, and credentials without I/O."""
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
        extra = {option.name: option.value for option in model_input.request.sampling.extra}
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
            extra=self._config.decoding.extra,
        )
        self._endpoint()
        if self._config.api_key_env is not None and not os.environ.get(
            self._config.api_key_env
        ):
            raise MissingSecretError(
                f"Required environment variable is unset: {self._config.api_key_env}"
            )

    def _generate(
        self,
        model_input: ModelInput,
        *,
        idempotency_key: str | None,
    ) -> AdapterResult:
        self.preflight(model_input)
        request = model_input.request
        extra = {option.name: option.value for option in request.sampling.extra}
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
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        if self._config.api_key_env is not None:
            secret = os.environ.get(self._config.api_key_env)
            if not secret:
                raise MissingSecretError(
                    f"Required environment variable is unset: {self._config.api_key_env}"
                )
            headers["Authorization"] = f"Bearer {secret}"

        raw_response: bytes | None = None
        status_code: int | None = None
        response_headers: httpx.Headers | None = None
        try:
            with (
                httpx.Client(
                    timeout=self._timeout_seconds,
                    transport=self._transport,
                ) as client,
                client.stream("POST", self._endpoint(), headers=headers, json=payload) as response,
            ):
                status_code = response.status_code
                response_headers = response.headers
                raw_response = _read_limited_response(response, max_bytes=self._max_response_bytes)
        except httpx.HTTPError as error:
            raise OpenAITransportError(
                f"OpenAI-compatible request failed: {type(error).__name__}"
            ) from None
        if raw_response is None:
            raise OpenAITransportError("OpenAI-compatible request returned no response body")

        provider_request_id = _provider_request_id(raw_response)
        if status_code is not None and status_code >= 400:
            message = f"OpenAI-compatible endpoint returned HTTP {status_code}"
            if _is_retryable_status(status_code):
                raise OpenAITransportError(
                    message,
                    status_code=status_code,
                    retry_after_s=_retry_after_seconds(response_headers),
                    raw_response=raw_response,
                    provider_request_id=provider_request_id,
                )
            raise AdapterResponseError(
                message,
                raw_response=raw_response,
                provider_request_id=provider_request_id,
            )

        try:
            body = json.loads(raw_response.decode("utf-8"))
            if not isinstance(body, dict):
                raise TypeError("response body must be an object")
            choices = body["choices"]
            if not isinstance(choices, list) or len(choices) != 1:
                raise TypeError("choices must contain exactly one item")
            choice = choices[0]
            text = choice["message"]["content"]
            if not isinstance(text, str):
                raise TypeError("message content is not a string")
        except (KeyError, IndexError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise AdapterResponseError(
                "Invalid OpenAI-compatible response schema",
                raw_response=raw_response,
                provider_request_id=provider_request_id,
            ) from error

        usage = _parse_usage(
            body.get("usage"),
            raw_response=raw_response,
            provider_request_id=provider_request_id,
        )
        if usage is None:
            raise AdapterResponseError(
                "Successful response is missing token usage",
                raw_response=raw_response,
                provider_request_id=provider_request_id,
            )
        return AdapterResult(
            request_id=request.request_id,
            text=text,
            raw_response=raw_response,
            provider_request_id=provider_request_id,
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


def compute_usd_cost(usage: TokenUsage, pricing: PricingConfig) -> Decimal:
    """Compute usage cost from prices expressed in USD per million tokens."""
    return (
        Decimal(usage.input_tokens) * pricing.input + Decimal(usage.output_tokens) * pricing.output
    ) / Decimal(1_000_000)


def _parse_usage(
    raw: object,
    *,
    raw_response: bytes,
    provider_request_id: str | None,
) -> TokenUsage | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise AdapterResponseError(
            "Response usage must be an object",
            raw_response=raw_response,
            provider_request_id=provider_request_id,
        )
    try:
        return TokenUsage(
            input_tokens=raw["prompt_tokens"],
            output_tokens=raw["completion_tokens"],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise AdapterResponseError(
            "Invalid token usage in response",
            raw_response=raw_response,
            provider_request_id=provider_request_id,
        ) from error


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _provider_request_id(raw_response: bytes) -> str | None:
    try:
        body = json.loads(raw_response.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return _optional_string(body.get("id")) if isinstance(body, dict) else None


def _is_retryable_status(status_code: int) -> bool:
    return status_code in {408, 409, 425, 429} or status_code >= 500


def _retry_after_seconds(headers: httpx.Headers | None) -> float | None:
    if headers is None:
        return None
    value = headers.get("Retry-After")
    if value is None:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=UTC)
        return max(0.0, (retry_at - datetime.now(UTC)).total_seconds())


def _read_limited_response(response: httpx.Response, *, max_bytes: int) -> bytes:
    content = bytearray()
    for chunk in response.iter_bytes():
        remaining = max_bytes - len(content)
        content.extend(chunk[:remaining])
        if len(chunk) > remaining:
            raise AdapterResponseError(
                f"OpenAI-compatible response exceeds {max_bytes} byte limit",
                raw_response=bytes(content),
                raw_truncated=True,
            )
    return bytes(content)
