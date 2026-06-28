#!/usr/bin/env python3
"""Generate honest mapped PPA evidence for COPPER.

Mapped PPA rows are PASS only when a place-and-route or implementation flow
finishes and emits timing. Generic Yosys resource rows remain in the synthesis
ledgers and are deliberately not promoted here.
"""

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
RESULTS = ROOT / "research" / "results"
LOG_DIR = RESULTS / "logs" / "mapped_ppa"
OPENROAD_LOG_DIR = RESULTS / "logs" / "openroad"
VIVADO_LOG_DIR = RESULTS / "logs" / "vivado"
OUT = RESULTS / "mapped_ppa.csv"
OVERHEAD = RESULTS / "mapped_ppa_overhead.csv"

CLOCK_MHZ = os.environ.get("COPPER_MAPPED_PPA_CLOCK_MHZ", "50")
VIVADO_PART = os.environ.get("COPPER_VIVADO_PART", "xc7a35tcsg324-1")


@dataclass(frozen=True)
class Design:
    name: str
    top: str
    sources: tuple[str, ...]
    scope: str
    params: tuple[tuple[str, int], ...] = ()


NEARCORE_BASELINE = Design(
    "nearcore_stub_baseline",
    "nearcore_stub_baseline",
    ("research/baseline_prefetch_unit.sv", "research/rtl/integration/copper_near_core_stub.sv"),
    "near_core_stub",
)
NEARCORE_COPPER = Design(
    "nearcore_stub_plus_copper",
    "nearcore_stub_plus_copper",
    ("research/copper_prefetch_unit_open.sv", "research/rtl/integration/copper_near_core_stub.sv"),
    "near_core_stub",
    (("ENTRIES", 8), ("QUEUE_DEPTH", 4)),
)
FULLCORE_BASELINE = Design(
    "baseline_core_wrapper",
    "",
    (),
    "full_core",
)
FULLCORE_COPPER = Design(
    "core_wrapper_plus_copper",
    "",
    (),
    "full_core",
)
UNIT_BASELINE = Design(
    "baseline_prefetch_unit",
    "baseline_prefetch_unit",
    ("research/baseline_prefetch_unit.sv",),
    "unit",
)
UNIT_COPPER = Design(
    "copper_unit",
    "copper_prefetch_unit_open",
    ("research/copper_prefetch_unit_open.sv",),
    "unit",
    (("ENTRIES", 2), ("QUEUE_DEPTH", 1)),
)

