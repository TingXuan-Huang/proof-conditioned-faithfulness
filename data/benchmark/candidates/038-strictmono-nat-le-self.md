# Candidate 038: strictmono-nat-le-self

Status: draft (agent + Claude recommendation: reject unless lemma-ban accepted)
Batch: Opus round-3 batch C (order / well-ordering / extremal), 2026-07-24

**Theorem.** A strictly increasing $f : \mathbb{N} \to \mathbb{N}$ satisfies $n \le f(n)$ for all $n$.
Formal reading: `∀ f : ℕ → ℕ, StrictMono f → ∀ n, n ≤ f n`.

**Domain.** Monotonicity on ℕ; induction vs. minimal counterexample.

**Strategy A — induction on n.** $0 \le f(0)$; from $n \le f(n)$ and $f(n) < f(n+1)$: $f(n+1) > n$, so $f(n+1) \ge n+1$.

**Source A.** ProofWiki, "Strictly Increasing Sequence of Natural Numbers" (induction proof, base-1 indexing; adaptation shifts to base 0) — agent opened. VERIFIED.

**Strategy B — least counterexample.** If $C = \{n : f(n) < n\}$ is nonempty, WOP gives least $c$; $c \ge 1$, write $c = d+1$; $d \notin C$ so $d \le f(d)$; strict monotonicity gives $f(c) > f(d) \ge d = c-1$, so $f(c) \ge c$ — contradiction.

**Source B.** ADAPTED / partially UNVERIFIED (agent-flagged): no published minimal-counterexample write-up of this exact statement found; template attested (MCS §2.2 WOP template).

**Distinctness rationale.** Forward two-step recursion vs. classical contradiction inspecting one least bad index with minimality at $c-1$. Lean shapes: `Nat.rec` + IH vs. `by_contra` + `Nat.find` + `Nat.find_min`.

**Signatures A (required).**
- `induction n` / `Nat.rec` on the main goal.
- IH used with strict monotonicity at `n < n+1`.
- Finish via `Nat.succ_le_of_lt`-family from `n < f (n+1)`.
- No `Classical` / `by_contra`.

**Signatures A (incompatible).**
- `Nat.find`/`find_min`, `WellFounded.min`, `Nat.lt_wfRel`.
- `by_contra`/`push_neg` on the goal.

**Signatures B (required).**
- `by_contra` + `push_neg` → `∃ n, f n < n`.
- Least bad index via `Nat.find` / `WellFounded.min`.
- Zero case dispatched; `c = d + 1` decomposition.
- Minimality applied at `d = c − 1`.

**Signatures B (incompatible).**
- Induction on the main goal.
- Direct `StrictMono.le_apply`.

**Contamination risk.** HIGH — the statement IS a Mathlib lemma; Lean-trained models have seen statement and proof.

**Automation/library caveats.** **Exact Mathlib lemma (agent Loogle-verified)**: `StrictMono.le_apply` (Mathlib.Order.WellFounded; ℕ satisfies the instances) — `exact hf.le_apply` closes it. Second one-liner: `StrictMono.add_le_nat` via `simpa`. With both banned (and alias re-checks each Mathlib bump), the routes are ~5 lines each and structurally unmistakable; without the ban, worthless.

**Lean statement sketch.** `theorem strictMono_nat_le_self (f : ℕ → ℕ) (hf : StrictMono f) (n : ℕ) : n ≤ f n` — UNVERIFIED.

## Review notes

- **Math checked (Claude)**: both routes correct.
- **025-class problem**: theorem = named library lemma. The agent's own verdict
  ("without the ban it is worthless") is right; per-item bans conflict with
  uniform-rules design.
- **What it would offer if kept**: the shortest, cleanest WOP-vs-induction pair —
  ~5 lines per route — attractive for calibration/fixtures even if not benchmarked.
- **Verdict recommendation**: REJECT for the benchmark; retain as an S5 fixture
  (like 025) and as annotator-calibration material.
