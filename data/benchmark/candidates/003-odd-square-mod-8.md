# Candidate 003: odd-square-mod-8

Status: draft
Batch: 1 (number theory / divisibility / parity), Opus agent, 2026-07-24

**Theorem.** For every odd integer $n$, $8 \mid n^2 - 1$ (equivalently $n^2 \equiv 1 \pmod 8$). Formal reading: $\forall n \in \mathbb{Z},\; \text{Odd } n \Rightarrow 8 \mid (n^2 - 1)$.

**Domain.** Divisibility / parity / modular arithmetic.

**Strategy A — algebraic factorization + consecutive-integer parity.** Since $n$ is odd, write $n = 2k+1$ for some integer $k$. Then
$n^2 - 1 = (2k+1)^2 - 1 = 4k^2 + 4k = 4k(k+1).$
Now $k(k+1)$ is a product of two consecutive integers, hence even, say $k(k+1) = 2m$. Therefore $n^2-1 = 4\cdot 2m = 8m$, so $8 \mid n^2-1$. This is a symbolic computation with no residue enumeration.

**Source A.** Physics Forums, "Is This Proof That 8 Divides n² − 1 for Odd n Valid?," https://www.physicsforums.com/threads/proving-8-n-2-1-for-n-odd.959518/ — sets $n=2b+1$, reduces to $4b(b+1)$ and uses that $b(b+1)$ is even. Corroborated by https://brainly.com/question/39899258.

**Strategy B — case analysis over residues mod 8.** Work modulo 8. An odd integer is congruent to one of $1,3,5,7 \pmod 8$. Squaring: $1^2=1$, $3^2=9\equiv 1$, $5^2=25\equiv 1$, $7^2=49\equiv 1 \pmod 8$. In every case $n^2 \equiv 1 \pmod 8$, i.e. $8 \mid n^2-1$. The argument is a finite check over the residue classes, using no symbolic $(2k+1)$ substitution.

**Source B.** Keith Conrad, "Modular Arithmetic" (UConn expository notes), https://kconrad.math.uconn.edu/blurbs/ugradnumthy/modarith.pdf — squares of odd residues checked modulo 8. Also University of Queensland MATH2301, "Chapter 2 Modular Arithmetic," https://courses.smp.uq.edu.au/MATH2301/Chapter2.pdf.

**Distinctness rationale.** Route A is a single algebraic identity $n^2-1 = 4k(k+1)$ plus the "consecutive integers are even" lemma; route B is an exhaustive finite case split over the four odd residues mod 8. A blinded expert distinguishes a symbolic-factorization proof from a `decide`/enumeration-of-residues proof.

**Signatures A (required).**
- Substitution $n = 2k+1$ and expansion to $n^2-1 = 4k(k+1)$ (ring normalization).
- Lemma that $k(k+1)$ (product of consecutive integers) is even.
- Concludes $8\mid$ from $4 \cdot (\text{even})$.

**Signatures A (incompatible).**
- Enumeration over residues of $n \bmod 8$ (or `ZMod 8` `decide`).
- A four-way case split on $n \% 8 \in \{1,3,5,7\}$.

**Signatures B (required).**
- Reduction to `ZMod 8` (or `n % 8`) and checking each odd residue squares to $1$.
- Finite/decidable closure: `decide`, `Finset`, `interval_cases`, or `omega` over residues.
- No symbolic $(2k+1)$ factorization used as the crux.

**Signatures B (incompatible).**
- Symbolic substitution $n=2k+1$ and the factor $4k(k+1)$.
- Reliance on the "product of two consecutive integers is even" lemma.

**Contamination risk.** MEDIUM — a common number-theory/discrete-math exercise with both routes in course notes, but less iconic than √2, and the two proofs are short enough that phrasings diverge.

**Lean statement sketch.** `theorem eight_dvd_odd_sq_sub_one (n : ℤ) (hn : Odd n) : (8 : ℤ) ∣ n^2 - 1` — UNVERIFIED.

## Review notes

- **Why MEDIUM contamination**: common course exercise with both routes in university
  notes (Conrad, UQ), but far less iconic than √2; the exact pairing of these two
  routes for this theorem is unlikely to be memorized as a unit.
- **Formalization caveat (from discovery agent)**: Strategy B is intrinsically
  automation-shaped (`decide` over `ZMod 8` is one line) — signature design must ensure
  route A outputs don't get misread as B just because a model finishes with `omega`,
  and vice versa. This is the sharpest automation-ambiguity case in batch 1; it may
  become a useful *fixture* for testing the signature extractor itself.
- **What to scrutinize at approval**: whether "no symbolic (2k+1) factorization used as
  the crux" is decidable enough for annotators — a model could do the substitution AND
  finish with omega, landing between routes. The mixed_or_alternative label will likely
  get real use on this item.
