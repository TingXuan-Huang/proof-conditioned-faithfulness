# Progress Log

Running log, newest entry first. Copy an entry template from
[PROGRESS_LOG.template.md](PROGRESS_LOG.template.md), fill it in, and prepend it here.

Two purposes: keeps the agent oriented across sessions (what's been built, what broke and
why, in what order), and serves as raw material for later retrospective analysis — an
agent can be run over this file to audit how the agentic workflow itself is going, not
just the code.

---

### 2026-07-25 — Compile-screen submitted pilot reference proofs

- **Tier:** exploratory
- **File(s):** `data/benchmark/reference-briefs/brief-{001,033,036,040,041}-*.md` and
  ignored artifacts under `outputs/reference-proof-checks/`.
- **What:** Extracted ten submitted Route A/B Lean blocks verbatim and exercised them in
  offline CPU SLURM jobs. The normative 120-second run persisted bounded timeout/error
  results; combined job `37699980` showed the runner continues across bad declarations;
  extended job `37700033` completed in 19:35 with a 1,200-second warm-up allowance and
  600 seconds per route. One route (`036-A`) compiled without `sorry`; nine produced Lean
  errors. Three (`033-A`, `041-A`, `041-B`) also contain `sorry`.
- **Why:** Validates that the prototype compilation pipeline accepts a submitted valid
  proof, rejects or diagnoses invalid inputs, continues after failures, and persists
  evidence. Repairing the submitted proofs is outside this prototype checkpoint.
- **How it works:** Each route is written to a fresh file, compiled with Lean 4.15.0,
  and followed by `#print axioms`. The extended limits are diagnostic only and do not
  change S2's normative 120-second contract. `036-A` reported only allowed axioms
  (`propext`, `Quot.sound`). No network, paid API request, GPU, or model download was used.
- **Reused pattern or new one?** Reuses the S2 fresh-file and axiom-audit boundary; adds
  an operational cache warm-up/extended-time diagnostic for umbrella `import Mathlib`
  on GPFS-backed compute nodes.
- **Review findings:** No pipeline correctness bug was found. The apparent widespread
  failures in the first run were cold/full-import timeouts; larger diagnostic bounds
  resolved all of them into one success and nine concrete Lean errors. Proof errors are
  recorded as data and skipped, not repaired.
- **Verification:** Runner passed Ruff; batch scripts passed `bash -n` (ShellCheck is not
  installed). SLURM `37700033` finished `COMPLETED`, exit `0`, on `n3447`; summary was
  `total=10 compiles=1 no_sorry_and_compiles=1`. Results are in
  `outputs/reference-proof-checks/37700033/results.json`.

### 2026-07-25 — Complete fixture-backed S1-S5 engineering checkpoint

- **Tier:** exploratory
- **File(s):** `ProofFaithfulness/{Audit,Dependency}.lean`,
  `src/proof_faithfulness/{lean,generation,evaluation,models}/`, `configs/`, `prompts/`,
  and their unit/integration fixtures.
- **What:** Completed the trusted Lean checker, dependency/utilization probe, generation
  harness, and evaluation/annotation tooling against offline fixtures. Exact evidence:
  S2 `lake build` green plus 17 checker tests; S3 13 probe tests; S4 45 conditioned + 15
  theorem-only = 60 Tier-1 pilot requests at `$0`, valid `plan-check` with Tier 2
  `+30/+0`, 21 exact harness tests and 131 focused S4 tests; S5 41 exact tests. No
  network or paid request was made.
- **Why:** Reaches the engineering checkpoint at which the remaining ordered inputs are
  human-owned pilot approval/reference proofs and, later, a key plus an `approvals/`
  permit for Gate A. Passing S1-S5 does not mark Gates P, S, C, or A approved.
- **How it works:** The checker parses exactly one escaped proof term and audits axioms
  in an isolated process. The probe separates syntax evidence from elaborated
  `letFun`/`letE` utilization. The harness binds request identity, plan, budget approval,
  raw artifacts, retries, and resume state. Evaluation exports blinded packets and
  preserves independent labels through calibration, disagreement, and adjudication.
- **Reused pattern or new one?** Reuses frozen Pydantic contracts, content addressing,
  atomic writes, and fail-closed validation across all stages. The Lean report commands
  and paid-run ledger/permit boundary are new load-bearing patterns.
