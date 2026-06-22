#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm

TAG=n32768_fakeonly_f4
POLICY_LIST=${POLICY_LIST:-"none naive copper_clpd64k copper_clpd64k_peb"}
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
  --native-binary research/bin/aarch64_heap_pointer_roi_stress
  --native-arg=--nodes=32768
  --native-arg=--passes=0
  --native-arg=--fake=32768
  --native-arg=--fake-passes=4
  --native-arg=--rewrite=0
)

run_policy() {
  local label="$1"
  shift
  local outdir="research/results/gem5_arm_ubuntu_fs_heap_roi_${TAG}_${label}"
  echo "COPPER_FAKEONLY_START ${label}"
  ./external/gem5/build/ARM/gem5.fast.exe --outdir="${outdir}" "${COMMON[@]}" "$@" \
    > "${outdir}.host.out" 2> "${outdir}.host.err"
  echo "COPPER_FAKEONLY_DONE ${label}"
}

for policy in ${POLICY_LIST}; do
  case "${policy}" in
    none)
      run_policy none --prefetcher none --provenance-entries 16384
      ;;
    stride)
      run_policy stride --prefetcher stride --provenance-entries 16384
      ;;
    spp)
      run_policy spp --prefetcher spp --provenance-entries 65536
      ;;
    naive)
      run_policy naive --prefetcher naive --provenance-entries 16384
      ;;
    copper_clpd64k)
      run_policy copper_clpd64k --prefetcher copper --provenance-entries 65536 --line-provenance
      ;;
    copper_clpd64k_peb)
      run_policy copper_clpd64k_peb --prefetcher copper --provenance-entries 65536 --line-provenance --clear-copper-on-stats-reset
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
