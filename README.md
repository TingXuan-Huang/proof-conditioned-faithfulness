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

Planning complete; implementation not yet started. See
[docs/plans/active/](docs/plans/active/) for the execution plan, human decision plan,
and the 30-pair curation plan. Progress checklist lives in the
[human plan](docs/plans/active/proof-conditioned-faithfulness-HUMAN_PLAN.md) §2.

## Orientation

- **Agents**: start at [AGENTS.md](AGENTS.md) — the map of this repo.
- **Humans**: the three plans in `docs/plans/active/` are the project; everything else
  is scaffolding. Engineering standards live in [coding-standard/](coding-standard/).

## Setup

Not yet initialized (no environment, no Lean toolchain pinned). Follow
[coding-standard/PROJECT_SETUP.md](coding-standard/PROJECT_SETUP.md) when
implementation starts — remaining steps are tracked in [todo.md](todo.md).
