"""Deterministic adapter for offline end-to-end smoke tests."""

from __future__ import annotations

import json
from decimal import Decimal

from proof_faithfulness.models.base import (
    AdapterResult,
    ModelCapabilities,
    ModelInput,
    validate_request_identity,
)
from proof_faithfulness.models.config import MockAdapterConfig, compute_adapter_config_hash
from proof_faithfulness.schema import TokenUsage


class MockAdapter:
    def __init__(self, config: MockAdapterConfig) -> None:
        self._config = config

    @property
    def name(self) -> str:
        return self._config.adapter

    @property
    def capabilities(self) -> ModelCapabilities:
        return self._config.capabilities

    def generate(self, model_input: ModelInput) -> AdapterResult:
        validate_request_identity(
            model_input,
            adapter_name=self.name,
            provider=self._config.provider,
            model_key=self._config.model_key,
            model_id=self._config.model_id,
            model_revision=self._config.model_revision,
            backend_config_hash=compute_adapter_config_hash(self._config),
            capabilities=self.capabilities,
        )
        response = {
            "id": f"mock-{model_input.request.request_id[:16]}",
            "text": self._config.response_text,
            "finish_reason": "stop",
        }
        return AdapterResult(
            request_id=model_input.request.request_id,
            text=self._config.response_text,
            raw_response=(
                json.dumps(response, ensure_ascii=True, sort_keys=True).encode("utf-8") + b"\n"
            ),
            provider_request_id=response["id"],
            token_usage=TokenUsage(input_tokens=0, output_tokens=0),
            usd_cost=Decimal(0),
            finish_reason="stop",
        )
