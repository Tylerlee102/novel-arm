#!/usr/bin/env python3
"""Cross-build an OpenSSL SHA256 service workload for ARM64 gem5 runs."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLANG = ROOT / "tools" / "msys64" / "ucrt64" / "bin" / "clang.exe"
SYSROOT = ROOT / "tools" / "arm64_ubuntu_24_sysroot"
SRC = ROOT / "research" / "aarch64_openssl_sha_service_workload.c"
OUT = ROOT / "research" / "bin" / "aarch64_openssl_sha_service_workload"
LOG_DIR = ROOT / "research" / "results" / "openssl_sha_service_workload_build"


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
        str(SRC),
        str(SYSROOT / "usr" / "lib" / "aarch64-linux-gnu" / "libcrypto.so.3"),
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
        "# OpenSSL SHA Service Workload AArch64 Build",
        "",
        "Source: deterministic native AArch64 service-style workload that calls",
        "OpenSSL libcrypto's exported SHA256 routine while maintaining session",
        "hash/LRU metadata and pointer-shaped ticket words loaded as data.",
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
    (LOG_DIR / "OPENSSL_SHA_SERVICE_WORKLOAD_BUILD.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(OUT)
    print(f"build_status={'PASS' if proc.returncode == 0 else 'FAIL'}")
    if proc.returncode:
        raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
