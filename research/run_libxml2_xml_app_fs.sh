#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm
export PATH="/ucrt64/bin:/usr/bin:${PATH}"

TAG=${TAG:-xml_smoke}
RECORDS=${RECORDS:-64}
ROUNDS=${ROUNDS:-2}
SCAN_DEPTH=${SCAN_DEPTH:-2}
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
  --native-binary research/bin/aarch64_libxml2_xml_workload
  --native-arg=--records
  --native-arg="${RECORDS}"
  --native-arg=--rounds
  --native-arg="${ROUNDS}"
  --native-arg=--scan-depth
  --native-arg="${SCAN_DEPTH}"
  --native-arg=--seed
  --native-arg="${SEED}"
)

run_policy() {
  local label="$1"
  shift
  local outdir="research/results/gem5_arm_ubuntu_fs_libxml2_${TAG}_${label}"
  echo "COPPER_LIBXML2_XML_APP_START ${label}"
  ./external/gem5/build/ARM/gem5.fast.exe --outdir="${outdir}" "${COMMON[@]}" "$@" \
    > "${outdir}.host.out" 2> "${outdir}.host.err"
  echo "COPPER_LIBXML2_XML_APP_DONE ${label}"
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
    * )
      echo "unknown policy: ${policy}" >&2
      exit 2
      ;;
  esac
done
