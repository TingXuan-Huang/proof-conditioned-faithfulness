# Candidate 036: coins-three-five

Status: draft
Batch: Opus round-3 batch C (order / well-ordering / extremal), 2026-07-24

**Theorem.** Every $n \ge 8$ is a sum of nonnegative multiples of 3 and 5.
Formal reading: `∀ n : ℕ, 8 ≤ n → ∃ a b : ℕ, n = 3 * a + 5 * b`.

**Domain.** Well-ordering vs. strong induction (additive representation).

**Strategy A — strong induction, three base cases.** Bases $8 = 3+5$, $9 = 3\cdot3$, $10 = 5\cdot2$. For $n \ge 11$: apply the IH to $n-3 \ge 8$ and add one 3.

**Source A.** Lehman-Leighton-Meyer, *Mathematics for Computer Science*, §5.2.3 "Making Change" (pp. 126-127, 2015-05-18 ed.) — exactly this proof; agent opened the PDF. VERIFIED.

**Strategy B — well-ordering / least counterexample.** If the set $C$ of bad $n \ge 8$ is nonempty, WOP gives a least $c$; the base checks force $c \ge 11$; then $c - 3 \ge 8$ is smaller, hence good, and adding a 3 makes $c$ good — contradiction.

**Source B.** ADAPTED over an attested prescribed-method exercise: MCS Ch. 2 Problem 2.7 explicitly demands "Use the Well Ordering Principle to prove [this exact statement]" (with a footnote refusing credit for induction proofs); write-up follows MCS §2.2's own WOP template. Agent found no published fully-written WOP proof of this statement.

**Distinctness rationale.** A is constructive-forward (computes the representation via an eliminator); B is classical-backward (touches only one hypothetical least bad value; load-bearing step is minimality, not an IH). Lean shapes: `Nat.strong_induction_on`/`Nat.le_induction` vs. `by_contra` + `Nat.find` + `Nat.find_min`.

**Signatures A (required).**
- Strong-induction eliminator on the main goal.
- Three-way base split at 8/9/10 with literal witnesses (1,1), (3,0), (0,2).
- IH instantiated at `n − 3` with side goal `8 ≤ n − 3`.
- Constructive: no `by_contra`/`Classical.em`/`push_neg` at top level.

**Signatures A (incompatible).**
- `Nat.find`/`find_spec`/`find_min`, `WellFounded.min`, least-counterexample hypotheses.
- `by_contra` on the outer goal.

**Signatures B (required).**
- `by_contra` + `push_neg` → `∃ n, 8 ≤ n ∧ ¬∃ a b, …`.
- Least element via `Nat.find` / `WellFounded.min`.
- Minimality invoked at `c − 3` via `Nat.find_min` with `c − 3 < c`.
- Ends in contradiction, not a returned witness for arbitrary n.

**Signatures B (incompatible).**
- Any induction eliminator driving the main goal.
- IH applied to `n − 3` inside an induction block.

**Contamination risk.** MEDIUM — the 3/5 stamp problem is a standard exercise with many public strong-induction solutions; the WOP write-up is far rarer; agent found no public Lean 4 proof.

**Automation/library caveats.** Multi-step (not one-line) collapse via `frobeniusNumber_pair` (Chicken McNugget, Mathlib.NumberTheory.FrobeniusNumber) + `AddSubmonoid.mem_closure_pair` — ban both + `exists_frobeniusNumber_iff`. Two strategy-independent third routes flagged: (i) stamp-swapping ordinary induction (swap 5→3+3 / 3·3→5·2; attested at ODU CS381 Unit 16) — grade as neither A nor B; (ii) residue-split on `n % 3` + omega witnesses. `omega` alone cannot discharge the ∃; `decide` unavailable.

**Lean statement sketch.** `theorem coins_three_five (n : ℕ) (hn : 8 ≤ n) : ∃ a b : ℕ, n = 3 * a + 5 * b` — UNVERIFIED.

## Review notes

- **Sources**: A verified in the MCS PDF. B is the strongest possible form of
  ADAPTED — the source itself PRESCRIBES the WOP method for this exact statement
  (and bans induction for credit), it just doesn't print the solution.
- **Math checked (Claude)**: both routes correct.
- **Exactly the missing contrast**: first WOP-vs-induction pair in the pool —
  the classic strategy dichotomy the benchmark had zero coverage of. MEDIUM
  contamination, no one-line collapse, ℕ-native statement (no heavy API).
- **Grading note**: the two flagged third routes make this a 3+-behavior item like
  027 — the rubric's third-label machinery gets real use here.
- **Verdict recommendation**: KEEP — pilot-eligible, arguably pilot-priority (fills
  the missing contrast axis).
