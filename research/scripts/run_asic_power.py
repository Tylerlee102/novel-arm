#!/usr/bin/env python3
"""Generate optional ASIC-library timing/power evidence.

This script only marks ASIC rows PASS when a real OpenSTA/OpenROAD binary runs
on a Nangate45 Liberty-mapped netlist and emits a power report. The result is a
standard-cell Liberty tool estimate, not silicon measurement and not signoff
power with extracted parasitics.
"""

from __future__ import annotations

import csv
import hashlib
import os
import platform
import re
import shutil
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "research" / "results"
LOG_DIR = RESULTS / "logs" / "asic_power"
WORK_DIR = RESULTS / "asic_power"
OUT = RESULTS / "asic_power.csv"
OVERHEAD = RESULTS / "asic_power_overhead.csv"

CLOCK_PERIOD_NS = os.environ.get("COPPER_ASIC_CLOCK_PERIOD_NS", "20.0")
ACTIVITY = os.environ.get("COPPER_ASIC_GLOBAL_ACTIVITY", "0.10")
NANGATE_LIB_URL = os.environ.get(
    "COPPER_NANGATE45_LIB_URL",
    "https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-flow-scripts/master/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib",
)


@dataclass(frozen=True)
class Design:
    name: str
    top: str
    sources: tuple[str, ...]
    scope: str
    params: tuple[tuple[str, int], ...] = ()


PICORV32_SOURCES = (
    "external/picorv32/picorv32.v",
    "research/baseline_prefetch_unit.sv",
    "research/copper_prefetch_unit_open.sv",
    "research/rtl/fullcore/picorv32_copper_wrapper.sv",
)

FULLCORE_BLOCKER = (
    "BLOCKED: no real full-core RTL integration is present, so no full-core ASIC "
    "power row is claimed."
)

