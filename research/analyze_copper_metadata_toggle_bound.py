#!/usr/bin/env python3
"""Sensitivity bound for COPPER metadata access energy.

This is not ASIC signoff. It turns measured COPPER CLPD event counts into a
small pJ/access sensitivity table and compares the result with gem5 DRAM-energy
scale for the same public app/service rows.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
TRAFFIC_CSV = RESULTS / "copper_prefetch_traffic_overhead_20260616.csv"
DRAM_CSV = RESULTS / "copper_dram_energy_scorecard_20260618.csv"
OUT_MD = RESULTS / "COPPER_METADATA_TOGGLE_BOUND_20260619.md"
OUT_CSV = RESULTS / "copper_metadata_toggle_bound_20260619.csv"


@dataclass(frozen=True)
class Scenario:
    name: str
    read_pj: float
    write_pj: float
    compare_pj: float


SCENARIOS = [
    Scenario("low", read_pj=1.0, write_pj=2.0, compare_pj=0.2),
    Scenario("mid", read_pj=5.0, write_pj=10.0, compare_pj=1.0),
    Scenario("high", read_pj=20.0, write_pj=40.0, compare_pj=5.0),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def fnum(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    return 0.0 if value == "" else float(value)


def main() -> None:
    traffic_rows = [
        row
        for row in read_csv(TRAFFIC_CSV)
        if row["policy"] == "copper_clpd64k_peb"
    ]
    workloads = {row["workload"] for row in traffic_rows}
    dram_rows = [
        row
        for row in read_csv(DRAM_CSV)
        if row["policy"] == "copper_clpd64k_peb" and row["workload"] in workloads
    ]

    commits = sum(fnum(row, "learnedProofs") for row in traffic_rows)
    allow = sum(fnum(row, "allowedCandidates") for row in traffic_rows)
    block = sum(fnum(row, "blockedNoProvenance") for row in traffic_rows)
    fault = sum(fnum(row, "targetLineWitnessMisses") for row in traffic_rows)
    reads = allow + block + fault
    writes = commits
    events = reads + writes

    dram_total_pj = sum(fnum(row, "totalEnergy") for row in dram_rows)
    dram_op_pj = sum(fnum(row, "opEnergy") for row in dram_rows)

    rows: list[dict[str, float | str]] = []
    for scenario in SCENARIOS:
        metadata_pj = (
            reads * scenario.read_pj
            + writes * scenario.write_pj
            + events * scenario.compare_pj
        )
        rows.append(
            {
                "scenario": scenario.name,
                "read_pj": scenario.read_pj,
                "write_pj": scenario.write_pj,
                "compare_pj": scenario.compare_pj,
                "metadata_pj": metadata_pj,
                "metadata_uJ": metadata_pj / 1_000_000.0,
                "pct_dram_op": 100.0 * metadata_pj / dram_op_pj,
                "pct_dram_total": 100.0 * metadata_pj / dram_total_pj,
            }
        )

    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "scenario",
                "read_pj",
                "write_pj",
                "compare_pj",
                "metadata_pj",
                "metadata_uJ",
                "pct_dram_op",
                "pct_dram_total",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    worst = max(rows, key=lambda row: float(row["pct_dram_op"]))
    lines = [
        "# COPPER Metadata Toggle Bound",
        "",
        "Date: 2026-06-19",
        "",
        "Purpose: give a rerunnable sensitivity bound for COPPER metadata access energy using measured full-system CLPD event counts. This is not ASIC signoff and does not replace instruction-level SAIF/VCD or a foundry-calibrated SRAM/compiler flow.",
        "",
        "## Inputs",
        "",
        f"- Source traffic CSV: `{TRAFFIC_CSV.relative_to(ROOT)}`",
        f"- Source DRAM-energy CSV: `{DRAM_CSV.relative_to(ROOT)}`",
        f"- Workload rows: {len(traffic_rows)} COPPER CLPD-64K+PEB public app/service/parser rows",
        f"- Learned-proof writes: {int(writes):,}",
        f"- CLPD authority reads: {int(reads):,}",
        f"- Total metadata events: {int(events):,}",
        f"- Summed COPPER DRAM operation energy over matching rows: {dram_op_pj:,.0f} pJ",
        f"- Summed COPPER total DRAM energy over matching rows: {dram_total_pj:,.0f} pJ",
        "",
        "## Sensitivity Table",
        "",
        "| Scenario | Read pJ | Write pJ | Compare pJ/event | Metadata energy | % of DRAM op energy | % of total DRAM energy |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['scenario']} | {row['read_pj']:.1f} | {row['write_pj']:.1f} | "
            f"{row['compare_pj']:.1f} | {row['metadata_uJ']:.3f} uJ | "
            f"{row['pct_dram_op']:.4f}% | {row['pct_dram_total']:.6f}% |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Even the deliberately high scenario is {float(worst['pct_dram_op']):.4f}% of matching COPPER DRAM operation energy.",
            "- This supports the narrow claim that metadata-table access energy is unlikely to dominate the measured memory-system energy story under these assumptions.",
            "- This does not prove full-chip power, SRAM compiler energy, physical wire energy, or integrated clocking overhead.",
            "- The paper should continue to describe this as a sensitivity bound, not calibrated silicon power.",
            "",
            f"CSV: `{OUT_CSV.relative_to(ROOT)}`",
            "",
            "status=PASS",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(OUT_MD)


if __name__ == "__main__":
    main()
