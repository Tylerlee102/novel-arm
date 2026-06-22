#!/usr/bin/env python3
"""Cross-build the MiBench Patricia trie workload for ARM64 gem5 FS runs."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLANG = ROOT / "tools" / "msys64" / "ucrt64" / "bin" / "clang.exe"
SYSROOT = ROOT / "tools" / "arm64_ubuntu_24_sysroot"
MIBENCH_DIR = ROOT / "external" / "mibench_network" / "network" / "patricia"
SRC = ROOT / "research" / "aarch64_mibench_patricia_workload.c"
OUT = ROOT / "research" / "bin" / "aarch64_mibench_patricia_workload"
LOG_DIR = ROOT / "research" / "results" / "mibench_patricia_workload_build"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(CLANG),
        "--target=aarch64-linux-gnu",
        f"--sysroot={SYSROOT}",
        "-fuse-ld=lld",
        "-O2",
        "-DNDEBUG",
        "-I",
        str(MIBENCH_DIR),
        str(SRC),
        str(MIBENCH_DIR / "patricia.c"),
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
    (LOG_DIR / "build.log").write_text(proc.stdout, encoding="utf-8")
    lines = [
        "# MiBench Patricia Workload AArch64 Build",
        "",
        "Source: deterministic native AArch64 workload using the public",
        "MiBench network/patricia Patricia trie implementation and the",
        "MiBench `small.udp` packet-field input. The driver adds checksum",
        "and return-code reporting for gem5 full-system evaluation.",
        "",
        "Public source archive: `external/mibench_download/network.tar.gz`.",
        f"MiBench source directory: `{MIBENCH_DIR}`.",
        f"Binary: `{OUT}`",
        "",
        "Build command:",
        "",
        "```text",
        " ".join(str(item) for item in cmd),
        "```",
        "",
        f"build_status={'PASS' if proc.returncode == 0 else 'FAIL'}",
        "",
    ]
    (LOG_DIR / "MIBENCH_PATRICIA_WORKLOAD_BUILD.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(OUT)
    print(f"build_status={'PASS' if proc.returncode == 0 else 'FAIL'}")
    if proc.returncode:
        raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
