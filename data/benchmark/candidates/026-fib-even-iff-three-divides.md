# Candidate 026: fib-even-iff-three-divides

Status: draft
Batch: Opus round-2 batch B (parity / invariants / integer reasoning), 2026-07-24

**Theorem.** With $F_0=0$, $F_1=1$: $F_n$ is even $\iff 3 \mid n$.
Formal reading: `∀ n : ℕ, Even (Nat.fib n) ↔ 3 ∣ n`

**Domain.** Parity / modular reasoning (period of a recurrence mod 2) vs. divisibility structure.

**Strategy A — parity sequence has period 3.** Joint induction on $k$: "$F_{3k}$ even, $F_{3k+1}$ odd, $F_{3k+2}$ odd." Base $k=0$: $0,1,1$. Step: even/odd bookkeeping through the recurrence (odd+odd=even, even+odd=odd, odd+even=odd). Every $n$ is $3k$, $3k{+}1$, or $3k{+}2$; only the first is even, and only the first has $3 \mid n$.

**Source A.** Stanford CS103ACE (Spring 2024) Week 6 solutions §4 "Larger Step Sizes: Even Fibonacci Numbers," pp. 6-7, https://web.stanford.edu/class/archive/cs/cs103ace/cs103ace.1246/materials/week06_solutions.pdf (agent opened). **Partial attestation, honestly flagged by the agent**: the written solution covers only 3∣n ⟹ even; the biconditional is attested as stated exercises (UCI Math 13 self-test 5-3, statement only; Hammack *Book of Proof* Ch. 10 Ex. 42); the two odd cases as written are the agent's own extension.

**Strategy B — instantiate the Fibonacci divisibility theorem at m = 3.** From $F_m \mid F_n \iff m \mid n$ (for $m > 2$) with $F_3 = 2$: for $n > 2$, even $\iff 2 \mid F_n \iff F_3 \mid F_n \iff 3 \mid n$; check $n = 0,1,2$ by hand. (Or via strong divisibility: $\gcd(2, F_n) = F_{\gcd(3,n)}$.)

**Source B.** ProofWiki "Divisibility of Fibonacci Number" (agent opened; full theorem + proof via Honsberger). Erickson (Colorado College 2006), "Divisibility in the Fibonacci Numbers" (agent opened; proves $\gcd(F_m,F_n) = F_{\gcd(m,n)}$). **Agent-flagged**: neither source spells out the $m{=}3$ specialization — that one-line instantiation is the agent's; the general theorem is fully attested.

**Distinctness rationale.** A lives in ℤ/2 and unfolds the recurrence, never mentioning Fibonacci-divides-Fibonacci; B never unfolds the recurrence for general $n$ and instantiates a lattice-structure theorem at $m=3$. Three-goal step-3 induction vs. library-theorem instantiation + small case split.

**Signatures A (required).**
- Step-3 induction (custom recursor or `n % 3` split with `Nat.div_add_mod`).
- Repeated `Nat.fib_add_two` + parity lemmas (`Nat.even_add`, `Odd.add_odd`, `Even.add_odd`).
- Base values `fib_zero/one/two`.
- Conjunctive IH carrying three consecutive parities.

**Signatures A (incompatible).**
- `Nat.fib_dvd`, `Nat.fib_gcd`, `Nat.isStrongDvdSequence_fib`.
- Any `Nat.fib m ∣ Nat.fib n` subgoal.

**Signatures B (required).**
- `Nat.fib_dvd` or `Nat.fib_gcd`.
- Instantiation at literal 3 with `Nat.fib 3 = 2` (decide/norm_num).
- Case split on `Nat.gcd 3 n ∈ {1, 3}`; no general recurrence unfolding.

**Signatures B (incompatible).**
- Induction with `fib_add_two` rewriting in the step.
- IH bundling parities of `fib (3k)`, `fib (3k+1)`, `fib (3k+2)`.

**Contamination risk.** MEDIUM-HIGH theorem / MEDIUM pairing — route A heavily memorized; route B rarely the presented proof of this parity fact.

**Automation/library caveats.** No single-lemma collapse: Mathlib's `Nat.Fib.Basic` has `fib_dvd`/`fib_gcd` but NO `fib_even_iff` (agent checked the mathlib4 docs listing). But `fib_dvd` gives B's forward direction in one line — route B is essentially a designed library-call route, low difficulty. `norm_num`'s NatFib extension evaluates numerals (closes base cases instantly, both routes — expected, harmless).

**Lean statement sketch.** `theorem fib_even_iff (n : ℕ) : Even (Nat.fib n) ↔ 3 ∣ n` — UNVERIFIED.

## Review notes

- **Sources**: weakest attestation in the round, and the agent said so itself —
  route A's biconditional write-up and route B's m=3 instantiation are agent
  extensions of attested material. Either find one clean full-biconditional source
  or approve on direct verification (both proofs are short and hand-checkable).
- **Math checked (Claude)**: both routes correct.
- **Policy tension worth settling at rubric-freeze**: route B's REQUIRED signatures
  are library calls (`fib_dvd`/`fib_gcd`) — the provisional library-lookup policy
  says library-closure codes as mixed_or_alternative, but here library use IS the
  conditioned strategy. Resolution: the policy should key on whether the cited
  lemma matches the conditioned route's signatures, not on library use per se.
  This candidate is the cleanest test case for that wording.
- **Pool balance**: third Fibonacci item (013, 014); at most one or two survive per
  split.
- **Verdict recommendation**: BENCH — interesting policy probe, weak attestation,
  crowded domain.
