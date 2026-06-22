#!/usr/bin/env python3
"""Summarize official GAPBS AArch64 full-system gem5 runs."""

from __future__ import annotations

import csv
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "gem5_arm_ubuntu_fs_gapbs_official"


RUNS = [
    ("none", RESULTS / "gem5_arm_ubuntu_fs_gapbs_official_bfs_g10_none"),
    ("naive", RESULTS / "gem5_arm_ubuntu_fs_gapbs_official_bfs_g10_naive"),
    ("copper", RESULTS / "gem5_arm_ubuntu_fs_gapbs_official_bfs_g10_copper"),
]


SUM_PREFIXES = {
    "insts": "board.processor.switch",
    "l1d_demand_misses": "board.cache_hierarchy.l1d-cache-",
    "l1d_demand_accesses": "board.cache_hierarchy.l1d-cache-",
    "l1d_overall_misses": "board.cache_hierarchy.l1d-cache-",
    "l2_demand_misses": "board.cache_hierarchy.l2-cache-",
}


PREFETCH_COUNTERS = [
    "pfIssued",
    "pfUseful",
    "pfUnused",
    "pfIdentified",
    "pointerLikeCandidates",
    "learnedProofs",
    "allowedCandidates",
    "blockedNoProvenance",
    "fillPrefetchTranslated",
    "fillPrefetchTranslationFault",
    "fillPrefetchTranslationUnavailable",
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
        name, raw = parts[0], parts[1]
        try:
            value = float(raw)
        except ValueError:
            value = math.nan
        stats[name] = value
    return stats


def sum_matching(stats: dict[str, float], suffix: str, contains: str | None = None) -> int:
    return int(
        sum(
            v
            for k, v in stats.items()
            if k.endswith(suffix)
            and (contains is None or contains in k)
            and not math.isnan(v)
        )
    )


def terminal_info(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    info: dict[str, str] = {}
    graph = re.search(r"Graph has ([0-9,]+) nodes and ([0-9,]+) undirected edges", text)
    if graph:
        info["nodes"] = graph.group(1).replace(",", "")
        info["edges"] = graph.group(2).replace(",", "")
    trial = re.search(r"Trial Time:\s+([0-9.]+)", text)
    if trial:
        info["trial_time_printed"] = trial.group(1)
    done = re.search(r"COPPER_FS_NATIVE_A64_DONE rc=([0-9]+)", text)
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
            "insts_not_nop": str(sum_matching(stats, ".core.commitStats0.numInstsNotNOP", "board.processor.switch")),
            "l1d_demand_misses": str(sum_matching(stats, ".demandMisses::total", "board.cache_hierarchy.l1d-cache-")),
            "l1d_demand_accesses": str(sum_matching(stats, ".demandAccesses::total", "board.cache_hierarchy.l1d-cache-")),
            "l1d_overall_misses": str(sum_matching(stats, ".overallMisses::total", "board.cache_hierarchy.l1d-cache-")),
            "l2_demand_misses": str(sum_matching(stats, ".demandMisses::total", "board.cache_hierarchy.l2-cache-")),
            "nodes": info.get("nodes", ""),
            "edges": info.get("edges", ""),
            "trial_time_printed": info.get("trial_time_printed", ""),
            "rc": info.get("rc", ""),
        }
        for counter in PREFETCH_COUNTERS:
            row[counter] = str(sum_matching(stats, f".prefetcher.{counter}", ".prefetcher."))
        rows.append(row)

    base_ticks = int(rows[0]["roi_ticks"])
    for row in rows:
        ticks = int(row["roi_ticks"])
        row["tick_delta_vs_none_pct"] = f"{((ticks / base_ticks) - 1.0) * 100.0:.3f}"
    return rows


def write_outputs(rows: list[dict[str, str]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / "gapbs_official_bfs_g10_fs_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Official GAPBS AArch64 Full-System BFS g10 Summary",
        "",
        "This is the first local official GAPBS C++ AArch64 full-system run set.",
        "The public GAPBS BFS source was cross-built with clang++/lld against an",
        "extracted ARM64 Ubuntu 24.04 sysroot from the gem5 disk image, copied into",
        "the guest through the existing readfile path, and executed under Linux 6.8.12",
        "with the L1D prefetcher attached.",
        "",
        "Workload: `bfs -g 10 -k 8 -n 1 -r 1`",
        "",
        "| Policy | ROI ticks | Delta vs none | Insts | L1D demand misses | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked no provenance | Translated PF | Translation faults | CTLW hits | CTLW misses | Terminal stops | rc |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {policy} | {roi_ticks} | {tick_delta_vs_none_pct}% | {insts_not_nop} | "
            "{l1d_demand_misses} | {pfIssued} | {pfUseful} | {pointerLikeCandidates} | "
            "{learnedProofs} | {allowedCandidates} | {blockedNoProvenance} | "
            "{fillPrefetchTranslated} | {fillPrefetchTranslationFault} | "
            "{targetLineWitnessHits} | {targetLineWitnessMisses} | "
            "{carriedProvenanceTerminalStops} | {rc} |".format(**row)
        )
    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            "- The old official-GAPBS blocker is partially removed: local tooling can now build and run official GAPBS C++ BFS as an AArch64 Linux binary under gem5 full-system.",
            "- This is still a small g10 single-kernel point, not a full GAPBS suite or large-scale campaign.",
            "- COPPER sees real pointer-like C++ process data, learns committed proofs, allows only proven candidates, blocks unproven pointer-shaped candidates, and records zero COPPER fill-origin translation faults in this run.",
            "- Official GAPBS uses integer vertex IDs for graph edges, so this run is mainly external-validity/safety/control evidence rather than a DMP speedup showcase.",
            "",
        ]
    )
    md_path = OUT / "GAPBS_OFFICIAL_BFS_G10_FS_SUMMARY.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(md_path)
    print(csv_path)


def main() -> None:
    rows = summarize()
    write_outputs(rows)


if __name__ == "__main__":
    main()
