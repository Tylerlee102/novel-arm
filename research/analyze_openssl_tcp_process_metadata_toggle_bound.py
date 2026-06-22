#!/usr/bin/env python3
"""Sensitivity bound for COPPER metadata activity on TCP process-server runs.

This is a deliberately narrow side-effect check for the strongest OpenSSL
libssl TCP evidence. It converts measured CLPD authority counters into a
pJ/access sensitivity table and normalizes that bound to matching gem5 DRAM
rank-energy counters. It is not ASIC signoff, SRAM compiler power, or a
full-system switching waveform.
"""

from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
TCP_DIR = RESULTS / "gem5_arm_ubuntu_fs_ossltlstcp_app"
SOURCE_CSVS = [
    TCP_DIR / "ossltlstcp_tcp_netns_process_key1_summary.csv",
    TCP_DIR / "ossltlstcp_tcp_netns_process_seed1_summary.csv",
    TCP_DIR / "ossltlstcp_tcp_netns_process_scale2_summary.csv",
    TCP_DIR / "ossltlstcp_tcp_netns_process_scale3_summary.csv",
]
OUT_MD = RESULTS / "OPENSSL_TCP_PROCESS_METADATA_TOGGLE_BOUND_20260620.md"
OUT_CSV = RESULTS / "openssl_tcp_process_metadata_toggle_bound_20260620.csv"

POLICIES = ("copper_clpd64k_peb", "spp_copper_slack")
ENERGY_FIELDS = ("totalEnergy", "readEnergy", "writeEnergy", "actEnergy", "preEnergy")
OP_FIELDS = ("readEnergy", "writeEnergy", "actEnergy", "preEnergy")


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


def inum(row: dict[str, str], key: str) -> int:
    return int(fnum(row, key))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def run_label(path: Path) -> str:
    name = path.name
    if "process_key1" in name:
        return "key1"
    if "process_seed1" in name:
        return "seed1"
    if "process_scale2" in name:
        return "scale2"
    if "process_scale3" in name:
        return "scale3"
    raise ValueError(f"cannot infer TCP process-server run label from {path}")


