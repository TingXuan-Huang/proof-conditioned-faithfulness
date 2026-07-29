# Cluster Experiment Incident And Recovery Log

**Project:** proof-conditioned-faithfulness  
**Hosts:** UW Hyak Klone and planned Tillicum execution  
**Coverage:** 2026-07-24 through 2026-07-29  
**Last updated:** 2026-07-29

This is the durable troubleshooting record for engineering and real-backend
calibration. It records failed approaches as well as fixes so a future operator does
not repeat them. It is not an experiment-results document and does not approve a human
gate.

## How To Classify A Failure

Always determine which layer failed before interpreting the result:

1. **Infrastructure:** scheduler, filesystem, container, module, network, or GPU job
   failed before the harness could run.
2. **Harness:** request identity, artifact, retry, checker, or launcher code behaved
   incorrectly.
3. **Backend compatibility:** a model or external pipeline could not satisfy its
   documented execution contract.
4. **Model output:** generation completed, but the returned Lean text was invalid.
5. **Human gate:** code cannot decide strategy faithfulness, final slate membership,
   spending authorization, or statistical policy.

Only category 4 is evidence about a generated proof. Timeouts, signals, failed imports,
missing executables, and pipeline crashes must never be reported as theorem invalidity.

## Known-Good Checkpoint

The final offline verification was SLURM job `37869456`:

```text
Mathlib warm-up: passed in 424.831 seconds
pytest: 283 passed in 51.69 seconds
Ruff: passed
Pyright: 0 errors, 0 warnings, 0 informations
lake build: passed with one existing unused-variable warning
```

The job verified the immutable environment snapshot for commit `5ae84e759...` and a
checksummed source overlay for `b7eb71fa...`. Launcher-only commit `15fe536` was then
checked with `bash -n` and a numeric GPU-memory regression. Seven focused paid-request,
preflight, ambiguous-retry, kill/resume, and refusal tests passed in 0.44 seconds. An
artifact audit verified 114 SHA-256 sidecars with zero mismatches.

Real-backend results and exact revisions are in
`docs/REAL-BACKEND-COMPATIBILITY-REPORT.md`.

## Incident Index

### I001 - Mathlib cache download failed TLS validation

- **Layer:** infrastructure/bootstrap.
- **Symptom:** the Mathlib cache could not be retrieved even though outbound network
  access worked.
- **Cause:** the process did not use the cluster CA bundle.
- **Fix:** set `SSL_CERT_FILE=/etc/pki/tls/certs/ca-bundle.crt`; the retry downloaded all
  5,826 cache artifacts.
- **Prevention:** export the CA path in controlled setup jobs and verify the cache before
  compiling candidates.

### I002 - Pyright Node runtime could not load `libatomic.so.1`

- **Layer:** infrastructure/runtime.
- **Symptom:** Pyright failed before type analysis with a shared-library loader error.
- **Cause:** the login/compute environment lacked the GCC runtime on its library path.
- **Fix:** `module load gcc/12.3.0` before Pyright. Node-local job `37868405` reproduced
  the failure after 281 passing tests; final job `37869456` passed Pyright after loading
  the module.
- **Prevention:** every verification launcher loads GCC explicitly instead of relying on
  an interactive shell.

### I003 - Cold `import Mathlib` exceeded proof timeouts

- **Layer:** infrastructure/Lean startup.
- **Evidence:** jobs `37696157`, `37697588`, `37699980`, `37700033`, and `37715755`.
- **Symptom:** many unrelated submitted proofs appeared to time out at the same boundary.
- **Cause:** each fresh process paid the full umbrella-import and GPFS metadata cost.
  The initial 120-second boundary measured startup, not proof elaboration.
- **Fix:** separate a fixed-source warm-up with a 1,200-second ceiling from a 600-second
  per-candidate check. Diagnostic job `37700033` resolved all seven timeouts into one
  compiling proof and nine concrete Lean errors.
- **Prevention:** warm once on the same node before candidate checks. Preserve timeout as
  an operational category; never translate it to syntax/type invalidity.

### I004 - Shared GPFS stalled despite low CPU and I/O use

