# Candidate 028: sub-dvd-pow-sub-pow

Status: draft
Batch: Opus round-2 batch C (elementary algebra / divisibility), 2026-07-24

**Theorem.** In a commutative ring $R$: $(a-b) \mid (a^n - b^n)$ for all $a, b \in R$, $n \in \mathbb{N}$.
Formal reading: `∀ (a b : R) (n : ℕ), a - b ∣ a ^ n - b ^ n`.

**Domain.** Algebraic divisibility / factorization.

**Strategy A — explicit cofactor by telescoping cancellation.** Let $S = \sum_{j=0}^{n-1} a^{n-1-j} b^j$. Then $aS$ has leading term $a^n$, $bS$ reindexes to end at $b^n$, and the overlapping terms cancel pairwise: $(a-b)S = a^n - b^n$. Divisibility with explicit witness $S$.

**Source A.** ProofWiki, "Difference of Two Powers," Proof 1 (shift-and-subtract computation) — https://proofwiki.org/wiki/Difference_of_Two_Powers (cites Andrews, *Number Theory* 1971, §1-1 Ex. 3).

**Strategy B — strong induction with a two-term recurrence.** Bases $n=0$ (everything divides 0) and $n=1$. Step via $a^{k+1} - b^{k+1} = (a+b)(a^k - b^k) - ab(a^{k-1} - b^{k-1})$ (checked by expansion); apply the IH at $k$ and $k-1$ and closure of divisibility under ring multiples and subtraction.

**Source B.** ProofWiki, same page, Proof 4 (complete finite induction with that recurrence).

**Distinctness rationale.** A produces a closed-form cofactor with zero recursion (a `Dvd.intro` with a `Finset.sum` witness); B writes down no factor at all and climbs a two-step recurrence (`Nat.strong_induction_on`, two base cases).

**Signatures A (required).**
- Explicit witness `⟨∑ j ∈ range n, a^(n-1-j) * b^j, _⟩` / `Dvd.intro`.
- `Finset.sum` reindexing (`sum_range_succ'`-family).
- `Finset.mul_sum` / `sum_sub_distrib` forming `a*S - b*S` with middle-block cancellation.
- No recursion on `n`.

**Signatures A (incompatible).**
- `induction n` / `Nat.strong_induction_on` structuring the main goal.
- Two base cases, or IH used at both k and k−1.

**Signatures B (required).**
- `Nat.strong_induction_on` (or two-step `Nat.rec`) on the exponent.
- Separate n=0 and n=1 bases.
- The recurrence identity closed by `ring`.
- `dvd_sub` + `Dvd.dvd.mul_left` on two IHs.

**Signatures B (incompatible).**
- Any `Finset.sum` witness in the divisibility proof.
- `Finset.mul_sum` / reindexing lemmas.

**Contamination risk.** HIGH — among the most reproduced elementary divisibility results; both proofs verbatim in countless texts and prior formalization corpora.

**Automation/library caveats.** **SEVERE (agent-flagged, exact locations given)**: Mathlib has the exact result `sub_dvd_pow_sub_pow` and `Commute.sub_dvd_pow_sub_pow` (Mathlib/Algebra/Ring/GeomSum.lean), plus `geom_sum₂_mul` which IS route A's identity. `exact sub_dvd_pow_sub_pow a b n` closes the goal route-blind. Usable only with import bans or self-containment requirements — both against the benchmark's uniform-rules design.

**Lean statement sketch.** `theorem sub_dvd_pow_sub_pow' {R : Type*} [CommRing R] (a b : R) (n : ℕ) : a - b ∣ a ^ n - b ^ n` — UNVERIFIED.

## Review notes

- **Sources**: single-site (both routes from one ProofWiki page) but that page cites
  Andrews; attestation fine.
- **Math checked (Claude)**: both routes correct.
- **Library collapse is disqualifying-grade**: exact Mathlib lemma + route A's
  identity as a named lemma — same failure mode as 025, second-worst in pool.
- **Sibling redundancy (agent-flagged)**: 029 covers overlapping ground with a
  fresher route-A type; keep at most one of {028, 029}, prefer 029.
- **Verdict recommendation**: REJECT-leaning bench — file value is as a second
  library-collapse fixture for S5; not a benchmark pair.
