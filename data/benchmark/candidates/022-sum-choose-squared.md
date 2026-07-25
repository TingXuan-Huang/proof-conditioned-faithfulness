# Candidate 022: sum-choose-squared

Status: draft
Batch: Opus round-2 batch A (finite sets / counting), 2026-07-24

**Theorem.** For every $n \in \mathbb{N}$: $\sum_{k=0}^{n} \binom{n}{k}^2 = \binom{2n}{n}$.
Formal reading: $\sum_{k \in \mathrm{range}(n+1)} (\mathrm{choose}\, n\, k)^2 = \mathrm{choose}\,(2n)\,n$ in $\mathbb{N}$.

**Domain.** Finite sets / counting (partition by a statistic, product rule).

**Strategy A — double counting split by a statistic.** Split a $2n$-set into halves $M$, $W$ of size $n$. The $n$-subsets of the whole set number $\binom{2n}{n}$. Alternatively sort each $n$-subset by $k = |{\cdot} \cap M|$: each class is (k-subset of M) × ((n−k)-subset of W), giving $\binom{n}{k}\binom{n}{n-k}$ per class; classes are disjoint and exhaustive, so $\binom{2n}{n} = \sum_k \binom{n}{k}\binom{n}{n-k}$; symmetry $\binom{n}{n-k}=\binom{n}{k}$ finishes.

**Source A.** cut-the-knot (Bogomolny), "Another Binomial Identity with Proofs," committee proof — https://www.cut-the-knot.org/arithmetic/combinatorics/AnotherBinomialIdentity.shtml (agent opened and read). Second attestation: ProofWiki "Sum of Squares of Binomial Coefficients," Combinatorial Proof section (agent opened and read).

**Strategy B — coefficient comparison in a polynomial product.** From $(1+x)^n (1+x)^n = (1+x)^{2n}$, compare the coefficient of $x^n$: right side $\binom{2n}{n}$ by the binomial theorem; left side the convolution $\sum_k \binom{n}{k}\binom{n}{n-k}$. Equal polynomials have equal coefficients; symmetry finishes.

**Source B.** Same cut-the-knot page, generating-functions section; ProofWiki same page, Algebraic Proof section (agent opened and read both).

**Distinctness rationale.** A never leaves finite sets (partition + product rule); B never mentions a set (formal polynomial identity + coefficient extraction). They share only the final symmetry rewrite.

**Signatures A (required).**
- Concrete $2n$ carrier as disjoint union (`Fin n ⊕ Fin n` / `Finset.disjUnion`).
- Fiberwise partition of `powersetCard n univ` via `Finset.card_eq_sum_card_fiberwise`.
- Product rule per fiber (bijection to a product / `Finset.card_product`).
- `Nat.choose_symm` at the end.

**Signatures A (incompatible).**
- `Polynomial.coeff`/`Polynomial.X`/`coeff_mul`, `pow_add` on $(1+X)$, antidiagonal convolutions.
- Direct appeal to `Nat.add_choose_eq` (Mathlib's Vandermonde).

**Signatures B (required).**
- `add_pow`/`Commute.add_pow` or `Polynomial` machinery with `coeff_mul` over `antidiagonal`.
- `pow_add`/`two_mul` to split $(1+x)^{2n}$.
- Coefficient extraction, or appeal to `Nat.add_choose_eq`.
- `Nat.choose_symm` to fold into squares.

**Signatures B (incompatible).**
- Explicit carrier of objects + fiberwise partition / hand-built bijection.
- `Finset.powersetCard` as the counted object.

**Contamination risk.** HIGH — among the most reproduced binomial identities; the committee-vs-coefficient pairing is in essentially every combinatorics text.

**Automation/library caveats.** No exact Mathlib lemma found for $\sum \binom{n}{k}^2 = \binom{2n}{n}$ (absence UNVERIFIED), BUT `Nat.add_choose_eq` (Vandermonde) IS route B's core, so route B may collapse to "apply `Nat.add_choose_eq` + `choose_symm`" in a few lines — grade `Nat.add_choose_eq` as a route-B signature. Route A is automation-resistant.

**Lean statement sketch.** `theorem sum_choose_sq (n : ℕ) : ∑ k ∈ Finset.range (n + 1), (n.choose k) ^ 2 = (2 * n).choose n` — UNVERIFIED.

## Review notes

- **Sources**: cut-the-knot + ProofWiki, agent reports both opened; spot-check at
  approval (cut-the-knot pages are stable; ProofWiki needed a browser user-agent).
- **Math checked (Claude)**: both routes correct.
- **Pool overlap — significant**: the "double-count vs. algebraic identity" contrast is
  now the pool's most repeated axis (005, 011, 017, 021, 022). Central-binomial object
  also overlaps 011. Prefer at most one or two of {005, 017, 022} in any split.
- **Vandermonde asymmetry**: route B via `Nat.add_choose_eq` is dramatically shorter
  than route A's fiberwise decomposition — the pool's starkest length asymmetry after
  013/015; a formal-fairness concern for responsiveness scoring.
- **Verdict recommendation**: BENCH — well-made but redundant on the saturated axis;
  keep as alternate if a counting slot opens.
