#!/usr/bin/env python3
"""Run matched full/near-core synthesis evidence for COPPER.

The current open target is a near-core stub, not a full CPU. Rows and overhead
notes label that scope explicitly. If Yosys is unavailable, BLOCKED rows are
written instead of substituting estimates.
"""

from __future__ import annotations

import csv
import os
import platform
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "research" / "results"
LOG_DIR = RESULTS / "logs" / "fullcore_synthesis"
OUT = RESULTS / "fullcore_synthesis.csv"
OVERHEAD = RESULTS / "fullcore_synthesis_overhead.csv"


@dataclass(frozen=True)
class Design:
    name: str
    top: str
    sources: tuple[str, ...]
    scope: str
    params: tuple[tuple[str, int], ...] = ()


DESIGNS = (
    Design(
        "baseline_core_stub_with_prefetch_interface",
        "baseline_core_stub_with_prefetch_interface",
        ("research/baseline_prefetch_unit.sv", "research/rtl/integration/copper_near_core_stub.sv"),
        "near_core_stub",
    ),
    Design(
        "core_stub_plus_copper",
        "core_stub_plus_copper",
        ("research/copper_prefetch_unit_open.sv", "research/rtl/integration/copper_near_core_stub.sv"),
        "near_core_stub",
        (("ENTRIES", 8), ("QUEUE_DEPTH", 4)),
    ),
    Design("baseline_prefetch_unit", "baseline_prefetch_unit", ("research/baseline_prefetch_unit.sv",), "unit_prefetch"),
    Design(
        "copper_unit",
        "copper_prefetch_unit_open",
        ("research/copper_prefetch_unit_open.sv",),
        "unit_prefetch",
        (("ENTRIES", 2), ("QUEUE_DEPTH", 1)),
    ),
    Design(
        "copper_with_queue",
        "copper_prefetch_unit_open",
        ("research/copper_prefetch_unit_open.sv",),
        "unit_prefetch",
        (("ENTRIES", 4), ("QUEUE_DEPTH", 4)),
    ),
    Design(
        "copper_with_tables",
        "copper_prefetch_unit_open",
        ("research/copper_prefetch_unit_open.sv",),
        "unit_prefetch",
        (("ENTRIES", 16), ("QUEUE_DEPTH", 4)),
    ),
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


ENVIRONMENT = current_environment()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def parse_total_cells(output: str) -> str:
    matches = re.findall(r"Number of cells:\s+(\d+)", output)
    return matches[-1] if matches else ""


def parse_cell_counts(output: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in output.splitlines():
        match = re.match(r"\s+([A-Za-z0-9_$.\[\]-]+)\s+(\d+)\s*$", line)
        if match:
            counts[match.group(1)] = int(match.group(2))
    return counts


def sum_prefix(counts: dict[str, int], prefixes: tuple[str, ...]) -> str:
    value = sum(count for cell, count in counts.items() if cell.startswith(prefixes))
    return str(value) if value else ""


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def blank_row(design: Design, status: str, report_path: Path, notes: str) -> dict[str, str]:
    return {
        "design": design.name,
        "target": "generic",
        "flow": "yosys",
        "environment": ENVIRONMENT,
        "status": status,
        "lut": "",
        "ff": "",
        "bram": "",
        "dsp": "",
        "cells": "",
        "area_um2": "",
        "fmax_mhz": "",
        "wns": "",
        "tns": "",
        "power_mw": "",
        "report_path": rel(report_path),
        "notes": notes,
    }


def yosys_script(design: Design) -> str:
    reads = " ".join(f"read_verilog -sv {source};" for source in design.sources)
    params = " ".join(f"-set {key} {value}" for key, value in design.params)
    chparam = f"chparam {params} {design.top}; " if params else ""
    return f"{reads} {chparam}synth -top {design.top}; stat"


def run_design(design: Design) -> dict[str, str]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"yosys_generic_{design.name}.log"
    yosys = shutil.which("yosys")
    if not yosys:
        log_path.write_text("yosys not found on PATH\n", encoding="utf-8")
        return blank_row(
            design,
            "BLOCKED",
            log_path,
            f"{design.scope} synthesis blocked because Yosys is unavailable; no full-core or near-core number is claimed.",
        )
    command = [yosys, "-p", yosys_script(design)]
    proc = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
    log_path.write_text("$ " + " ".join(command) + "\n" + proc.stdout, encoding="utf-8")
    counts = parse_cell_counts(proc.stdout)
    return {
        "design": design.name,
        "target": "generic",
        "flow": "yosys",
        "environment": ENVIRONMENT,
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "lut": "",
        "ff": "",
        "bram": "",
        "dsp": "",
        "cells": parse_total_cells(proc.stdout),
        "area_um2": "",
        "fmax_mhz": "",
        "wns": "",
        "tns": "",
        "power_mw": "",
        "report_path": rel(log_path),
        "notes": f"Matched {design.scope} generic Yosys synthesis. No mapped timing, Fmax, or power is inferred."
        if proc.returncode == 0
        else f"{design.scope} Yosys synthesis failed; see log.",
    }


def overhead_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_design = {row["design"]: row for row in rows if row.get("target") == "generic" and row.get("flow") == "yosys"}
    pairs = (
        ("cells_near_core_baseline_vs_core_stub_plus_copper", "baseline_core_stub_with_prefetch_interface", "core_stub_plus_copper", "near_core_stub"),
        ("cells_unit_baseline_vs_copper_unit", "baseline_prefetch_unit", "copper_unit", "unit_prefetch"),
        ("cells_unit_baseline_vs_copper_with_queue", "baseline_prefetch_unit", "copper_with_queue", "unit_prefetch"),
        ("cells_unit_baseline_vs_copper_with_tables", "baseline_prefetch_unit", "copper_with_tables", "unit_prefetch"),
    )
    out: list[dict[str, str]] = []
    for metric, baseline_name, copper_name, scope in pairs:
        baseline = by_design.get(baseline_name)
        copper = by_design.get(copper_name)
        if baseline and copper and baseline.get("status") == "PASS" and copper.get("status") == "PASS" and baseline.get("cells") and copper.get("cells"):
            b = float(baseline["cells"])
            c = float(copper["cells"])
            out.append(
                {
                    "target": "generic",
                    "flow": "yosys",
                    "environment": ENVIRONMENT,
                    "metric": metric,
                    "baseline": f"{b:.0f}",
                    "with_copper": f"{c:.0f}",
                    "delta": f"{c - b:.0f}",
                    "percent_overhead": f"{((c - b) / b * 100.0) if b else 0.0:.6f}",
                    "scope": scope,
                    "notes": f"Matched {scope} overhead from the same generic Yosys flow; no full-core timing or power claim.",
                }
            )
        else:
            out.append(
                {
                    "target": "generic",
                    "flow": "yosys",
                    "environment": ENVIRONMENT,
                    "metric": metric,
                    "baseline": baseline.get("cells", "") if baseline else "",
                    "with_copper": copper.get("cells", "") if copper else "",
                    "delta": "",
                    "percent_overhead": "",
                    "scope": scope,
                    "notes": f"BLOCKED: matched {scope} overhead requires PASS rows and measured cells for both designs.",
                }
            )
    return out


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = [run_design(design) for design in DESIGNS]
    fields = [
        "design",
        "target",
        "flow",
        "environment",
        "status",
        "lut",
        "ff",
        "bram",
        "dsp",
        "cells",
        "area_um2",
        "fmax_mhz",
        "wns",
        "tns",
        "power_mw",
        "report_path",
        "notes",
    ]
    write_csv(OUT, fields, rows)
    write_csv(
        OVERHEAD,
        ["target", "flow", "environment", "metric", "baseline", "with_copper", "delta", "percent_overhead", "scope", "notes"],
        overhead_rows(rows),
    )
    print(f"wrote {rel(OUT)} and {rel(OVERHEAD)}")
    return 1 if any(row["status"] == "FAIL" for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
