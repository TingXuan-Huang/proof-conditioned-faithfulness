# Candidate 033: digits-perm-nine

Status: draft
Batch: Opus round-3 batch B (digits / base representation / sums), 2026-07-24

**Theorem.** If two naturals have the same multiset of base-10 digits, 9 divides their difference.
Formal reading: `∀ m n : ℕ, (Nat.digits 10 m).Perm (Nat.digits 10 n) → (9 : ℤ) ∣ (m : ℤ) − (n : ℤ)`.

**Domain.** Base-10 digit representation (casting-out-nines family).

**Strategy A — digit-sum invariant (congruence route).** $10^i \equiv 1 \pmod 9$ (since $10^i - 1 = 9\cdot\underbrace{1\ldots1}_i$), so $n \equiv S(n) \pmod 9$ termwise. Permutation ⟹ $S(m) = S(n)$ (sums are rearrangement-invariant — the hypothesis is used exactly once, here). Subtract the congruences.

**Source A.** Talwalkar, "Number Minus Reverse Is Divisible By 9," MindYourDecisions, 2023-06-01 (agent opened; derivation matches). Corroborating: Wikipedia "Casting out nines" (agent opened).

**Strategy B — position-displacement / swap invariance (no digit sums).** Match digit $d_i$ at position $i$ in $n$ to position $\sigma(i)$ in $m$: $m - n = \sum_i d_i(10^{\sigma(i)} - 10^i)$, and $9 \mid 10^a - 10^b$ always ($10^b(10^{a-b}-1)$, geometric sum). Generator form: adjacent digit swap changes the value by $9(a-b)$; prepending a digit multiplies an established difference by 10. The digit sum is never formed.

**Source B.** Quintanilla, "A mathematical magic trick," Mean Green Math (UNT), 2013-06-24 (agent opened; exact displacement formula with the three-case argument). Swap base step: Cuemath NCERT solution page (agent opened).

**Distinctness rationale.** A routes through one global invariant (digit sum), consuming the permutation only via sum-invariance; B accounts per-digit displacement between place values, extracting 9 from $10^a - 10^b$. Blinded tell: does $S(n)$ ever appear.

**Signatures A (required).**
- `(Nat.digits 10 _).sum` as an explicit intermediate object.
- Permutation consumed by `List.Perm.sum_eq` and nowhere else.
- Two congruences `x ≡ S(x) [MOD 9]` combined by transitivity/subtraction.

**Signatures A (incompatible).**
- Case analysis / structural recursion over `List.Perm` constructors.
- Manipulation of place-value differences `10^i − 10^j` or `Nat.ofDigits` cons-cells.

**Signatures B (required).**
- Structural induction over `List.Perm` (or explicit displacement sum).
- Visible algebraic step producing the factor 9 from a swap or from `10^c − 1 = 9·Σ 10^j`.
- Place-value arithmetic `Nat.ofDigits 10 (d :: L) = d + 10 * Nat.ofDigits 10 L` with divisibility through ×10.

**Signatures B (incompatible).**
- Any `(Nat.digits 10 _).sum`, `Nat.modEq_nine_digits_sum`, `Nat.nine_dvd_iff`, `List.Perm.sum_eq`.
- Reduction to digit-sum equality.

**Contamination risk.** MEDIUM — the digit-sum route is everywhere; the permutation-form theorem and the `List.Perm`-induction shape are uncommon in public corpora.

**Automation/library caveats.** **Asymmetric collapse (agent-verified against mathlib4 docs)**: route A collapses to ~4 lines via `Nat.modEq_nine_digits_sum` + `List.Perm.sum_eq`; the full ban list is in the file source (also `Nat.dvd_iff_dvd_digits_sum`, `Nat.nine_dvd_iff`, `Nat.modEq_three/eleven_digits_sum`). Route B stays ~12 lines. `omega`/`decide` inapplicable. Statement care: `Perm` on digit lists excludes leading-zero pseudo-rearrangements; ℤ-subtraction avoids ℕ truncation.

**Lean statement sketch.** `theorem digits_perm_sub_dvd_nine (m n : ℕ) (h : (Nat.digits 10 m).Perm (Nat.digits 10 n)) : (9 : ℤ) ∣ (m : ℤ) - (n : ℤ)` — UNVERIFIED.

## Review notes

- **Sources**: blog/education sites rather than textbooks, but agent opened all four
  and the math is elementary; both routes independently attested.
- **Math checked (Claude)**: both routes correct; the statement-form choices (Perm
  hypothesis, ℤ subtraction) show real care.
- **Fresh domain**: first digit-representation candidate; route B's List.Perm
  structural induction is a formal shape nothing else in the pool has.
- **Same asymmetric-collapse pattern as 032** (library lemma ≈ route A compressed):
  more evidence for the rubric wording flagged in 026/032 review notes.
- **Verdict recommendation**: KEEP — pilot-eligible if the rubric's library policy
  is settled first; otherwise core.
