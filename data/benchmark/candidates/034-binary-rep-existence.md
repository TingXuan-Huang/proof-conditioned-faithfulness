# Candidate 034: binary-rep-existence

Status: draft
Batch: Opus round-3 batch B (digits / base representation / sums), 2026-07-24

**Theorem.** Every natural number is a sum of distinct powers of 2: `∀ n : ℕ, ∃ S : Finset ℕ, ∑ i ∈ S, 2^i = n`.

**Domain.** Base-2 representation (existence half of the basis representation theorem).

**Strategy A — parity recursion (halving).** Strong induction. $n=0$: $S=\emptyset$. Even $n = 2m$: shift the exponents of $m$'s representation by +1 (distinctness preserved — injective shift). Odd $n = 2m+1$: same, then add $2^0$; $0 \notin S{+}1$ since all shifted exponents ≥ 1.

**Source A.** K. Shannon, MATH 300 handout "Every natural number can be written as the sum of Distinct powers of 2," Salisbury University (agent read the PDF in full; both cases match).

**Strategy B — greedy largest power (extremal step + descent).** Take the largest $k$ with $2^k \le n$; maximality gives $r = n - 2^k < 2^k$. Recurse on $r$ (if nonzero); every exponent in $r$'s representation is $< k$ because $2^i \le r < 2^k$, so $k \notin S$ — distinctness comes entirely from the maximality bound.

**Source B.** UT Austin CS Frege course notes, "Strong Induction" (agent opened; takes $2^k \le n+1 < 2^{k+1}$, recurses on the remainder, concludes distinctness from the inequality).

**Distinctness rationale.** Different well-founded decompositions and different distinctness mechanisms: recursion on $n/2$ + injective exponent shift vs. recursion on $n - 2^k$ + maximality bound. Blinded tell: parity split vs. "largest power ≤ n."

**Signatures A (required).**
- Parity case split (`Nat.even_or_odd` / `n % 2`) atop the induction.
- Recursion on `n / 2` justified by `Nat.div_lt_self` (or `Nat.binaryRec`).
- Witness built by `Finset.image (· + 1) S` + `Finset.sum_image` + injectivity.
- Odd case adds `2^0` with `0 ∉ image (·+1) S` from "members ≥ 1".

**Signatures A (incompatible).**
- `Nat.log 2 n`, `Nat.pow_log_le_self`, `Nat.lt_pow_succ_log_self`, explicit largest-k.
- Subtraction `n − 2^k` in the recursive call.

**Signatures B (required).**
- `k` with `2^k ≤ n < 2^(k+1)` (via `Nat.log 2` or `Nat.findGreatest`/maximality).
- Recursive call on `n − 2^k` with `n − 2^k < 2^k` proved and used.
- `Finset.insert k S` + `k ∉ S` from exponent bound (needs a strengthened IH).

**Signatures B (incompatible).**
- Parity split or `n / 2`.
- Exponent-shift image `(· + 1)`.

**Contamination risk.** MEDIUM-HIGH — both routes are Rosen-style textbook exercises with abundant public solutions.

**Automation/library caveats.** **One-line collapse (agent-verified)**: `Finset.twoPowSum_toFinset_bitIndices` (Mathlib/Data/Nat/BitIndices.lean) IS the theorem. Second collapse: `Nat.digits 2` + `Nat.ofDigits_digits`. Third: `Nat.binaryRec` hands route A over nearly free. Ban list: `Nat.bitIndices*`, `Nat.binaryRec`, `Nat.digits`-shortcuts. `decide`/`omega` inapplicable.

**Lean statement sketch.** `theorem exists_sum_distinct_two_pow (n : ℕ) : ∃ S : Finset ℕ, ∑ i ∈ S, 2 ^ i = n` — UNVERIFIED.

## Review notes

- **Sources**: both opened and read by the agent; solid course materials.
- **Math checked (Claude)**: both routes correct; B genuinely needs the strengthened
  IH (exponent bound) — a nice formal-shape discriminator.
- **Value**: the greedy/extremal-descent route type is nearly absent from the pool
  (overlaps the order/extremal agent's territory — compare on arrival). Existential
  statement form makes strategy grading subtler: the WITNESS structure (image-shift
  vs. insert-max) is the signature, which S5's extractor must read from the term.
- **Library collapse**: `bitIndices` one-liner is 025-class for the bare existential.
- **Verdict recommendation**: BENCH — good pair, but the existential-goal grading
  subtlety and the one-line collapse make it a poor pilot item; reconsider for core
  after the rubric handles witness-structure signatures.
