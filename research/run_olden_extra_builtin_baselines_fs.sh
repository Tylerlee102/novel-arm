#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm

TAG=${TAG:-suite4_randomalloc}
OLDEN_BIN_DIR=${OLDEN_BIN_DIR:-research/bin/olden_aarch64_random_alloc}
OLDEN_SIZE=${OLDEN_SIZE:-small}
if [[ -n "${OLDEN_KERNELS:-}" ]]; then
  read -r -a KERNELS <<< "${OLDEN_KERNELS}"
else
  KERNELS=(treeadd bisort mst health)
fi
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
  --olden-suite
  --olden-size "${OLDEN_SIZE}"
  --olden-bin-dir "${OLDEN_BIN_DIR}"
  --olden-kernels "${KERNELS[@]}"
)

run_policy() {
  local label="$1"
  shift
  local outdir="research/results/gem5_arm_ubuntu_fs_olden_${TAG}_${label}"
  echo "COPPER_OLDEN_EXTRA_BUILTIN_BASELINE_START ${label}"
  ./external/gem5/build/ARM/gem5.fast.exe --outdir="${outdir}" "${COMMON[@]}" "$@" \
    > "${outdir}.host.out" 2> "${outdir}.host.err"
  echo "COPPER_OLDEN_EXTRA_BUILTIN_BASELINE_DONE ${label}"
}

run_policy ampm --prefetcher ampm --provenance-entries 65536
run_policy indirect --prefetcher indirect --provenance-entries 65536
run_policy isb --prefetcher isb --provenance-entries 65536
