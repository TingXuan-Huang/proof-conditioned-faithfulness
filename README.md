# Proof-Conditioned Lean Faithfulness Study

Does a proof-conditioned Lean system actually follow the proof it is given?

For the same theorem, we curate two complete, correct informal proofs using genuinely
different mathematical strategies (A and B). Holding the Lean theorem statement fixed,
we give the system proof A or proof B and test whether its generated Lean proof changes
strategy accordingly — counterfactual strategy responsiveness under a fixed trusted
statement. The primary contribution is an evaluation benchmark (5-pair pilot → 30-pair
core, possible expansion to 50), not a new trained model. Target venue: NeurIPS 2026
workshop (specific workshop TBD).

Author: Tingxuan Huang.

## Status

Implementation is underway. The reproducible Python 3.12 and Lean 4.15/Mathlib
environment is built, and S1 (data contracts, deterministic IDs, artifact storage, and
CLI scaffolding) has passed its exit checks. Offline S4 model/prover adapter work is in
progress. Formal experiment readiness remains at Gate P: the human still needs to
approve the five pilot pairs before the ordered P → S → C → A gates can advance.

See [the active implementation plan](docs/plans/active/PLAN.md) for the current
checklist. Under its skip-don't-stall rule, fixture, mock, and tooling work continues
while human review is pending; no draft candidate or mock-model result is treated as a
frozen benchmark or real model smoke test.

## Orientation

- **Agents**: start at [AGENTS.md](AGENTS.md) — the map of this repo.
- **Humans**: the three plans in `docs/plans/active/` are the project; everything else
  is scaffolding. Engineering standards live in [coding-standard/](coding-standard/).

## Setup

The environment uses the committed `uv.lock`, Python 3.12, Lean 4.15.0, and Mathlib tag
`v4.15.0` (commit `9837ca9d65d9de6fad1ef4381750ca688774e608`). Server-specific setup and verification
commands are in the [server harness runbook](docs/SERVER-HARNESS-RUNBOOK.md); remaining
one-time project tasks are tracked in [todo.md](todo.md).
