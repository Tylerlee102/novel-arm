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

DEMAND_ACCESS_PJ = 120.0
PREFETCH_ACCESS_PJ = 120.0
LOGIC_CYCLE_PJ = 0.05
ASSUMPTIONS = (
    "proxy_assumed; source=explicit_local_assumption_not_measured;"
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
                "notes",
            ],
            [
                {
                    "benchmark": "ALL",
                    "input": "NA",
                    "seed": "NA",
                    "config": "NA",
                    "evidence_level": "proxy_assumed",
                    "energy_model": "memory_traffic_proxy_v1",
                    "demand_accesses": "NA",
                    "prefetch_accesses": "NA",
                    "total_accesses": "NA",
                    "estimated_memory_energy_pj": "NA",
                    "estimated_logic_energy_pj": "NA",
                    "total_estimated_energy_pj": "NA",
                    "energy_overhead_pct": "NA",
                    "assumptions": ASSUMPTIONS,
                    "notes": note,
                }
            ],
        )
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
                "evidence_level": "proxy_assumed",
                "energy_model": "memory_traffic_proxy_v1",
                "demand_accesses": f"{demand:.0f}",
                "prefetch_accesses": f"{prefetch:.0f}",
                "total_accesses": f"{demand + prefetch:.0f}",
                "estimated_memory_energy_pj": f"{memory_energy:.3f}",
                "estimated_logic_energy_pj": f"{logic_energy:.3f}",
                "total_estimated_energy_pj": f"{total:.3f}",
                "energy_overhead_pct": "",
                "assumptions": ASSUMPTIONS,
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
        "notes",
    ]
    write_csv(OUT, fields, rows)

    copper_overheads = [fnum(str(r["energy_overhead_pct"])) for r in rows if r.get("config") == "copper"]
    write_csv(
        SUMMARY,
        ["evidence_level", "energy_model", "rows", "copper_mean_energy_overhead_pct", "copper_median_energy_overhead_pct", "status", "notes"],
        [
            {
                "evidence_level": "proxy_assumed",
                "energy_model": "memory_traffic_proxy_v1",
                "rows": len(rows),
                "copper_mean_energy_overhead_pct": f"{mean(copper_overheads):.6f}" if copper_overheads else "NA",
                "copper_median_energy_overhead_pct": f"{median(copper_overheads):.6f}" if copper_overheads else "NA",
                "status": "PASS" if rows else "BLOCKED",
                "notes": ASSUMPTIONS,
            }
        ],
    )
    log_path.write_text(
        "Generated proxy_assumed energy rows from core_integrated traffic/performance CSVs.\n"
        + ASSUMPTIONS
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {rel(OUT)} and {rel(SUMMARY)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
