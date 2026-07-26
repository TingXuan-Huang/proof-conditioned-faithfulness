# SERVER-HARNESS-RUNBOOK.md — Operating the Experiment on the SLURM Cluster

This is the control-plane companion to docs/plans/active/PLAN.md (which says WHAT to
build and in what order; this file says HOW to operate it: setup, jobs, run states,
locks, budgets, logs, recovery). The SLURM host facts discovered under T008 are recorded
in §1; only Tillicum account-specific allocation/billing, direct compute-node egress,
secret delivery, and the exact frontier provider remain open. Everything here is written
for a stateless agent arriving with only a fresh clone.

## 1. Server facts (fill in at environment discovery, PLAN.md 2.1)

    canonical host:   Tillicum (University of Washington GPU cluster), SLURM
    development host: Klone (University of Washington Hyak HPC), SLURM
    compute budget:   $250 in cluster credits (2026-07-24) — GPU jobs burn this;
                      keep dev on CPU/login nodes + mock adapters; GPUs only for
                      real batches, serve → run → shut down
    secret delivery:  waiting on human (see §3); do not infer a mechanism
    API budget:       $20 credit on the frontier provider (exact provider name to be
                      confirmed by the user; enough for pilot + cheap-provider core;
                      top-up decision deferred until post-pilot cost data)
    test cluster:     Klone (UW Hyak) — DEV/TEST host (user decision 2026-07-24,
                      superseding the earlier reserve-only policy). Split of duties:
                      - Klone: environment bring-up rehearsal, S1-S5 development and
                        tests, Lean toolchain + statement checks during development,
                        mock runs, first vLLM serving trials. Free/idle capacity;
                        preemption is fine for all of this.
                      - Tillicum: THE canonical experiment host. Everything that
                        enters the paper — slate smoke (2.4), pilot, core, and every
                        artifact referenced by a freeze manifest — runs here and
                        only here. One environment in the manifest.
                      Run 2.1 discovery on BOTH; keep two facts blocks. The Lean
                      toolchain pin and uv.lock make the two environments match by
                      construction; verify with the same smoke fixtures on each.
                      PAID API jobs never run on a preemptible partition anywhere.
                      Cost escape hatch unchanged: if Tillicum credits run low
                      post-2.4, CPU-only Lean checking (and, last resort, local
                      inference) may move to Klone ckpt — recorded per-run in the
                      manifest if it ever happens.

