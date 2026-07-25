# Candidate 044: two-pow-lt-factorial

Status: draft
Batch: Opus round-3 batch E (discrete/integer inequalities), 2026-07-24

**Theorem.** $2^n < n!$ for all $n \ge 4$.
Formal reading: `∀ n : ℕ, 4 ≤ n → 2 ^ n < Nat.factorial n`.

**Domain.** Exponential vs. factorial growth.

**Strategy A — induction anchored at 4.** Base: $16 < 24$. Step: $(k+1)! = (k+1)k! > (k+1)2^k \ge 2\cdot2^k$.

**Source A.** Hildebrand, Math 213 "Induction Proofs III" sampler, UIUC, Problem 5 — agent opened via Wayback Machine (live host refused connections). VERIFIED.

**Strategy B — split the product, compare factor by factor.** $n! = 24\prod_{j=5}^n j$ and $2^n = 16\prod_{j=5}^n 2$; same index set, each left factor $j \ge 5 > 2$; termwise product monotonicity + strict prefix comparison $24 > 16$. No induction hypothesis about the inequality is ever formed.

**Source B.** **UNVERIFIED for this exact statement (agent-flagged)** — the split-and-compare technique is verified on adjacent factorial inequalities (MSE 1964074 and MSE 1264448), but no opened source applies it to $2^n < n!$ itself.

**Distinctness rationale.** A is a `Nat.le_induction` skeleton consuming an IH; B converts both sides to `Finset` products over a shared interval and applies one termwise-domination lemma — no recursion on the goal.

**Signatures A (required).**
- `Nat.le_induction` (or guarded induction) outermost.
- IH literally `2 ^ k < k !` used in the step.
- `Nat.factorial_succ` + multiply-through + `2 ≤ k+1`.

**Signatures A (incompatible).**
- `Finset.prod` over an interval, `prod_Ico_id_eq_factorial`, `prod_const`.
- Factor-by-factor comparison across a shared index set.

**Signatures B (required).**
- `n!` as a Finset product (`Finset.prod_Ico_id_eq_factorial`-family) and `2^n` as `Finset.prod_const`.
- Product split at index 4 (`Finset.prod_Ico_consecutive`-family).
- Termwise domination (`Finset.prod_le_prod'`/`prod_lt_prod` or gcongr) with side goal `2 ≤ j`.
- Closed numeric `16 < 24` on the prefix.

**Signatures B (incompatible).**
- Any in-context hypothesis `2 ^ k < k !` (IH on the goal).
- `Nat.le_induction`/`Nat.rec` with the inequality as motive.

**Contamination risk.** HIGH for route A (among the most reproduced induction exercises anywhere); MEDIUM for route B (rare write-ups).

**Automation/library caveats.** Loogle-verified: no exact/near lemma (`_ ^ _ < Nat.factorial _` matches only the `Filter.Eventually` lemma `Nat.eventually_pow_lt_factorial_sub` — an awkward genuine shortcut to watch; threshold extraction non-automatic). Opposite direction only: `Nat.factorial_le_pow`. decide fixed-n only; omega blind to pow/factorial; gcongr inside route B's termwise step is expected and NOT evidence of route A.

**Lean statement sketch.** `theorem two_pow_lt_factorial {n : ℕ} (hn : 4 ≤ n) : 2 ^ n < n !` — UNVERIFIED.

## Review notes

- **Sources**: A verified (Wayback); **B is the weakest attestation in round 3** —
  technique-level only, exact statement unattested. Either find a written
  split-product proof of this exact fact or approve on direct verification.
- **Math checked (Claude)**: both routes correct.
- **Concerns**: route A is contamination-maximal as an induction exercise; the
  theorem is the classic "please induct" prompt, so conditioning on B tests
  something real (can the model resist the induction attractor?) — arguably the
  cleanest "attractor-resistance" probe in the pool.
- **Verdict recommendation**: BENCH — interesting probe, weak route-B attestation.
