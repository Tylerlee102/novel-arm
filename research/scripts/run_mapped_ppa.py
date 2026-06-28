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
PICORV32_SOURCES = (
    "external/picorv32/picorv32.v",
    "research/baseline_prefetch_unit.sv",
    "research/copper_prefetch_unit_open.sv",
    "research/rtl/fullcore/picorv32_copper_wrapper.sv",
)
FULLCORE_BASELINE = Design(
    "full_core_baseline",
    "",
    (),
    "full_core",
)
FULLCORE_COPPER = Design(
    "full_core_plus_copper",
    "",
    (),
    "full_core",
)
CORE_WRAPPER_BASELINE = Design(
    "baseline_core_wrapper",
    "baseline_core_wrapper",
    PICORV32_SOURCES,
    "accepted_core_wrapper",
)
CORE_WRAPPER_PREFETCH_BASELINE = Design(
    "core_wrapper_plus_baseline_prefetch",
    "core_wrapper_plus_baseline_prefetch",
    PICORV32_SOURCES,
    "accepted_core_wrapper",
)
CORE_WRAPPER_COPPER = Design(
    "core_wrapper_plus_copper",
    "core_wrapper_plus_copper",
    PICORV32_SOURCES,
    "accepted_core_wrapper",
    (("ENTRIES", 8), ("QUEUE_DEPTH", 4)),
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
MAPPED_DESIGNS = (
    NEARCORE_BASELINE,
    NEARCORE_COPPER,
    CORE_WRAPPER_BASELINE,
    CORE_WRAPPER_PREFETCH_BASELINE,
    CORE_WRAPPER_COPPER,
)
FALLBACK_DESIGNS = MAPPED_DESIGNS + (UNIT_BASELINE, UNIT_COPPER)

FIELDS = [
    "evidence_id",
    "scope",
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
OVERHEAD_FIELDS = [
    "evidence_id",
    "scope",
    "design",
    "target",
    "flow",
    "environment",
    "status",
    "metric",
    "baseline",
    "with_copper",
    "delta",
    "percent_overhead",
    "report_path",
    "notes",
]


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
    aliases = {
        "vivado": ("vivado", "vivado.bat"),
    }
    tool_roots = [
        os.environ.get("COPPER_OSS_CAD_SUITE", ""),
        os.environ.get("COPPER_MSYS64_HOME", ""),
        os.environ.get("COPPER_VIVADO_HOME", ""),
        str(Path.home() / "tools" / "oss-cad-suite"),
        str(Path.home() / "msys64" / "usr"),
        str(Path.home() / "msys64" / "mingw64"),
        str(ROOT / "tools" / "oss-cad-suite"),
        str(ROOT / "tools" / "msys64" / "usr"),
        str(ROOT / "tools" / "msys64" / "mingw64"),
        str(ROOT / ".tools" / "winlibs" / "mingw64"),
        str(ROOT / ".tools" / "oss-cad-suite" / "oss-cad-suite"),
        "C:/AMDDesignTools/2025.2/Vivado",
        "C:/Xilinx/Vivado/2025.2",
        "C:/Xilinx/Vivado/2024.2",
    ]
    names: list[str] = []
    for alias in aliases.get(name, (name,)):
        if platform.system().lower().startswith("win") and not alias.endswith((".exe", ".bat", ".cmd")):
            names.extend((f"{alias}.bat", f"{alias}.exe", f"{alias}.cmd", alias))
        else:
            names.append(alias)
    names = list(dict.fromkeys(names))
    for root in tool_roots:
        if root:
            base = Path(root)
            for candidate in names:
                candidates.extend((base / candidate, base / "bin" / candidate))
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def evidence_id(prefix: str, *parts: str) -> str:
    body = "_".join(re.sub(r"[^A-Za-z0-9]+", "_", str(part)).strip("_").lower() for part in parts if part)
    return f"{prefix}_{body}" if body else prefix


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
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            env=command_env(command),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        return proc.returncode, "$ " + " ".join(command) + "\n" + proc.stdout
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        return 124, "$ " + " ".join(command) + f"\nTIMEOUT after {timeout}s\n" + output


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
        "evidence_id": evidence_id("mapped", design.scope, design.name, target, flow, ENVIRONMENT),
        "scope": design.scope,
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


def vivado_fmax_from_wns(wns: str) -> str:
    try:
        clock_mhz = float(CLOCK_MHZ)
        slack_ns = float(wns)
    except (TypeError, ValueError):
        return ""
    if clock_mhz <= 0:
        return ""
    period_ns = 1000.0 / clock_mhz
    critical_path_ns = period_ns - slack_ns
    if critical_path_ns <= 0:
        return ""
    return f"{1000.0 / critical_path_ns:.3f}"


def value_or_na(value: str) -> str:
    return value if value not in {"", None} else "NA"


def flow_timeout(design: Design) -> int:
    return 900 if design.scope in {"accepted_core_wrapper", "core_wrapper", "full_core"} else 300


def nextpnr_ecp5(design: Design) -> dict[str, str]:
    log_path = LOG_DIR / f"ecp5_{design.name}.log"
    yosys = tool_path("yosys")
    nextpnr = tool_path("nextpnr-ecp5")
    if not yosys or not nextpnr:
        missing = "yosys" if not yosys else "nextpnr-ecp5"
        note = f"BLOCKED: ECP5 mapped PPA requires {missing} on PATH."
        write_text(log_path, note + "\n")
        return blank_row(design, "ecp5-85k", "yosys+nextpnr-ecp5", "BLOCKED", log_path, note)
    missing_sources = [source for source in design.sources if not (ROOT / source).exists()]
    if missing_sources:
        note = f"BLOCKED: missing RTL source(s): {', '.join(missing_sources)}."
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
                timeout=flow_timeout(design),
            )
        else:
            pnr_code, pnr_output = 1, "nextpnr-ecp5 skipped because Yosys ECP5 mapping failed\n"
    output = yosys_output + "\n" + pnr_output
    write_text(log_path, output)
    return mapped_row(design, "ecp5-85k", "yosys+nextpnr-ecp5", yosys_code, pnr_code, log_path, output)


def nextpnr_ice40(design: Design) -> dict[str, str]:
    log_path = LOG_DIR / f"ice40_{design.name}.log"
    yosys = tool_path("yosys")
    nextpnr = tool_path("nextpnr-ice40")
    if not yosys or not nextpnr:
        missing = "yosys" if not yosys else "nextpnr-ice40"
        note = f"BLOCKED: iCE40 mapped PPA requires {missing} on PATH."
        write_text(log_path, note + "\n")
        return blank_row(design, "ice40-hx8k", "yosys+nextpnr-ice40", "BLOCKED", log_path, note)
    missing_sources = [source for source in design.sources if not (ROOT / source).exists()]
    if missing_sources:
        note = f"BLOCKED: missing RTL source(s): {', '.join(missing_sources)}."
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
                timeout=flow_timeout(design),
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
        "evidence_id": evidence_id("mapped", design.scope, design.name, target, flow, ENVIRONMENT),
        "scope": design.scope,
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


def generic_yosys(design: Design) -> dict[str, str]:
    log_path = LOG_DIR / f"generic_yosys_{design.name}.log"
    yosys = tool_path("yosys")
    if not yosys:
        note = "BLOCKED: generic Yosys resource fallback requires yosys on PATH."
        write_text(log_path, note + "\n")
        return blank_row(design, "generic-yosys", "generic-yosys-resource", "BLOCKED", log_path, note)
    missing_sources = [source for source in design.sources if not (ROOT / source).exists()]
    if missing_sources:
        note = f"BLOCKED: missing RTL source(s): {', '.join(missing_sources)}."
        write_text(log_path, note + "\n")
        return blank_row(design, "generic-yosys", "generic-yosys-resource", "BLOCKED", log_path, note)
    script = yosys_script(design, f"synth -top {design.top}; stat")
    code, output = run_capture([yosys, "-p", script], timeout=180)
    write_text(log_path, output)
    counts = parse_cell_counts(output)
    status = "PASS" if code == 0 else "FAIL"
    row = blank_row(
        design,
        "generic-yosys",
        "generic-yosys-resource",
        status,
        log_path,
        (
            "Generic Yosys resource-only fallback. "
            "fmax_mhz/WNS/TNS/power_mw are NA because this is not mapped timing or power."
            if status == "PASS"
            else "FAIL: generic Yosys resource fallback did not complete; see log."
        ),
    )
    row["lut"] = value_or_na(str(sum(value for cell, value in counts.items() if cell.startswith("$_"))) if counts else "")
    row["ff"] = value_or_na(str(sum(value for cell, value in counts.items() if "DFF" in cell.upper())) if counts else "")
    row["cells"] = value_or_na(parse_total_cells(output))
    row["fmax_mhz"] = "NA"
    row["wns"] = "NA"
    row["tns"] = "NA"
    row["power_mw"] = "NA"
    return row


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
    vivado = tool_path("vivado")
    if not vivado:
        note = "BLOCKED: Vivado mapped implementation requires vivado on PATH."
        write_text(log_path, note + "\n")
        return blank_row(design, f"vivado-{VIVADO_PART}", "vivado-impl", "BLOCKED", log_path, note)
    missing_sources = [source for source in design.sources if not (ROOT / source).exists()]
    if missing_sources:
        note = f"BLOCKED: missing RTL source(s): {', '.join(missing_sources)}."
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
    row["fmax_mhz"] = value_or_na(vivado_fmax_from_wns(row["wns"]) or row["fmax_mhz"])
    row["power_mw"] = value_or_na(parse_vivado_power_mw(combined))
    if code == 0:
        row["notes"] = (
            f"Vivado implementation completed at {CLOCK_MHZ} MHz target. "
            "fmax_mhz is derived from report_timing_summary setup slack and the target clock; "
            "power_mw is from report_power when present and is not silicon measurement."
        )
    return row


def openroad_blocked_rows() -> list[dict[str, str]]:
    log_path = OPENROAD_LOG_DIR / "openroad_availability.log"
    openroad = tool_path("openroad")
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
        blank_row(design, "openroad", "openroad-opensta", "BLOCKED", log_path, note)
        for design in MAPPED_DESIGNS
    ]


