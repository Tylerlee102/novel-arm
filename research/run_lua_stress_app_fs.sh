#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm

export TAG=app_stress
export ROWS=4096
export LOOKUPS=12000
export UPDATES=4096
export TRAVERSALS=12000
export POLICY_LIST="none stride naive copper_clpd64k_peb dcpt spp ampm spp_copper_slack"

bash research/run_lua_table_app_fs.sh
