# Coding Guide

For the agent (or human) writing code. See [README.md](README.md) for shared invariants
(tiers, promotion, stakes gate, todo.md, load-bearing artifacts, commits). Language-specific
style rules live in [style/python.md](style/python.md), [style/shell.md](style/shell.md),
and [style/markdown.md](style/markdown.md) — this file covers process, not per-language
syntax.

Each section: **Rules** → **Checklist** (`[always]`/`[floor]`/`[lib]` tags per README §2)
→ **Reflection questions** (answer briefly before acting).

## 1. Before coding

**Rules**
- Resolve scope ambiguity at the design stage, before touching code — ask the user, or
  log it to `todo.md`, rather than silently deciding scope on the coding agent's own
  judgment. This is specifically to avoid constant back-and-forth interrupting
  implementation later.
- Run the stakes-gate scan (README §4) before writing anything — if the task touches
  secrets, a billed API, destructive writes, or data leaving the machine, that changes
  what guardrails need to be built in from the first line, not added after the fact.
- **Optional — ask, don't default**: if this is the first script in the project writing
  a result file (figure/table) without an experiment tracker already in the loop,
  ask the user whether they want git-hash provenance stamping (embedding the current
  commit hash into the output filename, e.g. `figure.a1b2c3d.png`, via a read-only
  `git rev-parse --short HEAD`) — not something to add by default. If the project
  already uses an experiment tracker (W&B/MLflow/Neptune), its auto-captured git
  metadata already covers this and the question doesn't need asking.

**Checklist**
- `[always]` Is the scope of this task fully specified, or is there a judgment call being
  made silently? If silent, stop and ask/log.
- `[always]` Does this task touch any stakes-gate trigger? If yes, plan the guardrail
  (rate cap, dry-run flag, confirmation step) as part of the design, not an afterthought.

**Reflection questions**
- Is this request too loosely defined for me to be confident I'm building the right
  thing? (Harper Reed's "going over your skis" — the plan is what gives you something to
  check progress against later.)
- Did anyone ask for this specific piece, or am I about to add something nobody
  requested? (The scope-creep test, distinct from ordinary complexity/YAGNI below.)

## 2. Functionality first

**Rules**
- Priority order for this agent role is **correctness of output, then tests, then
  design/style** — not Google's reviewer-side design-first order (see CODE_REVIEW.md).
  A test can pass while still measuring the wrong thing; that's the gap this priority
  exists to close.
- Every number this code produces gets a statistical/sanity check, and that check is
  **always** also written to `todo.md` — never fully delegated to agent self-certification,
  even when the agent ran its own check.
- `assert` is for tests and internal invariants only (e.g. a tensor-shape check) — never
  for validating real preconditions like a CLI argument or config value, since asserts are
  silently stripped under `-O`. Use `raise ValueError` for anything that must fail loudly
  in all cases.
- Numpy arrays / torch tensors: never rely on implicit bool context (`if arr:` raises on
  multi-element arrays) and never `x = x or default` when `x` might be an array — use
  `is None` explicitly and `.size`/`.numel()` for emptiness checks.

**Checklist**
- `[always]` Does this number mean what I think it means? Sanity-checked, not just
  shape-checked.
- `[always]` Statistical check logged to `todo.md`, not just run silently.
- `[always]` Any `assert` in this code — is it a real invariant, or should it be a
  `raise`?

**Reflection questions**
- If this were wrong in the most likely way, would any test I'm about to write actually
  notice?
- Does this number mean what I think it means, or have I only checked that it's the
  right shape/type?

## 3. Tests

**Rules**
- Tests ship in the same change as the code, and must actually fail when the code is
  broken — not just exist.
- Exploratory-tier code is exempt from this requirement.

**Checklist**
- `[floor]` Does this test fail if I revert the fix it's testing?
- `[lib]` Tests cover the interesting/edge cases, not just the happy path.

**Reflection questions**
- If this test passes, what have I actually learned about correctness?

## 4. Design while writing

