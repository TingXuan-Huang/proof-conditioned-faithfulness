# Proof-Conditioned Lean Faithfulness Study

Does a proof-conditioned Lean system actually follow the proof it is given?

For the same theorem, this project curates two complete informal proofs that use
different mathematical strategies. The Lean statement stays fixed while the supplied
proof changes from route A to route B. The experiment measures whether the generated
Lean proof changes strategy accordingly.

The primary contribution is an evaluation benchmark and reproducible generation/checking
pipeline, not a newly trained model. The intended submission target is the MATH-AI
workshop at NeurIPS 2026.

Author: Tingxuan Huang.

## Current Status

- Fixture-backed engineering stages S1-S5 are complete.
- Real-backend calibration is complete for GPT-OSS 120B, Qwen3-32B,
  DeepSeek-Prover-V2-7B, and the testing-only Meta Muse Spark API.
- ProofBridge is not runnable from its public release. ProofFlow reached generation but
  failed in upstream proof-graph construction.
- The final offline checkpoint passed 283 tests, Ruff, Pyright, and `lake build`.
- No pilot, core experiment, or GPT-5.6 Terra production request has run.
- Gate P, Gate S, final model-slate approval, and statistical decisions remain
  human-owned and open.

Read these before operating the project:

- [Real-backend readiness report](docs/REAL-BACKEND-COMPATIBILITY-REPORT.md)
- [Human review checklist](docs/HUMAN-REVIEW-TODO.md)
- [Cluster incident and recovery log](docs/CLUSTER-EXPERIMENT-INCIDENTS.md)
- [Server harness runbook](docs/SERVER-HARNESS-RUNBOOK.md)
- [Active implementation plan](docs/plans/active/PLAN.md)

## Repository Map

| Path | Purpose |
| --- | --- |
| `src/proof_faithfulness/` | Python contracts, generation, checking, and evaluation code |
| `ProofFaithfulness/` | Trusted Lean audit and dependency tooling |
| `configs/calibration/` | One-request real-backend calibration manifests |
| `configs/experiment/` | Condition matrix and offline request planning |
| `prompts/` | Versioned, hashed prompt templates |
| `data/benchmark/` | Candidate pairs, reference briefs, and submitted proof data |
| `scripts/slurm/` | Checksummed snapshot and local-model SLURM launchers |
| `outputs/calibration/` | Ignored calibration artifacts; never scientific experiment data |
| `approvals/` | Machine-readable paid-request authorization records |
| `docs/` | Plan, runbook, readiness evidence, incidents, and human decisions |

Agents should also read [AGENTS.md](AGENTS.md). Engineering conventions live in
[`coding-standard/`](coding-standard/).

## Hyak Assumptions

The checked-in launchers currently target the owner's UW Hyak layout:

```text
project:  /mmfs1/gscratch/stf/thuang27/proof-conditioned-faithfulness
weights:  /gscratch/scrubbed/thuang27/proof-faithfulness/huggingface
images:   /gscratch/scrubbed/thuang27/proof-faithfulness/containers
snapshots:/gscratch/scrubbed/thuang27/proof-faithfulness/snapshots
```

Another Hyak user must review and change account names and absolute storage paths before
submitting jobs. Do not place model weights in `$HOME`. Scrubbed storage is temporary;
reverify cached model and snapshot hashes before reuse.

The environment is pinned to Python 3.12, Lean 4.15.0, Mathlib tag `v4.15.0` at commit
`9837ca9d65d9de6fad1ef4381750ca688774e608`, and the committed `uv.lock`.

## 1. Log In And Inspect The Checkout

On a Hyak login node:

```bash
cd /mmfs1/gscratch/stf/thuang27/proof-conditioned-faithfulness
module load gcc/12.3.0

git rev-parse HEAD
git status --short
uv --version
lake --version
```

Generation requires a clean Git worktree. Commit or intentionally discard reviewed
changes before a GPU or API run. Never bypass this rule for scientific output.

For a new clone:

```bash
REPOSITORY_URL="https://github.com/<owner>/proof-conditioned-faithfulness.git"
git clone "$REPOSITORY_URL" proof-conditioned-faithfulness
cd proof-conditioned-faithfulness
module load gcc/12.3.0

uv sync --frozen --all-extras
uv run python -c \
  'import proof_faithfulness; print(proof_faithfulness.__version__)'
```

Do not run `uv lock` on the server. A stale or missing lockfile is a repository problem,
not permission to regenerate the environment on a compute host.

If the Lean cache is not installed:

```bash
export SSL_CERT_FILE=/etc/pki/tls/certs/ca-bundle.crt
lake exe cache get
lake build
```

## 2. Start An Interactive CPU Session

Use a normal CPU allocation for manual verification:

