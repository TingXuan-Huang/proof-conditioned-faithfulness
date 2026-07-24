> **SUPERSEDED (2026-07-24).** This plan is retired (todo T009). The single
> controlling plan is [../active/PLAN.md](../active/PLAN.md). This file is kept as
> historical reference only — do not execute from it.

# Task Plan: Proof-Conditioned Faithfulness Plans

## Goal

Maintain a coordinated set of planning documents: an implementation-ready ExecPlan, a human decision plan, and a joint agent–human curation plan for sourcing, formalizing, reviewing, and freezing 30 A/B proof-strategy examples.

## Phases

- [x] Phase 1: Inspect the workspace, source research idea, and ExecPlan requirements.
- [x] Phase 2: Resolve experimental-design choices through the grill-me interview.
- [x] Phase 3: Verify related work, statistical methods, current systems, Lean tooling, and NeurIPS 2026 workshop feasibility.
- [x] Phase 4: Synthesize confirmed facts, accepted decisions, assumptions, and open questions.
- [x] Phase 5: Write `proof-conditioned-faithfulness-EXECPLAN.md`.
- [x] Phase 6: Write `proof-conditioned-faithfulness-HUMAN_PLAN.md`.
- [x] Phase 7: Audit both deliverables against `.agent/PLAN.md` and `RESEARCH_CODE_STANDARD.md`.
- [x] Phase 8: Write and audit `proof-strategy-pair-JOINT-CURATION-PLAN.md`.

## Key Questions

1. What exactly do ProofBridge, ProofFlow, StepProof, and the robustness/faithfulness paper evaluate?
2. Which statistical contrasts and agreement statistics are appropriate for the paired, hierarchical design?
3. Which current model categories can accept informal proofs and produce Lean reproducibly?
4. Which Lean and Mathlib mechanisms can support proof-dependency and local-step-utilization extraction?
5. Which NeurIPS 2026 workshop calls are suitable, and are their deadlines still feasible?

## Decisions Made

- The primary scientific target is counterfactual strategy responsiveness under a fixed trusted Lean theorem statement.
- Full theorem-plus-proof autoformalization is a secondary track.
- The pilot has five theorem pairs; the main benchmark begins with 30 and may expand toward 50 under a preregistered precision rule.
- The core conditions are theorem-only, proofs A and B, and symmetric paraphrases, with preservation and validity-only prompts and three samples per cell.
- Validity, conditional responsiveness, and end-to-end responsiveness are reported separately.
- A second qualified human annotator is available.
- NeurIPS 2026 workshops remain the submission goal, subject to verified calls and deadlines.
- The deliverables are separate agent and human plans, both with dated progress checkboxes and decision logs.
- The joint curation plan will target 30 human-approved A/B strategy pairs, with the agent sourcing a larger candidate pool from traceable human-authored mathematical sources.
- Candidate-stage records require a parsable and elaborated Lean theorem statement but do not require a Lean proof.

## Errors Encountered

- The repository instruction `.agent/AGENT.md` refers to `.agent/PLANS.md`, but the available template is `.agent/PLAN.md`. Treat `.agent/PLAN.md` as the operative ExecPlan specification and record the mismatch.
- The planning workspace is not a Git repository. The ExecPlan now requires the implementation agent to create or clone a correctly scoped repository on the server before research artifacts or commits are produced.

## Status

**Complete as of 2026-07-23** — the three plans now cross-reference one another. The joint plan defines a 45–60 candidate discovery funnel leading to 30 human-approved A/B pairs, source reliability and copyright rules, versioned JSONL schemas, proposition-only Lean checking, review roles, rejection codes, batch workboards, and the unresolved synchronization decision about later reference Lean proofs.
