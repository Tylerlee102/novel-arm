#!/usr/bin/env bash
set -euo pipefail

for seed in 1 2; do
  export TAG="app_small_seed${seed}"
  export ROWS=1024
  export LOOKUPS=3000
  export UPDATES=1024
  export TRAVERSALS=3000
  export SEED="${seed}"
  export POLICY_LIST="none naive copper_clpd64k_peb spp spp_copper_slack"
  bash research/run_lua_table_app_fs.sh
done
