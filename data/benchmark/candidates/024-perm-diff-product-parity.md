# Candidate 024: perm-diff-product-parity

Status: draft
Batch: Opus round-2 batch B (parity / invariants / integer reasoning), 2026-07-24

**Theorem.** Let $n$ be an odd positive integer and $a_1,\dots,a_n$ a permutation of $1,\dots,n$. Then $P = (a_1-1)(a_2-2)\cdots(a_n-n)$ is even.
Formal reading: `∀ n : ℕ, Odd n → ∀ σ : Equiv.Perm (Fin n), Even (∏ i : Fin n, ((σ i : ℤ) − (i : ℤ)))` (0-indexing harmless: $(a_i+1)-(i+1) = a_i-i$).

**Domain.** Parity / invariance (additive invariant) vs. counting.

**Strategy A — global additive invariant.** Suppose $P$ odd; then every factor $a_i - i$ is odd. The sum $S = \sum_i (a_i - i)$ is a sum of $n$ odd numbers with $n$ odd, hence odd. But $S = \sum a_i - \sum i = 0$ since the $a_i$ are a rearrangement — and 0 is even. Contradiction.

**Source A.** Arthur Engel, *Problem-Solving Strategies*, Springer 1998, Ch. 1 "The Invariance Principle", Problem 31 (p. 11) + Solution 31 (p. 19). Agent opened the PDF mirror at mathematicalolympiads.wordpress.com (75427434-problem-books-...pdf) and matched the solution text.

**Strategy B — counting parity classes.** Suppose $P$ odd; then $a_i$ and $i$ always have opposite parity. The odd positions number $(n+1)/2$ and each demands an even value; the even positions number $(n-1)/2$ and each demands an odd value. So exactly $(n-1)/2$ of the values are odd — but $\{1,\dots,n\}$ contains $(n+1)/2$ odd numbers. $(n-1)/2 \ne (n+1)/2$, contradiction.

**Source B.** Emory (Oxford College) Math Center, Math 125 "The Pigeonhole Principle" problem set, Problem 5, https://mathcenter.oxford.emory.edu/site/math125/probSetPigeonholePrinciple/ (agent opened; posted solution is this counting contradiction). Statement independently attested: CMU 21-301 Combinatorics HW7 P1, https://www.math.cmu.edu/~af1p/Teaching/Combinatorics/F07/hw7.pdf

**Distinctness rationale.** A reaches contradiction from one additive invariant (the telescoping sum is 0) and never counts parity classes; B never forms a sum and compares cardinalities of two parity classes via injectivity. Integer-sum contradiction vs. set-cardinality contradiction.

**Signatures A (required).**
- `Finset.sum` over the factors + the rewrite `∑ i, σ i = ∑ i, i` (`Equiv.sum_comp`/`Fintype.sum_equiv`).
- "Sum of an odd number of odds is odd" (typically via `ZMod 2`, sum collapses to `n`).
- Contradiction opened on `Odd (∏ …)` decomposed via "every factor odd".
- No `Finset.card` of a parity-filtered set.

**Signatures A (incompatible).**
- `Finset.card_le_card_of_injOn` or any pigeonhole application.
- Computing `((Finset.range n).filter Odd).card = (n+1)/2`.

**Signatures B (required).**
- `Finset.filter` by `Odd`/`Even` on index or value set, with explicit cards $(n+1)/2$, $(n-1)/2$.
- Injectivity-driven cardinality bound (`card_le_card_of_injOn` / `card_image_of_injective`).
- Numeric contradiction `(n+1)/2 ≤ (n−1)/2` (omega-closable given `Odd n`).

**Signatures B (incompatible).**
- Any `Finset.sum` over `σ i − i`, or `∑ σ i = ∑ i`.
- `Equiv.sum_comp` / `Fintype.sum_equiv`.

**Contamination risk.** MEDIUM — Engel Ch.1 #31 is an olympiad chestnut with the sum-invariant proof likely memorized, but the parity-class counting proof is reproduced far less; the pairing discriminates.

**Automation/library caveats.** No collapse found: `decide` unavailable (∀n), `omega` can't see the product or `Equiv.Perm`, no Mathlib lemma states this. Both routes share the opening "product odd ⟹ every factor odd" — grading must key on the contradiction mechanism, not the setup. A ZMod-2-laundered route A still shows the `∑ σ i = ∑ i` signature.

**Lean statement sketch.** `theorem perm_diff_prod_even {n : ℕ} (hn : Odd n) (σ : Equiv.Perm (Fin n)) : Even (∏ i : Fin n, ((σ i : ℤ) - (i : ℤ)))` — UNVERIFIED.

## Review notes

- **Sources**: Engel is a canonical book (agent matched solution text in an open PDF
  mirror — cite the book, not the mirror, at publish time for license hygiene); Emory
  page agent-opened; CMU statement-only backup. Spot-check Emory at approval.
- **Math checked (Claude)**: both routes correct, including the (n±1)/2 counts.
- **Fresh territory**: first permutation-based candidate, first invariant-vs-counting
  contrast; automation-resistant; MEDIUM contamination. `Equiv.Perm (Fin n)` and the
  ℤ-cast product are slightly heavier statement machinery than the pool average —
  check statement-formalization fairness at Gate S.
- **Verdict recommendation**: KEEP — pilot-eligible; best find of the parity batch.
