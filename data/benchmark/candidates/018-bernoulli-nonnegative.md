# Candidate 018: bernoulli-nonnegative

Status: draft
Batch: Codex-external batch 2 (number theory / algebra / inequalities), 2026-07-24.
Renumbered from Codex's "010" (collision with pool numbering).

**Theorem.** For every real number $x\ge 0$ and every integer $n\ge 1$,
$(1+x)^n\ge 1+nx$. Formal reading:
$\forall x\in\mathbb{R},\forall n\in\mathbb{N}_{>0},\;x\ge0\Rightarrow
1+nx\le(1+x)^n$.

**Domain.** Elementary inequalities / finite algebra.

**Strategy A — Induction on the exponent.** For $n=1$, both sides are
$1+x$. Assume $(1+x)^n\ge 1+nx$. Because $1+x>0$, multiplication preserves
the inequality, so
$$
(1+x)^{n+1}\ge(1+nx)(1+x)
=1+(n+1)x+nx^2\ge1+(n+1)x,
$$
where the last step uses $n\ge1$ and $x^2\ge0$. This completes the induction.

**Source A.** [*Advanced Calculus, Math 25, Midterm 1: Solutions*][ucd-bernoulli],
John K. Hunter, UC Davis, Problem 2, pp. 2–3 — gives the base case and this
multiplicative induction step.

[ucd-bernoulli]: https://www.math.ucdavis.edu/~hunter/m25_15/midterm1_solutions_25.pdf

**Strategy B — Expand by the binomial theorem.** The binomial theorem gives
$$
(1+x)^n=1+nx+\sum_{k=2}^{n}\binom{n}{k}x^k.
$$
For $x\ge0$, every binomial coefficient and every power $x^k$ in the remaining
sum is nonnegative. Dropping that nonnegative remainder yields
$(1+x)^n\ge1+nx$. For $n=1$ the remainder is empty and equality holds.

**Source B.** [“Bernoulli Inequality”][msu-bernoulli], Eric W. Weisstein,
CRC/MathWorld archive hosted by Michigan State University — expands
$(1+x)^n$ and obtains the $x>0$ case by truncating after the linear term; the
$x=0$ boundary is immediate.

[msu-bernoulli]: https://archive.lib.msu.edu/crcmath/math/math/b/b111.htm

**Distinctness rationale.** Strategy A is recursive: it transforms the
$n$-case into the $n+1$-case by multiplying one inequality. Strategy B is a
single closed-form expansion whose higher-degree terms form a nonnegative
remainder, with no induction hypothesis.

**Signatures A (required).**

- Base case $n=1$ and an induction hypothesis for exponent $n$.
- Multiplication of the hypothesis by the positive factor $1+x$.
- The step isolates and discards the nonnegative term $nx^2$.

**Signatures A (incompatible).**

- No finite sum over binomial coefficients.
- No simultaneous treatment of all powers $x^k$ for $2\le k\le n$.

**Signatures B (required).**

- The full binomial expansion of $(1+x)^n$ is introduced.
- The constant and linear terms are identified as $1+nx$.
- All terms of degree at least two are proved nonnegative and dropped together.

**Signatures B (incompatible).**

- No induction hypothesis relating exponents $n$ and $n+1$.
- No multiplication of a prior inequality by $1+x$.

**Contamination risk.** HIGH — Bernoulli's inequality and these two proofs are
standard textbook material, although their resulting formal proof shapes are
especially clean and easy to distinguish.

**Lean statement sketch.**
`theorem bernoulli_nonnegative (x : ℝ) (n : ℕ) (hn : 1 ≤ n) (hx : 0 ≤ x) : 1 + (n : ℝ) * x ≤ (1 + x) ^ n`
— UNVERIFIED.

## Review notes (Claude verification pass, 2026-07-24)

- **Sources VERIFIED by direct fetch**: Hunter UC Davis Math 25 midterm VERIFIED
  (Problem 2, exactly the multiply-by-(1+x) induction; the solution even remarks
  "We proved it in class from the binomial theorem" — corroborating route B's
  attestation). MSU CRC/MathWorld archive VERIFIED (expansion + truncation route).
- **Math checked**: both proofs correct. Distinct (recursive step vs. one-shot
  closed-form expansion with a dropped nonnegative tail).
- **Mathlib caution — stronger lemma exists**: `one_add_mul_le_pow` proves this for
  all x ≥ −2, not just x ≥ 0. Library-lookup at full strength; a model may cite it
  and be done. HIGH contamination (self-declared, correct).
- **Formalization asymmetry**: route B needs `add_pow` (binomial theorem) plus finite
  sum nonnegativity over `Finset.range` — noticeably heavier than route A's induction.
- **Familiar-bucket pressure**: the pool already oversupplies HIGH items
  ({002, 005, 013} + 009 MEDIUM-HIGH); 018 adds another famous-named-inequality item.
- **Verdict recommendation**: BENCH — clean and well-sourced but redundant with the
  oversupplied familiar bucket; use as a core alternate if a HIGH slot opens.
