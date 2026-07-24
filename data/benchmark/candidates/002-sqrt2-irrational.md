# Candidate 002: sqrt2-irrational

Status: draft
Batch: 1 (number theory / divisibility / parity), Opus agent, 2026-07-24

**Theorem.** There are no positive integers $a, b$ with $a^2 = 2b^2$ (equivalently, $\sqrt 2$ is irrational). Formal reading: $\forall a\, b \in \mathbb{N},\; b \ne 0 \Rightarrow a^2 \ne 2b^2$.

**Domain.** Integer reasoning / parity / divisibility.

**Strategy A — parity via infinite descent (Pythagorean/Euclid).** Suppose $\sqrt 2 = a/b$ with the fraction in lowest terms ($\gcd(a,b)=1$), so $a^2 = 2b^2$. Then $a^2$ is even, and since a square is even only if its root is even, $a$ is even, say $a = 2c$. Substituting, $4c^2 = 2b^2$, so $b^2 = 2c^2$, whence $b^2$ is even and $b$ is even. But then $2 \mid a$ and $2 \mid b$, contradicting $\gcd(a,b)=1$. This uses no prime factorization — only the parity fact "$2 \mid a^2 \Rightarrow 2 \mid a$."

**Source A.** "Square root of 2 is irrational," cut-the-knot, https://www.cut-the-knot.org/proofs/sq_root.shtml — Proof 2 (assume lowest terms, derive both $p$ and $q$ even, contradiction). Also Math Fun Facts, "Irrationality by Infinite Descent," Harvey Mudd, https://math.hmc.edu/funfacts/irrationality-by-infinite-descent/.

**Strategy B — unique factorization (2-adic exponent parity).** Suppose $a^2 = 2b^2$ with $a,b$ positive integers. By the Fundamental Theorem of Arithmetic, in any square the exponent of the prime $2$ is even: if $v_2(x)$ is the exponent of $2$ in $x$, then $v_2(a^2)=2v_2(a)$ is even, while $v_2(2b^2)=1+2v_2(b)$ is odd. But $a^2 = 2b^2$ forces $v_2(a^2)=v_2(2b^2)$, i.e. an even number equals an odd number — a contradiction. Hence no such $a,b$ exist. (No coprimality/lowest-terms assumption is used; the crux is counting prime multiplicities.)

**Source B.** cut-the-knot, https://www.cut-the-knot.org/proofs/sq_root.shtml — Proof 3 (prime factorization: $p^2$ has an even number of prime-2 factors while $2q^2$ has an odd number). Also GraphicMaths, "Root 2 is irrational: proof by prime factorisation," https://graphicmaths.substack.com/p/root-2-is-irrational-proof-by-prime.

**Distinctness rationale.** Route A assumes a reduced fraction and derives a contradiction from a shared factor of 2 using only elementary parity; route B never reduces the fraction and instead invokes the uniqueness of prime factorization to compare the parity of the exponent of 2 on each side. A blinded expert distinguishes "coprime + descent" from "count prime multiplicities / FTA."

**Signatures A (required).**
- Assumes $\gcd(a,b)=1$ / fraction in lowest terms (or a minimal-$b$ descent).
- Parity lemma used: $2\mid a^2 \Rightarrow 2\mid a$ (`Int.even_pow`, `Nat.even_mul`, etc.), applied to both $a$ and then $b$.
- Contradiction reached from "$2\mid a$ and $2\mid b$" against coprimality (or from an infinite-descent minimality violation).

**Signatures A (incompatible).**
- Any use of `Nat.factorization` / `padicValNat` / prime-multiplicity counting.
- Explicit appeal to the Fundamental Theorem of Arithmetic / unique factorization.

**Signatures B (required).**
- Uses prime factorization / multiplicity of 2 (`Nat.factorization`, `padicValNat 2`, or `Nat.factors`).
- Establishes exponent of 2 in $a^2$ is even and in $2b^2$ is odd, then derives an even = odd contradiction.
- Appeal to unique factorization / `UniqueFactorizationMonoid` / FTA.

**Signatures B (incompatible).**
- A "lowest terms / coprime" reduction of $a/b$.
- Deriving that both $a$ and $b$ are even.

**Contamination risk.** HIGH — √2 irrationality is the canonical irrationality example, and both the parity proof and the prime-factorization proof are extremely widely reproduced; LLMs almost certainly memorize both.

**Lean statement sketch.** `theorem no_sqrt2_soln (a b : ℕ) (hb : b ≠ 0) : a^2 ≠ 2 * b^2` (or `Irrational (Real.sqrt 2)`) — UNVERIFIED.

## Review notes

- **Why HIGH contamination**: the canonical irrationality example — both routes appear
  in essentially every intro-proofs course, Wikipedia, and countless blog posts; models
  have near-certainly memorized both proofs *and* existing Lean formalizations
  (Mathlib itself contains `Nat.Prime.irrational_sqrt` / `irrational_sqrt_two`).
  Expect models to potentially bypass both strategies with a library call — the
  extractor/signature design must anticipate `exact irrational_sqrt_two`-style outputs
  as a third "library-lookup" behavior that matches *neither* strategy.
- **Role in benchmark**: strongest source attestation of batch 1 (cut-the-knot
  explicitly enumerates the routes as Proof 2 and Proof 3) — use as a deliberate
  "familiar bucket" item (the design wants ~⅓ familiar), not as evidence of fresh
  strategy-following.
- **What to scrutinize at approval**: statement formulation choice matters — the
  `a² ≠ 2b²` integer form forces an actual proof, while `Irrational (Real.sqrt 2)`
  invites the one-line Mathlib lookup. Recommend the integer form.
