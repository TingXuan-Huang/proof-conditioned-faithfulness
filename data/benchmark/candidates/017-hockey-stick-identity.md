# Candidate 017: hockey-stick-identity

Status: draft
Batch: Codex-external batch 1 (divisibility / finite sums / counting), 2026-07-24.
Renumbered from Codex's "008" (collision with pool numbering).

**Theorem.** For natural numbers $r\le n$,
$\sum_{i=r}^{n}\binom{i}{r}=\binom{n+1}{r+1}$. Formal reading:
$\forall r,n\in\mathbb{N},\;r\le n\Rightarrow
\sum_{i=r}^{n}\binom{i}{r}=\binom{n+1}{r+1}$.

**Domain.** Finite sums / finite sets and counting.

**Strategy A — Induction using Pascal’s rule.** Fix $r$ and induct on
$n\ge r$. At $n=r$, both sides equal $1$. For the step, assume
$\sum_{i=r}^{n-1}\binom{i}{r}=\binom{n}{r+1}$. Peeling off the last term gives
$$
\sum_{i=r}^{n}\binom{i}{r}
=\binom{n}{r+1}+\binom{n}{r}
=\binom{n+1}{r+1},
$$
where the last equality is Pascal’s rule. Thus the identity holds for every
$n\ge r$.

**Source A.** [*Worksheet 13: March 6 (Solutions)*][berkeley-worksheet], Jacob
Elafandi, UC Berkeley Math 55, Problem 9, p. 3 — gives the base case and the
inductive step using Pascal’s rule.

[berkeley-worksheet]: https://math.berkeley.edu/~elafandi/teaching/55a_s24/ws13_sol.pdf

**Strategy B — Count subsets by their largest element.** Count the
$(r+1)$-element subsets of $\{1,\ldots,n+1\}$. Directly there are
$\binom{n+1}{r+1}$. Alternatively, partition these subsets by their largest
element. If the largest element is $i+1$, where $r\le i\le n$, the other $r$
elements must be chosen from $\{1,\ldots,i\}$, giving $\binom{i}{r}$ subsets.
The classes are disjoint and exhaustive, so summing their sizes gives
$\sum_{i=r}^{n}\binom{i}{r}=\binom{n+1}{r+1}$.

**Source B.** [*Combinatorics, §1.8: Combinatorial Identities*][osu-identities],
The Ohio State University Ximera project, Example 5 — partitions committees by
the largest assigned number. Also [*MAT 145: Problem Set 3 Solutions*][ucd-ps3],
Prof. Casals and T.A. A. Aguirre, UC Davis, Problem 3(b), pp. 2–3, gives the same
subset-counting route in an equivalent reindexing. **(DEAD LINK — HTTP 404 on
2026-07-24; do not rely on this one.)**

[osu-identities]: https://ximera.osu.edu/math/combinatorics/combinatoricsBook/combinatoricsBook/combinatorics/identities/identities
[ucd-ps3]: https://www.math.ucdavis.edu/~casals/Teaching/Winter19/Winter19MAT145_PSet3Solutions.pdf

**Distinctness rationale.** Strategy A recursively extends a finite-sum
identity and closes the step with Pascal’s algebraic recurrence. Strategy B is
a nonrecursive double count that constructs a partition of a family of finite
sets by a largest-element statistic.

**Signatures A (required).**

- Induction on the upper bound $n$, with base case $n=r$.
- The last summand $\binom{n}{r}$ is peeled from the finite sum.
- Pascal’s rule combines $\binom{n}{r+1}+\binom{n}{r}$.

**Signatures A (incompatible).**

- No finite family of $(r+1)$-subsets is constructed.
- No partition according to a subset’s largest element.

**Signatures B (required).**

- A set of $(r+1)$-subsets of an $(n+1)$-element ordered set is counted.
- The subsets are partitioned by largest element $i+1$.
- The class with largest element $i+1$ is counted as $\binom{i}{r}$.

**Signatures B (incompatible).**

- No induction hypothesis on a shorter sum.
- No recursive use of Pascal’s rule to close an $n-1$ to $n$ step.

**Contamination risk.** MEDIUM — the hockey-stick identity is familiar, but its
induction-versus-largest-element proof pair is less iconic than the excluded
Gauss and binomial-row-sum examples.

**Lean statement sketch.**
`theorem hockey_stick (r n : ℕ) (h : r ≤ n) : (∑ i in Finset.Icc r n, Nat.choose i r) = Nat.choose (n + 1) (r + 1)`
— UNVERIFIED.

## Review notes (Claude verification pass, 2026-07-24)

- **Sources checked by direct fetch**: Berkeley ws13 VERIFIED (Problem 9, exactly the
  Pascal-rule induction as described, page 3). OSU Ximera VERIFIED (Example 5,
  largest-element partition of committees, as described). The UC Davis Casals PSet3
  link is DEAD (HTTP 404) — treat route B as attested by Ximera alone, or replace the
  dead link (AoPS "Hockey Stick Identity" page carries the same double count).
- **Math checked**: both proofs correct. Distinct skeletons (inductive fold + Pascal
  vs. non-recursive partition double count).
- **Mathlib caution — exact lemma exists**: `Nat.sum_Icc_choose` IS the hockey-stick
  identity. Library-lookup policy applies at full strength (theorem = library lemma,
  like 009/014/018).
- **Formalization asymmetry**: route B's largest-element bijection is substantially
  longer in Lean than route A's induction — same fairness concern as 005 route B
  (double counting), and the pool already has that contrast in 005/011. Contamination
  is arguably MEDIUM-HIGH, not MEDIUM (hockey-stick is an AoPS/olympiad staple).
- **Verdict recommendation**: KEEP as bench/alternate — solid pair, but overlaps 005's
  proof-shape contrast (algebraic-identity vs. double-count) and adds another
  exact-Mathlib-lemma item; prefer at most one of {005, 017} per split.
