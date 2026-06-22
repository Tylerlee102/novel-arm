#!/usr/bin/env python3
"""Cross-build a PCRE2 regex workload for ARM64 gem5 full-system runs."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLANG = ROOT / "tools" / "msys64" / "ucrt64" / "bin" / "clang.exe"
SYSROOT = ROOT / "tools" / "arm64_ubuntu_24_sysroot"
SRC = ROOT / "research" / "aarch64_pcre2_regex_workload.c"
OUT = ROOT / "research" / "bin" / "aarch64_pcre2_regex_workload"
LOG_DIR = ROOT / "research" / "results" / "pcre2_regex_workload_build"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    lib = SYSROOT / "usr" / "lib" / "aarch64-linux-gnu" / "libpcre2-8.so.0.11.2"
    cmd = [
        str(CLANG),
        "--target=aarch64-linux-gnu",
        f"--sysroot={SYSROOT}",
        "-fuse-ld=lld",
        "-O2",
        "-DNDEBUG",
        str(SRC),
        str(lib),
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
        "# PCRE2 Regex Workload AArch64 Build",
        "",
        "Source: deterministic native AArch64 workload that calls the public",
        "PCRE2 8-bit regex compiler and matcher through the Ubuntu ARM64",
        "guest library stack while scanning log-like records containing",
        "address-shaped ticket words loaded as data.",
        "",
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
    (LOG_DIR / "PCRE2_REGEX_WORKLOAD_BUILD.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(OUT)
    print(f"build_status={'PASS' if proc.returncode == 0 else 'FAIL'}")
    if proc.returncode:
        raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
