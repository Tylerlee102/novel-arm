#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm
export PATH="/ucrt64/bin:/usr/bin:${PATH}"

TAG=${TAG:-app_smoke}
SESSIONS=${SESSIONS:-128}
REQUESTS=${REQUESTS:-256}
BLOCKS=${BLOCKS:-1}
SCAN_DEPTH=${SCAN_DEPTH:-8}
ROUNDS=${ROUNDS:-1}
SEED=${SEED:-0}
POLICY_LIST=${POLICY_LIST:-"none stride naive copper_clpd64k_peb dcpt spp ampm spp_copper_slack"}
EXTRA_NATIVE_ARGS=()
if [[ "${NO_POISON:-0}" == "1" ]]; then
  EXTRA_NATIVE_ARGS+=(--native-arg=--no-poison)
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
  --native-binary research/bin/aarch64_openssl_sha_service_workload
  --native-arg=--sessions
  --native-arg="${SESSIONS}"
  --native-arg=--requests
  --native-arg="${REQUESTS}"
  --native-arg=--blocks
  --native-arg="${BLOCKS}"
  --native-arg=--scan-depth
  --native-arg="${SCAN_DEPTH}"
  --native-arg=--rounds
  --native-arg="${ROUNDS}"
  --native-arg=--seed
  --native-arg="${SEED}"
  "${EXTRA_NATIVE_ARGS[@]}"
)

run_policy() {
  local label="$1"
  shift
  local outdir="research/results/gem5_arm_ubuntu_fs_osslsha_${TAG}_${label}"
  echo "COPPER_OPENSSL_SHA_APP_START ${label}"
  ./external/gem5/build/ARM/gem5.fast.exe --outdir="${outdir}" "${COMMON[@]}" "$@" \
    > "${outdir}.host.out" 2> "${outdir}.host.err"
  echo "COPPER_OPENSSL_SHA_APP_DONE ${label}"
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
    spp)
      run_policy spp --prefetcher spp --provenance-entries 65536
      ;;
    spp_copper_slack)
      run_policy spp_copper_slack --prefetcher spp_copper_slack --provenance-entries 65536 --line-provenance --clear-copper-on-stats-reset
      ;;
    dcpt)
      run_policy dcpt --prefetcher dcpt --provenance-entries 65536
      ;;
    ampm)
      run_policy ampm --prefetcher ampm --provenance-entries 65536
      ;;
    *)
      echo "unknown policy: ${policy}" >&2
      exit 2
      ;;
  esac
done
