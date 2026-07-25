from pathlib import Path

from proof_faithfulness.lean import (
    FAILURE_AXIOM_AUDIT,
    FAILURE_MULTIPLE_BLOCKS,
    FAILURE_PROHIBITED_AXIOM,
    FAILURE_PROHIBITED_SORRY,
    FAILURE_STATEMENT_CHANGED,
    FAILURE_SUCCESS,
    FAILURE_SYNTAX,
    FAILURE_TIMEOUT,
    FAILURE_TRUST_BYPASS,
    FAILURE_TYPE,
    LeanCandidateSpec,
    check_candidate,
    network_isolation_probe,
)
from proof_faithfulness.lean.checker import DIAGNOSTIC_TRUNCATION_MARKER, _parse_axioms

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "lean"
REQUEST_ID = "a" * 64


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _identity_spec(
    *,
    imports: tuple[str, ...] = ("Mathlib.Data.Nat.Defs",),
) -> LeanCandidateSpec:
    return LeanCandidateSpec.from_declaration(
        imports=imports,
        declaration_name="fixtureIdentity",
        declaration="theorem fixtureIdentity (n : Nat) : n = n",
    )


def _check(
    spec: LeanCandidateSpec,
    fixture_name: str,
    *,
    timeout_seconds: float = 120.0,
):
    return check_candidate(
        spec,
        _fixture(fixture_name),
        request_id=REQUEST_ID,
        project_root=ROOT,
        timeout_seconds=timeout_seconds,
    )


def test_valid_fixture_has_exact_success_category() -> None:
    outcome = _check(_identity_spec(), "valid.lean")

    assert outcome.result.failure_category == FAILURE_SUCCESS
    assert outcome.result.statement_hash_matches
    assert outcome.result.axioms == ()


def test_term_proof_body_is_assembled_without_rewriting() -> None:
    outcome = _check(_identity_spec(), "term_body.lean")

    assert outcome.result.failure_category == FAILURE_SUCCESS
    assert outcome.assembled_source is not None
    assert (
        'theorem fixtureIdentity (n : Nat) : n = n := pf_checked_candidate% "rfl"'
        in outcome.assembled_source
    )


def test_syntax_invalid_fixture_has_exact_category() -> None:
    outcome = _check(_identity_spec(), "syntax_invalid.lean")

    assert outcome.result.failure_category == FAILURE_SYNTAX


def test_type_invalid_fixture_has_exact_category() -> None:
    outcome = _check(_identity_spec(), "type_invalid.lean")

    assert outcome.result.failure_category == FAILURE_TYPE


def test_timeout_fixture_has_exact_category() -> None:
    outcome = _check(_identity_spec(), "timeout.lean", timeout_seconds=0.001)

    assert outcome.result.failure_category == FAILURE_TIMEOUT


def test_statement_changed_fixture_has_exact_category_without_execution() -> None:
    outcome = _check(_identity_spec(), "statement_changed.lean")

    assert outcome.result.failure_category == FAILURE_STATEMENT_CHANGED
    assert not outcome.result.statement_hash_matches
    assert outcome.result.exit_code is None


def test_sorry_fixture_is_rejected_with_exact_category() -> None:
    outcome = _check(_identity_spec(), "sorry.lean")

    assert outcome.result.failure_category == FAILURE_PROHIBITED_SORRY
    assert outcome.result.prohibited_token_findings == ("prohibited_sorry:sorry",)


def test_native_trust_bypass_fixture_is_rejected_without_execution() -> None:
    outcome = _check(_identity_spec(), "native_bypass.lean")

    assert outcome.result.failure_category == FAILURE_TRUST_BYPASS
    assert outcome.result.exit_code is None


def test_candidate_must_be_exactly_one_term_and_cannot_append_a_command() -> None:
    outcome = _check(_identity_spec(), "trailing_command.lean")

    assert outcome.result.failure_category == FAILURE_SYNTAX
    assert "PF_UNTRUSTED_COMMAND_EXECUTED" not in outcome.stdout
    assert "PF_UNTRUSTED_COMMAND_EXECUTED" not in outcome.stderr
    assert outcome.assembled_source is not None
    assert "\nrun_cmd" not in outcome.assembled_source


def test_custom_axiom_fixture_is_rejected_by_transitive_audit() -> None:
    spec = LeanCandidateSpec.from_declaration(
        imports=("ProofFaithfulnessTest.CustomAxiom",),
        declaration_name="fixtureContradiction",
        declaration="theorem fixtureContradiction : False",
    )
    outcome = _check(spec, "custom_axiom.lean")

    assert outcome.result.failure_category == FAILURE_PROHIBITED_AXIOM
    assert outcome.result.axioms == ("fixtureFalse",)


def test_candidate_diagnostic_cannot_spoof_the_axiom_audit() -> None:
    spec = LeanCandidateSpec.from_declaration(
        imports=("ProofFaithfulnessTest.CustomAxiom",),
        declaration_name="fixtureContradiction",
        declaration="theorem fixtureContradiction : False",
    )
    outcome = check_candidate(
        spec,
        'by\n  trace "fixtureContradiction depends on axioms: [Classical.choice]"\n'
        "  exact fixtureFalse",
        request_id=REQUEST_ID,
        project_root=ROOT,
    )

    assert outcome.result.failure_category == FAILURE_PROHIBITED_AXIOM
    assert outcome.result.axioms == ("fixtureFalse",)


def test_duplicate_trusted_axiom_marker_fails_closed() -> None:
    outcome = check_candidate(
        _identity_spec(),
        'by\n  trace "PF_AXIOMS_JSON:[]"\n  rfl',
        request_id=REQUEST_ID,
        project_root=ROOT,
    )

    assert outcome.result.failure_category == FAILURE_AXIOM_AUDIT


def test_truncated_diagnostics_cannot_supply_an_axiom_report() -> None:
    diagnostics = f"PF_AXIOMS_JSON:[]\n{DIAGNOSTIC_TRUNCATION_MARKER}\n"

    assert _parse_axioms(diagnostics) is None


def test_multiple_blocks_fixture_has_exact_category_without_execution() -> None:
    outcome = _check(_identity_spec(), "multiple_blocks.md")

    assert outcome.result.failure_category == FAILURE_MULTIPLE_BLOCKS
    assert outcome.result.exit_code is None


def test_allowed_classical_fixture_passes_with_fixed_axiom() -> None:
    spec = LeanCandidateSpec.from_declaration(
        imports=("Mathlib.Data.Nat.Defs",),
        declaration_name="fixtureClassical",
        declaration="theorem fixtureClassical (p : Prop) : p ∨ ¬p",
    )
    outcome = _check(spec, "allowed_classical.lean")

    assert outcome.result.failure_category == FAILURE_SUCCESS
    assert set(outcome.result.axioms) <= {"propext", "Classical.choice", "Quot.sound"}
    assert "Classical.choice" in outcome.result.axioms


def test_exact_full_declaration_is_accepted() -> None:
    outcome = _check(_identity_spec(), "full_declaration.lean")

    assert outcome.result.failure_category == FAILURE_SUCCESS
    assert outcome.result.statement_hash_matches


def test_child_sandbox_actually_denies_socket_syscalls() -> None:
    assert network_isolation_probe()
