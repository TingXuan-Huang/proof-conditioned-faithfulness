# HUMAN-REVIEW-TODO.md

**Owner:** Tingxuan Huang \
**Prepared by:** coding agent, 2026-07-25 \
**Last engineering update:** 2026-07-29

This is the human-facing review and decision queue for the proof-conditioned
faithfulness prototype. Every checkbox is human-owned and intentionally unchecked.
Passing fixture tests is evidence that the machinery runs; it is not approval of the
benchmark, scientific interpretation, model slate, spending, or publication claims.

## Current state in one minute

- Real-backend compatibility testing is complete. GPT-OSS passed on H200/MXFP4, Qwen
  passed on the required H200/BF16, DeepSeek-Prover passed generation on L40/BF16, one
  approved Meta request passed live transport, and both pipeline incompatibilities are
  checksummed. Read `docs/REAL-BACKEND-COMPATIBILITY-REPORT.md` before choosing a slate.
- Final offline job `37869456` passed a node-local Mathlib warm-up, 283 pytest tests,
  Ruff, zero-error Pyright, and `lake build`. Seven focused paid-safety/resume tests and
  all 114 authoritative calibration sidecars also passed verification.
- The Meta request cost `$0.008082`, then immediate resume skipped it without another
  request. Its output is calibration-only and cannot enter pilot/core results. No
  GPT-5.6 Terra, pilot, or core request has run.
- Qwen H200, DeepSeek, and Meta produced respectively `type_invalid`, `multiple_blocks`,
  and `syntax_invalid` proof text. This is acceptable compatibility evidence: the
  checker classified each outcome and correctly skipped dependent stages. GPT-OSS and
  an independent Qwen A100 sample passed Lean/dependency/evaluation end to end.
- ProofBridge's public release lacks runnable inference/checkpoint assets. ProofFlow
  reached pinned Qwen generation, then failed in upstream `build_proof_graph`. Humans
  must decide whether to patch, replace, or exclude the pipeline category.
- A GPU-accounting bug is fixed in commit `15fe536`; audited correction records report
  Qwen H200 peak 130,983 MiB and DeepSeek L40 peak 41,781 MiB. Original inaccurate
  runtime artifacts remain preserved.
- Trusted node-local job `37724510` accepted the exact `036-A` statement/body with only
  allowed axioms and persisted S3. Its provisional `automation_bypass` classification
  requires human interpretation. Nine other submitted routes have saved Lean errors;
  three contain `sorry`. Gate P, Gate S, and every candidate Status remain open.
- A Meta credential value was pasted into chat and later used only through the approved
  interactive environment path. It was not found in tracked or calibration artifacts.
  Unset it locally and revoke it in the Meta dashboard; use a fresh key for any later
  separately approved request.
- Klone full-Mathlib execution now requires a checksummed LZ4 snapshot extracted into
  private node-local /tmp. GPFS job 37717888 timed out with almost no CPU use. Local
  4 GiB job 37720527 exited 139, while unlimited 37720766 and bounded 8 GiB 37721113
  both succeeded at about 4,072,000 KiB maximum RSS.
- The child remains bounded at 8,192 MiB and SLURM jobs must request at least 16 GiB.
  A resource signal is an operational outcome, not a proof failure. This evidence does
  not approve a human gate.
- S1-S5 remain green on fixture/mock Exit criteria. Deferred deep reviews remain open.
- The proposed pilot-5 is 001/033/036/040/041. It is still draft; Gate P is open.
- Ten submitted reference routes were compiled in extended offline SLURM job
  `37700033`. Only `036-A` compiles. Nine routes have saved Lean errors, and three of
  those also contain `sorry`. Gate S is open.
- The owner reports a second annotator is secured. Onboarding, independence/conflict
  review, rubric training, and annotation calibration remain human-owned.
- S5 can blind and import labels and compute agreement on fixtures. Humans have not
  frozen the rubric or produced real annotations.
- Local checkpoint commits after `origin/main` are not pushed.

## Immediate model-slate review

- [ ] Read every row and evidence path in
  `docs/REAL-BACKEND-COMPATIBILITY-REPORT.md`; confirm the measured model identity,
  hardware, memory, latency, throughput, and cost are sufficient for the intended run.
