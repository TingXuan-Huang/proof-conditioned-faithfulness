# Candidate 037: division-algorithm-existence

Status: draft
Batch: Opus round-3 batch C (order / well-ordering / extremal), 2026-07-24

**Theorem.** Existence half of the division algorithm on ℕ: `∀ n q : ℕ, 0 < q → ∃ m r : ℕ, r < q ∧ n = m * q + r`.

**Domain.** Well-ordering of remainders vs. structural induction on the dividend.

**Strategy A — well-ordering of the remainder set.** $S = \{n - xq : xq \le n\}$ is nonempty ($x=0$); WOP gives least $r = n - mq$. If $r \ge q$ then $r - q \in S$ is smaller — contradiction; so $r < q$.

**Source A.** W. Cook, *Well Ordering, Division, and the Euclidean Algorithm* (MATH 2510), Theorem "Division Algorithm" pp. 1-2 — agent opened. Corroborating: McKernan Math 104A §2 Thm 2.5 (TLS-chain quirk noted); J. M. Lee Math 300 handout. VERIFIED.

**Strategy B — induction on the dividend, divisor fixed.** Base $n=0$: $(0,0)$. Step: from $n = mq + r$, $r < q$: if $r+1 = q$ take $(m+1, 0)$; else $(m, r+1)$.

**Source B.** Tao, *Analysis I*, Prop. 2.3.9 + Exercise 2.3.5 (hint: fix q, induct on n); fully worked at taoanalysis.wordpress.com "Exercise 2.3.5" — agent opened. VERIFIED.

**Distinctness rationale.** A never inducts — names a candidate-remainder set, applies WOP once, refutes $r \ge q$ by minimality; B never mentions a set — builds $(m,r)$ primitive-recursively with the wrap-around case split. Blinded tell: "minimal element of $\{n - xq\}$" vs. "case $r+1 = q$".

**Signatures A (required).**
- Least-element extraction over remainders (`Nat.find` on `fun r => ∃ x, n = x*q + r`, or `WellFounded.min`).
- Minimality refuting `q ≤ r` at `r − q`.
- Local `by_contra`/`absurd` confined to the `r < q` subgoal.
- Pair obtained by destructuring, not recursion.

**Signatures A (incompatible).**
- `induction n` generating an IH of the goal shape.
- Case split on `r + 1 = q` vs. `r + 1 < q`.

**Signatures B (required).**
- `induction n` / `Nat.rec` on the dividend, q fixed.
- IH `∃ m r, r < q ∧ n = m*q + r` destructured in the successor branch.
- Two-branch case analysis `r+1 = q` vs. `r+1 < q`.
- Literal witnesses `⟨m+1, 0, …⟩` and `⟨m, r+1, …⟩`.

**Signatures B (incompatible).**
- `Nat.find`/`find_min`/`WellFounded.min` or least-element hypotheses.
- `by_contra` on the top-level goal.

**Contamination risk.** HIGH — among the most reproduced proofs in mathematics; both routes verbatim in many texts; a public Lean 4 companion to Tao's Analysis I exists (teorth/analysis; specific file UNVERIFIED, 404 on the tried path).

**Automation/library caveats.** **One-line strategy-independent collapse**: `exact ⟨n / q, n % q, Nat.mod_lt _ hq, by omega⟩` via `Nat.div_add_mod` + `Nat.mod_lt`. Ban list: `Nat.div_add_mod` family, `Nat.divModEquiv`, and consider banning `/`/`%` notation on ℕ for this item. `omega` handles `/`,`%` only for numeral divisors, so with variable q it cannot close alone. Usable ONLY with the ban list enforced.

**Lean statement sketch.** `theorem nat_div_exists (n q : ℕ) (hq : 0 < q) : ∃ m r : ℕ, r < q ∧ n = m * q + r` — UNVERIFIED.

## Review notes

- **Sources**: both routes theorem-level verified in opened sources — the best
  attestation of the round.
- **Math checked (Claude)**: both routes correct.
- **The catch**: `n/q` and `n%q` are PRIMITIVES in Lean — the "proof" is destructing
  built-ins, so the collapse is deeper than a banable lemma; it's notation-level.
  Same WOP-vs-induction contrast as 036 but with far worse collapse and HIGH
  contamination.
- **Verdict recommendation**: BENCH behind 036 — keep only if 036 falls at review,
  and only with the notation-level ban accepted as a per-item rule (which conflicts
  with uniform-rules design).
