# Candidate 014: consecutive-fib-coprime

Status: draft
Batch: 5 (Fibonacci / recurrences / AM-GM), Opus agent, 2026-07-24

**Theorem.** Any two consecutive Fibonacci numbers are coprime: $\gcd(F_n,F_{n+1})=1$ for all $n\ge 0$.
Formal reading: `Nat.Coprime (Nat.fib n) (Nat.fib (n+1))`.

**Domain.** Fibonacci / number-theoretic identity.

**Strategy A — Euclidean descent (induction).** Base: $\gcd(F_0,F_1)=\gcd(0,1)=1$. Step: using $F_{n+2}=F_{n+1}+F_n$ and $\gcd(a,\,a+b)=\gcd(a,b)$:
$\gcd(F_{n+1},F_{n+2})=\gcd(F_{n+1},F_n)=1$ by the induction hypothesis.

**Source A.** ProofWiki, "Consecutive Fibonacci Numbers are Coprime," https://proofwiki.org/wiki/Consecutive_Fibonacci_Numbers_are_Coprime ; cut-the-knot, "GCD of Fibonacci Numbers," https://www.cut-the-knot.org/arithmetic/algebra/FibonacciGCD.shtml

**Strategy B — Cassini certificate (non-inductive divisor argument).** Cassini's identity: $F_{n-1}F_{n+1}-F_n^2=(-1)^n$ for $n\ge1$. Let $d$ divide both $F_n$ and $F_{n+1}$. Since $F_{n-1}=F_{n+1}-F_n$, also $d\mid F_{n-1}$; hence $d$ divides $F_{n-1}F_{n+1} - F_n^2 = \pm1$, so $d=1$. ($n=0$ directly: $\gcd(0,1)=1$.) Cassini itself is provable independently, e.g. $\det(Q^n)=(-1)^n$ for the Fibonacci matrix $Q$.

**Source B.** University of Alberta Math 228 "Divisibility" notes (Cassini-based alternative explicitly given), http://www.math.ualberta.ca/~isaac/math228/s07/divisibility.pdf ; Cassini identity + matrix proof: Wikipedia, "Cassini and Catalan identities," https://en.wikipedia.org/wiki/Cassini_and_Catalan_identities

**Distinctness rationale.** A inducts on the coprimality predicate via gcd-absorption descent. B performs no induction on coprimality: it exhibits an explicit unit-valued integer combination (Bézout-style certificate) and concludes from "d divides a unit." Inductive gcd-rewrite vs. divides-a-unit certificate.

**Signatures A (required).**
- Induction over $n$.
- gcd absorption lemma $\gcd(a,a+b)=\gcd(a,b)$.
- Recurrence $F_{n+2}=F_n+F_{n+1}$ as the reduction step.

**Signatures A (incompatible).**
- No closed-form product/determinant identity.
- No explicit $\pm1$ linear combination constructed.

**Signatures B (required).**
- Cassini identity invoked as a lemma.
- "Common divisor divides the difference, which is a unit" deduction.
- Expressing $F_{n-1}$ as $F_{n+1}-F_n$.

**Signatures B (incompatible).**
- No induction on the coprimality statement itself.
- No step-by-step gcd reduction along the index.

**Contamination risk.** MEDIUM — standard exercise with both routes documented; Mathlib very likely ships the statement, so proof-conditioning (forcing the informal route rather than citing the library) is what makes it non-trivial.

**Lean statement sketch.** `theorem fib_coprime_succ (n : ℕ) : Nat.Coprime (Nat.fib n) (Nat.fib (n+1))` — UNVERIFIED (check for an existing Mathlib lemma).

## Review notes

- **Why MEDIUM contamination**: both routes documented but the Cassini-corollary
  pairing is not a canonical duo; discovery agent ranked this one of its two freshest.
- **Source gap flagged by the agent**: route B is attested as an alternative in the
  U. Alberta notes, but no single canonical page spells out the exact
  Cassini→coprimality corollary line-by-line (ProofWiki has the induction route;
  Wikipedia proves Cassini but not the corollary). The deduction is elementary — either
  accept on direct verification or find one clean worked source before the publish gate.
- **Mathlib caution**: `Nat.fib_coprime_fib_succ` (or similar) almost certainly exists —
  library-lookup policy applies (see 002/005/007/008/009). This pool-wide pattern is
  now 6 of 15 candidates.
- **Cassini dependency**: route B needs Cassini available — check whether Mathlib has
  it; if a model must prove Cassini inline, route B's length balloons (asymmetric
  difficulty concern).
