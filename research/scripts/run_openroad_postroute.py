#!/usr/bin/env python3
"""Generate optional OpenROAD post-route core-wrapper evidence.

Rows are PASS only when OpenROAD-flow-scripts completes route plus final
reporting for matched PicoRV32 core-wrapper baseline/COPPER designs and emits
parseable timing and power from the post-route report. This is an open PDK
tool estimate, not silicon measurement and not full-core signoff.
"""

from __future__ import annotations

import csv
import json
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
LOG_DIR = RESULTS / "logs" / "openroad_postroute"
OUT = RESULTS / "openroad_postroute_power.csv"
OVERHEAD = RESULTS / "openroad_postroute_power_overhead.csv"

ORFS_URL = os.environ.get(
    "COPPER_ORFS_URL",
    "https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git",
)
ORFS_REF = os.environ.get(
    "COPPER_ORFS_REF",
    "8ae3ae362e2e9be94ab1d27b3dd647c8328a783f",
)
CLOCK_PERIOD_NS = os.environ.get("COPPER_OPENROAD_CLOCK_PERIOD_NS", "20.0")
CORE_UTILIZATION = os.environ.get("COPPER_OPENROAD_CORE_UTILIZATION", "35")
PLACE_DENSITY = os.environ.get("COPPER_OPENROAD_PLACE_DENSITY", "0.30")


@dataclass(frozen=True)
class Design:
    name: str
    top: str
    sources: tuple[str, ...]
    scope: str


PICORV32_SOURCES = (
    "external/picorv32/picorv32.v",
    "research/baseline_prefetch_unit.sv",
    "research/copper_prefetch_unit_open.sv",
    "research/rtl/fullcore/picorv32_copper_wrapper.sv",
)

FULLCORE_BLOCKER = (
    "BLOCKED: no real full-core RTL integration is present, so no full-core "
    "post-route ASIC PPA/power row is claimed."
)

DESIGNS = (
    Design("full_core_baseline", "", (), "full_core"),
    Design("full_core_plus_copper", "", (), "full_core"),
    Design("baseline_core_wrapper", "baseline_core_wrapper", PICORV32_SOURCES, "core_wrapper"),
    Design("core_wrapper_plus_copper", "core_wrapper_plus_copper", PICORV32_SOURCES, "core_wrapper"),
)

