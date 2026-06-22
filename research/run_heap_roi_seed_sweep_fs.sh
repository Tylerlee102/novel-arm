#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm

TAG=n32768_p16_f4
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
  --native-arg=--passes=16
  --native-arg=--fake=32768
  --native-arg=--fake-passes=4
)

run_policy() {
  local seed_label="$1"
  local seed_value="$2"
  local label="$3"
  shift 3
  local outdir="research/results/gem5_arm_ubuntu_fs_heap_roi_${TAG}_${seed_label}_${label}"
  echo "COPPER_SEED_SWEEP_START ${seed_label} ${label}"
  ./external/gem5/build/ARM/gem5.fast.exe --outdir="${outdir}" "${COMMON[@]}" \
    --native-arg=--seed="${seed_value}" "$@" \
    > "${outdir}.host.out" 2> "${outdir}.host.err"
  echo "COPPER_SEED_SWEEP_DONE ${seed_label} ${label}"
}

for seed_spec in seed2:0x0000000000000002 seed3:0x0000000000000003; do
  seed_label="${seed_spec%%:*}"
  seed_value="${seed_spec##*:}"
  run_policy "${seed_label}" "${seed_value}" none \
    --prefetcher none --provenance-entries 16384
  run_policy "${seed_label}" "${seed_value}" naive \
    --prefetcher naive --provenance-entries 16384
  run_policy "${seed_label}" "${seed_value}" copper_clpd64k \
    --prefetcher copper --provenance-entries 65536 --line-provenance
  run_policy "${seed_label}" "${seed_value}" copper_clpd64k_peb \
    --prefetcher copper --provenance-entries 65536 --line-provenance --clear-copper-on-stats-reset
done
