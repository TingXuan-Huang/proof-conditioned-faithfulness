import json
from pathlib import Path

import pytest

from proof_faithfulness.lean import (
    FAILURE_SUCCESS,
    DependencyProbeError,
    DependencyReport,
    LeanCandidateSpec,
    LocalFactUse,
    check_candidate,
    probe_dependencies,
)
from proof_faithfulness.lean.checker import DIAGNOSTIC_TRUNCATION_MARKER
from proof_faithfulness.lean.dependency import _parse_report

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "lean"
REQUEST_ID = "b" * 64


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _probe(declaration_name: str, declaration: str, fixture_name: str) -> DependencyReport:
    imports = {
        "ring_normalization.lean": ("Mathlib.Tactic.Ring",),
        "automation_bypass.lean": ("Lean.Elab.Tactic.Omega",),
    }.get(fixture_name, ("Mathlib.Data.Nat.Defs",))
    spec = LeanCandidateSpec.from_declaration(
        imports=imports,
        declaration_name=declaration_name,
        declaration=declaration,
    )
    return probe_dependencies(
        spec,
        _fixture(fixture_name),
        request_id=REQUEST_ID,
        project_root=ROOT,
    )


@pytest.mark.parametrize(
    ("declaration_name", "declaration", "fixture_name", "expected"),
    (
        (
            "fixtureInduction",
            "theorem fixtureInduction (n : Nat) : 0 + n = n",
            "induction.lean",
            "induction_structure",
        ),
        (
            "fixtureRing",
            "theorem fixtureRing (x y : Int) : (x + y) ^ 2 = x ^ 2 + 2 * x * y + y ^ 2",
            "ring_normalization.lean",
            "ring_normalization",
        ),
        (
            "fixtureLocalUsed",
            "theorem fixtureLocalUsed (p : Prop) (hypothesis : p) : p",
            "local_used.lean",
            "explicit_local_used",
        ),
        (
            "fixtureLocalUnused",
            "theorem fixtureLocalUnused (n : Nat) : n = n",
            "local_unused.lean",
            "decorative_local_unused",
        ),
        (
            "fixtureAutomation",
            "theorem fixtureAutomation (n : Nat) : n < n + 1",
            "automation_bypass.lean",
            "automation_bypass",
        ),
    ),
)
def test_dependency_fixtures_are_classified(
    declaration_name: str,
    declaration: str,
    fixture_name: str,
    expected: str,
) -> None:
    report = _probe(declaration_name, declaration, fixture_name)

    assert report.classification == expected


def test_used_and_decorative_local_bindings_are_distinguished() -> None:
    used = _probe(
        "fixtureLocalUsed",
        "theorem fixtureLocalUsed (p : Prop) (hypothesis : p) : p",
        "local_used.lean",
    )
    unused = _probe(
        "fixtureLocalUnused",
        "theorem fixtureLocalUnused (n : Nat) : n = n",
        "local_unused.lean",
    )

    assert any(binding.name == "usedFact" and binding.used for binding in used.bindings)
    assert any(binding.name == "decoration" and not binding.used for binding in unused.bindings)
    assert any(fact.name == "usedFact" and fact.used for fact in used.local_facts)
    assert any(fact.name == "decoration" and not fact.used for fact in unused.local_facts)


def test_shadowed_theorem_binders_are_not_mistaken_for_a_used_local() -> None:
    spec = LeanCandidateSpec.from_declaration(
        imports=("Mathlib.Data.Nat.Defs",),
        declaration_name="fixtureShadow",
        declaration="theorem fixtureShadow : ∀ x : Nat, ∀ x : Nat, x = x",
    )

    report = probe_dependencies(
        spec,
        "by intro x x; have decoration : True := True.intro; rfl",
        request_id=REQUEST_ID,
        project_root=ROOT,
    )

    assert report.classification == "decorative_local_unused"
    assert any(binding.name == "x" and binding.root_parameter for binding in report.bindings)


