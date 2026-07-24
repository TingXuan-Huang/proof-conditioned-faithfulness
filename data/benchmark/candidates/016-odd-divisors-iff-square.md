# Candidate 016: odd-divisors-iff-square

Status: draft
Batch: Codex-external batch 1 (divisibility / finite sums / counting), 2026-07-24.
Renumbered from Codex's "007" (collision with pool numbering).

**Theorem.** For every positive integer $n$, the number of positive divisors of
$n$ is odd if and only if $n$ is a perfect square. Formal reading:
$\forall n \in \mathbb{N}_{>0},\; |\{d \in \mathbb{N}_{>0}: d\mid n\}|$ is odd
$\Longleftrightarrow \exists m\in\mathbb{N}_{>0},\;n=m^2$.

**Domain.** Divisibility / finite sets and counting.

**Strategy A — Pair complementary divisors.** For each positive divisor $d$ of
$n$, pair $d$ with $n/d$. This operation is an involution: applying it twice
returns $d$. Every orbit therefore has two elements unless $d=n/d$. A fixed
point occurs exactly when $d^2=n$. If $n$ is not a square, all divisors lie in
two-element pairs, so their number is even. If $n$ is a square, its positive
square root is the unique fixed divisor and every other divisor is paired, so
the number of divisors is odd. This proves both directions.

**Source A.** [*Fundamental Theorem of Arithmetic*][ucf-notes], Arup Guha,
University of Central Florida COT 3100H lecture notes, “Parity of the Number of
Divisors,” p. 10 — explicitly pairs $d$ with $n/d$ and identifies $d=n/d$ as
the square case.

[ucf-notes]: https://www.cs.ucf.edu/~dmarino/ucf/cot3100h/lectures/COT3100NumTheory03.pdf

**Strategy B — Prime-exponent product formula.** By unique factorization, write
$n=\prod_{j=1}^{t}p_j^{a_j}$. A positive divisor is obtained by independently
choosing an exponent $e_j\in\{0,\ldots,a_j\}$ for each prime, so the number of
divisors is $\prod_{j=1}^{t}(a_j+1)$. This product is odd exactly when every
$a_j+1$ is odd, equivalently when every $a_j$ is even. The latter holds exactly
when
$n=\big(\prod_{j=1}^{t}p_j^{a_j/2}\big)^2$, so exactly when $n$ is a perfect
square.

**Source B.** [*Fundamental Theorem of Arithmetic*][ucf-notes], Arup Guha,
University of Central Florida COT 3100H lecture notes, “Number of Divisors of
an Integer” and “Parity of the Number of Divisors,” pp. 9–10 — derives the
product $\prod(a_j+1)$ and then its parity criterion.

**Distinctness rationale.** Strategy A acts directly on the finite divisor set
with a fixed-point involution. Strategy B never pairs divisors; it encodes them
as prime-exponent vectors and reduces the claim to the parity of a product.

**Signatures A (required).**

- The finite set of positive divisors of $n$ is the counted object.
- The map $d\mapsto n/d$ is used as an involution on that set.
- Fixed points are characterized by $d=n/d$, equivalently $d^2=n$.

**Signatures A (incompatible).**

- No prime factorization $n=\prod p_j^{a_j}$.
- No divisor-count formula $\prod(a_j+1)$.

**Signatures B (required).**

- A unique prime factorization $n=\prod p_j^{a_j}$ is introduced.
- Divisors are represented by independent exponent choices
  $0\le e_j\le a_j$.
- The divisor count becomes $\prod(a_j+1)$, whose parity is analyzed.

**Signatures B (incompatible).**

- No complementary-divisor map $d\mapsto n/d$.
- No orbit or fixed-point pairing argument on the divisor set.

**Contamination risk.** MEDIUM — the theorem is a standard exercise, but the
specific involution-versus-prime-exponent pairing is less likely to be recalled
as a fixed two-proof package than the usual headline identities.

**Lean statement sketch.**
`theorem odd_card_divisors_iff_square (n : ℕ) (hn : n ≠ 0) : Odd n.divisors.card ↔ ∃ m : ℕ, n = m ^ 2`
— UNVERIFIED.

## Review notes (Claude verification pass, 2026-07-24)

- **Sources VERIFIED by direct fetch**: the UCF Guha PDF is real and contains both
  routes — "Number of Divisors of an Integer" (τ(n) = ∏(aᵢ+1) via independent exponent
  choices) and "Parity of the Number of Divisors" (both the product-parity argument AND
  the d ↔ n/d pairing with the d = n/d square case). One caveat: the source states
  route A's pairing via worked examples (n = 36, 48) plus a prose argument, not a formal
  involution write-up — the candidate's involution phrasing is a (legitimate) tightening.
  Also note both routes come from ONE document; an independent second source for route A
  (e.g. the classic locker-problem literature) would strengthen the attestation.
- **Math checked**: both proofs correct and complete. Genuinely distinct skeletons
  (fixed-point involution on a finite set vs. valuation/product-parity).
- **Mathlib caution**: `Nat.card_divisors` (τ via factorization) exists and a
  square-iff-odd-divisor-count lemma likely exists — check before approval;
  library-lookup policy applies (would be pool item #7 with this pattern).
- **Formalization asymmetry**: route A needs a Finset involution-pairing argument
  (`Finset.card_involution`-style machinery) — heavier than route B's factorization
  computation. Same scrutiny as 011 (which also uses an involution route B — mild
  proof-shape overlap between 016A and 011B).
- **Verdict recommendation**: KEEP — one of the two strongest Codex finds; fresh
  theorem for the pool, fills the counting domain.