- **Layer:** infrastructure/storage.
- **Evidence:** job `37717888` ran 20:15, used 3.597 CPU seconds, read 86.47 MB, and
  timed out at 1,200.014 seconds.
- **Symptom:** Mathlib warm-up and even bounded Lake metadata work made little progress.
- **Cause:** shared-filesystem metadata latency, not a missing `.olean` file.
- **Fix:** package the commit and environment as a checksummed LZ4 SquashFS image, copy
  it to a private node-local `/tmp`, verify it again, and execute there.
- **Prevention:** use the node-local path for full Mathlib checks and write only durable
  results back to shared `outputs/`.

### I005 - Four-GiB Lean address-space limit killed valid work

- **Layer:** harness resource boundary.
- **Evidence:** `37720527` failed; unlimited control `37720766` and 8-GiB control
  `37721113` passed at about 4,072,000 KiB maximum RSS.
- **Symptom:** the child exited by signal/resource failure after node-local staging.
- **Cause:** the former 4,096-MiB `RLIMIT_AS` was below real Mathlib process demand.
- **Fix:** raise the bounded child limit to 8,192 MiB and request at least 16 GiB from
  SLURM (`6a65e5e`).
- **Prevention:** preserve exact signal and exit code. A resource signal is not evidence
  that the theorem is false or the proof text is invalid.

### I006 - SquashFS compression was unsupported

- **Layer:** infrastructure/staging.
- **Evidence:** job `37719618` failed in three seconds.
- **Symptom:** `mksquashfs` rejected the requested zstd compressor.
- **Cause:** the installed SquashFS tools did not include zstd support.
- **Fix:** use LZ4. The first full archive took 25:17; later snapshot job `37722524`
  completed in 5:37.
- **Prevention:** probe supported compressors before a long archive build.

### I007 - Restricted `PATH` hid `unsquashfs`

- **Layer:** infrastructure/launcher.
- **Evidence:** job `37719638` exited 127.
- **Symptom:** extraction failed before project verification.
- **Cause:** the controlled job `PATH` omitted the system location.
- **Fix:** call `/usr/sbin/unsquashfs` explicitly.
- **Prevention:** use absolute paths for cluster utilities that are outside the minimal
  job `PATH`.

### I008 - Pre-created extraction directory made `unsquashfs` write zero files

- **Layer:** launcher bug.
- **Evidence:** jobs `37720472`, `37865829`, `37865830`, and `37865831`.
- **Symptom:** `dir_scan: failed to make directory ... because File exists`, followed by
  `snapshot does not contain the project root`.
- **Cause:** the launcher created the destination directory before passing it to
  `unsquashfs -d`.
- **Fix:** create only the private parent and let `unsquashfs` create the destination
  (`39a63fe`).
- **Prevention:** run a real extraction smoke, not only `bash -n`, whenever staging code
  changes.

### I009 - Launcher invoked a nonexistent package `__main__`

- **Layer:** launcher bug.
- **Evidence:** job `37720494`.
- **Symptom:** the environment extracted, then Python could not execute the package as a
  module.
- **Cause:** the package exposes a console entrypoint, not the assumed `__main__`.
- **Fix:** invoke the installed `proof-faithfulness` entrypoint or the explicit Typer app.
- **Prevention:** verify the exact command inside the immutable snapshot before
  submission.

### I010 - `ELAN_HOME` pointed at a launcher-only directory

- **Layer:** launcher configuration.
- **Evidence:** T016 jobs `37722631` and `37722668` exited before proof execution;
  corrected job `37724510` passed.
- **Symptom:** Elan searched for a nonexistent Lean toolchain.
- **Cause:** the scrubbed directory contained the Elan launcher but not a complete
  `ELAN_HOME` tree.
- **Fix:** leave `ELAN_HOME` unset and put the verified launcher on `PATH`.
- **Prevention:** run `lake --version` before trusted work and do not infer a toolchain
  home from the launcher path.

### I011 - Submitted Lean proofs failed for data-level reasons

