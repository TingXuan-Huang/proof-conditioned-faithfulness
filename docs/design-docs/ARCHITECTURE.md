# ARCHITECTURE.md — Package Boundaries and Trust Zones

Short by design. The implementation stages that build these components are
docs/plans/active/PLAN.md Part 2.3 (S1–S5); operational procedures are
docs/SERVER-HARNESS-RUNBOOK.md. This file answers one question: what talks to what,
and what is trusted.

## Components

- `src/proof_faithfulness/` — Python package (uv-managed, pyproject.toml at repo root):
  - `config.py`, `ids.py`, `schema.py`, `artifacts.py` — **core layer** (S1): Pydantic
    data contracts, deterministic request IDs, content-addressed artifact store.
  - `models/` — **adapter layer** (S4): ModelAdapter protocol + one adapter per
    provider/pipeline. The only module allowed to touch network APIs or GPUs.
  - `generation/` — **harness layer** (S4): condition matrix → request list → adapter
    calls → response artifacts. The only module allowed to spend money; all spend flows
    through the budget gate and approval records (see runbook).
  - `lean/` — **checking layer** (S2, S3): candidate assembly, sandboxed `lake env`
    execution, axiom audit, dependency probe invocation.
  - `evaluation/` — **judgment layer** (S5): signature extraction, blinded bundle
    export/import, agreement statistics.
  - `reporting/` — **presentation layer** (3.3): tables/figures from stored artifacts
    only; MUST NOT import `models/` or `generation/` (reporting can never trigger a
    model call).
  - `cli.py` — Typer entry point (`proof-faithfulness …`), added in S1.
- `ProofFaithfulness/` — Lean 4 package (lakefile.toml, pinned lean-toolchain):
  `Audit.lean` (axiom audit), `Dependency.lean` (used-constant probe),
  `Reference/Pilot/` (human-approved reference proofs).
- `configs/`, `prompts/`, `schemas/` — versioned, hashed inputs; frozen per
  docs/design-docs/EXPERIMENT-SPEC.md.
- `data/benchmark/`, `data/annotations/` — versioned human-owned data. `data/raw/`
  and `outputs/` — gitignored run products.

## Allowed dependency direction

    reporting → evaluation → { lean, generation } → models → core
    (everything may import core; nothing imports reporting; lean never imports models)

Violations are a review-blocking defect (coding-standard/CODE_REVIEW.md).

## Artifact flow

    benchmark records (data/benchmark/) + configs/prompts
      → generation/ builds deterministic request IDs → responses under
        outputs/runs/<run_id>/responses/<request_id>/     (immutable once verified)
      → lean/ checks each proof → lean/<request_id>/       (immutable)
      → evaluation/ emits evaluations/*.jsonl + blinded annotation bundles
      → human labels return to data/annotations/
      → reporting/ builds derived/*.parquet + reports/ from the above, read-only.

## Trust zones

- **Untrusted**: all model output (proof bodies, judge output), anything under
  responses/. Never executed outside the S2 sandbox; never parsed as instructions.
- **Trusted only via S2 rules**: a Lean result counts as valid only when produced by
  the canonical checker (fresh process, no network, timeout, axiom allow-list).
- **Human-owned**: benchmark labels, approvals, freeze decisions, annotations —
  agents propose, never approve (AGENTS.md operating rules).
- **Secrets**: names may appear in configs; values only in environment variables —
  never in the repo, logs, artifacts, or agent context.