### 1a. Klone facts (2.1 discovery, 2026-07-24)

    scheduler:        SLURM               account: stf
    allocated CPU:    compute (680 CPUs), compute-hugemem (120), cpu-g2 (640),
                      cpu-g2-mem2x (192); account totals, not current free capacity
    allocated GPUs:   gpu-l40 (8 total), gpu-l40s (10 total); both 48 GB GDDR6;
                      each physical node has 8 GPUs; checkpoint access may expose
                      idle GPUs outside the allocation but is preemptible
    QoS:              normal; checkpoint QoS ckpt, ckpt-gpu, ckpt-scav
    storage:          GPFS project path /gscratch/stf; 60 TiB / 60,000,000 files
                      group quota, 57,993 GB / 47,768,186 files used at the
                      2026-07-25 probe; this user owns 760 GB / 726,770 files
    purge/backup:     no timed purge is documented for project gscratch, which is
                      NOT backed up or archival; /gscratch/scrubbed alone
                      auto-deletes files inactive for 21 days (10 TB per-user
                      limit, not guaranteed)
    network policy:   outbound works from compute nodes (probe job 37641229)
    containers:       Apptainer 1.5.2     secret delivery: waiting on human (§3)
    required module:  gcc/12.3.0 (Pyright Node runtime needs libatomic.so.1)
    cache TLS:        SSL_CERT_FILE=/etc/pki/tls/certs/ca-bundle.crt
    Lean cold import: a full `import Mathlib` from GPFS exceeded 600 s on a cold
                      cpu-g2 node in job 37696157. After repeated/same-node warming,
                      diagnostic job 37700033 used 113 s for its explicit warm-up and
                      roughly 94-120 s per route. Do not infer theorem invalidity from
                      a cold-import timeout. After job 37715755 repeatedly reached the
                      old 120 s boundary, the owner set normative S2 to a fixed-source
                      warm-up (1,200 s separate ceiling) and 600 s per fresh candidate.
                      Import narrowing remains a separate identity-changing decision.
    GPFS diagnosis:   job 37717888 timed out at 1,200.014 s after 20:15 elapsed while
                      using only 3.597 CPU seconds and reading 86.47 MB. Mathlib.olean
                      exists; compiled Mathlib is 4.8 GB/about 28,435 entries. Treat
                      this as shared-filesystem waiting, never theorem invalidity.
    memory evidence:  node-local 4 GiB job 37720527 exited 139 after 73.87 s. Unlimited
                      job 37720766 exited 0 in 1:40.12 at 4,071,788 KiB maximum RSS.
                      Bounded 8 GiB job 37721113 exited 0 in 3:18.66 at 4,072,176 KiB.
                      Normative RLIMIT_AS is 8,192 MiB; request at least 16 GiB from
                      SLURM. Preserve exact signal/exit code as resource_limit.
                      This is an operational classification: inspect the raw exit and
                      diagnostics because a signal alone does not prove RAM exhaustion.
    local snapshot:  LZ4 SquashFS build 37719636 completed in 25:17. Each Lean job
                      verifies archive checksum, copies and verifies it locally,
                      extracts into unique private /tmp, verifies git commit and clean
                      state, and has signal cleanup. There is no unverified GPFS
                      fallback. outputs/ and approvals/ are excluded; persistent
                      artifacts write back to the original shared outputs/ tree.
                      Commit-a65e9d8 build 37722524 completed in 5:37. Immutable
                      gauntlet 37722531 completed in 4:01: warm-up 114.798 s, lake
                      build green, 271 pytest tests, Ruff clean, Pyright 0, and exact
                      S4 plan/plan-check green. Trusted 036-A job 37724510 completed
                      warm-up/S2/S3 in 1:39 and verified all artifact sidecars.
    staging errors:   37719618 used unsupported zstd; 37719638 lost unsquashfs from
                      restricted PATH; 37720472 pre-created the extraction target;
                      37720494 invoked a nonexistent package __main__. All were
                      diagnosed and corrected before the memory experiments.
                      T016 jobs 37722631 and 37722668 then set ELAN_HOME to the
                      scrubbed launcher-only directory and failed before candidate
                      execution. Leave ELAN_HOME unset to use the verified installed
                      toolchain; corrected job 37724510 passed.

### 1b. Tillicum facts (public policy discovery, 2026-07-25)

    scheduler:        SLURM; access is QoS-based, not partition-based; no checkpoint
    GPUs:             192 NVIDIA H200 SXM, 141 GB each; 24 nodes, 8 GPUs per node;
                      every compute job must request >=1 GPU
    per-GPU bundle:   8 CPU cores and approximately 200 GB system RAM
    standard QoS:     normal (24 h, 16 GPUs/job, 48 concurrent GPUs/user),
                      debug (1 h, 1 GPU, 1 job), interactive (8 h, 2 GPUs, 2 jobs)
    special QoS:      long (7 d, 16 GPUs/job), wide (24 h), urgent (3 d,
                      64 GPUs/job); explicit access required; shared limits apply
    billing policy:   $0.90 per raw GPU-hour; urgent is billed at 2x; the user's
                      stated $250 credit exists, but its account attachment,
                      expiration, and enforced budget are waiting on human/account
                      access and must be checked with hyakusage before a real job
    storage policy:   GPFS; 10 GB home and 1 TB project/lab storage with daily
                      snapshots (7 retained); scrubbed allows up to 100 TB/user and
                      purges files after 60 days of inactivity
    containers:       Apptainer; bind /gpfs; hierarchical Lmod modules
    network policy:   waiting on direct compute-node probe
    secret delivery:  waiting on human (see §3)
    direct discovery: tillicum.hyak.uw.edu is reachable, but non-interactive login
                      correctly refused on 2026-07-25 because Tillicum requires 2FA;
                      account-specific sinfo/sacctmgr/hyakstorage/hyakusage probes
                      therefore remain pending

