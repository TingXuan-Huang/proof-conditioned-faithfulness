# Benchmark Candidates — Review Queue

Agent-proposed A/B proof-strategy pairs, one Markdown file per candidate, awaiting human
review. Per the curation workflow (PLAN.md Part 1.4 / JOINT-CURATION-PLAN): **an agent
may propose that a pair is ready, but it may never mark its own proposal approved.**

## Review states

Each candidate file carries a `Status:` line:

- `draft` — agent-proposed, unreviewed.
- `human_approved` — Tingxuan has verified: mathematical correctness of both proofs,
  genuine strategy distinctness, source reliability, statement fidelity.
- `rejected` — kept for the record with a one-line reason (prevents re-proposing).

Lean statement sketches in these files are **UNVERIFIED** until the server-side parse
check (PLAN.md Part 2.2) — approval here is mathematical/scientific, not formal.

## Provenance

Candidates are produced in agent batches of 2-3; each batch's search domain is recorded
in the file. Sources must be real and verifiable — a candidate with an UNVERIFIED source
cannot leave `draft` status until the source is confirmed or replaced.
