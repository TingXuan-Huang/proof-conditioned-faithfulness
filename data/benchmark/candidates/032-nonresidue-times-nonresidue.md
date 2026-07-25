# Candidate 032: nonresidue-times-nonresidue

Status: draft
Batch: Opus round-3 batch A (modular arithmetic / residues), 2026-07-24

**Theorem.** For an odd prime $p$ and nonzero non-squares $a, b$ mod $p$: $ab$ is a square mod $p$.
Formal reading: `∀ p [Fact p.Prime], p ≠ 2 → ∀ a b : ZMod p, a ≠ 0 → b ≠ 0 → ¬IsSquare a → ¬IsSquare b → IsSquare (a * b)`.

**Domain.** Quadratic-residue structure for a variable odd prime.

**Strategy A — Euler's criterion (exponent computation).** $c^{(p-1)/2} \equiv \pm 1$ with $+1$ exactly for squares (Fermat + root-counting in a field). Non-squares give $-1$, so $(ab)^{(p-1)/2} \equiv (-1)(-1) = 1$, and the converse direction of Euler's criterion makes $ab$ a square.

**Source A.** Donaldson, Math 180A §7, Theorem 7.9 (Euler's Criterion, full proof, p. 3) + Theorem 7.6 part 3 (QR×NR multiplication table) — agent opened. Wikipedia "Legendre symbol" §Properties corroborates. The $(-1)(-1)$ chaining is ADAPTED wording.

**Strategy B — cardinality + translation bijection (no exponents).** $|Q| = |N| = (p-1)/2$ (squaring is exactly 2-to-1 on $(\mathbb{Z}/p)^\times$ since $x^2 = y^2 \Rightarrow x = \pm y$ and $x \ne -x$ for odd $p$). $Q \cdot Q \subseteq Q$. For non-square $a$, $\mu(x) = ax$ is a bijection with $\mu(Q) \subseteq N$; injectivity + equal cardinalities force $\mu(Q) = N$, hence $\mu(N) = Q$. So $ab = \mu(b) \in Q$.

**Source B.** Donaldson, same PDF, Theorem 7.6 part 3 proof (the μ-bijection, "maps QR's bijectively to NR's and must therefore map NR's back to QR's") + Lemma 7.3 (the counting) — agent opened; full written proof, not a sketch. VERIFIED.

**Distinctness rationale.** A is a pure exponent computation never mentioning the residue SET or its size; B never raises to a power and works in any finite abelian group with an index-2 subgroup. Blinded tell: "$(p-1)/2$, Fermat, ±1" vs. "$|Q|=|N|$, bijection μ, image counting."

**Signatures A (required).**
- Exponent `(p−1)/2` (`p / 2` in Lean) explicit.
- `ZMod.euler_criterion` both directions.
- `mul_pow`/`pow_mul` combining `a^{p/2} * b^{p/2}`.
- `neg_mul_neg` / `ZMod.neg_one_ne_one` landing on 1.

**Signatures A (incompatible).**
- Any `Finset.card`/`Fintype.card` of residue sets.
- Any explicit `Equiv`/bijection between residues and non-residues.

**Signatures B (required).**
- Cardinality equality squares vs. non-squares (`Finset.filter` + `card_image_of_injOn`).
- Explicit multiplication bijection (`Equiv.mulLeft₀` / `mul_right_injective₀`).
- Field step `x² = y² → x = y ∨ x = −y`.
- Injective-implies-surjective on finite (`Finite.injective_iff_surjective` / `Finset.surj_on_of_inj_on_of_card_le`).

**Signatures B (incompatible).**
- Exponent `p/2` / `(p−1)/2` anywhere.
- `ZMod.euler_criterion`, `pow_card_sub_one_eq_one`, `quadraticChar_eq_pow_of_char_ne_two'`.

**Contamination risk.** MEDIUM-HIGH — first-course staple; route A near-certainly memorized; route B's explicit μ-bijection written out much less often.

**Automation/library caveats.** No decide/omega collapse (variable prime; `IsSquare` invisible to omega). **MEDIUM library collapse with an asymmetric twist (agent-flagged)**: `quadraticChar` bundled as `MulChar` + `map_mul` + `quadraticChar_eq_one/neg_one_iff` closes it in ~4 lines — and that shortcut is MORALLY route A (Euler's criterion packaged as a character), so it satisfies A while letting a model fake B. Grader must treat the whole `quadraticChar`/`legendreSym` namespace as route-A-signature territory. Route B is 25-40 lines vs. ~10 for A — sharpest length asymmetry of the round.

**Lean statement sketch.** `theorem nonsq_mul_nonsq (p : ℕ) [Fact p.Prime] (hp : p ≠ 2) (a b : ZMod p) (ha : a ≠ 0) (hb : b ≠ 0) (hna : ¬ IsSquare a) (hnb : ¬ IsSquare b) : IsSquare (a * b)` — UNVERIFIED.

## Review notes

- **Sources**: both routes fully written out in one open PDF (Donaldson 180A) with
  Wikipedia corroboration for A. Single-document concentration caveat (like 016/021).
- **Math checked (Claude)**: both routes correct.
- **Novel rubric insight worth keeping regardless of verdict**: a library shortcut
  can be route-ASYMMETRIC — `quadraticChar` silently implements A. The rubric's
  library policy (see 026 notes) needs to handle "library lemma ≈ one route's
  compressed form," not just route-blind closures. 022's Vandermonde note is the
  same phenomenon; this is the cleanest statement of it.
- **Verdict recommendation**: BENCH — good pair, but 031 is the stronger modular
  keeper and B's length asymmetry is steep.
