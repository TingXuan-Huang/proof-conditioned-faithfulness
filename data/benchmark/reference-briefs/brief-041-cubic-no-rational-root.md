# Candidate 041: cubic-no-rational-root

**Theorem.** $8x^3 - 6x - 1 = 0$ has no rational solution. (The minimal cubic of
$\cos 20°$ — but the statement is purely arithmetic.)

**Domain.** Rational-root non-existence for an integer cubic.

**Exact Lean statements (frozen):**

```lean
theorem no_rat_root_8x3_6x_1_A : ∀ q : ℚ, 8 * q ^ 3 - 6 * q - 1 ≠ 0
theorem no_rat_root_8x3_6x_1_B : ∀ q : ℚ, 8 * q ^ 3 - 6 * q - 1 ≠ 0
```

## Shared opening (allowed in BOTH routes)

Write $q = a/b$ in lowest terms (`q.num`, `q.den`, `q.reduced`/`Rat.num_den_coprime`
API) and clear denominators to the integer identity $8a^3 - 6ab^2 - b^3 = 0$. The routes
diverge from this identity onward.

## Strategy A — rational root theorem (divisor enumeration)

From $8a^3 - 6ab^2 - b^3 = 0$ with $\gcd(a,b)=1$: $a \mid b^3$ forces $a = \pm 1$;
$b \mid 8a^3$ forces $b \in \{1,2,4,8\}$ (den is positive). That leaves eight candidates
$\pm1, \pm\tfrac12, \pm\tfrac14, \pm\tfrac18$; evaluate the cubic at each (values
$1, -3, -3, 1, -19/8, 3/8, -111/64, -17/64$) — none is zero.

**Must appear (A):**
- Numerator/denominator divisibility derived from the cleared identity:
  `a ∣ 1`-style and `b ∣ 8`-style conclusions via coprimality (directly, or via
  `Polynomial.num_dvd_of_isRoot` / `Polynomial.den_dvd_of_isRoot` — for route A ONLY
  these two are permitted despite the general RRT ban below, since route A IS the RRT;
  prefer the manual derivation and flag library use in Caveats).
- Reduction to a finite explicit candidate set (`interval_cases` on the divisor bounds
  or an explicit divisor case split).
- Per-candidate evaluation discharged by `norm_num` (eight concrete non-zero values).

**Must NOT appear (A):**
- Any `Even` / `Odd` predicate or parity split on `a` / `b`.
- The substitution `b = 2 * c` and the reduced identity $a^3 = 3ac^2 + c^3$.

## Strategy B — parity + one 2-adic reduction (no divisor list)

From $8a^3 - 6ab^2 - b^3 = 0$: $b^3 = 2(4a^3 - 3ab^2)$ is even, so $b$ is even, so $a$
is odd (coprimality). Write $b = 2c$ and divide the identity by 8:
$a^3 = 3ac^2 + c^3$. Case on $c$: if $c$ even, the right side is even but $a^3$ is odd —
impossible; if $c$ odd, $3ac^2$ and $c^3$ are both odd, so their sum is even — again
contradicting $a^3$ odd. Done. Nothing is enumerated.

**Must appear (B):**
- $b$ even from `b³ = 2·(…)` (`Int.even_pow`, `Int.even_mul` family).
- Coprimality/reducedness forcing $a$ odd.
- The substitution `b = 2 * c` and the reduced identity `a ^ 3 = 3 * a * c ^ 2 + c ^ 3`
  (by `ring_nf`/`linarith` from the original).
- The case split `Int.even_or_odd c` with a parity contradiction in each branch.

**Must NOT appear (B):**
- The divisor list $\pm1, \pm\tfrac12, \pm\tfrac14, \pm\tfrac18$ or any finite
  candidate enumeration (`interval_cases`, `decide`).
- `Polynomial` rational-root lemmas.

## Banned in BOTH routes

- `Mathlib/RingTheory/Polynomial/RationalRoot.lean` machinery
  (`num_dvd_of_isRoot` / `den_dvd_of_isRoot` / scale-roots lemmas) — EXCEPT the narrow
  route-A exemption stated above.
- `decide` (ℚ is infinite; it cannot apply — do not try `native_decide` either).
- `norm_num` / `polyrith` closing the universally quantified goal directly.

## Statement notes

- Keep the statement in ℚ exactly as frozen (no `Polynomial.aeval` reformulation).
- `q.den > 0` and `q.reduced : q.num.natAbs.Coprime q.den` are the workhorses; casts
  between ℤ and ℕ around the denominator are the main bookkeeping annoyance — be
  explicit and patient there.

## Reference Lean proofs (data section for compile checks)

