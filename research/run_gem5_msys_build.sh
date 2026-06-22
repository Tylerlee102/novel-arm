#!/usr/bin/env bash
set -euo pipefail

export PATH=/usr/bin:$PATH
cd /c/Users/tyboy/OneDrive/Documents/novel-arm/external/gem5
exec scons build/ARM/gem5.opt -j6
