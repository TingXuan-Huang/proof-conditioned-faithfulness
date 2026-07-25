# Candidate 023: inclusion-exclusion-three-sets

Status: draft
Batch: Opus round-2 batch A (finite sets / counting), 2026-07-24

**Theorem.** For finite sets $A, B, C$ (decidable equality):
$$|A \cup B \cup C| + |A \cap B| + |A \cap C| + |B \cap C| = |A| + |B| + |C| + |A \cap B \cap C|,$$
the ℕ-subtraction-free form of three-set inclusion–exclusion.

**Domain.** Finite sets / counting (inclusion–exclusion).

**Strategy A — iterate the two-set principle plus distributivity.** Using $|X \cup Y| = |X| + |Y| − |X \cap Y|$ three times: first with $X = A\cup B$, $Y = C$; then on $|A \cup B|$; then, after distributing $(A\cup B)\cap C = (A\cap C)\cup(B\cap C)$, on that union — whose intersection normalizes to $A\cap B\cap C$ by intersection algebra. Collect terms.

**Source A.** Ximera/OSU *Combinatorics* open textbook, §2.2 "Inclusion-Exclusion Principle" — derives the 3-set case exactly this way. https://ximera.osu.edu/math/combinatorics/combinatoricsBook/combinatoricsBook/combinatorics/inclusionExclusion/inclusionExclusion (agent opened and read).

**Strategy B — element contribution / membership case analysis.** Every term is a sum of membership indicators over $U = A\cup B\cup C$. It suffices that each $x \in U$ contributes net 1 to the right-hand combination: if $x$ lies in exactly $r \in \{1,2,3\}$ of the sets, it contributes $r - \binom{r}{2} + \binom{r}{3}$, and the three cases give $1-0+0 = 2-1+0 = 3-3+1 = 1$. Sum over $U$.

**Source B.** Cornell CS280 (Spring 2001) Handout 25, *The Inclusion-Exclusion Principle* — element-classification proof; Theorem 25.4 generalizes via $\sum_i (-1)^{i+1}\binom{r}{i} = 1$. https://www.cs.cornell.edu/courses/cs280/2001sp/handouts/h25.pdf (agent opened and read). Second attestation: cut-the-knot, "The Inclusion-Exclusion Principle" (agent opened and read).

**Distinctness rationale.** A never inspects an element — pure cardinality algebra driven by the two-set identity; B never uses the two-set identity — indicator decomposition plus per-element case analysis.

**Signatures A (required).**
- Two-three uses of `Finset.card_union_add_card_inter`.
- `Finset.union_inter_distrib_right` for $(A\cup B)\cap C$.
- Intersection normalization (`inter_assoc`/`inter_comm`/`inter_self`).
- Final `omega`/`linarith` over the linear card relation.

**Signatures A (incompatible).**
- Any per-element reasoning: `card_eq_sum_ones`, `sum_boole`, `Set.indicator`, `by_cases hA : x ∈ A`.
- Top-level introduction of an arbitrary union element.

**Signatures B (required).**
- Cards rewritten as sums over the union (`card_eq_sum_ones` / `sum_filter` / `sum_boole`).
- Reduction of the goal to a pointwise statement about one $x$.
- Explicit membership case split (8 branches, or 3 after grouping by $r$).
- Branches closed by `simp [hA, hB, hC]` / `decide` / `omega` on numerals.

**Signatures B (incompatible).**
- Any packaged two-set inclusion-exclusion lemma (`card_union_add_card_inter`).
- `union_inter_distrib_right` restructuring.

**Contamination risk.** MEDIUM — statement ubiquitous; element-counting is the standard proof, but the fully carried-out iterate-the-two-set-case derivation is usually left as an exercise, so the pairing is less memorized.

**Automation/library caveats.** `decide`/`omega` cannot see set structure — no outright collapse (a plus). (i) `Finset.card_union_add_card_inter` IS the two-set case: grade it as a route-A signature, not "the theorem." (ii) Mathlib's general `Finset.inclusion_exclusion_card_biUnion` subsumes the statement but instantiating at 3 sets is awkward — flag any use as a third, off-benchmark route (library-lookup policy). (iii) The ℕ-subtraction-free statement form is load-bearing: truncated subtraction makes the usual form provable for spurious reasons.

**Lean statement sketch.** `theorem card_union_three {α : Type*} [DecidableEq α] (A B C : Finset α) : (A ∪ B ∪ C).card + (A ∩ B).card + (A ∩ C).card + (B ∩ C).card = A.card + B.card + C.card + (A ∩ B ∩ C).card` — UNVERIFIED.

## Review notes

- **Sources**: Ximera (already verified live earlier today for 017), Cornell handout +
  cut-the-knot per agent; spot-check the Cornell PDF at approval.
- **Math checked (Claude)**: both routes correct; the subtraction-free form is the
  right call and shows real formalization care.
- **Strongest keeper of this batch**: fresh contrast axis (cardinality algebra vs.
  per-element indicator case split), MEDIUM contamination, automation-resistant both
  routes, no exact library hit. Fills the counting domain without repeating the
  double-count-vs-algebra axis.
- **Verdict recommendation**: KEEP — pilot-eligible.
