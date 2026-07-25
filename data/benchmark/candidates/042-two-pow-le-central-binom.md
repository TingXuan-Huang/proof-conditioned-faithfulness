# Candidate 042: two-pow-le-central-binom

Status: draft
Batch: Opus round-3 batch E (discrete/integer inequalities), 2026-07-24

**Theorem.** $2^n \le \binom{2n}{n}$ for all $n$ (strict for $n \ge 2$).
Formal reading: `∀ n : ℕ, 2 ^ n ≤ Nat.choose (2 * n) n`.

**Domain.** Discrete growth: exponential vs. central binomial.

**Strategy A — counting / explicit injection ("one from each pair").** Split $[2n]$ into pairs $P_i = \{2i-1, 2i\}$. Each of the $2^n$ sign vectors picks one element per pair, giving an $n$-subset; the map is injective (the parity of $S_\varepsilon \cap P_i$ recovers $\varepsilon(i)$). So $2^n \le \binom{2n}{n}$. Strictness for $n \ge 2$: $T = \{1,2\} \cup \{2i : 3 \le i \le n\}$ is an $n$-set that is no $S_\varepsilon$.

**Source A.** MSE 1264448 ("2ⁿ(n!)² ≤ (2n)!", one-per-pair reading) + MSE 448861 (explicit injection f(X) checked 1-1) — agent opened both.

**Strategy B — induction on the central-binomial recurrence (ratio).** $b_{n+1}/b_n = (2n+2)(2n+1)/(n+1)^2 = (4n+2)/(n+1) \ge 2 = a_{n+1}/a_n$; base $1 = 1$; induct. Strictness propagates from $(4n+2)/(n+1) > 2$ for $n \ge 1$.

**Source B.** Same MSE threads (ratio-computation answers) — agent opened.

**Distinctness rationale.** A: no factorials, no induction — build an injection from $\mathrm{Bool}^n$ into $n$-subsets, finish by cardinality monotonicity. B: no sets — a recurrence/ratio computation wrapped in `Nat.rec`.

**Signatures A (required).**
- Pairing structure on a $2n$ carrier (partition into $n$ 2-blocks, or `Fin n → Bool → Fin (2*n)`).
- `Function.Injective`/`Set.InjOn` obligation discharged by reconstructing ε.
- Cardinality bridge: `Nat.choose_eq_card_powersetCard`-style + `Finset.card_le_card_of_injOn`/`Fintype.card_le_of_injective`.

**Signatures A (incompatible).**
- `Nat.rec`/`Nat.le_induction` with the inequality as motive.
- `Nat.succ_mul_centralBinom_succ` or factorial-cancellation of C(2n+2,n+1).

**Signatures B (required).**
- Top-level `induction n` with IH `2 ^ n ≤ (2*n).choose n`.
- The recurrence `(n+1)·C(2n+2,n+1) = 2(2n+1)·C(2n,n)` (or factorial equivalent).
- Arithmetic side goal (`2(n+1) ≤ 2(2n+1)`) by omega/linarith.

**Signatures B (incompatible).**
- `Finset`/`Fintype` cardinality reasoning, `powersetCard`, injection lemmas.
- Boolean-vector-indexed families of subsets.

**Contamination risk.** MEDIUM — well-travelled Q&A/competition chestnut, but no exact-lemma leakage.

**Automation/library caveats.** Loogle-verified ABSENT from Mathlib (`2 ^ _ ≤ centralBinom/choose` → 0 matches); adjacent-but-different: `Nat.centralBinom_le_four_pow`, `Nat.four_pow_le_two_mul_self_mul_centralBinom`, `Nat.choose_le_centralBinom`, `Nat.two_le_centralBinom`. Route B is library-assisted (`Nat.succ_mul_centralBinom_succ` + `centralBinom_eq_two_mul_choose` → 5-10 lines) — formal-effort asymmetry favoring B. omega/decide/nlinarith/positivity/gcongr can't close alone.

**Lean statement sketch.** `theorem two_pow_le_choose_two_mul (n : ℕ) : 2 ^ n ≤ (2 * n).choose n` — UNVERIFIED.

## Review notes

- **Sources**: MSE threads, agent-opened; adequate for verification-based approval.
- **Math checked (Claude)**: both routes correct, including the strictness witness
  (T has $2 + (n-2) = n$ elements, contains both of $P_1$, misses $P_2$).
- **Value**: first exponential-vs-binomial growth item; injection route is
  automation-resistant; no exact library hit (Loogle-verified). Mild proof-shape
  overlap: injection-counting resembles 011/016/021's bijection family.
- **Verdict recommendation**: KEEP — core-eligible; pilot-plausible if a counting
  slot remains after 023/024.
