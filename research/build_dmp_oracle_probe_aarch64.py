#!/usr/bin/env python3
"""Cross-build the direct DMP-oracle probe for ARM64 full-system runs."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLANGXX = ROOT / "tools" / "msys64" / "ucrt64" / "bin" / "clang++.exe"
SYSROOT = ROOT / "tools" / "arm64_ubuntu_24_sysroot"
SRC = ROOT / "research" / "aarch64_dmp_oracle_probe.cc"
M5OP = ROOT / "external" / "gem5" / "util" / "m5" / "src" / "abi" / "arm64" / "m5op.S"
OUT = ROOT / "research" / "bin" / "aarch64_dmp_oracle_probe"
LOG = ROOT / "research" / "results" / "dmp_oracle_probe_build.log"


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
        "-I",
        str(ROOT / "external" / "gem5" / "include"),
        str(SRC),
        str(M5OP),
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
