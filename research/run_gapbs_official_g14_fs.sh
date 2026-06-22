#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm

SCALE=${SCALE:-14}
DEGREE=${DEGREE:-8}
TAG=${TAG:-suite_g14}
POLICY_LIST=${POLICY_LIST:-"none naive copper"}
KERNELS=(bfs cc pr sssp)

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
  --official-gapbs-suite
  --official-gapbs-scale "${SCALE}"
  --official-gapbs-degree "${DEGREE}"
  --official-gapbs-kernels "${KERNELS[@]}"
)

run_policy() {
  local label="$1"
  shift
  local outdir="research/results/gem5_arm_ubuntu_fs_gapbs_official_${TAG}_${label}"
  echo "COPPER_GAPBS_OFFICIAL_G14_START ${label}"
  ./external/gem5/build/ARM/gem5.fast.exe --outdir="${outdir}" "${COMMON[@]}" "$@" \
    > "${outdir}.host.out" 2> "${outdir}.host.err"
  echo "COPPER_GAPBS_OFFICIAL_G14_DONE ${label}"
}

for policy in ${POLICY_LIST}; do
  case "${policy}" in
    none)
      run_policy none --prefetcher none --provenance-entries 65536
      ;;
    naive)
      run_policy naive --prefetcher naive --provenance-entries 65536
      ;;
    copper)
      run_policy copper --prefetcher copper --provenance-entries 65536
      ;;
    copper_clpd64k_peb)
      run_policy copper_clpd64k_peb --prefetcher copper --provenance-entries 65536 --line-provenance --clear-copper-on-stats-reset
      ;;
    *)
      echo "unknown policy: ${policy}" >&2
      exit 2
      ;;
  esac
done
