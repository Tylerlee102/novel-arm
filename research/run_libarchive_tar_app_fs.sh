#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm
export PATH="/ucrt64/bin:/usr/bin:${PATH}"

TAG=${TAG:-tar_tiny}
ENTRIES=${ENTRIES:-16}
ROUNDS=${ROUNDS:-1}
SCANS=${SCANS:-1}
SEED=${SEED:-0}
POLICY_LIST=${POLICY_LIST:-"none naive copper_clpd64k_peb spp spp_copper_slack"}

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
  --native-binary research/bin/aarch64_libarchive_tar_workload
  --native-arg=--entries
  --native-arg="${ENTRIES}"
  --native-arg=--rounds
  --native-arg="${ROUNDS}"
  --native-arg=--scans
  --native-arg="${SCANS}"
  --native-arg=--seed
  --native-arg="${SEED}"
)

run_policy() {
  local label="$1"
  shift
  local outdir="research/results/gem5_arm_ubuntu_fs_libarchive_${TAG}_${label}"
  echo "COPPER_LIBARCHIVE_TAR_APP_START ${label}"
  ./external/gem5/build/ARM/gem5.fast.exe --outdir="${outdir}" "${COMMON[@]}" "$@" \
    > "${outdir}.host.out" 2> "${outdir}.host.err"
  echo "COPPER_LIBARCHIVE_TAR_APP_DONE ${label}"
}

for policy in ${POLICY_LIST}; do
  case "${policy}" in
    none)
      run_policy none --prefetcher none
      ;;
    naive)
      run_policy naive --prefetcher naive --provenance-entries 65536
      ;;
    copper_clpd64k_peb)
      run_policy copper_clpd64k_peb --prefetcher copper --provenance-entries 65536 --line-provenance --clear-copper-on-stats-reset
      ;;
    spp)
      run_policy spp --prefetcher spp --provenance-entries 65536
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
