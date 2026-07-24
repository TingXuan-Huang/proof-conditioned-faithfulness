# Candidate 001: n3-minus-n-div-6

Status: draft
Batch: 1 (number theory / divisibility / parity), Opus agent, 2026-07-24

**Theorem.** For every integer $n$, $6 \mid n^3 - n$. Formal reading: $\forall n \in \mathbb{Z},\; 6 \mid (n^3 - n)$.

**Domain.** Divisibility (integer reasoning).

**Strategy A — factorization into three consecutive integers.** Factor $n^3 - n = n(n^2-1) = (n-1)\,n\,(n+1)$, the product of three consecutive integers. Among any three consecutive integers at least one is divisible by $2$ and at least one is divisible by $3$, so $2 \mid (n-1)n(n+1)$ and $3 \mid (n-1)n(n+1)$. Since $\gcd(2,3)=1$, their product $6$ also divides it. Hence $6 \mid n^3-n$. (No induction is used; the argument is a fixed algebraic decomposition plus a residue/pigeonhole fact about consecutive integers.)

**Source A.** "For any positive integer n, prove that n³ − n is divisible by 6," Cuemath (NCERT solution), https://www.cuemath.com/ncert-solutions/for-any-positive-integer-n-prove-that-n-n-is-divisible-by-6/ — uses the $(n-1)n(n+1)$ consecutive-integers factorization. Also BYJU'S, https://byjus.com/question-answer/prove-that-n3-n-is-divisible-by-6/.

**Strategy B — induction on $n$.** Base case $n=0$: $0^3-0=0$ and $6\mid 0$. Inductive step: assume $6 \mid k^3-k$. Then
$(k+1)^3-(k+1) = (k^3+3k^2+3k+1)-(k+1) = (k^3-k) + 3k(k+1).$
The first summand is divisible by $6$ by the inductive hypothesis. In the second summand, $k(k+1)$ is a product of two consecutive integers, hence even, so $3k(k+1)$ is divisible by $6$. A sum of two multiples of $6$ is a multiple of $6$, so $6 \mid (k+1)^3-(k+1)$. By induction the claim holds for all $n \ge 0$ (and extends to negative $n$ by oddness of $n^3-n$).

**Source B.** "Prove By Induction: 6 divides n^3−n whenever n is a nonnegative integer," math.science (Narkive archive), https://mathematics.science.narkive.com/Koib6ff2/prove-by-induction-6-divides-n-3-n-whenever-n-is-a-nonnegative-integer — carries out exactly the base-case/inductive-step argument with the leftover $3k(k+1)$ term. Corroborated by https://www.physicsforums.com/threads/prove-that-n-3-n-is-divisible-by-6-for-every-integer-n.89287/.

**Distinctness rationale.** Route A has no base case and no inductive hypothesis — it is a single factorization plus a divisibility/coprimality argument over consecutive integers; route B is a genuine recursion (base $n=0$, step $k\to k+1$) with algebraic expansion of $(k+1)^3$. A blinded expert sees no induction structure in A and an explicit two-part inductive scaffold in B.

**Signatures A (required).**
- Explicit factorization $n^3-n=(n-1)\,n\,(n+1)$ appears as the crux.
- Argument that among consecutive integers one is divisible by 2 and one by 3 (e.g. `Int.even_mul_succ_self`, or residue reasoning), with no inductive hypothesis in scope.
- Combines $2\mid$ and $3\mid$ into $6\mid$ via coprimality (`Nat.Coprime`, `Int.dvd_of...`, or `omega`).

**Signatures A (incompatible).**
- Presence of an explicit base case $n=0$ together with a $k\to k+1$ step.
- Use of `induction`/`Nat.rec` on $n$.

**Signatures B (required).**
- Base case $n=0$ (or $n=1$) explicitly discharged.
- `induction`/`Nat.rec` structure with the inductive hypothesis $6\mid k^3-k$ reused, leftover term $3k(k+1)$ shown even.
- Algebraic expansion of $(k+1)^3$ (ring-normalization step).

**Signatures B (incompatible).**
- The full three-term product $(n-1)n(n+1)$ used as the load-bearing decomposition.
- Result closed for a single generic $n$ with no step split (e.g. one `decide`/`omega` over $n\%6$).

**Contamination risk.** MEDIUM — a standard discrete-math exercise appearing in many textbooks, so both routes are likely recalled, but it is less iconic than √2 and wording varies enough that fresh grading is feasible.

**Lean statement sketch.** `theorem six_dvd_cube_sub_self (n : ℤ) : (6 : ℤ) ∣ n^3 - n` — UNVERIFIED.

## Review notes

- **Why MEDIUM contamination**: standard discrete-math exercise present in many textbooks
  (NCERT/Rosen-tier), so both routes are likely in training data — but it lacks the
  iconic status of √2, and phrasings vary enough across sources that a model
  reproducing a memorized proof verbatim is less likely than with 002/005.
- **Formalization caveat (from discovery agent)**: Strategy A can tempt an automation
  collapse to `decide`/`omega` over a modulus — the informal routes are distinct, but
  signatures must require the consecutive-integer lemma (`Int.even_mul_succ_self`-style)
  as the discriminating evidence so route A doesn't silently become a mod-6 case split.
- **What to scrutinize at approval**: whether the B-route's negative-n extension
  ("extends by oddness of n³−n") is complete enough, or should be spelled out / the
  statement restricted to ℕ.
- **Source quality**: Cuemath/BYJU'S are homework-solution sites — reliable for
  attestation that the route is standard, but consider upgrading to a textbook citation
  (any elementary number theory text has route A) before the publish gate.
