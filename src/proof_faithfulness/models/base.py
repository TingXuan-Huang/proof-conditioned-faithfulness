"""Transport-neutral contracts for model and prover inference."""

from __future__ import annotations

import hashlib
from decimal import Decimal
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from proof_faithfulness.ids import canonical_json
from proof_faithfulness.schema import GenerationRequest, TokenUsage


class AdapterError(RuntimeError):
    """Base class for normalized adapter failures."""


class AdapterConfigurationError(AdapterError):
    """Raised when configuration and a generation request disagree."""


class AdapterTransportError(AdapterError):
    """Raised when an HTTP or subprocess transport fails."""


class AdapterResponseError(AdapterError):
    """Raised with any received bytes when a transport response is invalid."""

    def __init__(
        self,
        message: str,
        *,
        raw_response: bytes | None = None,
        provider_request_id: str | None = None,
        raw_truncated: bool = False,
    ) -> None:
        super().__init__(message)
        self.raw_response = raw_response
        self.provider_request_id = provider_request_id
        self.raw_truncated = raw_truncated


class MissingSecretError(AdapterConfigurationError):
    """Raised when a configured secret environment variable is absent."""


class AdapterModel(BaseModel):
    """Immutable base for adapter data exchanged inside the harness."""

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", frozen=True)


class ChatMessage(AdapterModel):
    """One OpenAI-compatible chat message."""

    role: Literal["system", "user", "assistant"]
    content: str

    @field_validator("content")
    @classmethod
    def require_nonempty_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Chat message content cannot be empty or whitespace-only")
        return value


class ModelCapabilities(AdapterModel):
    """Features exposed by a configured adapter."""

    proof_conditioning: bool = True
    deterministic_seed: bool = True
    local_inference: bool = False
    structured_output: bool = False
    repair: bool = False
    cost_reporting: bool = False

    def enabled_flags(self) -> tuple[str, ...]:
        return tuple(name for name, enabled in self.model_dump(mode="python").items() if enabled)


def compute_rendered_prompt_hash(messages: tuple[ChatMessage, ...]) -> str:
    """Hash the exact ordered messages sent across an adapter boundary."""
    payload = {"messages": [message.model_dump(mode="json") for message in messages]}
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


class ModelInput(AdapterModel):
    """A request contract paired with the exact rendered chat content."""

    request: GenerationRequest
    messages: tuple[ChatMessage, ...]

    @model_validator(mode="after")
    def validate_prompt_hash(self) -> ModelInput:
        if not self.messages:
            raise ValueError("At least one chat message is required")
        actual_hash = compute_rendered_prompt_hash(self.messages)
        if actual_hash != self.request.rendered_prompt_hash:
            raise ValueError("Rendered messages do not match rendered_prompt_hash")
        return self


class AdapterResult(AdapterModel):
    """Normalized successful result returned by any inference backend."""

    request_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    text: str
    raw_response: bytes
    provider_request_id: str | None = None
    token_usage: TokenUsage
    usd_cost: Decimal = Field(ge=0)
    finish_reason: str | None = None


@runtime_checkable
class ModelAdapter(Protocol):
    """Common synchronous interface for API, local-model, and prover backends."""

    @property
    def name(self) -> str: ...

    @property
    def capabilities(self) -> ModelCapabilities: ...

    def generate(self, model_input: ModelInput) -> AdapterResult: ...


def validate_request_identity(
    model_input: ModelInput,
    *,
    adapter_name: str,
    provider: str,
    model_key: str,
    model_id: str,
    model_revision: str,
    backend_config_hash: str,
    capabilities: ModelCapabilities,
) -> None:
    """Fail closed when recorded request identity differs from live configuration."""
    request = model_input.request
    expected = {
        "model_adapter": adapter_name,
        "provider": provider,
        "model_key": model_key,
        "model_id": model_id,
        "model_revision": model_revision,
        "backend_config_hash": backend_config_hash,
    }
    actual = {
        "model_adapter": request.model_adapter,
        "provider": request.provider,
        "model_key": request.model_key,
        "model_id": request.model_id,
        "model_revision": request.model_revision,
        "backend_config_hash": request.backend_config_hash,
    }
    if actual != expected:
        raise AdapterConfigurationError(
            "Generation request identity does not match adapter configuration: "
            f"expected={expected!r}, actual={actual!r}"
        )
    unsupported = set(request.capability_flags) - set(capabilities.enabled_flags())
    if unsupported:
        raise AdapterConfigurationError(
            f"Request claims unsupported adapter capabilities: {sorted(unsupported)}"
        )


def validate_sampling_recipe(
    model_input: ModelInput,
    *,
    temperature: float,
    top_p: float,
    max_tokens: int,
    seed_base: int,
) -> None:
    """Require the request to use exactly the recipe pinned in model YAML."""
    sampling = model_input.request.sampling
    expected_seed = seed_base + model_input.request.sample_index
    actual = (sampling.temperature, sampling.top_p, sampling.max_tokens, sampling.seed)
    expected = (temperature, top_p, max_tokens, expected_seed)
    if actual != expected or sampling.extra:
        raise AdapterConfigurationError(
            f"Request sampling does not match pinned model recipe: expected={expected!r}"
        )
