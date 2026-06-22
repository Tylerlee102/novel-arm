#!/usr/bin/env python3
"""Cross-build a yyjson service-style workload for ARM64 gem5 full-system runs."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLANG = ROOT / "tools" / "msys64" / "ucrt64" / "bin" / "clang.exe"
SYSROOT = ROOT / "tools" / "arm64_ubuntu_24_sysroot"
YYJSON = ROOT / "external" / "yyjson" / "src"
SRC = ROOT / "research" / "aarch64_yyjson_workload.c"
OUT = ROOT / "research" / "bin" / "aarch64_yyjson_workload"
LOG_DIR = ROOT / "research" / "results" / "yyjson_workload_build"


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
        "-DYYJSON_DISABLE_WRITER=1",
        f"-I{YYJSON}",
        str(SRC),
        str(YYJSON / "yyjson.c"),
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
        "# yyjson Workload AArch64 Build",
        "",
        "Source: public yyjson source archive from github.com/ibireme/yyjson.",
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
    (LOG_DIR / "YYJSON_WORKLOAD_BUILD.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(OUT)
    print(f"build_status={'PASS' if proc.returncode == 0 else 'FAIL'}")
    if proc.returncode:
        raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
