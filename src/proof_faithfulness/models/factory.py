"""Adapter construction from validated configuration."""

from __future__ import annotations

from proof_faithfulness.models.base import ModelAdapter
from proof_faithfulness.models.config import (
    AdapterConfig,
    MockAdapterConfig,
    ModelConfig,
    PipelineAdapterConfig,
)
from proof_faithfulness.models.mock import MockAdapter
from proof_faithfulness.models.openai_compat import OpenAICompatibleAdapter
from proof_faithfulness.models.pipeline import ProofBridgeAdapter, ProofFlowAdapter


def build_adapter(config: AdapterConfig) -> ModelAdapter:
    """Build a concrete adapter from a discriminated configuration."""
    if isinstance(config, MockAdapterConfig):
        return MockAdapter(config)
    if isinstance(config, PipelineAdapterConfig):
        if config.adapter == "proofbridge":
            return ProofBridgeAdapter(config)
        return ProofFlowAdapter(config)
    if isinstance(config, ModelConfig):
        if config.provider in {"vllm", "openai_compat_api"}:
            return OpenAICompatibleAdapter(config)
        raise ValueError("Pipeline model configs require local runtime configuration")
    raise TypeError(f"Unsupported adapter config: {type(config).__name__}")