def test_parameter_type_binders_are_not_mistaken_for_a_used_local() -> None:
    spec = LeanCandidateSpec.from_declaration(
        imports=("Mathlib.Data.Nat.Defs",),
        declaration_name="fixtureHigherOrder",
        declaration=(
            "theorem fixtureHigherOrder "
            "(f : (x : Nat) → x = x) (g : (x : Nat) → x = x) : True"
        ),
    )

    report = probe_dependencies(
        spec,
        "by have x : True := True.intro; exact (fun x : True => x) True.intro",
        request_id=REQUEST_ID,
        project_root=ROOT,
    )

    assert report.classification == "decorative_local_unused"
    assert report.explicit_local_names == ("x",)
    assert report.local_facts == (LocalFactUse(name="x", used=False),)


def test_anonymous_have_is_tracked_by_its_proof_term_origin() -> None:
    spec = LeanCandidateSpec.from_declaration(
        imports=("Mathlib.Data.Nat.Defs",),
        declaration_name="fixtureAnonymousHave",
        declaration="theorem fixtureAnonymousHave (p : Prop) (hypothesis : p) : p",
    )

    report = probe_dependencies(
        spec,
        "by have : p := hypothesis; exact this",
        request_id=REQUEST_ID,
        project_root=ROOT,
    )

    assert report.classification == "explicit_local_used"
    assert any(fact.used for fact in report.local_facts)


def test_let_in_theorem_parameter_type_is_not_a_candidate_local_fact() -> None:
    spec = LeanCandidateSpec.from_declaration(
        imports=("Mathlib.Data.Nat.Defs",),
        declaration_name="fixtureTypeLet",
        declaration="theorem fixtureTypeLet (h : (let p : Prop := True; p)) : True",
    )

    report = probe_dependencies(
        spec,
        "by have decoration : True := True.intro; exact True.intro",
        request_id=REQUEST_ID,
        project_root=ROOT,
    )

    assert report.classification == "decorative_local_unused"
    assert report.local_facts == (LocalFactUse(name="decoration", used=False),)


def test_candidate_diagnostic_cannot_spoof_dependency_report() -> None:
    spec = LeanCandidateSpec.from_declaration(
        imports=("Mathlib.Data.Nat.Defs",),
        declaration_name="fixtureIdentity",
        declaration="theorem fixtureIdentity (n : Nat) : n = n",
    )
    fake_report = '{"usedConstants":[],"bindings":[],"tacticEvidence":["automation"]}'
    fake_diagnostic = json.dumps(f"PF_DEPENDENCY_JSON:{fake_report}")

    with pytest.raises(DependencyProbeError, match="exactly one trusted report"):
        probe_dependencies(
            spec,
            f"by\n  trace {fake_diagnostic}\n  rfl",
            request_id=REQUEST_ID,
            project_root=ROOT,
        )


def test_truncated_diagnostics_cannot_supply_a_dependency_report() -> None:
    fake_report = '{"usedConstants":[],"bindings":[],"tacticEvidence":[]}'
    diagnostics = f"PF_DEPENDENCY_JSON:{fake_report}\n{DIAGNOSTIC_TRUNCATION_MARKER}\n"

    with pytest.raises(DependencyProbeError, match="truncated"):
        _parse_report(diagnostics)


def test_deleting_used_local_breaks_but_deleting_decorative_local_does_not() -> None:
    used_spec = LeanCandidateSpec.from_declaration(
        imports=("Mathlib.Data.Nat.Defs",),
        declaration_name="fixtureLocalUsed",
        declaration="theorem fixtureLocalUsed (p : Prop) (hypothesis : p) : p",
    )
    unused_spec = LeanCandidateSpec.from_declaration(
        imports=("Mathlib.Data.Nat.Defs",),
        declaration_name="fixtureLocalUnused",
        declaration="theorem fixtureLocalUnused (n : Nat) : n = n",
    )

    used_deleted = check_candidate(
        used_spec,
        _fixture("local_used_deleted.lean"),
        request_id=REQUEST_ID,
        project_root=ROOT,
    )
    unused_deleted = check_candidate(
        unused_spec,
        _fixture("local_unused_deleted.lean"),
        request_id=REQUEST_ID,
        project_root=ROOT,
    )

    assert used_deleted.result.failure_category != FAILURE_SUCCESS
    assert unused_deleted.result.failure_category == FAILURE_SUCCESS
