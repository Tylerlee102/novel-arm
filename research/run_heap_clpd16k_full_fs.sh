#!/usr/bin/env bash
set -euo pipefail

cd /c/Users/tyboy/OneDrive/Documents/novel-arm

exec > research/results/gem5_arm_ubuntu_fs_heap_stress_n65536_p8_copper_clpd16k.host.out
exec 2> research/results/gem5_arm_ubuntu_fs_heap_stress_n65536_p8_copper_clpd16k.host.err

./external/gem5/build/ARM/gem5.fast.exe \
  --outdir=research/results/gem5_arm_ubuntu_fs_heap_stress_n65536_p8_copper_clpd16k \
  research/gem5_arm_ubuntu_fs_copper_workload.py \
  --kernel-arg no_systemd=true \
  --switch-roi-to-timing \
  --prefetcher copper \
  --candidate-min 0x400000 \
  --candidate-max 0x0000ffffffffffff \
  --pointer-bytes 8 \
  --pointer-alignment 8 \
  --recent-entries 4096 \
  --provenance-entries 16384 \
  --value-token-bits 48 \
  --prefetch-queue-size 64 \
  --line-provenance \
  --native-only \
  --native-binary research/bin/aarch64_heap_pointer_stress \
  --native-arg=--nodes=65536 \
  --native-arg=--passes=8 \
  --native-arg=--fake=65536
