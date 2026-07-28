#!/bin/bash
# Build a checksummed node-local execution snapshot for a committed calibration harness.

#SBATCH --job-name=pf-cal-snapshot
#SBATCH --account=stf
#SBATCH --partition=ckpt-g2
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=24G
#SBATCH --export=NONE
#SBATCH --output=/mmfs1/home/thuang27/pf-cal-snapshot-%j.out

set -euo pipefail
umask 077

readonly PROJECT_ROOT="/mmfs1/gscratch/stf/thuang27/proof-conditioned-faithfulness"
readonly EXPECTED_COMMIT="${1:?usage: build-calibration-snapshot.sbatch COMMIT}"
readonly SNAPSHOT_ROOT="/gscratch/scrubbed/thuang27/proof-faithfulness/snapshots"
readonly ARCHIVE="${SNAPSHOT_ROOT}/proof-faithfulness-${EXPECTED_COMMIT}.sqsh"
readonly TEMP_ARCHIVE="${ARCHIVE}.tmp-${SLURM_JOB_ID}"

cleanup() {
  rm -f "${TEMP_ARCHIVE}"
}
trap cleanup EXIT

cd "${PROJECT_ROOT}"
readonly ACTUAL_COMMIT="$(timeout 120 git rev-parse HEAD)"
if [[ "${ACTUAL_COMMIT}" != "${EXPECTED_COMMIT}" ]]; then
  printf 'commit mismatch: expected %s, got %s\n' \
    "${EXPECTED_COMMIT}" "${ACTUAL_COMMIT}" >&2
  exit 1
fi
if [[ -n "$(timeout 120 git status --porcelain)" ]]; then
  printf 'refusing to snapshot a dirty worktree\n' >&2
  exit 1
fi
if [[ -e "${ARCHIVE}" || -e "${ARCHIVE}.sha256" ]]; then
  printf 'refusing to overwrite existing snapshot: %s\n' "${ARCHIVE}" >&2
  exit 1
fi

mkdir -p "${SNAPSHOT_ROOT}"
printf 'JOB_ID=%s\nHOST=%s\nCOMMIT=%s\n' \
  "${SLURM_JOB_ID}" "$(hostname)" "${ACTUAL_COMMIT}"
mksquashfs "${PROJECT_ROOT}" "${TEMP_ARCHIVE}" \
  -comp lz4 \
  -b 1M \
  -processors "${SLURM_CPUS_PER_TASK}" \
  -noappend \
  -no-progress \
  -e outputs approvals .pytest_cache
mv "${TEMP_ARCHIVE}" "${ARCHIVE}"
sha256sum "${ARCHIVE}" > "${ARCHIVE}.sha256"
stat -c 'ARCHIVE=%n SIZE=%s' "${ARCHIVE}"
cat "${ARCHIVE}.sha256"
