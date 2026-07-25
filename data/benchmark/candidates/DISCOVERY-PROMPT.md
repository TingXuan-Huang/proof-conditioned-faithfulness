# Reusable Discovery Prompt — A/B Proof-Strategy Pairs

Paste the prompt below into any capable agent (Codex, Claude, etc.) to source new
candidates. Update the exclusion list at the bottom as candidates accumulate. Batch
size: 2-3 candidates per run. Results go into this folder as numbered files,
Status: draft, with the producing agent recorded in the Batch line.

---

You are doing source discovery for a research benchmark on proof-conditioned Lean
autoformalization. The benchmark needs theorems where TWO genuinely different, complete,
correct informal proof STRATEGIES exist, both attested in reliable human-authored
mathematical sources.

Find 2-3 candidate theorem pairs in these domains: elementary number theory, integer
reasoning, divisibility, parity, finite sums, finite sets/counting, elementary algebra,
elementary inequalities. (Avoid analysis with limits/continuity, geometry, topology —
formalization overhead would dominate.) Theorems must be elementary enough that a
Lean 4 + Mathlib formalization of the STATEMENT is straightforward.

Requirements per candidate:
1. One theorem, precisely stated.
2. Proof strategy A: a complete informal proof using one mathematical route.
3. Proof strategy B: a complete informal proof of the SAME theorem using a GENUINELY
   DIFFERENT mathematical route (e.g. induction vs. direct algebra, contradiction,
   extremal argument, counting/bijection, well-ordering, invariant, telescoping,
   pairing). "Different tactics, same idea" does NOT count — the routes must be
   distinguishable by a blinded expert.
4. Both strategies must come from real human-authored sources (textbooks, university
   lecture notes, ProofWiki, cut-the-knot, AoPS articles, published papers). Use web
   search to verify each strategy is actually attested in at least one source. Record
   source title + URL (or book title/author/section) for EACH strategy. Do not
   fabricate sources — if you cannot verify a source, say "UNVERIFIED" explicitly.
5. Write the proofs in YOUR OWN adapted wording (do not copy copyrighted text verbatim).
6. Draft strategy metadata: for each strategy, 2-4 "required signatures" (observable
   evidence expected in a formal proof following this route) and 1-2 "incompatible
   signatures" (evidence indicating the OTHER route).
7. Familiarity assessment: rate LOW/MEDIUM/HIGH contamination risk (is this
   theorem+proof pairing likely memorized by LLMs?) with one sentence of reasoning.

Prefer theorems where BOTH proofs are short (each under ~15 lines of informal text) and
the two strategies produce visibly different formal proof shapes.

**EXCLUDED — already in the candidate pool, do not propose these theorems or closely
equivalent restatements of them:**
1. 6 divides n³ − n
2. √2 is irrational / no integers with a² = 2b²
3. odd n implies 8 divides n² − 1
4. Σ k·k! = (n+1)! − 1
5. Σ C(n,k) = 2ⁿ
6. Σ 1/√k > 2(√(n+1) − 1)
7. coprime(a,n) ∧ coprime(b,n) → coprime(ab,n)
8. a/gcd(a,b) and b/gcd(a,b) are coprime
9. gcd(a,b)·lcm(a,b) = ab
10. 9 divides n³+(n+1)³+(n+2)³
11. 2 divides C(2n,n) (central binomial coefficient is even)
12. Σ 1/k² ≤ 2 − 1/n
13. Σ F_i² = F_n·F_{n+1} (Fibonacci sum of squares)
14. consecutive Fibonacci numbers are coprime
15. a²+b²+c² ≥ ab+bc+ca
16. n has an odd number of divisors ⟺ n is a perfect square
17. hockey-stick identity Σ_{i=r}^{n} C(i,r) = C(n+1,r+1)
18. Bernoulli's inequality (1+x)ⁿ ≥ 1+nx
19. two-variable Cauchy–Schwarz (ac+bd)² ≤ (a²+b²)(c²+d²)
20. # even-sized subsets = # odd-sized subsets (n ≥ 1)
21. Σ C(n,k)² = C(2n,n)
22. three-set inclusion–exclusion |A∪B∪C| identity
23. odd n, permutation a of {1..n}: ∏(aᵢ−i) is even
24. handshake lemma / # odd-degree vertices is even
25. F_n even ⟺ 3 | n
26. Euler duplication product ∏(1+X^(2^k)) = Σ X^j
27. (a−b) | (aⁿ−bⁿ)
28. (a+b) | (a^(2m+1)+b^(2m+1))
29. p | 2^p − 2 (Fermat little, base 2)
30. p | n²+n+1 ⇒ p = 3 or p ≡ 1 (mod 3)
31. nonresidue × nonresidue = residue mod odd prime
32. same digit multiset ⇒ 9 | difference
33. every n is a sum of distinct powers of 2
34. Nicomachus Σk³ = (Σk)²

Also avoid: sum of first n integers = n(n+1)/2 (Gauss pairing vs induction is
contamination-famous), sum of first n odd numbers = n², infinitude of primes, Binet's
formula, Erdős–Szekeres (flagged as a formalization-heavy stretch option, not pooled).

**Leads noted by prior batches, available if a slot opens**: Euclid's lemma itself
(Bézout vs. well-ordering descent — MEDIUM-HIGH contamination, named lemma);
Erdős–Szekeres (pigeonhole-labeling vs. Dilworth — heavier statement). Batch-3 agent
found no elementary pigeonhole theorem with two genuinely distinct attested routes.

Return your final answer as raw Markdown, one section per candidate, using exactly this
template per candidate:

## Candidate: <short-slug>
**Theorem.** <precise statement, also give a draft LaTeX-ish formal reading>
**Domain.** <e.g. divisibility>
**Strategy A — <name>.** <complete informal proof, adapted wording>
**Source A.** <title, author, URL or book section — or "UNVERIFIED" if not confirmed>
**Strategy B — <name>.** <complete informal proof, adapted wording>
**Source B.** <same>
**Distinctness rationale.** <1-2 sentences: why a blinded expert would call these different routes>
**Signatures A (required).** <bullet list>
**Signatures A (incompatible).** <bullet list>
**Signatures B (required).** <bullet list>
**Signatures B (incompatible).** <bullet list>
**Contamination risk.** <LOW/MEDIUM/HIGH + one sentence>
**Lean statement sketch.** <a one-line guess at the Lean 4 statement, marked UNVERIFIED>

Quality over quantity: 2 excellent candidates beat 3 mediocre ones. The single most
important property: both proofs COMPLETE and CORRECT, and the strategies genuinely
distinct.