- [ ] Choose GPT-OSS and/or Qwen as the open-weight production model. Qwen has both H200
  and A100 evidence; GPT-OSS requires H200-class capacity.
- [ ] Decide whether DeepSeek's multiple-block output should be accepted via a
  human-reviewed prompt/output-contract change, retained only as a fallback, or
  replaced. Do not let the harness repair generated proof text silently.
- [ ] Decide whether to patch/replace ProofBridge or ProofFlow, or explicitly freeze a
  slate without a proof-conditioned pipeline and record the scientific consequence.
- [ ] Confirm Meta remains testing-only and is excluded from every experimental
  manifest. Decide separately whether/when GPT-5.6 Terra receives a future approved
  smoke request.
- [ ] Revoke the chat-exposed Meta key. In the current shell run
  `unset META_MODEL_API_KEY`, then confirm
  `test -z "${META_MODEL_API_KEY+x}" && echo cleared`.
- [ ] After reviewing the above, record the human slate decision in the active plan.
  Only the human owner may freeze the slate or close a readiness gate.

## Incident and publication review

- [ ] Read `docs/CLUSTER-EXPERIMENT-INCIDENTS.md`. Confirm that infrastructure,
  harness, backend-compatibility, model-output, and human-gate failures are separated
  correctly and that no failed job is being interpreted as a mathematical result.
- [ ] Review the node-local LZ4 SquashFS policy, 8,192-MiB Lean child limit, at-least
  16-GiB SLURM request, 1,200-second warm-up, and 600-second candidate limit against
  jobs `37717888`, `37720527`, `37720766`, `37721113`, and `37869456`.
- [ ] Review the preserved correction records for Qwen H200 and DeepSeek L40 GPU peaks.
  Confirm reports use 130,983 MiB and 41,781 MiB rather than the original incorrect
  string-comparison values.
- [ ] Review every paid-request incident: missing approval, dirty worktree refusal,
  missing-secret preflight, one successful Meta request, exact cost settlement, no-op
  resume, secret scan, and required key revocation.
- [ ] Confirm the accepted limitations are acceptable for a prototype: ProofBridge is
  not runnable from its public release; ProofFlow fails in upstream proof-graph
  construction; DeepSeek emits multiple blocks; Qwen/Meta calibration proofs were
  invalid but honestly classified.
- [ ] Before publishing, fetch with your normal authenticated setup and inspect the
  complete local series. Do not assume the locally cached `origin/main` is current.

```bash
cd /mmfs1/gscratch/stf/thuang27/proof-conditioned-faithfulness
git status --short
git fetch origin
git rev-list --left-right --count origin/main...HEAD
git log --oneline origin/main..HEAD
git diff --stat origin/main...HEAD
git diff --check origin/main...HEAD
git grep -nP '(?<![A-Z])LLM_[A-Za-z0-9_-]{10,}|sk-[A-Za-z0-9_-]{20,}' -- . || true
```

- [ ] Confirm the secret scan returns no credential value, the worktree is clean, and
  the fetched remote is not ahead before running your authenticated push.

```bash
git push origin main
```

Publishing commits does not approve Gate P/S/C/A, the model slate, or a production run.

## Immediate manual reproduction

Use the root `README.md` as the primary copy-paste Hyak operating guide. This section is
the independent human confirmation checklist; when commands diverge, stop and reconcile
the README with `docs/SERVER-HARNESS-RUNBOOK.md` before running either version.

Run this on Klone in an interactive CPU allocation. Use normal `cpu-g2` when the
allocation is available; `ckpt-g2` is acceptable for development checks but can be
preempted. Never use a preemptible job for a paid API call.

- [ ] Start an interactive session and confirm the allocated hostname.

```bash
srun --account=stf --partition=cpu-g2 --time=01:30:00 \
  --cpus-per-task=2 --mem=16G --pty bash -l
hostname
```

- [ ] Enter the repository, load the required compiler runtime, and inspect the exact
  commit/worktree before running anything.

```bash
module load gcc/12.3.0
cd /mmfs1/gscratch/stf/thuang27/proof-conditioned-faithfulness
git rev-parse HEAD
git status --short
```

- [ ] Reproduce the frozen environment. Do not run `uv lock` on the server.

```bash
uv sync --frozen --all-extras
uv run python -c \
  "import proof_faithfulness; print(proof_faithfulness.__version__)"
lake --version
```

