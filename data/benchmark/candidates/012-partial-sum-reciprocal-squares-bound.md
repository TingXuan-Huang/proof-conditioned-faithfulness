# Candidate 012: partial-sum-reciprocal-squares-bound

Status: draft
Batch: 4 (low-contamination hunt), Opus agent, 2026-07-24

**Theorem.** For every $n \ge 1$, $\sum_{k=1}^{n} \frac{1}{k^2} \le 2 - \frac{1}{n}$ (over ℝ).
Formal reading: `∀ n : ℕ, 1 ≤ n → ∑ k ∈ Finset.Icc 1 n, (1:ℝ)/(k:ℝ)^2 ≤ 2 - 1/(n:ℝ)`.

**Domain.** Elementary inequalities / finite sums.

**Strategy A — telescoping comparison.** For $k \ge 2$, $k^2 > k(k-1) > 0$, so $\frac{1}{k^2} \le \frac{1}{k(k-1)} = \frac{1}{k-1} - \frac{1}{k}$. Summing from $k=2$ to $n$ telescopes to $1 - \frac1n$. Adding the $k=1$ term (=1) gives $\sum_{k=1}^n \frac1{k^2} \le 2 - \frac1n$.

**Source A.** ADAPTED (specific finite bound $2 - 1/n$); the comparison-telescope is the classical Jacob Bernoulli (1689) argument. Cut-the-knot, *Telescoping Sums, Series and Products* — https://www.cut-the-knot.org/m/Algebra/TelescopingSums.shtml ; A. Máté, *Telescoping sums* (CUNY notes) — https://www.sci.brooklyn.cuny.edu/~mate/misc/telescoping_sums.pdf ; Bernoulli's "< 2" bound: MAA Convergence, *Euler's Calculation of the Sum of the Reciprocals of the Squares*.

**Strategy B — induction on $n$.** Base $n=1$: $1 = 2 - 1/1$, equality. Step: assume the bound at $n$. Then it suffices that $\frac1{n+1} + \frac1{(n+1)^2} \le \frac1n$, i.e. $\frac{n+2}{(n+1)^2} \le \frac1n$, i.e. $n(n+2) \le (n+1)^2$, i.e. $n^2+2n \le n^2+2n+1$ — true. Induction closes.

**Source B.** ADAPTED; induction on a summation bound of this shape is a standard exercise pattern (Máté notes above; ProofWiki category *Sums of Sequences*, https://proofwiki.org/wiki/Category:Sums_of_Sequences). Core inequality $n(n+2) < (n+1)^2$ is elementary.

**Distinctness rationale.** Strategy A bounds each term by a difference and collapses in one telescoping step with no $n$-recursion; Strategy B never introduces the $\frac1{k(k-1)}$ comparison and carries the bound through a per-step induction reducing to $n(n+2)\le(n+1)^2$. Different formal skeletons: telescope vs `Nat.rec`.

**Signatures A (required).**
- Per-term bound `1/k^2 ≤ 1/(k*(k-1))` for `k ≥ 2` (with positivity side goals).
- Partial-fraction rewrite `1/(k*(k-1)) = 1/(k-1) - 1/k`.
- Telescoping evaluation to `1 - 1/n`.

**Signatures A (incompatible).**
- No `induction n` carrying the inequality as hypothesis.
- No reduction to `n*(n+2) ≤ (n+1)^2`.

**Signatures B (required).**
- Induction on `n` (unfolding one term via `Finset.sum` succ lemma).
- Induction hypothesis `S n ≤ 2 - 1/n` used.
- Successor step reduced to `n*(n+2) ≤ (n+1)^2`.

**Signatures B (incompatible).**
- No per-term `1/(k*(k-1))` comparison lemma.
- No telescoping cancellation identity.

**Contamination risk.** LOW-MEDIUM — the "$\sum 1/k^2 < 2$" story is famous, but the exact partial-sum constant $2 − 1/n$ with a matched telescoping-vs-induction pair is a niche exercise form.

**Lean statement sketch.** `theorem sum_inv_sq_le (n : ℕ) (hn : 1 ≤ n) : ∑ k ∈ Finset.Icc 1 n, (1:ℝ)/(k:ℝ)^2 ≤ 2 - 1/(n:ℝ)` — UNVERIFIED.

## Review notes

- **Why LOW-MEDIUM contamination**: the general Basel-adjacent story is famous, but
  this exact finite form with this exact A/B pairing is niche.
- **ADAPTED-source caveat**: both routes are marked ADAPTED — the specific constant
  form is the agent's instantiation of classical techniques. Approve on direct
  mathematical verification (both proofs are short and checkable by hand), not source
  authority.
- **Real-arithmetic overhead**: second candidate (after 006) using ℝ — division,
  positivity side-goals, casts. Same uniform-difficulty consideration as 006; together
  they'd give the inequalities domain two representatives if both approved.
- **Note vs. 006**: structurally similar pairing (induction vs. telescoping-comparison
  on a real-valued sum bound) — if both enter the pilot, the pilot over-samples this
  proof-shape contrast; prefer one of {006, 012} in the pilot and hold the other for
  the core.
