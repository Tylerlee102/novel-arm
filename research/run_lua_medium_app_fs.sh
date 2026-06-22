#!/usr/bin/env bash
set -euo pipefail

export TAG=app_medium
export ROWS=2048
export LOOKUPS=6000
export UPDATES=2048
export TRAVERSALS=6000
export POLICY_LIST="none stride naive copper_clpd64k_peb dcpt spp ampm spp_copper_slack"

bash research/run_lua_table_app_fs.sh
