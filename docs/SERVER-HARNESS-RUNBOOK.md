# SERVER-HARNESS-RUNBOOK.md — Operating the Experiment on the SLURM Cluster

This is the control-plane companion to docs/plans/active/PLAN.md (which says WHAT to
build and in what order; this file says HOW to operate it: setup, jobs, run states,
locks, budgets, logs, recovery). The server is a SLURM cluster (confirmed 2026-07-24;
partition/GPU/quota details tracked as todo T008 — record them in §1 when known).
Everything here is written for a stateless agent arriving with only a fresh clone.

## 1. Server facts (fill in at environment discovery, PLAN.md 2.1)

    cluster:          Tillicum (University of Washington HPC), SLURM (confirmed)
    compute budget:   $250 in cluster credits (2026-07-24) — GPU jobs burn this;
                      keep dev on CPU/login nodes + mock adapters; GPUs only for
                      real batches, serve → run → shut down
    partitions:       TBD (sinfo)         GPUs: TBD (types/VRAM — gates model sizes)
    storage quota:    TBD                 network policy: TBD (test from a compute job!)
    proxy/module cmds: TBD                secret delivery: TBD (see §3)
    API budget:       $20 credit on the frontier provider (exact provider name to be
                      confirmed by the user; enough for pilot + cheap-provider core;
                      top-up decision deferred until post-pilot cost data)

If compute nodes have no outbound network, API generation jobs must run on a login/DTN
node or via the cluster's designated proxy — discover this BEFORE any paid batch.

## 2. One-time setup from a clean clone (idempotent)

Working directory: the user-designated path on the cluster (never a scratch dir that
gets purged mid-experiment — check quota/purge policy first).

    git clone <remote-url> proof-conditioned-faithfulness
    cd proof-conditioned-faithfulness
    uv sync --frozen --all-extras            # exact versions from committed uv.lock
    uv run python -c "import proof_faithfulness; print(proof_faithfulness.__version__)"
                                             # expect: 0.1.0

    # Lean toolchain (pinned; PLAN.md 2.2):
    curl -sSf https://elan.lean-lang.org/elan-init.sh | sh -s -- -y   # if elan absent
    lake --version                           # expect the lean-toolchain pinned version
    lake exe cache get                       # Mathlib cache for the pinned commit
    lake build                               # expect: no errors, cache-served

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
    uv run proof-faithfulness run --run-id <run_id> --stage <stage>

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
measured). Respect HTTP 429/Retry-After via tenacity with exponential backoff + jitter;
retries reuse the SAME request_id (transport retries are not new samples — PLAN.md
Decision Log). Log every retry as an event. Local vLLM inference: one model resident
per GPU; never co-schedule two model servers on one GPU without measured headroom.

## 8. Budget enforcement & approval records

Machine-readable approvals live in `approvals/` (versioned):

    {"scope": "pilot-tier1", "run_ids": ["..."], "max_usd": 40.0,
     "approved_by": "Tingxuan", "date": "2026-08-XX", "note": "..."}

The harness refuses to enter `running` on paid work without a matching record, halts
new requests when the run's cumulative cost (from events.jsonl) reaches max_usd
(`budget_halt` event, state → failed with reason budget), and enforces the $500
aggregate ceiling across all runs. A chat "yes" is not an approval until this file
exists — the agent may DRAFT the record; the human commits it (agents never approve).

## 9. Structured event log

Append-only `outputs/runs/<run_id>/events.jsonl`, one JSON object per line:
`ts, event, request_id?, detail`. Event vocabulary: stage_transition, request_start,
request_end (with usd_cost, latency_s, tokens), retry, lean_check_start/end,
budget_halt, lock_acquired/released/broken, error. No secrets, no proof text (bodies
live in the artifact store; events reference request_ids).

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
note. A cancelled run may be resumed (→ submitted) under the same approval if budget
remains, or closed permanently.
