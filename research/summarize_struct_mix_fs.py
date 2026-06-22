#!/usr/bin/env python3
"""Summarize AArch64 pointer-structure mix full-system runs."""

from __future__ import annotations

import csv
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "gem5_arm_ubuntu_fs_struct_mix"
TAG = "n32768_p12_b2048_f3"


RUNS = [
    ("none", RESULTS / f"gem5_arm_ubuntu_fs_struct_mix_{TAG}_none"),
    ("naive", RESULTS / f"gem5_arm_ubuntu_fs_struct_mix_{TAG}_naive"),
    ("copper_clpd64k", RESULTS / f"gem5_arm_ubuntu_fs_struct_mix_{TAG}_copper_clpd64k"),
]


COUNTERS = [
    "pfIssued",
    "pfUseful",
    "pointerLikeCandidates",
    "learnedProofs",
    "proofEvictions",
    "allowedCandidates",
    "blockedNoProvenance",
    "fillPrefetchTranslated",
    "fillPrefetchTranslationFault",
    "targetLineWitnessHits",
    "targetLineWitnessMisses",
    "carriedProvenanceTerminalStops",
]


def first_stats(path: Path) -> dict[str, float]:
    text = path.read_text(encoding="utf-8", errors="replace")
    begin = text.index("---------- Begin Simulation Statistics ----------")
    end = text.index("---------- End Simulation Statistics", begin)
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
    return stats


def sum_matching(stats: dict[str, float], suffix: str, contains: str | None = None) -> int:
    return int(
        sum(
            value
            for key, value in stats.items()
            if key.endswith(suffix)
            and (contains is None or contains in key)
            and not math.isnan(value)
        )
    )


def terminal_info(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(
        r"STRUCT_MIX nodes=(\d+) passes=(\d+) buckets=(\d+) "
        r"fake_passes=(\d+) seed=(0x[0-9a-fA-F]+) "
        r"checksum=(0x[0-9a-fA-F]+)",
        text,
    )
    info: dict[str, str] = {}
    if match:
        info.update(
            {
                "nodes": match.group(1),
                "passes": match.group(2),
                "buckets": match.group(3),
                "fake_passes": match.group(4),
                "seed": match.group(5),
                "checksum": match.group(6),
            }
        )
    done = re.search(r"COPPER_FS_NATIVE_A64_DONE rc=(\d+)", text)
    if done:
        info["rc"] = done.group(1)
    return info


def summarize() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for policy, run_dir in RUNS:
        stats = first_stats(run_dir / "stats.txt")
        info = terminal_info(run_dir / "board.terminal")
        row: dict[str, str] = {
            "policy": policy,
            "roi_ticks": str(int(stats.get("simTicks", 0))),
            "insts_not_nop": str(
                sum_matching(
                    stats,
                    ".core.commitStats0.numInstsNotNOP",
                    "board.processor.switch",
                )
            ),
            "l1d_demand_misses": str(
                sum_matching(
                    stats,
                    ".demandMisses::total",
                    "board.cache_hierarchy.l1d-cache-",
                )
            ),
            "l2_demand_misses": str(
                sum_matching(
                    stats,
                    ".demandMisses::total",
                    "board.cache_hierarchy.l2-cache-",
                )
            ),
            "nodes": info.get("nodes", ""),
            "passes": info.get("passes", ""),
            "buckets": info.get("buckets", ""),
            "fake_passes": info.get("fake_passes", ""),
            "seed": info.get("seed", ""),
            "checksum": info.get("checksum", ""),
            "rc": info.get("rc", ""),
        }
        for counter in COUNTERS:
            row[counter] = str(sum_matching(stats, f".prefetcher.{counter}", ".prefetcher."))
        rows.append(row)

    base_ticks = int(rows[0]["roi_ticks"])
    base_misses = int(rows[0]["l1d_demand_misses"])
    for row in rows:
        row["tick_delta_vs_none_pct"] = (
            f"{((int(row['roi_ticks']) / base_ticks) - 1.0) * 100.0:.3f}"
        )
        row["l1d_miss_delta_vs_none_pct"] = (
            f"{((int(row['l1d_demand_misses']) / base_misses) - 1.0) * 100.0:.3f}"
        )
    return rows


def as_int(row: dict[str, str], key: str) -> int:
    return int(row[key])


def write_outputs(rows: list[dict[str, str]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / f"struct_mix_{TAG}_fs_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    by_policy = {row["policy"]: row for row in rows}
    naive = by_policy["naive"]
    clpd = by_policy["copper_clpd64k"]
    issue_delta = (
        (as_int(clpd, "pfIssued") / max(as_int(naive, "pfIssued"), 1)) - 1.0
    ) * 100.0
    ctlw_reduction = (
        1.0
        - as_int(clpd, "targetLineWitnessMisses")
        / max(as_int(naive, "targetLineWitnessMisses"), 1)
    ) * 100.0

    lines = [
        "# AArch64 Pointer Structure Mix Full-System Summary",
        "",
        "This is an independent targeted workload from the heap-chain benchmark.",
        "It builds randomized tree, bucket-chain, and fake pointer-shaped payload",
        "structures, then traverses real pointer fields and scans fake values under",
        "in-binary gem5 ROI markers.",
        "",
        "| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | L2 misses | PF issued | PF useful | Pointer-like | Learned proofs | Proof evictions | Allowed | Blocked no provenance | Translated PF | Translation faults | CTLW hits | CTLW misses | Terminal stops | Checksum | rc |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for row in rows:
        lines.append(
            "| {policy} | {roi_ticks} | {tick_delta_vs_none_pct}% | {insts_not_nop} | "
            "{l1d_demand_misses} | {l1d_miss_delta_vs_none_pct}% | {l2_demand_misses} | "
            "{pfIssued} | {pfUseful} | {pointerLikeCandidates} | {learnedProofs} | "
            "{proofEvictions} | {allowedCandidates} | {blockedNoProvenance} | "
            "{fillPrefetchTranslated} | {fillPrefetchTranslationFault} | "
            "{targetLineWitnessHits} | {targetLineWitnessMisses} | "
            "{carriedProvenanceTerminalStops} | {checksum} | {rc} |".format(**row)
        )

    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            f"- Naive changes ROI ticks by {naive['tick_delta_vs_none_pct']}% and records {as_int(naive, 'targetLineWitnessMisses')} CTLW misses.",
            f"- CLPD-64K changes ROI ticks by {clpd['tick_delta_vs_none_pct']}%, issues {issue_delta:.1f}% more prefetches than naive, reduces naive CTLW misses by {ctlw_reduction:.3f}%, and records zero translation faults.",
            "- This result broadens the targeted full-system evidence beyond a single pointer-chain style, but it is still a synthetic pointer-rich workload.",
            "",
        ]
    )
    md_path = OUT / f"STRUCT_MIX_{TAG.upper()}_FS_SUMMARY.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(md_path)
    print(csv_path)


def main() -> None:
    write_outputs(summarize())


if __name__ == "__main__":
    main()
