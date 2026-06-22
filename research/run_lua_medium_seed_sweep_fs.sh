#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm

for seed in 1 2; do
  export TAG="app_medium_seed${seed}"
  export ROWS=2048
  export LOOKUPS=6000
  export UPDATES=2048
  export TRAVERSALS=6000
  export SEED="${seed}"
  export POLICY_LIST="none naive copper_clpd64k_peb spp spp_copper_slack"
  /usr/bin/bash research/run_lua_table_app_fs.sh
done
