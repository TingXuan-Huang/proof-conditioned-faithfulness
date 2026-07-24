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
- [ ] T004 (P3) Add GitHub remote and push once the repo is ready to leave this machine.
- [ ] T005 (P3) Verify the specific NeurIPS 2026 workshop + deadline (human-owned;
      HUMAN_PLAN §3).

## Done

(move completed items here with date)
