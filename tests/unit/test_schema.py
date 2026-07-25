"""Adversarial tests for S1 data-contract validation."""

import math
from copy import deepcopy
from typing import Any

import pytest
from pydantic import ValidationError

from proof_faithfulness.ids import compute_request_id
from proof_faithfulness.schema import (
    BenchmarkDataset,
    BenchmarkRecord,
    GenerationRequest,
    SamplingParameters,
)


def _variant(proof_id: str) -> dict[str, Any]:
    prefix = proof_id.lower()
    first_step = f"{prefix}1"
    second_step = f"{prefix}2"
    return {
        "proof_id": proof_id,
        "informal_proof": f"Complete proof {proof_id}",
        "paraphrase": f"Independent paraphrase {proof_id}",
        "strategy_labels": [f"strategy_{prefix}"],
        "required_signatures": [f"required_{prefix}"],
        "incompatible_signatures": [f"incompatible_{prefix}"],
        "steps": [
            {
                "step_id": first_step,
                "text": "Establish the first fact.",
                "roles": ["strategy_essential"],
            },
            {
                "step_id": second_step,
                "text": "Use the first fact to finish.",
                "roles": ["logically_necessary"],
                "predecessor_step_ids": [first_step],
            },
        ],
        "dependency_edges": [
            {
                "predecessor_step_id": first_step,
                "successor_step_id": second_step,
            }
        ],
    }


def _benchmark() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "theorem_id": "theorem-001",
        "domain": "number theory",
        "difficulty": "elementary",
        "source": {
            "citations": [{"title": "Source", "url": "https://example.test/source"}],
            "adaptation_notes": "Wording adapted for this benchmark.",
        },
        "contamination": {"risk": "medium", "rationale": "A standard exercise."},
        "informal_statement": "A complete theorem statement.",
        "lean": {
            "declaration_name": "theorem_001",
            "declaration": "theorem theorem_001 : True := by trivial",
            "statement_hash": "a" * 64,
            "imports": ["Mathlib"],
            "import_hash": "b" * 64,
            "lean_version": "4.15.0",
            "mathlib_tag": "v4.15.0",
            "mathlib_commit": "c" * 64,
        },
        "proof_variants": [_variant("A"), _variant("B")],
        "split": "pilot",
        "status": "draft",
    }


def test_benchmark_record_accepts_valid_pair() -> None:
    record = BenchmarkRecord.model_validate(_benchmark())
    assert tuple(variant.proof_id for variant in record.proof_variants) == ("A", "B")


def test_benchmark_record_rejects_duplicate_proof_ids() -> None:
    benchmark = _benchmark()
    benchmark["proof_variants"] = [_variant("A"), _variant("A")]
    with pytest.raises(ValidationError, match="exactly IDs A and B"):
        BenchmarkRecord.model_validate(benchmark)


def test_benchmark_record_rejects_dangling_dependency() -> None:
    benchmark = _benchmark()
    variants = benchmark["proof_variants"]
    first_variant = variants[0]
    first_variant["dependency_edges"] = [
        {"predecessor_step_id": "missing", "successor_step_id": "a2"}
    ]
    with pytest.raises(ValidationError, match="exactly match"):
        BenchmarkRecord.model_validate(benchmark)


def test_benchmark_record_rejects_cycle() -> None:
    benchmark = _benchmark()
    variants = benchmark["proof_variants"]
    first_variant = variants[0]
    steps = first_variant["steps"]
    steps[0]["predecessor_step_ids"] = ["a2"]
    first_variant["dependency_edges"] = [
        {"predecessor_step_id": "a2", "successor_step_id": "a1"},
        {"predecessor_step_id": "a1", "successor_step_id": "a2"},
    ]
    with pytest.raises(ValidationError, match="cycle"):
        BenchmarkRecord.model_validate(benchmark)


def test_benchmark_record_rejects_identical_signatures() -> None:
    benchmark = _benchmark()
    variants = benchmark["proof_variants"]
    first_variant = variants[0]
    second_variant = variants[1]
    for key in ("strategy_labels", "required_signatures", "incompatible_signatures"):
        second_variant[key] = deepcopy(first_variant[key])
    with pytest.raises(ValidationError, match="identical strategy signatures"):
        BenchmarkRecord.model_validate(benchmark)


def test_benchmark_record_rejects_reordered_identical_signatures() -> None:
    benchmark = _benchmark()
    variants = benchmark["proof_variants"]
    first_variant = variants[0]
    second_variant = variants[1]
    first_variant["strategy_labels"] = ["shared_1", "shared_2"]
    first_variant["required_signatures"] = ["required_1", "required_2"]
    first_variant["incompatible_signatures"] = ["incompatible_1", "incompatible_2"]
    for key in ("strategy_labels", "required_signatures", "incompatible_signatures"):
        second_variant[key] = list(reversed(first_variant[key]))
    with pytest.raises(ValidationError, match="identical strategy signatures"):
        BenchmarkRecord.model_validate(benchmark)


