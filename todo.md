# todo.md

Priority tags per [coding-standard/README.md](coding-standard/README.md) §5:
P0 = stakes-gate/security · P1 = bugs · P2 = design · P3 = deferrable.
Every entry gets an ID (T001, T002, ...) so in-code TODOs can reference it.

## Open

- [ ] T001 (P2) Fill out `coding-standard/PROJECT_ARTIFACTS.md` — declare this project's
      load-bearing artifacts (human-owned; candidates per HUMAN_PLAN: the benchmark
      pair data, the Lean statement translations, the strategy-labeling prompts).
- [ ] T002 (P2) Complete PROJECT_SETUP.md remaining steps when implementation starts:
      conda env + environment.yml, setup.py + `pip install -e .`, LICENSE, CITATION.
- [ ] T003 (P2) Pin Lean/Mathlib toolchain version before any Lean statement work
      (JOINT-CURATION-PLAN requires statements to elaborate in a pinned environment).
- [ ] T006 (P2) Freeze the five analysis decisions (primary estimand, sample pairing,
      ambiguity coding, uncertainty method, agreement threshold) — full explanations and
      examples in docs/design-docs/analysis-decisions-pending.md. Deferred by design:
      decide after the pilot run, but **hard gate: frozen before core-run results are
      inspected**.
- [ ] T008 (P2) Server access details — CONFIRMED 2026-07-24: cluster = Tillicum
      (UW HPC), SLURM, $250 compute credits; frontier API = $20 credit (provider
      name still to be confirmed by user — "MetaSpark" per voice transcript,
      verify exact name for configs). Still needed: partitions, GPU types/VRAM,
      storage quota + purge policy, compute-node network policy, secret delivery.
      Record answers in docs/SERVER-HARNESS-RUNBOOK.md §1. Blocks 2.4 slate freeze.
- [ ] T010 (P3) Rerun the LOW-CONTAMINATION discovery round — the round-3 agent
      hunting deliberately obscure A/B pairs died on a session usage limit
      (2026-07-24, resets 7pm PT) with zero results. Why it matters: the pool of 44
      runs famous-heavy (~1/3 HIGH-risk) against the ⅔-new/adapted target, so fresh
      LOW/LOW-MED pairs are the scarcest resource for the final 30. How: launch 1-3
      Opus agents with the prompt in data/benchmark/candidates/DISCOVERY-PROMPT.md,
      objective "minimize contamination" (hunt problem-set corners, regional
      olympiad training, second-tier identities; agent should reject its own HIGH
      finds), exclusion list 1-43 + NOTES-library-collapse-catalog.md. File keepers
      as 045+. Optional — do after (or during) the human review pass reveals which
      domains still need low-contamination fills.
- [ ] T007 (P2) Recruit a second qualified annotator (or explicitly preregister a
      single-annotator + LLM-judge fallback). Blocks the annotation phase.
      See analysis-decisions-pending.md §(f).

## Done

- [x] T004 (P3) 2026-07-24 — GitHub remote added and pushed:
      https://github.com/TingXuan-Huang/proof-conditioned-faithfulness.git (commit f79f0ac).
      GitHub is now the single source of truth; laptop→server file copying prohibited.
- [x] T009 (P2) 2026-07-24 — Old plans banner-retired to docs/plans/completed/;
      all pending work committed. PLAN.md is the sole active plan.

- [x] T005 (P3) 2026-07-24 — Venue verified: **MATH-AI @ NeurIPS 2026 (Atlanta)** is the
      primary target — deadline Sept 25, 2026 AoE, notification Oct 19, 4 pages +
      unlimited refs/appendix, non-archival (https://mathai-2026.github.io/cfp).
      Fallback: VERICODEGEN (deadline Sept 10, Lean/autoformalization explicitly in
      scope, https://vericodegen.github.io/) — fallback decision needed by ~Sept 5.