- **Layer:** model/human-supplied proof data.
- **Evidence:** `outputs/reference-proof-checks/37700033/results.json` and
  `docs/T016-REFERENCE-PROOF-REPORT.md`.
- **Symptom:** only `036-A` compiled; nine routes had Lean errors; `033-A`, `041-A`, and
  `041-B` contained `sorry`.
- **Cause:** proof-specific theorem, type, divisibility, rational/log, and placeholder
  errors after operational timeouts were removed.
- **Disposition:** record diagnostics and skip S3 for failed routes. Do not repair them
  automatically. Humans decide replacement, repair, and Gate S status.

### I012 - A stricter model schema exposed a stale test fixture

- **Layer:** test/code integration.
- **Symptom:** a full suite passed 246 tests and failed one fixture after
  `context_window` became required.
- **Cause:** the fixture did not track the updated model contract.
- **Fix:** add the required field and pass its targeted regression.
- **Prevention:** centralize valid model fixtures and run the full suite after schema
  changes.

### I013 - Pyright found a `Decimal` mismatch

- **Layer:** static typing.
- **Symptom:** Pyright reported one error after the generation/budget implementation.
- **Cause:** inconsistent numeric typing at a cost-accounting boundary.
- **Fix:** preserve `Decimal` through the boundary; Pyright then passed.
- **Prevention:** never mix float and `Decimal` in authorization or spend accounting.

### I014 - Code reviews found trust, spend, provenance, and blinding defects

- **Layer:** harness correctness.
- **Findings fixed:** trusted-report truncation/spoof ambiguity; source-name collisions
  in local-fact utilization; cross-run duplicate paid IDs; caller-overridable ceilings;
  approval/lock/interrupt races; incomplete raw failure evidence; theorem-only and
  evaluation provenance gaps; blinding leaks; agreement edge cases; and crash recovery.
- **Fixes:** S2/S3, S4, and S5 regression work through commits `f446236`, `627fcd6`,
  `08ceba8`, and their follow-ups.
- **Deferred:** deep reviews T017-T020 remain open. Prototype review does not replace
  publication-level review.

### I015 - Checkpoint model server returned repeated 503/readiness failures

- **Layer:** model serving / preemptible infrastructure.
- **Evidence:** direct jobs `37851878` and `37852006` failed before readiness; logs show
  repeated HTTP 503 or server exit.
- **Cause:** early vLLM bring-up and checkpoint-resource instability; no terminal model
  response was persisted.
- **Fix:** isolate vLLM cache/environment, verify the server PID, poll `/v1/models`, and
  assert the expected model identity before generation (`dd0a0a0`, `5ae84e7`). Later
  jobs passed.
- **Prevention:** use checkpoint GPUs only for free calibration. Never run paid API work
  in a preemptible allocation.

### I016 - Slow shared `git status` wasted a loaded GPU model

- **Layer:** provenance check / shared filesystem.
- **Evidence:** GPT job `37854616` loaded, then the harness's 10-second
  `git status --porcelain` timed out.
- **Symptom:** `HarnessError: Unable to resolve the harness Git identity` after costly
  model startup.
- **Cause:** provenance was resolved from the shared worktree after model loading.
- **Fix:** execute from an immutable clean snapshot and pass the already verified commit
  to the harness (`e8f8b90` and later launchers).
- **Prevention:** verify Git identity and cleanliness before allocating/loading a GPU;
  avoid shared-GPFS Git commands on the hot path.

### I017 - A dirty worktree correctly blocked generation

- **Layer:** safety/provenance.
- **Symptom:** manual Meta calibration raised `HarnessError: Generation requires a clean
  Git worktree`.
- **Cause:** uncommitted engineering/documentation changes made the harness identity
  ambiguous.
- **Resolution:** review and commit the changes, then rerun. Do not weaken the default
  clean-tree rule for production.
- **Prevention:** run `git status --short` before planning and before entering a paid or
  GPU allocation. Use an explicit dirty override only for clearly labeled disposable
  development, never scientific output.

### I018 - Calibration reentry rejected an already completed response

- **Layer:** harness resume bug.
- **Symptom:** after requeue/reentry, the first pass correctly skipped a verified
  terminal artifact but calibration expected exactly one newly processed response.
