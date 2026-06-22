#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm

export POLICY_LIST="stride dcpt ampm"

echo "COPPER_APP_BASELINE_GAP sqlite app_medium"
TAG=app_medium \
ROWS=2048 \
LOOKUPS=6000 \
RANGES=256 \
UPDATES=1024 \
PAYLOAD_ROWS=2048 \
/usr/bin/bash research/run_sqlite_pointer_app_fs.sh

echo "COPPER_APP_BASELINE_GAP sqlite app_stress"
TAG=app_stress \
ROWS=4096 \
LOOKUPS=12000 \
RANGES=512 \
UPDATES=2048 \
PAYLOAD_ROWS=4096 \
/usr/bin/bash research/run_sqlite_pointer_app_fs.sh

echo "COPPER_APP_BASELINE_GAP lua app_medium"
TAG=app_medium \
ROWS=2048 \
LOOKUPS=6000 \
UPDATES=2048 \
TRAVERSALS=6000 \
SEED=0 \
/usr/bin/bash research/run_lua_table_app_fs.sh

echo "COPPER_APP_BASELINE_GAP lua app_stress"
TAG=app_stress \
ROWS=4096 \
LOOKUPS=12000 \
UPDATES=4096 \
TRAVERSALS=12000 \
SEED=0 \
/usr/bin/bash research/run_lua_table_app_fs.sh

echo "COPPER_APP_BASELINE_GAP duktape app_medium"
TAG=app_medium \
ROWS=1024 \
LOOKUPS=2400 \
UPDATES=1024 \
TRAVERSALS=2400 \
/usr/bin/bash research/run_duktape_object_app_fs.sh

echo "COPPER_APP_BASELINE_GAP duktape app_stress"
TAG=app_stress \
ROWS=2048 \
LOOKUPS=4800 \
UPDATES=2048 \
TRAVERSALS=4800 \
/usr/bin/bash research/run_duktape_object_app_fs.sh
