#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm

POLICIES=(none naive copper_clpd64k_peb spp spp_copper_slack)
SEED=1

run_sqlite_policy() {
  local policy="$1"
  local tag="app_stress_seed${SEED}"
  local outdir="research/results/gem5_arm_ubuntu_fs_sqlite_${tag}_${policy}"
  if [[ -s "${outdir}.host.out" && -s "${outdir}/stats.txt" ]]; then
    echo "COPPER_PUBLIC_APP_STRESS_SKIP sqlite seed=${SEED} policy=${policy}"
    return
  fi
  echo "COPPER_PUBLIC_APP_STRESS_RUN sqlite seed=${SEED} policy=${policy}"
  TAG="${tag}" \
  ROWS=4096 \
  LOOKUPS=12000 \
  RANGES=512 \
  UPDATES=2048 \
  PAYLOAD_ROWS=4096 \
  SEED="${SEED}" \
  POLICY_LIST="${policy}" \
  /usr/bin/bash research/run_sqlite_pointer_app_fs.sh
}

run_lua_policy() {
  local policy="$1"
  local tag="app_stress_seed${SEED}"
  local outdir="research/results/gem5_arm_ubuntu_fs_lua_${tag}_${policy}"
  if [[ -s "${outdir}.host.out" && -s "${outdir}/stats.txt" ]]; then
    echo "COPPER_PUBLIC_APP_STRESS_SKIP lua seed=${SEED} policy=${policy}"
    return
  fi
  echo "COPPER_PUBLIC_APP_STRESS_RUN lua seed=${SEED} policy=${policy}"
  TAG="${tag}" \
  ROWS=4096 \
  LOOKUPS=12000 \
  UPDATES=4096 \
  TRAVERSALS=12000 \
  SEED="${SEED}" \
  POLICY_LIST="${policy}" \
  /usr/bin/bash research/run_lua_table_app_fs.sh
}

run_duktape_policy() {
  local policy="$1"
  local tag="app_stress_seed${SEED}"
  local outdir="research/results/gem5_arm_ubuntu_fs_duktape_${tag}_${policy}"
  if [[ -s "${outdir}.host.out" && -s "${outdir}/stats.txt" ]]; then
    echo "COPPER_PUBLIC_APP_STRESS_SKIP duktape seed=${SEED} policy=${policy}"
    return
  fi
  echo "COPPER_PUBLIC_APP_STRESS_RUN duktape seed=${SEED} policy=${policy}"
  TAG="${tag}" \
  ROWS=2048 \
  LOOKUPS=4800 \
  UPDATES=2048 \
  TRAVERSALS=4800 \
  SEED="${SEED}" \
  POLICY_LIST="${policy}" \
  /usr/bin/bash research/run_duktape_object_app_fs.sh
}

for policy in "${POLICIES[@]}"; do
  run_sqlite_policy "${policy}"
done
for policy in "${POLICIES[@]}"; do
  run_lua_policy "${policy}"
done
for policy in "${POLICIES[@]}"; do
  run_duktape_policy "${policy}"
done