def test_benchmark_dataset_rejects_duplicate_theorem_ids() -> None:
    record = BenchmarkRecord.model_validate(_benchmark())
    with pytest.raises(ValidationError, match="theorem IDs must be unique"):
        BenchmarkDataset(records=(record, record))


def test_frozen_pilot_requires_reference_proofs() -> None:
    benchmark = _benchmark()
    benchmark["status"] = "frozen"
    with pytest.raises(ValidationError, match="reference Lean proof"):
        BenchmarkRecord.model_validate(benchmark)


def test_lean_spec_rejects_custom_axiom_policy() -> None:
    benchmark = _benchmark()
    benchmark["lean"]["expected_axioms"] = ["User.customAxiom"]
    with pytest.raises(ValidationError, match="fixed trusted-checker policy"):
        BenchmarkRecord.model_validate(benchmark)


def test_generation_request_rejects_mismatched_request_id() -> None:
    sampling = {"temperature": 0.2, "top_p": 1.0, "max_tokens": 8192}
    request = {
        "schema_version": "1.0",
        "theorem_id": "theorem-001",
        "statement_hash": "a" * 64,
        "import_hash": "b" * 64,
        "condition": "proof_a",
        "proof_id": "A",
        "proof_hash": "c" * 64,
        "prompt_name": "preservation",
        "prompt_version": "v1",
        "prompt_hash": "d" * 64,
        "rendered_prompt_hash": "e" * 64,
        "chat_template_hash": "f" * 64,
        "model_adapter": "mock",
        "provider": "local",
        "model_key": "deterministic_mock",
        "model_id": "deterministic-mock",
        "model_revision": "mock-v1",
        "backend_config_hash": "9" * 64,
        "sampling": sampling,
        "sample_index": 0,
        "request_id": "0" * 64,
    }
    with pytest.raises(ValidationError, match="does not match"):
        GenerationRequest.model_validate(request)
    request["request_id"] = compute_request_id(
        schema_version="1.0",
        theorem_id="theorem-001",
        statement_hash="a" * 64,
        import_hash="b" * 64,
        condition="proof_a",
        proof_hash="c" * 64,
        prompt_hash="d" * 64,
        rendered_prompt_hash="e" * 64,
        chat_template_hash="f" * 64,
        model_key="deterministic_mock",
        model_id="deterministic-mock",
        model_revision="mock-v1",
        backend_config_hash="9" * 64,
        sampling={"temperature": 0.2, "top_p": 1.0, "max_tokens": 8192, "seed": None, "extra": []},
        sample_index=0,
    )
    assert GenerationRequest.model_validate(request).request_id == request["request_id"]


def test_generation_request_is_deeply_immutable() -> None:
    sampling = {"temperature": 0.2, "top_p": 1.0, "max_tokens": 8192, "extra": []}
    request_id = compute_request_id(
        schema_version="1.0",
        theorem_id="theorem-001",
        statement_hash="a" * 64,
        import_hash="b" * 64,
        condition="theorem_only",
        proof_hash="c" * 64,
        prompt_hash="d" * 64,
        rendered_prompt_hash="f" * 64,
        chat_template_hash="e" * 64,
        model_key="deterministic_mock",
        model_id="deterministic-mock",
        model_revision="mock-v1",
        backend_config_hash="9" * 64,
        sampling={**sampling, "seed": None},
        sample_index=0,
    )
    request = GenerationRequest.model_validate(
        {
            "schema_version": "1.0",
            "theorem_id": "theorem-001",
            "statement_hash": "a" * 64,
            "import_hash": "b" * 64,
            "condition": "theorem_only",
            "proof_id": None,
            "proof_hash": "c" * 64,
            "prompt_name": "theorem_only",
            "prompt_version": "v1",
            "prompt_hash": "d" * 64,
            "rendered_prompt_hash": "f" * 64,
            "chat_template_hash": "e" * 64,
            "model_adapter": "mock",
            "provider": "local",
            "model_key": "deterministic_mock",
            "model_id": "deterministic-mock",
            "model_revision": "mock-v1",
            "backend_config_hash": "9" * 64,
            "sampling": sampling,
            "sample_index": 0,
            "request_id": request_id,
        }
    )
    assert isinstance(request.sampling.extra, tuple)
    with pytest.raises(ValidationError, match="frozen"):
        request.sampling.temperature = 0.3


def test_sampling_parameters_reject_non_finite_float() -> None:
    with pytest.raises(ValidationError, match="finite number"):
        SamplingParameters(temperature=math.inf, top_p=1.0, max_tokens=8192)