- [ ] Independently rerun the full engineering gauntlet. Latest agent job `37869456`
  passed the checksummed source overlay with 283 tests, clean Ruff, zero-error Pyright,
  and a green Lean build; this unchecked item is human reproduction, not missing agent
  verification.

```bash
uv run pytest -q
uv run ruff check src tests
uv run pyright
lake build
```

Expected current result: 283 tests and all four commands pass. Treat any failure as a
new blocker and record the exact command, commit, host, module state, exit code, and
diagnostic.

## Manual Lean checks

- [ ] Rerun the exact S2 and S3 fixture suites.

```bash
uv run pytest tests/integration/test_lean_checker.py -q
uv run pytest tests/integration/test_dependency_probe.py -q
```

Expected recorded counts are 17 S2 tests and 13 S3 tests. Confirm that `sorry`, custom
axioms, changed statements, trust bypasses, and multiple code blocks are rejected, and
that deletion distinguishes a used local fact from a decorative one.

- [ ] Manually inspect the trusted checker and Lean audit boundary before trusting it
  for pilot acceptance.

Files to read:

- `src/proof_faithfulness/lean/checker.py`
- `src/proof_faithfulness/lean/sandbox.py`
- `ProofFaithfulness/Audit.lean`
- `tests/integration/test_lean_checker.py`

Questions to answer in your own words:

- Does the checker compile the exact statement rather than a model-modified statement?
- Can any accepted input introduce imports, declarations, `sorry`, custom axioms,
  `unsafe`, `native_decide`, or another trust bypass?
- Is the allowed axiom list correct for the intended paper claim?
- Does a timeout or sandbox failure remain distinguishable from a mathematical failure?

- [ ] Rerun the extended reference compilation in the interactive allocation if the
  host-local diagnostic script is still present. This script is operational tooling,
  not a committed experiment interface.

```bash
reference_check_dir="outputs/reference-proof-checks/human-$(date -u +%Y%m%dT%H%M%SZ)"
.venv/bin/python /mmfs1/home/thuang27/reference_lean_check.py \
  --project-root "$PWD" \
  --output-dir "${reference_check_dir}" \
  --warmup-timeout-seconds 1200 \
  --route-timeout-seconds 600
```

Expected current summary is `total=10 compiles=1 no_sorry_and_compiles=1`. The accepted
route is `036-A`, whose axiom output is `[propext, Quot.sound]`. The complete prior
record is `outputs/reference-proof-checks/37700033/results.json`.

- [ ] Inspect the persisted S3 report for `036-A` from job `37724510`. It reports
  `automation_bypass`, tactic evidence `induction`/`explicit_local`/`automation`, and
  local facts `hcases=true`, `hn11=false`, `hsmall=true`. Decide whether the actual
  `omega` calls are only the arithmetic side-goal uses permitted by the Route-A brief,
  and whether the proof realizes the intended constructive strong-induction strategy.
  This is human interpretation; do not promote the machine label into a rejection.
  Failed or `sorry` routes correctly skipped S3. The checksummed report and exact paths
  are in `docs/T016-REFERENCE-PROOF-REPORT.md`. Also decide whether the controlled
  host-local runner should become reviewed repository tooling.

## Model and generation code review

- [ ] Read the model identity, capability, and execution boundary.

Files to read:

- `src/proof_faithfulness/models/base.py`
- `src/proof_faithfulness/models/config.py`
- `src/proof_faithfulness/models/factory.py`
- `src/proof_faithfulness/models/openai_compat.py`
- `src/proof_faithfulness/models/pipeline.py`
- `configs/experiment/planning-models.yaml`
- `docs/design-docs/model-slate-provisional.md`

Verify that the model ID, revision, backend hash, chat-template hash, sampling recipe,
prompt hash, and sample index all affect request identity. Confirm that local vLLM,
frontier API, and ProofBridge/ProofFlow execution cannot silently masquerade as one
another.

- [ ] Read the generation, resume, and artifact code.

Files to read:

- `src/proof_faithfulness/generation/planning.py`
- `src/proof_faithfulness/generation/run.py`
- `src/proof_faithfulness/generation/artifacts.py`
- `src/proof_faithfulness/generation/locks.py`
- `src/proof_faithfulness/generation/repair.py`
- `src/proof_faithfulness/artifacts.py`

