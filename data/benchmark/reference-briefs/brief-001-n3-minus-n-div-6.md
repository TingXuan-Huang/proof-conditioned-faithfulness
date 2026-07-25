# Candidate 001: n3-minus-n-div-6

**Theorem.** For every integer $n$, $6 \mid n^3 - n$.

**Domain.** Divisibility (integer reasoning).

**Exact Lean statements (frozen):**

```lean
theorem six_dvd_cube_sub_self_A (n : ℤ) : (6 : ℤ) ∣ n ^ 3 - n
theorem six_dvd_cube_sub_self_B (n : ℤ) : (6 : ℤ) ∣ n ^ 3 - n
```

## Strategy A — factorization into three consecutive integers

Factor $n^3 - n = n(n^2-1) = (n-1)\,n\,(n+1)$, the product of three consecutive
integers. Among any three consecutive integers at least one is divisible by $2$ and at
least one is divisible by $3$, so $2 \mid (n-1)n(n+1)$ and $3 \mid (n-1)n(n+1)$. Since
$\gcd(2,3)=1$, their product $6$ also divides it. No induction is used; the argument is
a fixed algebraic decomposition plus a residue fact about consecutive integers.

**Must appear (A):**
- The explicit factorization $n^3-n=(n-1)\,n\,(n+1)$ as the crux (e.g. proved by `ring`).
- Divisibility by 2 and by 3 established from the consecutive-integer structure
  (e.g. `Int.even_mul_succ_self`, or an explicit residue argument) — with no inductive
  hypothesis anywhere in scope.
- The combination $2\mid x \land 3\mid x \Rightarrow 6\mid x$ via coprimality
  (e.g. `Nat.Coprime.mul_dvd_of_dvd_of_dvd` / `IsCoprime.mul_dvd`).

**Must NOT appear (A):**
- Any `induction` / `Int.induction_on` / `Nat.rec` on `n`; any base case + step split.

## Strategy B — induction on n

Base case $n=0$: $0^3-0=0$ and $6\mid 0$. Inductive step: assume $6 \mid k^3-k$. Then
$(k+1)^3-(k+1) = (k^3-k) + 3k(k+1)$. The first summand is divisible by 6 by the
inductive hypothesis; in the second, $k(k+1)$ is a product of two consecutive integers,
hence even, so $3k(k+1)$ is divisible by 6. A sum of two multiples of 6 is a multiple
of 6.

**Implementation note (negatives).** The statement is over ℤ. Preferred shape: `induction
n using Int.induction_on` — base 0, a $k\to k+1$ step exactly as above, and a $k\to k-1$
step with the mirrored algebra $(k-1)^3-(k-1) = (k^3-k) - 3k(k-1)$, $k(k-1)$ even.
Alternative (also acceptable): prove the ℕ version by ordinary induction and extend to
negatives via the oddness of $n^3 - n$ (i.e. $(-n)^3-(-n) = -(n^3-n)$ and `Dvd.dvd.neg`).
Either way the theorem statement itself stays exactly as frozen above.

**Must appear (B):**
- An induction eliminator on `n` with the base case explicitly discharged.
- The inductive hypothesis $6\mid k^3-k$ actually used in the step.
- The leftover term $3k(k\pm1)$ isolated by ring normalization, with $k(k\pm1)$ shown
  even.

**Must NOT appear (B):**
- The three-term product $(n-1)n(n+1)$ as the load-bearing decomposition.
- Closing the goal for generic `n` without a base/step split.

## Banned in BOTH routes

- Any exhaustive mod-6 (or mod-2/mod-3) case split that closes the whole goal in one
  sweep (e.g. `Int.emod_emod_of_dvd` + `decide`-style residue enumeration, or
  `omega` after a `n % 6` split). That is a third route, not A or B.
- `decide` / `norm_num` discharging the main divisibility goal directly.
