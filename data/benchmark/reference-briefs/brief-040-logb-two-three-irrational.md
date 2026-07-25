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
$3 > 1$ and the base $> 1$), then $2^{p/q} = 3$, hence $2^p = 3^q$ in ℕ. This bridge is
deliberately shared and is the dominant formal component — that is by design (it burdens
neither route unfairly). Build it as a helper lemma; the routes diverge only AFTER
`2 ^ p = 3 ^ q` is on the board.

**Bridge scaffold (recommended).** The helper MUST carry the logb hypothesis — it is
unprovable from positivity alone:

```lean
private lemma irrational_logb_two_three_bridge (p d : ℕ) (hp : 0 < p) (hd : 0 < d)
    (h : Real.logb 2 3 = (p : ℝ) / (d : ℝ)) : (2 : ℕ) ^ p = 3 ^ d
```

Extraction, from `Irrational` unfolded: `rintro ⟨x, hx⟩` gives `x : ℚ` with
`(x : ℝ) = Real.logb 2 3`; `Real.logb_pos (by norm_num) (by norm_num)` gives
`0 < Real.logb 2 3`, hence `0 < x`; take `p := x.num.toNat`, `d := x.den`
(`Rat.num_div_den` + casts give the `h` above).

Two workable proof paths for the bridge — pick either:
- **log path (fewer rpow side conditions):** `Real.logb` unfolds to
  `Real.log 3 / Real.log 2`; from `h` and `Real.log_pos (by norm_num : (1:ℝ) < 2)`,
  `field_simp` yields `(d : ℝ) * Real.log 3 = (p : ℝ) * Real.log 2`; rewrite both sides
  with `Real.log_pow` backwards to get `Real.log ((3:ℝ) ^ d) = Real.log ((2:ℝ) ^ p)`;
  conclude `(3:ℝ) ^ d = (2:ℝ) ^ p` by injectivity of log on positives
  (`Real.log_injOn_pos`, or `Real.exp_log` applied to both positive sides); finish with
  `exact_mod_cast`.
- **rpow path:** `Real.rpow_logb (by norm_num) (by norm_num) (by norm_num) :
  (2:ℝ) ^ Real.logb 2 3 = 3`; substitute `h`; raise to the `d`-th power and collapse
  `((2:ℝ) ^ ((p:ℝ)/d)) ^ (d:ℝ)` via `← Real.rpow_natCast`, `← Real.rpow_mul
  (by norm_num : (0:ℝ) ≤ 2)`, `div_mul_cancel₀` (`(d:ℝ) ≠ 0`); cast down to ℕ.

Lemma names here are from-memory anchors — verify at compile time and flag drift in
Caveats per the common brief; do not withhold the artifact over them.

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
