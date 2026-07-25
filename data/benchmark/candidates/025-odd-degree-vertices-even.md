# Candidate 025: odd-degree-vertices-even

Status: draft (agent recommendation: reject unless restated — see Review notes)
Batch: Opus round-2 batch B (parity / invariants / integer reasoning), 2026-07-24

**Theorem.** In any finite undirected graph, the number of vertices of odd degree is even.
Formal reading: `∀ {V} [Fintype V] [DecidableEq V] (G : SimpleGraph V) [DecidableRel G.Adj], Even ((Finset.univ.filter fun v => Odd (G.degree v)).card)`

**Domain.** Parity invariant (process monovariant) vs. double counting.

**Strategy A — invariant under adding one edge.** Start from the edgeless graph: the odd-degree set $O$ is empty, $|O|=0$ even. Insert edges one at a time: inserting $\{u,v\}$ flips exactly the memberships of $u,v$ in $O$ — both even → $|O|+2$; both odd → $|O|-2$; mixed → unchanged. Parity of $|O|$ is invariant, so it stays even.

**Source A.** Engel, *Problem-Solving Strategies*, Ch. 1, Problem 32 (p. 11) + Solution 32 (p. 19) — the handshake-ceremony version of exactly this invariant argument (agent opened same PDF mirror as 024).

**Strategy B — double counting incidences.** Count endpoint-incidences $(v,e)$ two ways: $\sum_v \deg v = 2|E|$. Split vertices by degree parity: the even-degree part contributes an even sum, so $\sum_{v \in V_{odd}} \deg v$ is even; a sum of $|V_{odd}|$ odd numbers is even only if $|V_{odd}|$ is even.

**Source B.** Nagoya University student seminar note (Hevidu & Riichi, May 2024), https://www.math.nagoya-u.ac.jp/~richard/teaching/s2024/SML_HR_2.pdf (agent opened; exact proof). ProofWiki "Handshake Lemma" + corollary; cites Chartrand, *Introductory Graph Theory* §2.1 Thm 2.1.

**Distinctness rationale.** A is a dynamic induction over the edge set with a 3-case per-step parity analysis, never computing $\sum \deg$; B is a static double count with no induction. Formal shapes: `Finset.induction_on` over edges vs. degree-sum formula + filtered-sum split.

**Signatures A (required).**
- Induction over the edge set (`Finset.induction_on` on `edgeFinset` or a `Multiset (Sym2 V)`/`List (V × V)` encoding).
- Edgeless base case reducing to `card = 0`.
- Per-step lemma: exactly two degrees flip parity; 3-way endpoint-parity case split.
- No `∑ v, degree v` anywhere.

**Signatures A (incompatible).**
- `SimpleGraph.sum_degrees_eq_twice_card_edges` or any `∑ deg = 2|E|` hypothesis.
- `Finset.sum_filter_add_sum_filter_not` on a degree sum.

**Signatures B (required).**
- Degree-sum identity (library or hand-rolled incidence double count).
- Parity split of the sum over vertices.
- "Sum of k odds even ⟹ k even" closing step (typically ZMod 2).
- No edge induction, no empty-graph base case.

**Signatures B (incompatible).**
- Edge induction + edgeless base case.
- Per-inserted-edge endpoint parity case analysis.

**Contamination risk.** HIGH — handshaking lemma; both routes among the most reproduced proofs in discrete math.

**Automation/library caveats.** SEVERE (agent-flagged): Mathlib states the theorem verbatim — `SimpleGraph.even_card_odd_degree_vertices` (Mathlib/Combinatorics/SimpleGraph/DegreeSum.lean); a bare `exact` closes the goal with zero route signatures. `sum_degrees_eq_twice_card_edges` hands route B its substance in one lemma. Usable only by (a) banning both lemmas, or (b) restating over a bespoke encoding (degrees from a `Multiset (Sym2 V)`), which also makes route A the natural formal shape.

**Lean statement sketch.** `theorem even_card_odd_degree {V : Type*} [Fintype V] [DecidableEq V] (G : SimpleGraph V) [DecidableRel G.Adj] : Even ((Finset.univ.filter fun v => Odd (G.degree v)).card)` — UNVERIFIED.

## Review notes

- **Sources**: solid (Engel book; Nagoya note; ProofWiki/Chartrand). Not the problem.
- **The problem is the verbatim Mathlib lemma** — worst library-collapse case in the
  entire pool (worse than 018: here even the STATEMENT is the library's). A bespoke
  multiset-of-edges restatement would fix it but adds statement machinery the models
  haven't seen, hurting comparability; per-item lemma bans are contrary to the
  benchmark's uniform-rules design.
- **Also**: pool's first SimpleGraph item — heavy API surface for a 4-page-paper
  benchmark, HIGH contamination on top.
- **Verdict recommendation**: REJECT for the benchmark (keep on file as the canonical
  illustration of the library-collapse failure mode — useful for the paper's rubric
  discussion and as an S5 library-lookup fixture).
