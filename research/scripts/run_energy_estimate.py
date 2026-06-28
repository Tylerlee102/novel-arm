#!/usr/bin/env python3
"""Generate a clearly labeled COPPER energy proxy.

This is not measured silicon or EDA power. It is a memory-traffic proxy using
explicit per-access assumptions and the core_integrated traffic/performance CSVs.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, median


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "research" / "results"
LOG_DIR = RESULTS / "logs" / "energy"
TRAFFIC = RESULTS / "core_integrated_memory_traffic.csv"
PERF = RESULTS / "core_integrated_performance.csv"
OUT = RESULTS / "energy_proxy.csv"
SUMMARY = RESULTS / "energy_summary.csv"
POWER_INDEX = RESULTS / "power_report_index.csv"
MAPPED_PPA = RESULTS / "mapped_ppa.csv"
ASIC_POWER = RESULTS / "asic_power.csv"
OPENROAD_POSTROUTE_POWER = RESULTS / "openroad_postroute_power.csv"
MCPAT_CSV = RESULTS / "copper_mcpat_sensitivity_20260618.csv"
MCPAT_MD = RESULTS / "COPPER_MCPAT_SENSITIVITY_20260618.md"

DEMAND_ACCESS_PJ = 120.0
PREFETCH_ACCESS_PJ = 120.0
LOGIC_CYCLE_PJ = 0.05
SOURCE = "explicit_local_assumption_not_measured"
ASSUMPTIONS = (
    "proxy_assumed_memory_energy; source=explicit_local_assumption_not_measured;"
    " demand_access_pj=120.0; prefetch_access_pj=120.0; logic_cycle_pj=0.05;"
    " not calibrated to silicon, CACTI, McPAT, Vivado, or a process library"
)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def positive_float(value: str) -> bool:
    try:
        return float(value) > 0.0
    except (TypeError, ValueError):
        return False


def fpga_tool_power_evidence() -> dict[str, str] | None:
    evidence: list[tuple[Path, dict[str, str]]] = []
    for path in (MAPPED_PPA, RESULTS / "synthesis.csv", RESULTS / "fullcore_synthesis.csv"):
        for row in read_csv(path):
            report = row.get("report_path", "")
            report_path = ROOT / report if report else Path()
            if (
                row.get("status") == "PASS"
                and positive_float(row.get("power_mw", ""))
                and report
                and report_path.exists()
            ):
                evidence.append((path, row))
    if not evidence:
        return None

    def priority(item: tuple[Path, dict[str, str]]) -> tuple[int, int]:
        row = item[1]
        design = row.get("design", "")
        target = row.get("target", "")
        if design == "core_wrapper_plus_copper" and target.startswith("vivado-"):
            return (0, 0)
        if "core_wrapper" in design and target.startswith("vivado-"):
            return (1, 0)
        if target.startswith("vivado-"):
            return (2, 0)
        return (3, 0)

    evidence.sort(key=priority)
    first_path, first_row = evidence[0]
    designs = "; ".join(
        f"{row.get('design', '')} on {row.get('target', '')} power_mw={row.get('power_mw', '')}"
        for _, row in evidence[:4]
    )
    return {
        "source": "; ".join(sorted({rel(path) for path, _ in evidence})),
        "report_path": first_row.get("report_path", ""),
        "tool": first_row.get("flow", ""),
        "environment": first_row.get("environment", "current"),
        "notes": (
            f"FPGA tool-estimated power rows found: {designs}. "
            "Treat as Vivado/EDA report power for the stated mapped FPGA target, not silicon "
            "measurement, ASIC signoff, or full-core power."
        ),
    }


def asic_liberty_power_evidence() -> dict[str, str] | None:
    rows = [
        row
        for row in read_csv(ASIC_POWER)
        if row.get("status") == "PASS"
        and row.get("scope") == "core_wrapper"
        and positive_float(row.get("total_power_mw", ""))
        and row.get("report_path")
        and (ROOT / row.get("report_path", "")).exists()
    ]
    if not rows:
        return None

    def priority(row: dict[str, str]) -> tuple[int, str]:
        design = row.get("design", "")
        if design == "core_wrapper_plus_copper":
            return (0, design)
        if design == "baseline_core_wrapper":
            return (1, design)
        return (2, design)

    rows.sort(key=priority)
    first = rows[0]
    designs = "; ".join(
        f"{row.get('design', '')} total_power_mw={row.get('total_power_mw', '')}"
        for row in rows[:4]
    )
    return {
        "source": rel(ASIC_POWER),
        "report_path": first.get("report_path", ""),
        "tool": first.get("flow", ""),
        "environment": first.get("environment", "current"),
        "notes": (
            f"ASIC standard-cell Liberty tool estimate rows found: {designs}. "
            "This is a Nangate45 Liberty estimate from a tool report, not silicon measurement, "
            "not post-route signoff with extracted parasitics, and not full-core power."
        ),
    }


def openroad_postroute_power_evidence() -> dict[str, str] | None:
    rows = [
        row
        for row in read_csv(OPENROAD_POSTROUTE_POWER)
        if row.get("status") == "PASS"
        and row.get("scope") == "core_wrapper"
        and positive_float(row.get("total_power_mw", ""))
        and row.get("report_path")
        and (ROOT / row.get("report_path", "")).exists()
    ]
    if not rows:
        return None

    def priority(row: dict[str, str]) -> tuple[int, str]:
        design = row.get("design", "")
        if design == "core_wrapper_plus_copper":
            return (0, design)
        if design == "baseline_core_wrapper":
            return (1, design)
        return (2, design)

    rows.sort(key=priority)
    first = rows[0]
    designs = "; ".join(
        f"{row.get('design', '')} total_power_mw={row.get('total_power_mw', '')}"
        for row in rows[:4]
    )
    return {
        "source": rel(OPENROAD_POSTROUTE_POWER),
        "report_path": first.get("report_path", ""),
        "tool": first.get("flow", ""),
        "environment": first.get("environment", "current"),
        "notes": (
            f"OpenROAD post-route tool-estimate rows found: {designs}. "
            "This is an OpenROAD-flow-scripts Nangate45 post-route estimate, "
            "not silicon measurement, not foundry signoff, and not full-core power."
        ),
    }


def mcpat_activity_evidence() -> dict[str, str] | None:
    rows = read_csv(MCPAT_CSV)
    ok_rows = [
        row
        for row in rows
        if row.get("status") == "ok"
        and positive_float(row.get("mcpat_system_runtime_dynamic_power", ""))
        and positive_float(row.get("mcpat_system_total_runtime_energy", ""))
    ]
    if not ok_rows:
        return None

    report_path = MCPAT_MD if MCPAT_MD.exists() else MCPAT_CSV
    return {
        "source": rel(MCPAT_CSV),
        "report_path": rel(report_path),
        "tool": "McPAT 0.8 via research/analyze_copper_mcpat_sensitivity.py",
        "environment": "current",
        "notes": (
            f"Activity-based McPAT proxy found: {len(ok_rows)}/{len(rows)} rows use measured gem5 ROI "
            "activity counters in a fixed AArch64-style core/cache model. This is not silicon power, "
            "not RTL signoff power, and does not separately model COPPER metadata-table switching."
        ),
    }


def write_power_index(proxy_status: str) -> None:
    openroad_postroute = openroad_postroute_power_evidence()
    asic_power = asic_liberty_power_evidence()
    fpga_power = fpga_tool_power_evidence()
    mcpat = mcpat_activity_evidence()
    write_csv(
        POWER_INDEX,
        ["evidence_level", "status", "source", "report_path", "tool", "environment", "notes"],
        [
            {
                "evidence_level": "openroad_postroute_tool_estimate",
                "status": "PASS" if openroad_postroute else "BLOCKED",
                "source": openroad_postroute["source"] if openroad_postroute else rel(OPENROAD_POSTROUTE_POWER),
                "report_path": openroad_postroute["report_path"] if openroad_postroute else "",
                "tool": openroad_postroute["tool"] if openroad_postroute else "",
                "environment": openroad_postroute["environment"] if openroad_postroute else "current",
                "notes": openroad_postroute["notes"]
                if openroad_postroute
                else (
                    "No OpenROAD post-route core-wrapper power/timing PASS row was found. "
                    "Do not claim post-route ASIC, signoff, silicon, or full-core power."
                ),
            },
            {
                "evidence_level": "asic_liberty_tool_estimate",
                "status": "PASS" if asic_power else "BLOCKED",
                "source": asic_power["source"] if asic_power else rel(ASIC_POWER),
                "report_path": asic_power["report_path"] if asic_power else "",
                "tool": asic_power["tool"] if asic_power else "",
                "environment": asic_power["environment"] if asic_power else "current",
                "notes": asic_power["notes"]
                if asic_power
                else (
                    "No OpenSTA/OpenROAD ASIC Liberty tool-power PASS row was found. "
                    "Do not claim ASIC, signoff, silicon, or full-core power."
                ),
            },
            {
                "evidence_level": "fpga_tool_estimate",
                "status": "PASS" if fpga_power else "BLOCKED",
                "source": fpga_power["source"] if fpga_power else "none",
                "report_path": fpga_power["report_path"] if fpga_power else "",
                "tool": fpga_power["tool"] if fpga_power else "",
                "environment": fpga_power["environment"] if fpga_power else "current",
                "notes": fpga_power["notes"]
                if fpga_power
                else (
                    "No Vivado report_power, OpenROAD power, ASIC, CACTI, or process-calibrated "
                    "RTL power report with a PASS power_mw row was found in this open evidence pass. "
                    "McPAT activity-proxy evidence is indexed separately under proxy_activity."
                ),
            },
            {
                "evidence_level": "proxy_activity",
                "status": "PASS" if mcpat else "BLOCKED",
                "source": mcpat["source"] if mcpat else "none",
                "report_path": mcpat["report_path"] if mcpat else "",
                "tool": mcpat["tool"] if mcpat else "",
                "environment": mcpat["environment"] if mcpat else "current",
                "notes": (
                    mcpat["notes"]
                    if mcpat
                    else (
                        "No activity-calibrated proxy power flow is available in this pass. "
                        "SAIF/activity traces are not converted into power without a calibrated tool report."
                    )
                ),
            },
            {
                "evidence_level": "proxy_assumed_memory_energy",
                "status": proxy_status,
                "source": f"{rel(TRAFFIC)}; {rel(PERF)}",
                "report_path": rel(OUT),
                "tool": "research/scripts/run_energy_estimate.py",
                "environment": "current",
                "notes": ASSUMPTIONS,
            },
        ],
    )


def fnum(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "energy_proxy.log"
    traffic_rows = read_csv(TRAFFIC)
    perf_rows = read_csv(PERF)
    perf_by_key = {
        (r["benchmark"], r["input"], r["seed"], r["config"]): r
        for r in perf_rows
        if r.get("evidence_level") == "core_integrated"
    }
    if not traffic_rows:
        note = f"missing input CSV: {rel(TRAFFIC)}"
        write_csv(
            OUT,
            [
                "benchmark",
                "input",
                "seed",
                "config",
                "evidence_level",
                "energy_model",
                "demand_accesses",
                "prefetch_accesses",
                "total_accesses",
                "estimated_memory_energy_pj",
                "estimated_logic_energy_pj",
                "total_estimated_energy_pj",
                "energy_overhead_pct",
                "assumptions",
                "source",
                "notes",
            ],
            [
                {
                    "benchmark": "ALL",
                    "input": "NA",
                    "seed": "NA",
                    "config": "NA",
                    "evidence_level": "proxy_assumed_memory_energy",
                    "energy_model": "memory_traffic_proxy_v1",
                    "demand_accesses": "NA",
                    "prefetch_accesses": "NA",
                    "total_accesses": "NA",
                    "estimated_memory_energy_pj": "NA",
                    "estimated_logic_energy_pj": "NA",
                    "total_estimated_energy_pj": "NA",
                    "energy_overhead_pct": "NA",
                    "assumptions": ASSUMPTIONS,
                    "source": SOURCE,
                    "notes": note,
                }
            ],
        )
        write_power_index("BLOCKED")
        log_path.write_text(note + "\n", encoding="utf-8")
        return 0

    totals_by_group: dict[tuple[str, str, str], dict[str, float]] = defaultdict(dict)
    intermediate: list[dict[str, object]] = []
    for row in traffic_rows:
        if row.get("evidence_level") != "core_integrated":
            continue
        key = (row["benchmark"], row["input"], row["seed"], row["config"])
        perf = perf_by_key.get(key, {})
        demand = fnum(row.get("demand_loads", "0"))
        prefetch = fnum(row.get("prefetch_loads", "0"))
        cycles = fnum(perf.get("cycles", "0"))
        memory_energy = demand * DEMAND_ACCESS_PJ + prefetch * PREFETCH_ACCESS_PJ
        logic_energy = cycles * LOGIC_CYCLE_PJ
        total = memory_energy + logic_energy
        group_key = (row["benchmark"], row["input"], row["seed"])
        totals_by_group[group_key][row["config"]] = total
        intermediate.append(
            {
                "benchmark": row["benchmark"],
                "input": row["input"],
                "seed": row["seed"],
                "config": row["config"],
                "evidence_level": "proxy_assumed_memory_energy",
                "energy_model": "memory_traffic_proxy_v1",
                "demand_accesses": f"{demand:.0f}",
                "prefetch_accesses": f"{prefetch:.0f}",
                "total_accesses": f"{demand + prefetch:.0f}",
                "estimated_memory_energy_pj": f"{memory_energy:.3f}",
                "estimated_logic_energy_pj": f"{logic_energy:.3f}",
                "total_estimated_energy_pj": f"{total:.3f}",
                "energy_overhead_pct": "",
                "assumptions": ASSUMPTIONS,
                "source": SOURCE,
                "notes": f"Proxy derived from {rel(TRAFFIC)} and {rel(PERF)}; not measured power.",
            }
        )

    rows: list[dict[str, object]] = []
    for row in intermediate:
        group_key = (str(row["benchmark"]), str(row["input"]), str(row["seed"]))
        baseline = totals_by_group[group_key].get("no_prefetch", 0.0)
        total = fnum(str(row["total_estimated_energy_pj"]))
        overhead = ((total / baseline) - 1.0) * 100.0 if baseline else 0.0
        row["energy_overhead_pct"] = f"{overhead:.6f}"
        rows.append(row)

    fields = [
        "benchmark",
        "input",
        "seed",
        "config",
        "evidence_level",
        "energy_model",
        "demand_accesses",
        "prefetch_accesses",
        "total_accesses",
        "estimated_memory_energy_pj",
        "estimated_logic_energy_pj",
        "total_estimated_energy_pj",
        "energy_overhead_pct",
        "assumptions",
        "source",
        "notes",
    ]
    write_csv(OUT, fields, rows)

    copper_overheads = [fnum(str(r["energy_overhead_pct"])) for r in rows if r.get("config") == "copper"]
    write_csv(
        SUMMARY,
        ["evidence_level", "energy_model", "rows", "copper_mean_energy_overhead_pct", "copper_median_energy_overhead_pct", "status", "notes"],
        [
            {
                "evidence_level": "proxy_assumed_memory_energy",
                "energy_model": "memory_traffic_proxy_v1",
                "rows": len(rows),
                "copper_mean_energy_overhead_pct": f"{mean(copper_overheads):.6f}" if copper_overheads else "NA",
                "copper_median_energy_overhead_pct": f"{median(copper_overheads):.6f}" if copper_overheads else "NA",
                "status": "PASS" if rows else "BLOCKED",
                "notes": ASSUMPTIONS,
            }
        ],
    )
    write_power_index("PASS" if rows else "BLOCKED")
    log_path.write_text(
        "Generated proxy_assumed_memory_energy rows from core_integrated traffic/performance CSVs.\n"
        + ASSUMPTIONS
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {rel(OUT)} and {rel(SUMMARY)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
