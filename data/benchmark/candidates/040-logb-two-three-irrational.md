# Candidate 040: logb-two-three-irrational

Status: draft
Batch: Opus round-3 batch D (irrationality / field arithmetic), 2026-07-24

**Theorem.** $\log_2 3$ is irrational. Formal reading: `Irrational (Real.logb 2 3)`.

**Domain.** Irrationality of a logarithm (prime to prime base); elementary integer arithmetic after clearing the exponent.

**Strategy A — parity.** If $\log_2 3 = p/q$ ($p, q \ge 1$; positivity since $3 > 1$, base $> 1$), then $2^p = 3^q$. The left side is even ($p \ge 1$), the right side odd (product of odds). Contradiction.

**Source A.** Wikipedia "Irrational number" §Logarithms (verbatim match, agent opened); independently MSE https://math.stackexchange.com/a/656150.

**Strategy B — coprimality of powers.** From $2^c = 3^d$: $\gcd(2,3) = 1$ lifts to $\gcd(2^c, 3^d) = 1$; but the numbers are EQUAL, so $N = \gcd(N,N) = 1$ — yet $N = 2^c \ge 2$. No parity used; works verbatim for $\log_3 5$.

**Source B.** Bill Dubuque, https://math.stackexchange.com/a/656278 (verbatim general theorem gcd(a,b)=1 ⇒ log_b a ∉ ℚ; agent opened). Reduction-step attestation: ProofWiki "Irrationality of Logarithm" (via text proxy — Cloudflare blocks direct fetch).

**Distinctness rationale.** A inspects parity of the two sides; B never mentions parity — two coprime equal numbers must both be 1. Shared content is only the reduction $2^p = 3^q$.

**Signatures A (required).**
- Bridge to `2 ^ p = 3 ^ q` with `p, q ≥ 1` (`Real.rpow_natCast`, `Real.rpow_logb`/`Real.logb_eq_iff_rpow_eq`, cast injectivity).
- `Even (2 ^ p)` (`Nat.even_pow` / `dvd_pow_self`).
- `Odd (3 ^ q)` (`Odd.pow`).
- Even/odd exclusion close.

**Signatures A (incompatible).**
- `Nat.Coprime`/`Nat.gcd`/`Nat.Coprime.pow` relating the sides.
- `Nat.factorization`/`padicValNat`/`multiplicity`.

**Signatures B (required).**
- Same bridge to `2 ^ c = 3 ^ d`.
- `Nat.Coprime 2 3` lifted by `Nat.Coprime.pow`.
- Rewrite to `Nat.Coprime N N` → `N = 1` (`Nat.coprime_self_iff_one`), contradict `2 ≤ 2^c`.

**Signatures B (incompatible).**
- Any `Even`/`Odd` predicate or parity split.
- Exponent counting via factorization/multiplicity.

**Contamination risk.** MEDIUM — route A is on Wikipedia (highly memorized); route B markedly rarer; no formal proof to recall wholesale.

**Automation/library caveats.** Loogle `Irrational, Real.logb` → **0 declarations**: no direct collapse. `decide`/`norm_num` can't touch it. Real work is the `Real.logb` → `2^p = 3^q` bridge (shared by both routes — good for fairness). Third route to label separately: `Nat.factorization` exponent counting.

**Lean statement sketch.** `theorem irrational_logb_two_three : Irrational (Real.logb 2 3)` — UNVERIFIED.

## Review notes

- **Sources**: strong (Wikipedia verbatim + Dubuque's general theorem); ProofWiki
  attestation via proxy is acceptable corroboration.
- **Math checked (Claude)**: both routes correct.
- **Why this is the keeper of the batch**: genuinely new domain (logarithms), NO
  library collapse at all (rare in this pool), the hard formal work (the logb
  bridge) is shared by both routes so neither is unfairly burdened, MEDIUM
  contamination with a rare route B.
- **Gate-S check**: confirm the `Real.logb` bridge is provable at reasonable length
  in the pinned Mathlib before pilot inclusion.
- **Verdict recommendation**: KEEP — pilot-eligible.