DESIGNS = (
    Design("full_core_baseline", "", (), "full_core"),
    Design("full_core_plus_copper", "", (), "full_core"),
    Design("baseline_core_wrapper", "baseline_core_wrapper", PICORV32_SOURCES, "core_wrapper"),
    Design(
        "core_wrapper_plus_copper",
        "core_wrapper_plus_copper",
        PICORV32_SOURCES,
        "core_wrapper",
        (("ENTRIES", 8), ("QUEUE_DEPTH", 4)),
    ),
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
    "wns",
    "tns",
    "internal_power_mw",
    "switching_power_mw",
    "leakage_power_mw",
    "total_power_mw",
    "report_path",
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
    return text.replace(str(Path.home()), "{USER_HOME}").replace(Path.home().as_posix(), "{USER_HOME}")


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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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
    except OSError as exc:
        return 127, "$ " + " ".join(command) + f"\n{exc}\n"


def blank_row(design: Design, status: str, report_path: Path, notes: str) -> dict[str, str]:
    return {
        "design": design.name,
        "target": "nangate45",
        "flow": "yosys+opensta-liberty",
        "environment": ENVIRONMENT,
        "status": status,
        "scope": design.scope,
        "cells": "NA",
        "area_um2": "NA",
        "wns": "NA",
        "tns": "NA",
        "internal_power_mw": "NA",
        "switching_power_mw": "NA",
        "leakage_power_mw": "NA",
        "total_power_mw": "NA",
        "report_path": rel(report_path),
        "notes": notes,
    }


def liberty_path() -> tuple[Path | None, str]:
    configured = os.environ.get("COPPER_NANGATE45_LIB", "").strip()
    candidates = []
    if configured:
        candidates.append(Path(configured))
    candidates.extend(
        [
            WORK_DIR / "nangate45" / "NangateOpenCellLibrary_typical.lib",
            ROOT / "external" / "nangate45" / "NangateOpenCellLibrary_typical.lib",
        ]
    )
    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate, f"using existing Nangate45 liberty {rel(candidate) if candidate.is_relative_to(ROOT) else candidate}"

    target = WORK_DIR / "nangate45" / "NangateOpenCellLibrary_typical.lib"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(NANGATE_LIB_URL, target)
    except Exception as exc:
        return None, f"BLOCKED: Nangate45 Liberty download failed from {NANGATE_LIB_URL}: {exc}"
    return target, f"downloaded Nangate45 liberty from OpenROAD-flow-scripts; sha256={sha256(target)}"


def source_reads(design: Design) -> str:
    return " ".join(f"read_verilog -sv {source};" for source in design.sources)


def chparam(design: Design) -> str:
    if not design.params:
        return ""
    settings = " ".join(f"-set {key} {value}" for key, value in design.params)
    return f"chparam {settings} {design.top}; "


def yosys_script(design: Design, liberty: Path, netlist: Path) -> str:
    return (
        f"{source_reads(design)} "
        f"{chparam(design)}"
        f"hierarchy -check -top {design.top}; proc; opt; memory; opt; "
        f"techmap; opt; dfflibmap -liberty {liberty.as_posix()}; "
        f"abc -liberty {liberty.as_posix()}; clean -purge; "
        f"stat -liberty {liberty.as_posix()}; "
        f"write_verilog -noattr -noexpr -nodec -nohex -simple-lhs {netlist.as_posix()}"
    )


def sta_script(design: Design, liberty: Path, netlist: Path) -> str:
    return f"""
read_liberty {liberty.as_posix()}
read_verilog {netlist.as_posix()}
link_design {design.top}
create_clock -name clk -period {CLOCK_PERIOD_NS} [get_ports clk]
set_power_activity -global -activity {ACTIVITY}
report_checks -path_delay max
report_worst_slack -max
report_tns
report_power
exit
""".lstrip()


def parse_total_cells(output: str) -> str:
    matches = re.findall(r"Number of cells:\s+(\d+)", output)
    return matches[-1] if matches else "NA"


def parse_area(output: str) -> str:
    matches = re.findall(r"Chip area for module '[^']+':\s+([0-9.]+)", output)
    return matches[-1] if matches else "NA"


def parse_slack(output: str) -> str:
    patterns = (
        r"worst slack[^-\d]*(-?[0-9.]+)",
        r"wns[^-\d]*(-?[0-9.]+)",
        r"slack\s*\([^)]*\)\s*(-?[0-9.]+)",
    )
    for pattern in patterns:
        matches = re.findall(pattern, output, re.I)
        if matches:
            return matches[-1]
    return "NA"


def parse_tns(output: str) -> str:
    matches = re.findall(r"(?:tns|total negative slack)[^-\d]*(-?[0-9.]+)", output, re.I)
    return matches[-1] if matches else "NA"


def parse_power(output: str) -> tuple[str, str, str, str]:
    total_lines = [line for line in output.splitlines() if re.match(r"\s*Total\b", line)]
    for line in reversed(total_lines):
        numbers = re.findall(r"-?[0-9]+(?:\.[0-9]+)?(?:e[-+]?\d+)?", line, re.I)
        if len(numbers) >= 4:
            internal, switching, leakage, total = numbers[-4:]
            return internal, switching, leakage, total
    return "NA", "NA", "NA", "NA"


def sanitize_verilog_for_opensta(netlist: Path) -> str:
    """Remove declaration signedness that OpenSTA's Verilog reader rejects."""
    text = netlist.read_text(encoding="utf-8", errors="replace")
    cleaned, count = re.subn(r"\b(wire|reg|input|output|inout)\s+signed\b", r"\1", text)
    if count:
        write_raw_text(netlist, cleaned)
    return f"OpenSTA netlist compatibility: removed {count} declaration-level signed keyword(s)."


def netlist_context(output: str, netlist: Path, radius: int = 5) -> str:
    matches = re.findall(rf"{re.escape(str(netlist))}\s+line\s+(\d+)|line\s+(\d+),\s+syntax error", output)
    line_numbers = [int(a or b) for a, b in matches if (a or b)]
    if not line_numbers or not netlist.exists():
        return ""
    lines = netlist.read_text(encoding="utf-8", errors="replace").splitlines()
    line_no = line_numbers[-1]
    start = max(1, line_no - radius)
    end = min(len(lines), line_no + radius)
    excerpt = "\n".join(f"{idx}: {lines[idx - 1]}" for idx in range(start, end + 1))
    return f"\nOpenSTA/OpenROAD netlist parse context around line {line_no}:\n{excerpt}\n"


def run_design(design: Design, liberty: Path, sta_tool: str, sta_kind: str) -> dict[str, str]:
    log_path = LOG_DIR / f"{design.name}.log"
    if design.scope == "full_core":
        write_text(log_path, FULLCORE_BLOCKER + "\n")
        return blank_row(design, "BLOCKED", log_path, FULLCORE_BLOCKER)

    missing_sources = [source for source in design.sources if not (ROOT / source).exists()]
    if missing_sources:
        note = f"BLOCKED: missing RTL source(s): {', '.join(missing_sources)}."
        write_text(log_path, note + "\n")
        return blank_row(design, "BLOCKED", log_path, note)

    yosys = tool_path("yosys")
    if not yosys:
        note = "BLOCKED: ASIC Liberty mapping requires Yosys."
        write_text(log_path, note + "\n")
        return blank_row(design, "BLOCKED", log_path, note)

    design_dir = WORK_DIR / design.name
    design_dir.mkdir(parents=True, exist_ok=True)
    netlist = design_dir / f"{design.name}_nangate45.v"
    sta_tcl = design_dir / "sta_power.tcl"
    synth_code, synth_output = run_capture([yosys, "-p", yosys_script(design, liberty, netlist)], timeout=300)
    if synth_code != 0 or not netlist.exists():
        output = synth_output + "\nOpenSTA/OpenROAD skipped because Yosys Liberty mapping failed.\n"
        write_text(log_path, output)
        row = blank_row(design, "FAIL", log_path, "FAIL: Yosys Liberty mapping did not complete; see log.")
        row["cells"] = parse_total_cells(synth_output)
        row["area_um2"] = parse_area(synth_output)
        return row

    synth_output += "\n" + sanitize_verilog_for_opensta(netlist) + "\n"
    write_raw_text(sta_tcl, sta_script(design, liberty, netlist))
    if sta_kind == "openroad":
        sta_command = [sta_tool, "-exit", str(sta_tcl)]
    else:
        sta_command = [sta_tool, str(sta_tcl)]
    sta_code, sta_output = run_capture(sta_command, timeout=300)
    output = synth_output + "\n" + sta_output
    internal, switching, leakage, total = parse_power(output)
    status = "PASS" if sta_code == 0 and total != "NA" else "FAIL"
    if status == "FAIL":
        output += netlist_context(sta_output, netlist)
    write_text(log_path, output)
    notes = (
        "Nangate45 standard-cell Liberty tool estimate from Yosys mapping plus "
        f"{sta_kind}; clock_period_ns={CLOCK_PERIOD_NS}; global_activity={ACTIVITY}. "
        "This is not silicon measurement, not post-route signoff with extracted parasitics, "
        "and not full-core power."
    )
    if status == "FAIL":
        notes = "FAIL: OpenSTA/OpenROAD did not emit parseable Liberty power; see log."
    return {
        "design": design.name,
        "target": "nangate45",
        "flow": "yosys+opensta-liberty",
        "environment": ENVIRONMENT,
        "status": status,
        "scope": design.scope,
        "cells": parse_total_cells(synth_output),
        "area_um2": parse_area(synth_output),
        "wns": parse_slack(output),
        "tns": parse_tns(output),
        "internal_power_mw": internal,
        "switching_power_mw": switching,
        "leakage_power_mw": leakage,
        "total_power_mw": total,
        "report_path": rel(log_path),
        "notes": notes,
    }


def numeric(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def overhead_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_name = {row["design"]: row for row in rows}
    baseline = by_name.get("baseline_core_wrapper")
    copper = by_name.get("core_wrapper_plus_copper")
    out: list[dict[str, str]] = []
    if not baseline or not copper or baseline.get("status") != "PASS" or copper.get("status") != "PASS":
        return [
            {
                "target": "nangate45",
                "flow": "yosys+opensta-liberty",
                "scope": "core_wrapper",
                "metric": "core_wrapper_asic_liberty_power",
                "baseline": "",
                "with_copper": "",
                "delta": "",
                "percent_overhead": "",
                "notes": "BLOCKED: matched ASIC Liberty power overhead requires PASS rows for baseline and COPPER.",
            }
        ]
    for metric in ("cells", "area_um2", "wns", "tns", "internal_power_mw", "switching_power_mw", "leakage_power_mw", "total_power_mw"):
        b = numeric(baseline.get(metric, ""))
        c = numeric(copper.get(metric, ""))
        if b is None or c is None:
            continue
        delta = c - b
        pct = (delta / b * 100.0) if b else 0.0
        out.append(
            {
                "target": "nangate45",
                "flow": "yosys+opensta-liberty",
                "scope": "core_wrapper",
                "metric": f"core_wrapper_{metric}",
                "baseline": f"{b:.6f}".rstrip("0").rstrip("."),
                "with_copper": f"{c:.6f}".rstrip("0").rstrip("."),
                "delta": f"{delta:.6f}".rstrip("0").rstrip("."),
                "percent_overhead": f"{pct:.6f}",
                "notes": "Matched core-wrapper ASIC Liberty estimate from same library and clock/activity assumptions.",
            }
        )
    return out


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    sta_tool = tool_path("sta")
    sta_kind = "opensta"
    if not sta_tool:
        sta_tool = tool_path("openroad")
        sta_kind = "openroad"
    log_path = LOG_DIR / "asic_power_availability.log"
    rows: list[dict[str, str]] = []
    if not sta_tool:
        note = (
            "BLOCKED: ASIC Liberty power requires OpenSTA `sta` or OpenROAD on PATH. "
            "No standard-cell power is inferred."
        )
        write_text(log_path, note + "\n")
        rows = [blank_row(design, "BLOCKED", log_path, note if design.scope != "full_core" else FULLCORE_BLOCKER) for design in DESIGNS]
    else:
        liberty, liberty_note = liberty_path()
        if not liberty:
            write_text(log_path, liberty_note + "\n")
            rows = [blank_row(design, "BLOCKED", log_path, liberty_note if design.scope != "full_core" else FULLCORE_BLOCKER) for design in DESIGNS]
        else:
            write_text(log_path, f"{sta_kind}={sta_tool}\n{liberty_note}\n")
            rows = [run_design(design, liberty, sta_tool, sta_kind) for design in DESIGNS]
    write_csv(OUT, FIELDS, rows)
    write_csv(OVERHEAD, OVERHEAD_FIELDS, overhead_rows(rows))
    print(f"wrote {rel(OUT)} and {rel(OVERHEAD)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