Sources for these facts are the 2026-07-25 outputs of `sinfo`,
`scontrol show partition`, `sacctmgr show qos`, `hyakalloc`, and `hyakstorage` on
Klone, plus the current UW Research Computing Tillicum
[architecture](https://hyak.uw.edu/docs/systems/tillicum/architecture),
[scheduling](https://hyak.uw.edu/docs/systems/tillicum/scheduling-jobs), and
[storage](https://hyak.uw.edu/docs/systems/tillicum/storage) documentation. A
two-minute Klone checkpoint `nvidia-smi` probe
(job 37665822) never started and was cancelled with zero runtime; VRAM is taken
from the cluster's official GPU inventory instead.

If compute nodes have no outbound network, API generation jobs must run on a login/DTN
node or via the cluster's designated proxy — discover this BEFORE any paid batch.

## 2. One-time setup from a clean clone (idempotent)

Working directory: the user-designated path on the cluster (never a scratch dir that
gets purged mid-experiment — check quota/purge policy first).

    git clone <remote-url> proof-conditioned-faithfulness
    cd proof-conditioned-faithfulness
    module load gcc/12.3.0                  # libatomic.so.1 for Pyright's Node runtime
    uv sync --frozen --all-extras            # exact versions from committed uv.lock
    uv run python -c "import proof_faithfulness; print(proof_faithfulness.__version__)"
                                             # expect: 0.1.0

    # Lean toolchain (pinned; PLAN.md 2.2):
    curl -sSf https://elan.lean-lang.org/elan-init.sh | sh -s -- -y   # if elan absent
    lake --version                           # expect the lean-toolchain pinned version
    SSL_CERT_FILE=/etc/pki/tls/certs/ca-bundle.crt lake exe cache get
                                             # Mathlib cache for the pinned commit
    lake build                               # expect: no errors, cache-served

    uv run proof-faithfulness env lean-warmup \
      --project-root . --timeout-seconds 1200
                                             # fixed source; no candidate/model output

### 2a. Klone node-local Lean staging

Full-Mathlib checks on Klone must stage a commit-bound LZ4 SquashFS image. The current
archive builder and runner are operational tools, not experiment approval. A runner
must implement every step below and fail closed at the first mismatch:

1. Require a clean source commit and name the archive with the full commit hash.
2. Build with compressor lz4, never unsupported zstd, and exclude outputs/, approvals/,
   secrets, and transient caches.
3. Store a SHA-256 sidecar beside the archive. Verify the shared archive before copying,
   then verify the local copy against the same digest before extraction.
4. Create a unique job-owned parent under /tmp with mode 0700. Do not pre-create the
   final unsquashfs destination. Install EXIT, TERM, INT, and HUP cleanup traps.
5. Use absolute /usr/sbin/unsquashfs under restricted SLURM environments. Verify the
   extracted git commit and clean state before running any local code.
6. Export PYTHONPATH from the extraction and call the installed proof-faithfulness
   entry point. Do not rely on a package __main__ module.
7. Put the verified Elan launcher on PATH, leave `ELAN_HOME` unset, and require
   `lake --version` to report Lean 4.15.0 before warm-up. Setting `ELAN_HOME` to the
   launcher-only scrubbed directory is invalid. An alternative `ELAN_HOME` is allowed
   only after verifying it contains the pinned toolchain binaries.
8. Keep child RLIMIT_AS at 8,192 MiB, retain the 1,200/600-second limits, request at
   least 16 GiB SLURM memory, and persist results only to original shared outputs/.

Representative checks:

    test -n "${SLURM_JOB_ID:?}"
    install -d -m 0700 "/tmp/${USER}/proof-faithfulness-${SLURM_JOB_ID}"
    sha256sum -c "${ARCHIVE}.sha256"
    cp "${ARCHIVE}" "${LOCAL_ARCHIVE}"
    printf '%s  %s\n' "${EXPECTED_SHA256}" "${LOCAL_ARCHIVE}" > "${LOCAL_SHA_FILE}"
    sha256sum -c "${LOCAL_SHA_FILE}"
    /usr/sbin/unsquashfs -d "${EXTRACT_ROOT}" "${LOCAL_ARCHIVE}"
    test "$(git -C "${EXTRACT_ROOT}" rev-parse HEAD)" = "${EXPECTED_COMMIT}"
    test -z "$(git -C "${EXTRACT_ROOT}" status --porcelain)"
    unset ELAN_HOME
    lake --version                              # Lean 4.15.0

The archive is one-time work per immutable commit. Never reuse one whose digest, commit,
exclusions, or toolchain identity differs from the intended run, and never fall back to
an unverified shared tree.

`uv sync --frozen` fails if uv.lock is missing or stale — that means the clone is bad
or someone edited pyproject.toml without re-locking on the laptop; stop and report,
do not run `uv lock` on the server (the lockfile is laptop-owned).

## 3. Secrets

Secret NAMES (e.g. OPENAI_API_KEY) may appear in configs and this file; VALUES never
enter the repo, logs, events.jsonl, artifacts, or agent context. Delivery: the user
places values in a private env file OUTSIDE the repo (e.g. ~/.proof_faithfulness_env,
chmod 600); job scripts `source` it. Never `#SBATCH --export=ALL` from an interactive
shell with secrets loaded; use `--export=NONE` and source inside the script. Never echo
env in logs (`env`, `printenv` are banned in job scripts).

## 3b. Model weights — download, storage, serving, sampling

The design lives in PLAN.md S4 (adapters, request math, decoding defaults); this
section is the operational recipe the S4 code and job scripts implement.

**Storage.** Never let weights land in `$HOME` (quota death). Point the HF cache at
project/scratch storage and record the path in §1:

    export HF_HOME=/path/to/project/storage/hf     # in job scripts AND ~/.bashrc
    # Size planning (bf16): 7B ≈ 15 GB, 32B ≈ 65 GB, 72B ≈ 145 GB + vLLM overhead.

**Download (one-time per model, BEFORE any GPU job).** Downloads run on a node with
outbound network (login/DTN if compute nodes are offline — §1 network check):

    hf download <org/model> --revision <FULL_COMMIT_HASH>
    # older CLI name: huggingface-cli download

Rules: (1) the revision is the exact commit hash pinned in configs/models/*.yaml —
never a branch name; the same hash goes into EXPERIMENT-SPEC §3 at slate freeze.
(2) Gated models (e.g. Llama family) need an HF token — secret NAME `HF_TOKEN`,
value via §3; prefer ungated models to avoid the license-acceptance detour.
(3) After download, verify: `hf download` again is a no-op and prints the cache
path; record that path in the model's config entry.

**Serving (one model per GPU job, per §7).** Template:

    vllm serve <org/model> --revision <FULL_COMMIT_HASH> \
        --port 8000 --max-model-len 16384 \
        # sized per model/GPU; add --tensor-parallel-size N for multi-GPU models
    # On offline compute nodes, after pre-downloading:
    export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

The harness waits for `GET /health` (vLLM readiness) before sending requests, and
the job script shuts the server down when the batch completes (serve → run → stop).
First-time bring-up sanity check, before any slate smoke: one hand-written prompt
via `curl localhost:8000/v1/chat/completions`, eyeball the output.

**Sampling (how S4 requests map onto the server).** All decoding parameters come
from configs (defaults temperature 0.2 / top_p 1.0 / max 8192 tokens; a specialized
prover's documented recipe OVERRIDES these and is recorded as a deviation —
Decision Log). Each sample_index is its OWN request with its own deterministic
request ID — never use the API's n>1 batching, which would break the
one-artifact-per-request-ID invariant. Pass `seed` per request where the backend
supports it (vLLM does; best-effort determinism — record it, don't rely on it).
Prover prompt templates (e.g. DeepSeek-Prover/Kimina chat formats) are part of the
hashed prompt template, not ad-hoc code.

## 4. SLURM job lifecycle

One SLURM job = one run stage (a generation batch, a Lean-check sweep, an eval pass).
Template (adjust partition/time/mem after §1 is filled; shell style per
coding-standard/style/shell.md):

    #!/bin/bash
    #SBATCH --job-name=pf-<run_id>-<stage>
    #SBATCH --output=outputs/slurm/%x-%j.out
    #SBATCH --time=04:00:00
    #SBATCH --export=NONE
    #SBATCH --signal=B:USR1@120          # graceful-shutdown warning 120s before timeout
    set -euo pipefail
    source ~/.proof_faithfulness_env
    cd "$SLURM_SUBMIT_DIR"
    uv run proof-faithfulness run \
        --requests <finalized-requests.jsonl> \
        --run-id <run_id> \
        --models configs/experiment/planning-models.yaml \
        --outputs-root outputs \
        --approvals-root approvals \
        --approval-scope <scope>

Operate with:

    sbatch scripts/slurm/<stage>.sbatch      # prints "Submitted batch job <jobid>"
                                             # → immediately record jobid in state.json (§5)
    squeue -u "$USER"                        # live status
    sacct -j <jobid> --format=JobID,State,Elapsed,MaxRSS,ExitCode   # post-mortem
    scancel <jobid>                          # cancel; then set state=cancelled (§5)

The harness must trap SIGUSR1: finish the in-flight request, flush events.jsonl,
release the lock (§6), exit 0. Requeue is manual (a human or the agent resubmits after
checking state) — never `#SBATCH --requeue`, which could double-spend.

## 5. Run-state machine

Persistent state lives in `outputs/runs/<run_id>/state.json` — never only in an agent's
context. States and legal transitions:

    planned → approved → submitted → running → complete
                              ↘ failed / cancelled   (both may → submitted again on retry)

    {"run_id": "...", "state": "running", "slurm_job_id": "12345",
     "owner": {"host": "...", "pid": 0, "started_at": "..."},
     "approval": "approvals/2026-08-XX-pilot-t1.json",
     "updated_at": "...", "history": [ ...every prior transition, append-only... ]}

Rules: `approved` requires the approval record to exist (§8). `submitted` is written in
the same breath as the sbatch call. Transitions are made only by the owning worker or a
human; history is append-only. `plan` / `plan-check` CLI commands operate on `planned`
runs and are free; anything that spends money requires state ≥ approved.

## 6. Worker lock (duplicate-spend prevention)

Exactly one worker per run_id. Before any paid request, the worker acquires
`outputs/runs/<run_id>/LOCK` by atomic create (open with O_CREAT|O_EXCL — mkdir works
too); the file contains host, PID, SLURM job ID, and a heartbeat timestamp the worker
refreshes every 60 s. A lock with a heartbeat older than 10 minutes is stale: verify
via `sacct` that its job is dead, then remove and log a `lock_broken` event. Never
delete a lock whose job still shows RUNNING. Second layer of protection: request-level
idempotency — resume logic skips any request_id whose terminal artifact exists and
passes checksum, so even a lock failure cannot silently double-charge more than the
in-flight request.

## 7. Concurrency & rate limits

Per-provider concurrency cap in configs/models/<provider>.yaml (default 4 until
measured). Transport retries use the harness's internal bounded `RetryPolicy` (default:
three attempts, 0.25 s exponential base, 4 s cap, 10% jitter), and provider-classified
`Retry-After` may raise the delay. Retries reuse the SAME request_id and checksummed
attempt ledger; they are not new samples. A paid transport failure is not retried unless
the provider-specific classifier proves it failed before acceptance; ambiguous paid
attempts fail closed. Log every retry as an event. Local vLLM inference: one model
resident per GPU; never co-schedule two model servers on one GPU without measured
headroom.

## 8. Budget enforcement & approval records

Machine-readable approvals live in `approvals/` (versioned):

    {"scope": "pilot-tier1", "run_ids": ["..."],
     "requests_sha256": "<sha256 of finalized requests.jsonl>",
     "request_count": 60, "max_usd": "40.0",
     "approved_by": "Tingxuan", "date": "2026-08-XX", "note": "..."}

Each approval must bind exactly one run_id and the finalized manifest's byte checksum and
request count. The harness refuses paid transport without exactly one matching record,
atomically reserves each request's worst-case cost, and settles provider-reported cost in
`outputs/runs/<run_id>/budget.json`. That ledger and its SHA-256 sidecar are authoritative
for per-run and aggregate accounting; every scanned run ledger must verify before more
paid work can proceed. The harness halts before a request would exceed `max_usd` and
enforces an absolute $500 aggregate ceiling across all run ledgers. A chat "yes" is not
an approval until this file exists — the agent may DRAFT the record; the human commits it
(agents never approve).

## 9. Structured event log

Append-only `outputs/runs/<run_id>/events.jsonl`, one JSON object per line:
`ts, event, request_id?, detail`. Event vocabulary: stage_transition, request_start,
request_end (with usd_cost, latency_s, tokens), retry, lean_check_start/end,
budget_halt, lock_acquired/released/broken, error. No secrets, no proof text (bodies
live in the artifact store; events reference request_ids).

Events are operational telemetry, not the spend authority. Use the verified
`budget.json` plus `budget.json.sha256` for approval-bound reservation and settlement
accounting; the event-log query below is only a monitoring cross-check.

Monitoring one-liners:

    tail -f outputs/runs/<run_id>/events.jsonl
    jq -s '[.[] | select(.event=="request_end") | .detail.usd_cost] | add' \
        outputs/runs/<run_id>/events.jsonl          # spend so far
    jq -r 'select(.event=="error") | .ts + " " + .detail.msg' \
        outputs/runs/<run_id>/events.jsonl          # errors only

## 10. Recovery

After ANY interruption (agent context loss, node failure, timeout, scancel), recovery
is the same read-only sequence — state on disk is the truth, never memory:

1. `git status --short && git log --oneline -3` — confirm the tree.
2. Read PLAN.md Progress section — where the project believes it is.
3. For each run directory: read state.json; `sacct -j <slurm_job_id>` — reconcile
   (job dead but state=running → verify lock stale per §6, set state=failed with
   reason, log the reconciliation).
4. `tail -20 events.jsonl` — what actually happened last.
5. Resume: resubmit the stage (§4). Resume logic re-derives the full request list from
   the manifest and skips verified terminal artifacts — re-running a completed run is a
   no-op by design (idempotent). If resume would exceed the approval's max_usd, stop
   and request a new approval instead.

Frozen runs are immutable: recovery never rewrites artifacts under a frozen run —
corrections happen in a child run with parent_run_id (PLAN.md S1).

## 11. Cancellation & abort

`scancel <jobid>` → worker traps signal, flushes, releases lock → human/agent sets
state=cancelled with reason in history → spend-to-date noted in the approval's ledger
record and events without editing the human approval. A cancelled run may be resumed
(→ submitted) under the same approval if its manifest identity is unchanged and verified
budget remains, or closed permanently.
