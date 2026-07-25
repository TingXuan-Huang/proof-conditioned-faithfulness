# Candidate 027: euler-binary-product

Status: draft
Batch: Opus round-2 batch C (elementary algebra / finite products), 2026-07-24

**Theorem.** In $\mathbb{Z}[X]$, for every $n$: $\prod_{k=0}^{n-1} (1 + X^{2^k}) = \sum_{j=0}^{2^n-1} X^j$ (both sides 1 at $n=0$).
Formal reading: `∏ k < n, (1 + X ^ 2 ^ k) = ∑ j < 2 ^ n, X ^ j` in `Polynomial ℤ`.

**Domain.** Finite products / polynomial identity (Euler's duplication product).

**Strategy A — telescoping by repeated difference of squares.** Multiply the product $P$ by $(1-X)$ and absorb factors left to right: $(1 - X^{2^m})(1 + X^{2^m}) = 1 - X^{2^{m+1}}$, so $(1-X)P = 1 - X^{2^n}$. The geometric sum satisfies the same: $(1-X)\sum_{j<2^n} X^j = 1 - X^{2^n}$. Cancel $1-X \ne 0$ in the integral domain $\mathbb{Z}[X]$.

**Source A.** cut-the-knot (Bogomolny), "Telescoping Sums, Series and Products," section on $\prod(1+a^{2^k})$ — https://www.cut-the-knot.org/m/Algebra/TelescopingSums.shtml. Corroborating: Brilliant wiki "Telescoping Series — Product" (worked $(1+x)(1+x^2)\cdots(1+x^{16}) = (1-x^{32})/(1-x)$).

**Strategy B — binary-representation counting.** Expand by distributivity: the product is $\sum_{S \subseteq \{0..n-1\}} X^{w(S)}$ with $w(S) = \sum_{k \in S} 2^k$. The map $S \mapsto w(S)$ is a bijection onto $\{0,\dots,2^n-1\}$ by existence-and-uniqueness of the $n$-bit binary expansion. Re-index.

**Source B.** Allouche & Mendès France, "Euler, Pisot, Prouhet-Thue-Morse, Wallis and the duplication of sines," arXiv:math/0610525, Proposition 1 + Corollary 1 (attributed to Euler; proof "a direct consequence of the uniqueness of the base 2 expansion"). Corroborating: Wilf, *Lectures on Integer Partitions* (PIMS 2000), §2 Example 2 (infinite-product form of the same argument).

**Distinctness rationale.** A manipulates the whole product via the auxiliary factor $(1-X)$ and cancellation, never inspecting coefficients; B expands into a subset-indexed sum and transports it along a binary-representation bijection, never introducing $(1-X)$.

**Signatures A (required).**
- Multiplication by `(1 - X)` + cancellation (`mul_left_cancel₀` / domain division).
- Repeated difference-of-squares step `(1 - X^(2^k))(1 + X^(2^k)) = 1 - X^(2^(k+1))`.
- Geometric-sum fact (`geom_sum_mul`-family) producing `1 - X ^ 2 ^ n`.
- Exponent arithmetic `2^(k+1) = 2^k * 2` as the collapse engine.

**Signatures A (incompatible).**
- `Finset.prod_add`, `Finset.powerset`, subset-indexed sums.
- Bijection/reindexing lemmas or binary digits (`Nat.testBit`, `Nat.bits`).

**Signatures B (required).**
- `Finset.prod_add` (or equivalent subset expansion of `∏ (1 + f k)`).
- Sum indexed by `Finset.powerset (Finset.range n)` with terms `X ^ (∑ k ∈ S, 2^k)`.
- Explicit bijection `S ↦ ∑ k ∈ S, 2^k` onto `range (2^n)` via binary uniqueness.
- `Finset.prod_pow_eq_pow_sum` / `pow_add` to fold products of powers.

**Signatures B (incompatible).**
- The factor `(1 - X)` anywhere; geometric-sum lemmas on the RHS.
- Domain-cancellation lemmas.

**Contamination risk.** MEDIUM — the identity is standard but the paired telescoping-vs-binary-counting presentation of the FINITE version is much rarer than the infinite folklore form.

**Automation/library caveats.** `ring`/`polyrith`/`omega`/`decide` inapplicable (variable-length product/sum). Agent found NO exact Mathlib lemma (searched GeomSum + BigOperators ring files; `Finset.prod_add` and `geom_sum_mul` are ingredients, not the result). **Grader caveat (agent-flagged): a genuine THIRD route exists** — induction on $n$ via the range split $\sum_{j<2^{n+1}} X^j = (1 + X^{2^n})\sum_{j<2^n} X^j$ — short and Lean-friendly; the rubric must give it its own label rather than folding it into A or B. State in `Polynomial ℤ` to keep A's cancellation legitimate.

**Lean statement sketch.** `theorem euler_binary_product (n : ℕ) : ∏ k ∈ Finset.range n, (1 + (Polynomial.X : Polynomial ℤ) ^ (2 ^ k)) = ∑ j ∈ Finset.range (2 ^ n), (Polynomial.X : Polynomial ℤ) ^ j` — UNVERIFIED.

## Review notes

- **Sources**: cut-the-knot + Brilliant (route A), arXiv paper + Wilf lectures
  (route B) — diverse and independently attested; spot-check the arXiv Prop. 1 at
  approval (stable source).
- **Math checked (Claude)**: both routes correct; the third-route caveat is real and
  the honest flag is exactly what the rubric needs (predicted-third-behavior, like
  library-lookup but structural).
- **Best find of the algebra batch**: fresh domain (polynomial identities), no exact
  library hit, automation-resistant, MEDIUM contamination. Statement lives in
  `Polynomial ℤ` — the heaviest statement machinery in the pool after 006/012's ℝ;
  check Gate S fairness and whether slate models handle `Polynomial` API at all
  (pilot smoke will tell).
- **Verdict recommendation**: KEEP — pilot-eligible if the Polynomial-API concern
  clears at the smoke slice.
