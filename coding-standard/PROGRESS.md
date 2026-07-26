# Progress Log

Running log, newest entry first. Copy an entry template from
[PROGRESS_LOG.template.md](PROGRESS_LOG.template.md), fill it in, and prepend it here.

Two purposes: keeps the agent oriented across sessions (what's been built, what broke and
why, in what order), and serves as raw material for later retrospective analysis — an
agent can be run over this file to audit how the agentic workflow itself is going, not
just the code.

---

### 2026-07-25 — Adopt 600-second trusted-check timeout after SLURM boundary evidence

- **Tier:** prototype trust-boundary correction
- **File(s):** trusted Lean checker, root CLI, checker tests, PLAN, runbook, human TODO,
  and `todo.md` T016/T017.
- **What:** The owner changed normative S2 from 120 to 600 seconds per fresh candidate.
  Batch preflight runs a separate fixed-source Mathlib/audit warm-up with a 1,200-second
  ceiling before candidates; the warm-up contains no model output.
- **Why:** Clean-commit CPU job `37715755` passed `lake build` but emitted 18 pytest
  failure markers at roughly successive 120-second boundaries before cancellation.
  Pytest had not printed tracebacks, so exact failures were not observed; old timeout
  evidence is operationally invalid, never theorem invalidity.
- **How it works:** `DEFAULT_TIMEOUT_SECONDS` is the shared S2/S3/generated-response
  default. `proof-faithfulness env lean-warmup` uses the existing network-isolated,
  resource-bounded subprocess with its own default. Timeout fixtures pass explicit
  millisecond-scale limits. A fresh clean-commit full gauntlet remains required.
- **Human boundary:** This records the timeout decision only. It does not approve Gate P,
  Gate S, a candidate Status, an import change, or proof faithfulness.

### 2026-07-25 — Consolidate the engineering and human-review handoff

- **Tier:** exploratory documentation checkpoint
- **File(s):** repository history through `6c64f6d`,
  `docs/plans/active/PLAN.md`, `todo.md`,
  `docs/SERVER-HARNESS-RUNBOOK.md`, and
  `docs/HUMAN-REVIEW-TODO.md`.
- **What:** Reconciled the complete project history, stage evidence, known failures,
  prototype limitations, and human-owned decisions into this progress log and a
  standalone human checklist. This snapshot is the starting point for a future human
  or agent; it does not promote any draft candidate or approve any gate.
- **Why:** S1-S5 are green on fixtures, but that statement alone hides important
  distinctions: real reference proofs mostly do not compile, some production choices
  remain provisional, no real model/API smoke has run, and the owner still needs to
  review load-bearing code and research decisions.
- **How it works:** The checklist separates reproducible commands from code-reading
  scope and from decisions. Every uncertain timeout, import, model, billing,
  annotation, or analysis choice is left as an unchecked human gate rather than being
  silently converted into an implementation decision.

#### Historical progress reconstructed

1. **Research and repository setup (2026-07-22 to 2026-07-24):** Established the
   counterfactual proof-conditioning question, MATH-AI primary venue, Tier 1-4 condition
   matrix, five-pair pilot/30-pair core structure, and human ownership rules. Created the
   Python 3.12/uv and Lean 4.15.0/Mathlib v4.15.0 scaffold, active plan, runbook, coding
   standard, schemas, and GitHub remote.
2. **Benchmark discovery (2026-07-24):** Drafted candidates 001-044 over several
   discovery rounds, recorded contamination and library-collapse risks, and proposed
   001/033/036/040/041 as a pilot-5. The proposal remains unapproved. T010 retains the
   optional low-contamination discovery rerun.
3. **Server discovery (2026-07-24 to 2026-07-25):** Verified Klone allocations,
   partitions, L40/L40S 48 GB GPUs, quota/purge policy, compute-node egress, Apptainer,
   and required GCC/TLS settings. Recorded public Tillicum H200, QoS, storage, purge,
   and billing facts. Account attachment, credit expiration, direct Tillicum egress,
   secret delivery, and exact frontier provider remain open under T008.
