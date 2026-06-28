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
POWER_INDEX_FIELDS = [
    "evidence_level",
    "status",
    "source",
    "report_path",
    "tool",
    "environment",
    "scope",
    "power_kind",
    "baseline_design",
    "copper_design",
    "tool_report_power",
    "fpga_estimate",
    "asic_tool_estimate",
    "postroute_estimate",
    "activity_proxy",
    "assumption_proxy",
    "silicon_measured",
    "signoff_grade",
    "full_core",
    "notes",
]


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


def power_index_row(
    evidence_level: str,
    status: str,
    source: str,
    report_path: str = "",
    tool: str = "",
    environment: str = "current",
    scope: str = "core_wrapper",
    power_kind: str = "",
    baseline_design: str = "",
    copper_design: str = "",
    tool_report_power: bool = False,
    fpga_estimate: bool = False,
    asic_tool_estimate: bool = False,
    postroute_estimate: bool = False,
    activity_proxy: bool = False,
    assumption_proxy: bool = False,
    silicon_measured: bool = False,
    signoff_grade: bool = False,
    full_core: bool = False,
    notes: str = "",
) -> dict[str, str]:
    def yn(value: bool) -> str:
        return "yes" if value else "no"

    return {
        "evidence_level": evidence_level,
        "status": status,
        "source": source,
        "report_path": report_path,
        "tool": tool,
        "environment": environment,
        "scope": scope,
        "power_kind": power_kind,
        "baseline_design": baseline_design,
        "copper_design": copper_design,
        "tool_report_power": yn(tool_report_power),
        "fpga_estimate": yn(fpga_estimate),
        "asic_tool_estimate": yn(asic_tool_estimate),
        "postroute_estimate": yn(postroute_estimate),
        "activity_proxy": yn(activity_proxy),
        "assumption_proxy": yn(assumption_proxy),
        "silicon_measured": yn(silicon_measured),
        "signoff_grade": yn(signoff_grade),
        "full_core": yn(full_core),
        "notes": notes,
    }


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

    pairs = {
        "core_wrapper": ("baseline_core_wrapper", "core_wrapper_plus_copper"),
        "near_core_stub": ("nearcore_stub_baseline", "nearcore_stub_plus_copper"),
        "unit": ("baseline_prefetch_unit", "copper_unit"),
    }
    by_group: dict[tuple[str, str, str], list[tuple[Path, dict[str, str]]]] = {}
    for item in evidence:
        row = item[1]
        by_group.setdefault((row.get("scope", ""), row.get("target", ""), row.get("flow", "")), []).append(item)

    matched: list[tuple[int, tuple[str, str, str], list[tuple[Path, dict[str, str]]]]] = []
    for group, items in by_group.items():
        scope, target, _flow = group
        baseline, copper = pairs.get(scope, ("", ""))
        designs = {row.get("design", "") for _, row in items}
        if baseline and copper and {baseline, copper}.issubset(designs):
            priority_value = 0 if scope == "core_wrapper" and target.startswith("vivado-") else 1
            matched.append((priority_value, group, items))
    if matched:
        matched.sort(key=lambda item: item[0])
        _priority, (scope, _target, _flow), evidence = matched[0]
        baseline_design, copper_design = pairs[scope]
    else:
        baseline_design, copper_design = "", ""

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
        "scope": first_row.get("scope", "mapped_fpga"),
        "baseline_design": baseline_design,
        "copper_design": copper_design,
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
    by_design = {row.get("design", ""): row for row in rows}
    if not {"baseline_core_wrapper", "core_wrapper_plus_copper"}.issubset(by_design):
        return None
    rows = [by_design["core_wrapper_plus_copper"], by_design["baseline_core_wrapper"]]

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
        "scope": first.get("scope", "core_wrapper"),
        "baseline_design": "baseline_core_wrapper",
        "copper_design": "core_wrapper_plus_copper",
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
    by_design = {row.get("design", ""): row for row in rows}
    if not {"baseline_core_wrapper", "core_wrapper_plus_copper"}.issubset(by_design):
        return None
    rows = [by_design["core_wrapper_plus_copper"], by_design["baseline_core_wrapper"]]

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
        "scope": first.get("scope", "core_wrapper"),
        "baseline_design": "baseline_core_wrapper",
        "copper_design": "core_wrapper_plus_copper",
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
        "scope": "model_proxy",
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
        POWER_INDEX_FIELDS,
        [
            power_index_row(
                "openroad_postroute_tool_estimate",
                "PASS" if openroad_postroute else "BLOCKED",
                openroad_postroute["source"] if openroad_postroute else rel(OPENROAD_POSTROUTE_POWER),
                report_path=openroad_postroute["report_path"] if openroad_postroute else "",
                tool=openroad_postroute["tool"] if openroad_postroute else "",
                environment=openroad_postroute["environment"] if openroad_postroute else "current",
                scope=openroad_postroute["scope"] if openroad_postroute else "core_wrapper",
                power_kind="nangate45_openroad_postroute_tool_estimate",
                baseline_design=openroad_postroute["baseline_design"] if openroad_postroute else "baseline_core_wrapper",
                copper_design=openroad_postroute["copper_design"] if openroad_postroute else "core_wrapper_plus_copper",
                tool_report_power=bool(openroad_postroute),
                asic_tool_estimate=bool(openroad_postroute),
                postroute_estimate=bool(openroad_postroute),
                notes=openroad_postroute["notes"]
                if openroad_postroute
                else (
                    "No OpenROAD post-route core-wrapper power/timing PASS row was found. "
                    "Do not claim post-route ASIC, signoff, silicon, or full-core power."
                ),
            ),
            power_index_row(
                "asic_liberty_tool_estimate",
                "PASS" if asic_power else "BLOCKED",
                asic_power["source"] if asic_power else rel(ASIC_POWER),
                report_path=asic_power["report_path"] if asic_power else "",
                tool=asic_power["tool"] if asic_power else "",
                environment=asic_power["environment"] if asic_power else "current",
                scope=asic_power["scope"] if asic_power else "core_wrapper",
                power_kind="nangate45_liberty_tool_estimate",
                baseline_design=asic_power["baseline_design"] if asic_power else "baseline_core_wrapper",
                copper_design=asic_power["copper_design"] if asic_power else "core_wrapper_plus_copper",
                tool_report_power=bool(asic_power),
                asic_tool_estimate=bool(asic_power),
                notes=asic_power["notes"]
                if asic_power
                else (
                    "No OpenSTA/OpenROAD ASIC Liberty tool-power PASS row was found. "
                    "Do not claim ASIC, signoff, silicon, or full-core power."
                ),
            ),
            power_index_row(
                "fpga_tool_estimate",
                "PASS" if fpga_power else "BLOCKED",
                fpga_power["source"] if fpga_power else "none",
                report_path=fpga_power["report_path"] if fpga_power else "",
                tool=fpga_power["tool"] if fpga_power else "",
                environment=fpga_power["environment"] if fpga_power else "current",
                scope=fpga_power["scope"] if fpga_power else "mapped_fpga",
                power_kind="vivado_fpga_report_power",
                baseline_design=fpga_power["baseline_design"] if fpga_power else "",
                copper_design=fpga_power["copper_design"] if fpga_power else "",
                tool_report_power=bool(fpga_power),
                fpga_estimate=bool(fpga_power),
                notes=fpga_power["notes"]
                if fpga_power
                else (
                    "No Vivado report_power, OpenROAD power, ASIC, CACTI, or process-calibrated "
                    "RTL power report with a PASS power_mw row was found in this open evidence pass. "
                    "McPAT activity-proxy evidence is indexed separately under proxy_activity."
                ),
            ),
            power_index_row(
                "proxy_activity",
                "PASS" if mcpat else "BLOCKED",
                mcpat["source"] if mcpat else "none",
                report_path=mcpat["report_path"] if mcpat else "",
                tool=mcpat["tool"] if mcpat else "",
                environment=mcpat["environment"] if mcpat else "current",
                scope=mcpat["scope"] if mcpat else "model_proxy",
                power_kind="mcpat_activity_proxy",
                activity_proxy=bool(mcpat),
                notes=(
                    mcpat["notes"]
                    if mcpat
                    else (
                        "No activity-calibrated proxy power flow is available in this pass. "
                        "SAIF/activity traces are not converted into power without a calibrated tool report."
                    )
                ),
            ),
            power_index_row(
                "proxy_assumed_memory_energy",
                proxy_status,
                f"{rel(TRAFFIC)}; {rel(PERF)}",
                report_path=rel(OUT),
                tool="research/scripts/run_energy_estimate.py",
                environment="current",
                scope="model_proxy",
                power_kind="assumed_memory_energy_proxy",
                assumption_proxy=proxy_status == "PASS",
                notes=ASSUMPTIONS,
            ),
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
