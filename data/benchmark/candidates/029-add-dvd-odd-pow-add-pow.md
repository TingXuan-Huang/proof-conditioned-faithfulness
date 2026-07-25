# Candidate 029: add-dvd-odd-pow-add-pow

Status: draft
Batch: Opus round-2 batch C (elementary algebra / divisibility), 2026-07-24

**Theorem.** In a commutative ring $R$: $(a+b) \mid (a^{2m+1} + b^{2m+1})$ for all $a, b \in R$, $m \in \mathbb{N}$.
Formal reading: `∀ (a b : R) (m : ℕ), a + b ∣ a ^ (2*m+1) + b ^ (2*m+1)`.

**Domain.** Algebraic divisibility (odd-power sums).

**Strategy A — sign-substitution reduction to the difference case.** Odd exponent gives $(-b)^{2m+1} = -(b^{2m+1})$, so $a^{2m+1} + b^{2m+1} = a^{2m+1} - (-b)^{2m+1}$. Apply difference-of-powers factorization at the pair $(a, -b)$: the divisor is $a - (-b) = a + b$, with alternating-sign cofactor $\sum_j (-1)^j a^{2m-j} b^j$.

**Source A.** ProofWiki, "Sum of Two Odd Powers" — https://proofwiki.org/wiki/Sum_of_Two_Odd_Powers (exactly this substitution, citing Spiegel, *Mathematical Handbook*, §2.21).

**Strategy B — strong induction with a quadratic recurrence.** Bases $m=0$ ($a+b$) and $m=1$ ($a^3+b^3 = (a+b)(a^2-ab+b^2)$). Step: $a^{2k+3} + b^{2k+3} = (a^2+b^2)(a^{2k+1}+b^{2k+1}) - a^2b^2(a^{2k-1}+b^{2k-1})$; IH at $k$ and $k-1$ plus closure of divisibility.

**Source B.** ProofWiki, "Sum of Odd Positive Powers" — https://proofwiki.org/wiki/Sum_of_Odd_Positive_Powers (strong induction with that expansion; cites Andrews §1-1 Ex. 18).

**Distinctness rationale.** A is a one-step change of variable plus an odd-power parity fact, delegating to a known factorization — no induction; B never substitutes $-b$ and climbs odd exponents two at a time via a quadratic recurrence.

**Signatures A (required).**
- `Odd.neg_pow` rewriting `(-b)^(2m+1) = -(b^(2m+1))`.
- Goal rewrite `a^N + b^N → a^N - (-b)^N` (`sub_neg_eq_add`).
- Difference-of-powers factorization/divisibility invoked at `(a, -b)`.
- Optionally the alternating cofactor `∑ (-1)^j a^(2m-j) b^j`.

**Signatures A (incompatible).**
- `induction m` / strong induction on the exponent.
- The auxiliary factors `(a^2 + b^2)` or `a^2 * b^2`.

**Signatures B (required).**
- Strong induction on `m` with bases m=0 AND m=1.
- The quadratic-recurrence identity closed by `ring`.
- `dvd_sub` / `Dvd.dvd.mul_left` on two IHs.

**Signatures B (incompatible).**
- Any `-b`, `Odd.neg_pow`, `neg_pow`.
- Any difference-of-powers factorization or alternating cofactor.

**Contamination risk.** HIGH — stock exercise; both routes widely reproduced; theorem sits in Mathlib.

**Automation/library caveats.** **SEVERE, same class as 028**: Mathlib's `Odd.add_dvd_pow_add_pow` (Mathlib/Algebra/Ring/GeomSum.lean) closes the goal route-blind via `exact Odd.add_dvd_pow_add_pow a b ⟨m, by ring⟩`. Needs import bans / self-containment — against uniform-rules design. `ring` alone can't close (∀m).

**Lean statement sketch.** `theorem add_dvd_odd_pow_add_pow {R : Type*} [CommRing R] (a b : R) (m : ℕ) : a + b ∣ a ^ (2 * m + 1) + b ^ (2 * m + 1)` — UNVERIFIED.

## Review notes

- **Sources**: two separate ProofWiki pages with book citations; fine.
- **Math checked (Claude)**: both routes correct.
- **Unique value**: route A's TYPE — reduction-to-a-known-case via sign substitution —
  is a strategy shape absent everywhere else in the pool. If the library-collapse
  problem is ever solved rubric-side (e.g. the 026-style "cited lemma must match the
  conditioned route" wording), this pair becomes attractive.
- **Sibling rule (agent-flagged)**: keep at most one of {028, 029}; prefer this one.
- **Verdict recommendation**: BENCH — behind 027 in the algebra domain; blocked by
  the same library-collapse concern as 028 unless the rubric wording resolves it.
