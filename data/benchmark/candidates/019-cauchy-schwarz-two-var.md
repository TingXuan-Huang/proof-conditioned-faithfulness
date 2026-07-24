# Candidate 019: cauchy-schwarz-two-var

Status: draft
Batch: Codex-external batch 2 (number theory / algebra / inequalities), 2026-07-24.
Renumbered from Codex's "011" (collision with pool numbering).

**Theorem.** For all real numbers $a,b,c,d$,
$(ac+bd)^2\le(a^2+b^2)(c^2+d^2)$. Formal reading:
$\forall a,b,c,d\in\mathbb{R},\;(ac+bd)^2\le
(a^2+b^2)(c^2+d^2)$.

**Domain.** Elementary algebra / inequalities.

**Strategy A — Lagrange identity as a sum of squares.** Direct expansion and
collection of terms gives the two-dimensional Lagrange identity
$$
(a^2+b^2)(c^2+d^2)-(ac+bd)^2=(ad-bc)^2.
$$
The right-hand side is a square and is therefore nonnegative. Hence the left
side is nonnegative, which is exactly
$(ac+bd)^2\le(a^2+b^2)(c^2+d^2)$.

**Source A.** [*Real Algebra from Hilbert's 17th Problem*][real-algebra], José
F. Fernando and J. Manuel Gamboa, §4.6, p. 68 — derives the general Lagrange
identity and immediately obtains Cauchy–Schwarz as a finite sum of squares;
the displayed proof above is its $n=2$ specialization.

[real-algebra]: https://josefer-ucm.github.io/articulos/rgh17.pdf

**Strategy B — Nonnegative quadratic and its discriminant.** For real $t$,
define
$$
f(t)=(at+c)^2+(bt+d)^2
=(a^2+b^2)t^2+2(ac+bd)t+(c^2+d^2).
$$
This is nonnegative for every $t$. If $a=b=0$, the desired inequality is
immediate. Otherwise its leading coefficient is positive, so an everywhere
nonnegative quadratic has discriminant at most zero. Thus
$$
4(ac+bd)^2-4(a^2+b^2)(c^2+d^2)\le0,
$$
and division by $4$ gives the claimed inequality.

**Source B.** [*Discriminant Inequalities*][mit-discriminant], Adam Hesterberg,
MIT ESP Splash 2012, “Four forms of Cauchy-Schwarz,” p. 1 — constructs the
nonnegative sum-of-squares polynomial and derives Cauchy–Schwarz from its
nonpositive discriminant.

[mit-discriminant]: https://esp.mit.edu/download/3f9ea80533386aac77b1ec621b4ac0ee/M6293_Splash_discriminants.pdf

**Distinctness rationale.** Strategy A rewrites the target's difference as
one explicit square. Strategy B introduces a new universally quantified
quadratic in an auxiliary variable and extracts the target from a root-counting
property of its discriminant.

**Signatures A (required).**

- The difference between the right and left sides is formed directly.
- It is normalized to the identity $(ad-bc)^2$.
- Nonnegativity of that single square closes the proof.

**Signatures A (incompatible).**

- No auxiliary real parameter or quadratic polynomial.
- No discriminant or root-counting argument.

**Signatures B (required).**

- An auxiliary variable $t$ and the polynomial
  $(at+c)^2+(bt+d)^2$ are introduced.
- Nonnegativity is asserted for every real $t$.
- The quadratic's discriminant is shown to be nonpositive.
- The degenerate case $a=b=0$ is handled separately.

**Signatures B (incompatible).**

- No direct normalization of the target difference to $(ad-bc)^2$.
- No proof that closes from a single theorem-specific square alone.

**Contamination risk.** HIGH — Cauchy–Schwarz is exceptionally familiar and
both proofs are classical, though the two formal routes remain unmistakably
different.

**Lean statement sketch.**
`theorem cauchy_schwarz_two_variable (a b c d : ℝ) : (a * c + b * d) ^ 2 ≤ (a ^ 2 + b ^ 2) * (c ^ 2 + d ^ 2)`
— UNVERIFIED.

## Review notes (Claude verification pass, 2026-07-24)

- **Sources VERIFIED by direct fetch**: Fernando & Gamboa "Real Algebra" VERIFIED —
  section (4.6) "Lagrange identity and Cauchy-Schwarz inequality" is literally on
  book p. 68, with the (LI) sum-of-squares identity and (CS) corollary. MIT Splash
  Hesterberg handout VERIFIED — "Four forms of Cauchy-Schwarz", nonnegative
  polynomial f(x) = Σ(aᵢx+bᵢ)², nonpositive discriminant. Codex's citations were
  exact to the page.
- **Math checked**: both proofs correct; the a=b=0 degenerate case in route B is
  properly handled.
- **Automation collapse — worst in pool, tied with 015**: `nlinarith [sq_nonneg
  (a*d - b*c)]` closes this in one call, which IS route A in compressed form; route B
  via Mathlib's `discrim_le_zero` is feasible but contrived. Also exact library hits:
  `inner_mul_le_norm_mul_norm` / two-variable specializations.
- **Pool overlap**: same "SOS identity vs. named structural technique on ℝ" contrast
  as 015 — running both over-samples one proof-shape axis; both are HIGH-ish
  contamination inequality items in an already-full familiar bucket.
- **Verdict recommendation**: BENCH or deliberate stress-test twin for 015 — not a
  clean core pair on its own.
