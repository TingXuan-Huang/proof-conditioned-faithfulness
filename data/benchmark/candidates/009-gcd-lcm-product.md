# Candidate 009: gcd-lcm-product

Status: draft
Batch: 3 (gcd / pigeonhole / well-ordering), Opus agent, 2026-07-24

**Theorem.** For positive integers `a,b`: `gcd(a,b) · lcm(a,b) = a·b`.

**Domain.** gcd / lcm divisibility.

**Strategy A — prime-factorization exponents.** Write `a = ∏ p_i^{x_i}` and `b = ∏ p_i^{y_i}` over the common set of primes. Then `gcd(a,b) = ∏ p_i^{min(x_i,y_i)}` and `lcm(a,b) = ∏ p_i^{max(x_i,y_i)}`. For each prime, `min(x_i,y_i) + max(x_i,y_i) = x_i + y_i`. Multiplying gcd and lcm therefore gives `∏ p_i^{x_i + y_i} = a·b`.

**Source A.** UMD Math 406, §3.5 "The Fundamental Theorem of Arithmetic," https://www.math.umd.edu/~immortal/MATH406/lecturenotes/ch3-5.pdf ; Brainly worked proof, https://brainly.com/question/48606803

**Strategy B — Bézout / coprime-reduction via divisibility.** Set `d = gcd(a,b)`, write `a = d a'`, `b = d b'` with `gcd(a',b')=1`. Claim `m := d a' b' = ab/d` is the least common multiple. It is a common multiple: `m = a b'` and `m = a' b`. It divides every common multiple: if `a ∣ c` and `b ∣ c`, then since `gcd(a',b')=1`, coprime factors multiply to give `d a' b' ∣ c`. Hence `lcm(a,b) = ab/d`, so `gcd·lcm = ab`. Never uses prime factorizations.

**Source B.** ProofWiki, "Product of GCD and LCM," https://proofwiki.org/wiki/Product_of_GCD_and_LCM ; UMD Math 406 §3.3 notes (coprime-reduction lemmas).

**Distinctness rationale.** Route A is a per-prime exponent computation resting on `min+max = sum`; Route B is a divisibility/universal-property argument that avoids factorization entirely. A blinded reader sees "exponent vectors + min/max" vs. "divides-all-common-multiples with coprime lifting."

**Signatures A (required).**
- Introduces prime-exponent representations (`Nat.factorization`) of `a`, `b`.
- Expresses gcd/lcm as per-prime min/max of exponents (`Nat.factorization_gcd`, `Nat.factorization_lcm`).
- Uses the identity `min x y + max x y = x + y`.

**Signatures A (incompatible).**
- Any Bézout step or `gcd(a',b')=1` coprime reduction.
- A "divides every common multiple" universal-property argument for lcm.

**Signatures B (required).**
- Reduces `a = d*a'`, `b = d*b'` with `Nat.Coprime a' b'`.
- Shows `a*b/d` is a common multiple and divides an arbitrary common multiple `c` via coprime lifting.
- Concludes via lcm's least/universal property, no exponent vectors.

**Signatures B (incompatible).**
- Any use of `Nat.factorization` / per-prime min/max.
- The `min x y + max x y = x + y` step.

**Contamination risk.** MEDIUM-HIGH — this is the named identity `Nat.gcd_mul_lcm` in Mathlib and a staple textbook result; the statement and at least the prime-factorization proof are very likely memorized. The divisibility route provides some separation.

**Lean statement sketch.** `theorem gcd_mul_lcm (a b : ℕ) : Nat.gcd a b * Nat.lcm a b = a * b` — UNVERIFIED.

## Review notes

- **Why MEDIUM-HIGH contamination**: named textbook identity, exact Mathlib lemma
  (`Nat.gcd_mul_lcm`), and the factorization proof is the canonical one. Third
  candidate in the familiar bucket behind 002/005 — the pool now has more HIGH-ish
  items than the ⅓-familiar target wants; expect at most one of {002, 005, 009} in the
  pilot.
- **Library-lookup issue at its worst**: the theorem name IS the Mathlib lemma name.
  Same rubric-policy dependency as 002/005/007/008.
- **Formalization asymmetry to scrutinize**: route A via `Nat.factorization` is real
  Mathlib machinery but verbose; route B is closer to how Mathlib itself proves it —
  asymmetric difficulty can bias responsiveness, same concern as 005 route B.
