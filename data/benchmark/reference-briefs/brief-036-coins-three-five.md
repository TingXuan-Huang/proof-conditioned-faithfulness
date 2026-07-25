# Candidate 036: coins-three-five

**Theorem.** Every $n \ge 8$ is a sum of nonnegative multiples of 3 and 5.

**Domain.** Well-ordering vs. strong induction (additive representation).

**Exact Lean statements (frozen):**

```lean
theorem coins_three_five_A (n : ℕ) (hn : 8 ≤ n) : ∃ a b : ℕ, n = 3 * a + 5 * b
theorem coins_three_five_B (n : ℕ) (hn : 8 ≤ n) : ∃ a b : ℕ, n = 3 * a + 5 * b
```

## Strategy A — strong induction, three base cases (constructive-forward)

Bases: $8 = 3+5$, $9 = 3\cdot3$, $10 = 5\cdot2$. For $n \ge 11$: apply the inductive
hypothesis to $n-3 \ge 8$ and add one more 3. The proof COMPUTES a representation for
every $n$ via the eliminator.

**Must appear (A):**
- A strong-induction eliminator driving the main goal (`Nat.strong_induction_on`,
  `Nat.strongRecOn`, or `Nat.le_induction`-based equivalent).
- A three-way base split at 8/9/10 with literal witnesses `(1,1)`, `(3,0)`, `(0,2)`.
- The IH instantiated at `n − 3`, with the side goal `8 ≤ n − 3` discharged from
  `11 ≤ n` (mind ℕ subtraction).
- Constructive throughout: no `by_contra` / `Classical.em` / `push_neg` at top level.

**Must NOT appear (A):**
- `Nat.find` / `Nat.find_spec` / `Nat.find_min`, `WellFounded.min`, or any
  least-counterexample hypothesis.

## Strategy B — well-ordering / least counterexample (classical-backward)

Suppose the set of "bad" $n \ge 8$ (with no representation) is nonempty. Well-ordering
gives a least bad $c$; checking 8, 9, 10 directly forces $c \ge 11$; then $c - 3 \ge 8$
is smaller than $c$, hence good, and adding one 3 to its representation makes $c$ good —
contradiction. The proof touches only ONE hypothetical value; the load-bearing step is
minimality, not an inductive hypothesis.

**Must appear (B):**
- `by_contra` + `push_neg` producing `∃ n, 8 ≤ n ∧ ¬∃ a b, …` (or the equivalent
  nonempty bad-set formulation).
- The least element obtained via `Nat.find` (or `WellFounded.min` / `Nat.lt_wfRel`).
- Minimality invoked at `c − 3` via `Nat.find_min` (or the min-property) with the
  side goal `c − 3 < c`.
- Ends in a contradiction — it never returns a witness for an arbitrary `n`.

**Must NOT appear (B):**
- Any induction eliminator driving the main goal.
- An inductive hypothesis applied to `n − 3` inside an induction block.

## Banned in BOTH routes

- `frobeniusNumber_pair`, `exists_frobeniusNumber_iff`,
  `AddSubmonoid.mem_closure_pair` (Chicken McNugget library collapse).
- Third route (i): "stamp-swapping" ordinary induction (replace a 5 by 3+3, or three
  3s by two 5s in the step) — this is neither A nor B; do not use it in either proof.
- Third route (ii): case split on `n % 3` with `omega`-produced witnesses closing each
  residue class. Also neither A nor B.
- `omega` may discharge arithmetic SIDE goals (e.g. `8 ≤ n − 3`), but must not produce
  the existential witnesses for the main goal.

## Reference Lean proofs (data section for compile checks)

### Route A

```lean
import Mathlib

theorem coins_three_five_A (n : ℕ) (hn : 8 ≤ n) : ∃ a b : ℕ, n = 3 * a + 5 * b := by
  induction n using Nat.strong_induction_on with
  | h n ih =>
      by_cases hle : n ≤ 10
      · have hcases : n = 8 ∨ n = 9 ∨ n = 10 := by
          omega
        rcases hcases with rfl | rfl | rfl
        · exact ⟨1, 1, by norm_num⟩
        · exact ⟨3, 0, by norm_num⟩
        · exact ⟨0, 2, by norm_num⟩
      · have hn11 : 11 ≤ n := by
          omega
        have hsmall : 8 ≤ n - 3 := by
          omega
        obtain ⟨a, b, hab⟩ := ih (n - 3) (by omega) hsmall
        refine ⟨a + 1, b, ?_⟩
        omega
```

### Route B

```lean
import Mathlib

theorem coins_three_five_B (n : ℕ) (hn : 8 ≤ n) : ∃ a b : ℕ, n = 3 * a + 5 * b := by
  by_contra h
  push_neg at h

  let P : ℕ → Prop := fun k =>
    8 ≤ k ∧ ¬ ∃ a b : ℕ, k = 3 * a + 5 * b

  have hP : ∃ k, P k := by
    refine ⟨n, hn, ?_⟩
    intro hrep
    rcases hrep with ⟨a, b, hab⟩
    exact h a b hab

  have hc : P (Nat.find hP) := Nat.find_spec hP

  have hc11 : 11 ≤ Nat.find hP := by
    by_contra hlt
    have hle : Nat.find hP ≤ 10 := by
      omega
    have hcases : Nat.find hP = 8 ∨ Nat.find hP = 9 ∨ Nat.find hP = 10 := by
      omega
    rcases hcases with h8 | h9 | h10
    · subst h8
      exact hc.2 ⟨1, 1, by norm_num⟩
    · subst h9
      exact hc.2 ⟨3, 0, by norm_num⟩
    · subst h10
      exact hc.2 ⟨0, 2, by norm_num⟩

  have hlt : Nat.find hP - 3 < Nat.find hP := by
    omega

  have hnot : ¬ P (Nat.find hP - 3) := Nat.find_min hP hlt

  have hsmall : P (Nat.find hP - 3) := by
    constructor
    · omega
    · intro hrep
      rcases hrep with ⟨a, b, hab⟩
      apply hc.2
      refine ⟨a + 1, b, ?_⟩
      omega

  exact hnot hsmall
```
