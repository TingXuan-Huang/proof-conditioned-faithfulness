# Candidate 007: coprime-multiplicative

Status: draft
Batch: 3 (gcd / pigeonhole / well-ordering), Opus agent, 2026-07-24

**Theorem.** If `a` is coprime to `n` and `b` is coprime to `n`, then `ab` is coprime to `n`. Formal reading: `gcd(a,n)=1 ∧ gcd(b,n)=1 → gcd(a·b, n)=1`.

**Domain.** gcd / Bézout-style coprimality.

**Strategy A — Bézout coefficients.** By Bézout there are integers `x,y` with `ax + ny = 1` and integers `u,v` with `bu + nv = 1`. Multiply the two equations:
`1 = (ax+ny)(bu+nv) = ab(xu) + n(axv + buy + nyv)`.
This exhibits `1` as an integer linear combination of `ab` and `n`. Any common divisor of `ab` and `n` divides the right side, hence divides `1`, so `gcd(ab,n)=1`.

**Source A.** University of South Carolina, Number Theory HW (Howard), https://people.math.sc.edu/howard/Classes/580f/hw4.pdf ; Brilliant, "Bézout's Identity," https://brilliant.org/wiki/bezouts-identity/

**Strategy B — Euclid's lemma / prime divisors.** Suppose for contradiction `gcd(ab,n) > 1`; let `p` be a prime dividing both `ab` and `n`. By Euclid's lemma, `p ∣ ab` forces `p ∣ a` or `p ∣ b`. If `p ∣ a`, then `p` divides both `a` and `n`, contradicting `gcd(a,n)=1`; if `p ∣ b`, it contradicts `gcd(b,n)=1`. So no prime divides both `ab` and `n`, hence `gcd(ab,n)=1`.

**Source B.** Wellesley, Math 223 Assignment 3 Solutions (Schultz), https://palmer.wellesley.edu/~aschultz/w18/math223/homework/w18_223_hwk03_solns.pdf ; Brainly worked solution, https://brainly.com/question/33061188

**Distinctness rationale.** Route A produces an explicit integer certificate `ab·X + n·Y = 1` by algebraic multiplication of two Bézout equations; Route B never forms a linear combination and instead reasons about an arbitrary common prime factor via Euclid's lemma and contradiction. A blinded reader sees "constructive combination" vs. "prime-divisor case split."

**Signatures A (required).**
- Introduces Bézout witnesses `a*x + n*y = 1` and `b*u + n*v = 1`.
- Multiplies the two equations and regroups into `a*b*X + n*Y = 1`.
- Concludes coprimality from a linear combination equal to `1` (e.g. `Nat.Coprime` via `IsCoprime`/Bézout).

**Signatures A (incompatible).**
- Uses `Nat.Prime.dvd_mul` / Euclid's lemma or a "let `p` be a common prime divisor" step.
- Argues by contradiction from `gcd(ab,n) > 1`.

**Signatures B (required).**
- Instantiates an arbitrary (prime) common divisor and applies `p ∣ ab → p ∣ a ∨ p ∣ b`.
- Case split on `p ∣ a` vs `p ∣ b`, each contradicting a coprimality hypothesis.
- Uses only divisibility/prime facts, no explicit integers `x,y`.

**Signatures B (incompatible).**
- Any Bézout equation `a*x + n*y = 1`.
- Algebraic product-of-two-equations regrouping.

**Contamination risk.** MEDIUM — a standard intro-number-theory exercise (both routes appear in course notes), so the Bézout route in particular may be readily reproduced, though it is not a famous named theorem.

**Lean statement sketch.** `theorem coprime_mul {a b n : ℕ} (ha : Nat.Coprime a n) (hb : Nat.Coprime b n) : Nat.Coprime (a * b) n` — UNVERIFIED.

## Review notes

- **Why MEDIUM contamination**: both routes are standard course material, but the
  theorem isn't a named identity — verbatim joint recall of the exact A/B pairing is
  unlikely.
- **Mathlib caution**: `Nat.Coprime.mul` is exactly this statement — the library-lookup
  third behavior applies (see 002/005 notes). The ℤ/`IsCoprime` phrasing may partly
  dodge the one-liner; decide statement form at approval.
- **What to scrutinize**: whether Bézout on ℕ (vs ℤ) makes route A awkward in Lean —
  `Nat.gcd_eq_gcd_ab` gives integer coefficients; the statement may be cleanest over ℤ.
