# Candidate 040: logb-two-three-irrational

**Theorem.** $\log_2 3$ is irrational.

**Domain.** Irrationality of a logarithm (prime-to-prime base); elementary integer
arithmetic after clearing the exponent.

**Exact Lean statements (frozen):**

```lean
theorem irrational_logb_two_three_A : Irrational (Real.logb 2 3)
theorem irrational_logb_two_three_B : Irrational (Real.logb 2 3)
```

## Shared bridge (allowed and expected in BOTH routes)

Both routes start identically: if $\log_2 3 = p/q$ with $p, q \ge 1$ (positivity because
$3 > 1$ and the base $> 1$), then $2^{p/q} = 3$, hence $2^p = 3^q$ in ℕ. Useful API:
`Real.rpow_natCast`, `Real.rpow_logb` / `Real.logb_eq_iff_rpow_eq`, positivity lemmas,
and cast injectivity to land in ℕ. This bridge is deliberately shared — build it as a
common-shaped opening (or a helper lemma per proof); the routes diverge only AFTER
`2 ^ p = 3 ^ q` is on the board.

## Strategy A — parity

$2^p$ is even (since $p \ge 1$); $3^q$ is odd (a product of odds). An even number cannot
equal an odd number. Contradiction.

**Must appear (A):**
- The bridge to `2 ^ p = 3 ^ q` with `p, q ≥ 1`.
- `Even (2 ^ p)` (e.g. `Nat.even_pow` / `dvd_pow_self`, from `p ≠ 0`).
- `Odd (3 ^ q)` (e.g. `Odd.pow`).
- The even/odd exclusion closing the proof (`Nat.even_iff_not_odd` or similar).

**Must NOT appear (A):**
- `Nat.Coprime` / `Nat.gcd` / `Nat.Coprime.pow` relating the two sides.
- `Nat.factorization` / `padicValNat` / `multiplicity`.

## Strategy B — coprimality of powers

From $2^c = 3^d$: $\gcd(2,3) = 1$ lifts to $\gcd(2^c, 3^d) = 1$. But the two numbers are
EQUAL, so this is $\gcd(N, N) = 1$, i.e. $N = 1$ — yet $N = 2^c \ge 2$. Contradiction.
Parity is never mentioned; the argument works verbatim for $\log_3 5$.

**Must appear (B):**
- The same bridge to `2 ^ c = 3 ^ d`.
- `Nat.Coprime 2 3` lifted by `Nat.Coprime.pow`.
- The rewrite to `Nat.Coprime N N`, then `N = 1` via `Nat.coprime_self_iff_one`,
  contradicted by `2 ≤ 2 ^ c`.

**Must NOT appear (B):**
- Any `Even` / `Odd` predicate or parity case split.
- Exponent counting via `Nat.factorization` / `padicValNat` / `multiplicity`.

## Banned in BOTH routes

- The unique-factorization third route: comparing prime factorizations /
  `Nat.factorization` / `padicValNat` / `multiplicity` exponent counting.
- Loogle shows **no** Mathlib declaration matching `Irrational (Real.logb _ _)` — there
  is no library one-liner; do not hunt for one. `decide` / `norm_num` cannot touch the
  main goal.

## Statement notes

- `Irrational x` unfolds to `x ∉ Set.range ((↑) : ℚ → ℝ)`; opening move is typically
  `rintro ⟨q, hq⟩` (after `rw [Irrational]`-style setup or `Rat.not_irrational`-adjacent
  API). Getting from `q` to positive naturals `p, q` uses `3 > 1 → logb 2 3 > 0`, so
  `q.num > 0` — handle the num/den bookkeeping explicitly.
- The `Real.logb` bridge is the hard formal work and it is SHARED — spend your care
  there once, then keep each route's divergent half short and unmistakable.
