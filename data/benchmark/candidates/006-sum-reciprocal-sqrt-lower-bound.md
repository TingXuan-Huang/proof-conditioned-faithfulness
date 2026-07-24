# Candidate 006: sum-reciprocal-sqrt-lower-bound

Status: draft
Batch: 2 (finite sums / sets / algebra / inequalities), Opus agent, 2026-07-24

**Theorem.** For every integer $n\ge 1$, $\sum_{k=1}^{n}\frac{1}{\sqrt{k}} > 2\big(\sqrt{n+1}-1\big)$.
Formal reading: `∀ n ≥ 1, 2 * (Real.sqrt (n+1) - 1) < ∑ k in Finset.Icc 1 n, 1 / Real.sqrt k`.

**Domain.** Elementary inequalities (finite sums over the reals; uses √, no limits).

**Strategy A — Induction on $n$.**
Base case $n=1$: LHS $=1$ and RHS $=2(\sqrt2-1)\approx 0.828$, so $1>2(\sqrt2-1)$.
Inductive step: assume $\sum_{k=1}^{n}1/\sqrt{k} > 2(\sqrt{n+1}-1)$. It suffices to show the added term dominates the increase in the bound, i.e. $\frac{1}{\sqrt{n+1}} > 2\big(\sqrt{n+2}-\sqrt{n+1}\big)$. Rationalizing, $2(\sqrt{n+2}-\sqrt{n+1}) = \frac{2}{\sqrt{n+2}+\sqrt{n+1}} < \frac{2}{2\sqrt{n+1}} = \frac{1}{\sqrt{n+1}}$. Adding $1/\sqrt{n+1}$ to the hypothesis then gives the claim for $n+1$.

**Source A.** Cut-the-Knot, "Improving an Inequality" (Alexander Bogomolny; problem from an old Russian problem collection), Solution 1 by induction, https://www.cut-the-knot.org/arithmetic/algebra/ImprovedInequality2.shtml.

**Strategy B — Term-wise bound + telescoping.**
For each $k\ge 1$, rationalizing gives $2(\sqrt{k+1}-\sqrt{k}) = \frac{2}{\sqrt{k+1}+\sqrt{k}} < \frac{2}{2\sqrt{k}} = \frac{1}{\sqrt{k}}$, so $\frac{1}{\sqrt{k}} > 2(\sqrt{k+1}-\sqrt{k})$. Summing this pointwise inequality over $k=1,\dots,n$, the right side telescopes:
$$\sum_{k=1}^{n}\frac{1}{\sqrt{k}} > \sum_{k=1}^{n} 2\big(\sqrt{k+1}-\sqrt{k}\big) = 2\big(\sqrt{n+1}-\sqrt{1}\big) = 2\big(\sqrt{n+1}-1\big).$$

**Source B.** Same Cut-the-Knot page, Solution 2 (telescoping) — both routes appear side by side on this single reliable page.

**Distinctness rationale.** Route A inducts on $n$, reducing the $n+1$ case to the $n$ case via a single-term estimate; route B proves one pointwise inequality for all $k$ and sums it, letting the bound telescope — no recursion on $n$. **Reviewer note:** both routes share the same rationalization algebra ($2/(\sqrt{k+1}+\sqrt{k}) < 1/\sqrt{k}$) — the distinctness is in proof *shape* (recursion vs. sum-of-pointwise-bounds), which is real but subtler than the other candidates. Worth deliberate scrutiny at approval time.

**Signatures A (required).**
- Base case $n=1$ checked ($1 > 2(\sqrt2-1)$).
- Inductive hypothesis invoked; last term $1/\sqrt{n+1}$ peeled off the sum.
- Reduction to the single inequality $1/\sqrt{n+1} > 2(\sqrt{n+2}-\sqrt{n+1})$.

**Signatures A (incompatible).**
- No summation of a per-term inequality across all $k$.
- No telescoping cancellation of $\sqrt{k+1}-\sqrt{k}$ over the whole range.

**Signatures B (required).**
- Universal per-term lemma $1/\sqrt{k} > 2(\sqrt{k+1}-\sqrt{k})$ for all $k$.
- Monotonicity of the finite sum applied to a term-wise inequality (`Finset.sum_lt_sum` / `sum_le_sum`).
- Telescoping of $\sum 2(\sqrt{k+1}-\sqrt{k})$ to $2(\sqrt{n+1}-1)$.

**Signatures B (incompatible).**
- No base-case-plus-hypothesis structure on the full sum.
- No step that rewrites the $n+1$ statement in terms of the $n$ statement.

**Contamination risk.** MEDIUM — a known olympiad-style inequality with both proofs on Cut-the-Knot, but much less ubiquitous than the headline identities; a model may recognize the telescoping trick without having memorized this exact pairing.

**Lean statement sketch.** `theorem sum_one_div_sqrt_lb (n : ℕ) (hn : 1 ≤ n) : 2 * (Real.sqrt (n+1) - 1) < ∑ k in Finset.Icc 1 n, 1 / Real.sqrt (k : ℝ)` — UNVERIFIED.

## Review notes

- **Why MEDIUM contamination**: known olympiad-style inequality with both proofs on one
  cut-the-knot page, but far less ubiquitous than the headline identities; a model may
  know the telescoping trick generally without having memorized this exact pairing.
- **Distinctness is the subtlest of the six**: both routes share the identical
  rationalization step ($2/(\sqrt{k+1}+\sqrt{k}) < 1/\sqrt k$) — the difference is
  proof *shape* (recursion on the whole sum vs. one universal per-term bound summed).
  Real, but annotators will need the shape-level framing spelled out in the rubric.
  Scrutinize hardest here before approving.
- **Formalization caveat**: only candidate using `Real.sqrt` — statement is still
  simple, but proofs involve real-number inequality reasoning (`Real.sqrt` lemmas,
  positivity side-goals), a notch more Mathlib overhead than the ℕ/ℤ candidates. If the
  pilot needs uniform difficulty, this is the one to swap out; if the pilot wants
  domain spread, it's the only inequalities representative so far.
