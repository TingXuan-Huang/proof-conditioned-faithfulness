# Candidate 033: digits-perm-nine

**Theorem.** If two naturals have the same multiset of base-10 digits, 9 divides their
difference.

**Domain.** Base-10 digit representation (casting-out-nines family).

**Exact Lean statements (frozen):**

```lean
theorem digits_perm_sub_dvd_nine_A (m n : ℕ)
    (h : (Nat.digits 10 m).Perm (Nat.digits 10 n)) : (9 : ℤ) ∣ (m : ℤ) - (n : ℤ)
theorem digits_perm_sub_dvd_nine_B (m n : ℕ)
    (h : (Nat.digits 10 m).Perm (Nat.digits 10 n)) : (9 : ℤ) ∣ (m : ℤ) - (n : ℤ)
```

## Strategy A — digit-sum invariant (congruence route)

$10^i \equiv 1 \pmod 9$ (since $10^i - 1 = 9\cdot\underbrace{1\ldots1}_i$), so every
number is congruent to its digit sum mod 9, termwise over the digit expansion.
The permutation hypothesis is consumed exactly once: sums are rearrangement-invariant,
so $S(m) = S(n)$. Subtract the two congruences $m \equiv S(m)$, $n \equiv S(n)$.

**Must appear (A):**
- `(Nat.digits 10 _).sum` as an explicit intermediate object.
- The permutation consumed by `List.Perm.sum_eq` (route A is EXEMPT from the
  both-routes ban on this one lemma) and nowhere else.
- Two congruences `x ≡ (digits x).sum [MOD 9]` (or the ZMOD/Int form) combined by
  subtraction/transitivity.
- **Explicitness requirement:** derive the congruence `n ≡ S(n) [MOD 9]` yourself by
  induction over the digit expansion (`Nat.ofDigits` cons-step, using `10 ≡ 1 [MOD 9]`),
  rather than citing a one-shot library lemma. If the manual derivation truly blows up,
  you may fall back to `Nat.modEq_digits_sum`-family lemmas — but flag the fallback
  prominently in Caveats.

**Must NOT appear (A):**
- Case analysis / structural recursion over `List.Perm` constructors.
- Manipulation of place-value differences `10^i − 10^j`.

## Strategy B — position-displacement / swap invariance (no digit sums)

Induct structurally on the permutation itself. In the displacement view,
$m - n = \sum_i d_i(10^{\sigma(i)} - 10^i)$ and $9 \mid 10^a - 10^b$ always
($= 10^b(10^{a-b}-1)$, geometric sum). Generator form over `List.Perm` constructors:
`nil` gives 0; `cons` prepends the same digit to both sides (an established difference
is multiplied by 10); `swap` of two adjacent digits changes the value by a multiple of 9
($ab - ba$ pattern: $10\cdot x + y - (10\cdot y + x) = 9(x - y)$); `trans` chains
divisibilities. The digit sum is never formed.

**Implementation note (expected proof shape).** Do NOT try to induct on `h` with the
goal still phrased in `m`/`n`. Prove a helper lemma generalized over lists —

```lean
lemma digits_perm_sub_dvd_nine_B_aux (a b : List ℕ) (h : a.Perm b) :
    (9 : ℤ) ∣ (Nat.ofDigits 10 a : ℤ) - (Nat.ofDigits 10 b : ℤ)
```

— by `induction h`, then finish the main theorem by rewriting with
`Nat.ofDigits_digits` and applying the helper. Recall that `List.Perm.swap` is
HEADS-ONLY: `Perm (y :: x :: l) (x :: y :: l)`. It never swaps arbitrary positions —
arbitrary rearrangements are generated through `cons`/`trans` — so the four cases are:
`nil` (0), `cons` (difference = 10·(X−Y), use the cons equation once per side),
`swap` (two cons unfoldings per side give (y + 10x + 100·Z) − (x + 10y + 100·Z)
= 9(x−y)), `trans` (chain via `dvd_sub`-style algebra / `sub_add_sub_cancel`).
This helper does not violate the digit-sum ban — no sum is ever formed.

**Must appear (B):**
- Structural induction over the `List.Perm` hypothesis (`induction h` with
  nil/cons/swap/trans cases), in the generalized helper-lemma form above.
- A visible algebraic step producing the factor 9 (the swap case's $9(x-y)$, or
  $10^c - 1 = 9\cdot\Sigma 10^j$).
- Place-value arithmetic through `Nat.ofDigits 10 (d :: L) = d + 10 * Nat.ofDigits 10 L`
  with divisibility carried through multiplication by 10.

**Must NOT appear (B):**
- Any `(Nat.digits 10 _).sum` or reduction to digit-sum equality.
- `List.Perm.sum_eq`.

## Banned in BOTH routes (Mathlib collapse lemmas)