- **Cause:** the calibration wrapper was stricter than the underlying resume contract.
- **Fix:** accept either `processed=1` or verified `skipped=1` on entry, and still require
  the second pass to be a no-op (`5ae84e7`).
- **Prevention:** test reentry after response persistence, not only immediate in-process
  resume.

### I019 - Reassessment risked overwriting original diagnostics

- **Layer:** artifact provenance.
- **Symptom:** an early node-local reassessment design wrote fixed-name Lean/assessment
  outputs into the original generation run.
- **Risk:** assessor versions and original timeout evidence could be mixed.
- **Fix:** create immutable child runs with checksummed copied requests/responses and a
  `reassessment-provenance.json`. GPT and Qwen reassessments now use child namespaces.
- **Prevention:** never overwrite a source run to change a downstream assessment.

### I020 - Generic `python` was absent inside `--cleanenv` container

- **Layer:** container launcher.
- **Evidence:** Qwen job `37868404` extracted successfully, then failed with
  `"python": executable file not found in $PATH`.
- **Cause:** `apptainer exec --cleanenv` removed host assumptions and the image exposed
  a versioned interpreter.
- **Fix:** invoke `/usr/bin/python3.12` explicitly (`2008175`).
- **Prevention:** inspect and pin interpreter paths inside each container image.

### I021 - DeepSeek tokenizer dispatch produced byte-marker glyphs

- **Layer:** backend compatibility.
- **Evidence:** old run `37854617` generated text containing literal tokenizer markers
  and was classified `extraction_invalid`.
- **Cause:** the model's tokenizer class did not dispatch correctly under Transformers
  5 in the serving image.
- **Fix:** build and checksum a pretrained-fast tokenizer overlay without changing the
  pinned model-weight revision (`ef6f3d9`). Corrected run `37868477` decoded normally.
- **Prevention:** perform a tokenizer encode/decode smoke before allocating the full
  model and record tokenizer identity separately from weight identity.

### I022 - Downstream Lean assessment began from a cold cache

- **Layer:** launcher/Lean staging.
- **Evidence:** initial GPT child reassessment timed out; same-node warm-up followed by
  `calibration-gpt-oss-120b-reassess-warm-37868405` passed Lean, dependency, and
  evaluation.
- **Cause:** local model generation succeeded, but the launcher began assessment before
  warming Mathlib on that node.
- **Fix:** call the trusted `warm_mathlib_cache` before assessment (`b7eb71f`).
- **Prevention:** generation success and Lean readiness are separate checks; warm Lean
  explicitly even when model serving is already warm.

### I023 - Scheduler association limits delayed parallel work

- **Layer:** scheduler capacity.
- **Evidence:** several jobs reported `AssocGrpCpuLimit`; others waited on `Priority`.
- **Symptom:** GPU and CPU jobs remained pending even when the requested device appeared
  available.
- **Cause:** account-level CPU/QoS limits, not necessarily GPU scarcity.
- **Resolution:** use `squeue`, `sacct`, and `squeue --start`; avoid submitting many
  CPU-heavy launchers under the same association; place dependencies intentionally.
- **Prevention:** choose L40/A100 for models that fit instead of queuing every model on
  H200. Give long jobs an estimated wait rather than repeatedly resubmitting them.

### I024 - Meta approval was absent or did not match the run

- **Layer:** paid-request safeguard operating as designed.
- **Symptom:** `MissingApprovalError` for run ID and scope.
- **Cause:** `approvals/` did not contain exactly one record binding the current run ID,
  request-manifest SHA-256, request count, scope, and maximum dollars.
- **Fix:** plan first, compute the request-file hash/count, review it, and create the
  machine-readable approval. The later approval allowed one request with a `$5.50`
  ceiling and actual harness-settled spend `$0.008082`.
- **Prevention:** approval is intentionally not a CLI convenience flag. Never bypass it.

### I025 - Missing API secret was detected too late in the attempt lifecycle

