# PLANS.md — Execution-Plan Standard for This Repository

This is the repo-owned copy of the planning standard (source: the Research_Ideas
`.agent/PLAN.md` kit file, which does not exist on the server — that is why this copy is
checked in). Every plan in docs/plans/active/ must be maintained in accordance with
this document. The controlling plan for this project is
[docs/plans/active/PLAN.md](active/PLAN.md).

An execution plan ("ExecPlan") is a design document that a coding agent can follow to
deliver a working feature or system change. Treat the reader as a complete beginner to
this repository: they have only the current working tree and the single ExecPlan file.
There is no memory of prior plans and no external context.

## How to use ExecPlans

When authoring an ExecPlan, follow this file to the letter. Be thorough in reading (and
re-reading) source material to produce an accurate specification; start from the
skeleton below and flesh it out as you research.

When implementing an ExecPlan, do not prompt the user for "next steps"; proceed to the
next milestone. Keep all sections up to date; add or split entries at every stopping
point to affirmatively state progress made and next steps. Resolve ambiguities
autonomously and commit frequently. (Project-specific exception: anything the plan
marks as a HUMAN GATE, human checkpoint, or human-owned decision stays human-owned —
see AGENTS.md operating rules.)

When discussing an ExecPlan, record decisions in its Decision Log for posterity; it
must be unambiguously clear why any change to the specification was made. ExecPlans are
living documents; it must always be possible to restart from only the ExecPlan and no
other work.

When a design has significant unknowns, use milestones to build proofs of concept that
validate feasibility before the full implementation.

## Non-negotiable requirements

- Every ExecPlan is fully self-contained: all knowledge and instructions a novice
  needs to succeed, in the plan itself.
- Every ExecPlan is a living document, revised as progress is made; each revision
  remains fully self-contained.
- Every ExecPlan enables a complete novice to implement end-to-end without prior
  knowledge of this repo.
- Every ExecPlan produces demonstrably working behavior, not merely code changes that
  "meet a definition".
- Every ExecPlan defines every term of art in plain language — or does not use it.

Purpose and intent come first: begin with a few sentences on why the work matters from
a user's perspective — what someone can do afterward that they could not before, and
how to see it working. Then give exact steps: what to edit, what to run, what to
observe. Do not point to external blogs or docs; embed required knowledge in your own
words. If a prior plan is checked in, incorporate it by reference; otherwise include
all relevant context directly.

## Formatting

Write in plain prose; prefer sentences over lists. Checklists are permitted only in the
Progress section, where they are mandatory. When a plan is the entire content of a
Markdown file, no outer code fence is used; commands, transcripts, diffs, and code
appear as indented blocks (never nested triple-backtick fences).

## Guidelines

Self-containment and plain language are paramount: define any non-ordinary term
immediately and name the files or commands where it appears in this repository. Do not
outsource key decisions to the reader; when ambiguity exists, resolve it in the plan and
explain why. Anchor the plan in observable outcomes — acceptance is behavior a human can
verify ("running X prints Y"), not internal attributes ("added a struct"). Name files by
full repository-relative path; show working directory and exact command line; state
environment assumptions. Write steps idempotently — safe to run twice; if a step can
fail halfway, say how to retry. Validation is not optional: include the exact test
commands, expected outputs, and error messages so a novice can tell success from
failure. Capture concise evidence (transcripts, short diffs) as indented examples.

## Milestones

Milestones are narrative, not bureaucracy: for each, a brief paragraph on scope, what
will exist at the end that did not before, the commands to run, and the acceptance to
observe — goal, work, result, proof. Each milestone must be independently verifiable
and incrementally implement the overall goal. Progress and milestones are distinct:
milestones tell the story, Progress tracks granular work; both must exist. Prototyping
milestones are encouraged when they de-risk a larger change; label them as prototypes
with promotion/discard criteria. Prefer additive changes followed by subtractions that
keep tests passing.

## Living-document sections (mandatory)

Every ExecPlan contains and maintains: a `Progress` section (dated checkboxes,
including partially-completed splits), a `Surprises & Discoveries` section
(observation + evidence), a `Decision Log` (decision, rationale, date/author), and an
`Outcomes & Retrospective` section (filled at major milestones and completion). If you
change course mid-implementation, document why in the Decision Log and reflect it in
Progress.

## Skeleton

    # <Short, action-oriented description>

    This ExecPlan is a living document maintained per docs/plans/PLANS.md.

    ## Purpose / Big Picture
    ## Progress                    (dated checkboxes, always current)
    ## Surprises & Discoveries     (observation + evidence)
    ## Decision Log                (decision, rationale, date/author)
    ## Outcomes & Retrospective
    ## Context and Orientation     (current state, key files by full path, terms defined)
    ## Plan of Work                (prose sequence of edits, concrete and minimal)
    ## Concrete Steps              (exact commands + working directory + expected transcript)
    ## Validation and Acceptance   (behavioral acceptance, exact test commands)
    ## Idempotence and Recovery    (safe retries, rollback paths)
    ## Artifacts and Notes         (concise evidence)
    ## Interfaces and Dependencies (prescriptive: names, paths, signatures)

When you revise a plan, reflect the change across all sections and append a dated note
at the bottom describing the change and why. The bar: SELF-CONTAINED, SELF-SUFFICIENT,
NOVICE-GUIDING, OUTCOME-FOCUSED.