Verify that retries reuse the same request ID, a corrupt or ambiguous terminal artifact
does not cause a duplicate inference, repair outputs remain separate from first
attempts, and resume skips only checksum-verified terminal artifacts.

- [ ] Rerun offline planning and generation tests before any model smoke.

```bash
uv run proof-faithfulness plan --tier 1 --split pilot
uv run proof-faithfulness plan-check --tier 1 --split pilot
uv run pytest tests/unit/test_model_adapters.py \
  tests/unit/test_generation_artifacts.py \
  tests/unit/test_generation_budget.py \
  tests/unit/test_generation_planning.py \
  tests/unit/test_generation_scheduler.py \
  tests/integration/test_generation_harness.py \
  tests/integration/test_generation_repair.py -q
```

Expected planning is 45 requests per proof-conditioned model and 15 per theorem-only
model. The refusal and crash/resume tests must pass without network access.

- [ ] Before downloading weights or allocating a production GPU, freeze the actual
  open-weight and specialized-prover model IDs, immutable revisions, decoding recipes,
  context windows, GPU counts, and vLLM/prover commands. Confirm the Tillicum credit
  attachment and shut-down procedure. Do not infer these values from the provisional
  slate.

## Paid API and billing review

- [ ] Personally review every paid-request boundary.

Files to read:

- `src/proof_faithfulness/models/openai_compat.py`
- `src/proof_faithfulness/generation/budget.py`
- `src/proof_faithfulness/generation/run.py`
- `src/proof_faithfulness/generation/artifacts.py`
- `src/proof_faithfulness/generation/locks.py`
- `tests/unit/test_generation_budget.py`
- `tests/integration/test_generation_harness.py`
- `docs/SERVER-HARNESS-RUNBOOK.md` sections 3, 4, and 6

- [ ] Run the refusal tests yourself while `approvals/` is empty.

```bash
uv run pytest \
  tests/unit/test_generation_budget.py::test_paid_reservation_refuses_when_approvals_directory_is_empty \
  tests/integration/test_generation_harness.py::test_paid_request_without_approval_refuses_before_adapter_call \
  tests/unit/test_model_adapters.py::test_frontier_request_is_blocked_without_budget_permit \
  -q
```

- [ ] Confirm the exact provider, account, available credit, pricing table, key
  environment-variable name, secret-delivery path, and machine-readable approval scope.
  Never paste a secret value into Git, chat, logs, or an approval record.

- [ ] Review the planned request manifest and cost reservation before placing an
  approval. Check exact theorem IDs, conditions, sample indices, model revisions,
  per-request maximum, aggregate maximum, and manifest hash.

- [ ] Run one approved request only after the previous items pass. Inspect its raw
  artifact, checksum, provider request ID, token usage, cost, event log, and resume
  behavior before authorizing a larger smoke slice.

## Evaluation and human annotation review

- [ ] Read the blinding, label import, and statistics code.

Files to read:

- `src/proof_faithfulness/evaluation/blinding.py`
- `src/proof_faithfulness/evaluation/annotations.py`
- `src/proof_faithfulness/evaluation/metrics.py`
- `src/proof_faithfulness/evaluation/signatures.py`
- `tests/unit/test_evaluation.py`
- `tests/integration/test_blinding.py`

- [ ] Confirm that exported packets reveal no model name, condition, prompt text,
  sample index, or indirect identity signal. Confirm that original independent labels
  survive disagreement handling and adjudication unchanged.

- [ ] Freeze the annotation rubric and recruit a second qualified annotator, or
  preregister the documented weaker fallback. Code review does not decide whether a
  proof genuinely follows Route A or Route B.

## Human decisions and feedback questions

Every item below changes the scientific contract, experiment identity, cost exposure,
or interpretation. Record the answer in the active plan's Decision Log before changing
code or running the affected stage.

- [ ] **Eight-GiB memory boundary:** Review jobs 37720527, 37720766, and 37721113 and
  confirm the 8,192 MiB child RLIMIT_AS plus at least 16 GiB SLURM allocation. Confirm
  exact signal/exit codes remain visible and resource_limit is never counted as
  syntax/type invalidity.
