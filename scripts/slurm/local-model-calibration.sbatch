#!/bin/bash
# Run one calibration-only local model through vLLM and the full harness path.

#SBATCH --job-name=pf-model-cal
#SBATCH --account=ckpt-stf
#SBATCH --partition=ckpt-all
#SBATCH --gres=gpu:h200:1
#SBATCH --time=08:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=128G
#SBATCH --requeue
#SBATCH --export=NONE
#SBATCH --output=/mmfs1/home/thuang27/pf-model-cal-%j.out

set -euo pipefail
umask 077

readonly MODEL_KEY="${1:?usage: local-model-calibration.sbatch MODEL_KEY COMMIT}"
readonly EXPECTED_COMMIT="${2:?usage: local-model-calibration.sbatch MODEL_KEY COMMIT}"
case "${MODEL_KEY}" in
  gpt-oss-120b)
    readonly MANIFEST_NAME="gpt_oss_120b.yaml"
    ;;
  qwen3-32b)
    readonly MANIFEST_NAME="qwen3_32b.yaml"
    ;;
  deepseek-prover-v2-7b)
    readonly MANIFEST_NAME="deepseek_prover_v2_7b.yaml"
    ;;
  *)
    printf 'unsupported calibration model: %s\n' "${MODEL_KEY}" >&2
    exit 2
    ;;
esac

readonly SNAPSHOT_ROOT="/gscratch/scrubbed/thuang27/proof-faithfulness/snapshots"
readonly ARCHIVE="${SNAPSHOT_ROOT}/proof-faithfulness-${EXPECTED_COMMIT}.sqsh"
readonly IMAGE="/gscratch/scrubbed/thuang27/proof-faithfulness/containers/vllm-openai-v0.19.1.sif"
readonly HF_HOME="/gscratch/scrubbed/thuang27/proof-faithfulness/huggingface"
readonly SHARED_OUTPUTS="/mmfs1/gscratch/stf/thuang27/proof-conditioned-faithfulness/outputs/calibration"
readonly RUN_ID="calibration-${MODEL_KEY}-${SLURM_JOB_ID}"
readonly LOCAL_BASE="/tmp/${USER}/proof-faithfulness-calibration-${SLURM_JOB_ID}"
readonly LOCAL_ARCHIVE="${LOCAL_BASE}/environment.sqsh"
readonly EXTRACT_ROOT="${LOCAL_BASE}/root"
readonly RUNTIME_ROOT="${LOCAL_BASE}/runtime"

SERVER_PID=""
MONITOR_PID=""
PROJECT_ROOT=""
TOKENIZER_NOTE=""

attach_evidence() {
  local name="$1"
  local path="$2"
  if [[ -n "${PROJECT_ROOT}" && -f "${path}" ]]; then
    "${PROJECT_ROOT}/.venv/bin/python" -c \
      'from proof_faithfulness.cli import app; app()' \
      calibration attach-evidence \
      --run-id "${RUN_ID}" \
      --outputs-root "${SHARED_OUTPUTS}" \
      --name "${name}" \
      --evidence "${path}" >/dev/null || true
  fi
}

