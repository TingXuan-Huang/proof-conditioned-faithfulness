# Candidate 043: choose-lt-pow

Status: draft
Batch: Opus round-3 batch E (discrete/integer inequalities), 2026-07-24

**Theorem.** For $n \ge k \ge 2$: $\binom{n}{k} < n^k$.
Formal reading: `∀ n k : ℕ, 2 ≤ k → k ≤ n → Nat.choose n k < n ^ k`.

**Domain.** Binomial coefficient vs. power.

**Strategy A — falling-factorial algebra.** $\binom{n}{k} < n!/(n-k)! = n(n-1)\cdots(n-k+1)$ (since $k! \ge 2$), a product of $k$ factors each $\le n$ — so $\le n^k$; strictness from the factor $n-1 < n$ present when $k \ge 2$.

**Source A.** ProofWiki, "N Choose k is not greater than n^k," Proof 1 — agent opened.

**Strategy B — counting maps (strictly increasing vs. arbitrary).** $\binom{n}{k}$ = number of strictly increasing maps $[k] \to [n]$ (unique enumeration of each $k$-subset); $n^k$ = number of ALL maps. Proper inclusion for $k \ge 2$: the constant map 1 is not strictly increasing.

**Source B.** Same ProofWiki page, Proof 2 — agent opened.

**Distinctness rationale.** A is pure ℕ-arithmetic (cancel $k!$, bound a product termwise), never mentions a set or map; B never touches factorials — both sides become cardinalities of function spaces, closed by a proper-subset witness.

**Signatures A (required).**
- `choose` via `Nat.descFactorial`/factorial (`Nat.choose_eq_descFactorial_div_factorial` etc.).
- Termwise product bound (`Finset.prod_le_prod`, `Nat.descFactorial_le_pow`).
- Strictness traceable to `n − 1 < n` or `2 ≤ k!`.

**Signatures A (incompatible).**
- `Fintype.card` of an arrow type / `Fintype.card_fun`.
- Injection/subset arguments between finite collections.

**Signatures B (required).**
- `Fintype.card (K → N) = n ^ k` via `Fintype.card_fun`/`card_pi`.
- `choose` as cardinality of a StrictMono-map/subset family.
- Strict cardinality step with the constant function as explicit non-member witness.

**Signatures B (incompatible).**
- `Nat.descFactorial`, factorial division, `choose_symm` algebra.
- Explicit `∏` over `Finset.range k`.

**Contamination risk.** MEDIUM-HIGH — both proofs sit side-by-side on one ProofWiki page as Proof 1/Proof 2 (prime pretraining material).

**Automation/library caveats.** **Exact hit for the NON-strict form**: `Nat.choose_le_pow` — the item MUST be the strict version. Even strict has a ~3-line path: `Nat.choose_le_sub_pow` + `Nat.pow_lt_pow_left`; ban both. Adjacent: `Nat.choose_le_two_pow`, `choose_middle_le_pow`. omega/decide can't handle symbolic k.

**Lean statement sketch.** `theorem choose_lt_pow {n k : ℕ} (hk : 2 ≤ k) (hkn : k ≤ n) : n.choose k < n ^ k` — UNVERIFIED.

## Review notes

- **Sources**: single ProofWiki page carrying both routes — same co-location
  concentration as 028 and 039 (contamination AND single-source caveats together).
- **Math checked (Claude)**: both routes correct.
- **Concerns**: near-exact library lemma for the natural form (only strictness
  saves it), a short two-lemma bypass, and the Proof1/Proof2 co-location. The
  strict-form restatement is load-bearing — an unusual fragility.
- **Verdict recommendation**: BENCH — behind 042 in this domain.
