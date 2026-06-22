#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm

TAG=n32768_p12_b2048_f3
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
  --native-binary research/bin/aarch64_pointer_structure_mix
  --native-arg=--nodes=32768
  --native-arg=--passes=12
  --native-arg=--buckets=2048
  --native-arg=--fake-passes=3
)

run_policy() {
  local label="$1"
  shift
  local outdir="research/results/gem5_arm_ubuntu_fs_struct_mix_${TAG}_${label}"
  echo "COPPER_STRUCT_MIX_START ${label}"
  ./external/gem5/build/ARM/gem5.fast.exe --outdir="${outdir}" "${COMMON[@]}" "$@" \
    > "${outdir}.host.out" 2> "${outdir}.host.err"
  echo "COPPER_STRUCT_MIX_DONE ${label}"
}

run_policy none --prefetcher none --provenance-entries 16384
run_policy naive --prefetcher naive --provenance-entries 16384
run_policy copper_clpd64k --prefetcher copper --provenance-entries 65536 --line-provenance
