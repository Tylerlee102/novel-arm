#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm

export TAG=app_medium
export ROWS=1024
export LOOKUPS=2400
export UPDATES=1024
export TRAVERSALS=2400
export POLICY_LIST="none stride naive copper_clpd64k_peb dcpt spp ampm spp_copper_slack"

bash research/run_duktape_object_app_fs.sh