**Rules**
- No premature abstraction. Don't extract a shared helper across two experiments until
  the shape of what's genuinely common has stabilized — Metz's principle applies
  prospectively here, not just at promotion.
- **Wrong-abstraction signal, checked while writing**: if writing an abstraction already
  requires a parameter plus a conditional branch to cover a second caller, that
  abstraction is arriving pre-broken. Write the duplication instead; revisit once a third
  case actually reveals the real shared shape.
- Fit the surrounding system — does this belong here, or would it make more sense as a
  separate utility/library piece.

**Checklist**
- `[lib]` Do all callers of a shared abstraction genuinely need the same thing, or only
  superficially?

**Reflection questions**
- Is this abstraction earning its keep, or did I force-fit a second use case into it?
- How would I have solved this if I'd seen both callers' needs from the start?

## 5. Complexity & scope

**Rules**
- Solve the problem that needs solving now, not a speculated future one (YAGNI).
- Fewest elements — remove anything not serving correctness, clarity, or the no-duplication
  principle.
- Unrequested features are a distinct failure from over-complexity (see §1's scope-creep
  reflection question) — an agent will happily over-deliver on a loosely specified ask;
  the fix is resolving ambiguity at the design stage, not catching it after the fact.

**Checklist**
- `[always]` Is every piece of this change something the task actually asked for?
- `[always]` Would a simpler, functionally equivalent version work just as well?

**Reflection questions**
- Am I building for a hypothetical future requirement, or the one in front of me?

## 6. Naming & comments

**Rules**
- Names convey purpose without being unnecessarily long. Full naming-convention detail
  (case, per-type conventions, math-notation exception) lives in
  [style/python.md](style/python.md) — this section covers comment *discipline*, which
  applies across languages.
- **Reflect before writing a comment**: judge whether it explains *why* (keep) or just
  restates *what* the code does (drop).
- Block/inline comments stay short — target ~5 lines, never a paragraph. Docstrings are
  different: no length cap, since they're structured reference material consulted before
  calling a function, not prose read inline while scanning. See
  [style/python.md](style/python.md) "Comments & docstrings" for the full split and
  worked examples.
- **Comment-as-API-contract**: a docstring/comment block should let someone use the code
  correctly without reading the implementation — document inputs/outputs as an interface,
  not as a description of internals.

**Checklist**
- `[always]` Did I write this comment because it explains why, or because I felt like I
  should comment something here?
- `[lib]` Could someone call this function correctly from its docstring alone?

**Reflection questions**
- Is this comment explaining a hidden constraint or subtle reasoning, or just restating
  the next line of code?

## 7. After coding

**Rules**
- Generate a human-facing summary of everything written, regardless of tier — this is
  what makes README §6's "everything else" section of `PROJECT_ARTIFACTS.md` possible;
  log the summary there.
- **Self-review by diff**: read the actual diff before considering the change done, not
  just the final files — surfaces things a full-file read doesn't (leftover debug code,
  unintended formatting drift, scope creep beyond what was intended).
- **Self-test**: full test suite passing, locally (and in CI if applicable), before
  anything is considered ready for review/promotion.
- Escalate all mandatory items to `todo.md` (README §5): stakes-gate hits, statistical
  checks, anything touching a load-bearing artifact.
- Write the commit message per README §7 — imperative summary, blank line, body
  explaining what and why, kept as a separate commit from any prior refactor-only pass.
- If the change meets the "when to log" bar in `PROGRESS_LOG.template.md` (more than a
  trivial edit), prepend an entry to `PROGRESS.md`.

**Checklist**
- `[always]` Summary written to `PROJECT_ARTIFACTS.md`.
- `[always]` Diff self-reviewed, not just the final state.
- `[always]` Tests run and passing.
- `[always]` All mandatory-escalation items are in `todo.md`.
- `[floor]` Progress log entry added if the change warrants one.

**Reflection questions**
- If I handed this diff to someone else with zero context, would the commit message and
  summary be enough for them to know what changed and why?
