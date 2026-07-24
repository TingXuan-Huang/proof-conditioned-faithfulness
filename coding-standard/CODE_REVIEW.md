# Code Review Guide

For the agent (or human) reviewing code. See [README.md](README.md) for shared invariants.
Language-specific style enforcement lives in [style/python.md](style/python.md),
[style/shell.md](style/shell.md), and [style/markdown.md](style/markdown.md) — this file
covers review process and judgment, not per-language syntax checking (delegate that to
`ruff`/`shellcheck`/a formatter, per those files).

Priority order below follows Google's reviewer-side ordering (design → functionality →
complexity → tests → naming/comments/style → consistency → docs → context) — the inverse
of CODING.md's coding-priority order (correctness/tests first). Same anatomy as CODING.md:
**Rules** → **Checklist** → **Reflection questions**.

## 1. Setup

**Rules**
- **Topology**: one review agent per conceptual unit, plus 1-2 gate agents synthesizing
  across units into an overall verdict. Mirrors "Every Line" — fresh attention per unit
  instead of skimming one large promotion diff.
- **Batch cap**: don't review more than ~1 conceptual unit per pass. Split the promotion
  into smaller pieces first if any of: a self-review pass would take more than ~20
  minutes, the change touches more than ~5 files, or it took more than ~1-2 days to
  write. Concrete splitting pattern: for a large feature, promote the interface/API +
  docs as one change and the implementation as a separate one.
- **Refactor XOR behavior-change**: every change under review must declare itself as one
  or the other, never both. A promotion pass that would do both gets split into two
  separate passes (and two separate commits, per README §7). This declaration should be
  checkable against a **written behavior spec** — a short statement of what the code is
  supposed to do, written before the refactor starts — so "preserving" vs. "changing"
  behavior is a fact you can check, not a claim you're trusting. If no such spec exists
  going into a refactor pass, write one first.
- **Comment labeling** — every review finding is tagged one of:
  - **Suggestion** — optional, doesn't block.
  - **Required change** — blocks promotion.
  - **Open question** — needs discussion/clarification before it can be resolved either
    way.
- **Overall verdict** — one of three, not just pass/fail:
  - **Approve** — ready to promote/merge as-is.
  - **Approve with comments** ("LGTM with comments") — ready to promote, with
    non-blocking suggestions logged for later.
  - **Blocked** — required changes outstanding.
- **Good things**: every review notes patterns worth repeating, not just problems — not
  team mentoring (no second person here), but a review that only ever lists flaws trains
  both the coding agent and the human reading reviews to associate "review" with
  "criticism," which discourages actually reading them.
- **Partial-review disclosure**: when a review agent covers only certain files or aspects
  of a larger change (per the one-agent-per-unit topology), it states explicitly what it
  covered, so the gate agent knows what's actually been checked versus assumed covered by
  another agent.
- **Automated checks run first**: linting (`ruff`/`shellcheck`/formatter) is a
  precondition for review, not part of it — a clean automated-check pass happens before
  any of the sections below start.

**Checklist**
- `[always]` Automated lint/format checks pass before review begins.
- `[always]` Change is declared refactor-only or behavior-changing, not both.
- `[lib]` Batch size within the ~5-file / ~20-min cap, or explicitly split.

## 2. Design

**Rules**
- Thoroughness bar: the reviewer should be able to explain the change to someone else
  afterward. If the code is too hard to understand and that's slowing the review down,
  say so explicitly and stop — don't guess at intent or push through. If you can't
  understand it, it's a real signal others won't either.
- **Purpose check**: does the code accomplish the stated reason for the change — distinct
  from functionality-correctness (§3): this is "should this exist at all," not "does it
  compute the right thing."
- Does the design fit the surrounding system — does this belong here, in a library, or
  somewhere else; does it integrate cleanly; is now the right time to add it.
