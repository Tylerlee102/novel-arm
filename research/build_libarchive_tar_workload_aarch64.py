#!/usr/bin/env python3
"""Cross-build a libarchive TAR workload for ARM64 gem5 full-system runs."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLANG = ROOT / "tools" / "msys64" / "ucrt64" / "bin" / "clang.exe"
SYSROOT = ROOT / "tools" / "arm64_ubuntu_24_sysroot"
SRC = ROOT / "research" / "aarch64_libarchive_tar_workload.c"
OUT = ROOT / "research" / "bin" / "aarch64_libarchive_tar_workload"
LOG_DIR = ROOT / "research" / "results" / "libarchive_tar_workload_build"


def lib(name: str) -> Path:
    return SYSROOT / "usr" / "lib" / "aarch64-linux-gnu" / name


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
        str(lib("libarchive.so.13.7.2")),
        str(lib("libz.so.1.3")),
        str(lib("libbz2.so.1.0.4")),
        str(lib("liblzma.so.5.4.5")),
        str(lib("liblz4.so.1.9.4")),
        str(lib("libzstd.so.1.5.5")),
        str(lib("libxml2.so.2.9.14")),
        str(lib("libcrypto.so.3")),
        str(lib("libacl.so.1.1.2302")),
        str(lib("libattr.so.1.1.2502")),
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
        "# libarchive TAR Workload AArch64 Build",
        "",
        "Source: deterministic native AArch64 workload that calls the public",
        "libarchive TAR parser through the Ubuntu ARM64 guest library stack",
        "over in-memory archive entries containing address-shaped words as data.",
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
    (LOG_DIR / "LIBARCHIVE_TAR_WORKLOAD_BUILD.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(OUT)
    print(f"build_status={'PASS' if proc.returncode == 0 else 'FAIL'}")
    if proc.returncode:
        raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
