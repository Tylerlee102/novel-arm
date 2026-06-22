#!/usr/bin/env bash
set -euo pipefail

POLICIES="naive copper_clpd64k_peb spp_copper_slack"

for seed_name in seed1111 seed2222; do
  case "${seed_name}" in
    seed1111) seed=0x1111111111111111 ;;
    seed2222) seed=0x2222222222222222 ;;
    *) echo "unknown seed ${seed_name}" >&2; exit 2 ;;
  esac

  for secret in 0 1; do
    export ITEMS=512
    export PASSES=4
    export SECRET="${secret}"
    export PROBE_TARGETS=1
    export PROBE_PASSES=1
    export EVICT_KB=512
    export RESET_AFTER_EVICT=1
    export SPLIT_PROBE_STATS=1
    export SEED="${seed}"
    export TAG="i512_p4_probe1_evict512_split_${seed_name}_secret${secret}"
    export POLICY_LIST="${POLICIES}"
    bash research/run_dmp_oracle_probe_fs.sh
  done
done