`Nat.modEq_nine_digits_sum`, `Nat.dvd_iff_dvd_digits_sum`, `Nat.nine_dvd_iff`,
`Nat.modEq_three_digits_sum`, `Nat.modEq_eleven_digits_sum`, `Nat.three_dvd_iff`.
(Route A's explicitness requirement above is the controlled exception path.)

## Reference Lean proofs (data section for compile checks)

### Route A

```lean
import Mathlib

private lemma digits_perm_sub_dvd_nine_A_modEq_digits_sum
    (n : ℕ) :
    (n : ℤ) ≡ ((Nat.digits 10 n).sum : ℤ) [ZMOD 9] := by
  -- Intended proof:
  -- Expand n = Nat.ofDigits 10 (Nat.digits 10 n)
  -- Then induct over the digit list.
  --
  -- The core induction step uses:
  -- Nat.ofDigits 10 (d :: xs)
  --   = d + 10 * Nat.ofDigits 10 xs
  --
  -- and the fact:
  -- 10 ≡ 1 [ZMOD 9].
  --
  -- Exact Mathlib names for these lemmas may require adjustment.
  sorry


theorem digits_perm_sub_dvd_nine_A (m n : ℕ)
    (h : (Nat.digits 10 m).Perm (Nat.digits 10 n)) :
    (9 : ℤ) ∣ (m : ℤ) - (n : ℤ) := by

  have hm :
      (m : ℤ) ≡ ((Nat.digits 10 m).sum : ℤ) [ZMOD 9] :=
    digits_perm_sub_dvd_nine_A_modEq_digits_sum m

  have hn :
      (n : ℤ) ≡ ((Nat.digits 10 n).sum : ℤ) [ZMOD 9] :=
    digits_perm_sub_dvd_nine_A_modEq_digits_sum n

  have hsum :
      (Nat.digits 10 m).sum = (Nat.digits 10 n).sum := by
    exact List.Perm.sum_eq h

  have hmn :
      (m : ℤ) ≡ (n : ℤ) [ZMOD 9] := by
    calc
      (m : ℤ)
          ≡ ((Nat.digits 10 m).sum : ℤ) [ZMOD 9] := hm
      _ = ((Nat.digits 10 n).sum : ℤ) := by
        rw [hsum]
      _ ≡ (n : ℤ) [ZMOD 9] := hn.symm

  -- Convert ZMOD congruence to divisibility of difference.
  exact hmn.dvd
```

### Route B

```lean
import Mathlib

private lemma digits_perm_sub_dvd_nine_B_aux
    (a b : List ℕ)
    (h : a.Perm b) :
    (9 : ℤ) ∣
      (Nat.ofDigits 10 a : ℤ) -
      (Nat.ofDigits 10 b : ℤ) := by

  induction h with

  | nil =>
      simp

  | @cons x l₁ l₂ h ih =>
      -- Nat.ofDigits cons equation:
      --
      -- x + 10 * ofDigits l₁
      -- -
      -- x + 10 * ofDigits l₂
      --
      -- = 10 * (ofDigits l₁ - ofDigits l₂)
      --
      -- Carry divisibility through multiplication by 10.

      simp [Nat.ofDigits]
      obtain ⟨k, hk⟩ := ih
      refine ⟨10 * k, ?_⟩
      ring_nf
      rw [hk]
      ring

  | @swap x y l =>
      -- The critical algebraic step:
      --
      -- (y + 10*x + 100*Z)
      -- -
      -- (x + 10*y + 100*Z)
      --
      -- = 9*(x-y)

      simp [Nat.ofDigits]
      refine ⟨(x : ℤ) - y, ?_⟩
      ring

  | @trans l₁ l₂ l₃ h₁ h₂ ih₁ ih₂ =>
      obtain ⟨a, ha⟩ := ih₁
      obtain ⟨b, hb⟩ := ih₂

      refine ⟨a + b, ?_⟩
      ring_nf
      linarith


theorem digits_perm_sub_dvd_nine_B (m n : ℕ)
    (h : (Nat.digits 10 m).Perm (Nat.digits 10 n)) :
    (9 : ℤ) ∣ (m : ℤ) - (n : ℤ) := by

  have haux :=
    digits_perm_sub_dvd_nine_B_aux
      (Nat.digits 10 m)
      (Nat.digits 10 n)
      h

  simpa [Nat.ofDigits_digits] using haux
```

## Statement notes

- `Nat.digits` produces little-endian digit lists with no leading zeros — the `Perm`
  hypothesis is on exactly those lists; do not "normalize" them further.
- The conclusion subtracts in ℤ deliberately (ℕ subtraction truncates). Keep casts as
  written; `Nat.ofDigits_digits` recovers `m` and `n` from their expansions.