4. **S1 contracts and storage (2026-07-25):** Implemented strict Pydantic contracts,
   generated JSON Schemas, response-sensitive deterministic request IDs, atomic and
   checksummed artifact storage, immutable frozen runs, and the root CLI. Unit tests,
   Ruff, Pyright, schema reproduction, and CLI help passed at the recorded checkpoint.
5. **S2 trusted checking (2026-07-25):** Implemented fresh-process Lean compilation,
   exact statement/header enforcement, one-body extraction, bounded execution, socket
   isolation, normalized failures, prohibited-token checks, and an allow-listed axiom
   audit. Seventeen integration tests covered valid, syntax/type errors, timeout,
   changed statement, `sorry`, custom axiom, multiple blocks, trust bypass, and allowed
   classical axioms; `lake build` passed.
6. **S3 dependency probing (2026-07-25):** Added proof-term used-constant and local-fact
   evidence, tactic signatures, trusted report parsing, and used/unused deletion tests.
   Thirteen tests passed. Explicit-step utilization is provisional; choosing it versus
   a full dependency graph remains a human decision.
7. **S4 model and generation harness (2026-07-25):** Added strict adapter/model configs,
   deterministic mock inference, OpenAI-compatible transport, ProofBridge/ProofFlow
   subprocess adapters, hashed prompt rendering, exact planning, retries with stable
   request IDs, atomic response artifacts, verified resume, repair lineage, locks,
   aggregate budgets, and approval-bound paid requests. Offline planning reports 45
   proof-conditioned plus 15 theorem-only Tier-1 pilot requests. The exact harness tests
   passed 21 tests and the focused S4 suite passed 131 tests; an empty `approvals/`
   refuses paid work.
8. **S5 evaluation and annotation (2026-07-25):** Added deterministic signatures,
   blinded export, immutable private mappings, independent label import, calibration,
   disagreement/adjudication preservation, and agreement statistics. The 41-test exit
   passed, including grep-based leakage rejection and hand-computed 10-item statistics.
   Strategy meaning, rubric approval, labels, and adjudication remain human-owned.
9. **Integration checkpoint (2026-07-25):** Recorded 246 passing tests plus one stale
   `context_window` fixture failure; the fixture was fixed and its targeted regression
   passed. Ruff passed. Pyright found one Decimal typing issue, which was fixed before a
   zero-error rerun with `gcc/12.3.0`. `lake build` passed with one non-fatal unused
   variable warning. A post-fix full-pytest rerun was not observed and remains a useful
   human reproduction check.
10. **Submitted reference screening (2026-07-25):** Stored all ten human-supplied pilot
    Route A/B drafts without approving them. Extended offline SLURM job `37700033`
    completed in 19:35 with no timeout: only `036-A` compiled, with no `sorry` and only
    `propext`/`Quot.sound`; the other nine produced Lean errors. `033-A`, `041-A`, and
    `041-B` also contain `sorry`. Proof repair is intentionally out of scope for the
    prototype; only `036-A` is eligible for S3.
11. **Publication state (2026-07-25):** Local proof/data and documentation commits are
    `218d80f`, `57bafe6`, and `6c64f6d`. They are not on `origin/main`. Earlier HTTPS
    credentials could not supply a username; a later attempt was stopped before network
    access because execution policy treats an unverified external default-branch push
    as high risk. No credentials or remote settings were changed.

#### Error and incident ledger

- **Full test run:** One fixture omitted required `context_window`. Fixed; its targeted
  test passed. The full suite was not rerun afterward, so no broader post-fix pass is
  claimed.
- **Static typing:** Pyright exposed one Decimal type mismatch. Fixed; Pyright then
  passed. Its Node runtime required `module load gcc/12.3.0` for `libatomic.so.1`.
