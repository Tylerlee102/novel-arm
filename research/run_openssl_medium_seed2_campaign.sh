#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm

export TAG=app_medium_seed2
export SESSIONS=128
export REQUESTS=128
export CRYPTO_ROUNDS=2
export SCAN_DEPTH=8
export ROUNDS=1
export SEED=2
export POLICY_LIST="none naive copper_clpd64k_peb spp spp_copper_slack"
bash research/run_openssl_crypto_suite_fs.sh

export TAG=app_medium_seed2
export SESSIONS=32
export HANDSHAKES=32
export RECORDS=2
export SCAN_DEPTH=8
export ROUNDS=1
export SEED=2
export POLICY_LIST="none naive copper_clpd64k_peb spp spp_copper_slack"
bash research/run_openssl_tls_bio_fs.sh
