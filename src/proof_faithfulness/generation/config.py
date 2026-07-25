"""Strict configuration contracts for the generation condition matrix."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from proof_faithfulness.models import (
    AdapterConfig,
    DecodingConfig,
    MockAdapterConfig,
    ModelCapabilities,
    ModelConfig,
    PipelineAdapterConfig,
    PricingConfig,
    compute_adapter_config_hash,
)
from proof_faithfulness.schema import NonEmptyString, SchemaVersion

_EXPECTED_CONDITIONS = (
    ("theorem_only", 1, None, "none", "theorem_only_v1.txt", False),
    ("proof_a", 1, "A", "proof", "preservation_v1.txt", True),
    ("proof_b", 1, "B", "proof", "preservation_v1.txt", True),
    ("proof_a_validity", 2, "A", "proof", "validity_only_v1.txt", True),
    ("proof_b_validity", 2, "B", "proof", "validity_only_v1.txt", True),
    ("proof_a_paraphrase", 3, "A", "paraphrase", "preservation_v1.txt", True),
    ("proof_b_paraphrase", 3, "B", "paraphrase", "preservation_v1.txt", True),
    (
        "proof_a_paraphrase_validity",
        4,
        "A",
        "paraphrase",
        "validity_only_v1.txt",
        True,
    ),
    (
        "proof_b_paraphrase_validity",
        4,
        "B",
        "paraphrase",
        "validity_only_v1.txt",
        True,
    ),
)


class GenerationConfigModel(BaseModel):
    """Immutable base for generation configuration loaded from YAML."""

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", frozen=True)


class ConditionConfig(GenerationConfigModel):
    """One configured experimental condition."""

    key: NonEmptyString
    tier: int = Field(ge=1, le=4)
    proof_id: Literal["A", "B"] | None
    proof_source: Literal["none", "proof", "paraphrase"]
    system_template: NonEmptyString
    user_template: NonEmptyString
    requires_proof_conditioning: bool

    @model_validator(mode="after")
    def validate_proof_binding(self) -> ConditionConfig:
        if self.proof_source == "none":
            if self.proof_id is not None or self.requires_proof_conditioning:
                raise ValueError(
                    "A proof-free condition cannot bind a proof or require conditioning"
                )
        elif self.proof_id is None or not self.requires_proof_conditioning:
            raise ValueError("A proof condition must bind A or B and require proof conditioning")
        return self


class ConditionMatrix(GenerationConfigModel):
    """Versioned cumulative condition tiers and samples per cell."""

    schema_version: SchemaVersion
    samples_per_cell: int = Field(gt=0)
    conditions: tuple[ConditionConfig, ...]

    @model_validator(mode="after")
    def validate_matrix(self) -> ConditionMatrix:
        if self.samples_per_cell != 3:
            raise ValueError("The frozen condition matrix requires exactly 3 samples per cell")
        actual = tuple(
            (
                condition.key,
                condition.tier,
                condition.proof_id,
                condition.proof_source,
                condition.user_template,
                condition.requires_proof_conditioning,
            )
            for condition in self.conditions
        )
        if actual != _EXPECTED_CONDITIONS:
            raise ValueError("Conditions must exactly match the fixed T1-T4 matrix")
        if any(condition.system_template != "base_system_v1.txt" for condition in self.conditions):
            raise ValueError("Every fixed condition must use base_system_v1.txt")
        return self

    def through_tier(self, tier: int) -> tuple[ConditionConfig, ...]:
        """Returns the additive condition matrix through ``tier``."""
        if tier < 1 or tier > 4:
            raise ValueError("tier must be between 1 and 4")
        return tuple(condition for condition in self.conditions if condition.tier <= tier)


class PlanningModel(GenerationConfigModel):
    """Exact adapter config plus planning data absent from the mock backend."""

    backend_config: AdapterConfig
    mock_chat_template: NonEmptyString | None = None
    mock_decoding: DecodingConfig | None = None
    mock_max_input_tokens: int | None = Field(default=None, gt=0)
    paid_idempotency_verified: Literal[False] = False

    @model_validator(mode="after")
    def validate_backend(self) -> PlanningModel:
        is_mock = isinstance(self.backend_config, MockAdapterConfig)
        mock_fields = (
            self.mock_chat_template,
            self.mock_decoding,
            self.mock_max_input_tokens,
        )
        if is_mock and any(value is None for value in mock_fields):
            raise ValueError("Mock planning requires chat template, decoding, and input bound")
        if not is_mock and any(value is not None for value in mock_fields):
            raise ValueError("Production planning derives all model fields from backend_config")
        if isinstance(self.backend_config, ModelConfig):
            self.backend_config.require_revision()
        elif isinstance(self.backend_config, PipelineAdapterConfig):
            self.backend_config.model.require_revision()
        if self.paid and self.maximum_request_usd() <= 0:
            raise ValueError("A frontier planning config requires nonzero pinned pricing")
        return self

    @property
    def key(self) -> str:
        config = self.backend_config
        if isinstance(config, (MockAdapterConfig, PipelineAdapterConfig)):
            return config.model_key
        return config.key

    @property
    def adapter(self) -> str:
        return self.backend_config.adapter

    @property
    def provider(self) -> str:
        return self.backend_config.provider

    @property
    def model_id(self) -> str:
        return self.backend_config.model_id

    @property
    def revision(self) -> str:
        config = self.backend_config
        if isinstance(config, (MockAdapterConfig, PipelineAdapterConfig)):
            return config.model_revision
        return config.require_revision()

    @property
    def chat_template(self) -> str:
        config = self.backend_config
        if isinstance(config, MockAdapterConfig):
            if self.mock_chat_template is None:
                raise ValueError("Mock planning has no chat template")
            return self.mock_chat_template
        name = (
            config.model.chat_template
            if isinstance(config, PipelineAdapterConfig)
            else config.chat_template
        )
        return name if name.endswith(".txt") else f"{name}.txt"

    @property
    def decoding(self) -> DecodingConfig:
        config = self.backend_config
        if isinstance(config, MockAdapterConfig):
            if self.mock_decoding is None:
                raise ValueError("Mock planning has no decoding recipe")
            return self.mock_decoding
        return (
            config.model.decoding if isinstance(config, PipelineAdapterConfig) else config.decoding
        )

    @property
    def capabilities(self) -> ModelCapabilities:
        return self.backend_config.capabilities

    @property
    def pricing_usd_per_mtok(self) -> PricingConfig:
        config = self.backend_config
        if isinstance(config, MockAdapterConfig):
            return PricingConfig(input=Decimal(0), output=Decimal(0))
        if isinstance(config, PipelineAdapterConfig):
            return config.model.pricing_usd_per_mtok
        return config.pricing_usd_per_mtok

    @property
    def max_input_tokens(self) -> int:
        config = self.backend_config
        if isinstance(config, MockAdapterConfig):
            if self.mock_max_input_tokens is None:
                raise ValueError("Mock planning has no input bound")
            return self.mock_max_input_tokens
        model = config.model if isinstance(config, PipelineAdapterConfig) else config
        return model.context_window - model.decoding.max_tokens

    @property
    def paid(self) -> bool:
        config = self.backend_config
        return isinstance(config, ModelConfig) and config.category == "frontier_api"

    @property
    def mock_response_text(self) -> str:
        config = self.backend_config
        if not isinstance(config, MockAdapterConfig):
            raise TypeError("Only mock planning configs have a fixture response")
        return config.response_text

    @computed_field(return_type=str)
    @property
    def backend_config_hash(self) -> str:
        """Derives identity from every planning backend and pricing field."""
        return compute_planning_backend_hash(self)

    def maximum_request_usd(self) -> Decimal:
        """Returns the configured per-request spend reservation."""
        pricing = self.pricing_usd_per_mtok
        decoding = self.decoding
        return (
            Decimal(self.max_input_tokens) * pricing.input
            + Decimal(decoding.max_tokens) * pricing.output
        ) / Decimal(1_000_000)


class PlanningModels(GenerationConfigModel):
    """Collection of model planning identities."""

    schema_version: SchemaVersion
    models: tuple[PlanningModel, ...]

    @model_validator(mode="after")
    def reject_duplicate_models(self) -> PlanningModels:
        keys = tuple(model.key for model in self.models)
        if len(set(keys)) != len(keys):
            raise ValueError("Planning model keys must be unique")
        if not self.models:
            raise ValueError("At least one planning model is required")
        return self


class SplitPlanningConfig(GenerationConfigModel):
    """Request-count metadata that does not assert benchmark approval."""

    name: NonEmptyString
    status: Literal["proposed", "human_approved", "frozen"]
    theorem_count: int = Field(gt=0)
    theorem_ids: tuple[NonEmptyString, ...] = ()

    @model_validator(mode="after")
    def validate_ids(self) -> SplitPlanningConfig:
        if len(set(self.theorem_ids)) != len(self.theorem_ids):
            raise ValueError("Split theorem IDs must be unique")
        if self.theorem_ids and len(self.theorem_ids) != self.theorem_count:
            raise ValueError("theorem_count must match the listed theorem IDs")
        return self


class SplitPlanningFile(GenerationConfigModel):
    """Collection of named split request-count inputs."""

    schema_version: SchemaVersion
    splits: tuple[SplitPlanningConfig, ...]

    @model_validator(mode="after")
    def reject_duplicate_splits(self) -> SplitPlanningFile:
        names = tuple(split.name for split in self.splits)
        if len(set(names)) != len(names):
            raise ValueError("Split names must be unique")
        return self


def load_condition_matrix(path: Path) -> ConditionMatrix:
    """Loads the strict condition matrix from YAML."""
    return ConditionMatrix.model_validate(_load_yaml_mapping(path))


def load_planning_models(path: Path) -> tuple[PlanningModel, ...]:
    """Loads non-secret model planning identities from YAML."""
    return PlanningModels.model_validate(_load_yaml_mapping(path)).models


def load_splits(path: Path) -> tuple[SplitPlanningConfig, ...]:
    """Loads split request-count metadata from YAML."""
    return SplitPlanningFile.model_validate(_load_yaml_mapping(path)).splits


def _load_yaml_mapping(path: Path) -> dict[str, object]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"Generation config must be a YAML mapping: {path}")
    return raw


def compute_planning_backend_hash(model: PlanningModel) -> str:
    """Returns the canonical hash validated by the live adapter."""
    return compute_adapter_config_hash(model.backend_config)
