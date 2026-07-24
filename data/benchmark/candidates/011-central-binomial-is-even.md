# Candidate 011: central-binomial-is-even

Status: draft
Batch: 4 (low-contamination hunt), Opus agent, 2026-07-24

**Theorem.** For every $n \ge 1$, $2 \mid \binom{2n}{n}$.
Formal reading: `∀ n : ℕ, 1 ≤ n → 2 ∣ Nat.choose (2*n) n`.

**Domain.** Elementary combinatorics / divisibility of binomial coefficients.

**Strategy A — Pascal + symmetry (algebraic).** By Pascal's rule, $\binom{2n}{n} = \binom{2n-1}{n-1} + \binom{2n-1}{n}$. By symmetry $\binom{N}{k} = \binom{N}{N-k}$ with $N = 2n-1$, $k = n$: $\binom{2n-1}{n} = \binom{2n-1}{n-1}$. Therefore $\binom{2n}{n} = 2\binom{2n-1}{n-1}$, an explicit factor of 2. (Valid for $n \ge 1$.)

**Source A.** HandWiki, *Central binomial coefficient*, Properties ("½·C(2n,n) = C(2n−1,n−1) for n>0") — https://handwiki.org/wiki/Central_binomial_coefficient ; combinatorial statement: https://brainly.com/question/39440624 ; symmetry rule: ProofWiki, https://proofwiki.org/wiki/Symmetry_Rule_for_Binomial_Coefficients

**Strategy B — fixed-point-free involution (bijective parity).** $\binom{2n}{n}$ counts $n$-element subsets of a $2n$-element set $X$. Define $\iota(S) = X \setminus S$: it maps $n$-subsets to $n$-subsets, is an involution, and has no fixed point ($S = X\setminus S$ would force $S = \varnothing$, contradicting $|S| = n \ge 1$). A fixed-point-free involution partitions the family into 2-element orbits $\{S, X\setminus S\}$, so the count is even.

**Source B.** Evenness-by-fixed-point-free-involution is the standard parity principle: cp4space, *Involutions on a finite set* — https://cp4space.hatsya.com/2021/12/02/involutions-on-a-finite-set/ ; nLab, *involution* — https://ncatlab.org/nlab/show/involution . The complement-involution instantiation is standard.

**Distinctness rationale.** Strategy A is a two-line manipulation of binomial identities yielding a literal factor 2; Strategy B never touches a binomial identity and instead exhibits a fixed-point-free involution on the subset family. "Algebraic identity" vs. "counting/involution."

**Signatures A (required).**
- Pascal identity (`Nat.choose_succ_succ` / recurrence).
- Symmetry `Nat.choose_symm` (or `Nat.choose_symm_diff`).
- Exhibits witness `2 * Nat.choose (2*n-1) (n-1)`.

**Signatures A (incompatible).**
- No `Finset.powersetCard` / subset enumeration.
- No involution / card-pairing argument.

**Signatures B (required).**
- `Nat.choose` as `Finset.powersetCard` cardinality.
- Complement map on `Finset` and its involutivity; no fixed point from `n ≥ 1`.
- Even-cardinality-from-fixed-point-free-involution (orbit pairing).

**Signatures B (incompatible).**
- No Pascal recurrence use.
- No explicit algebraic factor `2 * choose (2n-1) (n-1)`.

**Contamination risk.** LOW — rarely posed as a standalone theorem (usually subsumed under Kummer/2-adic results), and this A/B pairing is not a standard textbook duo.

**Lean statement sketch.** `theorem two_dvd_central_choose (n : ℕ) (hn : 1 ≤ n) : 2 ∣ Nat.choose (2*n) n` — UNVERIFIED.

## Review notes

- **Why LOW contamination**: the standalone evenness statement is rarely a named
  exercise; the involution route especially is unlikely to be memorized for this
  specific statement.
- **Formalization asymmetry to scrutinize**: route A is ~3 Mathlib lemma applications;
  route B needs a fixed-point-free-involution-implies-even-card argument, which may
  require real Finset work — check whether Mathlib has a ready orbit-pairing lemma
  (`Finset.even_card` variants) before assuming route B is fairly achievable at
  comparable length. Asymmetric difficulty biases responsiveness (same concern class
  as 005/009).
- **Nat-subtraction edge**: `2n-1`, `n-1` in ℕ need the `n ≥ 1` hypothesis threaded
  carefully in route A's Lean form.