def fullcore_blocked_rows() -> list[dict[str, str]]:
    log_path = LOG_DIR / "fullcore_wrapper_availability.log"
    note = (
        "BLOCKED: no real full-core RTL integration is present. Accepted core-wrapper rows "
        "are reported separately with scope=accepted_core_wrapper and must not be called full-core PPA."
    )
    write_text(log_path, note + "\n")
    return [
        blank_row(FULLCORE_BASELINE, "full_core", "not_run", "BLOCKED", log_path, note),
        blank_row(FULLCORE_COPPER, "full_core", "not_run", "BLOCKED", log_path, note),
    ]


def matched_pass(rows: list[dict[str, str]], target: str, flow: str, scope: str) -> bool:
    names = {
        "near_core_stub": (NEARCORE_BASELINE.name, NEARCORE_COPPER.name),
        "accepted_core_wrapper": (CORE_WRAPPER_BASELINE.name, CORE_WRAPPER_COPPER.name),
        "core_wrapper": (CORE_WRAPPER_BASELINE.name, CORE_WRAPPER_COPPER.name),
        "unit": (UNIT_BASELINE.name, UNIT_COPPER.name),
    }[scope]
    by_name = {row["design"]: row for row in rows if row["target"] == target and row["flow"] == flow}
    return all(by_name.get(name, {}).get("status") == "PASS" for name in names)


