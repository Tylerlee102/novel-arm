#!/usr/bin/env python3
"""Run matched core-wrapper/near-core PPA evidence ledgers for COPPER.

Full-core rows remain BLOCKED unless a real full CPU-core integration is
present. The repository may also contain an accepted open-source PicoRV32
core-wrapper, which is labeled as core_wrapper rather than full_core.
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
    target: str
    runnable: bool
    blocked_reason: str = ""
    params: tuple[tuple[str, int], ...] = ()


FULLCORE_BLOCKER = (
    "BLOCKED: no real full-core RTL integration is present in this open artifact, "
    "so no full-core area/timing/power row is claimed."
)

PICORV32_SOURCES = (
    "external/picorv32/picorv32.v",
    "research/baseline_prefetch_unit.sv",
    "research/copper_prefetch_unit_open.sv",
    "research/rtl/fullcore/picorv32_copper_wrapper.sv",
)

DESIGNS = (
    Design("full_core_baseline", "", (), "full_core", "full_core", False, FULLCORE_BLOCKER),
    Design("full_core_plus_copper", "", (), "full_core", "full_core", False, FULLCORE_BLOCKER),
    Design(
        "baseline_core_wrapper",
        "baseline_core_wrapper",
        PICORV32_SOURCES,
        "core_wrapper",
        "picorv32_core_wrapper",
        True,
    ),
    Design(
        "core_wrapper_plus_baseline_prefetch",
        "core_wrapper_plus_baseline_prefetch",
        PICORV32_SOURCES,
        "core_wrapper",
        "picorv32_core_wrapper",
        True,
    ),
    Design(
        "core_wrapper_plus_copper",
        "core_wrapper_plus_copper",
        PICORV32_SOURCES,
        "core_wrapper",
        "picorv32_core_wrapper",
        True,
        "",
        (("ENTRIES", 8), ("QUEUE_DEPTH", 4)),
    ),
    Design(
        "nearcore_stub_baseline",
        "nearcore_stub_baseline",
        ("research/baseline_prefetch_unit.sv", "research/rtl/integration/copper_near_core_stub.sv"),
        "near_core_stub",
        "generic",
        True,
    ),
    Design(
        "nearcore_stub_plus_copper",
        "nearcore_stub_plus_copper",
        ("research/copper_prefetch_unit_open.sv", "research/rtl/integration/copper_near_core_stub.sv"),
        "near_core_stub",
        "generic",
        True,
        "",
        (("ENTRIES", 8), ("QUEUE_DEPTH", 4)),
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


def scrub_text(text: str) -> str:
    return text.replace(str(Path.home()), "{USER_HOME}").replace(Path.home().as_posix(), "{USER_HOME}")


def write_log(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(scrub_text(text), encoding="utf-8")


def parse_total_cells(output: str) -> str:
    matches = re.findall(r"Number of cells:\s+(\d+)", output)
    if not matches:
        matches = re.findall(r"^\s+(\d+)\s+cells\s*$", output, re.M)
    return matches[-1] if matches else ""


def parse_cell_counts(output: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in output.splitlines():
        match = re.match(r"\s+([A-Za-z0-9_$.\\\[\]-]+)\s+(\d+)\s*$", line)
        if match:
            counts[match.group(1)] = int(match.group(2))
            continue
        match = re.match(r"\s+(\d+)\s+([A-Za-z0-9_$.\\\[\]-]+)\s*$", line)
        if match:
            counts[match.group(2)] = int(match.group(1))
    return counts


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def row_for(design: Design, status: str, report_path: Path, notes: str, cells: str = "", lut: str = "", ff: str = "") -> dict[str, str]:
    return {
        "design": design.name,
        "target": design.target,
        "flow": "yosys" if design.runnable else "not_run",
        "environment": ENVIRONMENT,
        "status": status,
        "lut": lut,
        "ff": ff,
        "bram": "",
        "dsp": "",
        "cells": cells,
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
    log_path = LOG_DIR / f"{design.name}.log"
    if not design.runnable:
        write_log(log_path, design.blocked_reason + "\n")
        return row_for(design, "BLOCKED", log_path, design.blocked_reason)

    missing_sources = [source for source in design.sources if not (ROOT / source).exists()]
    if missing_sources:
        note = f"BLOCKED: missing RTL source(s): {', '.join(missing_sources)}."
        write_log(log_path, note + "\n")
        return row_for(design, "BLOCKED", log_path, note)

    yosys = shutil.which("yosys")
    if not yosys:
        note = (
            f"BLOCKED: {design.scope} synthesis requires Yosys on PATH. "
            "No cells, timing, or power are inferred."
        )
        write_log(log_path, note + "\n")
        return row_for(design, "BLOCKED", log_path, note)

    command = [yosys, "-p", yosys_script(design)]
    proc = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
    write_log(log_path, "$ " + " ".join(command) + "\n" + proc.stdout)
    counts = parse_cell_counts(proc.stdout)
    status = "PASS" if proc.returncode == 0 else "FAIL"
    notes = (
        f"Matched {design.scope} generic Yosys resource row. "
        "Fmax/WNS/TNS/power_mw are blank because no mapped timing or power report was run."
    )
    if status != "PASS":
        notes = f"{design.scope} Yosys synthesis failed; see log."
    return row_for(
        design,
        status,
        log_path,
        notes,
        cells=parse_total_cells(proc.stdout),
        lut=str(sum(value for cell, value in counts.items() if cell.startswith("$_"))) if counts else "",
        ff=str(sum(value for cell, value in counts.items() if "DFF" in cell.upper())) if counts else "",
    )


def overhead_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_design = {row["design"]: row for row in rows}
    pairs = (
        ("full_core_cells_baseline_vs_copper", "full_core_baseline", "full_core_plus_copper", "full_core"),
        ("core_wrapper_cells_baseline_vs_copper", "baseline_core_wrapper", "core_wrapper_plus_copper", "core_wrapper"),
        ("core_wrapper_cells_prefetch_baseline_vs_copper", "core_wrapper_plus_baseline_prefetch", "core_wrapper_plus_copper", "core_wrapper"),
        ("near_core_stub_cells_baseline_vs_copper", "nearcore_stub_baseline", "nearcore_stub_plus_copper", "near_core_stub"),
    )
    out: list[dict[str, str]] = []
    for metric, baseline_name, copper_name, scope in pairs:
        baseline = by_design.get(baseline_name, {})
        copper = by_design.get(copper_name, {})
        if baseline.get("status") == "PASS" and copper.get("status") == "PASS" and baseline.get("cells") and copper.get("cells"):
            b = float(baseline["cells"])
            c = float(copper["cells"])
            out.append(
                {
                    "target": baseline.get("target", "generic"),
                    "flow": baseline.get("flow", "yosys"),
                    "environment": ENVIRONMENT,
                    "metric": metric,
                    "baseline_design": baseline_name,
                    "with_copper_design": copper_name,
                    "baseline": f"{b:.0f}",
                    "with_copper": f"{c:.0f}",
                    "delta": f"{c - b:.0f}",
                    "percent_overhead": f"{((c - b) / b * 100.0) if b else 0.0:.6f}",
                    "scope": scope,
                    "status": "PASS",
                    "notes": f"Matched {scope} generic Yosys resource overhead only; no mapped timing or power claim.",
                }
            )
        else:
            reason = (
                f"BLOCKED: matched {scope} overhead requires PASS rows and measured cells for "
                f"{baseline_name} and {copper_name}."
            )
            if scope == "full_core":
                reason = FULLCORE_BLOCKER
            out.append(
                {
                    "target": baseline.get("target", "full_core" if scope == "full_core" else "generic"),
                    "flow": baseline.get("flow", "not_run"),
                    "environment": ENVIRONMENT,
                    "metric": metric,
                    "baseline_design": baseline_name,
                    "with_copper_design": copper_name,
                    "baseline": baseline.get("cells", ""),
                    "with_copper": copper.get("cells", ""),
                    "delta": "",
                    "percent_overhead": "",
                    "scope": scope,
                    "status": "BLOCKED",
                    "notes": reason,
                }
            )
    return out


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = [run_design(design) for design in DESIGNS]
    write_csv(
        OUT,
        [
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
        ],
        rows,
    )
    write_csv(
        OVERHEAD,
        [
            "target",
            "flow",
            "environment",
            "metric",
            "baseline_design",
            "with_copper_design",
            "baseline",
            "with_copper",
            "delta",
            "percent_overhead",
            "scope",
            "status",
            "notes",
        ],
        overhead_rows(rows),
    )
    print(f"wrote {rel(OUT)} and {rel(OVERHEAD)}")
    return 1 if any(row["status"] == "FAIL" for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