- **Review findings:** Blocking issues fixed before the checkpoint included truncated or
  spoofed trusted reports, binder-name utilization collisions, cross-run duplicate paid
  IDs, caller-overridable ceilings, lock/interrupt/approval races, incomplete raw
  failure evidence, blinding leaks, incomplete calibration/freeze provenance, agreement
  edge cases, and crash recovery. The final S2/S3 quick standard pass found one blocker
  and it was fixed; its research pass found no blocker. S4's existing standard pass
  found 10 blockers and all 10 were fixed; its research pass reported all blocking
  findings fixed but did not retain a numerical count. Existing S5 review evidence was
  accepted without another deep round. Minor cosmetic/extensibility findings were
  deferred under the prototype policy.
- **Verification:** One integration-gauntlet pass produced `246 passed, 1 failed`; the
  failure was a stale test fixture missing required `context_window`, and its targeted
  regression passed after correction (`1 passed`). Full Ruff passed. Pyright first
  found one Decimal error and then passed with zero errors after correction and
  `module load gcc/12.3.0`. `lake build` passed with one non-fatal unused-variable
  warning. A post-fix full-pytest rerun was not observed in this checkpoint. Publishing
  is locally blocked: `git push origin main` cannot read an HTTPS username, `gh` is not
  installed, and the previously tested SSH path was denied; credentials were not changed.
- **Standard feedback (optional):** Prototype review blocks correctness, trust,
  data-integrity, blinding, spend, and Exit failures; low-risk library polish can be
  logged for later. Deferred limitations include heuristic tactic-occurrence evidence,
  conservative numeric blinding matches, broader Part-3 metrics, and optional batch
  transport/request-order randomization policy.

### 2026-07-25 — Build reproducible S1 contracts and S4 adapter foundation

- **Tier:** library
- **File(s):** `src/proof_faithfulness/{schema,ids,artifacts,cli}.py`,
  `src/proof_faithfulness/models/`, `tests/unit/`, Lean scaffold, emitted schemas.
- **What:** Added frozen data contracts, response-affecting request identities,
  crash-recoverable checksummed run storage, CLI inspection/export, normative model-slate
  configuration, deterministic mock inference, OpenAI-compatible local transport, and
  commit-bound ProofBridge/ProofFlow subprocess adapters.
- **Why:** Implements S1 and the reviewed adapter foundation required before S2-S5 can
  share stable request, artifact, and model boundaries.
- **How it works:** Every response-affecting input, including prompt bytes, slate key,
  model identity, and backend configuration, is hashed. Paid frontier transport remains
  fail-closed pending T011; external pipelines are revision-checked, environment-
  allowlisted, size-bounded, and process-group isolated.
- **Reused pattern or new one?** Reuses Pydantic contracts and content-addressed atomic
  artifacts; introduces the common `ModelAdapter` boundary used by the generation lane.

### 2026-07-24 — Add fourth proof-strategy discovery batch

- **Tier:** exploratory
- **File(s):** `data/benchmark/candidates/009-gcd-times-lcm.md`,
  `data/benchmark/candidates/010-bernoulli-nonnegative.md`,
  `data/benchmark/candidates/011-cauchy-schwarz-two-variable.md`
- **What:** Added three draft A/B theorem candidates with complete paraphrased proofs,
  precise source locators, strategy signatures, contamination assessments, and
  unverified Lean statement sketches.
- **Why:** Continued the reusable discovery workflow with two to three additional
  candidates outside the existing exclusion list.
- **How it works:** Full source documents were inspected for both claimed routes. The
  batch covers prime valuations versus coprime reduction, induction versus binomial
  expansion, and a direct Lagrange identity versus a discriminant argument.
- **Reused pattern or new one?** Reuses the numbered draft-candidate and human-review
  boundary. The two classic inequality candidates are explicitly marked high
  contamination risk rather than screened out silently.

### 2026-07-24 — Add third proof-strategy discovery batch

- **Tier:** exploratory
- **File(s):**
  `data/benchmark/candidates/007-odd-number-of-divisors-iff-square.md`,
  `data/benchmark/candidates/008-hockey-stick-identity.md`
- **What:** Added two draft A/B theorem candidates with complete paraphrased proofs,
  source locators, strategy signatures, contamination assessments, and unverified Lean
  statement sketches.
- **Why:** The reusable discovery prompt requests small batches of source-verified
  candidates whose two proofs have visibly different formal shapes.
- **How it works:** Each claimed route was checked in the full university-hosted source;
  the batch kept only the divisor-involution versus prime-exponent contrast and the
  induction versus largest-element double-counting contrast.
- **Reused pattern or new one?** Reuses the existing numbered draft-candidate format and
  review boundary; neither file is human-approved.

<!-- Newest entries go here, above this line. -->
