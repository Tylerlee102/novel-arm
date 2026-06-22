#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm

export TAG=app_stress
export ROWS=2048
export LOOKUPS=4800
export UPDATES=2048
export TRAVERSALS=4800
export POLICY_LIST="none stride naive copper_clpd64k_peb dcpt spp ampm spp_copper_slack"

bash research/run_duktape_object_app_fs.sh
