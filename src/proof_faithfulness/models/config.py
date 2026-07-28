"""Normative model-slate YAML and internal adapter runtime configuration."""

from __future__ import annotations

import hashlib
import re
from decimal import Decimal
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from proof_faithfulness.ids import canonical_json
from proof_faithfulness.models.base import ModelCapabilities
from proof_faithfulness.schema import NonEmptyString, SamplingOption


class ConfigModel(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", frozen=True)


class DecodingConfig(ConfigModel):
    """The exact per-model decoding recipe from the S4 contract."""

    temperature: float = Field(ge=0)
    top_p: float = Field(gt=0, le=1)
    max_tokens: int = Field(gt=0)
    seed_base: int
    extra: tuple[SamplingOption, ...] = ()

    @model_validator(mode="after")
    def reject_duplicate_options(self) -> DecodingConfig:
        names = tuple(option.name for option in self.extra)
        if len(set(names)) != len(names):
            raise ValueError("Decoding option names must be unique")
        return self


class PricingConfig(ConfigModel):
    """USD prices per one million input and output tokens."""

    input: Decimal = Field(ge=0)
    output: Decimal = Field(ge=0)


class ModelConfig(ConfigModel):
    """One model YAML in the exact normative S4 model-slate shape."""

    key: NonEmptyString
    category: Literal["frontier_api", "open_weight", "prover", "pipeline"]
    provider: Literal["vllm", "openai_compat_api", "proofbridge", "proofflow"]
    model_id: NonEmptyString
    revision: NonEmptyString | None
    base_url: HttpUrl | None
    api_key_env: str | None
    chat_template: NonEmptyString
    decoding: DecodingConfig
    concurrency: int = Field(gt=0)
    pricing_usd_per_mtok: PricingConfig
    pipeline_commit: str | None
    context_window: int = Field(gt=0)
    dtype: NonEmptyString | None = None
    quantization: NonEmptyString | None = None
    serving_args: tuple[NonEmptyString, ...] = ()

    @property
    def adapter(self) -> str:
        if self.provider in {"vllm", "openai_compat_api"}:
            return "openai_compatible"
        return self.provider

    @property
    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            proof_conditioning=True,
            deterministic_seed=True,
            local_inference=self.provider != "openai_compat_api",
            structured_output=False,
            repair=self.category in {"prover", "pipeline"},
            cost_reporting=True,
        )

    def require_revision(self) -> str:
        if self.revision is None:
            raise ValueError(f"Model revision is not frozen for {self.key}")
        return self.revision

    @model_validator(mode="after")
    def validate_provider_contract(self) -> ModelConfig:
        expected_providers = {
            "frontier_api": {"openai_compat_api"},
            "open_weight": {"vllm"},
            "prover": {"vllm"},
            "pipeline": {"proofbridge", "proofflow"},
        }
        if self.provider not in expected_providers[self.category]:
            raise ValueError(
                f"Provider {self.provider!r} is incompatible with category {self.category!r}"
            )
        if self.api_key_env is not None and not re.fullmatch(r"[A-Z_][A-Z0-9_]*", self.api_key_env):
            raise ValueError("api_key_env must be an uppercase environment-variable name")
        if self.category == "pipeline":
            if self.base_url is not None or self.api_key_env is not None:
                raise ValueError("Pipeline configs must set base_url and api_key_env to null")
        else:
            if self.base_url is None:
                raise ValueError("Non-pipeline configs require base_url")
            if self.pipeline_commit is not None:
                raise ValueError("pipeline_commit is only valid for pipeline configs")
            if self.base_url.username is not None or self.base_url.password is not None:
                raise ValueError("base_url must not contain userinfo credentials")
            if self.base_url.query is not None or self.base_url.fragment is not None:
                raise ValueError("base_url must not contain a query or fragment")
            if self.category == "frontier_api" and self.base_url.scheme != "https":
                raise ValueError("A frontier API must use an HTTPS base_url")
            if self.category != "frontier_api" and self.api_key_env is not None:
                raise ValueError("api_key_env is only valid for frontier API configs")
        if self.provider in {"vllm", "proofbridge", "proofflow"} and (
            self.pricing_usd_per_mtok.input != 0 or self.pricing_usd_per_mtok.output != 0
        ):
            raise ValueError("Local model and pipeline pricing must be zero")
        if self.context_window <= self.decoding.max_tokens:
            raise ValueError("context_window must exceed decoding.max_tokens")
        if self.provider == "vllm":
            if self.dtype is None:
                raise ValueError("vLLM configs require an explicit dtype")
        elif self.dtype is not None or self.quantization is not None or self.serving_args:
            raise ValueError("Serving dtype, quantization, and args are only valid for vLLM")
        if self.pipeline_commit is not None and not re.fullmatch(
            r"[0-9a-f]{40}", self.pipeline_commit
        ):
            raise ValueError("pipeline_commit must be a full 40-character Git commit")
        return self


