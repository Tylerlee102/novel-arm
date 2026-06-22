#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm
export PATH="/ucrt64/bin:/usr/bin:${PATH}"

TAG=${TAG:-patricia_smoke}
LIMIT=${LIMIT:-2048}
LOOKUPS=${LOOKUPS:-4096}
ROUNDS=${ROUNDS:-1}
SEED=${SEED:-0}
INPUT_FILE=${INPUT_FILE:-external/mibench_network/network/patricia/small.udp}
POLICY_LIST=${POLICY_LIST:-"none naive copper_clpd64k_peb spp spp_copper_slack"}
STAGE_COMPRESSED=${STAGE_COMPRESSED:-1}

PRE_CMD_FILE="research/results/mibench_patricia_${TAG}_guest_pre_command.sh"
CMD_FILE="research/results/mibench_patricia_${TAG}_guest_command.sh"
mkdir -p research/results
if [[ "${STAGE_COMPRESSED}" == "1" ]]; then
  {
    echo "cat > /tmp/mibench_patricia_input.udp.gz.b64 <<'B64_MIBENCH_PATRICIA_GZ'"
    gzip -c "${INPUT_FILE}" | base64
    echo "B64_MIBENCH_PATRICIA_GZ"
    echo "base64 -d /tmp/mibench_patricia_input.udp.gz.b64 > /tmp/mibench_patricia_input.udp.gz"
    echo "gzip -dc /tmp/mibench_patricia_input.udp.gz > /tmp/mibench_patricia_input.udp"
    echo "ls -l /tmp/mibench_patricia_input.udp /tmp/mibench_patricia_input.udp.gz || true"
  } > "${PRE_CMD_FILE}"
else
  {
    echo "cat > /tmp/mibench_patricia_input.b64 <<'B64_MIBENCH_PATRICIA'"
    base64 "${INPUT_FILE}"
    echo "B64_MIBENCH_PATRICIA"
    echo "base64 -d /tmp/mibench_patricia_input.b64 > /tmp/mibench_patricia_input.udp"
    echo "ls -l /tmp/mibench_patricia_input.udp || true"
  } > "${PRE_CMD_FILE}"
fi
{
  echo "/tmp/aarch64_native_workload --input /tmp/mibench_patricia_input.udp --limit ${LIMIT} --lookups ${LOOKUPS} --rounds ${ROUNDS} --seed ${SEED} || native_rc=\$?"
} > "${CMD_FILE}"

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
  --native-binary research/bin/aarch64_mibench_patricia_workload
  --native-pre-command-file "${PRE_CMD_FILE}"
  --native-shell-command-file "${CMD_FILE}"
)

run_policy() {
  local label="$1"
  shift
  local outdir="research/results/gem5_arm_ubuntu_fs_mibench_patricia_${TAG}_${label}"
  echo "COPPER_MIBENCH_PATRICIA_START ${label}"
  ./external/gem5/build/ARM/gem5.fast.exe --outdir="${outdir}" "${COMMON[@]}" "$@" \
    > "${outdir}.host.out" 2> "${outdir}.host.err"
  echo "COPPER_MIBENCH_PATRICIA_DONE ${label}"
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