- **Layer:** paid transport harness.
- **Symptom:** after approval and clean-tree checks, the run raised
  `MissingSecretError: META_MODEL_API_KEY`.
- **Cause:** the shell variable was set but not exported in one manual attempt, and the
  adapter originally checked it after attempt bookkeeping began.
- **Fix:** export the variable for the child process; move endpoint, identity, sampling,
  and secret preflight ahead of the transport-attempt boundary while keeping approval
  as the first gate (`d2c2e13`).
- **Prevention:** use `test -n "${META_MODEL_API_KEY:-}"` without printing the value,
  export it, and ensure missing-secret tests prove no network call or ambiguous paid
  attempt occurred.

### I026 - An API key value was pasted into chat

- **Layer:** secret handling / human operation.
- **Risk:** chat exposure means the credential should be considered compromised even
  though exact-prefix scans found no value in Git or calibration artifacts.
- **Resolution:** clear the current shell with `unset META_MODEL_API_KEY` and revoke the
  key in the Meta dashboard. Create a fresh key only for a later separately approved
  request.
- **Prevention:** use silent terminal input or a mode-0600 file outside the repository;
  never paste secret values into chat, logs, commands, approvals, or documentation.

### I027 - Meta returned a tiny visible proof after many reasoning tokens

- **Layer:** model output, not parser loss.
- **Evidence:** the raw payload recorded 1,869 output tokens, including provider-reported
  reasoning tokens, while visible text was `:= Nat.add_zero n`.
- **Symptom:** the result looked like no proof was generated.
- **Cause:** the provider returned a short visible answer after hidden/reasoning output.
  The harness persisted the verbatim raw response and extracted the visible field
  correctly.
- **Disposition:** trusted Lean classified the extra `:=` as `syntax_invalid`. Do not
  repair the output. Use a longer calibration theorem only under a new approved request
  identity.

### I028 - GPU peak memory was compared as text

- **Layer:** measurement-integrity bug.
- **Symptom:** Qwen H200 recorded 791 MiB despite raw samples reaching 130,983 MiB;
  DeepSeek recorded 457 MiB despite samples reaching 41,781 MiB.
- **Cause:** awk compared string-valued fields lexicographically.
- **Fix:** coerce each field numerically before comparison (`15fe536`). Preserve the
  original runtime artifact and add checksummed `runtime-correction.json` records.
- **Prevention:** test metric reducers with values whose digit lengths differ and audit
  derived metrics against raw samples.

### I029 - Qwen, DeepSeek, and Meta generated invalid Lean text

- **Layer:** model output.
- **Evidence:** Qwen H200 returned `Nat.add_zero` without `n` (`type_invalid`);
  corrected DeepSeek returned multiple code blocks (`multiple_blocks`); Meta returned an
  extra `:=` (`syntax_invalid`).
- **Disposition:** generation, persistence, resume, checking, and classification passed.
  Dependency/evaluation stages correctly skipped after trusted Lean failure. Backend
  compatibility does not require the one calibration sample to compile.
- **Human question:** decide whether DeepSeek needs a prompt/output-contract change.

### I030 - ProofBridge public release was not runnable

- **Layer:** external pipeline compatibility.
- **Evidence:** `calibration-proofbridge-20260728` contains checksummed raw failure data.
- **Symptom:** no generation entrypoint or checkpoint could be invoked.
- **Cause:** pinned upstream commit `465d2a03...` does not publish a documented runnable
  inference entrypoint or trained checkpoint.
- **Disposition:** infeasible from the public release. Human review decides whether to
  obtain private assets, patch/replace it, or remove the category with disclosure.

### I031 - ProofFlow failed after successful underlying generation

- **Layer:** external pipeline compatibility.
- **Evidence:** job `37868402` and run `calibration-proofflow-qwen3-32b-37868402`.
- **Symptom:** pinned Qwen loaded and returned `Nat.add_zero n`; ProofFlow then raised
  `RuntimeError: Unexpected error in build_proof_graph`.
- **Cause:** the minimal calibration proof was incompatible with upstream proof-graph
  construction at commit `97f1b7be...`.
