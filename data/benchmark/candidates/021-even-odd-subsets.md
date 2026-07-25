# Candidate 021: even-odd-subsets

Status: draft
Batch: Opus round-2 batch A (finite sets / counting), 2026-07-24

**Theorem.** Let $n \ge 1$ and let $S$ be a finite set with $|S| = n$. The number of subsets of $S$ of even cardinality equals the number of subsets of odd cardinality. Equivalently, $\sum_{k \text{ even}} \binom{n}{k} = \sum_{k \text{ odd}} \binom{n}{k}$ for $n \ge 1$.
Formal reading: $\#\{X \in \mathcal{P}(S) : 2 \mid |X|\} = \#\{X \in \mathcal{P}(S) : 2 \nmid |X|\}$.

**Domain.** Finite sets / counting (subset families, parity, involution).

**Strategy A — parity-reversing involution.** Since $n \ge 1$, fix an element $a \in S$. Define $f : \mathcal{P}(S) \to \mathcal{P}(S)$ by $f(X) = X \mathbin{\triangle} \{a\}$ (add $a$ if absent, remove it if present). Applying $f$ twice returns $X$, so $f$ is a self-inverse bijection of $\mathcal{P}(S)$, and it changes cardinality by exactly one, so it exchanges even-sized and odd-sized subsets. Restricting $f$ to the even-sized subsets gives a bijection onto the odd-sized subsets; a bijection between finite families forces equal counts.

**Source A.** Shagnik Das, *The Binomial Theorem and Combinatorial Proofs*, Discrete Mathematics I lecture notes, FU Berlin, 2016 — combinatorial proof of Corollary 4(ii), p. 3. http://discretemath.imp.fu-berlin.de/DMI-2016/notes/binthm.pdf (agent opened and read; host's HTTPS cert mismatched, fetched over HTTP).

**Strategy B — evaluate the binomial theorem at $x = -1$.** The binomial theorem gives $(x+y)^n = \sum_k \binom{n}{k} x^k y^{n-k}$. Substitute $x=-1$, $y=1$: the left side is $0^n = 0$ (as $n \ge 1$); the right side is $\sum_k (-1)^k \binom{n}{k}$, i.e. (even-index sum) − (odd-index sum). Hence the two sums are equal, and $\binom{n}{k}$ counts $k$-subsets, transporting the identity back to subset counts.

**Source B.** Same document, algebraic proof of Corollary 4(ii), p. 2 (agent opened and read). ProofWiki "Sum of Even Index Binomial Coefficients" — UNVERIFIED (search-result level only).

**Distinctness rationale.** A builds a self-inverse map on the power set, no binomial coefficients or negatives; B evaluates a polynomial identity in a ring with −1 and needs the separate "C(n,k) counts k-subsets" bridge. "Construct involution, transport cardinality" vs. "substitute into algebraic identity, split by parity."

**Signatures A (required).**
- Distinguished element extracted from nonemptiness ($n \ge 1$ used exactly here).
- Map via `insert a X` / `X.erase a` (or symmetric difference with `{a}`) + proof it is an involution.
- Cardinality transfer via `Finset.card_bij'` / `card_nbij'`-style lemma with explicit inverse.
- `Finset.card_insert_of_not_mem` / `card_erase_of_mem` for the ±1 size change + parity flip.

**Signatures A (incompatible).**
- Any `add_pow`, `Nat.choose`, `Int.alternating_sum_range_choose`, or $(-1)^k$.
- Casting cards into ℤ/ring and closing with `ring`/`linear_combination`.

**Signatures B (required).**
- Binomial theorem (`add_pow`/`Commute.add_pow`) or `Int.alternating_sum_range_choose`.
- Work in ℤ (or ring) with casts off `Finset.card`/`Nat.choose`.
- `zero_pow` with $n \ne 0$ side condition.
- Range-sum split by parity + rearrangement via `sub_eq_zero`.

**Signatures B (incompatible).**
- Any map between the even and odd subset families / `Finset.card_bij`.
- `insert`/`erase` of a fixed base-type element.

**Contamination risk.** HIGH — both proofs are canonical and appear together in many lecture notes (including the cited source).

**Automation/library caveats.** `Int.alternating_sum_range_choose` collapses the `Nat.choose` formulation of route B to ~one `simpa` — so STATE THE THEOREM IN FINSET/PARITY-FILTER FORM over `Finset (Finset (Fin n))`, where the agent found no exact Mathlib lemma (absence UNVERIFIED). `decide` only reaches concrete n; route A is automation-resistant.

**Lean statement sketch.** `theorem even_eq_odd_subsets (n : ℕ) (hn : 0 < n) : ((Finset.univ : Finset (Finset (Fin n))).filter fun s => Even s.card).card = ((Finset.univ : Finset (Finset (Fin n))).filter fun s => Odd s.card).card` — UNVERIFIED.

## Review notes

- **Sources**: agent reports opening the FU Berlin PDF (both routes in one document —
  same single-source concentration caveat as 016); ProofWiki backup UNVERIFIED. Spot-
  check the PDF before approval; note the HTTP-only fetch quirk.
- **Math checked (Claude)**: both routes correct. Statement-form choice is load-bearing
  (see automation caveat) — the Finset-filter form is the benchmark-fair one.
- **Pool overlap**: route A is a third involution appearance (011 route B, 016 route A)
  and route B is a third binomial-theorem-evaluation (005 route A, 018 route B) — the
  pairing is fresh but both individual shapes are now well-represented.
- **Familiar bucket**: another HIGH item; competes with {002, 005, 013, 018, 019}.
- **Verdict recommendation**: KEEP as bench — clean and well-structured, but watch the
  proof-shape saturation and HIGH contamination.
