# Candidate 010: nine-divides-three-consecutive-cubes

Status: draft
Batch: 4 (low-contamination hunt), Opus agent, 2026-07-24

**Theorem.** For every natural number $n$, $9 \mid n^3 + (n+1)^3 + (n+2)^3$.
Formal reading: `∀ n : ℕ, 9 ∣ (n^3 + (n+1)^3 + (n+2)^3)`.

**Domain.** Elementary number theory / divisibility.

**Strategy A — telescoping induction.** Let $f(n) = n^3+(n+1)^3+(n+2)^3$. Base case: $f(0)=0+1+8=9$. Inductive step: form the difference
$$f(n+1)-f(n) = (n+3)^3 - n^3 = 9n^2 + 27n + 27 = 9(n^2+3n+3),$$
because the middle two cubes coincide and only the endpoints change. The difference is a manifest multiple of $9$; if $9 \mid f(n)$ then $9 \mid f(n+1)$. Induction closes the claim.

**Source A.** R. Grimaldi, *Discrete and Combinatorial Mathematics*, 5th ed., Ch. 14 Problem 31 ("sum of the cubes of three consecutive integers is divisible by 9") — https://www.vaia.com/en-us/textbooks/math/discrete-and-combinatorial-mathematics-an-applied-introduction-5-edition/chapter-14/problem-31-prove-that-the-sum-of-the-cubes-of-three-consecut/ ; same statement + induction: https://brainly.in/question/14759472 and https://www.toppr.com/ask/question/prove-by-induction-that-the-sum-of-the-cubes-of-three-consecutive-natural-numbers-is/

**Strategy B — centering + factorization mod 3.** Put $m = n+1$, so the integers are $m-1, m, m+1$. Then
$$(m-1)^3 + m^3 + (m+1)^3 = 3m^3 + 6m = 3m(m^2+2).$$
It remains to show $3 \mid m(m^2+2)$, i.e. $3 \mid m^3+2m$. Modulo $3$, $2m \equiv -m$, so $m^3 + 2m \equiv m^3 - m = (m-1)m(m+1)$, a product of three consecutive integers, always divisible by $3$. Hence $9 \mid 3m(m^2+2)$. No induction; a single algebraic identity plus one modular reduction.

**Source B.** ADAPTED (same theorem, different route). The centering/symmetrize-then-reduce technique: *Divisibility of the Sums of the Powers of Consecutive Integers*, arXiv:2304.07605 (technique source — PDF text not extractable, cited for topic only). Consecutive-integer divisibility lemma: ProofWiki, https://proofwiki.org/wiki/Product_of_r_Consecutive_Integers_is_Divisible_by_r!

**Distinctness rationale.** Strategy A never factors the expression and reasons about the discrete difference $f(n+1)-f(n)$ inside an induction; Strategy B is closed-form with no recursion, resting on an algebraic identity and a modular argument.

**Signatures A (required).**
- Induction on `n` (`Nat.rec` / `induction n`).
- Base-case evaluation `f 0 = 9`.
- Rewrite of the successor difference to `9 * (n^2 + 3*n + 3)` (`ring`/`ring_nf`).
- `Dvd` closure: from `9 ∣ f n` deduce `9 ∣ f (n+1)` by adding a multiple of 9.

**Signatures A (incompatible).**
- No `ZMod 3` / `Int.emod` modular reduction.
- No appeal to a "product of 3 consecutive integers" divisibility lemma.

**Signatures B (required).**
- Algebraic rewrite to `3 * (n+1) * ((n+1)^2 + 2)` (`ring`).
- Reduction mod 3 (`ZMod 3` cast or `Int.emod`/`decide` on residues).
- Use of `(m-1)*m*(m+1)` divisible by 3.

**Signatures B (incompatible).**
- No induction on `n` (`Nat.rec`).
- No successor-difference / telescoping step.

**Contamination risk.** LOW — the induction form circulates on homework sites, but the paired centering-and-mod-3 route for this exact statement is not a canonical textbook pairing, so a two-strategy record is unlikely to be memorized jointly.

**Lean statement sketch.** `theorem nine_dvd_cubes (n : ℕ) : 9 ∣ n^3 + (n+1)^3 + (n+2)^3` — UNVERIFIED.

## Review notes

- **Why LOW contamination**: theorem is a known exercise but the specific A/B pairing
  is not a standard duo; the B route is an adapted instantiation of a general
  technique, not a copied proof.
- **Discovery agent's top pick of its batch**: both proofs under ~8 lines, visibly
  different formal skeletons (Nat.rec vs. ring+mod).
- **ADAPTED-source caveat**: route B's technique source (arXiv:2304.07605) could not be
  text-verified (binary PDF) — cited as topic/technique only. The route itself is
  elementary and self-contained; approve on mathematical correctness directly rather
  than on source authority.
- **Same automation caution as 001/003**: mod-3 reasoning invites `decide`/`omega`
  collapse; route B's signatures already key on the factorization + consecutive-product
  lemma rather than tactic names — verify that holds up when writing the rubric.
