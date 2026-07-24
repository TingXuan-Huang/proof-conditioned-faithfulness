# Research Code Standard

Portable standard for solo ML/interpretability research, written for both a human and an
AI coding agent (Claude Code) to follow. This file holds what's shared across writing code
and reviewing it — [CODING.md](CODING.md) and [CODE_REVIEW.md](CODE_REVIEW.md) hold what's
different by mode. Copy this whole `coding-standard/` directory into a project and fill out
[PROJECT_ARTIFACTS.md](PROJECT_ARTIFACTS.md) first. [PROGRESS.md](PROGRESS.md) is the
running log of what's been built and what's broken and been fixed, newest entry first —
entries are copied from [PROGRESS_LOG.template.md](PROGRESS_LOG.template.md), which covers
both feature-added and debugging-session entries. [PROJECT_SETUP.md](PROJECT_SETUP.md)
covers one-time project setup (research projects only — skip it for non-research work).
[style/research.md](style/research.md) is a second, add-on review pass for ML/research
code, run alongside (not instead of) [CODE_REVIEW.md](CODE_REVIEW.md).

Derived from a multi-source reading pass (Google, Palantir, Sandi Metz, Fowler, Beck,
Harper Reed, Simon Willison) — full source notes and the decision history behind every
rule here live in `code-quality-research/reading-notes/decisions.md` in the parent
research repo.

## 1. Purpose

**Guiding failure mode: silent wrong results, not unmaintainable software.** A function
that's ugly but computes the right number is a better outcome than a beautifully organized
function that computes the wrong one and nobody notices. Every rule in this standard
exists to make wrongness loud, not to make code pretty.

## 2. Two tiers

| | **Exploratory** (default) | **Library** |
|---|---|---|
| What | Notebooks, one-off sweeps, plots, probes | Anything reused, or anything a reported number depends on |
| Review | None | Full review pass (CODE_REVIEW.md) |
| Refactoring | Free-form, anytime, no process | Continuous, but every pass — even behavior-preserving — goes through the review gate |

Every file starts exploratory. Promotion (§3) is the only way into the library tier.

**Checklist tags**, used throughout CODING.md and CODE_REVIEW.md:
- `[always]` — applies to all code, both tiers, no exceptions.
- `[floor]` — applies to all code, but is a lighter-touch expectation than `[always]`.
- `[lib]` — library tier only.

## 3. Promotion triggers

Promote exploratory code to library tier when **any** of the following is true:

1. A second experiment imports or copies the code.
2. Any number it produces is headed into a paper, report, or real decision.
3. A discrete, self-contained pipeline stage or process it implements is complete and
   stable — even if nothing has reused it yet and no number has shipped. This closes the
   gap the first two triggers miss: code that's *done* but hasn't been reused or reported
   on yet. Event-based, not time-based — there is no "N weeks of touching the same file"
   trigger; sustained iteration on one file is a prompt to check whether trigger 1 or 2
   already silently applies, not a new trigger of its own.

**Promoting near-duplicate code**: if promoting two similar exploratory scripts into one
shared library function would require adding a parameter plus a conditional to cover both
callers, that's the signal the abstraction is wrong before it's even written. Inline both
callers, strip each to what it actually needs, and re-derive the abstraction from what's
genuinely common — don't parameterize whichever draft got promoted first.

## 4. Stakes gate — hard override, independent of tier

Regardless of tier or promotion status, code that touches any of the following is **never**
fully unreviewed, even at exploratory tier:

- Secrets or credentials (API keys, passwords, tokens).
- A billed/usage-charged API, without a hard rate limit or spend cap.
- Destructive writes outside `outputs/`/`data/processed/` (anything that deletes or
  overwrites data outside designated scratch/output directories).