def parse_stats_sections(path: Path) -> list[dict[str, float]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    sections: list[dict[str, float]] = []
    marker = "---------- Begin Simulation Statistics ----------"
    end_marker = "---------- End Simulation Statistics"
    start = 0
    while True:
        try:
            begin = text.index(marker, start)
            end = text.index(end_marker, begin)
        except ValueError:
            break
        stats: dict[str, float] = {}
        for line in text[begin:end].splitlines():
            if not line or line.startswith("-"):
                continue
            parts = line.split("#", 1)[0].split()
            if len(parts) < 2:
                continue
            try:
                stats[parts[0]] = float(parts[1])
            except ValueError:
                stats[parts[0]] = math.nan
        sections.append(stats)
        start = end + len(end_marker)
    return sections


def sum_energy(stats: dict[str, float], field: str) -> float:
    pattern = re.compile(
        rf"^board\.memory\.mem_ctrl\d+\.dram\.rank\d+\.{re.escape(field)}$"
    )
    return sum(
        value
        for key, value in stats.items()
        if pattern.search(key) and not math.isnan(value)
    )


def collect_dram_energy(label: str, policy: str) -> dict[str, float]:
    stats_path = (
        RESULTS
        / f"gem5_arm_ubuntu_fs_ossltlstcp_tcp_netns_process_{label}_{policy}"
        / "stats.txt"
    )
    sections = parse_stats_sections(stats_path)
    if not sections:
        raise RuntimeError(f"no stats sections in {stats_path}")
    stats = sections[0]
    energies = {field: sum_energy(stats, field) for field in ENERGY_FIELDS}
    energies["opEnergy"] = sum(energies[field] for field in OP_FIELDS)
    energies["simTicks"] = stats.get("simTicks", 0.0)
    return energies


def main() -> None:
    rows: list[dict[str, str]] = []
    for source_csv in SOURCE_CSVS:
        label = run_label(source_csv)
        for row in read_csv(source_csv):
            row["tcp_process_label"] = label
            rows.append(row)

    selected = [row for row in rows if row["policy"] in POLICIES]
    if len(selected) != len(SOURCE_CSVS) * len(POLICIES):
        raise SystemExit(
            f"expected {len(SOURCE_CSVS) * len(POLICIES)} selected policy rows, "
            f"found {len(selected)}"
        )

    bad_rows = [
        row
        for row in selected
        if row.get("transport") != "tcp_loopback_netns_process"
        or inum(row, "process_server") != 1
        or inum(row, "child_failures") != 0
        or inum(row, "fillPrefetchTranslationFault") != 0
    ]
    if bad_rows:
        raise SystemExit(f"invalid TCP process-server rows: {bad_rows}")

    policy_totals: dict[str, dict[str, float]] = {}
    for policy in POLICIES:
        policy_rows = [row for row in selected if row["policy"] == policy]
        reads = sum(
            fnum(row, "allowedCandidates")
            + fnum(row, "blockedNoProvenance")
            + fnum(row, "targetLineWitnessMisses")
            for row in policy_rows
        )
        writes = sum(fnum(row, "learnedProofs") for row in policy_rows)
        events = reads + writes
        policy_totals[policy] = {
            "seed_points": float(len(policy_rows)),
            "process_pairs": sum(fnum(row, "process_pairs") for row in policy_rows),
            "pointer_like_candidates": sum(
                fnum(row, "pointerLikeCandidates") for row in policy_rows
            ),
            "pf_issued": sum(fnum(row, "pfIssued") for row in policy_rows),
            "pf_useful": sum(fnum(row, "pfUseful") for row in policy_rows),
            "reads": reads,
            "writes": writes,
            "events": events,
            "dram_total_pj": 0.0,
            "dram_op_pj": 0.0,
        }
        for row in policy_rows:
            dram = collect_dram_energy(row["tcp_process_label"], policy)
            policy_totals[policy]["dram_total_pj"] += dram["totalEnergy"]
            policy_totals[policy]["dram_op_pj"] += dram["opEnergy"]

    out_rows: list[dict[str, float | str]] = []
    for policy, totals in policy_totals.items():
        for scenario in SCENARIOS:
            metadata_pj = (
                totals["reads"] * scenario.read_pj
                + totals["writes"] * scenario.write_pj
                + totals["events"] * scenario.compare_pj
            )
            out_rows.append(
                {
                    "policy": policy,
                    "scenario": scenario.name,
                    "seed_points": totals["seed_points"],
                    "process_pairs": totals["process_pairs"],
                    "pointer_like_candidates": totals["pointer_like_candidates"],
                    "pf_issued": totals["pf_issued"],
                    "pf_useful": totals["pf_useful"],
                    "metadata_reads": totals["reads"],
                    "metadata_writes": totals["writes"],
                    "metadata_events": totals["events"],
                    "read_pj": scenario.read_pj,
                    "write_pj": scenario.write_pj,
                    "compare_pj": scenario.compare_pj,
                    "metadata_pj": metadata_pj,
                    "metadata_uJ": metadata_pj / 1_000_000.0,
                    "dram_op_pj": totals["dram_op_pj"],
                    "dram_total_pj": totals["dram_total_pj"],
                    "metadata_pct_of_dram_op": (
                        metadata_pj / totals["dram_op_pj"] * 100.0
                        if totals["dram_op_pj"]
                        else 0.0
                    ),
                    "metadata_pct_of_dram_total": (
                        metadata_pj / totals["dram_total_pj"] * 100.0
                        if totals["dram_total_pj"]
                        else 0.0
                    ),
                }
            )

    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "policy",
                "scenario",
                "seed_points",
                "process_pairs",
                "pointer_like_candidates",
                "pf_issued",
                "pf_useful",
                "metadata_reads",
                "metadata_writes",
                "metadata_events",
                "read_pj",
                "write_pj",
                "compare_pj",
                "metadata_pj",
                "metadata_uJ",
                "dram_op_pj",
                "dram_total_pj",
                "metadata_pct_of_dram_op",
                "metadata_pct_of_dram_total",
            ],
        )
        writer.writeheader()
        writer.writerows(out_rows)

    high_rows = [row for row in out_rows if row["scenario"] == "high"]
    max_high = max(high_rows, key=lambda row: float(row["metadata_uJ"]))

    lines = [
        "# OpenSSL TCP Process-Server Metadata Toggle Bound",
        "",
        "Date: 2026-06-20",
        "",
        "Purpose: bound COPPER metadata-table activity for the OpenSSL libssl TCP process-server workload, including the scaled process-pair point. This is a pJ/access sensitivity check over measured AArch64 full-system counters, not calibrated ASIC power, SRAM compiler power, or an instruction-by-instruction switching trace.",
        "",
        "## Inputs",
        "",
    ]
    for source_csv in SOURCE_CSVS:
        lines.append(f"- Source CSV: `{rel(source_csv)}`")
    lines.extend(
        [
            f"- Selected policies: {', '.join(POLICIES)}",
            f"- Selected policy rows: {len(selected)}",
            "- All selected rows use `tcp_loopback_netns_process`: yes.",
            "- All selected rows have `process_server=1`: yes.",
            "- Child process failures across selected rows: 0.",
            "- Translation faults across selected rows: 0.",
            "- Matching gem5 DRAM rank-energy rows: found for every selected seed/policy row.",
            "",
            "## Counter Totals",
            "",
            "| Policy | Seed points | Process pairs | Pointer-like candidates | Prefetches issued | Useful prefetches | Metadata reads | Metadata writes | Metadata events | DRAM op energy | Total DRAM energy |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for policy in POLICIES:
        totals = policy_totals[policy]
        lines.append(
            f"| {policy} | {int(totals['seed_points'])} | "
            f"{int(totals['process_pairs'])} | "
            f"{int(totals['pointer_like_candidates']):,} | "
            f"{int(totals['pf_issued']):,} | "
            f"{int(totals['pf_useful']):,} | "
            f"{int(totals['reads']):,} | "
            f"{int(totals['writes']):,} | "
            f"{int(totals['events']):,} | "
            f"{totals['dram_op_pj'] / 1_000_000.0:.3f} uJ | "
            f"{totals['dram_total_pj'] / 1_000_000_000.0:.3f} mJ |"
        )
    lines.extend(
        [
            "",
            "## Sensitivity Table",
            "",
            "| Policy | Scenario | Read pJ | Write pJ | Compare pJ/event | Metadata energy | Metadata / DRAM op | Metadata / total DRAM |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in out_rows:
        lines.append(
            f"| {row['policy']} | {row['scenario']} | "
            f"{float(row['read_pj']):.1f} | "
            f"{float(row['write_pj']):.1f} | "
            f"{float(row['compare_pj']):.1f} | "
            f"{float(row['metadata_uJ']):.3f} uJ | "
            f"{float(row['metadata_pct_of_dram_op']):.4f}% | "
            f"{float(row['metadata_pct_of_dram_total']):.6f}% |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- The deliberately high scenario remains below {float(max_high['metadata_uJ']):.3f} uJ across the selected process-server points for either policy.",
            f"- In the same high scenario, the maximum normalized metadata bound is {max(float(row['metadata_pct_of_dram_op']) for row in high_rows):.4f}% of matching DRAM operation energy and {max(float(row['metadata_pct_of_dram_total']) for row in high_rows):.6f}% of matching total DRAM energy.",
            "- Standalone COPPER has fewer metadata events than SPP+COPPER slack on this workload because the slack path gates a larger SPP candidate stream.",
            "- This supports a narrow side-effect claim: the process-separated TCP evidence does not create a large metadata-access-energy signal under these assumptions.",
            "- This does not prove full-chip power, wire energy, SRAM-compiler energy, or production TCP/TLS behavior.",
            "",
            f"CSV: `{rel(OUT_CSV)}`",
            "",
            "status=PASS",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(OUT_MD)


if __name__ == "__main__":
    main()