- **Wrong-abstraction scan**: actively look for the smell (a parameter + conditional
  interleaving cases that used to be uniform), not just check new code for premature
  abstraction. When found: inline back into each caller, strip each to what it actually
  needs, then either leave callers separate or re-abstract cleanly from the de-duplicated
  result.

**Checklist**
- `[lib]` Could I explain this change to someone else right now?
- `[lib]` Does every abstraction in this change have genuinely uniform callers, or does
  one of them need a parameter+conditional to fit?

**Reflection questions**
- Is this code trying to solve a problem that doesn't need solving yet?
- Would I have solved this differently — and if so, why is that difference significant?

## 3. Functionality (adversarial)

**Rules**
- Verify the statistical/sanity check from CODING.md §2 actually ran and was logged to
  `todo.md` — don't trust agent self-certification alone.
- Think adversarially: construct inputs/configurations likely to break the code, not just
  read it and assume correctness.
- Edge cases and concurrency get deliberate attention — these aren't reliably caught by
  just running the code once.
- Check for reinvented functionality that an existing library already provides.

**Checklist**
- `[always]` Statistical check present in `todo.md` for any new number-producing code.
- `[lib]` At least one adversarial input considered and either handled or explicitly
  out of scope.

**Reflection questions**
- What input or configuration would break this?
- Am I re-implementing something a library already does well?

## 4. Complexity & scope creep

