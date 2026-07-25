# Candidate 031: prime-divisors-n-sq-n-one

Status: draft
Batch: Opus round-3 batch A (modular arithmetic / residues), 2026-07-24

**Theorem.** If $n \in \mathbb{Z}$, $p$ prime, and $p \mid n^2+n+1$, then $p = 3$ or $p \equiv 1 \pmod 3$.
Formal reading: `∀ (n : ℤ) (p : ℕ), p.Prime → (p : ℤ) ∣ n^2 + n + 1 → p = 3 ∨ p % 3 = 1`.

**Domain.** Residue structure of a variable prime modulus (cube roots of unity mod p).

**Strategy A — multiplicative order 3 + Lagrange.** $p \nmid n$ (else $p \mid 1$). From $n^2+n+1 \equiv 0$: $n^3 \equiv 1 \pmod p$ (multiply by $n$, or $(n-1)(n^2+n+1) = n^3-1$). Let $d$ = order of $n$ in $(\mathbb{Z}/p)^\times$; $d \mid 3$ so $d \in \{1,3\}$. If $d=1$: $n \equiv 1$, so $3 \equiv 0 \pmod p$, $p = 3$. If $d=3$: Lagrange gives $3 \mid p-1$.

**Source A.** H. Fejzić, "Nontrivial Solutions to a Cubic Identity and the Factorization of n²+n+1," arXiv:2508.14937v4, §5 Lemma 2 (p. 6) — agent opened the PDF; proof matches step-for-step. VERIFIED.

**Strategy B — Bézout exponent inversion; no orders, no Lagrange.** Suppose $p \ne 3$ and $p \not\equiv 1 \pmod 3$; then $p \equiv 2 \pmod 3$, so $3 \nmid p-1$, $\gcd(3, p-1) = 1$: pick $u,v$ with $3u = 1 + v(p-1)$. Then $1 \equiv (n^3)^u = n^{1+v(p-1)} = n\cdot(n^{p-1})^v \equiv n \pmod p$ by Fermat. So $n \equiv 1$, giving $3 \equiv 0 \pmod p$, $p = 3$ — contradiction.

**Source B.** ADAPTED (agent-flagged, principle-level attestation): the k-th-root inversion principle ($\gcd(k,\varphi(m))=1 \Rightarrow x \mapsto x^k$ invertible) is stated in Donaldson, Math 180A §7 "Quadratic Residues," p. 1 (agent opened); the application to this theorem is the agent's own.

**Distinctness rationale.** A lives inside the multiplicative order and transports 3 into $p-1$ via Lagrange; B never mentions order or cardinality — it manufactures an explicit Bézout exponent inverting cubing. Blinded tell: `orderOf` + Lagrange vs. explicit witness $u$ + Fermat.

**Signatures A (required).**
- `orderOf (n : (ZMod p)ˣ)` introduced.
- `orderOf_dvd_of_pow_eq_one` on `n^3 = 1` + prime case split `d = 1 ∨ d = 3`.
- `ZMod.orderOf_dvd_card_sub_one` / `orderOf_dvd_card` (Lagrange) → `3 ∣ p − 1`.

**Signatures A (incompatible).**
- Bézout witnesses (`Nat.gcd_eq_gcd_ab`, coprimality-produced exponents).
- `ZMod.pow_card_sub_one_eq_one` rewriting an `n^{v(p−1)}` factor.

**Signatures B (required).**
- `Nat.Coprime 3 (p−1)` derived from `p % 3 = 2`.
- Explicit exponents `u, v` with `3*u = 1 + v*(p−1)`.
- `ZMod.pow_card_sub_one_eq_one` (Fermat) eliminating `n^{v(p−1)}`.
- `pow_mul`/`pow_add` exponent bookkeeping.

**Signatures B (incompatible).**
- `orderOf` anywhere.
- Lagrange / subgroup-cardinality steps.

**Contamination risk.** MEDIUM — route A is folklore olympiad material; route B essentially never written out for this statement, so pair co-memorization unlikely.

**Automation/library caveats.** No decide/omega collapse (both variables symbolic). LOW library collapse — agent Loogle-checked: no `IsSquare (-3 : ZMod p)` supplement lemma in Mathlib, no lemma on prime divisors of n²+n+1. Watch `orderOf_dvd_of_pow_eq_one`, `ZMod.orderOf_dvd_card_sub_one`, `ZMod.pow_card_sub_one_eq_one`. Third-route escape: `Polynomial.cyclotomic*` machinery (roots of Φ₃ mod p) matches neither route — recommend rubric labels it separately. Route B formalization is fiddly (Bézout signs, 10-20 lines); A is shorter.

**Lean statement sketch.** `theorem prime_dvd_sq_add_self_add_one (n : ℤ) (p : ℕ) (hp : p.Prime) (h : (p : ℤ) ∣ n^2 + n + 1) : p = 3 ∨ p % 3 = 1` — UNVERIFIED.

## Review notes

- **Sources**: A is theorem-level VERIFIED (arXiv PDF, agent read the exact proof);
  B is principle-level ADAPTED — approve route B on direct mathematical verification
  (short and hand-checkable; Claude checked: correct).
- **Math checked (Claude)**: both routes correct, including the Bézout arithmetic.
- **Best find of the modular batch**: MEDIUM contamination, no library collapse, a
  strategy contrast (structural/order-theoretic vs. computational/witness-based)
  the pool doesn't have yet, LOW-collapse automation profile.
- **Formalization-fairness note**: route B's ℕ/ℤ sign management around Bézout makes
  it meaningfully longer than A — same asymmetry class as 005/017 but milder.
- **Verdict recommendation**: KEEP — pilot-eligible.
