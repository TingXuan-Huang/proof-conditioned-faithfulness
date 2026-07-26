"""Fail-closed execution boundary for untrusted Lean proof candidates."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from proof_faithfulness.schema import FIXED_ALLOWED_AXIOMS, LeanCheckResult

FAILURE_SUCCESS = "success"
FAILURE_MULTIPLE_BLOCKS = "multiple_blocks"
FAILURE_EXTRACTION = "extraction_invalid"
FAILURE_STATEMENT_CHANGED = "statement_changed"
FAILURE_PROHIBITED_SORRY = "prohibited_sorry"
FAILURE_PROHIBITED_AXIOM = "prohibited_axiom"
FAILURE_TRUST_BYPASS = "trust_bypass"
FAILURE_SYNTAX = "syntax_invalid"
FAILURE_TYPE = "type_invalid"
FAILURE_TIMEOUT = "timeout"
FAILURE_AXIOM_AUDIT = "axiom_audit_failed"
FAILURE_SANDBOX = "sandbox_error"

DEFAULT_TIMEOUT_SECONDS = 600.0
DEFAULT_WARMUP_TIMEOUT_SECONDS = 1200.0
DEFAULT_MEMORY_LIMIT_MB = 4096
DEFAULT_MAX_HEARTBEATS = 2_000_000
MAX_DIAGNOSTIC_BYTES = 1_048_576
DIAGNOSTIC_TRUNCATION_MARKER = "[diagnostic output truncated]"

_HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_LEAN_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*$")
_FULL_DECLARATION_PATTERN = re.compile(r"^(?:theorem|lemma)\b")
_FENCE_PATTERN = re.compile(r"```(?:lean|Lean)?[ \t]*\r?\n(.*?)```", re.DOTALL)
_ASSIGNMENT_PATTERN = re.compile(r":=")
_AXIOM_PATTERN = re.compile(r"PF_AXIOMS_JSON:(\[[^\r\n]*\])")
_SYNTAX_MARKERS = (
    "candidate is not exactly one lean term",
    "unexpected end of input",
    "unexpected token",
    "unexpected identifier",
    "invalid syntax",
    "unterminated",
)

_PROHIBITED_GROUPS = (
    (FAILURE_PROHIBITED_SORRY, ("sorry", "admit", "sorryAx")),
    (FAILURE_PROHIBITED_AXIOM, ("axiom",)),
    (
        FAILURE_TRUST_BYPASS,
        (
            "unsafe",
            "native",
            "native_decide",
            "run_tac",
            "implemented_by",
            "extern",
            "extract_lets",
            "evalTactic",
            "set_option",
            "macro",
            "elab",
            "syntax",
            "def",
            "example",
            "instance",
            "inductive",
            "structure",
            "class",
            "abbrev",
            "mutual",
            "where",
            "private",
            "protected",
            "noncomputable",
            "variable",
            "universe",
            "termination_by",
            "decreasing_by",
            "namespace",
            "section",
            "end",
            "open",
            "attribute",
            "local",
            "scoped",
            "export",
            "initialize",
            "eval",
            "check",
            "print",
            "reduce",
            "import",
            "theorem",
            "lemma",
            "opaque",
        ),
    ),
)


@dataclass(frozen=True)
class LeanCandidateSpec:
    """Trusted statement metadata used to assemble one candidate file."""

    imports: tuple[str, ...]
    declaration_name: str
    declaration: str
    statement_hash: str

    def __post_init__(self) -> None:
        if not self.imports:
            raise ValueError("At least one canonical Lean import is required")
        if len(set(self.imports)) != len(self.imports):
            raise ValueError("Canonical Lean imports must be unique")
        for module_name in self.imports:
            if _LEAN_NAME_PATTERN.fullmatch(module_name) is None:
                raise ValueError(f"Invalid Lean module name: {module_name!r}")
        if _LEAN_NAME_PATTERN.fullmatch(self.declaration_name) is None:
            raise ValueError(f"Invalid Lean declaration name: {self.declaration_name!r}")
        declaration = self.declaration.strip()
        expected_prefix = re.compile(
            rf"^(?:theorem|lemma)\s+{re.escape(self.declaration_name)}(?:\s|\(|\{{|\[|:)"
        )
        if expected_prefix.search(declaration) is None:
            raise ValueError("Canonical declaration name does not match declaration text")
        if _HASH_PATTERN.fullmatch(self.statement_hash) is None:
            raise ValueError("Statement hash must be a lowercase SHA-256 digest")
        if hash_lean_statement(declaration) != self.statement_hash:
            raise ValueError("Statement hash does not match the canonical declaration")

    @classmethod
    def from_declaration(
        cls,
        *,
        imports: tuple[str, ...],
        declaration_name: str,
        declaration: str,
    ) -> LeanCandidateSpec:
        """Build trusted metadata while deriving its normalized statement hash."""
        return cls(
            imports=imports,
            declaration_name=declaration_name,
            declaration=declaration,
            statement_hash=hash_lean_statement(declaration),
        )


@dataclass(frozen=True)
class CheckOutcome:
    """A normalized check result plus bounded compiler diagnostics."""

    result: LeanCheckResult
    stdout: str
    stderr: str
    assembled_source: str | None


@dataclass(frozen=True)
class LeanWarmupResult:
    """Bounded result of loading the fixed trusted Lean/Mathlib environment."""

    exit_code: int | None
    stdout: str
    stderr: str
    wall_time_seconds: float
    timed_out: bool = False
    setup_error: str | None = None

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out and self.setup_error is None


@dataclass(frozen=True)
class _ExtractedCandidate:
    status: str
    body: str | None
    statement_hash_matches: bool
    prohibited_findings: tuple[str, ...] = ()


@dataclass(frozen=True)
class _ExecutionResult:
    exit_code: int | None
    stdout: str
    stderr: str
    wall_time_seconds: float
    timed_out: bool = False
    setup_error: str | None = None


def hash_lean_statement(declaration: str) -> str:
    """Hash a declaration after deterministic line-ending/whitespace normalization."""
    normalized = _normalize_declaration(declaration)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def check_candidate(
    spec: LeanCandidateSpec,
    model_output: str,
    *,
    request_id: str,
    project_root: Path | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB,
    max_heartbeats: int = DEFAULT_MAX_HEARTBEATS,
) -> CheckOutcome:
    """Compile and axiom-audit one untrusted candidate in a fresh process.

    The child process receives a finite heartbeat budget, a wall-clock timeout,
    an address-space limit, and a seccomp filter denying all socket syscalls.
    Compiler output is bounded before it crosses back into the harness process.
    """
    _validate_execution_parameters(
        request_id=request_id,
        timeout_seconds=timeout_seconds,
        memory_limit_mb=memory_limit_mb,
        max_heartbeats=max_heartbeats,
    )
    started = time.monotonic()
    extracted = _extract_candidate(spec, model_output)
    if extracted.body is None:
        return _preflight_outcome(
            request_id=request_id,
            extracted=extracted,
            wall_time_seconds=time.monotonic() - started,
        )

    source = _assemble_source(spec, extracted.body)
    root = project_root if project_root is not None else Path(__file__).resolve().parents[3]
    with tempfile.TemporaryDirectory(prefix="proof-faithfulness-lean-") as temporary:
        source_path = Path(temporary) / "Candidate.lean"
        source_path.write_text(source, encoding="utf-8", newline="\n")
        lake = shutil.which("lake")
        if lake is None:
            execution = _ExecutionResult(
                exit_code=None,
                stdout="",
                stderr="",
                wall_time_seconds=time.monotonic() - started,
                setup_error="lake executable was not found",
            )
        else:
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
    return _execution_outcome(
        request_id=request_id,
        extracted=extracted,
        execution=execution,
        source=source,
    )


def warm_mathlib_cache(
    *,
    project_root: Path | None = None,
    timeout_seconds: float = DEFAULT_WARMUP_TIMEOUT_SECONDS,
    memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB,
    max_heartbeats: int = DEFAULT_MAX_HEARTBEATS,
) -> LeanWarmupResult:
    """Load the fixed trusted Lean environment once before a batch of checks.

    This operation never includes model output. It uses the ordinary network-isolated,
    resource-bounded Lean subprocess so a cold filesystem cache cannot hang preflight.
    Candidate checks remain fresh processes with an independent 600-second limit.
    """
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("Warm-up timeout must be finite and positive")
    if memory_limit_mb <= 0:
        raise ValueError("Warm-up memory limit must be positive")
    if max_heartbeats <= 0:
        raise ValueError("Warm-up maxHeartbeats must be finite and positive")
    started = time.monotonic()
    lake = shutil.which("lake")
    if lake is None:
        return LeanWarmupResult(
            exit_code=None,
            stdout="",
            stderr="",
            wall_time_seconds=time.monotonic() - started,
            setup_error="lake executable was not found",
        )
    root = project_root if project_root is not None else Path(__file__).resolve().parents[3]
    source = (
        "import Mathlib\n"
        "import ProofFaithfulness.Audit\n"
        "#check ProofFaithfulness.Audit.parseCandidateTerm\n"
    )
    with tempfile.TemporaryDirectory(prefix="proof-faithfulness-warmup-") as temporary:
        source_path = Path(temporary) / "Warmup.lean"
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
    return LeanWarmupResult(
        exit_code=execution.exit_code,
        stdout=execution.stdout,
        stderr=execution.stderr,
        wall_time_seconds=execution.wall_time_seconds,
        timed_out=execution.timed_out,
        setup_error=execution.setup_error,
    )


def network_isolation_probe() -> bool:
    """Return whether the production child sandbox actually denies socket creation."""
    probe = (
        "import errno, socket, sys\n"
        "try:\n"
        "    socket.socket()\n"
        "except PermissionError as error:\n"
        "    if error.errno == errno.EPERM:\n"
        "        print('PF_NETWORK_BLOCKED')\n"
        "        sys.exit(0)\n"
        "sys.exit(7)\n"
    )
    execution = _execute_sandboxed(
        [sys.executable, "-c", probe],
        cwd=Path.cwd(),
        timeout_seconds=5.0,
        memory_limit_mb=256,
    )
    return (
        execution.exit_code == 0
        and execution.stdout.strip() == "PF_NETWORK_BLOCKED"
        and execution.setup_error is None
    )


def _validate_execution_parameters(
    *,
    request_id: str,
    timeout_seconds: float,
    memory_limit_mb: int,
    max_heartbeats: int,
) -> None:
    if _HASH_PATTERN.fullmatch(request_id) is None:
        raise ValueError("Request ID must be a lowercase SHA-256 digest")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("Timeout must be finite and positive")
    if memory_limit_mb <= 0:
        raise ValueError("Memory limit must be positive")
    if max_heartbeats <= 0:
        raise ValueError("Lean maxHeartbeats must be finite and positive")


def _normalize_declaration(declaration: str) -> str:
    normalized_newlines = declaration.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized_newlines.strip().split("\n")]
    return "\n".join(lines)


def _extract_candidate(spec: LeanCandidateSpec, model_output: str) -> _ExtractedCandidate:
    fenced_blocks = _FENCE_PATTERN.findall(model_output)
    if len(fenced_blocks) > 1:
        return _ExtractedCandidate(FAILURE_MULTIPLE_BLOCKS, None, True)
    if len(fenced_blocks) == 1:
        candidate = fenced_blocks[0].strip()
    elif "```" in model_output:
        return _ExtractedCandidate(FAILURE_EXTRACTION, None, True)
    else:
        candidate = model_output.strip()
    if not candidate:
        return _ExtractedCandidate(FAILURE_EXTRACTION, None, True)

    statement_matches = True
    body = candidate
    if _FULL_DECLARATION_PATTERN.match(candidate):
        matching_declarations = [
            candidate[assignment.end() :].strip()
            for assignment in _ASSIGNMENT_PATTERN.finditer(candidate)
            if hash_lean_statement(candidate[: assignment.start()].strip()) == spec.statement_hash
        ]
        if len(matching_declarations) != 1:
            return _ExtractedCandidate(FAILURE_STATEMENT_CHANGED, None, False)
        body = matching_declarations[0]
        if not body:
            return _ExtractedCandidate(FAILURE_EXTRACTION, None, True)

    findings = _find_prohibited_tokens(body)
    if findings:
        category = findings[0].split(":", maxsplit=1)[0]
        return _ExtractedCandidate(category, None, statement_matches, findings)
    return _ExtractedCandidate("success", body, statement_matches)


def _find_prohibited_tokens(source: str) -> tuple[str, ...]:
    scanned = _strip_comments_and_strings(source)
    findings: list[str] = []
    for category, tokens in _PROHIBITED_GROUPS:
        for token in tokens:
            if re.search(rf"(?<![A-Za-z0-9_']){re.escape(token)}(?![A-Za-z0-9_'])", scanned):
                findings.append(f"{category}:{token}")
    return tuple(findings)


def _strip_comments_and_strings(source: str) -> str:
    output: list[str] = []
    i = 0
    block_depth = 0
    in_string = False
    while i < len(source):
        pair = source[i : i + 2]
        if block_depth:
            if pair == "/-":
                block_depth += 1
                output.extend("  ")
                i += 2
            elif pair == "-/":
                block_depth -= 1
                output.extend("  ")
                i += 2
            else:
                output.append("\n" if source[i] == "\n" else " ")
                i += 1
        elif in_string:
            if source[i] == "\\" and i + 1 < len(source):
                output.extend("  ")
                i += 2
            elif source[i] == '"':
                in_string = False
                output.append(" ")
                i += 1
            else:
                output.append("\n" if source[i] == "\n" else " ")
                i += 1
        elif pair == "--":
            newline = source.find("\n", i + 2)
            if newline == -1:
                output.extend(" " * (len(source) - i))
                break
            output.extend(" " * (newline - i))
            output.append("\n")
            i = newline + 1
        elif pair == "/-":
            block_depth = 1
            output.extend("  ")
            i += 2
        elif source[i] == '"':
            in_string = True
            output.append(" ")
            i += 1
        else:
            output.append(source[i])
            i += 1
    return "".join(output)


def _assemble_source(spec: LeanCandidateSpec, body: str) -> str:
    proof_term = _lean_string_literal(body.strip())
    import_modules = (*spec.imports, "ProofFaithfulness.Audit")
    imports = "\n".join(f"import {module}" for module in dict.fromkeys(import_modules))
    return (
        f"{imports}\n\n"
        f"{spec.declaration.strip()} := pf_checked_candidate% {proof_term}\n\n"
        f"#proof_axioms {spec.declaration_name}\n"
    )


def _lean_string_literal(value: str) -> str:
    """Encode untrusted source as data accepted by Lean's string-literal parser."""
    return json.dumps(value, ensure_ascii=False)


