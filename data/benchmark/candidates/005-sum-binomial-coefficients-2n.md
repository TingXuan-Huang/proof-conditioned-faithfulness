# Candidate 005: sum-binomial-coefficients-2n

Status: draft
Batch: 2 (finite sums / sets / algebra / inequalities), Opus agent, 2026-07-24

**Theorem.** For every natural number $n$, $\sum_{k=0}^{n}\binom{n}{k} = 2^{n}$.
Formal reading: `∀ n, (∑ k in Finset.range (n+1), Nat.choose n k) = 2^n`.

**Domain.** Finite sets / counting (binomial coefficients).

**Strategy A — Binomial theorem (algebraic substitution).**
The binomial theorem gives $(x+y)^n = \sum_{k=0}^{n}\binom{n}{k}x^{k}y^{n-k}$ for all $x,y$. Set $x=y=1$: every factor $x^k y^{n-k}=1$, so the right side collapses to $\sum_{k=0}^{n}\binom{n}{k}$, while the left side is $(1+1)^n = 2^n$. Therefore $\sum_{k=0}^{n}\binom{n}{k} = 2^n$.

**Source A.** Wikibooks, *Combinatorics/Binomial Theorem* (sets $a=b=1$), https://en.wikibooks.org/wiki/Combinatorics/Binomial_Theorem; also GeeksforGeeks, "Sum of Binomial Coefficients," https://www.geeksforgeeks.org/maths/sum-of-binomial-coefficients/.

**Strategy B — Combinatorial double counting.**
Count the subsets of a set $S$ with $|S|=n$ in two ways. First, partition subsets by size: there are exactly $\binom{n}{k}$ subsets of size $k$, so the total is $\sum_{k=0}^{n}\binom{n}{k}$. Second, build a subset by deciding independently for each of the $n$ elements whether it is in or out — two choices per element, hence $2^n$ subsets in all. Both count the same collection (the power set of $S$), so the two expressions are equal.

**Source B.** John Hammond, *Discrete Math for Shockers* (Wichita State University), §5.3 "Combinatorial Proofs," https://www.math.wichita.edu/discrete-book/section-counting-binomial.html — gives exactly this two-way count. Also Wikibooks, *Combinatorics/Subsets of a set*.

**Distinctness rationale.** Route A is pure algebra: instantiate a polynomial identity at $x=y=1$. Route B never expands a power — it exhibits a bijection/partition of the power set and counts cardinalities. A blinded expert sees "used `add_pow` / binomial expansion" versus "counted subsets by size and by element choices."

**Signatures A (required).**
- Invocation of the binomial theorem (`add_pow`).
- Substitution $x=y=1$ (or $(1+1)^n$) with $1^k$ factors dropping out.
- Identification $2^n=(1+1)^n$.

**Signatures A (incompatible).**
- No appeal to power-set cardinality or subset counting.
- No bijection to $\{0,1\}^n$ / per-element choices.

**Signatures B (required).**
- Power set partitioned by subset size, size-$k$ block having cardinality $\binom{n}{k}$ (`Finset.card_powersetCard` style).
- Independent per-element in/out choice giving $2^n$ (bijection subsets ↔ $\{0,1\}^n$, or `Finset.card_powerset`).
- Two cardinality counts equated.

**Signatures B (incompatible).**
- No polynomial expansion of $(1+1)^n$ / no `add_pow`.
- No substitution of numeric values into a binomial identity.

**Contamination risk.** HIGH — textbook-canonical identity whose two proofs appear in essentially every combinatorics course; both near-certainly memorized. Candidate for the deliberate "familiar bucket" (like 002-sqrt2-irrational).

**Lean statement sketch.** `theorem sum_choose_eq_pow (n : ℕ) : ∑ k in Finset.range (n+1), n.choose k = 2^n` — UNVERIFIED.

## Review notes

- **Why HIGH contamination**: textbook-canonical identity whose two proofs appear in
  essentially every combinatorics course; both near-certainly memorized.
- **The bigger problem — Mathlib already has this exact lemma** (`Nat.sum_range_choose`):
  a model can close the goal in one line with a library call that follows *neither*
  strategy. Same "library-lookup as third behavior" issue as 002, but worse, since here
  the lookup is the exact statement rather than a related one. If approved, the
  signature rubric needs an explicit policy for library-call outputs (likely:
  mixed_or_alternative, never a strategy match).
- **Recommendation**: weakest candidate of the six for the core benchmark — consider
  `rejected` or hold as a familiar-bucket alternate behind 002. If both 002 and 005 are
  kept, the familiar bucket is overweighted toward "famous identities with Mathlib
  shortcuts."
- **What to scrutinize at approval**: whether the double-counting route (B) is even
  *expressible* at reasonable length in Lean 4/Mathlib — a `Finset.card_powerset`-based
  proof is real but substantially longer than route A; asymmetric formalization
  difficulty between routes can bias responsiveness measurement.
