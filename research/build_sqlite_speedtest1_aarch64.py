#!/usr/bin/env python3
"""Cross-build upstream SQLite speedtest1 for ARM64 gem5 full-system runs."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLANG = ROOT / "tools" / "msys64" / "ucrt64" / "bin" / "clang.exe"
SYSROOT = ROOT / "tools" / "arm64_ubuntu_24_sysroot"
SQLITE_AMALGAMATION = ROOT / "external" / "sqlite" / "sqlite-amalgamation-3530200"
SQLITE_SOURCE = ROOT / "external" / "sqlite" / "sqlite-src-3530200"
SRC = SQLITE_SOURCE / "test" / "speedtest1.c"
OUT = ROOT / "research" / "bin" / "aarch64_sqlite_speedtest1"
LOG_DIR = ROOT / "research" / "results" / "sqlite_speedtest1_build"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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
        "-DSQLITE_THREADSAFE=0",
        "-DSQLITE_OMIT_LOAD_EXTENSION",
        "-DSQLITE_DEFAULT_MEMSTATUS=0",
        "-DSQLITE_ENABLE_RTREE",
        f"-I{SQLITE_AMALGAMATION}",
        str(SRC),
        str(SQLITE_AMALGAMATION / "sqlite3.c"),
        "-lm",
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
        "# SQLite speedtest1 AArch64 Build",
        "",
        "Purpose: build upstream SQLite speedtest1 as a native AArch64 Linux",
        "binary for gem5 full-system COPPER policy comparisons.",
        "",
        "Source:",
        "",
        "- SQLite release: 3.53.2.",
        "- Upstream source archive: `sqlite-src-3530200.zip`.",
        "- Benchmark source: `external/sqlite/sqlite-src-3530200/test/speedtest1.c`.",
        "- SQLite amalgamation: `external/sqlite/sqlite-amalgamation-3530200/sqlite3.c`.",
        "",
        "Hashes:",
        "",
        f"- `speedtest1.c` SHA-256: `{sha256(SRC)}`",
        f"- `sqlite3.c` SHA-256: `{sha256(SQLITE_AMALGAMATION / 'sqlite3.c')}`",
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
    (LOG_DIR / "SQLITE_SPEEDTEST1_AARCH64_BUILD.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(OUT)
    print(f"build_status={'PASS' if proc.returncode == 0 else 'FAIL'}")
    if proc.returncode:
        raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
