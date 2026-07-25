# Candidate 039: sqrt2-plus-sqrt3-irrational

Status: draft
Batch: Opus round-3 batch D (irrationality / field arithmetic), 2026-07-24

**Theorem.** $\sqrt2 + \sqrt3$ is irrational. Formal reading: `Irrational (Real.sqrt 2 + Real.sqrt 3)`.

**Domain.** Irrationality of a sum of quadratic surds.

**Strategy A — conjugate/reciprocal reduction to Irrational √2.** Set $a = \sqrt3+\sqrt2$, $b = \sqrt3-\sqrt2$; $ab = 1$. If $a$ were rational then $b = 1/a$ is rational, so $a - b = 2\sqrt2$ is rational — contradicting irrationality of $\sqrt2$. No polynomial, no divisibility, no case analysis.

**Source A.** MSE 5124183, answer https://math.stackexchange.com/a/5124318 (agent opened; verbatim match), pointing also to https://math.stackexchange.com/a/93469.

**Strategy B — minimal polynomial + rational root theorem.** $r = \sqrt2+\sqrt3$ satisfies $r^4 - 10r^2 + 1 = 0$ (square twice). A rational root $p/q$ in lowest terms forces $q = 1$, $p \mid 1$, so $p = \pm1$; both give $1 - 10 + 1 = -8 \ne 0$. No appeal to any square root's irrationality.

**Source B.** MSE 5124183, Anne Bauval's answer https://math.stackexchange.com/a/5124196; independently Physics Forums thread 273982 (both opened by agent).

**Distinctness rationale.** A: two-line field manipulation ending in known irrationality of √2, no polynomial. B: explicit monic quartic ending in integer-divisibility/finite-candidate check, never citing a root's irrationality. Blinded tell: "conjugate + reciprocal" vs. "quartic + rational-root."

**Signatures A (required).**
- Auxiliary term `√3 − √2` (or the reciprocal) with `(√3+√2)(√3−√2) = 1` via `Real.sq_sqrt` + nonneg side goals.
- ℚ-closure under `⁻¹`, `−`: exhibits `√2 = ((q:ℝ) − (q:ℝ)⁻¹)/2`.
- Terminal `irrational_sqrt_two` (or `Nat.Prime.irrational_sqrt` at 2).

**Signatures A (incompatible).**
- The quartic `x^4 − 10x^2 + 1`, `Polynomial` machinery, `Rat.num/den` divisibility.
- Finite root-candidate enumeration.

**Signatures B (required).**
- Derivation `r^4 − 10r^2 + 1 = 0` (`Real.sq_sqrt` at 2, 3, 6 + ring normalization).
- Transfer to ℚ with `Rat.num/den` coprimality or Mathlib rational-root lemmas.
- Finite check of ±1 via `norm_num`/`decide`.

**Signatures B (incompatible).**
- `irrational_sqrt_two`, `Nat.Prime.irrational_sqrt`, `irrational_sqrt_natCast_iff`.
- Constructing the conjugate or reciprocal.

**Contamination risk.** HIGH — stock exercise; a single 2026 MSE thread carries BOTH routes.

**Automation/library caveats.** No Mathlib lemma on sums of square roots (Loogle-checked). **Serious third route (agent-flagged)**: `Irrational √6` via norm_num extension, then `Irrational (5 + 2√6)` via `Irrational.ratCast_*`, then `Irrational.of_pow` after rewriting $(√2+√3)^2$ — ~4 lines, bypasses both routes; grader must label it separately.

**Lean statement sketch.** `theorem irrational_sqrt_two_add_sqrt_three : Irrational (Real.sqrt 2 + Real.sqrt 3)` — UNVERIFIED.

## Review notes

- **Sources**: forum-based but agent-opened with verbatim matches; fine for
  verification-based approval.
- **Math checked (Claude)**: both routes correct.
- **Concerns**: HIGH contamination (both routes co-located in one thread), a 4-line
  third-route bypass, and ℝ/`Real.sqrt` API weight. The conjugate route is elegant
  and formally distinctive, though.
- **Verdict recommendation**: BENCH — 040/041 are the stronger irrationality items.
