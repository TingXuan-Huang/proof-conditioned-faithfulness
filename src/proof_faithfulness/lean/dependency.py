"""Invoke the Lean proof-term dependency probe and normalize its report."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from proof_faithfulness.lean.checker import (
    DEFAULT_MAX_HEARTBEATS,
    DEFAULT_MEMORY_LIMIT_MB,
    DEFAULT_TIMEOUT_SECONDS,
    DIAGNOSTIC_TRUNCATION_MARKER,
    FAILURE_SUCCESS,
    LeanCandidateSpec,
    _assemble_source,
    _execute_sandboxed,
    _extract_candidate,
    _lean_string_literal,
    check_candidate,
)

DependencyClassification = Literal[
    "induction_structure",
    "ring_normalization",
    "explicit_local_used",
    "decorative_local_unused",
    "automation_bypass",
    "unresolved",
]

_REPORT_PATTERN = re.compile(r"PF_DEPENDENCY_JSON:(\{[^\r\n]*\})")


class DependencyProbeError(RuntimeError):
    """The candidate was untrusted or its dependency report was unavailable."""


@dataclass(frozen=True)
class BindingUse:
    """One elaborated lambda, forall, or let binding and whether its body uses it."""

    name: str
    kind: Literal["forall", "lambda", "let"]
    used: bool
    root_parameter: bool


@dataclass(frozen=True)
class LocalFactUse:
    """One proof-term let/let_fun introduced by an explicit local tactic."""

    name: str
    used: bool


@dataclass(frozen=True)
class DependencyReport:
    """Machine-readable proof-term and tactic-syntax dependency evidence."""

    used_constants: tuple[str, ...]
    bindings: tuple[BindingUse, ...]
    local_facts: tuple[LocalFactUse, ...]
    tactic_evidence: tuple[str, ...]
    explicit_local_names: tuple[str, ...]
    classification: DependencyClassification


def probe_dependencies(
    spec: LeanCandidateSpec,
    model_output: str,
    *,
    request_id: str,
    project_root: Path | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB,
    max_heartbeats: int = DEFAULT_MAX_HEARTBEATS,
) -> DependencyReport:
    """Trust-check a candidate, then inspect dependencies in a second fresh process."""
    root = project_root if project_root is not None else Path(__file__).resolve().parents[3]
    check = check_candidate(
        spec,
        model_output,
        request_id=request_id,
        project_root=root,
        timeout_seconds=timeout_seconds,
        memory_limit_mb=memory_limit_mb,
        max_heartbeats=max_heartbeats,
    )
    if check.result.failure_category != FAILURE_SUCCESS:
        raise DependencyProbeError(
            f"Candidate did not pass the trusted checker: {check.result.failure_category}"
        )
    extracted = _extract_candidate(spec, model_output)
    if extracted.body is None:
        raise DependencyProbeError("Candidate extraction unexpectedly failed after trusted check")
    source = _assemble_dependency_source(spec, extracted.body)
    lake = shutil.which("lake")
    if lake is None:
        raise DependencyProbeError("lake executable was not found")
    with tempfile.TemporaryDirectory(prefix="proof-faithfulness-dependency-") as temporary:
        source_path = Path(temporary) / "DependencyCandidate.lean"
        source_path.write_text(source, encoding="utf-8", newline="\n")
        execution = _execute_sandboxed(
            [
                lake,
                "env",
                "lean",
                f"-DmaxHeartbeats={max_heartbeats}",
                str(source_path),
            ],
            cwd=root,
            timeout_seconds=timeout_seconds,
            memory_limit_mb=memory_limit_mb,
        )
    if execution.setup_error is not None:
        raise DependencyProbeError(f"Dependency sandbox failed: {execution.setup_error}")
    if execution.timed_out:
        raise DependencyProbeError("Dependency probe timed out")
    if execution.exit_code != 0:
        diagnostic = (execution.stderr or execution.stdout).strip()
        raise DependencyProbeError(f"Dependency probe failed: {diagnostic}")
    return _parse_report(f"{execution.stdout}\n{execution.stderr}")


def _assemble_dependency_source(spec: LeanCandidateSpec, body: str) -> str:
    base = _assemble_source(spec, body)
    lines = base.splitlines()
    lines = [line for line in lines if not line.startswith("#proof_axioms ")]
    if "ProofFaithfulness.Dependency" not in spec.imports:
        lines.insert(len(spec.imports), "import ProofFaithfulness.Dependency")
    lines.extend(
        (
            "",
            f"#proof_dependency {spec.declaration_name} {_lean_string_literal(body)}",
            "",
        )
    )
    return "\n".join(lines)


def _parse_report(diagnostics: str) -> DependencyReport:
    if DIAGNOSTIC_TRUNCATION_MARKER in diagnostics:
        raise DependencyProbeError("Dependency probe diagnostics were truncated")
    matches = _REPORT_PATTERN.findall(diagnostics)
    if len(matches) != 1:
        raise DependencyProbeError("Dependency probe must emit exactly one trusted report marker")
    try:
        payload = json.loads(matches[0])
        bindings = tuple(
            BindingUse(
                name=item["name"],
                kind=item["kind"],
                used=item["used"],
                root_parameter=item["rootParameter"],
            )
            for item in payload["bindings"]
        )
        local_facts = tuple(
            LocalFactUse(name=item["name"], used=item["used"])
            for item in payload["localFacts"]
        )
        used_constants = tuple(payload["usedConstants"])
        tactic_evidence = tuple(payload["tacticEvidence"])
        explicit_local_names = tuple(payload["explicitLocalNames"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise DependencyProbeError("Dependency probe emitted an invalid report") from error
    return DependencyReport(
        used_constants=used_constants,
        bindings=bindings,
        local_facts=local_facts,
        tactic_evidence=tactic_evidence,
        explicit_local_names=explicit_local_names,
        classification=_classify(tactic_evidence, local_facts),
    )


def _classify(
    tactic_evidence: tuple[str, ...],
    local_facts: tuple[LocalFactUse, ...],
) -> DependencyClassification:
    evidence = set(tactic_evidence)
    if "automation" in evidence:
        return "automation_bypass"
    if "induction" in evidence:
        return "induction_structure"
    if "ring_normalization" in evidence:
        return "ring_normalization"
    if "explicit_local" in evidence:
        if not local_facts:
            return "unresolved"
        if any(fact.used for fact in local_facts):
            return "explicit_local_used"
        return "decorative_local_unused"
    return "unresolved"
