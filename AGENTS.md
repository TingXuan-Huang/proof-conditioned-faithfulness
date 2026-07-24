# AGENTS.md — Map of This Repository

This file is a table of contents, not an instruction manual. Read the section matching
your current task, open only the file(s) it points to, and go. (Rationale: a giant
instruction file crowds out the task itself — keep this under ~100 lines.)

## What this project is

Proof-Conditioned Lean Faithfulness Study: does a proof-conditioned Lean system actually
follow the informal proof it is given? Fixed Lean theorem statement; two informal proofs
(strategies A/B) per theorem; test whether the generated Lean proof changes strategy
accordingly. Target: NeurIPS 2026 workshop. Full context:
[docs/plans/active/proof-conditioned-faithfulness-HUMAN_PLAN.md](docs/plans/active/proof-conditioned-faithfulness-HUMAN_PLAN.md).

## Operating rules — always in effect

- Shared invariants (two-tier code model, promotion triggers, stakes gate, todo.md
  protocol, commit conventions): [coding-standard/README.md](coding-standard/README.md).
  Read this once per session if you haven't.
- **Never** mark your own proposal human-approved. Benchmark labels, statistical
  commitments, spending, and paper claims are human-owned — see HUMAN_PLAN §3.
- Standards files are edited only after explicit human approval (README §8).

## Task → which doc to open

| Your task | Open |
|---|---|
| Writing any code | [coding-standard/CODING.md](coding-standard/CODING.md) |
| Reviewing code (general pass) | [coding-standard/CODE_REVIEW.md](coding-standard/CODE_REVIEW.md) |
| Reviewing ML/research code (add-on pass) | [coding-standard/style/research.md](coding-standard/style/research.md) |
| Python style specifics | [coding-standard/style/python.md](coding-standard/style/python.md) |
| Shell/SLURM script style | [coding-standard/style/shell.md](coding-standard/style/shell.md) |
| Markdown/docs style | [coding-standard/style/markdown.md](coding-standard/style/markdown.md) |
| Implementation plan for the experiment pipeline | [docs/plans/active/proof-conditioned-faithfulness-EXECPLAN.md](docs/plans/active/proof-conditioned-faithfulness-EXECPLAN.md) |
| Curating the 30 A/B proof-strategy pairs | [docs/plans/active/proof-strategy-pair-JOINT-CURATION-PLAN.md](docs/plans/active/proof-strategy-pair-JOINT-CURATION-PLAN.md) |
| What humans decide vs. agents execute | [docs/plans/active/proof-conditioned-faithfulness-HUMAN_PLAN.md](docs/plans/active/proof-conditioned-faithfulness-HUMAN_PLAN.md) |
| Accepted design decisions & repo facts | [docs/design-docs/notes.md](docs/design-docs/notes.md) |
| What's been built / broken / fixed so far | [coding-standard/PROGRESS.md](coding-standard/PROGRESS.md) |
| Which files the human personally understands | [coding-standard/PROJECT_ARTIFACTS.md](coding-standard/PROJECT_ARTIFACTS.md) |
| Open work items, by priority (P0–P3) | [todo.md](todo.md) |
| One-time setup steps (env, packaging) | [coding-standard/PROJECT_SETUP.md](coding-standard/PROJECT_SETUP.md) |

## Directory layout

```
docs/plans/active/      living plans (move to ../completed/ when done)
docs/design-docs/       accepted decisions, design notes
docs/generated/         agent-generated reference docs (schemas, tooling notes)
data/                   raw data — read-only after ingest
results/                generated outputs (figures, tables, run artifacts)
scripts/                driver scripts, notebooks — directly executed
src/                    importable library code (pip install -e .)
tests/                  test suite
```

## After every work session

1. Update [coding-standard/PROGRESS.md](coding-standard/PROGRESS.md) if the change
   warrants an entry (template: PROGRESS_LOG.template.md).
2. Log agent summaries of new files in PROJECT_ARTIFACTS.md ("everything else" section).
3. Escalate anything matching the stakes gate or statistical checks to todo.md.
4. Generate the §8 process-reflection report (proposal only — never self-edit standards).
