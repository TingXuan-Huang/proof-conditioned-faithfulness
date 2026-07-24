# Candidate 004: sum-k-times-k-factorial

Status: draft
Batch: 2 (finite sums / sets / algebra / inequalities), Opus agent, 2026-07-24

**Theorem.** For every positive integer $n$, $\sum_{k=1}^{n} k\cdot k! = (n+1)! - 1$.
Formal reading: `∀ n ≥ 1, (∑ k in Finset.Icc 1 n, k * k!) = (n+1)! - 1`.

**Domain.** Finite sums (natural-number arithmetic with factorials).

**Strategy A — Induction on $n$.**
Base case $n=1$: LHS $=1\cdot 1!=1$ and RHS $=2!-1=1$, so they agree.
Inductive step: assume $\sum_{k=1}^{n}k\cdot k! = (n+1)!-1$. Add the next term:
$$\sum_{k=1}^{n+1}k\cdot k! = \big[(n+1)!-1\big] + (n+1)\cdot(n+1)! = (n+1)!\,\big[1+(n+1)\big] - 1 = (n+1)!\,(n+2) - 1 = (n+2)! - 1.$$
This is the claim for $n+1$, closing the induction.

**Source A.** Canonical induction exercise from Kenneth Rosen, *Discrete Mathematics and Its Applications* (mathematical-induction section, e.g. §5.1 Ex. 21). The identity also appears in Mike Zabrocki, York University MATH 1200 telescoping notes, garsia.math.yorku.ca/~zabrocki/math1200f21/files/telescoping.pdf. **Sourcing caveat**: the identity's status as a standard Rosen induction exercise is search-confirmed, but one specific answer-key PDF was unreachable (TLS-cert mismatch) — the induction route rests on canonical-exercise status plus the agent's own re-derivation. Flag for reviewer attention.

**Strategy B — Telescoping.**
Observe $k\cdot k! = (k+1)! - k!$ (since $(k+1)! = (k+1)k! = k\cdot k! + k!$). Substituting term by term,
$$\sum_{k=1}^{n} k\cdot k! = \sum_{k=1}^{n}\big[(k+1)! - k!\big] = (n+1)! - 1!,$$
because every interior factorial cancels against its neighbor, leaving only the top term $(n+1)!$ and the bottom term $1! = 1$. Hence the sum is $(n+1)! - 1$.

**Source B.** Cut-the-Knot, "Telescoping Sums, Series and Products" (Alexander Bogomolny), https://www.cut-the-knot.org/m/Algebra/TelescopingSums.shtml — explicitly lists $\sum_{k=0}^{n}k\cdot k! = (n+1)!-1$ with the remark "Simply observe that $k\cdot k!=(k+1)!-k!$". Also the Zabrocki York U notes above (telescoping exercises).

**Distinctness rationale.** Route A runs a recursion (base case + hypothesis + algebraic closure) and never rewrites a term as a difference; route B rewrites each summand into a first-order difference $(k+1)!-k!$ and collapses the sum by cancellation. A blinded reader sees "assumed for $n$, proved for $n+1$" versus "wrote $a_{k+1}-a_k$ and cancelled."

**Signatures A (required).**
- Explicit base case $n=1$ evaluated on both sides.
- Inductive hypothesis invoked and one summand $(n+1)(n+1)!$ appended (last-term peel, e.g. `Finset.sum_Icc_succ_top`).
- Algebraic factoring $(n+1)![1+(n+1)] = (n+2)!$.

**Signatures A (incompatible).**
- No per-term rewrite $k\cdot k! = (k+1)!-k!$.
- No cancellation of interior factorial terms.

**Signatures B (required).**
- Per-term identity $k\cdot k! = (k+1)! - k!$ stated/used.
- Application of a telescoping/sum-of-differences lemma so interior terms cancel.
- Final value read off as top-minus-bottom $(n+1)! - 1!$.

**Signatures B (incompatible).**
- No "assume true for $n$" inductive-hypothesis line applied to the whole identity.
- No separately evaluated base case as the load-bearing step.

**Contamination risk.** MEDIUM — a well-known Rosen induction exercise and the telescoping trick is a standard "aha," so both routes are in training data, but the pairing is far less iconic than Gauss's sum.

**Lean statement sketch.** `theorem sum_k_mul_factorial (n : ℕ) (hn : 1 ≤ n) : ∑ k in Finset.Icc 1 n, k * k.factorial = (n+1).factorial - 1` — UNVERIFIED (natural subtraction is safe since $(n+1)!\ge 1$).

## Review notes

- **Why MEDIUM contamination**: well-known Rosen induction exercise and the telescoping
  rewrite is a standard trick, so both routes are in training data — but the pairing is
  much less iconic than Gauss's sum, and the theorem is specific enough that verbatim
  recall is less likely.
- **Sourcing caveat**: the induction route's direct source PDF was unreachable
  (TLS-cert error) — route A currently rests on "canonical Rosen exercise" status
  (search-confirmed) plus agent re-derivation. Before approval, either accept that
  basis explicitly or locate one clean induction write-up (any Rosen solutions manual
  or discrete-math course notes will do).
- **Formalization caveat**: natural-number subtraction in the RHS `(n+1)! - 1` is safe
  but will require a small `Nat.sub` argument in Lean; alternatively state as
  `∑ ... + 1 = (n+1)!` to avoid subtraction entirely — cleaner and
  strategy-neutral. Decide the canonical form before freezing the statement.
