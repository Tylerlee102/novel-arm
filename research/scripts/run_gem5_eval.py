#!/usr/bin/env python3
"""Record gem5 availability for the COPPER evaluation flow.

This script does not fabricate gem5 data. If a runnable gem5 binary is not
available, it writes BLOCKED rows with the exact reason.
"""

from __future__ import annotations

import csv
import os
import platform
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "research" / "results"
LOG_DIR = RESULTS / "logs" / "gem5"
PERF = RESULTS / "gem5_performance.csv"
PREF = RESULTS / "gem5_prefetch_metrics.csv"
TRAFFIC = RESULTS / "gem5_memory_traffic.csv"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


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


def runnable_gem5() -> tuple[str, str]:
    for name in ("gem5.opt", "gem5"):
        path = shutil.which(name)
        if path:
            try:
                proc = subprocess.run(
                    [path, "--version"],
                    cwd=ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=20,
                )
            except Exception as exc:
                return "", f"{path} was found but could not run: {exc}"
            if proc.returncode == 0:
                return path, proc.stdout.strip().splitlines()[0] if proc.stdout.strip() else path
            return "", f"{path} returned exit {proc.returncode}: {proc.stdout.strip()[:240]}"
    local = ROOT / "external" / "gem5" / "build" / "ARM" / "gem5.opt"
    if local.exists():
        return "", f"{rel(local)} exists but is not on PATH and Phase 0 showed it is not executable in this OS session."
    return "", "gem5/gem5.opt not found on PATH."


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "gem5_availability.log"
    gem5, note = runnable_gem5()
    if gem5:
        note = (
            "Runnable gem5 was found, but this pass does not include a configured "
            "full gem5 workload campaign. No performance rows are promoted."
        )
    log_path.write_text(note + "\n", encoding="utf-8")
    env = current_environment()
    common = {
        "benchmark": "ALL",
        "input": "NA",
        "seed": "NA",
        "config": "NA",
        "evidence_level": "gem5",
        "simulator": gem5 or "gem5_unavailable",
        "log_path": rel(log_path),
        "notes": note,
    }
    write_csv(
        PERF,
        [
            "benchmark",
            "input",
            "seed",
            "config",
            "evidence_level",
            "simulator",
            "cycles",
            "instructions",
            "ipc",
            "cache_misses",
            "memory_stalls",
            "speedup_vs_no_prefetch",
            "speedup_vs_best_baseline",
            "status",
            "log_path",
            "notes",
        ],
        [{**common, "cycles": "NA", "instructions": "NA", "ipc": "NA", "cache_misses": "NA", "memory_stalls": "NA", "speedup_vs_no_prefetch": "NA", "speedup_vs_best_baseline": "NA", "status": "BLOCKED"}],
    )
    write_csv(
        PREF,
        [
            "benchmark",
            "input",
            "seed",
            "config",
            "evidence_level",
            "simulator",
            "prefetches_issued",
            "useful_prefetches",
            "useless_prefetches",
            "late_prefetches",
            "queue_drops",
            "coverage",
            "accuracy",
            "lateness_rate",
            "log_path",
            "notes",
        ],
        [{**common, "prefetches_issued": "NA", "useful_prefetches": "NA", "useless_prefetches": "NA", "late_prefetches": "NA", "queue_drops": "NA", "coverage": "NA", "accuracy": "NA", "lateness_rate": "NA"}],
    )
    write_csv(
        TRAFFIC,
        [
            "benchmark",
            "input",
            "seed",
            "config",
            "evidence_level",
            "simulator",
            "demand_loads",
            "prefetch_loads",
            "total_memory_requests",
            "traffic_overhead_pct",
            "bandwidth_pressure_metric",
            "log_path",
            "notes",
        ],
        [{**common, "demand_loads": "NA", "prefetch_loads": "NA", "total_memory_requests": "NA", "traffic_overhead_pct": "NA", "bandwidth_pressure_metric": "NA"}],
    )
    print(f"wrote {rel(PERF)}, {rel(PREF)}, and {rel(TRAFFIC)} with BLOCKED gem5 rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
