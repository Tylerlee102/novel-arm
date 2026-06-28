#!/usr/bin/env python3
"""Create synthesis ledgers from real reports and open-source tool runs."""

from __future__ import annotations

import csv
import os
import platform
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "research"
RESULTS = RESEARCH / "results"
SRC = RESULTS / "copper_clpd_sram_synth_summary.csv"
SYNTH = RESULTS / "synthesis.csv"
OVERHEAD = RESULTS / "synthesis_overhead.csv"
LOG_DIR = RESULTS / "logs" / "synthesis"


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


def tool_path(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    candidates: list[Path] = []
    oss_roots = [
        os.environ.get("COPPER_OSS_CAD_SUITE", ""),
        "C:/Users/tyboy/tools/oss-cad-suite",
        str(ROOT / "tools" / "oss-cad-suite"),
        str(ROOT / ".tools" / "oss-cad-suite" / "oss-cad-suite"),
    ]
    names = [name]
    if platform.system().lower().startswith("win") and not name.endswith(".exe"):
        names.append(f"{name}.exe")
    for root in oss_roots:
        if root:
            candidates.extend(Path(root) / "bin" / candidate for candidate in names)
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


@dataclass(frozen=True)
class Design:
    name: str
    source: str
    top: str
    params: tuple[tuple[str, int], ...] = ()


DESIGNS = [
    Design("baseline_prefetch_unit", "research/baseline_prefetch_unit.sv", "baseline_prefetch_unit"),
    Design("copper_unit", "research/copper_prefetch_unit_open.sv", "copper_prefetch_unit_open", (("ENTRIES", 2), ("QUEUE_DEPTH", 1))),
    Design("copper_with_queue", "research/copper_prefetch_unit_open.sv", "copper_prefetch_unit_open", (("ENTRIES", 4), ("QUEUE_DEPTH", 4))),
    Design("copper_with_tables", "research/copper_prefetch_unit_open.sv", "copper_prefetch_unit_open", (("ENTRIES", 16), ("QUEUE_DEPTH", 4))),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def write_log(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def command_text(design: Design, tail: str) -> str:
    chparams = " ".join(f"-set {key} {value}" for key, value in design.params)
    param_cmd = f"chparam {chparams} {design.top}; " if chparams else ""
    return f"read_verilog -sv {design.source}; {param_cmd}{tail}"


def command_env(command: list[str]) -> dict[str, str]:
    env = os.environ.copy()
    extra_paths = []
    for item in command:
        try:
            path = Path(item)
        except (TypeError, ValueError):
            continue
        if path.exists() and path.parent:
            extra_paths.append(str(path.parent))
            if path.parent.name == "bin" and (path.parent.parent / "lib").exists():
                extra_paths.append(str(path.parent.parent / "lib"))
    if extra_paths:
        env["PATH"] = os.pathsep.join(extra_paths + [env.get("PATH", "")])
    return env


def run_capture(command: list[str], timeout: int) -> tuple[int, str]:
    proc = subprocess.run(
        command,
        cwd=ROOT,
        env=command_env(command),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    return proc.returncode, proc.stdout


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


def parse_total_cells(output: str) -> str:
    matches = re.findall(r"Number of cells:\s+(\d+)", output)
    if not matches:
        matches = re.findall(r"^\s+(\d+)\s+cells\s*$", output, re.M)
    return matches[-1] if matches else ""


def sum_prefix(counts: dict[str, int], prefixes: tuple[str, ...]) -> str:
    value = sum(count for cell, count in counts.items() if cell.startswith(prefixes))
    return str(value) if value else ""


def parse_fmax(output: str) -> str:
    matches = re.findall(r"Max frequency for clock[^:]*:\s*([0-9.]+)\s+MHz", output, re.I)
    return matches[-1] if matches else ""


def blank_row(design: Design, target: str, flow: str, status: str, report_path: Path, notes: str) -> dict[str, str]:
    return {
        "design": design.name,
        "target": target,
        "flow": flow,
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


def run_yosys_generic(design: Design) -> dict[str, str]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"yosys_generic_{design.name}.log"
    yosys = tool_path("yosys")
    if not yosys:
        write_log(log_path, "yosys not found on PATH\n")
        return blank_row(
            design,
            "generic",
            "yosys",
            "BLOCKED",
            log_path,
            "Open-source generic synthesis blocked because Yosys is unavailable.",
        )
    script = command_text(design, f"synth -top {design.top}; stat")
    code, output = run_capture([yosys, "-p", script], timeout=120)
    write_log(log_path, output)
    counts = parse_cell_counts(output)
    return {
        "design": design.name,
        "target": "generic",
        "flow": "yosys",
        "environment": ENVIRONMENT,
        "status": "PASS" if code == 0 else "FAIL",
        "lut": "",
        "ff": "",
        "bram": "",
        "dsp": "",
        "cells": parse_total_cells(output),
        "area_um2": "",
        "fmax_mhz": "",
        "wns": "",
        "tns": "",
        "power_mw": "",
        "report_path": rel(log_path),
        "notes": "Generic synthesis only; no mapped FPGA timing, Fmax, or power inferred."
        if code == 0
        else "Yosys generic synthesis failed; see log for exact unsupported construct or error.",
    }


def run_nextpnr_ice40(design: Design) -> dict[str, str]:
    log_path = LOG_DIR / f"nextpnr_ice40_{design.name}.log"
    yosys = tool_path("yosys")
    nextpnr = tool_path("nextpnr-ice40")
    if not yosys or not nextpnr:
        missing = "yosys" if not yosys else "nextpnr-ice40"
        write_log(log_path, f"{missing} not found on PATH\n")
        return blank_row(
            design,
            "ice40-hx8k",
            "yosys+nextpnr-ice40",
            "BLOCKED",
            log_path,
            f"Optional iCE40 place-and-route blocked because {missing} is unavailable.",
        )
    with tempfile.TemporaryDirectory(prefix="copper_ice40_") as tmp:
        tmpdir = Path(tmp)
        json_path = tmpdir / f"{design.name}.json"
        asc_path = tmpdir / f"{design.name}.asc"
        script = command_text(design, f"synth_ice40 -top {design.top} -json {json_path.as_posix()}; stat")
        yosys_code, yosys_output = run_capture([yosys, "-p", script], timeout=120)
        if yosys_code == 0:
            pnr_code, pnr_output = run_capture(
                [
                    nextpnr,
                    "--hx8k",
                    "--package",
                    "ct256",
                    "--pcf-allow-unconstrained",
                    "--json",
                    str(json_path),
                    "--asc",
                    str(asc_path),
                ],
                timeout=180,
            )
        else:
            pnr_code, pnr_output = 1, "nextpnr skipped because Yosys iCE40 mapping failed\n"
    output = yosys_output + "\n" + pnr_output
    write_log(log_path, output)
    counts = parse_cell_counts(output)
    status = "PASS" if yosys_code == 0 and pnr_code == 0 else "FAIL"
    return {
        "design": design.name,
        "target": "ice40-hx8k",
        "flow": "yosys+nextpnr-ice40",
        "environment": ENVIRONMENT,
        "status": status,
        "lut": sum_prefix(counts, ("SB_LUT4",)),
        "ff": sum_prefix(counts, ("SB_DFF",)),
        "bram": sum_prefix(counts, ("SB_RAM",)),
        "dsp": sum_prefix(counts, ("SB_MAC",)),
        "cells": parse_total_cells(output),
        "area_um2": "",
        "fmax_mhz": parse_fmax(output),
        "wns": "",
        "tns": "",
        "power_mw": "",
        "report_path": rel(log_path),
        "notes": "Optional iCE40 place-and-route attempt; Fmax is reported only if nextpnr emits it; no power inferred."
        if status == "PASS"
        else "Optional iCE40 flow failed; see log for exact synthesis/place-and-route blocker.",
    }


def run_nextpnr_ecp5(design: Design) -> dict[str, str]:
    log_path = LOG_DIR / f"nextpnr_ecp5_{design.name}.log"
    yosys = tool_path("yosys")
    nextpnr = tool_path("nextpnr-ecp5")
    if not yosys or not nextpnr:
        missing = "yosys" if not yosys else "nextpnr-ecp5"
        write_log(log_path, f"{missing} not found on PATH\n")
        return blank_row(
            design,
            "ecp5-85k",
            "yosys+nextpnr-ecp5",
            "BLOCKED",
            log_path,
            f"Optional ECP5 place-and-route blocked because {missing} is unavailable.",
        )
    with tempfile.TemporaryDirectory(prefix="copper_ecp5_") as tmp:
        tmpdir = Path(tmp)
        json_path = tmpdir / f"{design.name}.json"
        cfg_path = tmpdir / f"{design.name}.config"
        script = command_text(design, f"synth_ecp5 -top {design.top} -json {json_path.as_posix()}; stat")
        yosys_code, yosys_output = run_capture([yosys, "-p", script], timeout=120)
        if yosys_code == 0:
            pnr_code, pnr_output = run_capture(
                [
                    nextpnr,
                    "--85k",
                    "--package",
                    "CABGA381",
                    "--json",
                    str(json_path),
                    "--textcfg",
                    str(cfg_path),
                ],
                timeout=180,
            )
        else:
            pnr_code, pnr_output = 1, "nextpnr skipped because Yosys ECP5 mapping failed\n"
    output = yosys_output + "\n" + pnr_output
    write_log(log_path, output)
    counts = parse_cell_counts(output)
    status = "PASS" if yosys_code == 0 and pnr_code == 0 else "FAIL"
    return {
        "design": design.name,
        "target": "ecp5-85k",
        "flow": "yosys+nextpnr-ecp5",
        "environment": ENVIRONMENT,
        "status": status,
        "lut": sum_prefix(counts, ("LUT4",)),
        "ff": sum_prefix(counts, ("TRELLIS_FF",)),
        "bram": sum_prefix(counts, ("DP16KD",)),
        "dsp": sum_prefix(counts, ("MULT18X18",)),
        "cells": parse_total_cells(output),
        "area_um2": "",
        "fmax_mhz": parse_fmax(output),
        "wns": "",
        "tns": "",
        "power_mw": "",
        "report_path": rel(log_path),
        "notes": "Optional ECP5 place-and-route attempt; Fmax is reported only if nextpnr emits it; no power inferred."
        if status == "PASS"
        else "Optional ECP5 flow failed; see log for exact synthesis/place-and-route blocker.",
    }


def open_source_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for design in DESIGNS:
        rows.append(run_yosys_generic(design))
    for design in DESIGNS:
        rows.append(run_nextpnr_ice40(design))
    for design in DESIGNS:
        rows.append(run_nextpnr_ecp5(design))
    return rows


def vivado_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in read_csv(SRC):
        errors = int(float(row.get("errors", "0") or 0))
        fits = row.get("fits_part", "").lower() == "true"
        status = "PASS" if errors == 0 and fits else ("PARTIAL" if errors == 0 else "FAIL")
        rows.append(
            {
                "design": f"copper_clpd_sram_dir_{row.get('name', '')}",
                "target": row.get("part", ""),
                "flow": "vivado_existing_report",
                "environment": "local_windows",
                "status": status,
                "lut": row.get("luts", ""),
                "ff": row.get("regs", ""),
                "bram": row.get("bram_tiles", ""),
                "dsp": row.get("dsps", ""),
                "cells": "",
                "area_um2": "",
                "fmax_mhz": "",
                "wns": row.get("wns_ns", ""),
                "tns": "",
                "power_mw": "",
                "report_path": rel(SRC),
                "notes": "Parsed from existing Vivado summary; not a fresh rerun.",
            }
        )
    return rows


def overhead_for_metric(
    rows: list[dict[str, str]],
    environment: str,
    target: str,
    flow: str,
    metric: str,
    designs: tuple[str, ...],
) -> list[dict[str, str]]:
    by_design = {
        row["design"]: row
        for row in rows
        if row.get("environment") == environment and row["target"] == target and row["flow"] == flow
    }
    baseline = by_design.get("baseline_prefetch_unit")
    out: list[dict[str, str]] = []
    for design in designs:
        copper = by_design.get(design)
        if (
            baseline
            and copper
            and baseline["status"] == "PASS"
            and copper["status"] == "PASS"
            and baseline.get(metric)
            and copper.get(metric)
        ):
            b = float(baseline[metric])
            c = float(copper[metric])
            out.append(
                {
                    "target": target,
                    "flow": flow,
                    "environment": environment,
                    "metric": f"{metric}_baseline_prefetch_unit_vs_{design}",
                    "baseline": f"{b:.0f}",
                    "copper": f"{c:.0f}",
                    "delta": f"{c - b:.0f}",
                    "percent_overhead": f"{((c - b) / b * 100.0) if b else 0.0:.6f}",
                    "notes": "Matched unit-level overhead from the same open-source flow; scope is the prefetch unit, not a full core.",
                }
            )
        else:
            out.append(
                {
                    "target": target,
                    "flow": flow,
                    "environment": environment,
                    "metric": f"{metric}_baseline_prefetch_unit_vs_{design}",
                    "baseline": baseline.get(metric, "") if baseline else "",
                    "copper": copper.get(metric, "") if copper else "",
                    "delta": "",
                    "percent_overhead": "",
                    "notes": "BLOCKED: matched overhead requires PASS rows and metric values for both designs.",
                }
            )
    return out


def overhead_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    designs = ("copper_unit", "copper_with_queue", "copper_with_tables")
    environments = sorted({row.get("environment", "local_windows") for row in rows if row.get("flow") != "vivado_existing_report"})
    out: list[dict[str, str]] = []
    for environment in environments:
        out.extend(overhead_for_metric(rows, environment, "generic", "yosys", "cells", designs))
        out.extend(overhead_for_metric(rows, environment, "ice40-hx8k", "yosys+nextpnr-ice40", "lut", designs))
        out.extend(overhead_for_metric(rows, environment, "ice40-hx8k", "yosys+nextpnr-ice40", "ff", designs))
        out.extend(overhead_for_metric(rows, environment, "ecp5-85k", "yosys+nextpnr-ecp5", "lut", designs))
        out.extend(overhead_for_metric(rows, environment, "ecp5-85k", "yosys+nextpnr-ecp5", "ff", designs))
    return out


def merged_rows(path: Path, fieldnames: list[str], new_rows: list[dict[str, str]], key_fields: list[str]) -> list[dict[str, str]]:
    normalized_new = [{field: row.get(field, "") for field in fieldnames} for row in new_rows]
    new_keys = {tuple(row.get(field, "") for field in key_fields) for row in normalized_new}
    keep: list[dict[str, str]] = []
    if path.exists():
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if not row.get("environment"):
                    row["environment"] = "local_windows"
                normalized = {field: row.get(field, "") for field in fieldnames}
                key = tuple(normalized.get(field, "") for field in key_fields)
                if key not in new_keys:
                    keep.append(normalized)
    return keep + normalized_new


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    rows = open_source_rows() + vivado_rows()
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
    all_synth_rows = merged_rows(SYNTH, fields, rows, ["design", "target", "flow", "environment"])
    write_rows(SYNTH, fields, all_synth_rows)
    overhead_fields = ["target", "flow", "environment", "metric", "baseline", "copper", "delta", "percent_overhead", "notes"]
    write_rows(OVERHEAD, overhead_fields, overhead_rows(all_synth_rows))
    print(f"wrote {SYNTH.relative_to(ROOT)} and {OVERHEAD.relative_to(ROOT)}")
    generic_rows = [row for row in rows if row["flow"] == "yosys"]
    return 1 if any(row["status"] == "FAIL" for row in generic_rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
