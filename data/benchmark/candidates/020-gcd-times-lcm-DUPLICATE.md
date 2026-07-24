# Candidate 020: gcd-times-lcm — RECOMMEND REJECT (duplicate)

Status: draft (agent recommendation: reject — duplicate of 009; human decides)
Batch: Codex-external batch 2 (number theory / algebra / inequalities), 2026-07-24.
Renumbered from Codex's "009".

> **Duplicate notice (Claude verification pass, 2026-07-24)**: this theorem is
> pool candidate 009 (gcd·lcm = ab) and exclusion-list item #9. Codex was evidently
> run with the older 6-item exclusion list. The A/B routes here are essentially the
> same pair as 009's (valuation min/max vs. coprime-reduction/universal-property) —
> nothing new to merge except two additional source links (Cornell CS280 HW4, UMD
> Lipsman handout), which are UNVERIFIED and can be spot-checked and folded into 009
> if 009 survives review. No independent value otherwise.

**Theorem.** For all positive integers $a$ and $b$,
$\gcd(a,b)\operatorname{lcm}(a,b)=ab$. Formal reading:
$\forall a,b\in\mathbb{N}_{>0},\;\gcd(a,b)\cdot\operatorname{lcm}(a,b)=a\cdot b$.

**Domain.** Elementary number theory / divisibility.

**Strategy A — Compare prime exponents.** List every prime occurring in $a$ or
$b$ and write $a=\prod_i p_i^{\alpha_i}$ and
$b=\prod_i p_i^{\beta_i}$, allowing zero exponents. In the gcd, the exponent
of $p_i$ is $\min(\alpha_i,\beta_i)$; in the lcm it is
$\max(\alpha_i,\beta_i)$. Hence the exponent of $p_i$ in their product is
$$
\min(\alpha_i,\beta_i)+\max(\alpha_i,\beta_i)
=\alpha_i+\beta_i,
$$
which is exactly its exponent in $ab$. Unique factorization therefore gives
$\gcd(a,b)\operatorname{lcm}(a,b)=ab$.

**Source A.** [*CS 280: Suggested Solutions for Homework 4*][cornell-hw4],
Cornell University course staff, Problem 3, p. 3 — writes the prime
factorizations and proves the identity using the min/max exponent equation.

[cornell-hw4]: https://www.cs.cornell.edu/courses/cs280/2003fa/HW/280hw4s.pdf

**Strategy B — Remove the gcd and reduce to a coprime pair.** Let
$g=\gcd(a,b)$ and write $a=gc$, $b=gd$, where $\gcd(c,d)=1$. First,
$\operatorname{lcm}(c,d)=cd$: the product $cd$ is a common multiple, and if
$M$ is any common multiple, write $M=ck$. Since $d\mid M=ck$ and
$\gcd(c,d)=1$, Euclid's lemma gives $d\mid k$, so $cd\mid M$. Moreover,
common multiples of $gc,gd$ are exactly the numbers $gN$ for which $N$ is a
common multiple of $c,d$. Indeed, if $M$ is a common multiple of $gc,gd$,
then $g\mid M$, so $M=gN$, and cancellation gives $c\mid N$ and $d\mid N$;
the converse is immediate.
Thus scaling both arguments scales the lcm, and
$\operatorname{lcm}(a,b)=g\operatorname{lcm}(c,d)=g\,c\,d$. Therefore
$$
\gcd(a,b)\operatorname{lcm}(a,b)
=g(g\,c\,d)=g^2cd=(gc)(gd)=ab.
$$

**Source B.** [*Theorem: $\operatorname{lcm}(a,b)\times\gcd(a,b)=ab$*][umd-gcd-lcm],
Ron Lipsman, University of Maryland number-theory handout — proves the scaling
lemma, reduces by the gcd to coprime $c,d$, and proves
$\operatorname{lcm}(c,d)=cd$ from the least-common-multiple definition.

[umd-gcd-lcm]: https://math.umd.edu/~rlipsman/courses/numbertheory-poolesville.13-14/GCDxLCM.pdf

**Distinctness rationale.** Strategy A works globally with unique prime
factorization and a pointwise min/max calculation on valuations. Strategy B
uses no prime expansion; it factors out the gcd and reasons from coprimality,
Euclid's lemma, and the universal property of the lcm.

**Signatures A (required).**

- Simultaneous prime factorizations of $a$ and $b$ are introduced.
- Gcd and lcm exponents are represented by `min` and `max`.
- The identity $\min(x,y)+\max(x,y)=x+y$ is applied prime by prime.

**Signatures A (incompatible).**

- No reduction $a=gc$, $b=gd$ to a coprime pair.
- No proof that every common multiple of $c,d$ is divisible by $cd$.

**Signatures B (required).**

- $g=\gcd(a,b)$ is extracted, with $a=gc$, $b=gd$, and $\gcd(c,d)=1$.
- The coprime lemma $\operatorname{lcm}(c,d)=cd$ is proved from divisibility.
- Euclid's lemma is used to show $d\mid k$ from $d\mid ck$.
- Scaling of lcm is used to return from $c,d$ to $a,b$.

**Signatures B (incompatible).**

- No family of prime valuations or exponent vectors.
- No `min`/`max` identity on prime exponents.

**Contamination risk.** MEDIUM — the identity itself is standard, but the
specific valuation-versus-coprime-reduction pair is less canonical than the
usual one-line prime-factorization proof.

**Lean statement sketch.**
`theorem gcd_mul_lcm_pos (a b : ℕ) (ha : 0 < a) (hb : 0 < b) : Nat.gcd a b * Nat.lcm a b = a * b`
— UNVERIFIED.
