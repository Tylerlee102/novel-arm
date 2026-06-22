#!/usr/bin/env python3
"""Cross-build a yyjson-to-SQLite service-style workload for ARM64 gem5 runs."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLANG = ROOT / "tools" / "msys64" / "ucrt64" / "bin" / "clang.exe"
SYSROOT = ROOT / "tools" / "arm64_ubuntu_24_sysroot"
SQLITE = ROOT / "external" / "sqlite" / "sqlite-amalgamation-3530200"
YYJSON = ROOT / "external" / "yyjson" / "src"
SRC = ROOT / "research" / "aarch64_json_sqlite_ingest_workload.c"
OUT = ROOT / "research" / "bin" / "aarch64_json_sqlite_ingest_workload"
LOG_DIR = ROOT / "research" / "results" / "json_sqlite_ingest_workload_build"


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
        "-DYYJSON_DISABLE_WRITER=1",
        f"-I{SQLITE}",
        f"-I{YYJSON}",
        str(SRC),
        str(SQLITE / "sqlite3.c"),
        str(YYJSON / "yyjson.c"),
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
        "# JSON-to-SQLite Ingest Workload AArch64 Build",
        "",
        "Sources: public yyjson source archive and SQLite amalgamation.",
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
    (LOG_DIR / "JSON_SQLITE_INGEST_WORKLOAD_BUILD.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(OUT)
    print(f"build_status={'PASS' if proc.returncode == 0 else 'FAIL'}")
    if proc.returncode:
        raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
