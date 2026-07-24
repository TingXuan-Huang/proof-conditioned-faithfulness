# Candidate 015: sq-sum-ge-prod-abc

Status: draft
Batch: 5 (Fibonacci / recurrences / AM-GM), Opus agent, 2026-07-24

**Theorem.** For all real $a,b,c$: $a^2+b^2+c^2 \ge ab+bc+ca$ (equality iff $a=b=c$).
Formal reading: `∀ a b c : ℝ, a*b + b*c + c*a ≤ a^2 + b^2 + c^2`.

**Domain.** Elementary three-variable inequality (AM-GM family).

**Strategy A — sum of squares (SOS).** Directly:
$$2\big(a^2+b^2+c^2-ab-bc-ca\big)=(a-b)^2+(b-c)^2+(c-a)^2\ge 0.$$
Divide by 2. Equality forces each square to vanish, i.e. $a=b=c$.

**Source A.** cut-the-knot, "ab+bc+ca does not exceed a²+b²+c²," Proofs 3-4, https://www.cut-the-knot.org/m/Algebra/AbBcCaLeAaBbCc.shtml ; also math-only-math, "Express as sum of squares."

**Strategy B — Cauchy–Schwarz.** Apply Cauchy–Schwarz to $u=(a,b,c)$ and $v=(b,c,a)$:
$$ab+bc+ca = u\cdot v \le \lVert u\rVert\,\lVert v\rVert = \sqrt{a^2+b^2+c^2}\,\sqrt{b^2+c^2+a^2} = a^2+b^2+c^2.$$
Equality in Cauchy–Schwarz requires $u, v$ proportional, which with the cyclic permutation forces $a=b=c$.

**Source B.** Same cut-the-knot page, Proof 12 (Cauchy–Schwarz).

**Distinctness rationale.** A is a self-contained ring identity plus nonnegativity of squares (no external theorem). B invokes a named structural inequality on a chosen pair of vectors — a different lemma and proof term. (The pairwise-AM-GM route was deliberately avoided: in Lean it collapses to the same `sq_nonneg` witnesses as A and would not be genuinely distinct.)

**Signatures A (required).**
- Polynomial/ring identity $2(\text{LHS}-\text{RHS})=\sum(\cdot)^2$.
- Nonnegativity of real squares (`sq_nonneg`).
- Purely elementary, no external inequality theorem.

**Signatures A (incompatible).**
- Does not invoke Cauchy–Schwarz / inner-product norm bound.
- Introduces no auxiliary vectors.

**Signatures B (required).**
- Cauchy–Schwarz / inner-product-norm inequality as a lemma (`inner_mul_le_norm_mul_norm` or `Finset.inner_mul_le_norm_mul_norm`).
- Explicit paired vectors $(a,b,c)$ and $(b,c,a)$.
- Identification $\lVert(a,b,c)\rVert^2=\lVert(b,c,a)\rVert^2=a^2+b^2+c^2$.

**Signatures B (incompatible).**
- No explicit sum-of-three-squares algebraic identity.
- Does not reduce solely to `sq_nonneg` of pairwise differences.

**Contamination risk.** MEDIUM — the inequality is textbook-common and the SOS proof ubiquitous, but the SOS-vs-Cauchy-Schwarz pairing yields two demonstrably different formal shapes.

**Lean statement sketch.** `theorem sq_sum_ge_cyclic (a b c : ℝ) : a*b + b*c + c*a ≤ a^2 + b^2 + c^2` — UNVERIFIED.

## Review notes

- **Why MEDIUM contamination**: famous inequality, ubiquitous SOS proof — but the
  benchmark pairing deliberately uses Cauchy–Schwarz as B rather than the near-duplicate
  pairwise-AM-GM, which preserves genuine formal-shape separation. The discovery agent's
  reasoning on *why* AM-GM was excluded (it collapses to A's `sq_nonneg` witnesses in
  Lean) is itself a useful precedent for future curation: distinctness must survive
  formalization, not just read differently informally.
- **The `nlinarith` problem**: the statement is a one-call `nlinarith`/`polyrith` target
  — the strongest automation-collapse case in the pool (worse than 001/003/010). Both
  strategies can be entirely bypassed. Signature rubric must decide: is a bare
  `nlinarith` proof mixed_or_alternative? (Provisionally yes, matching the
  library-lookup policy.) Expect many such outputs on this item — which may itself be
  scientifically interesting (does proof-conditioning suppress automation reliance?).
- **Route B overhead**: Cauchy–Schwarz via inner-product spaces pulls in
  `EuclideanSpace`/`inner` machinery — check the realistic formal length vs. route A's
  ~3 lines. Sharpest difficulty asymmetry in the pool.