FIELDS = [
    "design",
    "target",
    "flow",
    "environment",
    "status",
    "scope",
    "cells",
    "area_um2",
    "die_area_um2",
    "utilization_pct",
    "wns",
    "tns",
    "fmax_mhz",
    "internal_power_mw",
    "switching_power_mw",
    "leakage_power_mw",
    "total_power_mw",
    "report_path",
    "orfs_ref",
    "notes",
]
OVERHEAD_FIELDS = [
    "target",
    "flow",
    "scope",
    "metric",
    "baseline",
    "with_copper",
    "delta",
    "percent_overhead",
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


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def scrub(text: str) -> str:
    home = Path.home()
    return text.replace(str(home), "{USER_HOME}").replace(home.as_posix(), "{USER_HOME}")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(scrub(text), encoding="utf-8")


def write_raw_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def tool_path(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    candidates: list[Path] = []
    oss_roots = [
        os.environ.get("COPPER_OSS_CAD_SUITE", ""),
        str(Path.home() / "tools" / "oss-cad-suite"),
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


def command_env(extra_paths: list[str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    paths = list(extra_paths or [])
    for tool in ("openroad", "yosys"):
        found = tool_path(tool)
        if found:
            tool_dir = str(Path(found).parent)
            paths.append(tool_dir)
            if tool == "openroad":
                env["OPENROAD_EXE"] = found
            elif tool == "yosys":
                env["YOSYS_EXE"] = found
    if paths:
        env["PATH"] = os.pathsep.join(paths + [env.get("PATH", "")])
    return env


def run_capture(command: list[str], timeout: int, cwd: Path | None = None) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            command,
            cwd=cwd or ROOT,
            env=command_env(),
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
    except OSError as exc:
        return 127, "$ " + " ".join(command) + f"\n{exc}\n"


def blank_row(design: Design, status: str, report_path: Path, notes: str) -> dict[str, str]:
    return {
        "design": design.name,
        "target": "nangate45",
        "flow": "openroad-flow-scripts-postroute",
        "environment": ENVIRONMENT,
        "status": status,
        "scope": design.scope,
        "cells": "NA",
        "area_um2": "NA",
        "die_area_um2": "NA",
        "utilization_pct": "NA",
        "wns": "NA",
        "tns": "NA",
        "fmax_mhz": "NA",
        "internal_power_mw": "NA",
        "switching_power_mw": "NA",
        "leakage_power_mw": "NA",
        "total_power_mw": "NA",
        "report_path": rel(report_path),
        "orfs_ref": ORFS_REF,
        "notes": notes,
    }


def dependency_blocker() -> str | None:
    required = {
        "git": shutil.which("git"),
        "make": shutil.which("make"),
        "bash": shutil.which("bash"),
        "yosys": tool_path("yosys"),
        "openroad": tool_path("openroad"),
    }
    missing = [name for name, path in required.items() if not path]
    if missing:
        return "BLOCKED: OpenROAD post-route flow requires " + ", ".join(missing) + " on PATH."
    return None


def prepare_orfs(parent: Path) -> tuple[Path | None, str]:
    configured = os.environ.get("COPPER_ORFS_HOME", "").strip()
    if configured:
        flow = Path(configured) / "flow"
        if (flow / "Makefile").exists():
            return flow, f"using configured OpenROAD-flow-scripts at {configured}"
        return None, f"BLOCKED: COPPER_ORFS_HOME does not contain flow/Makefile: {configured}"

    git = shutil.which("git")
    if not git:
        return None, "BLOCKED: git is required to fetch OpenROAD-flow-scripts."
    repo = parent / "OpenROAD-flow-scripts"
    init_code, init_output = run_capture([git, "init", str(repo)], timeout=60)
    if init_code != 0:
        return None, init_output
    commands = [
        [git, "-C", str(repo), "remote", "add", "origin", ORFS_URL],
        [git, "-C", str(repo), "fetch", "--depth", "1", "origin", ORFS_REF],
        [git, "-C", str(repo), "checkout", "--detach", "FETCH_HEAD"],
    ]
    output = init_output
    for command in commands:
        code, text = run_capture(command, timeout=300)
        output += "\n" + text
        if code != 0:
            return None, output
    flow = repo / "flow"
    if not (flow / "Makefile").exists():
        return None, output + "\nBLOCKED: fetched ORFS tree has no flow/Makefile.\n"
    return flow, output


def design_config(design: Design, config_dir: Path, work_home: Path) -> Path:
    config = config_dir / design.name / "config.mk"
    sdc = config_dir / design.name / "constraint.sdc"
    config.parent.mkdir(parents=True, exist_ok=True)
    sources = " ".join((ROOT / source).as_posix() for source in design.sources)
    write_raw_text(
        sdc,
        f"""
current_design {design.top}
set clk_name core_clock
set clk_port_name clk
set clk_period {CLOCK_PERIOD_NS}
set clk_io_pct 0.2

set clk_port [get_ports $clk_port_name]
create_clock -name $clk_name -period $clk_period $clk_port
set clk_io_name vclk_$clk_name
create_clock -name $clk_io_name -period $clk_period
set_clock_latency 0.070 [get_clocks $clk_name]
set_clock_latency 0.070 [get_clocks $clk_io_name]

set non_clock_inputs [all_inputs -no_clocks]
set_input_delay [expr $clk_period * $clk_io_pct] -clock $clk_io_name $non_clock_inputs
set_output_delay [expr $clk_period * $clk_io_pct] -clock $clk_io_name [all_outputs]
""".lstrip(),
    )
    write_raw_text(
        config,
        f"""
export DESIGN_NAME = {design.top}
export DESIGN_NICKNAME = {design.name}
export PLATFORM = nangate45
export VERILOG_FILES = {sources}
export SDC_FILE = {sdc.as_posix()}
export WORK_HOME = {work_home.as_posix()}
export FLOW_VARIANT = base
export ABC_AREA = 1
export ADDER_MAP_FILE :=
export CORE_UTILIZATION ?= {CORE_UTILIZATION}
export PLACE_DENSITY ?= {PLACE_DENSITY}
export PLACE_DENSITY_LB_ADDON = 0.20
export TNS_END_PERCENT = 100
export SYNTH_REPEATABLE_BUILD ?= 1
export PDN_TCL ?= $(PLATFORM_DIR)/grid_strategy-M1-M4-M7.tcl
""".lstrip(),
    )
    return config


def collect_text(paths: list[Path]) -> str:
    chunks = []
    for path in paths:
        if path.exists() and path.is_file():
            chunks.append(f"\n===== {path.name} =====\n")
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "".join(chunks)


def copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists() and src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())


def copy_evidence(work_home: Path, design: Design, config: Path, evidence_dir: Path, make_output: str) -> tuple[Path, str]:
    design_dir = Path("nangate45") / design.name / "base"
    reports = work_home / "reports" / design_dir
    logs = work_home / "logs" / design_dir
    results = work_home / "results" / design_dir
    evidence_dir.mkdir(parents=True, exist_ok=True)
    write_text(evidence_dir / "orfs_make.log", make_output)
    copy_if_exists(config, evidence_dir / "config.mk")
    copy_if_exists(config.parent / "constraint.sdc", evidence_dir / "constraint.sdc")
    for source_dir in (reports, logs):
        if source_dir.exists():
            for path in source_dir.rglob("*"):
                if path.is_file() and path.suffix.lower() in {".rpt", ".log", ".json"}:
                    copy_if_exists(path, evidence_dir / source_dir.name / path.relative_to(source_dir))
    for name in ("5_route.def", "6_final.def", "6_final.spef", "6_final.v"):
        copy_if_exists(results / name, evidence_dir / "results" / name)
    text_paths = [evidence_dir / "orfs_make.log"]
    text_paths.extend(sorted(evidence_dir.rglob("*.rpt")))
    text_paths.extend(sorted(evidence_dir.rglob("*.log")))
    return evidence_dir / "orfs_make.log", collect_text(text_paths)


def parse_first_float(patterns: tuple[str, ...], text: str) -> str:
    for pattern in patterns:
        matches = re.findall(pattern, text, re.I | re.M)
        if matches:
            value = matches[-1]
            if isinstance(value, tuple):
                value = next((part for part in reversed(value) if part), "")
            return str(value)
    return "NA"


def parse_report_section_number(section: str, text: str) -> str:
    pattern = rf"{re.escape(section)}\s*\n[-=]+\s*\n\s*(-?[0-9]+(?:\.[0-9]+)?)"
    matches = re.findall(pattern, text, re.I)
    return matches[-1] if matches else "NA"


def parse_power(text: str) -> tuple[str, str, str, str]:
    lines = text.splitlines()
    report_power_lines: list[str] = []
    for idx, line in enumerate(lines):
        if "report_power" in line.lower():
            report_power_lines.extend(lines[idx : idx + 40])
    search_lines = report_power_lines or lines
    total_lines = [line for line in search_lines if re.match(r"\s*Total\b", line)]
    for line in reversed(total_lines):
        numbers = re.findall(r"-?[0-9]+(?:\.[0-9]+)?(?:e[-+]?\d+)?", line, re.I)
        if len(numbers) >= 4:
            watts = [float(value) for value in numbers[:4]]
            return tuple(f"{value * 1000.0:.6g}" for value in watts)  # type: ignore[return-value]
    return "NA", "NA", "NA", "NA"


def parse_cells(text: str) -> str:
    totals = re.findall(r"^\s*Total\s+([0-9]+)\s+[0-9.]+\s*$", text, re.I | re.M)
    if totals:
        return totals[-1]
    matches = re.findall(r"^\s*(?:Number of cells:|Insts:)\s*([0-9]+)\s*$", text, re.I | re.M)
    if matches:
        return matches[-1]
    return "NA"


def parse_area(text: str) -> str:
    return parse_first_float(
        (
            r"Design area\s+([0-9.]+)\s+u\^?2",
            r"Chip area for module '[^']+':\s+([0-9.]+)",
            r"area[_ ]um2[^0-9.]*([0-9.]+)",
        ),
        text,
    )


def fmt(value: object, scale: float = 1.0) -> str:
    try:
        return f"{float(value) * scale:.6g}"
    except (TypeError, ValueError):
        return "NA"


def report_json_path(report_path: Path) -> Path | None:
    candidates = sorted(report_path.parent.rglob("6_report.json"))
    return candidates[-1] if candidates else None


def parse_json_metrics(report_path: Path) -> dict[str, str]:
    json_path = report_json_path(report_path)
    if not json_path:
        return {}
    try:
        metrics = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    def value(*keys: str) -> object:
        for key in keys:
            if key in metrics:
                return metrics[key]
        return None

    out = {
        "cells": fmt(value("finish__design__instance__count__stdcell", "finish__design__instance__count")),
        "area_um2": fmt(value("finish__design__instance__area__stdcell", "finish__design__instance__area")),
        "die_area_um2": fmt(value("finish__design__die__area")),
        "utilization_pct": fmt(value("finish__design__instance__utilization__stdcell", "finish__design__instance__utilization"), 100.0),
        "wns": fmt(value("finish__timing__setup__ws")),
        "tns": fmt(value("finish__timing__setup__tns")),
        "internal_power_mw": fmt(value("finish__power__internal__total"), 1000.0),
        "switching_power_mw": fmt(value("finish__power__switching__total"), 1000.0),
        "leakage_power_mw": fmt(value("finish__power__leakage__total"), 1000.0),
        "total_power_mw": fmt(value("finish__power__total"), 1000.0),
        "flow_errors": fmt(value("finish__flow__errors__count")),
    }
    try:
        period_ns = float(CLOCK_PERIOD_NS)
        slack_ns = float(out["wns"])
        critical_ns = period_ns - slack_ns
        out["fmax_mhz"] = f"{1000.0 / critical_ns:.3f}" if critical_ns > 0 else "NA"
    except ValueError:
        out["fmax_mhz"] = "NA"
    return {key: value for key, value in out.items() if value != "NA"}


def parse_design(design: Design, code: int, report_path: Path, text: str) -> dict[str, str]:
    internal, switching, leakage, total = parse_power(text)
    wns = parse_first_float((r"wns\s+(-?[0-9.]+)", r"worst slack\s+(-?[0-9.]+)"), text)
    if wns == "NA":
        wns = parse_report_section_number("finish report_wns", text)
    if wns == "NA":
        wns = parse_report_section_number("finish report_worst_slack", text)
    tns = parse_first_float((r"tns\s+(-?[0-9.]+)", r"total negative slack\s+(-?[0-9.]+)"), text)
    if tns == "NA":
        tns = parse_report_section_number("finish report_tns", text)
    fmax_period = parse_first_float((r"clock min period[^0-9.]*([0-9.]+)", r"period_min[^0-9.]*([0-9.]+)"), text)
    if fmax_period == "NA":
        fmax_period = parse_report_section_number("finish report_clock_min_period", text)
    fmax = "NA"
    try:
        period = float(fmax_period)
        if period > 0:
            fmax = f"{1000.0 / period:.3f}"
    except ValueError:
        pass
    json_metrics = parse_json_metrics(report_path)
    cells = json_metrics.get("cells", parse_cells(text))
    area = json_metrics.get("area_um2", parse_area(text))
    die_area = json_metrics.get("die_area_um2", "NA")
    utilization = json_metrics.get("utilization_pct", "NA")
    wns = json_metrics.get("wns", wns)
    tns = json_metrics.get("tns", tns)
    fmax = json_metrics.get("fmax_mhz", fmax)
    internal = json_metrics.get("internal_power_mw", internal)
    switching = json_metrics.get("switching_power_mw", switching)
    leakage = json_metrics.get("leakage_power_mw", leakage)
    total = json_metrics.get("total_power_mw", total)
    flow_errors = json_metrics.get("flow_errors", "0")
    status = "PASS" if code == 0 and flow_errors == "0" and total != "NA" and (wns != "NA" or tns != "NA" or fmax != "NA") else "FAIL"
    notes = (
        "OpenROAD-flow-scripts route plus final timing/power reports completed for PicoRV32 core_wrapper; "
        f"clock_period_ns={CLOCK_PERIOD_NS}; core_utilization={CORE_UTILIZATION}; "
        f"place_density={PLACE_DENSITY}; ORFS ref={ORFS_REF}. This is post-route "
        "OpenROAD/Nangate45 tool-estimated power/timing, not silicon measurement, "
        "not foundry signoff, and not full-core power. GDS/image export is not required "
        "for this row."
    )
    if status == "FAIL":
        notes = "FAIL: OpenROAD-flow-scripts did not complete route/final report or did not emit parseable timing and power."
    return {
        "design": design.name,
        "target": "nangate45",
        "flow": "openroad-flow-scripts-postroute",
        "environment": ENVIRONMENT,
        "status": status,
        "scope": design.scope,
        "cells": cells,
        "area_um2": area,
        "die_area_um2": die_area,
        "utilization_pct": utilization,
        "wns": wns,
        "tns": tns,
        "fmax_mhz": fmax,
        "internal_power_mw": internal,
        "switching_power_mw": switching,
        "leakage_power_mw": leakage,
        "total_power_mw": total,
        "report_path": rel(report_path),
        "orfs_ref": ORFS_REF,
        "notes": notes,
    }


def run_design(design: Design, flow_home: Path, temp_root: Path) -> dict[str, str]:
    log_path = LOG_DIR / design.name / "orfs_make.log"
    if design.scope == "full_core":
        write_text(log_path, FULLCORE_BLOCKER + "\n")
        return blank_row(design, "BLOCKED", log_path, FULLCORE_BLOCKER)

    missing_sources = [source for source in design.sources if not (ROOT / source).exists()]
    if missing_sources:
        note = f"BLOCKED: missing RTL source(s): {', '.join(missing_sources)}."
        write_text(log_path, note + "\n")
        return blank_row(design, "BLOCKED", log_path, note)

    config_root = temp_root / "designs"
    work_home = temp_root / "work" / design.name
    config = design_config(design, config_root, work_home)
    make = shutil.which("make") or "make"
    route_code, route_output = run_capture(
        [make, "-C", str(flow_home), f"DESIGN_CONFIG={config}", "route"],
        timeout=2400,
    )
    finish_code = 1
    finish_output = "OpenROAD final reporting skipped because route failed.\n"
    if route_code == 0:
        finish_code, finish_output = run_capture(
            [make, "-C", str(flow_home), f"DESIGN_CONFIG={config}", "do-finish"],
            timeout=900,
        )
    combined = route_output + "\n" + finish_output
    report_path, text = copy_evidence(work_home, design, config, LOG_DIR / design.name, combined)
    return parse_design(design, route_code, report_path, text)


def numeric(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def overhead_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_name = {row["design"]: row for row in rows}
    baseline = by_name.get("baseline_core_wrapper")
    copper = by_name.get("core_wrapper_plus_copper")
    if not baseline or not copper or baseline.get("status") != "PASS" or copper.get("status") != "PASS":
        return [
            {
                "target": "nangate45",
                "flow": "openroad-flow-scripts-postroute",
                "scope": "core_wrapper",
                "metric": "core_wrapper_openroad_postroute_power",
                "baseline": "",
                "with_copper": "",
                "delta": "",
                "percent_overhead": "",
                "notes": "BLOCKED: matched OpenROAD post-route overhead requires PASS rows for baseline and COPPER.",
            }
        ]

    out: list[dict[str, str]] = []
    for metric in ("cells", "area_um2", "wns", "tns", "fmax_mhz", "internal_power_mw", "switching_power_mw", "leakage_power_mw", "total_power_mw"):
        b = numeric(baseline.get(metric, ""))
        c = numeric(copper.get(metric, ""))
        if b is None or c is None:
            continue
        delta = c - b
        pct = (delta / b * 100.0) if b else 0.0
        out.append(
            {
                "target": "nangate45",
                "flow": "openroad-flow-scripts-postroute",
                "scope": "core_wrapper",
                "metric": f"core_wrapper_openroad_postroute_{metric}",
                "baseline": f"{b:.6f}".rstrip("0").rstrip("."),
                "with_copper": f"{c:.6f}".rstrip("0").rstrip("."),
                "delta": f"{delta:.6f}".rstrip("0").rstrip("."),
                "percent_overhead": f"{pct:.6f}",
                "notes": "Matched core-wrapper OpenROAD post-route estimate from same ORFS ref, platform, and constraints.",
            }
        )
    return out


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    blocker = dependency_blocker()
    if blocker:
        log_path = LOG_DIR / "openroad_postroute_availability.log"
        write_text(log_path, blocker + "\n")
        rows = [blank_row(design, "BLOCKED", log_path, blocker if design.scope != "full_core" else FULLCORE_BLOCKER) for design in DESIGNS]
        write_csv(OUT, FIELDS, rows)
        write_csv(OVERHEAD, OVERHEAD_FIELDS, overhead_rows(rows))
        print(f"wrote {rel(OUT)} and {rel(OVERHEAD)}")
        return 0

    with tempfile.TemporaryDirectory(prefix="copper_orfs_") as tmp:
        temp_root = Path(tmp)
        flow_home, note = prepare_orfs(temp_root)
        write_text(LOG_DIR / "orfs_fetch.log", note + "\n")
        if not flow_home:
            rows = [
                blank_row(
                    design,
                    "BLOCKED",
                    LOG_DIR / "orfs_fetch.log",
                    note if design.scope != "full_core" else FULLCORE_BLOCKER,
                )
                for design in DESIGNS
            ]
        else:
            rows = [run_design(design, flow_home, temp_root) for design in DESIGNS]
    write_csv(OUT, FIELDS, rows)
    write_csv(OVERHEAD, OVERHEAD_FIELDS, overhead_rows(rows))
    print(f"wrote {rel(OUT)} and {rel(OVERHEAD)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
