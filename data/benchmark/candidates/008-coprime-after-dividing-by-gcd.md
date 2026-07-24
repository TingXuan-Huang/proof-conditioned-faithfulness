# Candidate 008: coprime-after-dividing-by-gcd

Status: draft
Batch: 3 (gcd / pigeonhole / well-ordering), Opus agent, 2026-07-24

**Theorem.** Let `d = gcd(a,b) > 0`. Then `a/d` and `b/d` are coprime. Formal reading: `d = gcd(a,b) ∧ d > 0 → gcd(a/d, b/d) = 1`.

**Domain.** gcd / well-ordering (maximality-of-gcd argument).

**Strategy A — Bézout, divide through.** By Bézout, `d = a·x + b·y` for integers `x,y`. Since `d ∣ a` and `d ∣ b`, divide the identity by `d`: `1 = (a/d)·x + (b/d)·y`. Thus `1` is an integer linear combination of `a/d` and `b/d`, so any common divisor of `a/d` and `b/d` divides `1`, giving `gcd(a/d, b/d) = 1`.

**Source A.** UMD Math 406, §3.3 "The Greatest Common Divisor" lecture notes, https://www.math.umd.edu/~immortal/MATH406/lecturenotes/ch3-3.pdf ; Gordon College NTIC, "The Bezout Identity," https://math.gordon.edu/ntic/ntic/section-bezout-id.html

**Strategy B — maximality contradiction (well-ordering).** Let `α` be any common divisor of `a/d` and `b/d`, so `a/d = α x` and `b/d = α y`. Then `a = (α d) x` and `b = (α d) y`, so `α d` is a common divisor of `a` and `b`. Because `d` is the *greatest* common divisor, `α d ≤ d`, forcing `α ≤ 1`, i.e. `α = 1`. Since the only positive common divisor of `a/d` and `b/d` is `1`, they are coprime.

**Source B.** UMD Math 406, §3.3 lecture notes (maximality argument stated in the notes), https://www.math.umd.edu/~immortal/MATH406/lecturenotes/ch3-3.pdf

**Distinctness rationale.** Route A constructs an explicit Bézout certificate `(a/d)x + (b/d)y = 1`; Route B never forms a combination and instead invokes the extremal (greatest/maximal) characterization of `gcd`, deriving `α d ≤ d`. A blinded reader distinguishes "linear-combination-equals-1" from "extremal `d·α ≤ d` contradiction."

**Signatures A (required).**
- Uses Bézout `d = a*x + b*y`.
- Divides the identity by `d` to get `1 = (a/d)*x + (b/d)*y`.
- Concludes coprimality from a combination equal to `1`.

**Signatures A (incompatible).**
- Invokes the "greatest"/maximality property of `gcd` (an inequality `d*α ≤ d`).
- Assumes a divisor `α` and multiplies back up to `a`, `b`.

**Signatures B (required).**
- Introduces an arbitrary common divisor `α` of `a/d`, `b/d` and writes `a = α*d*x`, `b = α*d*y`.
- Shows `α*d` is a common divisor of `a`, `b`, then bounds it by `d` via maximality (`Nat.le_of_dvd` / gcd's greatest property).
- Concludes `α ≤ 1`.

**Signatures B (incompatible).**
- Any Bézout equation or division of a Bézout identity by `d`.
- A linear combination of `a/d`, `b/d` equal to `1`.

**Contamination risk.** MEDIUM — the statement matches Mathlib's `Nat.coprime_div_gcd_div_gcd`, so the true statement is well known; however the maximality route is generated far less often than the Bézout route, preserving strategy-level separation.

**Lean statement sketch.** `theorem coprime_div_gcd {a b : ℕ} (h : 0 < Nat.gcd a b) : Nat.Coprime (a / Nat.gcd a b) (b / Nat.gcd a b)` — UNVERIFIED.

## Review notes

- **Why MEDIUM contamination**: statement is a known library lemma, but the *pairing*
  (Bézout vs. maximality) is not a standard textbook duo; the maximality route is
  under-generated relative to Bézout.
- **Mathlib caution — exact lemma exists**: `Nat.coprime_div_gcd_div_gcd` closes this in
  one line. Same library-lookup policy question as 002/005/007. This is now a *pattern*
  across candidates: the frozen rubric needs one general rule for library-call outputs
  before the pilot.
- **Cross-domain value**: route B is the pool's only genuine well-ordering/extremal
  argument so far — worth keeping for strategy diversity even if the statement is
  library-known.
- **Single-source caveat**: both routes attested from the same UMD notes; consider
  finding one independent second source for route B before the publish gate.