cleanup() {
  set +e
  if [[ -n "${SERVER_PID}" ]]; then
    kill "${SERVER_PID}" 2>/dev/null || true
    wait "${SERVER_PID}" 2>/dev/null || true
  fi
  if [[ -n "${MONITOR_PID}" ]]; then
    kill "${MONITOR_PID}" 2>/dev/null || true
    wait "${MONITOR_PID}" 2>/dev/null || true
  fi
  attach_evidence server.log "${RUNTIME_ROOT}/server.log"
  attach_evidence gpu-samples.csv "${RUNTIME_ROOT}/gpu-samples.csv"
  attach_evidence model-info.json "${RUNTIME_ROOT}/model-info.json"
  attach_evidence server-argv.txt "${RUNTIME_ROOT}/server-argv.txt"
  chmod -R u+w "${LOCAL_BASE}" 2>/dev/null || true
  rm -rf "${LOCAL_BASE}"
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT

set +u
module load gcc/12.3.0
set -u
export PATH="/gscratch/scrubbed/thuang27/.elan/bin:/usr/local/bin:/usr/sbin:/usr/bin:/bin"
export UV_CACHE_DIR="${LOCAL_BASE}/uv-cache"
export UV_OFFLINE=true
export TMPDIR="${LOCAL_BASE}/tmp"
export HF_HOME
export HF_HUB_CACHE="${HF_HOME}/hub"
export TRANSFORMERS_CACHE="${HF_HOME}/transformers"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export XDG_CACHE_HOME="${LOCAL_BASE}/cache"
export FLASHINFER_WORKSPACE_DIR="${LOCAL_BASE}/flashinfer"
export VLLM_CACHE_ROOT="${LOCAL_BASE}/vllm-cache"
export VLLM_NO_USAGE_STATS=1
export NO_PROXY="127.0.0.1,localhost"
export no_proxy="${NO_PROXY}"

install -d -m 700 \
  "${LOCAL_BASE}" "${RUNTIME_ROOT}" "${TMPDIR}" \
  "${UV_CACHE_DIR}" "${HF_HUB_CACHE}" "${TRANSFORMERS_CACHE}" \
  "${XDG_CACHE_HOME}" "${FLASHINFER_WORKSPACE_DIR}" "${VLLM_CACHE_ROOT}"

read -r EXPECTED_SHA256 _ < "${ARCHIVE}.sha256"
printf '%s  %s\n' "${EXPECTED_SHA256}" "${ARCHIVE}" | sha256sum -c -
cp "${ARCHIVE}" "${LOCAL_ARCHIVE}"
printf '%s  %s\n' "${EXPECTED_SHA256}" "${LOCAL_ARCHIVE}" | sha256sum -c -
/usr/sbin/unsquashfs \
  -processors "${SLURM_CPUS_PER_TASK}" \
  -d "${EXTRACT_ROOT}" \
  "${LOCAL_ARCHIVE}"

if [[ -f "${EXTRACT_ROOT}/pyproject.toml" ]]; then
  PROJECT_ROOT="${EXTRACT_ROOT}"
elif [[ -f "${EXTRACT_ROOT}/proof-conditioned-faithfulness/pyproject.toml" ]]; then
  PROJECT_ROOT="${EXTRACT_ROOT}/proof-conditioned-faithfulness"
else
  printf 'snapshot does not contain the project root\n' >&2
  exit 1
fi
readonly PROJECT_ROOT
cd "${PROJECT_ROOT}"
if [[ "$(git rev-parse HEAD)" != "${EXPECTED_COMMIT}" ]]; then
  printf 'snapshot commit mismatch\n' >&2
  exit 1
fi
if [[ -n "$(git status --porcelain)" ]]; then
  printf 'snapshot worktree is not clean\n' >&2
  exit 1
fi
if [[ ! -f "${IMAGE}" ]]; then
  printf 'pinned vLLM image is missing: %s\n' "${IMAGE}" >&2
  exit 1
fi

export PYTHONPATH="${PROJECT_ROOT}/src"
readonly PYTHON="${PROJECT_ROOT}/.venv/bin/python"
readonly MANIFEST="${PROJECT_ROOT}/configs/calibration/${MANIFEST_NAME}"
readonly CLI_ENTRY='from proof_faithfulness.cli import app; app()'

"${PYTHON}" - <<PY
from pathlib import Path
from proof_faithfulness.artifacts import RunArtifactStore
RunArtifactStore(Path(${SHARED_OUTPUTS@Q}), ${RUN_ID@Q}).initialize()
PY

mapfile -t SERVER_ARGS < <(
  "${PYTHON}" -c "${CLI_ENTRY}" calibration vllm-argv --models "${MANIFEST}"
)
printf '%s\n' "${SERVER_ARGS[@]}" > "${RUNTIME_ROOT}/server-argv.txt"
PORT=""
EXPECTED_MODEL=""
for ((index = 0; index < ${#SERVER_ARGS[@]}; index++)); do
  case "${SERVER_ARGS[index]}" in
    --model) EXPECTED_MODEL="${SERVER_ARGS[index + 1]}" ;;
    --port) PORT="${SERVER_ARGS[index + 1]}" ;;
  esac
done
if [[ -z "${PORT}" || -z "${EXPECTED_MODEL}" ]]; then
  printf 'manifest-derived server arguments lack model or port\n' >&2
  exit 1
fi
if "${PYTHON}" -c \
    'import socket,sys; sock=socket.socket(); sock.settimeout(1); code=sock.connect_ex(("127.0.0.1", int(sys.argv[1]))); sock.close(); raise SystemExit(0 if code == 0 else 1)' \
    "${PORT}"; then
  printf 'refusing occupied vLLM port: %s\n' "${PORT}" >&2
  exit 1
fi
: > "${RUNTIME_ROOT}/server.log"
if [[ "${MODEL_KEY}" == "deepseek-prover-v2-7b" ]]; then
  readonly TOKENIZER_OVERLAY="/gscratch/scrubbed/thuang27/proof-faithfulness/huggingface/tokenizer-overlays/deepseek-prover-v2-7b/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b-pretrained-fast"
  printf '%s  %s\n' \
    "091b9dadb9845f0e8386c38bdb87e98db8adc7b0aacf36cb9257c00d0a668714" \
    "${TOKENIZER_OVERLAY}/tokenizer.json" \
    "4053f0035c788f77b81d98d470f51abf51ee41f8c608679d4d1e74b02e328859" \
    "${TOKENIZER_OVERLAY}/tokenizer_config.json" \
    "da65b8f28475bf69826889a601848c5c2cb37f5847f239301aa3a82948c23445" \
    "${TOKENIZER_OVERLAY}/provenance.json" \
    | sha256sum -c - >> "${RUNTIME_ROOT}/server.log"
  apptainer exec --cleanenv \
    --bind "${HF_HOME}:${HF_HOME}" \
    "${IMAGE}" /usr/bin/python3.12 -c \
    'import json,sys; from transformers import AutoTokenizer; t=AutoTokenizer.from_pretrained(sys.argv[1], local_files_only=True, trust_remote_code=True); sample=" a\nb"; ids=t.encode(sample, add_special_tokens=False); decoded=t.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False); chat=t.apply_chat_template([{"role":"user","content":"line one\nline two"}], tokenize=False, add_generation_prompt=True); assert t.is_fast and decoded == sample and "line one\nline two" in chat; print(json.dumps({"tokenizer_class": type(t).__name__, "is_fast": t.is_fast, "roundtrip_ids": ids, "roundtrip_decoded": decoded, "chat_template_ok": True}))' \
    "${TOKENIZER_OVERLAY}" >> "${RUNTIME_ROOT}/server.log"
  TOKENIZER_NOTE="DeepSeek tokenizer overlay 4053f0035c788f77b81d98d470f51abf51ee41f8c608679d4d1e74b02e328859 corrects Transformers-5 class dispatch; source model revision remains pinned."
fi
readonly SERVER_VERSION="$(
  apptainer exec "${IMAGE}" /usr/bin/python3.12 -c \
    'import vllm; print(vllm.__version__)'
)"
readonly CONTAINER_SHA256="$(sha256sum "${IMAGE}" | cut -d' ' -f1)"

printf 'timestamp,name,uuid,memory_total_mb,memory_used_mb\n' \
  > "${RUNTIME_ROOT}/gpu-samples.csv"
(
  while true; do
    nvidia-smi \
      --query-gpu=timestamp,name,uuid,memory.total,memory.used \
      --format=csv,noheader,nounits >> "${RUNTIME_ROOT}/gpu-samples.csv"
    sleep 1
  done
) &
MONITOR_PID="$!"

readonly LOAD_START="$(date +%s)"
apptainer exec --cleanenv \
  --nv \
  --bind "${HF_HOME}:${HF_HOME}" \
  --bind "${LOCAL_BASE}:${LOCAL_BASE}" \
  --env "HF_HOME=${HF_HOME}" \
  --env "HF_HUB_CACHE=${HF_HUB_CACHE}" \
  --env "TRANSFORMERS_CACHE=${TRANSFORMERS_CACHE}" \
  --env "HF_HUB_OFFLINE=${HF_HUB_OFFLINE}" \
  --env "TRANSFORMERS_OFFLINE=${TRANSFORMERS_OFFLINE}" \
  --env "XDG_CACHE_HOME=${XDG_CACHE_HOME}" \
  --env "FLASHINFER_WORKSPACE_DIR=${FLASHINFER_WORKSPACE_DIR}" \
  --env "VLLM_CACHE_ROOT=${VLLM_CACHE_ROOT}" \
  --env "VLLM_NO_USAGE_STATS=${VLLM_NO_USAGE_STATS}" \
  "${IMAGE}" \
  /usr/bin/python3.12 -m vllm.entrypoints.openai.api_server \
  "${SERVER_ARGS[@]}" \
  --download-dir "${HF_HUB_CACHE}" \
  >> "${RUNTIME_ROOT}/server.log" 2>&1 &
SERVER_PID="$!"

READY=false
for _ in $(seq 1 720); do
  if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
    printf 'vLLM exited before readiness\n' >&2
    exit 1
  fi
  if curl --fail --silent --show-error \
    "http://127.0.0.1:${PORT}/v1/models" \
      > "${RUNTIME_ROOT}/model-info.json"; then
    READY=true
    break
  fi
  sleep 5
done
if [[ "${READY}" != true ]]; then
  printf 'vLLM did not become ready within 3600 seconds\n' >&2
  exit 1
fi
kill -0 "${SERVER_PID}"
"${PYTHON}" -c \
  'import json,sys; body=json.load(open(sys.argv[1], encoding="utf-8")); ids=[item.get("id") for item in body.get("data", []) if isinstance(item, dict)]; assert sys.argv[2] in ids, (sys.argv[2], ids)' \
  "${RUNTIME_ROOT}/model-info.json" "${EXPECTED_MODEL}"
readonly LOAD_END="$(date +%s)"
readonly LOAD_TIME="$((LOAD_END - LOAD_START))"

"${PYTHON}" -c "${CLI_ENTRY}" calibration run \
  --models "${MANIFEST}" \
  --run-id "${RUN_ID}" \
  --outputs-root "${SHARED_OUTPUTS}"
"${PYTHON}" - <<'PY'
from pathlib import Path

from proof_faithfulness.lean.checker import warm_mathlib_cache

result = warm_mathlib_cache(project_root=Path.cwd())
print(result)
if not result.success:
    raise RuntimeError(f"trusted Mathlib warm-up failed: {result}")
PY
"${PYTHON}" -c "${CLI_ENTRY}" calibration assess \
  --models "${MANIFEST}" \
  --run-id "${RUN_ID}" \
  --outputs-root "${SHARED_OUTPUTS}" \
  --project-root "${PROJECT_ROOT}"

readonly GPU_NAME="$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
readonly GPU_UUID="$(nvidia-smi --query-gpu=uuid --format=csv,noheader | head -1)"
readonly GPU_TOTAL="$(
  nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1
)"
readonly GPU_PEAK="$(
  awk -F, 'NR > 1 {gsub(/ /, "", $5); if ($5 > max) max=$5} END {print max+0}' \
    "${RUNTIME_ROOT}/gpu-samples.csv"
)"
readonly HOSTNAME_VALUE="$(hostname)"
readonly ARGV_JSON="$(
  "${PYTHON}" -c 'import json,sys; print(json.dumps(tuple(x.rstrip("\n") for x in sys.stdin)))' \
    < "${RUNTIME_ROOT}/server-argv.txt"
)"
"${PYTHON}" - <<PY
from pathlib import Path
from proof_faithfulness.calibration import RuntimeMetadata
metadata = RuntimeMetadata(
    backend_key=${MODEL_KEY@Q},
    model_id=${SERVER_ARGS[1]@Q},
    revision=${SERVER_ARGS[3]@Q},
    transport="vllm",
    server_software="vllm",
    server_version=${SERVER_VERSION@Q},
    hostname=${HOSTNAME_VALUE@Q},
    slurm_job_id=${SLURM_JOB_ID@Q},
    gpu_name=${GPU_NAME@Q},
    gpu_uuid=${GPU_UUID@Q},
    gpu_memory_total_mb=int(${GPU_TOTAL@Q}),
    peak_gpu_memory_mb=int(${GPU_PEAK@Q}),
    load_time_s=float(${LOAD_TIME@Q}),
    serving_configuration=${ARGV_JSON},
    container_sha256=${CONTAINER_SHA256@Q},
    notes=tuple(filter(None, (
        "Calibration-only; not pilot or experimental data.",
        ${TOKENIZER_NOTE@Q},
    ))),
)
Path(${RUNTIME_ROOT@Q}, "runtime.json").write_text(
    metadata.model_dump_json(indent=2) + "\n", encoding="utf-8"
)
PY
"${PYTHON}" -c "${CLI_ENTRY}" calibration attach-runtime \
  --run-id "${RUN_ID}" \
  --outputs-root "${SHARED_OUTPUTS}" \
  --metadata "${RUNTIME_ROOT}/runtime.json"

attach_evidence server.log "${RUNTIME_ROOT}/server.log"
attach_evidence gpu-samples.csv "${RUNTIME_ROOT}/gpu-samples.csv"
attach_evidence model-info.json "${RUNTIME_ROOT}/model-info.json"
attach_evidence server-argv.txt "${RUNTIME_ROOT}/server-argv.txt"
printf 'CALIBRATION_COMPLETE=%s RUN_ID=%s\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${RUN_ID}"