def has_real_timing(row: dict[str, str]) -> bool:
    return any(row.get(field, "").strip().upper() not in {"", "NA"} for field in ("fmax_mhz", "wns", "tns"))


def has_matched_mapped_timing(rows: list[dict[str, str]], scope: str) -> bool:
    pairs = {
        "accepted_core_wrapper": (CORE_WRAPPER_BASELINE.name, CORE_WRAPPER_COPPER.name),
        "near_core_stub": (NEARCORE_BASELINE.name, NEARCORE_COPPER.name),
        "unit": (UNIT_BASELINE.name, UNIT_COPPER.name),
    }
    baseline, copper = pairs[scope]
    by_key: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        if (
            row.get("status") == "PASS"
            and row.get("scope") == scope
            and row.get("flow") not in {"yosys", "not_run", "generic-yosys-resource", ""}
            and has_real_timing(row)
        ):
            by_key.setdefault((row.get("target", ""), row.get("flow", "")), set()).add(row.get("design", ""))
    return any({baseline, copper}.issubset(designs) for designs in by_key.values())


def run_ordered_flows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    rows.extend(fullcore_blocked_rows())
    rows.extend(vivado_impl(design) for design in MAPPED_DESIGNS)
    rows.extend(nextpnr_ecp5(design) for design in MAPPED_DESIGNS)
    rows.extend(nextpnr_ice40(design) for design in MAPPED_DESIGNS)
    rows.extend(openroad_blocked_rows())
    rows.extend(generic_yosys(design) for design in FALLBACK_DESIGNS)
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
            ("near_core_stub", "near_core_stub", NEARCORE_BASELINE.name, NEARCORE_COPPER.name),
            ("full_core", "full_core", FULLCORE_BASELINE.name, FULLCORE_COPPER.name),
            ("accepted_core_wrapper", "accepted_core_wrapper", CORE_WRAPPER_BASELINE.name, CORE_WRAPPER_COPPER.name),
            ("accepted_core_wrapper", "accepted_core_wrapper", CORE_WRAPPER_PREFETCH_BASELINE.name, CORE_WRAPPER_COPPER.name),
            ("unit", "unit", UNIT_BASELINE.name, UNIT_COPPER.name),
        )
        for scope, metric_scope, baseline_name, copper_name in pairs:
            baseline = by_name.get(baseline_name)
            copper = by_name.get(copper_name)
            if not baseline or not copper:
                continue
            if baseline.get("status") != "PASS" or copper.get("status") != "PASS":
                out.append(
                    {
                        "evidence_id": evidence_id("mapped_overhead", metric_scope, "blocked", target, flow, baseline_name, copper_name, ENVIRONMENT),
                        "scope": scope,
                        "design": f"{baseline_name}__vs__{copper_name}",
                        "target": target,
                        "flow": flow,
                        "environment": ENVIRONMENT,
                        "status": "BLOCKED",
                        "metric": f"{metric_scope}_mapped_timing",
                        "baseline": "",
                        "with_copper": "",
                        "delta": "",
                        "percent_overhead": "",
                        "report_path": rel(OUT),
                        "notes": "BLOCKED: matched mapped PPA overhead requires PASS rows for baseline and COPPER.",
                    }
                )
                continue
            for metric in ("lut", "ff", "bram", "dsp", "cells", "fmax_mhz", "wns", "tns", "power_mw"):
                b = numeric(baseline.get(metric, ""))
                c = numeric(copper.get(metric, ""))
                if b is None or c is None:
                    continue
                delta = c - b
                pct = (delta / b * 100.0) if b else 0.0
                out.append(
                    {
                        "evidence_id": evidence_id("mapped_overhead", metric_scope, metric, target, flow, baseline_name, copper_name, ENVIRONMENT),
                        "scope": scope,
                        "design": f"{baseline_name}__vs__{copper_name}",
                        "target": target,
                        "flow": flow,
                        "environment": ENVIRONMENT,
                        "status": "PASS",
                        "metric": f"{metric_scope}_{metric}",
                        "baseline": f"{b:.6f}".rstrip("0").rstrip("."),
                        "with_copper": f"{c:.6f}".rstrip("0").rstrip("."),
                        "delta": f"{delta:.6f}".rstrip("0").rstrip("."),
                        "percent_overhead": f"{pct:.6f}",
                        "report_path": rel(OUT),
                        "notes": "Matched mapped PPA overhead from same target, flow, and constraints.",
                    }
                )
    if not out:
        out.append(
            {
                "evidence_id": evidence_id("mapped_overhead", "near_core_stub", "none", ENVIRONMENT),
                "scope": "near_core_stub",
                "design": f"{NEARCORE_BASELINE.name}__vs__{NEARCORE_COPPER.name}",
                "target": "none",
                "flow": "none",
                "environment": ENVIRONMENT,
                "status": "BLOCKED",
                "metric": "near_core_stub_mapped_timing",
                "baseline": "",
                "with_copper": "",
                "delta": "",
                "percent_overhead": "",
                "report_path": rel(OUT),
                "notes": "BLOCKED: no matched mapped PPA PASS pair was produced.",
            }
        )
    return out


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    rows = run_ordered_flows()
    write_csv(OUT, FIELDS, rows)
    write_csv(OVERHEAD, OVERHEAD_FIELDS, overhead_rows(rows))
    print(f"wrote {rel(OUT)} and {rel(OVERHEAD)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
