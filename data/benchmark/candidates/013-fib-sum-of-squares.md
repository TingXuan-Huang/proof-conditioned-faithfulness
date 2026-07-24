# Candidate 013: fib-sum-of-squares

Status: draft
Batch: 5 (Fibonacci / recurrences / AM-GM), Opus agent, 2026-07-24

**Theorem.** For all $n\ge 1$: $\sum_{i=1}^{n} F_i^2 = F_n\,F_{n+1}$ (with $F_1=F_2=1$).
Formal reading: `∑ i ∈ Finset.range (n+1), (Nat.fib i)^2 = Nat.fib n * Nat.fib (n+1)` (the $i=0$ term vanishes since `Nat.fib 0 = 0`).

**Domain.** Fibonacci / linear-recurrence finite-sum identity.

**Strategy A — algebraic telescoping.** For each $i\ge 1$, the recurrence gives $F_i=F_{i+1}-F_{i-1}$, hence $F_i^2=F_iF_{i+1}-F_{i-1}F_i$. Summing over $i=1,\dots,n$, the right side telescopes over $a_i:=F_{i-1}F_i$: total $= a_{n+1}-a_1 = F_nF_{n+1}-F_0F_1 = F_nF_{n+1}$.

**Source A.** Standard telescoping hint: Homework.Study (URL in agent transcript); ProofWiki, "Sum of Sequence of Squares of Fibonacci Numbers," https://proofwiki.org/wiki/Sum_of_Sequence_of_Squares_of_Fibonacci_Numbers

**Strategy B — rectangle dissection (area counted two ways).** Attach squares of sides $F_1, F_2, \dots, F_n$ successively; inductively the block after $k$ squares is $F_k\times F_{k+1}$ (fits flush because $F_k+F_{k+1}=F_{k+2}$). After $n$ squares the figure is an $F_n\times F_{n+1}$ rectangle. Area as disjoint squares $= \sum F_i^2$; as a rectangle $= F_nF_{n+1}$. Equate.

**Source B.** "Proof Without Words: Sum of Squares of Consecutive Fibonacci Numbers," *College Mathematics Journal* 49(2), 2018, https://www.tandfonline.com/doi/full/10.1080/07468342.2018.1424425 ; Chasnov, *Fibonacci Numbers and the Golden Ratio* (HKUST notes), https://www.math.hkust.edu.hk/~machas/fibonacci.pdf

**Distinctness rationale.** A is a term-by-term algebraic rewrite collapsing by cancellation; B never manipulates the summand — it partitions a geometric region and equates two area counts. Different formal skeletons: telescoping fold vs. induction on a geometric invariant.

**Signatures A (required).**
- Single-term identity $F_i^2=F_iF_{i+1}-F_{i-1}F_i$.
- Telescoping cancellation over `Finset.range` (adjacent-difference fold).
- Endpoint evaluation using $F_0F_1=0$.

**Signatures A (incompatible).**
- No geometric region / area introduced.
- No two-way counting of a set.

**Signatures B (required).**
- A region whose area is counted two ways (dissection = rectangle).
- Structural induction maintaining the invariant "current block is $F_k\times F_{k+1}$".
- Fit condition driven by $F_k+F_{k+1}=F_{k+2}$.

**Signatures B (incompatible).**
- No per-term algebraic factoring of $F_i^2$.
- No telescoping / adjacent-difference cancellation.

**Contamination risk.** HIGH — one of the most-reproduced Fibonacci identities; both proofs appear verbatim across the web.

**Lean statement sketch.** `theorem fib_sq_sum (n : ℕ) : ∑ i ∈ Finset.range (n+1), Nat.fib i ^ 2 = Nat.fib n * Nat.fib (n+1)` — UNVERIFIED.

## Review notes

- **Why HIGH contamination**: canonical Fibonacci identity, both routes ubiquitous.
  Third HIGH item in the pool ({002, 005, 013}, plus 009 MEDIUM-HIGH) — familiar bucket
  is now oversupplied; at most one or two of these survive into any given split.
- **The serious formalization question — route B may not be benchmark-fair**: the
  rectangle-dissection proof is a *geometric* argument; a faithful Lean formalization
  of "areas counted two ways" is a substantial undertaking (far beyond the ~15-line
  informal proof), and a model conditioned on B will almost certainly produce an
  algebraic proof wearing B's vocabulary. Scrutinize hard whether B's "acceptable
  formal refinements" can be defined at all without collapsing into route A's shape.
  This is the pool's clearest case of the informal/formal strategy-expressibility gap
  — arguably a reason to reject, or to keep deliberately as a stress-test item
  (documented as such), but not as a clean core pair.
- **Mathlib caution**: check for an existing `Nat.fib` sum-of-squares lemma.
