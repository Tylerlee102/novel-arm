#!/usr/bin/env python3
"""Cross-build an OpenSSL libssl memory-BIO TLS workload for ARM64 gem5 runs."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLANG = ROOT / "tools" / "msys64" / "ucrt64" / "bin" / "clang.exe"
SYSROOT = ROOT / "tools" / "arm64_ubuntu_24_sysroot"
SRC = ROOT / "research" / "aarch64_openssl_tls_bio_workload.c"
OUT = ROOT / "research" / "bin" / "aarch64_openssl_tls_bio_workload"
LOG_DIR = ROOT / "research" / "results" / "openssl_tls_bio_workload_build"


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
        str(ROOT / "external" / "gem5" / "include"),
        str(SRC),
        str(ROOT / "external" / "gem5" / "util" / "m5" / "src" / "abi" / "arm64" / "m5op.S"),
        str(SYSROOT / "usr" / "lib" / "aarch64-linux-gnu" / "libssl.so.3"),
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
        "# OpenSSL TLS Memory-BIO Workload AArch64 Build",
        "",
        "Source: deterministic native AArch64 service-style workload that calls",
        "OpenSSL libssl's TLS 1.2 PSK handshake and record path over paired",
        "memory BIOs while maintaining session hash/LRU metadata and",
        "pointer-shaped ticket words loaded as data.",
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
    (LOG_DIR / "OPENSSL_TLS_BIO_WORKLOAD_BUILD.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(OUT)
    print(f"build_status={'PASS' if proc.returncode == 0 else 'FAIL'}")
    if proc.returncode:
        raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
