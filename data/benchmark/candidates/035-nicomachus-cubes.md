# Candidate 035: nicomachus-cubes

Status: draft
Batch: Opus round-3 batch B (digits / base representation / sums), 2026-07-24

**Theorem.** $\sum_{k=1}^{n} k^3 = \left(\sum_{k=1}^{n} k\right)^2$ (Nicomachus).
Formal reading: `∀ n : ℕ, ∑ k ∈ Finset.range (n+1), k^3 = (∑ k ∈ Finset.range (n+1), k)^2`.

**Domain.** Finite sums with polynomial closed form (figurate-number family).

**Strategy A — odd-number block decomposition (Nicomachus–Wheatstone).** The $k$ consecutive odd numbers starting at $k^2-k+1$ sum to $k^3$; the blocks tile the odd numbers exactly (block $k$ ends at $k^2+k-1$, block $k+1$ starts at $k^2+k+1$). So $\sum k^3$ = sum of the first $T_n = n(n+1)/2$ odds $= T_n^2$.

**Source A.** PlanetMath "Nicomachus' theorem" (agent opened; Wheatstone decomposition + sum-of-odds). Corroborating: Wikipedia "Squared triangular number" (agent opened; Wheatstone 1854 formula).

**Strategy B — multiplication table counted two ways (gnomon double count, Row 1893).** The $n\times n$ table of $i\cdot j$: by factoring, total $= (\sum i)(\sum j) = T_n^2$; by gnomons $G_k = \{(i,j) : \max(i,j)=k\}$, each gnomon sums to $2k\,T_{k-1} + k^2 = k^3$. Compare.

**Source B.** Wikipedia "Squared triangular number" (agent opened; Row's multiplication-table method). Primary (Row 1893, *Geometric Exercises in Paper Folding*): UNVERIFIED.

**Distinctness rationale.** A reassembles cubes into a 1-D run of odd numbers; B evaluates a 2-D sum two ways (product-of-sums vs. max-fiber partition). Different objects, lemmas, and shapes.

**Signatures A (required).**
- `k^3` rewritten as an arithmetic progression of odds `Σ_{j<k} (k²−k+1+2j)`.
- Flatten/reindex a double sum into one range of length `T_n` (`Finset.sum_sigma`/`sum_biUnion`/bijection).
- Sum-of-odds identity `Σ_{m<M} (2m+1) = M²` at `M = T_n`.

**Signatures A (incompatible).**
- `Finset.sum_mul_sum` / product-set (`×ˢ`) formulation.
- Plain `induction n` closed by `ring`.

**Signatures B (required).**
- Double sum over `range n ×ˢ range n` of `i*j` + `Finset.sum_mul_sum` for `(Σk)²`.
- Partition of the product set by `max(i,j)` (`sum_fiberwise`/gnomon `sum_biUnion`).
- Per-gnomon evaluation `2k·T_{k−1} + k² = k³`.

**Signatures B (incompatible).**
- Odd numbers / sum-of-odds identity anywhere.
- Plain `induction n` closed by `ring`.

**Contamination risk.** HIGH — among the most-reproduced identities anywhere, AND a public Lean 4 + Isabelle formalization exists (Alonso, Calculemus blog, 2025-01-03 — agent opened it).

**Automation/library caveats.** **Dominant risk is the induction attractor (agent-flagged)**: `induction n` + `sum_range_succ` + `ring` closes it in ~5 lines matching NEITHER route — must be graded as an explicit third label (useful unfaithfulness detector if so). Library: Bernoulli `sum_range_pow` machinery is a legitimate heavy bypass; `Finset.sum_range_id_mul_two` gives Gauss. Sum-of-odds lemma existence in Mathlib UNVERIFIED. Excluded-list adjacency: route A uses "sum of first N odds = N²" as a LEMMA (that theorem is on the avoid list as a candidate) — lemma-level reuse policy needs a ruling.

**Lean statement sketch.** `theorem nicomachus (n : ℕ) : ∑ k ∈ Finset.range (n + 1), k ^ 3 = (∑ k ∈ Finset.range (n + 1), k) ^ 2` — UNVERIFIED.

## Review notes

- **Sources**: fine (PlanetMath + Wikipedia opened; Row primary unverified but
  secondary attestation is detailed).
- **Math checked (Claude)**: both routes correct (block endpoints and gnomon sums
  verified by hand).
- **The problem is contamination at maximum**: canonical identity + an existing
  public Lean formalization the models may have trained on — worst
  training-leakage profile in the pool. Familiar bucket already oversupplied.
- **The induction-attractor observation is the keeper here**: a strong, natural
  third route that matches neither conditioned proof — valuable as an S5 fixture
  and rubric test case even if the pair never enters the benchmark.
- **Verdict recommendation**: REJECT-leaning bench — hold as fixture/rubric
  material, not a benchmark pair.
