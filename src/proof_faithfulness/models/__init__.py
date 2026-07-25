"""Model and prover adapters used by the generation harness."""

from proof_faithfulness.models.base import (
    AdapterError,
    AdapterResult,
    ChatMessage,
    ModelAdapter,
    ModelCapabilities,
    ModelInput,
    compute_rendered_prompt_hash,
)
from proof_faithfulness.models.config import (
    AdapterConfig,
    DecodingConfig,
    MockAdapterConfig,
    ModelConfig,
    OpenAICompatibleConfig,
    PipelineAdapterConfig,
    PricingConfig,
    compute_adapter_config_hash,
    load_adapter_config,
)
from proof_faithfulness.models.factory import build_adapter

__all__ = [
    "AdapterConfig",
    "AdapterError",
    "AdapterResult",
    "ChatMessage",
    "DecodingConfig",
    "MockAdapterConfig",
    "ModelAdapter",
    "ModelCapabilities",
    "ModelConfig",
    "ModelInput",
    "OpenAICompatibleConfig",
    "PipelineAdapterConfig",
    "PricingConfig",
    "build_adapter",
    "compute_adapter_config_hash",
    "compute_rendered_prompt_hash",
    "load_adapter_config",
]
