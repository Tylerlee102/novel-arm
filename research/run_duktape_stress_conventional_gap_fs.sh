#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm

TAG=app_stress \
ROWS=2048 \
LOOKUPS=4800 \
UPDATES=2048 \
TRAVERSALS=4800 \
POLICY_LIST="stride dcpt ampm" \
/usr/bin/bash research/run_duktape_object_app_fs.sh
