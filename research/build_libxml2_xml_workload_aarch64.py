#!/usr/bin/env python3
"""Cross-build a libxml2 XML workload for ARM64 gem5 full-system runs."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLANG = ROOT / "tools" / "msys64" / "ucrt64" / "bin" / "clang.exe"
SYSROOT = ROOT / "tools" / "arm64_ubuntu_24_sysroot"
LIBXML2_INCLUDE = ROOT / "tools" / "msys64" / "ucrt64" / "include" / "libxml2"
SRC = ROOT / "research" / "aarch64_libxml2_xml_workload.c"
OUT = ROOT / "research" / "bin" / "aarch64_libxml2_xml_workload"
LOG_DIR = ROOT / "research" / "results" / "libxml2_xml_workload_build"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    libxml2 = SYSROOT / "usr" / "lib" / "aarch64-linux-gnu" / "libxml2.so.2.9.14"
    libz = SYSROOT / "usr" / "lib" / "aarch64-linux-gnu" / "libz.so.1.3"
    liblzma = SYSROOT / "usr" / "lib" / "aarch64-linux-gnu" / "liblzma.so.5.4.5"
    libm = SYSROOT / "usr" / "lib" / "aarch64-linux-gnu" / "libm.so.6"
    cmd = [
        str(CLANG),
        "--target=aarch64-linux-gnu",
        f"--sysroot={SYSROOT}",
        "-fuse-ld=lld",
        "-O2",
        "-DNDEBUG",
        f"-I{LIBXML2_INCLUDE}",
        str(SRC),
        str(libxml2),
        str(libz),
        str(liblzma),
        str(libm),
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
        "# libxml2 XML Workload AArch64 Build",
        "",
        "Source: deterministic native AArch64 workload that calls the public",
        "libxml2 XML parser and serializer through the Ubuntu ARM64 guest",
        "library stack over XML records containing address-shaped words as data.",
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
    (LOG_DIR / "LIBXML2_XML_WORKLOAD_BUILD.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(OUT)
    print(f"build_status={'PASS' if proc.returncode == 0 else 'FAIL'}")
    if proc.returncode:
        raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