- **Mathlib cache TLS:** Cache retrieval initially failed until
  `SSL_CERT_FILE=/etc/pki/tls/certs/ca-bundle.crt` was used. The cache then retrieved
  all 5,826 artifacts.
- **Sandbox tooling:** `uv` and Ruff could not write their configured shared caches from
  the restricted agent sandbox; the diagnostic runner used the existing `.venv` and
  Ruff `--no-cache`. The system `/usr/bin/python3` was too old for
  `from __future__ import annotations`, so the project Python 3.12 interpreter was used.
  ShellCheck is not installed; batch scripts received `bash -n` checks only.
- **SLURM capacity:** Job `37695207` waited on `AssocGrpMemLimit`; later normal jobs
  intermittently waited on `AssocGrpCpuLimit`. Prototype diagnostics used permitted
  `ckpt`/`ckpt-g2` capacity when appropriate. Preemption remains acceptable only for
  development checks, never for paid API jobs.
- **Cold umbrella import:** Cold `import Mathlib` on GPFS exceeded 600 seconds in job
  `37696157`. Normative 120-second fresh-process job `37697588` therefore produced seven
  timeouts, three direct errors, and zero accepted routes. Combined diagnostic job
  `37699980` amortized the import and preserved errors. Extended job `37700033` used a
  1,200-second warm-up and 600 seconds per route, resolved every timeout, and found one
  compiling route. These diagnostic limits did not change the S2 contract.
- **Reference 001:** Route A first fails because `omega` cannot prove an evenness goal
  and also names unavailable constants; Route B first fails on an `Int`/`Nat` evenness
  type mismatch.
- **Reference 033:** Route A has `sorry` and the final `ModEq.dvd` direction is reversed;
  Route B first fails while rewriting the `Nat.ofDigits` difference.
- **Reference 036:** Route A compiles with allowed axioms. Route B cannot synthesize
  `DecidablePred P` for `Nat.find`.
- **Reference 040:** Both routes first fail by rewriting `hx` in the wrong direction and
  contain additional rational-number/API mismatches. Neither compiles.
- **Reference 041:** Both routes first fail at the cast from `Rat.den_pos q` to the local
  integer denominator and contain further clearing-denominator/parity errors. Route A
  has two `sorry` placeholders; Route B has one.
- **Repository publication:** Push remains blocked as described above. Local commits and
  a clean worktree preserve the checkpoint.

#### Human-gated questions carried forward

- The owner decided S2 uses a separate 1,200-second fixed-source warm-up followed by
  600 seconds per fresh candidate. Verify this on each host. Decide separately whether
  canonical pilot imports remain
  `import Mathlib` or become minimal imports; import changes affect hashes and experiment
  identity.
- Decide whether the nine failing reference routes are replaced, repaired by a human,
  or removed with their candidate pair. Do not approve Gate S from the current drafts.
- Freeze the S3 utilization metric and human interpretation of ambiguous strategy use.
- Review the model/prover slate, revisions, decoding recipes, hardware placement, and
  real request counts before any model execution.
- Confirm provider, secret delivery, approval scope, request ceiling, and billing before
  any live API call. T011's permit is a guardrail, not authorization.
- Freeze analysis choices, annotation rubric, second-annotator plan, artifact ownership,
  license/citation, and release/push mechanism at their documented gates.
- Follow the unchecked tasks and exact commands in
  `docs/HUMAN-REVIEW-TODO.md`; agents must not mark those tasks approved.

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
  and followed by `#print axioms`. At the time, the extended limits were diagnostic;
  the owner later adopted the same 600-second candidate ceiling plus a separate
  fixed-source warm-up as the normative S2 contract. `036-A` reported only allowed axioms
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
      `outputs/reference-proof-checks/37700033/results.json`. Proof/data and documentation
      commits `218d80f` and `57bafe6` were created locally. Their push was stopped before
      network access because execution policy treats the unverified external
      `origin/main` mutation as high risk; credentials and remote configuration were not
      changed.

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