def _preflight_outcome(
    *,
    request_id: str,
    extracted: _ExtractedCandidate,
    wall_time_seconds: float,
) -> CheckOutcome:
    result = LeanCheckResult(
        schema_version="1.0",
        request_id=request_id,
        statement_hash_matches=extracted.statement_hash_matches,
        extraction_status=extracted.status,
        parser_status="not_run",
        elaboration_status="not_run",
        exit_code=None,
        wall_time_seconds=wall_time_seconds,
        axioms=(),
        prohibited_token_findings=extracted.prohibited_findings,
        failure_category=extracted.status,
    )
    return CheckOutcome(result=result, stdout="", stderr="", assembled_source=None)


def _execution_outcome(
    *,
    request_id: str,
    extracted: _ExtractedCandidate,
    execution: _ExecutionResult,
    source: str,
) -> CheckOutcome:
    diagnostics = f"{execution.stdout}\n{execution.stderr}"
    if execution.setup_error is not None or execution.exit_code == 126:
        category = FAILURE_SANDBOX
        parser_status = "not_run"
        elaboration_status = "not_run"
        axioms: tuple[str, ...] = ()
    elif execution.timed_out:
        category = FAILURE_TIMEOUT
        parser_status = "unknown"
        elaboration_status = "timeout"
        axioms = ()
    elif execution.exit_code != 0:
        category = _classify_compiler_failure(diagnostics)
        parser_status = "failed" if category == FAILURE_SYNTAX else "success"
        elaboration_status = "not_run" if category == FAILURE_SYNTAX else "failed"
        axioms = ()
    else:
        parsed_axioms = _parse_axioms(diagnostics)
        if parsed_axioms is None:
            category = FAILURE_AXIOM_AUDIT
            axioms = ()
        else:
            axioms = parsed_axioms
            unexpected_axioms = set(axioms) - set(FIXED_ALLOWED_AXIOMS)
            category = FAILURE_PROHIBITED_AXIOM if unexpected_axioms else FAILURE_SUCCESS
        parser_status = "success"
        elaboration_status = "success"
    result = LeanCheckResult(
        schema_version="1.0",
        request_id=request_id,
        statement_hash_matches=extracted.statement_hash_matches,
        extraction_status=extracted.status,
        parser_status=parser_status,
        elaboration_status=elaboration_status,
        exit_code=execution.exit_code,
        wall_time_seconds=execution.wall_time_seconds,
        axioms=axioms,
        prohibited_token_findings=extracted.prohibited_findings,
        failure_category=category,
    )
    return CheckOutcome(
        result=result,
        stdout=execution.stdout,
        stderr=execution.stderr,
        assembled_source=source,
    )