```bash
srun --account=stf --partition=cpu-g2 \
  --time=02:00:00 --cpus-per-task=4 --mem=32G --pty bash -l

module load gcc/12.3.0
cd /mmfs1/gscratch/stf/thuang27/proof-conditioned-faithfulness
export UV_CACHE_DIR="${TMPDIR:-/tmp/${USER}}/uv-cache"
mkdir -p "$UV_CACHE_DIR"
```

Record the allocated host and commit:

```bash
hostname
git rev-parse HEAD
git status --short
uv run proof-faithfulness env doctor
```

## 3. Run The Offline Smoke Tests

Start with checks that do not issue API requests or load model weights:

```bash
uv run pytest -q -p no:cacheprovider
uv run ruff check src tests
uv run pyright
lake build
```

The latest checkpoint passed 283 tests. The exact count may increase as tests are added;
the required condition is zero failures.

Run the trusted Lean and dependency suites separately when changing S2/S3:

```bash
uv run pytest tests/integration/test_lean_checker.py -q -p no:cacheprovider
uv run pytest tests/integration/test_dependency_probe.py -q -p no:cacheprovider
```

Warm Mathlib before checking real candidate/model output:

```bash
uv run proof-faithfulness env lean-warmup \
  --project-root . \
  --timeout-seconds 1200 \
  --memory-limit-mb 8192
```

Full `import Mathlib` work can stall on shared GPFS. If warm-up makes little progress,
do not increase timeouts indefinitely or classify a proof as invalid. Use the
checksummed node-local procedure in the runbook. Request at least 16 GiB for the
8,192-MiB Lean child limit.

## 4. Inspect Offline Request Planning

These commands create no paid or model request:

```bash
uv run proof-faithfulness plan --tier 1 --split pilot
uv run proof-faithfulness plan-check --tier 1 --split pilot
```

The Tier-1 pilot plan should report 45 proof-conditioned requests and 15 theorem-only
requests. Planning is not authorization to run them.

Inspect a backend manifest without reading its secret value:

```bash
uv run proof-faithfulness model inspect \
  --config configs/calibration/qwen3_32b.yaml

uv run proof-faithfulness calibration vllm-argv \
  --models configs/calibration/qwen3_32b.yaml
```

### Local model asset prerequisite

The SLURM launcher is offline and never downloads weights. The owner's current cache
must contain these exact revisions:

| Model | Revision |
| --- | --- |
| `openai/gpt-oss-120b` | `b5c939de8f754692c1647ca79fbf85e8c1e70f8a` |
| `Qwen/Qwen3-32B` | `9216db5781bf21249d130ec9da846c4624c16137` |
| `deepseek-ai/DeepSeek-Prover-V2-7B` | `a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b` |

Check the pinned vLLM image and cache before requesting a GPU:

```bash
HF_HOME="/gscratch/scrubbed/thuang27/proof-faithfulness/huggingface"
IMAGE="/gscratch/scrubbed/thuang27/proof-faithfulness/containers/vllm-openai-v0.19.1.sif"

test -f "$IMAGE"
sha256sum "$IMAGE"
test -d "$HF_HOME/hub/models--openai--gpt-oss-120b/snapshots/b5c939de8f754692c1647ca79fbf85e8c1e70f8a"
test -d "$HF_HOME/hub/models--Qwen--Qwen3-32B/snapshots/9216db5781bf21249d130ec9da846c4624c16137"
test -d "$HF_HOME/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b"
```

The recorded image SHA-256 is
`bc40ebbf3c8d9ab67e29c72b6ce0500b5d313226891edd4ece4d92bd9c5e3ccd`.
The launcher checks the model revisions from the manifests and runs with Hugging Face
offline mode enabled.

If a model is absent, download it on a network-enabled login/transfer node, not inside a
GPU allocation:

```bash
export HF_HOME="/gscratch/scrubbed/thuang27/proof-faithfulness/huggingface"

hf download openai/gpt-oss-120b \
  --revision b5c939de8f754692c1647ca79fbf85e8c1e70f8a
hf download Qwen/Qwen3-32B \
  --revision 9216db5781bf21249d130ec9da846c4624c16137
hf download deepseek-ai/DeepSeek-Prover-V2-7B \
  --revision a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b
```

These downloads are large. Download only selected backends, never use a branch name,
and rerun the same command to confirm it is a cache hit. DeepSeek additionally requires
the checksummed tokenizer overlay named in `local-model-calibration.sbatch`. If that
overlay is missing, stop and follow incident I021; do not silently use the old tokenizer.

## 5. Build A Checksummed Execution Snapshot

Local-model jobs refuse a dirty tree and require a snapshot named by the exact commit.
Build it once per commit:

```bash
cd /mmfs1/gscratch/stf/thuang27/proof-conditioned-faithfulness
test -z "$(git status --porcelain)" || {
  echo "Refusing dirty worktree" >&2
  exit 1
}

COMMIT="$(git rev-parse HEAD)"
SNAPSHOT_JOB="$(sbatch --parsable \
  scripts/slurm/build-calibration-snapshot.sbatch "$COMMIT")"

echo "snapshot job: $SNAPSHOT_JOB"
squeue -j "$SNAPSHOT_JOB"
```

After completion:

```bash
sacct -j "$SNAPSHOT_JOB" \
  --format=JobID,JobName,State,ExitCode,Elapsed,NodeList
tail -n 100 "$HOME/pf-cal-snapshot-${SNAPSHOT_JOB}.out"
```

Expected state is `COMPLETED` with exit `0:0`. The builder refuses to overwrite an
existing archive. If the archive already exists, verify its SHA-256 sidecar rather than
deleting it casually.

## 6. Run One Local Model Calibration

Each calibration is one theorem, one condition, and one sample. The launcher performs:

```text
verify snapshot -> start pinned vLLM -> verify model identity -> generate
-> persist raw response -> rerun to prove no-op resume -> warm Lean
-> trusted check -> conditional dependency/evaluation -> persist runtime evidence
```

### GPT-OSS 120B on H200

```bash
COMMIT="$(git rev-parse HEAD)"
JOB_ID="$(sbatch --parsable \
  --account=ckpt-stf --partition=ckpt-all --gres=gpu:h200:1 \
  scripts/slurm/local-model-calibration.sbatch gpt-oss-120b "$COMMIT")"
echo "$JOB_ID"
```

### Qwen3-32B on H200

```bash
COMMIT="$(git rev-parse HEAD)"
JOB_ID="$(sbatch --parsable \
  --account=ckpt-stf --partition=ckpt-all --gres=gpu:h200:1 \
  scripts/slurm/local-model-calibration.sbatch qwen3-32b "$COMMIT")"
echo "$JOB_ID"
```

Qwen also fits on a measured A100 80-GB fallback:

```bash
COMMIT="$(git rev-parse HEAD)"
JOB_ID="$(sbatch --parsable \
  --account=ckpt-stf --partition=ckpt-all --gres=gpu:a100:1 \
  scripts/slurm/local-model-calibration.sbatch qwen3-32b "$COMMIT")"
echo "$JOB_ID"
```

### DeepSeek-Prover-V2-7B on L40

Do not queue this 7B model on H200 when an L40 is available:

```bash
COMMIT="$(git rev-parse HEAD)"
JOB_ID="$(sbatch --parsable \
  --account=stf --partition=gpu-l40 --gres=gpu:l40:1 \
  --time=04:00:00 --cpus-per-task=2 --mem=64G \
  scripts/slurm/local-model-calibration.sbatch \
  deepseek-prover-v2-7b "$COMMIT")"
echo "$JOB_ID"
```

Checkpoint GPU jobs are preemptible. They are appropriate for free calibration, not a
paid API request or a production run.

## 7. Monitor And Inspect A Model Job

```bash
squeue -j "$JOB_ID" -o '%i %P %T %M %S %R'
sacct -j "$JOB_ID" \
  --format=JobID,JobName,Partition,State,ExitCode,Elapsed,NodeList
tail -f "$HOME/pf-model-cal-${JOB_ID}.out"
```

After completion:

```bash
MODEL_KEY=qwen3-32b  # change to the submitted launcher key
RUN_ID="calibration-${MODEL_KEY}-${JOB_ID}"
RUN_ROOT="outputs/calibration/runs/${RUN_ID}"

.venv/bin/python -m json.tool "$RUN_ROOT/reports/resume.json"
.venv/bin/python -m json.tool "$RUN_ROOT/reports/assessment.json"
.venv/bin/python -m json.tool "$RUN_ROOT/reports/runtime.json"
find "$RUN_ROOT" -type f | sort
```

A backend integration can pass even when the sampled Lean proof is invalid. Confirm
that generation and persistence completed, resume skipped the verified response, and
the checker recorded a precise category. Do not repair model text to make the smoke
look green.

## 8. Run A Paid API Calibration Safely

Do this only for a testing backend selected by the human owner. Meta calibration output
must never enter pilot/core data. GPT-5.6 Terra remains uncalled.

Every external request requires a new machine-readable approval that matches all of:

- run ID;
- request-manifest SHA-256;
- request count;
- approval scope;
- maximum dollars.

The historical approval in `approvals/` authorizes only its historical, already
completed run. Never edit or reuse it for a new request.

First choose separate planning and final run IDs. Stage the deterministic request
manifest under the planning ID with no key loaded. The expected result is
`MissingApprovalError`, with no network request:

```bash
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PLAN_RUN_ID="calibration-meta-plan-${STAMP}"
RUN_ID="calibration-meta-manual-${STAMP}"
MODEL_CONFIG="configs/calibration/meta_muse_spark_1_1.yaml"

unset META_MODEL_API_KEY
.venv/bin/proof-faithfulness calibration run \
  --models "$MODEL_CONFIG" \
  --run-id "$PLAN_RUN_ID" \
  --outputs-root outputs/calibration \
  --approvals-root approvals \
  --approval-scope calibration-testing \
  --aggregate-ceiling-usd 5.50
```

Inspect the generated request before authorizing anything:

```bash
REQUESTS="outputs/calibration/runs/${PLAN_RUN_ID}/requests.jsonl"
wc -l "$REQUESTS"
sha256sum "$REQUESTS"
less "$REQUESTS"
```

The human owner must then create and review a new approval following
`docs/SERVER-HARNESS-RUNBOOK.md` section 8. Its `run_ids` field names the final
`$RUN_ID`, while its request hash and count come from `$REQUESTS`. Calibration request
content is deterministic and does not include the run ID, so the final run will produce
the same request hash. Do not have an automation agent infer approval.

The human must commit the approval and return to a clean worktree before the paid run:

```bash
APPROVAL_FILE="approvals/YYYY-MM-DD-provider-calibration.json"
git add "$APPROVAL_FILE"
git commit -m "Approve one calibration API request"
test -z "$(git status --porcelain)" || {
  echo "Refusing paid request from dirty worktree" >&2
  exit 1
}
```

After the committed approval exists, load a fresh key silently:

```bash
set +x
read -rsp "Meta API key: " META_MODEL_API_KEY
printf '\n'
export META_MODEL_API_KEY
test -n "${META_MODEL_API_KEY:-}" && echo "API key loaded"
```

Run the same command with the approved ceiling:

```bash
.venv/bin/proof-faithfulness calibration run \
  --models "$MODEL_CONFIG" \
  --run-id "$RUN_ID" \
  --outputs-root outputs/calibration \
  --approvals-root approvals \
  --approval-scope calibration-testing \
  --aggregate-ceiling-usd 5.50
```

Then clear the process environment:

```bash
unset META_MODEL_API_KEY
test -z "${META_MODEL_API_KEY+x}" && echo "key cleared from this shell"
```

`unset` is not credential revocation. Delete/rotate any key exposed in chat, a command,
or a log through the provider dashboard.

Inspect the checksummed response, budget, and resume report before authorizing another
request:

```bash
RUN_ROOT="outputs/calibration/runs/${RUN_ID}"
.venv/bin/python -m json.tool "$RUN_ROOT/budget.json"
.venv/bin/python -m json.tool "$RUN_ROOT/reports/resume.json"
find "$RUN_ROOT/responses" -name response.json -print
```

Run downstream assessment without the secret after the response is persisted:

```bash
uv run proof-faithfulness env lean-warmup \
  --project-root . --timeout-seconds 1200 --memory-limit-mb 8192

.venv/bin/proof-faithfulness calibration assess \
  --models "$MODEL_CONFIG" \
  --run-id "$RUN_ID" \
  --outputs-root outputs/calibration \
  --project-root .
```

## 9. Failure Handling

Do not immediately resubmit a failed job. Classify it first:

| Symptom | Likely layer | Next action |
| --- | --- | --- |
| `AssocGrpCpuLimit` or `Priority` | Scheduler | Wait; inspect `squeue --start`; avoid duplicate submissions |
| Cold Lean timeout / very low CPU | GPFS/Mathlib staging | Use node-local snapshot and warm-up |
| Exit signal near 4 GiB | Lean resource limit | Confirm 8,192-MiB child and at least 16-GiB job memory |
| `unsquashfs` destination exists | Launcher | Do not pre-create the extraction destination |
| Generic `python` missing | Container | Use pinned `/usr/bin/python3.12` |
| Dirty-worktree refusal | Provenance safeguard | Review and commit; do not bypass for production |
| Missing approval | Spend safeguard | Inspect manifest and obtain exact human approval |
| Missing secret | Preflight | Export silently; confirm no transport occurred |
| Lean `type_invalid`/`multiple_blocks` | Model output | Preserve and report; do not repair |
| Checksum mismatch | Artifact integrity | Stop; never resume or overwrite blindly |

The complete history, exact job IDs, and fixes are in the
[incident log](docs/CLUSTER-EXPERIMENT-INCIDENTS.md).

## 10. Stop Before Production

The commands above are for engineering, fixtures, and calibration. Do not start the
pilot or core experiment until the human owner has:

1. approved the pilot pairs and reference proofs;
2. reviewed the readiness report and frozen the model/pipeline slate;
3. approved every external request manifest and budget;
4. recorded the required decisions in the active plan.

Publishing code is also separate from approving an experiment. Follow the Git review
commands in [HUMAN-REVIEW-TODO.md](docs/HUMAN-REVIEW-TODO.md) before pushing.
