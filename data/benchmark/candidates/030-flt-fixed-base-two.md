# Candidate 030: flt-fixed-base-two

Status: draft
Batch: Opus round-3 batch A (modular arithmetic / residues), 2026-07-24

**Theorem.** For every prime $p$: $p \mid 2^p - 2$.
Formal reading: `∀ p : ℕ, p.Prime → (p : ℤ) ∣ 2^p - 2`, equivalently `2^p ≡ 2 [ZMOD p]`.

**Domain.** Modular arithmetic; Fermat's little theorem at base 2, variable prime modulus.

**Strategy A — binomial expansion + prime divisibility of middle binomial coefficients.** For $0<k<p$: $k!(p-k)!\binom{p}{k} = p!$; $p$ divides the right side but neither factorial (all factors $< p$), so $p \mid \binom{p}{k}$. Expand $2^p = (1+1)^p = 2 + \sum_{0<k<p}\binom{p}{k}$; the middle sum is divisible by $p$.

**Source A.** Wikipedia, "Proofs of Fermat's little theorem," §Proof 1 (Euler induction + the freshman's-dream lemma with the $p \mid \binom{p}{i}$ justification) — agent opened. Base-2 single-expansion specialization is ADAPTED (source runs induction k→k+1).

**Strategy B — group action / necklace orbit counting.** Length-$p$ binary strings, $|S| = 2^p$; $\mathbb{Z}/p$ acts by rotation; fixed points are exactly the 2 constant strings; any non-constant string has trivial stabilizer (subgroups of prime order dichotomy), hence orbit size exactly $p$. The $2^p - 2$ non-constant strings partition into $p$-sized orbits.

**Source B.** Same Wikipedia page, §"Proof by counting necklaces" — agent opened. Specialized to a=2 and phrased via orbit-stabilizer (ADAPTED).

**Distinctness rationale.** A is closed-form algebra in ℕ (binomial sum + factorial-valuation lemma), constructs no set or map; B never writes a binomial coefficient — group action on a function type, divisibility from orbit sizes.

**Signatures A (required).**
- Explicit binomial expansion of `(1+1)^p` (`add_pow` / `Nat.sum_range_choose` / peeling).
- `p ∣ Nat.choose p k` for `0 < k < p`.
- `Finset.dvd_sum` over the middle range.
- Splitting off the k=0 and k=p endpoints.

**Signatures A (incompatible).**
- Any `MulAction`/`orbit`/`stabilizer` or orbit-cardinality machinery.
- Partitioning a finite type into equal-size blocks.

**Signatures B (required).**
- Group action of `ZMod p` (or cyclic group of order p) on `Fin p → Bool`.
- Orbit-size step (orbit-stabilizer or prime-order-subgroup dichotomy).
- Fixed-point count = 2.
- Summing orbit cardinalities to recover `2^p`.

**Signatures B (incompatible).**
- `Nat.choose` anywhere.
- `add_pow` / binomial theorem / `Nat.Prime.dvd_choose_self`.

**Contamination risk.** HIGH — this exact necklace-vs-binomial pair is THE canonical worked example of "two proofs of one theorem"; both routes near-certainly memorized verbatim.

**Automation/library caveats.** No decide/omega collapse (variable prime). **HIGH library collapse**: `ZMod.pow_card` closes the whole goal in ~3 lines matching NEITHER route; also dangerous: `ZMod.pow_card_sub_one_eq_one`, `add_pow_char`/`ZMod.add_pow_char` (kills A's freshman's dream), `Nat.Prime.dvd_choose_self` (kills A's key lemma). Usable only under strategy-conformance grading. Pool-overlap: A's expansion step is pooled identity 005 — partial head start on route A for models that memorized 005.

**Lean statement sketch.** `theorem two_pow_prime_sub_two (p : ℕ) (hp : p.Prime) : (p : ℤ) ∣ 2 ^ p - 2` — UNVERIFIED.

## Review notes

- **Sources**: both routes from one Wikipedia page (canonical, stable); ADAPTED
  specializations are mathematically trivial to verify. Attestation fine.
- **Math checked (Claude)**: both routes correct.
- **The tension**: contamination is about as HIGH as it gets (this pair is the
  textbook illustration of proof multiplicity), and `ZMod.pow_card` is a
  route-blind three-line kill. BUT route B is the pool's ONLY group-action/orbit
  strategy — a genuinely new strategy TYPE.
- **Verdict recommendation**: BENCH — if a group-action contrast is wanted in the
  final 30, this is the cleanest available carrier despite the fame; do not put it
  in the pilot 5.
