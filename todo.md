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
- [ ] T008 (P2) Server access details — scheduler CONFIRMED: SLURM (2026-07-24).
      Still needed: partitions, GPU availability, storage quota + purge policy,
      compute-node network policy, secret delivery method. Record answers in
      docs/SERVER-HARNESS-RUNBOOK.md §1. Blocks Part 2 of PLAN.md.
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
