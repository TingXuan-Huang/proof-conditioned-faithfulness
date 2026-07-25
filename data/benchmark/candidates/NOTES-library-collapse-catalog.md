# NOTES: Library-Collapse Catalog (not a candidate)

Curation reference, 2026-07-24, from the round-3 order/extremal discovery agent's
Loogle-verified appendix plus pool-wide observations. Purpose: (1) stop future
discovery agents from re-proposing dead theorems; (2) feed the S5 rubric's
library-lookup policy with concrete cases; (3) supply ready-made fixtures.

## Theorems killed outright by an exact Mathlib lemma (do not propose)

| Theorem | Killing lemma (Loogle-verified) |
|---|---|
| Injective self-map of a finite type is surjective | `Finite.injective_iff_surjective` (+ `Fintype.injective_iff_surjective`, `Finite.injective_iff_bijective`) |
| No infinite strictly decreasing sequence in ℕ | `not_strictAnti_of_wellFoundedLT` |
| Antitone ℕ→ℕ sequence eventually constant | `Nat.stabilises_of_antitone`, `WellFoundedLT.antitone_chain_condition` |
| Nonempty bounded set of naturals has a maximum | `Nat.sSup_mem`; finite versions via `Finset.max'_mem`, `Finset.exists_le_maximal` |
| Every n ≥ 2 has a prime divisor | `Nat.exists_prime_and_dvd` |
| n = 2^k · odd decomposition | `Nat.exists_eq_two_pow_mul_odd` |
| n = sum of distinct powers of 2 | `Finset.twoPowSum_toFinset_bitIndices` (pooled anyway as 034, bench) |
| # odd-degree vertices even | `SimpleGraph.even_card_odd_degree_vertices` (pooled as 025, reject-rec) |
| Strictly monotone f: ℕ→ℕ has n ≤ f n | `StrictMono.le_apply` (pooled as 038, reject-rec) |
| (a−b) ∣ (aⁿ−bⁿ) | `sub_dvd_pow_sub_pow`, `geom_sum₂_mul` (pooled as 028) |
| (a+b) ∣ odd-power sums | `Odd.add_dvd_pow_add_pow` (pooled as 029) |
| p ∣ 2^p − 2 | `ZMod.pow_card` (pooled as 030) |

## Best rejected alternative (bench, not pooled)

"Every integer > 1 is a product of primes" — the ONE theorem with both routes
(well-ordering: MCS Thm 2.3.1 §2.3; strong induction: MCS §5.2.2 re-proof) fully
worked in a single authoritative source. Attestation better than any pooled
candidate, but collapse is HIGH (`Nat.primeFactorsList`, `Nat.prod_primeFactorsList`,
`Nat.prime_of_mem_primeFactorsList`). Promote only if that lemma family is banned.

## Asymmetric-collapse cases (library lemma ≈ ONE route's compressed form)

- 022: `Nat.add_choose_eq` (Vandermonde) ≈ route B.
- 032: `quadraticChar`/`legendreSym` namespace ≈ route A (Euler's criterion packaged).
- 033: `Nat.modEq_nine_digits_sum` + `List.Perm.sum_eq` ≈ route A.
- 026: `Nat.fib_dvd`/`Nat.fib_gcd` ARE route B's required signatures (library-as-strategy).

Rubric implication (to settle at freeze, see analysis-decisions-pending.md): the
library-lookup policy must distinguish (a) route-blind closures (mixed_or_alternative),
(b) route-equivalent library calls (count toward the matching route), and
(c) prescribed-library routes (026-style). Wording proposal lives in 026/032/033
review notes.

## Third-route attractors (grade as separate labels, never fold into A/B)

- Plain induction + `ring` (035 Nicomachus — closes in ~5 lines).
- Induction + range-splitting (027 Euler product).
- Stamp-swapping induction and residue-split-omega (036 coins).
- Cyclotomic machinery (031).
