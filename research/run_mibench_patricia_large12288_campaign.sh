#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm

export TAG=patricia_large12288
export LIMIT=12288
export LOOKUPS=24576
export ROUNDS=1
export SEED=0
export INPUT_FILE=external/mibench_network/network/patricia/large.udp
export POLICY_LIST="none naive copper_clpd64k_peb spp spp_copper_slack"
export STAGE_COMPRESSED=1

bash research/run_mibench_patricia_fs.sh
