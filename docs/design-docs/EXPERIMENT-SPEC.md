# EXPERIMENT-SPEC.md — Frozen Experimental Parameters

Status: **STUB — nothing here is frozen yet.** Until each section's freeze gate passes,
the normative source is docs/plans/active/PLAN.md and
docs/design-docs/analysis-decisions-pending.md. This file exists now (2026-07-24) so
freezes have a designated home and the machine-readable manifest has a human-readable
mirror; it is filled in stages, each section at its own gate, never earlier.

Mirroring rule: every value recorded here must correspond 1:1 to the machine-readable
manifest (configs/experiment/*.yaml, and at core time
outputs/runs/<run_id>/manifest.json). If they ever disagree, that is a release-blocking
defect. Freezing a section means: values written here, mirrored in configs, both
committed, and the section header changed from PENDING to FROZEN with date + approver
(always the human — agents propose, never freeze).

## 1. Benchmark records — PENDING (freeze gate: core freeze, PLAN.md 2.6)

Pair IDs, statement hashes, splits (pilot 5 / core 30), inclusion-rule audit.

## 2. Condition matrix — structure decided, instantiation PENDING (gate: 2.6)

Decided (PLAN.md Decision Log 2026-07-24): tiers T1–T4, 3 samples per cell, additive
by deterministic request ID. **Tier 1 is the confirmatory tier. Tier 2 and above are
exploratory/hypothesis-generating — no confirmatory claims (decision 2026-07-24, from
the Codex-review grill session).** To record at freeze: exact condition keys, per-model
request counts, any capability-based omissions.

## 3. Model slate — categories decided, IDs PENDING (gate: smoke test, PLAN.md 2.4)

Four categories per Decision Log. To record at freeze: exact model IDs/revisions/
quantization, licenses, decoding configs incl. documented-recipe deviations, cost basis.

## 4. Prompts & decoding — PENDING (gate: 2.6; pilot may revise, core may not)

Template hashes for theorem_only/preservation/validity/repair; defaults
temperature 0.2, top_p 1.0, max 8192 tokens unless a documented model recipe wins.

## 5. Analysis decisions (a)–(e) and dispute rule (g) — PENDING (gate: T006 —
after pilot, BEFORE any core result is inspected)

Provisional values + worked examples live in analysis-decisions-pending.md. At T006 the
chosen values are copied here verbatim and marked FROZEN. This includes (g), the
mechanical definition of a "disputed" core case that triggers drafting reference Lean
proofs during core annotation.

## 6. Approval records — convention active now

Every paid batch requires a machine-readable approval record under approvals/
(schema in docs/SERVER-HARNESS-RUNBOOK.md §8) BEFORE submission; the harness refuses
paid requests without one. Aggregate planning ceiling: $500 (stop-gate, not permission).

## Freeze log

| Section | Frozen on | Approved by | Commit |
|---|---|---|---|
| (none yet) | | | |
