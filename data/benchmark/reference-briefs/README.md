# Reference-proof generation briefs

Prep sheets for generating the A/B **reference proofs** of the proposed pilot-5 with an
external reasoning model (agent mode). Workflow (owner: Tingxuan, 2026-07-25):

1. Paste `00-COMMON-BRIEF.md` once into the reasoning agent's context, then one
   `brief-XXX-*.md` per generation task.
2. Hand the returned Lean code to the server agent, which compiles it under the trusted
   checker rules (fresh file, axiom audit, no-`sorry`) and reports per-route pass/fail.
3. Compile pass is NOT approval: a human still verifies each proof follows its route
   (the "must appear / must NOT appear" lists) before any candidate flips to
   `Status: approved`. These proofs are load-bearing benchmark artifacts
   (coding-standard/PROJECT_ARTIFACTS.md) — human-owned.

Proposed pilot slate (Gate P remains the human's call; flipping Status on the candidate
files is the approval act): 001, 033, 036, 040, 041. Rationale: all MEDIUM
contamination; 033/036/040/041 were the review pass's pilot-eligible keepers (036
pilot-priority — the pool's only WOP-vs-induction contrast; 040 zero library collapse;
041 most collapse-resistant); 001 chosen by the user as the warm-up/pipeline-shakedown
pair. Five distinct formal shapes: ℤ-induction vs factorization, List.Perm structural
induction vs digit-sum congruence, WOP vs strong induction, parity vs coprimality after
a Real.logb bridge, divisor enumeration vs 2-adic parity in ℚ.

Briefs are derived from `../candidates/` files with sources/contamination/review notes
stripped and the signature lists recast as generation constraints. If a brief and its
candidate file disagree, the candidate file wins — fix the brief.
