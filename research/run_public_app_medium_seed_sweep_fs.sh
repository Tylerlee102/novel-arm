#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm

POLICIES="none naive copper_clpd64k_peb spp spp_copper_slack"

for seed in 1 2; do
  echo "COPPER_PUBLIC_APP_MEDIUM_SEED sqlite seed=${seed}"
  TAG="app_medium_seed${seed}" \
  ROWS=2048 \
  LOOKUPS=6000 \
  RANGES=256 \
  UPDATES=1024 \
  PAYLOAD_ROWS=2048 \
  SEED="${seed}" \
  POLICY_LIST="${POLICIES}" \
  /usr/bin/bash research/run_sqlite_pointer_app_fs.sh

  echo "COPPER_PUBLIC_APP_MEDIUM_SEED duktape seed=${seed}"
  TAG="app_medium_seed${seed}" \
  ROWS=1024 \
  LOOKUPS=2400 \
  UPDATES=1024 \
  TRAVERSALS=2400 \
  SEED="${seed}" \
  POLICY_LIST="${POLICIES}" \
  /usr/bin/bash research/run_duktape_object_app_fs.sh
done
