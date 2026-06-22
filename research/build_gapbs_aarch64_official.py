#!/usr/bin/env python3
"""Cross-build official GAPBS kernels for ARM64 Ubuntu gem5 full-system runs."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLANGXX = ROOT / "tools" / "msys64" / "ucrt64" / "bin" / "clang++.exe"
SYSROOT = ROOT / "tools" / "arm64_ubuntu_24_sysroot"
GAPBS_SRC = ROOT / "external" / "gapbs" / "src"
OUT_DIR = ROOT / "research" / "bin" / "gapbs_aarch64_official"
LOG_DIR = ROOT / "research" / "results" / "gapbs_aarch64_official_build"


KERNELS = ("bfs", "cc", "pr", "sssp", "bc", "tc")


def build_kernel(kernel: str) -> tuple[bool, str]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / kernel
    cmd = [
        str(CLANGXX),
        "--target=aarch64-linux-gnu",
        f"--sysroot={SYSROOT}",
        "-fuse-ld=lld",
        "-std=c++11",
        "-O2",
        "-DSERIAL=1",
        "-Wno-unknown-pragmas",
        f"-I{GAPBS_SRC}",
        str(GAPBS_SRC / f"{kernel}.cc"),
        "-o",
        str(out),
    ]
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    log = LOG_DIR / f"{kernel}.log"
    log.write_text(proc.stdout, encoding="utf-8")
    return proc.returncode == 0, proc.stdout


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kernels", nargs="*", default=list(KERNELS))
    args = parser.parse_args()

    failures = 0
    lines = [
        "# Official GAPBS AArch64 Build",
        "",
        "This build uses the unmodified public GAPBS kernel sources under",
        "`external/gapbs/src`, the extracted ARM64 Ubuntu 24.04 sysroot from the",
        "gem5 disk image, MSYS clang++, and LLVM lld.",
        "",
        "| Kernel | Status | Binary | Log |",
        "|---|---|---|---|",
    ]
    for kernel in args.kernels:
        ok, _ = build_kernel(kernel)
        if not ok:
            failures += 1
        lines.append(
            f"| {kernel} | {'PASS' if ok else 'FAIL'} | "
            f"`{OUT_DIR / kernel}` | `{LOG_DIR / (kernel + '.log')}` |"
        )

    lines.extend(
        [
            "",
            f"build_status={'PASS' if failures == 0 else 'FAIL'}",
            "",
        ]
    )
    summary = LOG_DIR / "GAPBS_AARCH64_OFFICIAL_BUILD.md"
    summary.write_text("\n".join(lines), encoding="utf-8")
    print(summary)
    print(f"build_status={'PASS' if failures == 0 else 'FAIL'}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