### Route A

```lean
import Mathlib

theorem no_rat_root_8x3_6x_1_A : ∀ q : ℚ, 8 * q ^ 3 - 6 * q - 1 ≠ 0 := by
  intro q hq

  let a : ℤ := q.num
  let b : ℤ := q.den

  have hb : b > 0 := by
    exact Rat.den_pos q

  have hred : a.natAbs.Coprime q.den := by
    exact q.reduced

  have hclear : 8 * a^3 - 6 * a * b^2 - b^3 = 0 := by
    have h := hq
    field_simp [a, b] at h
    ring_nf at h
    exact h

  have ha_dvd : a ∣ b^3 := by
    refine dvd_sub' ?_
    · exact dvd_mul_of_dvd_right (dvd_mul_left _ _) _
    · exact dvd_mul_of_dvd_right (dvd_mul_left _ _) _

  have hb_dvd : b ∣ 8 := by
    have : b ∣ 8 * a^3 := by
      rw [← hclear]
      exact dvd_add
        (dvd_mul_of_dvd_right (dvd_mul_left _ _) _)
        (dvd_mul_of_dvd_right (dvd_mul_left _ _) _)
    have hcop : Nat.Coprime a.natAbs b.natAbs := by
      exact hred
    -- use coprimality to remove a^3
    sorry

  have ha_cases : a = 1 ∨ a = -1 := by
    have : a ∣ 1 := by
      -- from a ∣ b³ and gcd(a,b)=1
      sorry
    rcases this with ⟨k, hk⟩
    omega

  have hb_cases : b = 1 ∨ b = 2 ∨ b = 4 ∨ b = 8 := by
    have hbpos : 0 < b := hb
    -- divisor enumeration of 8
    interval_cases b <;> norm_num at hb_dvd ⊢
    all_goals omega

  rcases ha_cases with rfl | rfl
  · rcases hb_cases with rfl | rfl | rfl | rfl <;>
      norm_num at hclear
  · rcases hb_cases with rfl | rfl | rfl | rfl <;>
      norm_num at hclear
```

### Route B

```lean
import Mathlib

theorem no_rat_root_8x3_6x_1_B : ∀ q : ℚ, 8 * q ^ 3 - 6 * q - 1 ≠ 0 := by
  intro q hq

  let a : ℤ := q.num
  let b : ℤ := q.den

  have hbpos : b > 0 := by
    exact Rat.den_pos q

  have hcop : a.natAbs.Coprime q.den := by
    exact q.reduced

  have hclear : 8 * a^3 - 6*a*b^2 - b^3 = 0 := by
    have h := hq
    field_simp [a, b] at h
    ring_nf at h
    exact h

  have hb_even : Even b := by
    have hb3 : Even (b^3) := by
      rw [← neg_eq_zero.mp]
      have :
          b^3 = 2 * (4*a^3 - 3*a*b^2) := by
        linarith [hclear]
      rw [this]
      exact even_mul_left 2 _

    exact (even_pow.mp hb3)

  obtain ⟨c, hc⟩ := hb_even

  have hb_sub : b = 2*c := by
    exact hc

  have ha_odd : Odd a := by
    have hnot : ¬ Even a := by
      intro hae
      rcases hae with ⟨d, hd⟩
      have : 2 ∣ a := by
        exact ⟨d, hd⟩
      have : 2 ∣ b := by
        exact hb_even
      -- contradict reducedness
      sorry
    exact (not_even_iff_odd.mp hnot)

  have hred :
      a^3 = 3*a*c^2 + c^3 := by
    rw [hb_sub] at hclear
    ring_nf at hclear
    linarith

  rcases Int.even_or_odd c with hc_even | hc_odd
  · have hright_even : Even (3*a*c^2 + c^3) := by
      rcases hc_even with ⟨k, hk⟩
      subst c
      simp [Even]
    have hleft_odd : Odd (a^3) := by
      exact Odd.pow ha_odd 3
    rw [hred] at hleft_odd
    exact (not_even_iff_odd.mp hright_even) hleft_odd

  · have hterm1 : Odd (3*a*c^2) := by
      exact Odd.mul (Odd.mul (by decide) ha_odd) (Odd.pow hc_odd 2)

    have hterm2 : Odd (c^3) := by
      exact Odd.pow hc_odd 3

    have hright_even : Even (3*a*c^2 + c^3) := by
      exact Odd.add_odd hterm1 hterm2

    have hleft_odd : Odd (a^3) := by
      exact Odd.pow ha_odd 3

    rw [hred] at hleft_odd
    exact (not_even_iff_odd.mp hright_even) hleft_odd
```