**Rules**
- Distinguish two different failures: **complexity/YAGNI** (solved the right problem in
  an overcomplicated way) versus **scope creep** (solved a problem nobody asked for at
  all — Harper Reed's unrequested "lore file" pattern). They call for different fixes:
  simplify vs. remove entirely.
- Flag over-engineering — generic solutions to problems that don't yet exist.

**Checklist**
- `[always]` Did anyone ask for every piece of this change?
- `[lib]` Is there a simpler, functionally equivalent version?

## 5. Tests

**Rules**
- Read the tests, don't just confirm they exist. Do they cover interesting cases, will
  they actually fail when the code breaks, do they lower overall coverage.
- Flag risk to test infrastructure/staging/integration tests — removed test utilities,
  config changes, artifact-layout changes are easy to miss since they're often outside
  normal automated checks.
- Explicitly flag whether integration tests are needed beyond unit tests, especially for
  code touching outside systems/configuration.
- **Manual QA, distinct from automated tests**: predicting and digging into edge cases by
  hand — adversarial manual testing, not just running the existing suite. Distinct from
  §6's load-bearing-artifact review (which is about understanding); this is about
  actively trying to break it.

**Checklist**
- `[lib]` Tests read, not just counted.
- `[lib]` Manual edge-case check performed, separate from the automated suite.

## 6. Naming, comments, style

**Rules**
- Comment and commit-message quality is its own review line, not just code quality —
  applies the discipline from CODING.md §6 and README §7 at review time, not just
  authoring time.
- TODO discipline: format matches README §5 (`# TODO: <link> - description`), no bare
  TODOs without a `todo.md` entry.
- Style guide is authority for anything mandatory; non-mandatory suggestions get a
  "Nit:" label and never block.
- **Style/formatting changes are a separate change from functional changes** — same
  reasoning as the refactor/behavior split in §1: a reformatting pass reviewed alongside
  logic changes gets skimmed at exactly the size that matters.

**Checklist**
- `[always]` No bare TODOs — every one has a `todo.md` entry.
- `[always]` No style/formatting changes bundled into a functional-change review.

## 7. Consistency & docs

**Rules**
- Style guide requirements are absolute; for style guide *recommendations* (not hard
  requirements), judgment call between following the guide vs. matching surrounding
  code — bias toward the guide unless local inconsistency is more confusing. If no rule
  applies, match existing code either way.
- If existing code is inconsistent with the guide, note it as a `todo.md` P3 item rather
  than fixing it inline (unless it's part of what's already being changed).
- External docs (README, usage docs) checked for updates when the change affects how
  something is built/tested/used/released.

**Checklist**
- `[lib]` External docs updated if usage changed.

## 8. Context

**Rules**
- Look beyond the diff at the surrounding file/system — a small diff can be the wrong
  fix if it's sitting inside a function that clearly needs restructuring first.
- **Protect code health**: don't accept a change that degrades the system even slightly,
  since most systems become unmanageable through accumulation of many small
  degradations, not one big one.

**Reflection questions**
- Is this change improving the system's overall code health, or just solving the
  immediate problem while adding to long-run complexity?

## 9. Safety line-item

**Rules**
- Unconditional check, every review, independent of everything else being reviewed: does
  this change touch any README §4 stakes-gate trigger (secrets, billed APIs, destructive
  writes, private data leaving the machine)? If yes, verify all three parts of the
  mechanism are in place (human escalation, generation-time guardrail, this review
  line-item itself).
- Security specifics where relevant: authorization/authentication consistency with the
  rest of the codebase, weak configuration, malicious input handling, missing log events
  for security-relevant actions.

**Checklist**
- `[always]` Stakes-gate check run and logged, regardless of tier.

## 10. Promotion review

**Rules**
- Check promotion triggers (README §3) actually apply before promoting.
- Near-duplicate promotions: inline-and-rederive per README §3, not parameterize the
  first draft.
- **Load-bearing artifact check**: if this change touches a file declared in
  `PROJECT_ARTIFACTS.md`'s load-bearing section, confirm the human has personally
  reviewed it — this can't be satisfied by an agent summary.
- **Reproducibility/backward-compatibility check**: does this change break the
  reproducibility of a previous experiment's results, or a public interface other code
  depends on? If so, is it OK to promote now, or should it wait?
- **Safe preview/dry-run before real execution**: anything being promoted, or otherwise
  high-stakes, gets a dry-run pass against real pipelines/data before running for real —
  not just as a billing-specific mitigation (README §4), as a general promotion practice.

**Checklist**
- `[lib]` Promotion trigger confirmed (not just "felt ready").
- `[lib]` Load-bearing artifacts personally reviewed by the human, if touched.
- `[lib]` Dry-run/preview pass completed before first real execution.

## 11. Dependency audit (periodic, not per-review)

**Rules**
- New-dependency scrutiny happens in a **separate, periodic audit pass**, not gated
  per-commit or per-promotion — ML/research work pulls in too many dependencies to gate
  every addition inline.
- During that periodic pass: scrutinize new/changed dependencies heavily — is each one
  necessary, is the version pinned for anything feeding a result.

**Checklist**
- `[audit]` (fires only during the periodic pass) Every dependency added since the last
  audit is justified and, if result-affecting, version-pinned.

## Appendix: worked examples

Reference examples for what each finding category looks like — useful directly as prompt
material for an AI review agent. `//R:` marks the suggested review comment.

**Inconsistent naming**
```python
count_total_page_visits: int  # R: name variables consistently
unique_users_count: int
```

**Inconsistent method signatures** (harmonize return conventions)
```python
def extract_string(s: str) -> str | None:
    """Returns None if s cannot be extracted."""
    ...

def rewrite_string(s: str) -> str:
    """Raises ValueError if s cannot be rewritten."""
    # R: should harmonize — use `| None` here too instead of raising, or vice versa
    ...
```

**Reinventing an existing library**
```python
def join_and_concatenate(items: list[str], sep: str) -> str:
    # R: replace with "".join(items) or the stdlib equivalent
    ...
```

**A bug, phrased as a question rather than an assertion**
```python
for i in range(num_iterations + 1):  # R: this runs num_iterations+1 times — intentional?
    ...
```

**An architectural concern, flagged for discussion rather than blocked outright**
```python
other_service.call()  # R: this adds a dependency on OtherService — worth discussing
                       #    whether we want that coupling before merging
```