FIELDS = [
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
OVERHEAD_FIELDS = ["target", "flow", "scope", "metric", "baseline", "with_copper", "delta", "percent_overhead", "notes"]


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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sanitized = text.replace(str(Path.home()), "{USER_HOME}").replace(Path.home().as_posix(), "{USER_HOME}")
    path.write_text(sanitized, encoding="utf-8")


def write_raw_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def run_capture(command: list[str], timeout: int) -> tuple[int, str]:
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    return proc.returncode, "$ " + " ".join(command) + "\n" + proc.stdout


def source_reads(design: Design) -> str:
    return " ".join(f"read_verilog -sv {source};" for source in design.sources)


def chparam(design: Design) -> str:
    if not design.params:
        return ""
    settings = " ".join(f"-set {key} {value}" for key, value in design.params)
    return f"chparam {settings} {design.top}; "


def yosys_script(design: Design, tail: str) -> str:
    return f"{source_reads(design)} {chparam(design)}{tail}"


def blank_row(design: Design, target: str, flow: str, status: str, report_path: Path, notes: str) -> dict[str, str]:
    return {
        "design": design.name,
        "target": target,
        "flow": flow,
        "environment": ENVIRONMENT,
        "status": status,
        "lut": "NA",
        "ff": "NA",
        "bram": "NA",
        "dsp": "NA",
        "cells": "NA",
        "area_um2": "NA",
        "fmax_mhz": "NA",
        "wns": "NA",
        "tns": "NA",
        "power_mw": "NA",
        "report_path": rel(report_path),
        "notes": notes,
    }


def parse_cell_counts(output: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in output.splitlines():
        match = re.match(r"\s+([A-Za-z0-9_$.\[\]-]+)\s+(\d+)\s*$", line)
        if match:
            counts[match.group(1)] = int(match.group(2))
    return counts


def parse_total_cells(output: str) -> str:
    matches = re.findall(r"Number of cells:\s+(\d+)", output)
    return matches[-1] if matches else ""


def parse_count_line(output: str, pattern: str) -> str:
    matches = re.findall(pattern, output, re.I | re.M)
    return matches[-1] if matches else ""


def parse_device_count(output: str, primitive: str) -> str:
    return parse_count_line(output, rf"Info:\s+{re.escape(primitive)}:\s+(\d+)\s*/")


def parse_ecp5_luts(output: str) -> str:
    logic = parse_count_line(output, r"Info:\s+logic LUTs:\s+(\d+)\s*/")
    carry = parse_count_line(output, r"Info:\s+carry LUTs:\s+(\d+)\s*/")
    if logic or carry:
        return str(int(logic or 0) + int(carry or 0))
    return parse_count_line(output, r"Info:\s+Total LUT4s:\s+(\d+)\s*/")


def parse_ecp5_ffs(output: str) -> str:
    return parse_count_line(output, r"Info:\s+Total DFFs:\s+(\d+)\s*/")


def sum_prefix(counts: dict[str, int], prefixes: tuple[str, ...]) -> str:
    value = sum(count for cell, count in counts.items() if cell.startswith(prefixes))
    return str(value) if value else ""


def parse_fmax(output: str) -> str:
    matches = re.findall(r"Max frequency for clock[^:]*:\s*([0-9.]+)\s+MHz", output, re.I)
    return matches[-1] if matches else ""


def parse_wns(output: str) -> str:
    patterns = (
        r"WNS\(ns\)\s*[:=]\s*(-?[0-9.]+)",
        r"Design Timing Summary\s*\n(?:.*\n){0,8}.*?WNS\(ns\).*?\n\s*(-?[0-9.]+)",
        r"slack\s*\(MET\)\s*[:=]\s*(-?[0-9.]+)",
        r"slack\s*\(VIOLATED\)\s*[:=]\s*(-?[0-9.]+)",
    )
    for pattern in patterns:
        matches = re.findall(pattern, output, re.I)
        if matches:
            return matches[-1]
    return ""


def parse_tns(output: str) -> str:
    matches = re.findall(r"TNS\(ns\)\s*[:=]\s*(-?[0-9.]+)", output, re.I)
    return matches[-1] if matches else ""


def parse_vivado_setup_wns(output: str) -> str:
    matches = re.findall(
        r"Setup\s*:\s*\d+\s+Failing Endpoints,\s*Worst Slack\s*(-?[0-9.]+)ns",
        output,
        re.I,
    )
    return matches[-1] if matches else ""


def parse_vivado_setup_tns(output: str) -> str:
    matches = re.findall(
        r"Setup\s*:\s*\d+\s+Failing Endpoints,\s*Worst Slack\s*-?[0-9.]+ns,\s*Total Violation\s*(-?[0-9.]+)ns",
        output,
        re.I,
    )
    return matches[-1] if matches else ""


def parse_vivado_util(output: str, label: str) -> str:
    matches = re.findall(rf"\|\s*{re.escape(label)}\s*\|\s*(\d+)\s*\|", output, re.I)
    return matches[-1] if matches else ""


def parse_vivado_power_mw(output: str) -> str:
    matches = re.findall(r"Total On-Chip Power\s*\(W\)\s*\|\s*([0-9.]+)", output, re.I)
    if not matches:
        matches = re.findall(r"Total On-Chip Power\s*:\s*([0-9.]+)\s*W", output, re.I)
    if not matches:
        return ""
    return f"{float(matches[-1]) * 1000.0:.3f}"


def value_or_na(value: str) -> str:
    return value if value not in {"", None} else "NA"


def nextpnr_ecp5(design: Design) -> dict[str, str]:
    log_path = LOG_DIR / f"ecp5_{design.name}.log"
    yosys = shutil.which("yosys")
    nextpnr = shutil.which("nextpnr-ecp5")
    if not yosys or not nextpnr:
        missing = "yosys" if not yosys else "nextpnr-ecp5"
        note = f"BLOCKED: ECP5 mapped PPA requires {missing} on PATH."
        write_text(log_path, note + "\n")
        return blank_row(design, "ecp5-85k", "yosys+nextpnr-ecp5", "BLOCKED", log_path, note)
    with tempfile.TemporaryDirectory(prefix="copper_mapped_ecp5_") as tmp:
        tmpdir = Path(tmp)
        json_path = tmpdir / f"{design.name}.json"
        cfg_path = tmpdir / f"{design.name}.config"
        script = yosys_script(design, f"synth_ecp5 -top {design.top} -json {json_path.as_posix()}; stat")
        yosys_code, yosys_output = run_capture([yosys, "-p", script], timeout=180)
        if yosys_code == 0:
            pnr_code, pnr_output = run_capture(
                [
                    nextpnr,
                    "--85k",
                    "--package",
                    "CABGA381",
                    "--speed",
                    "6",
                    "--freq",
                    CLOCK_MHZ,
                    "--lpf-allow-unconstrained",
                    "--json",
                    str(json_path),
                    "--textcfg",
                    str(cfg_path),
                ],
                timeout=300,
            )
        else:
            pnr_code, pnr_output = 1, "nextpnr-ecp5 skipped because Yosys ECP5 mapping failed\n"
    output = yosys_output + "\n" + pnr_output
    write_text(log_path, output)
    return mapped_row(design, "ecp5-85k", "yosys+nextpnr-ecp5", yosys_code, pnr_code, log_path, output)


def nextpnr_ice40(design: Design) -> dict[str, str]:
    log_path = LOG_DIR / f"ice40_{design.name}.log"
    yosys = shutil.which("yosys")
    nextpnr = shutil.which("nextpnr-ice40")
    if not yosys or not nextpnr:
        missing = "yosys" if not yosys else "nextpnr-ice40"
        note = f"BLOCKED: iCE40 mapped PPA requires {missing} on PATH."
        write_text(log_path, note + "\n")
        return blank_row(design, "ice40-hx8k", "yosys+nextpnr-ice40", "BLOCKED", log_path, note)
    with tempfile.TemporaryDirectory(prefix="copper_mapped_ice40_") as tmp:
        tmpdir = Path(tmp)
        json_path = tmpdir / f"{design.name}.json"
        asc_path = tmpdir / f"{design.name}.asc"
        script = yosys_script(design, f"synth_ice40 -top {design.top} -json {json_path.as_posix()}; stat")
        yosys_code, yosys_output = run_capture([yosys, "-p", script], timeout=180)
        if yosys_code == 0:
            pnr_code, pnr_output = run_capture(
                [
                    nextpnr,
                    "--hx8k",
                    "--package",
                    "ct256",
                    "--freq",
                    CLOCK_MHZ,
                    "--pcf-allow-unconstrained",
                    "--json",
                    str(json_path),
                    "--asc",
                    str(asc_path),
                ],
                timeout=300,
            )
        else:
            pnr_code, pnr_output = 1, "nextpnr-ice40 skipped because Yosys iCE40 mapping failed\n"
    output = yosys_output + "\n" + pnr_output
    write_text(log_path, output)
    return mapped_row(design, "ice40-hx8k", "yosys+nextpnr-ice40", yosys_code, pnr_code, log_path, output)


def mapped_row(
    design: Design,
    target: str,
    flow: str,
    synth_code: int,
    pnr_code: int,
    log_path: Path,
    output: str,
) -> dict[str, str]:
    counts = parse_cell_counts(output)
    lut = parse_ecp5_luts(output) if flow == "yosys+nextpnr-ecp5" else sum_prefix(counts, ("LUT4", "SB_LUT4"))
    ff = parse_ecp5_ffs(output) if flow == "yosys+nextpnr-ecp5" else sum_prefix(counts, ("TRELLIS_FF", "SB_DFF", "FD", "$_DFF"))
    bram = parse_device_count(output, "DP16KD") if flow == "yosys+nextpnr-ecp5" else sum_prefix(counts, ("DP16KD", "PDPW16KD", "SB_RAM", "RAMB"))
    dsp = parse_device_count(output, "MULT18X18D") if flow == "yosys+nextpnr-ecp5" else sum_prefix(counts, ("MULT18X18", "SB_MAC", "DSP"))
    cells = parse_device_count(output, "TRELLIS_COMB") if flow == "yosys+nextpnr-ecp5" else parse_total_cells(output)
    status = "PASS" if synth_code == 0 and pnr_code == 0 else "FAIL"
    note = (
        f"Mapped {design.scope} place-and-route completed at {CLOCK_MHZ} MHz target; "
        "fmax_mhz is reported only from timing output; power_mw is NA without a real power report."
    )
    if status != "PASS":
        note = f"FAIL: mapped {design.scope} synthesis/place-and-route did not complete; see log."
    return {
        "design": design.name,
        "target": target,
        "flow": flow,
        "environment": ENVIRONMENT,
        "status": status,
        "lut": value_or_na(lut),
        "ff": value_or_na(ff),
        "bram": value_or_na(bram),
        "dsp": value_or_na(dsp),
        "cells": value_or_na(cells),
        "area_um2": "NA",
        "fmax_mhz": value_or_na(parse_fmax(output)),
        "wns": value_or_na(parse_wns(output)),
        "tns": value_or_na(parse_tns(output)),
        "power_mw": "NA",
        "report_path": rel(log_path),
        "notes": note,
    }


def vivado_tcl(design: Design, run_dir: Path) -> str:
    source_lines = "\n".join(f"read_verilog -sv {{{(ROOT / source).as_posix()}}}" for source in design.sources)
    params = " ".join(f"-generic {key}={value}" for key, value in design.params)
    return f"""
set_msg_config -id {{Common 17-55}} -new_severity {{Warning}}
{source_lines}
synth_design -top {design.top} -part {VIVADO_PART} {params}
create_clock -period [expr {{1000.0 / {CLOCK_MHZ}}}] [get_ports clk]
opt_design
place_design
route_design
report_utilization -file {{{(run_dir / (design.name + "_utilization.rpt")).as_posix()}}}
report_timing_summary -file {{{(run_dir / (design.name + "_timing.rpt")).as_posix()}}}
report_power -file {{{(run_dir / (design.name + "_power.rpt")).as_posix()}}}
exit
""".lstrip()


def vivado_impl(design: Design) -> dict[str, str]:
    log_path = VIVADO_LOG_DIR / f"{design.name}.log"
    vivado = shutil.which("vivado")
    if not vivado:
        note = "BLOCKED: Vivado mapped implementation requires vivado on PATH."
        write_text(log_path, note + "\n")
        return blank_row(design, f"vivado-{VIVADO_PART}", "vivado-impl", "BLOCKED", log_path, note)
    run_dir = LOG_DIR / "vivado_runs" / design.name
    run_dir.mkdir(parents=True, exist_ok=True)
    tcl_path = run_dir / "run_vivado_impl.tcl"
    write_raw_text(tcl_path, vivado_tcl(design, run_dir))
    code, output = run_capture([vivado, "-mode", "batch", "-source", str(tcl_path)], timeout=1200)
    util_text = (run_dir / f"{design.name}_utilization.rpt").read_text(encoding="utf-8", errors="ignore") if (run_dir / f"{design.name}_utilization.rpt").exists() else ""
    timing_text = (run_dir / f"{design.name}_timing.rpt").read_text(encoding="utf-8", errors="ignore") if (run_dir / f"{design.name}_timing.rpt").exists() else ""
    power_text = (run_dir / f"{design.name}_power.rpt").read_text(encoding="utf-8", errors="ignore") if (run_dir / f"{design.name}_power.rpt").exists() else ""
    combined = output + "\n" + util_text + "\n" + timing_text + "\n" + power_text
    write_text(log_path, combined)
    row = mapped_row(design, f"vivado-{VIVADO_PART}", "vivado-impl", 0, code, log_path, combined)
    row["lut"] = value_or_na(parse_vivado_util(combined, "Slice LUTs"))
    row["ff"] = value_or_na(parse_vivado_util(combined, "Slice Registers"))
    row["bram"] = value_or_na(parse_vivado_util(combined, "Block RAM Tile"))
    row["dsp"] = value_or_na(parse_vivado_util(combined, "DSPs"))
    row["wns"] = value_or_na(parse_vivado_setup_wns(combined) or row["wns"])
    row["tns"] = value_or_na(parse_vivado_setup_tns(combined) or row["tns"])
    row["power_mw"] = value_or_na(parse_vivado_power_mw(combined))
    if code == 0:
        row["notes"] = (
            f"Vivado implementation completed at {CLOCK_MHZ} MHz target. "
            "power_mw is from report_power when present; this is tool-estimated power, not silicon measurement."
        )
    return row


def openroad_blocked_rows() -> list[dict[str, str]]:
    log_path = OPENROAD_LOG_DIR / "openroad_availability.log"
    openroad = shutil.which("openroad")
    platform_dir = os.environ.get("COPPER_OPENROAD_PLATFORM", "").strip()
    if not openroad:
        note = "BLOCKED: OpenROAD unavailable on PATH."
    elif not platform_dir:
        note = (
            "BLOCKED: OpenROAD binary exists, but no COPPER_OPENROAD_PLATFORM/Liberty/PDK setup "
            "is configured for a real mapped timing flow."
        )
    else:
        note = (
            "BLOCKED: OpenROAD platform setup was detected but this artifact does not include a "
            "validated OpenROAD flow script for the near-core stub."
        )
    write_text(log_path, note + "\n")
    return [
        blank_row(NEARCORE_BASELINE, "openroad", "openroad", "BLOCKED", log_path, note),
        blank_row(NEARCORE_COPPER, "openroad", "openroad", "BLOCKED", log_path, note),
    ]


def fullcore_blocked_rows() -> list[dict[str, str]]:
    log_path = LOG_DIR / "fullcore_wrapper_availability.log"
    note = (
        "BLOCKED: no real full-core or accepted baseline/core_wrapper_plus_copper RTL is present, "
        "so full-core mapped PPA cannot be run."
    )
    write_text(log_path, note + "\n")
    return [
        blank_row(FULLCORE_BASELINE, "full-core-wrapper", "not_run", "BLOCKED", log_path, note),
        blank_row(FULLCORE_COPPER, "full-core-wrapper", "not_run", "BLOCKED", log_path, note),
    ]


def matched_pass(rows: list[dict[str, str]], target: str, flow: str, scope: str) -> bool:
    names = {"near_core_stub": (NEARCORE_BASELINE.name, NEARCORE_COPPER.name), "unit": (UNIT_BASELINE.name, UNIT_COPPER.name)}[scope]
    by_name = {row["design"]: row for row in rows if row["target"] == target and row["flow"] == flow}
    return all(by_name.get(name, {}).get("status") == "PASS" for name in names)


def run_open_source_fpga() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    rows.extend(nextpnr_ecp5(design) for design in (NEARCORE_BASELINE, NEARCORE_COPPER))
    if not matched_pass(rows, "ecp5-85k", "yosys+nextpnr-ecp5", "near_core_stub"):
        rows.extend(nextpnr_ice40(design) for design in (NEARCORE_BASELINE, NEARCORE_COPPER))
    if not any(
        matched_pass(rows, target, flow, "near_core_stub")
        for target, flow in (("ecp5-85k", "yosys+nextpnr-ecp5"), ("ice40-hx8k", "yosys+nextpnr-ice40"))
    ):
        rows.extend(fullcore_blocked_rows())
        if shutil.which("yosys") and shutil.which("nextpnr-ecp5"):
            rows.extend(nextpnr_ecp5(design) for design in (UNIT_BASELINE, UNIT_COPPER))
        elif shutil.which("yosys") and shutil.which("nextpnr-ice40"):
            rows.extend(nextpnr_ice40(design) for design in (UNIT_BASELINE, UNIT_COPPER))
        else:
            log_path = LOG_DIR / "unit_fallback.log"
            note = "BLOCKED: unit-level fallback was not run because no Yosys plus nextpnr target is available."
            write_text(log_path, note + "\n")
            rows.extend(
                blank_row(design, "unit-fallback", "not_run", "BLOCKED", log_path, note)
                for design in (UNIT_BASELINE, UNIT_COPPER)
            )
    return rows


def run_vendor_or_asic() -> list[dict[str, str]]:
    rows = openroad_blocked_rows()
    rows.extend(vivado_impl(design) for design in (NEARCORE_BASELINE, NEARCORE_COPPER))
    return rows


def numeric(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def overhead_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    grouped: dict[tuple[str, str], dict[str, dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault((row["target"], row["flow"]), {})[row["design"]] = row
    for (target, flow), by_name in grouped.items():
        pairs = (
            ("near_core_stub", NEARCORE_BASELINE.name, NEARCORE_COPPER.name),
            ("full_core", FULLCORE_BASELINE.name, FULLCORE_COPPER.name),
            ("unit", UNIT_BASELINE.name, UNIT_COPPER.name),
        )
        for scope, baseline_name, copper_name in pairs:
            baseline = by_name.get(baseline_name)
            copper = by_name.get(copper_name)
            if not baseline or not copper:
                continue
            if baseline.get("status") != "PASS" or copper.get("status") != "PASS":
                out.append(
                    {
                        "target": target,
                        "flow": flow,
                        "scope": scope,
                        "metric": f"{scope}_mapped_timing",
                        "baseline": "",
                        "with_copper": "",
                        "delta": "",
                        "percent_overhead": "",
                        "notes": "BLOCKED: matched mapped PPA overhead requires PASS rows for baseline and COPPER.",
                    }
                )
                continue
            for metric in ("lut", "ff", "bram", "dsp", "cells", "fmax_mhz", "power_mw"):
                b = numeric(baseline.get(metric, ""))
                c = numeric(copper.get(metric, ""))
                if b is None or c is None:
                    continue
                delta = c - b
                pct = (delta / b * 100.0) if b else 0.0
                out.append(
                    {
                        "target": target,
                        "flow": flow,
                        "scope": scope,
                        "metric": f"{scope}_{metric}",
                        "baseline": f"{b:.6f}".rstrip("0").rstrip("."),
                        "with_copper": f"{c:.6f}".rstrip("0").rstrip("."),
                        "delta": f"{delta:.6f}".rstrip("0").rstrip("."),
                        "percent_overhead": f"{pct:.6f}",
                        "notes": "Matched mapped PPA overhead from same target, flow, and constraints.",
                    }
                )
    if not out:
        out.append(
            {
                "target": "none",
                "flow": "none",
                "scope": "near_core_stub",
                "metric": "near_core_stub_mapped_timing",
                "baseline": "",
                "with_copper": "",
                "delta": "",
                "percent_overhead": "",
                "notes": "BLOCKED: no matched mapped PPA PASS pair was produced.",
            }
        )
    return out


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    rows = run_open_source_fpga()
    rows.extend(run_vendor_or_asic())
    write_csv(OUT, FIELDS, rows)
    write_csv(OVERHEAD, OVERHEAD_FIELDS, overhead_rows(rows))
    print(f"wrote {rel(OUT)} and {rel(OVERHEAD)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