def _classify_compiler_failure(diagnostics: str) -> str:
    lowered = diagnostics.lower()
    if any(marker in lowered for marker in _SYNTAX_MARKERS):
        return FAILURE_SYNTAX
    return FAILURE_TYPE


def _parse_axioms(diagnostics: str) -> tuple[str, ...] | None:
    if DIAGNOSTIC_TRUNCATION_MARKER in diagnostics:
        return None
    matches = _AXIOM_PATTERN.findall(diagnostics)
    if len(matches) != 1:
        return None
    try:
        names = json.loads(matches[0])
    except json.JSONDecodeError:
        return None
    if not isinstance(names, list) or any(not isinstance(name, str) for name in names):
        return None
    return tuple(sorted(names))


def _execute_sandboxed(
    command: list[str],
    *,
    cwd: Path,
    timeout_seconds: float,
    memory_limit_mb: int,
) -> _ExecutionResult:
    started = time.monotonic()
    environment = _child_environment()
    sandbox_command = [
        sys.executable,
        "-m",
        "proof_faithfulness.lean.sandbox",
        str(timeout_seconds),
        str(memory_limit_mb),
        "--",
        *command,
    ]
    try:
        with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
            process = subprocess.Popen(
                sandbox_command,
                cwd=cwd,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout_file,
                stderr=stderr_file,
                start_new_session=True,
            )
            timed_out = False
            try:
                process.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
            finally:
                _terminate_process_group(process.pid)
                process.wait()
            stdout = _read_bounded(stdout_file)
            stderr = _read_bounded(stderr_file)
    except (OSError, subprocess.SubprocessError) as error:
        return _ExecutionResult(
            exit_code=None,
            stdout="",
            stderr="",
            wall_time_seconds=time.monotonic() - started,
            setup_error=f"{type(error).__name__}: {error}",
        )
    return _ExecutionResult(
        exit_code=process.returncode,
        stdout=stdout,
        stderr=stderr,
        wall_time_seconds=time.monotonic() - started,
        timed_out=timed_out,
    )


def _terminate_process_group(process_id: int) -> None:
    """Kill the dedicated child session so no compiler descendants survive a check."""
    try:
        os.killpg(process_id, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _child_environment() -> dict[str, str]:
    allowed_names = (
        "ELAN_HOME",
        "HOME",
        "LANG",
        "LC_ALL",
        "LD_LIBRARY_PATH",
        "LIBRARY_PATH",
        "PATH",
        "TMPDIR",
    )
    return {name: os.environ[name] for name in allowed_names if name in os.environ}


def _read_bounded(file_object: object) -> str:
    file_object.seek(0)  # type: ignore[attr-defined]
    content = file_object.read(MAX_DIAGNOSTIC_BYTES + 1)  # type: ignore[attr-defined]
    if len(content) > MAX_DIAGNOSTIC_BYTES:
        marker = DIAGNOSTIC_TRUNCATION_MARKER.encode("ascii")
        content = content[:MAX_DIAGNOSTIC_BYTES] + b"\n" + marker + b"\n"
    return content.decode("utf-8", errors="replace")
