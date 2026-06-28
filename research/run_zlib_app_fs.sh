#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "${SCRIPT_DIR}/.."
export PATH="/ucrt64/bin:/usr/bin:${PATH}"

TAG=${TAG:-app_smoke}
BYTES=${BYTES:-8192}
ROUNDS=${ROUNDS:-2}
SEED=${SEED:-0}
LEVEL=${LEVEL:-1}
POLICY_LIST=${POLICY_LIST:-"none stride naive copper_clpd64k_peb dcpt spp ampm spp_copper_slack"}

COMMON=(
  research/gem5_arm_ubuntu_fs_copper_workload.py
  --kernel-arg no_systemd=true
  --switch-roi-to-timing
  --candidate-min 0x400000
  --candidate-max 0x0000ffffffffffff
  --pointer-bytes 8
  --pointer-alignment 8
  --recent-entries 4096
  --value-token-bits 48
  --prefetch-queue-size 64
  --native-only
  --native-binary research/bin/aarch64_zlib_workload
  --native-arg=--bytes
  --native-arg="${BYTES}"
  --native-arg=--rounds
  --native-arg="${ROUNDS}"
  --native-arg=--seed
  --native-arg="${SEED}"
  --native-arg=--level
  --native-arg="${LEVEL}"
)

run_policy() {
  local label="$1"
  shift
  local outdir="research/results/gem5_arm_ubuntu_fs_zlib_${TAG}_${label}"
  echo "COPPER_ZLIB_APP_START ${label}"
  ./external/gem5/build/ARM/gem5.fast.exe --outdir="${outdir}" "${COMMON[@]}" "$@" \
    > "${outdir}.host.out" 2> "${outdir}.host.err"
  echo "COPPER_ZLIB_APP_DONE ${label}"
}

for policy in ${POLICY_LIST}; do
  case "${policy}" in
    none)
      run_policy none --prefetcher none
      ;;
    stride)
      run_policy stride --prefetcher stride
      ;;
    naive)
      run_policy naive --prefetcher naive --provenance-entries 65536
      ;;
    copper_clpd64k_peb)
      run_policy copper_clpd64k_peb --prefetcher copper --provenance-entries 65536 --line-provenance --clear-copper-on-stats-reset
      ;;
    dcpt)
      run_policy dcpt --prefetcher dcpt --provenance-entries 65536
      ;;
    spp)
      run_policy spp --prefetcher spp --provenance-entries 65536
      ;;
    ampm)
      run_policy ampm --prefetcher ampm --provenance-entries 65536
      ;;
    spp_copper_slack)
      run_policy spp_copper_slack --prefetcher spp_copper_slack --provenance-entries 65536 --line-provenance --clear-copper-on-stats-reset
      ;;
    *)
      echo "unknown policy: ${policy}" >&2
      exit 2
      ;;
  esac
done
