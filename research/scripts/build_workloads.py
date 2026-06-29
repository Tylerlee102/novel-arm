#!/usr/bin/env python3
"""Build the public COPPER C workload suite from source.

This script records one ledger row per required workload. A PASS row means the
binary was produced by the compiler command captured in the log. If no compiler
is available, rows are NOT_ATTEMPTED with the exact blocker in notes.
"""

from __future__ import annotations

import csv
import hashlib
import os
import platform
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "research"
RESULTS = RESEARCH / "results"
WORKLOADS = RESEARCH / "workloads"
BIN_DIR = RESEARCH / "bin" / "workloads"
LOG_DIR = RESULTS / "logs" / "workloads"
OUT = RESULTS / "workload_build.csv"
SOURCE = WORKLOADS / "copper_workload_suite.c"
BENCHMARKS = (
    "linked_list",
    "tree_traversal",
    "hash_table_chaining",
    "graph_adjacency_walk",
    "patricia",
    "array_scan",
    "matrix_or_array_loop",
    "compute_heavy_low_memory",
    "random_non_pointer_access",
    "short_pointer_chains",
    "long_pointer_chains",
    "mixed_pointer_array",
    "noisy_allocation_pattern",
    "branchy_pointer_chains",
)


def current_environment() -> str:
    override = os.environ.get("COPPER_ENVIRONMENT", "").strip()
    if override:
        return override
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        return "github_actions"
    if os.environ.get("CODESPACES", "").lower() == "true":
        return "codespaces"
    if Path("/.dockerenv").exists() or os.environ.get("container"):
        return "docker"
    if platform.system().lower().startswith("win"):
        return "local_windows"
    return "docker"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def compiler() -> tuple[str, list[str], str]:
    cc = os.environ.get("CC", "").strip()
    candidates = [cc] if cc else []
    candidates.extend(["gcc", "clang", "cc"])
    for name in candidates:
        path = shutil.which(name)
        if path:
            return name, [path], path
    return "", [], ""


def version_for(command: list[str]) -> str:
    if not command:
        return ""
    try:
        proc = subprocess.run(
            [command[0], "--version"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=15,
        )
    except Exception as exc:  # pragma: no cover
        return f"version probe failed: {exc}"
    return proc.stdout.splitlines()[0] if proc.stdout.splitlines() else f"exit={proc.returncode}"


def write_rows(rows: list[dict[str, str]]) -> None:
    fields = [
        "benchmark",
        "source_path",
        "binary_path",
        "compiler",
        "compiler_version",
        "target",
        "input_size",
        "build_status",
        "sha256",
        "notes",
    ]
    RESULTS.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def blocked_rows(status: str, note: str) -> list[dict[str, str]]:
    return [
        {
            "benchmark": benchmark,
            "source_path": rel(SOURCE),
            "binary_path": "",
            "compiler": "",
            "compiler_version": "",
            "target": "native_host",
            "input_size": "small",
            "build_status": status,
            "sha256": "",
            "notes": note,
        }
        for benchmark in BENCHMARKS
    ]


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "build_workloads.log"
    env = current_environment()

    name, cmd_prefix, compiler_path = compiler()
    if not SOURCE.exists():
        rows = blocked_rows("FAIL", f"source file missing: {rel(SOURCE)}")
        write_rows(rows)
        log_path.write_text(rows[0]["notes"] + "\n", encoding="utf-8")
        return 1
    if not cmd_prefix:
        note = "No C compiler found on PATH; checked CC, gcc, clang, and cc."
        write_rows(blocked_rows("NOT_ATTEMPTED", note))
        log_path.write_text(note + "\n", encoding="utf-8")
        print(f"wrote {rel(OUT)} with NOT_ATTEMPTED rows")
        return 0

    binary = BIN_DIR / ("copper_workload_suite.exe" if platform.system().lower().startswith("win") else "copper_workload_suite")
    compile_cmd = [
        *cmd_prefix,
        "-std=c11",
        "-O2",
        "-Wall",
        "-Wextra",
        str(SOURCE),
        "-o",
        str(binary),
    ]
    proc = subprocess.run(
        compile_cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )
    log_text = "$ " + " ".join(compile_cmd) + "\n" + proc.stdout
    log_path.write_text(log_text, encoding="utf-8")
    version = version_for(cmd_prefix)

    if proc.returncode != 0 or not binary.exists():
        note = f"Compile failed in {env}; see {rel(log_path)}."
        rows = blocked_rows("FAIL", note)
        for row in rows:
            row["compiler"] = compiler_path
            row["compiler_version"] = version
        write_rows(rows)
        print(f"wrote {rel(OUT)} with FAIL rows")
        return 1

    digest = sha256(binary)
    rows: list[dict[str, str]] = []
    for benchmark in BENCHMARKS:
        rows.append(
            {
                "benchmark": benchmark,
                "source_path": rel(SOURCE),
                "binary_path": rel(binary),
                "compiler": compiler_path,
                "compiler_version": version,
                "target": "native_host",
                "input_size": "small",
                "build_status": "PASS",
                "sha256": digest,
                "notes": f"Built from source by command captured in {rel(log_path)}; native_host binary only, not a gem5/full-system binary.",
            }
        )
    write_rows(rows)
    print(f"wrote {rel(OUT)} with PASS rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
