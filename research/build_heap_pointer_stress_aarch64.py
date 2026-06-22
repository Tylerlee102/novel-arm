#!/usr/bin/env python3
"""Cross-build the heap-pointer stress workload for ARM64 Ubuntu gem5 runs."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLANGXX = ROOT / "tools" / "msys64" / "ucrt64" / "bin" / "clang++.exe"
SYSROOT = ROOT / "tools" / "arm64_ubuntu_24_sysroot"
SRC = ROOT / "research" / "aarch64_heap_pointer_stress.cc"
OUT = ROOT / "research" / "bin" / "aarch64_heap_pointer_stress"
LOG = ROOT / "research" / "results" / "heap_pointer_stress_build.log"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(CLANGXX),
        "--target=aarch64-linux-gnu",
        f"--sysroot={SYSROOT}",
        "-fuse-ld=lld",
        "-std=c++17",
        "-O2",
        str(SRC),
        "-o",
        str(OUT),
    ]
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    LOG.write_text(proc.stdout, encoding="utf-8")
    print(OUT)
    print(f"build_status={'PASS' if proc.returncode == 0 else 'FAIL'}")
    if proc.returncode:
        raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
