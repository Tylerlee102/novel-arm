#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm

export TAG=app_stress
export ROWS=4096
export LOOKUPS=12000
export RANGES=512
export UPDATES=2048
export PAYLOAD_ROWS=4096
export POLICY_LIST="none stride naive copper_clpd64k_peb dcpt spp ampm spp_copper_slack"

bash research/run_sqlite_pointer_app_fs.sh