- Private or personal data leaving the machine — distinct from secrets: data flowing
  somewhere unintended (an API call, logging, a third-party library's telemetry) even
  when no credential is exposed. "Does this send data anywhere, and do I know everywhere
  it goes" is a different question from "does this expose a credential."

**Three-part mechanism, all required:**
1. **Human escalation** — flagged as a `todo.md` entry (§5), never silently exempted by
   tier.
2. **Generation-time guardrail** — the coding agent defaults to adding the relevant
   safeguard when writing code that touches one of these (a rate limit/max-call cap/
   dry-run flag for a billed API; a confirmation step before a destructive write).
3. **Review-checklist line item** — an explicit, unconditional check in CODE_REVIEW.md,
   independent of whatever else that review is covering.

## 5. `todo.md` protocol

Every project's `todo.md` uses priority tags:

- **P0** — security/stakes-gate hits (§4).
- **P1** — bugs.
- **P2** — design choices.
- **P3** — behavioral/nice-to-have, explicitly deferrable to whenever there's time.

**Mandatory escalation** — these always produce a `todo.md` entry, never staying purely
agent-internal: stakes-gate hits, statistical/output-correctness checks (CODING.md §2),
load-bearing-artifact reviews (§6 below), major CODE_REVIEW.md findings.

**In-code TODO format**: `# TODO: <link> - description`, where `<link>` points to the
matching `todo.md` entry (e.g. `# TODO: todo.md#T014 - handle empty batch case`), never a
person's name. Keeps the comment and its priority/status as one traceable pair.

A progress-log entry (see [PROGRESS_LOG.template.md](PROGRESS_LOG.template.md)) that
turns up a fix or a pattern worth remembering can produce a `todo.md` entry too — e.g. a
P2/P3 item to add the pattern it revealed as a new check somewhere in this standard.

## 6. Load-bearing artifacts & the project artifact index

Every project has one or two artifacts central enough that **the human must personally
read and be able to explain them**, regardless of tier or stakes-gate status: the ML model
definition, the prompt(s) for an agent system, the core benchmark data for a benchmark
paper, the core feature implementation for a tool. Which artifact(s) count is
project-specific, declared and personally summarized by the human in
[PROJECT_ARTIFACTS.md](PROJECT_ARTIFACTS.md).

`PROJECT_ARTIFACTS.md` has a second, complementary purpose: it's also where the **coding
agent keeps its own summaries of everything else** — the non-essential files and features
the human will not personally read in full. Every file the agent writes gets a short
agent-authored summary logged there, regardless of tier. This means the file has two
distinct sections with two different authors:

- **Load-bearing artifacts** — human-written, human-maintained, for the small set of
  files the human has personally read and can explain.
- **Everything else** — agent-written summaries, for files the human is trusting the
  agent's own account of rather than reading directly.

The split itself is informative: if `PROJECT_ARTIFACTS.md`'s "everything else" section is
much larger than its load-bearing section, that's a visible signal of how much of the
codebase the human actually understands firsthand versus how much rests on agent
self-report — worth noticing, not just filing away.

## 7. Commit conventions

- Summary line: capitalized, imperative mood ("Fix bug," not "Fixed bug"/"Fixes bug"),
  ≤80 chars.
- Blank line between summary and body — load-bearing, not stylistic; some tooling
  (rebase) breaks without it.
- Body wrapped to ~120 chars; further paragraphs separated by blank lines; bullets OK.
- Describe both *what* changed and *how*/*why* — "Make compile again" fails (says
  neither); "Add jcsv dependency to fix IntelliJ compilation" passes.
- **Keep history bisectable**: small commits, each leaving the code in a working state.
  This is why refactor-only and behavior-changing passes are separate commits (see
  CODE_REVIEW.md §9) — beyond review clarity, it's what makes `git bisect` (run by you or
  an agent) actually able to isolate the commit that introduced a bug. A messy,
  everything-at-once commit history denies that tool to both of you. Mixed refactor+
  behavior commits also **break cherry-picking and rebasing** — a behavior change
  bundled into a large refactor commit is expensive to isolate and undo later, since
  pulling just the behavior change out means untangling it from everything else in the
  same commit.
- Fixes made during a review round are pushed as a **separate commit**, never squashed
  into the original — preserves the record of what changed and why.

## 8. Process reflection

At the end of a coding session or a review pass, the agent (coding or review) generates a
short reflection report on the process itself — not the code. Cover:

- Which rules in this standard were actually followed, and which were skipped or bent,
  with a reason.
- Which rules were **hard to follow** — required unusual effort, felt like fighting the
  task rather than helping it.
- Which rules felt **redundant** — overlapped with another rule, or didn't add anything
  beyond what would have happened anyway.
- Any rule that produced a **clearly wrong or unhelpful outcome** this time, specific
  enough to point at (not a vague "this felt restrictive").

The "Standard feedback" field in [PROGRESS_LOG.template.md](PROGRESS_LOG.template.md)
feeds the same loop — a session that exposes a gap in this standard is exactly the kind of
finding this reflection report should surface.

This report is a **proposal, not an edit.** The agent never modifies README.md, CODING.md,
CODE_REVIEW.md, or PROJECT_ARTIFACTS.md based on its own reflection — it surfaces findings
(in the session, or appended to `todo.md` as a P2/P3 item) and waits. Only the human
reviews and explicitly accepts a change before any rule in this standard is edited. The
point is to keep the standard evolving from real friction, not to let it silently drift
out from under deliberate decisions made when it was written.