- **Disposition:** raw checksummed diagnostics are retained. No terminal
  `GenerationResponse` exists, so downstream/resume could not pass. Do not silently
  claim pipeline support.

### I032 - Direct final tests failed for sandbox/cache reasons

- **Layer:** execution environment.
- **Symptom:** `uv run pytest` could not create a temporary file in the configured
  scrubbed uv cache under sandbox permissions. A direct `.venv` retry then stalled at
  shared-GPFS Lean access.
- **Fix:** stop the non-representative direct run and submit final node-local job
  `37869456`, which passed the complete gauntlet.
- **Prevention:** set a writable `UV_CACHE_DIR` when sandboxed, but still use node-local
  staging for full Mathlib tests.

### I033 - Git publication failed without usable server credentials

- **Layer:** repository operations.
- **Symptom:** HTTPS push could not read a username; `gh` was unavailable; the tested
  SSH route was denied; later policy checks rejected mutation of an unverified external
  default branch before network access.
- **Resolution:** preserve clean local commits and do not change credentials or remotes.
  As of commit `f44813d`, local `main` was 32 commits ahead of the locally known
  `origin/main` and zero behind. This is not proof the remote has not changed since the
  last fetch.
- **Prevention:** the human should fetch, inspect divergence, review the full diff and
  secret scan, then push using their normal authenticated session.

## Repeated Lessons

1. **Warm and stage Lean separately from generation.** A successful GPU request says
   nothing about Mathlib readiness.
2. **Do provenance work before expensive allocation.** Verify commit, worktree,
   snapshot digest, model revision, tokenizer, container, and approval before loading a
   model.
3. **Preserve failures.** Raw provider/pipeline diagnostics and model text are evidence;
   do not overwrite or repair them.
4. **Use child runs for reinterpretation.** New checker versions produce new assessment
   artifacts, not edits to the original run.
5. **Treat scheduler state literally.** Pending, preempted, failed, and completed are
   operational states, not model-quality outcomes.
6. **Keep paid requests fail-closed.** Approval, manifest binding, preflight, durable
   attempt state, cost settlement, and no-op resume all matter.
7. **Audit raw measurements.** Derived memory, token, cost, and latency values require a
   sanity check against their raw evidence.

## Recovery Checklist For The Next Operator

```bash
cd /mmfs1/gscratch/stf/thuang27/proof-conditioned-faithfulness
module load gcc/12.3.0
git rev-parse HEAD
git status --short
lake --version
```

- Confirm the worktree is clean before generation.
- Do not run `uv lock` on the server; use the frozen lock.
- Verify snapshot, container, model, tokenizer, prompt, request manifest, and approval
  SHA-256 values before allocating a GPU or issuing a paid request.
- Use node-local SquashFS extraction without pre-creating its destination.
- Leave `ELAN_HOME` unset unless a complete alternate toolchain is verified.
- Invoke `/usr/bin/python3.12` inside the vLLM container.
- Warm Mathlib before S2/S3/evaluation assessment.
- Check the server PID and expected `/v1/models` identity before generation.
- Parse GPU-memory samples numerically and retain the raw CSV.
- Use L40/A100 where the model fits; reserve H200 for models that require it.
- Never use a preemptible job for a paid API request.
- After using an interactive API secret, `unset` it; revoke any value exposed in chat.
- Stop before pilot/core unless the human has reviewed the readiness report and closed
  the required gates.

## Still Unresolved Or Human-Owned

- Final model and proof-pipeline slate (T022).
- DeepSeek multi-block prompt/output-contract decision.
- ProofBridge/ProofFlow replacement, patch, or exclusion decision.
- Gate P and Gate S, including disposition of nine failed reference routes.
- S3 utilization definition and post-pilot estimand/statistical freeze (T006).
- Second-annotator onboarding, rubric calibration, and independence confirmation (T007).
- Tillicum credit attachment, direct egress, production secret delivery, and retention
  policy (T008).
- Fresh GPT-5.6 Terra credential and separately approved smoke, if selected (T012).
- Deferred deep reviews T017-T020.
- LICENSE, CITATION, artifact ownership, and authenticated Git publication.
