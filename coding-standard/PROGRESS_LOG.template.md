# Progress Log Entry Templates

Copy the relevant template below and append it to the **top** of `PROGRESS.md` (newest
first) whenever a session produces something worth recording. Not every change needs an
entry — see "When to log" at the bottom, which applies to both entry types.

`PROGRESS.md` serves two purposes: it keeps the agent oriented across sessions (what's
been built, what broke and why, in what order), and it's raw material for later
retrospective analysis — running an agent over `PROGRESS.md` to audit how the agentic
workflow itself is going (where time went, what kept breaking, what the standard missed)
is the point of keeping it structured and consistent rather than free-form notes.

---

## Template: Feature added

### [date] — [short title]

- **Tier:** exploratory / library
- **File(s):**
- **What:** what was implemented, briefly.
- **Why:** what task/need prompted this — link the `todo.md` item if one exists.
- **How it works:** the non-obvious part of the design, if any — skip this line if the
  implementation is straightforward enough that "what" already covers it.
- **Reused pattern or new one?** Does this reuse an existing abstraction/pattern in the
  codebase, or introduce a new one? If new, is it a candidate for
  `PROJECT_ARTIFACTS.md`'s load-bearing section?
- **Standard feedback (optional):** did anything about writing this expose a gap in
  `coding-standard/` itself? Per README §8, this is a proposal, not an edit.

---

## Template: Debugging session

### [date] — [short title]

- **Tier:** exploratory / library
- **File(s):**
- **Caught by:** manual observation / test failure / statistical sanity check / code
  review / other — *if this bug slipped past a check that should have caught it, that's
  the single most important field in this entry.*
- **Symptom:** what was actually observed — the wrong output, the crash, the surprising
  number. Quote the actual value/error, not a paraphrase.
- **Context:** what you were running — command, config, experiment, data version. Enough
  to reproduce.
- **Hypothesis log:** chronological, not cleaned up after the fact — what you suspected
  at each point and why, including wrong hypotheses. Wrong hypotheses are useful signal
  for next time.
- **Root cause:** the actual mechanism, not just "fixed it" — why the code produced the
  wrong result.
- **Fix:** what changed, and why this is the right fix rather than a workaround.
- **Known pattern?** Does this match an already-documented footgun (mutable default
  arguments, closure-over-loop-variable, NumPy/tensor truthiness, pipe-to-`while`
  subshell scoping, wrong abstraction, or other)? If yes, name it. If no, is this a new
  pattern worth adding to the standard?
- **Verification:** how you confirmed the fix actually works — what specifically would
  catch this bug if it recurred (a new test, a new statistical check, a new
  review-checklist line).
- **Standard feedback (optional):** same as above.

---

## When to log

Not every session needs an entry. Log a **feature-added** entry when the change is more
than a trivial edit — roughly, anything that would need its own line in
`PROJECT_ARTIFACTS.md`'s agent-maintained section anyway.

Log a **debugging** entry when at least one is true:

- The bug was a **silent wrong result** — a plausible-looking wrong answer, not a crash.
  This is the standard's core failure mode; these are the most valuable entries.
- It took real time to track down (rough guide: more than ~20 minutes).
- It matches, or might be, a recurring pattern.
- It exposed a gap in the standard itself.

Skip logging for: typos, obvious one-line fixes, anything resolved in under a couple of
minutes with an immediately obvious cause.
