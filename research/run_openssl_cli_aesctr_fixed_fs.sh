#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm
export PATH="/ucrt64/bin:/usr/bin:${PATH}"

TAG=${TAG:-aesctr_64k}
INPUT_BYTES=${INPUT_BYTES:-65536}
SEED=${SEED:-0}
INPUT_PATH=${INPUT_PATH:-/tmp/openssl_cli_input.bin}
OUTPUT_PATH=${OUTPUT_PATH:-/tmp/openssl_cli_aesctr_output.bin}
KEY_HEX=${KEY_HEX:-00112233445566778899aabbccddeeff}
IV_HEX=${IV_HEX:-0102030405060708090a0b0c0d0e0f10}
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
  --native-binary research/bin/aarch64_ubuntu_openssl_cli
  --native-preload-pointer-file
  --native-preload-path "${INPUT_PATH}"
  --native-preload-bytes "${INPUT_BYTES}"
  --native-preload-seed "${SEED}"
  --native-arg=enc
  --native-arg=-aes-128-ctr
  --native-arg=-K
  --native-arg="${KEY_HEX}"
  --native-arg=-iv
  --native-arg="${IV_HEX}"
  --native-arg=-in
  --native-arg="${INPUT_PATH}"
  --native-arg=-out
  --native-arg="${OUTPUT_PATH}"
  --native-after-arg=dgst
  --native-after-arg=-sha256
  --native-after-arg="${OUTPUT_PATH}"
)

run_policy() {
  local label="$1"
  shift
  local outdir="research/results/gem5_arm_ubuntu_fs_osslcli_${TAG}_${label}"
  echo "COPPER_OPENSSL_CLI_AESCTR_START ${label}"
  ./external/gem5/build/ARM/gem5.fast.exe --outdir="${outdir}" "${COMMON[@]}" "$@" \
    > "${outdir}.host.out" 2> "${outdir}.host.err"
  echo "COPPER_OPENSSL_CLI_AESCTR_DONE ${label}"
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
