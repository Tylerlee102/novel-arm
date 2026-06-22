#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm

ITEMS=${ITEMS:-8192}
PASSES=${PASSES:-4}
SECRET=${SECRET:-0}
PROBE_TARGETS=${PROBE_TARGETS:-0}
PROBE_PASSES=${PROBE_PASSES:-1}
EVICT_KB=${EVICT_KB:-0}
RESET_AFTER_EVICT=${RESET_AFTER_EVICT:-1}
SPLIT_PROBE_STATS=${SPLIT_PROBE_STATS:-0}
SEED=${SEED:-0x243f6a8885a308d3}
if [[ "${PROBE_TARGETS}" == "1" ]]; then
  TAG=${TAG:-i${ITEMS}_p${PASSES}_probe${PROBE_PASSES}_evict${EVICT_KB}_secret${SECRET}}
else
  TAG=${TAG:-i${ITEMS}_p${PASSES}_secret${SECRET}}
fi
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
  --native-binary research/bin/aarch64_dmp_oracle_probe
  --native-arg=--items=${ITEMS}
  --native-arg=--passes=${PASSES}
  --native-arg=--secret=${SECRET}
  --native-arg=--probe-targets=${PROBE_TARGETS}
  --native-arg=--probe-passes=${PROBE_PASSES}
  --native-arg=--evict-kb=${EVICT_KB}
  --native-arg=--reset-after-evict=${RESET_AFTER_EVICT}
  --native-arg=--split-probe-stats=${SPLIT_PROBE_STATS}
  --native-arg=--seed=${SEED}
)

run_policy() {
  local label="$1"
  shift
  local outdir="research/results/gem5_arm_ubuntu_fs_dmp_oracle_${TAG}_${label}"
  echo "DMP_ORACLE_START ${TAG} ${label}"
  ./external/gem5/build/ARM/gem5.fast.exe --outdir="${outdir}" "${COMMON[@]}" "$@" \
    > "${outdir}.host.out" 2> "${outdir}.host.err"
  echo "DMP_ORACLE_DONE ${TAG} ${label}"
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
