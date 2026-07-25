# Common brief — Lean reference-proof generation (paste this ONCE, before any candidate brief)

You are generating **reference proofs** for a research benchmark. For the candidate below
you will produce **two complete Lean 4 proofs of the exact same statement** — one
faithfully implementing Strategy A, one faithfully implementing Strategy B. These are
ground-truth artifacts: a proof that compiles but does not follow its named strategy is
worthless, and worse than no proof.

## Environment

- Lean 4 + current Mathlib (provisional toolchain target: Lean ~4.15-series with matching
  Mathlib; the exact pin will be confirmed server-side). Begin each file with
  `import Mathlib`. Avoid deprecated lemma names.
- Each route is delivered as ONE self-contained code block (imports + optional private
  helper lemmas + the theorem). Helper lemmas are allowed but must themselves respect the
  route's constraints and be prefixed with the theorem name.

## Hard rules (violations make the output unusable)

1. **The statement is frozen.** Everything before `:=`/`by` must be byte-identical to the
   statement given in the brief (only the `_A`/`_B` suffix differs). If the statement
   fails to elaborate as written, STOP and report the problem + your proposed correction
   separately — never silently change it.
2. **No escape hatches:** no `sorry`, `admit`, `stop`, `native_decide`, `unsafe`, no new
   `axiom` declarations. The proof must survive `#print axioms` with only
   `propext`, `Classical.choice`, `Quot.sound`.
3. **No route-collapsing closes:** the main goal may not be discharged by a single
   `decide` / `omega` / `norm_num` / one banned library lemma. Automation is fine for
   local arithmetic side-goals; the load-bearing structure of the route must be explicit.
4. **Faithfulness contract:** every item in that route's "must appear" list is visibly
   present; nothing in its "must NOT appear" list occurs anywhere in that route's proof
   (including inside helper lemmas). The per-candidate "banned lemmas" apply to BOTH
   routes unless the brief says otherwise.
5. If a route genuinely cannot be completed without violating a constraint, say so
   explicitly and explain why — do not smuggle a forbidden shortcut through.

## Output format (per candidate)

1. `### Route A` — one Lean code block.
2. `### Route B` — one Lean code block.
3. `### Signature checklist` — for each "must appear" item, one line naming where in the
   proof it appears (lemma name / tactic line). For each "must NOT appear" item, confirm
   absence.
4. `### Caveats` — anything you changed, any lemma you were unsure exists, any statement
   concern.

Clarity beats golf: a longer explicit proof that a human grader can align with the
informal strategy is preferred over a compressed clever one.