- [ ] **Node-local execution policy:** Review the commit-bound LZ4 SquashFS path:
  checksum before copy, checksum after copy, unique mode-0700 /tmp parent, absolute
  unsquashfs, extracted commit/clean checks, signal cleanup, exclusions, and shared
  result persistence. Confirm the runner leaves `ELAN_HOME` unset and verifies
  `lake --version`; jobs `37722631`/`37722668` showed that pointing `ELAN_HOME` at the
  launcher-only directory fails before proof execution. Decide whether the scripts
  become reviewed repository tooling.
- [ ] **Snapshot retention:** Decide cache ownership, retention, quota monitoring, and
  deletion policy for per-commit archives. Never reuse an archive across a digest,
  commit, toolchain, or exclusion change.
- [ ] **S5 integration review:** Inspect 08ceba85, especially verified terminal Lean
  artifacts, theorem-only provenance, crash recovery, and rejection of unchecked text.
- [ ] **Production API intake remains gated:** the approval-bound Meta testing request
  is complete and cannot enter scientific data. Revoke the credential exposed in chat.
  Before any GPT-5.6 Terra or other production-frontier request, identify and review the
  official endpoint, auth variable, wire model ID, pricing/usage schema, billing
  account/region, and retry contract. Deliver only a fresh value through the private
  environment mechanism; an exact matching `approvals/` record remains mandatory.

- [ ] **Timeout implementation review:** The owner decided on one fixed-source Mathlib
  warm-up per batch (1,200-second ceiling) and 600 seconds per fresh candidate after job
  `37715755` repeatedly reached 120 seconds. Manually verify the command, timeout
  classification, and persisted diagnostics; do not reinterpret old timeouts as theorem
  failures or treat this unchecked review item as Gate S approval.
- [ ] **Import policy:** Should pilot statements keep the umbrella `import Mathlib`, or
  use minimal candidate-specific imports? Minimal imports may improve performance and
  tighten dependencies, but changing them changes import hashes and request identity.
- [ ] **Reference-proof disposition:** Should the nine non-compiling routes be replaced,
  repaired by a human, or cause their candidate pair to be removed? Current drafts
  cannot satisfy Gate S.
- [ ] **Reference runner ownership:** Should the host-local diagnostic runner be
  promoted into reviewed repository tooling, or remain disposable operational code?
- [ ] **S3 metric:** Freeze explicit-step utilization versus a fuller dependency graph,
  and specify how automation-only and ambiguous cases are coded.
- [ ] **Model slate:** Freeze exact frontier, open-weight, specialized prover, and
  pipeline models, immutable revisions, hardware, decoding, and prompt templates.
- [ ] **API authorization:** Freeze provider, maximum approved dollars, request count,
  approval scope, pricing assumptions, retry policy, and who may authorize a top-up.
- [ ] **Analysis:** Freeze the primary estimand, sample pairing, ambiguity handling,
  theorem-clustered uncertainty method, agreement threshold, and disputed-pair rule
  before core results are inspected.
- [ ] **Annotation:** Freeze the rubric, calibration pass, annotator staffing,
  adjudication policy, and any LLM-judge role.
- [ ] **Artifacts and release:** Fill the human section of
  `coding-standard/PROJECT_ARTIFACTS.md`, choose LICENSE/CITATION metadata, decide how to
  publish the local commits after `origin/main`, and approve final release scope.

## Known submitted-proof outcomes

These are observations, not approval judgments. Full diagnostics are in
`outputs/reference-proof-checks/37700033/results.json`.

| Candidate | Route A | Route B |
|---|---|---|
| 001 | Compile error: `omega`/unavailable constants | Compile error: `Int`/`Nat` mismatch |
| 033 | Compile error plus `sorry`; divisibility direction | Compile error in `Nat.ofDigits` rewrite |
| 036 | Compiles; allowed axioms only | Compile error: missing `DecidablePred P` |
| 040 | Compile errors in rational/log argument | Compile errors in rational/log/coprime argument |
| 041 | Compile errors plus two `sorry` placeholders | Compile errors plus one `sorry` placeholder |

## Completion rule

This checklist is complete only when the owner has recorded each applicable decision,
rerun the relevant commands on the intended host, reviewed the load-bearing code and
artifacts, and explicitly approved the corresponding gate. Agents may add evidence or
questions, but must never check these boxes or infer approval from silence.
