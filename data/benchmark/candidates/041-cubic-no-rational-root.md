# Candidate 041: cubic-no-rational-root

Status: draft
Batch: Opus round-3 batch D (irrationality / field arithmetic), 2026-07-24

**Theorem.** $8x^3 - 6x - 1 = 0$ has no rational solution.
Formal reading: `∀ q : ℚ, 8*q^3 - 6*q - 1 ≠ 0`. (The cubic of $\cos 20°$ — but the statement is purely arithmetic.)

**Domain.** Rational-root non-existence for an integer cubic.

**Strategy A — rational root theorem (divisor enumeration).** $p/q$ in lowest terms with $8p^3 - 6pq^2 - q^3 = 0$: $p \mid q^3$ forces $p = \pm1$; $q \mid 8p^3$ forces $q \in \{1,2,4,8\}$. Eight candidates $\pm1, \pm\frac12, \pm\frac14, \pm\frac18$; evaluate f at each (values $1, -3, -3, 1, -19/8, 3/8, -111/64, -17/64$) — none zero.

**Source A.** Wikipedia "Angle trisection" §Proof of impossibility (verbatim candidate list; agent opened) + Wikipedia "Rational root theorem."

**Strategy B — parity + one 2-adic reduction (no divisor list).** From $8a^3 - 6ab^2 - b^3 = 0$: $b^3 = 2(4a^3 - 3ab^2)$ is even ⟹ $b$ even ⟹ $a$ odd (coprimality). Write $b = 2c$; divide by 8: $a^3 = 3ac^2 + c^3$. If $c$ even: RHS even, $a^3$ odd — impossible. If $c$ odd: $3ac^2$ odd + $c^3$ odd = even, again vs. $a^3$ odd. Done.

**Source B.** ADAPTED (agent-flagged, mechanism attested): the parity mechanism is Putnam 1952 A1 (Kalva archive, agent opened: odd leading + odd constant + odd p(1) ⟹ no rational roots). Adaptation: reduce to $a^3 - 3ac^2 - c^3 = 0$ first (leading 1, constant −1, p(1) = −3, all odd), deriving oddness from coprimality/parity so route B contains zero RRT reasoning.

**Distinctness rationale.** A enumerates divisors → eight explicit candidates → evaluation; B enumerates nothing — one substitution $b = 2c$ and two parity cases. The Lean proofs share no lemma family (Rat.num/den divisibility vs. Even/Odd).

**Signatures A (required).**
- `Rat.num`/`Rat.den` divisibility (`num ∣ 1`, `den ∣ 8`), directly or via `Polynomial.num_dvd_of_isRoot`/`den_dvd_of_isRoot`.
- Reduction to a finite candidate set (`interval_cases` / divisor case split).
- Per-candidate `norm_num` evaluation.

**Signatures A (incompatible).**
- Any `Even`/`Odd` predicate or parity split on num/den.
- Introducing `c` with `b = 2*c` and the reduced identity.

**Signatures B (required).**
- Denominator even from `b³ = 2·(…)` (`Int.even_pow`, `Int.even_mul`).
- Coprimality/reducedness ⟹ numerator odd.
- `b = 2*c` substitution and `a^3 = 3*a*c^2 + c^3`.
- Case split `Int.even_or_odd c` with parity contradiction in each branch.

**Signatures B (incompatible).**
- The divisor list ±1, ±1/2, ±1/4, ±1/8 or `Polynomial` rational-root lemmas.
- `interval_cases`/`decide` enumeration over roots.

**Contamination risk.** MEDIUM — route A is famous via angle trisection; the parity route for this specific non-monic cubic is uncommon and found nowhere verbatim.

**Automation/library caveats.** No Mathlib lemma states this; `decide` inapplicable (ℚ infinite); `norm_num` can't discharge the ∀. Most collapse-resistant of the batch. Asymmetry to account for: `Mathlib/RingTheory/Polynomial/RationalRoot.lean` lemmas make route A cheap while B stays manual.

**Lean statement sketch.** `theorem no_rat_root_8x3_6x_1 : ∀ q : ℚ, 8 * q ^ 3 - 6 * q - 1 ≠ 0` — UNVERIFIED.

## Review notes

- **Sources**: A verified (Wikipedia verbatim). B is well-flagged ADAPTED — the
  Putnam 1952 A1 mechanism is attested and the reduction is elementary; approve on
  direct verification (Claude checked: correct, both parity branches).
- **Math checked (Claude)**: both routes correct.
- **Strengths**: purely arithmetic ℚ statement (no Real.sqrt API), no library
  collapse, no automation collapse, MEDIUM contamination, genuinely disjoint lemma
  families between routes, and a great backstory (trisection impossibility) for
  the paper's exposition.
- **Verdict recommendation**: KEEP — pilot-eligible.