class PipelineAdapterConfig(ConfigModel):
    """Local runtime details layered over a normative pipeline model config."""

    model: ModelConfig
    command: tuple[NonEmptyString, ...]
    workdir: Path
    scratch_dir: Path | None = None
    timeout_seconds: float = Field(default=600, gt=0)
    max_response_bytes: int = Field(default=16 * 1024 * 1024, gt=0)
    environment_names: tuple[NonEmptyString, ...] = ()

    @property
    def adapter(self) -> Literal["proofbridge", "proofflow"]:
        if self.model.provider == "proofbridge":
            return "proofbridge"
        if self.model.provider == "proofflow":
            return "proofflow"
        raise ValueError("Pipeline runtime requires a pipeline provider")

    @property
    def provider(self) -> str:
        return self.model.provider

    @property
    def model_id(self) -> str:
        return self.model.model_id

    @property
    def model_revision(self) -> str:
        return self.model.require_revision()

    @property
    def model_key(self) -> str:
        return self.model.key

    @property
    def capabilities(self) -> ModelCapabilities:
        return self.model.capabilities

    @model_validator(mode="after")
    def validate_runtime(self) -> PipelineAdapterConfig:
        if self.model.category != "pipeline":
            raise ValueError("Pipeline runtime requires category=pipeline")
        if not self.command:
            raise ValueError("Pipeline command cannot be empty")
        command = "\0".join(self.command)
        for placeholder in ("{request_path}", "{response_path}"):
            if placeholder not in command:
                raise ValueError(f"Pipeline command must contain {placeholder}")
        if len(set(self.environment_names)) != len(self.environment_names):
            raise ValueError("environment_names must be unique")
        return self


class MockAdapterConfig(ConfigModel):
    """Internal deterministic backend used only by offline harness tests."""

    adapter: Literal["mock"] = "mock"
    provider: Literal["mock"] = "mock"
    model_key: NonEmptyString = "deterministic_mock"
    model_id: NonEmptyString = "deterministic-mock"
    model_revision: NonEmptyString = "mock-v1"
    response_text: str = "by\n  trivial"
    capabilities: ModelCapabilities = ModelCapabilities(
        proof_conditioning=True,
        deterministic_seed=True,
        local_inference=True,
        structured_output=False,
        repair=False,
        cost_reporting=True,
    )


OpenAICompatibleConfig = ModelConfig
type AdapterConfig = ModelConfig | PipelineAdapterConfig | MockAdapterConfig


def load_adapter_config(path: Path) -> ModelConfig:
    """Load a strict normative slate YAML without resolving any secret value."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"Adapter config must be a YAML mapping: {path}")
    return ModelConfig.model_validate(raw)


def compute_adapter_config_hash(config: ConfigModel) -> str:
    """Bind a request to every non-secret model and runtime configuration value."""
    serialized = canonical_json(config.model_dump(mode="json"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
