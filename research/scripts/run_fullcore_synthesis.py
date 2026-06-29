#!/usr/bin/env python3
"""Run matched core-wrapper/near-core PPA evidence ledgers for COPPER.

Full-core rows remain BLOCKED unless a real full CPU-core integration is
present. The repository may also contain an accepted open-source PicoRV32
core-wrapper, which is labeled as accepted_core_wrapper rather than full_core.
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
INVENTORY = RESULTS / "full_core_design_inventory.csv"
TARGET_INVENTORY = RESULTS / "full_core_target_inventory.csv"


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
    "BLOCKED: the PicoRV32 tiny-SoC full-core RTL target requires both "
    "full_core_baseline and full_core_plus_copper sources plus an available "
    "synthesis/mapped flow. No full-core row is claimed unless the matched "
    "full_core rows pass."
)

PICORV32_SOURCES = (
    "external/picorv32/picorv32.v",
    "research/baseline_prefetch_unit.sv",
    "research/copper_prefetch_unit_open.sv",
    "research/rtl/fullcore/picorv32_copper_wrapper.sv",
)

PICORV32_FULLCORE_SOURCES = (
    "external/picorv32/picorv32.v",
    "research/copper_prefetch_unit_open.sv",
    "research/rtl/fullcore/picorv32_full_core_soc.sv",
)

FULL_CORE_SEARCH_PATHS = (
    "research/rtl/fullcore",
    "research/rtl/integration",
    "external",
)

DESIGNS = (
    Design(
        "full_core_baseline",
        "full_core_baseline",
        PICORV32_FULLCORE_SOURCES,
        "full_core",
        "picorv32_tiny_soc",
        True,
        "",
        (("MEM_WORDS", 64),),
    ),
    Design(
        "full_core_plus_copper",
        "full_core_plus_copper",
        PICORV32_FULLCORE_SOURCES,
        "full_core",
        "picorv32_tiny_soc",
        True,
        "",
        (("MEM_WORDS", 64), ("ENTRIES", 8), ("QUEUE_DEPTH", 4)),
    ),
    Design(
        "baseline_core_wrapper",
        "baseline_core_wrapper",
        PICORV32_SOURCES,
        "accepted_core_wrapper",
        "picorv32_core_wrapper",
        True,
    ),
    Design(
        "core_wrapper_plus_baseline_prefetch",
        "core_wrapper_plus_baseline_prefetch",
        PICORV32_SOURCES,
        "accepted_core_wrapper",
        "picorv32_core_wrapper",
        True,
    ),
    Design(
        "core_wrapper_plus_copper",
        "core_wrapper_plus_copper",
        PICORV32_SOURCES,
        "accepted_core_wrapper",
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


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def evidence_id(prefix: str, *parts: str) -> str:
    body = "_".join(re.sub(r"[^A-Za-z0-9]+", "_", str(part)).strip("_").lower() for part in parts if part)
    return f"{prefix}_{body}" if body else prefix


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


def sources_present(sources: tuple[str, ...]) -> bool:
    return bool(sources) and all((ROOT / source).exists() for source in sources)


def inventory_rows() -> list[dict[str, str]]:
    scan_notes = (
        "Scanned research/rtl/fullcore, research/rtl/integration, and external/picorv32. "
        "The PicoRV32 tiny-SoC full-core harness is the open-source full_core target; "
        "the older NOP tie-off PicoRV32 wrapper remains accepted_core_wrapper only."
    )
    rows: list[dict[str, str]] = []
    for design in DESIGNS:
        if design.scope == "full_core":
            available = "yes" if sources_present(design.sources) else "no"
            qualifies = "yes" if available == "yes" else "no"
            status = "AVAILABLE" if available == "yes" else "BLOCKED"
            role = "picorv32_tiny_soc_full_core"
            notes = (
                "Open-source PicoRV32 tiny-SoC full-core harness with real local instruction/data "
                "memory and matched baseline/COPPER top modules. This is not production ARM, "
                "OoO, silicon, or signoff evidence. "
                + scan_notes
            )
        elif design.scope == "accepted_core_wrapper":
            available = "yes" if sources_present(design.sources) else "no"
            qualifies = "no"
            status = "AVAILABLE" if available == "yes" else "BLOCKED"
            role = "accepted_core_wrapper_fallback"
            notes = (
                "Accepted PicoRV32 core-wrapper fallback with real PicoRV32 RTL plus wrapper/prefetch sources. "
                "This is stronger than a stub but is not the target true full-core integration."
            )
        elif design.scope == "near_core_stub":
            available = "yes" if sources_present(design.sources) else "no"
            qualifies = "no"
            status = "AVAILABLE" if available == "yes" else "BLOCKED"
            role = "near_core_stub_fallback"
            notes = "Near-core stub fallback; not a full CPU/core integration."
        else:
            available = "no"
            qualifies = "no"
            status = "BLOCKED"
            role = "unknown"
            notes = "Unsupported scope in design inventory."
        rows.append(
            {
                "evidence_id": evidence_id("full_core_inventory", design.scope, design.name, design.target, ENVIRONMENT),
                "scope": design.scope,
                "design": design.name,
                "target": design.target,
                "flow": "inventory",
                "environment": ENVIRONMENT,
                "status": status,
                "available": available,
                "qualifies_true_full_core": qualifies,
                "role": role,
                "top": design.top,
                "rtl_sources": ";".join(design.sources),
                "search_paths": ";".join(FULL_CORE_SEARCH_PATHS),
                "report_path": rel(INVENTORY),
                "notes": notes,
            }
        )
    return rows


def row_for(design: Design, status: str, report_path: Path, notes: str, cells: str = "", lut: str = "", ff: str = "") -> dict[str, str]:
    return {
        "evidence_id": evidence_id("fullcore", design.scope, design.name, design.target, "yosys" if design.runnable else "not_run", ENVIRONMENT),
        "scope": design.scope,
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

    yosys = tool_path("yosys")
    if not yosys:
        note = (
            f"BLOCKED: {design.scope} synthesis requires Yosys on PATH. "
            "No cells, timing, or power are inferred."
        )
        write_log(log_path, note + "\n")
        return row_for(design, "BLOCKED", log_path, note)

    command = [yosys, "-p", yosys_script(design)]
    proc = subprocess.run(
        command,
        cwd=ROOT,
        env=command_env(command),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=180,
    )
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
        ("accepted_core_wrapper_cells_baseline_vs_copper", "baseline_core_wrapper", "core_wrapper_plus_copper", "accepted_core_wrapper"),
        ("accepted_core_wrapper_cells_prefetch_baseline_vs_copper", "core_wrapper_plus_baseline_prefetch", "core_wrapper_plus_copper", "accepted_core_wrapper"),
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
                    "evidence_id": evidence_id("fullcore_overhead", scope, metric, baseline_name, copper_name, baseline.get("target", "generic"), baseline.get("flow", "yosys"), ENVIRONMENT),
                    "scope": scope,
                    "design": f"{baseline_name}__vs__{copper_name}",
                    "status": "PASS",
                    "metric": metric,
                    "baseline": f"{b:.0f}",
                    "with_copper": f"{c:.0f}",
                    "delta": f"{c - b:.0f}",
                    "percent_overhead": f"{((c - b) / b * 100.0) if b else 0.0:.6f}",
                    "report_path": rel(OUT),
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
                    "evidence_id": evidence_id("fullcore_overhead", scope, metric, baseline_name, copper_name, baseline.get("target", "generic"), baseline.get("flow", "not_run"), ENVIRONMENT),
                    "scope": scope,
                    "design": f"{baseline_name}__vs__{copper_name}",
                    "status": "BLOCKED",
                    "metric": metric,
                    "baseline": baseline.get("cells", ""),
                    "with_copper": copper.get("cells", ""),
                    "delta": "",
                    "percent_overhead": "",
                    "report_path": rel(OUT),
                    "notes": reason,
                }
            )
    return out


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    inventory_fields = [
        "evidence_id",
        "scope",
        "design",
        "target",
        "flow",
        "environment",
        "status",
        "available",
        "qualifies_true_full_core",
        "role",
        "top",
        "rtl_sources",
        "search_paths",
        "report_path",
        "notes",
    ]
    inventory = inventory_rows()
    write_csv(
        INVENTORY,
        inventory_fields,
        inventory,
    )
    write_csv(TARGET_INVENTORY, inventory_fields, inventory)
    rows = [run_design(design) for design in DESIGNS]
    write_csv(
        OUT,
        [
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
        ],
        rows,
    )
    write_csv(
        OVERHEAD,
        [
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
        ],
        overhead_rows(rows),
    )
    print(f"wrote {rel(INVENTORY)}, {rel(TARGET_INVENTORY)}, {rel(OUT)}, and {rel(OVERHEAD)}")
    return 1 if any(row["status"] == "FAIL" for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
