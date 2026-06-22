#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm
export PATH="/ucrt64/bin:/usr/bin:${PATH}"

TAG=${TAG:-app_smoke}
SESSIONS=${SESSIONS:-16}
HANDSHAKES=${HANDSHAKES:-16}
RECORDS=${RECORDS:-1}
SCAN_DEPTH=${SCAN_DEPTH:-4}
ROUNDS=${ROUNDS:-1}
SEED=${SEED:-0}
POLICY_LIST=${POLICY_LIST:-"none stride naive copper_clpd64k_peb dcpt spp ampm spp_copper_slack"}
EXTRA_NATIVE_ARGS=()
if [[ "${NO_POISON:-0}" == "1" ]]; then
  EXTRA_NATIVE_ARGS+=(--native-arg=--no-poison)
fi
if [[ "${STRICT_TCP:-0}" == "1" ]]; then
  EXTRA_NATIVE_ARGS+=(--native-arg=--strict-tcp)
fi
if [[ "${PROCESS_SERVER:-0}" == "1" ]]; then
  EXTRA_NATIVE_ARGS+=(--native-arg=--process-server)
fi
if [[ "${NO_NETNS_LOOPBACK:-0}" == "1" ]]; then
  EXTRA_NATIVE_ARGS+=(--native-arg=--no-netns-loopback)
fi
if [[ -n "${EXTRA_TCP_ARGS:-}" ]]; then
  # shellcheck disable=SC2206
  EXTRA_TCP_ARG_WORDS=(${EXTRA_TCP_ARGS})
  for arg in "${EXTRA_TCP_ARG_WORDS[@]}"; do
    EXTRA_NATIVE_ARGS+=(--native-arg="${arg}")
  done
fi
NATIVE_PRE_COMMAND_ARGS=()
if [[ -n "${NATIVE_PRE_COMMAND:-}" ]]; then
  NATIVE_PRE_COMMAND_ARGS+=(--native-pre-command="${NATIVE_PRE_COMMAND}")
fi
if [[ -n "${TCP_PRE_COMMAND:-}" ]]; then
  NATIVE_PRE_COMMAND_ARGS+=(--native-pre-command="${TCP_PRE_COMMAND}")
fi
KERNEL_ARG_ARGS=()
if [[ "${NO_SYSTEMD:-1}" == "1" ]]; then
  KERNEL_ARG_ARGS+=(--kernel-arg no_systemd=true)
fi
if [[ -n "${EXTRA_KERNEL_ARG:-}" ]]; then
  KERNEL_ARG_ARGS+=(--kernel-arg "${EXTRA_KERNEL_ARG}")
fi

COMMON=(
  research/gem5_arm_ubuntu_fs_copper_workload.py
  "${KERNEL_ARG_ARGS[@]}"
  --switch-roi-to-timing
  --candidate-min 0x400000
  --candidate-max 0x0000ffffffffffff
  --pointer-bytes 8
  --pointer-alignment 8
  --recent-entries 4096
  --value-token-bits 48
  --prefetch-queue-size 64
  --native-self-roi
  --native-only
  --native-binary research/bin/aarch64_openssl_tls_tcp_workload
  --native-arg=--sessions
  --native-arg="${SESSIONS}"
  --native-arg=--handshakes
  --native-arg="${HANDSHAKES}"
  --native-arg=--records
  --native-arg="${RECORDS}"
  --native-arg=--scan-depth
  --native-arg="${SCAN_DEPTH}"
  --native-arg=--rounds
  --native-arg="${ROUNDS}"
  --native-arg=--seed
  --native-arg="${SEED}"
  "${EXTRA_NATIVE_ARGS[@]}"
  "${NATIVE_PRE_COMMAND_ARGS[@]}"
)

run_policy() {
  local label="$1"
  shift
  local outdir="research/results/gem5_arm_ubuntu_fs_ossltlstcp_${TAG}_${label}"
  echo "COPPER_OPENSSL_TLS_TCP_APP_START ${label}"
  ./external/gem5/build/ARM/gem5.fast.exe --outdir="${outdir}" "${COMMON[@]}" "$@" \
    > "${outdir}.host.out" 2> "${outdir}.host.err"
  echo "COPPER_OPENSSL_TLS_TCP_APP_DONE ${label}"
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
    dcpt)
      run_policy dcpt --prefetcher dcpt --provenance-entries 65536
      ;;
    spp)
      run_policy spp --prefetcher spp --provenance-entries 65536
      ;;
    ampm)
      run_policy ampm --prefetcher ampm --provenance-entries 65536
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

