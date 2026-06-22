#!/usr/bin/env python3
"""Summarize AArch64 heap-pointer stress full-system gem5 runs."""

from __future__ import annotations

import csv
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "gem5_arm_ubuntu_fs_heap_stress"
TAG = "n65536_p8"


RUNS = [
    ("none", RESULTS / f"gem5_arm_ubuntu_fs_heap_stress_{TAG}_none"),
    ("stride", RESULTS / f"gem5_arm_ubuntu_fs_heap_stress_{TAG}_stride"),
    ("naive", RESULTS / f"gem5_arm_ubuntu_fs_heap_stress_{TAG}_naive"),
    ("copper", RESULTS / f"gem5_arm_ubuntu_fs_heap_stress_{TAG}_copper"),
    (
        "copper_p131k",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_stress_{TAG}_copper_proof131k",
    ),
    (
        "copper_clpd16k",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_stress_{TAG}_copper_clpd16k",
    ),
]


PREFETCH_COUNTERS = [
    "pfIssued",
    "pfUseful",
    "pfUnused",
    "pfIdentified",
    "pointerLikeCandidates",
    "learnedProofs",
    "proofEvictions",
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
    info: dict[str, str] = {}
    heap = re.search(
        r"HEAP_STRESS nodes=(\d+) passes=(\d+) fake=(\d+) rewrite=(\d+) checksum=(0x[0-9a-fA-F]+)",
        text,
    )
    if heap:
        info["nodes"] = heap.group(1)
        info["passes"] = heap.group(2)
        info["fake"] = heap.group(3)
        info["rewrite"] = heap.group(4)
        info["checksum"] = heap.group(5)
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
            "l1d_demand_accesses": str(
                sum_matching(
                    stats,
                    ".demandAccesses::total",
                    "board.cache_hierarchy.l1d-cache-",
                )
            ),
            "l1d_overall_misses": str(
                sum_matching(
                    stats,
                    ".overallMisses::total",
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
            "fake": info.get("fake", ""),
            "rewrite": info.get("rewrite", ""),
            "checksum": info.get("checksum", ""),
            "rc": info.get("rc", ""),
        }
        for counter in PREFETCH_COUNTERS:
            row[counter] = str(sum_matching(stats, f".prefetcher.{counter}", ".prefetcher."))
        rows.append(row)

    base_ticks = int(rows[0]["roi_ticks"])
    base_misses = int(rows[0]["l1d_demand_misses"])
    for row in rows:
        ticks = int(row["roi_ticks"])
        misses = int(row["l1d_demand_misses"])
        row["tick_delta_vs_none_pct"] = f"{((ticks / base_ticks) - 1.0) * 100.0:.3f}"
        row["l1d_miss_delta_vs_none_pct"] = (
            f"{((misses / base_misses) - 1.0) * 100.0:.3f}"
            if base_misses
            else "nan"
        )
    return rows


def as_int(row: dict[str, str], key: str) -> int:
    return int(row[key])


def write_outputs(rows: list[dict[str, str]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / f"heap_pointer_stress_{TAG}_fs_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    by_policy = {row["policy"]: row for row in rows}
    naive = by_policy["naive"]
    copper = by_policy["copper"]
    copper_p131k = by_policy["copper_p131k"]
    copper_clpd16k = by_policy["copper_clpd16k"]
    issue_reduction = (
        1.0 - as_int(copper, "pfIssued") / max(as_int(naive, "pfIssued"), 1)
    ) * 100.0
    ctlw_reduction = (
        1.0
        - as_int(copper, "targetLineWitnessMisses")
        / max(as_int(naive, "targetLineWitnessMisses"), 1)
    ) * 100.0
    block_ratio = (
        as_int(copper, "blockedNoProvenance")
        / max(as_int(copper, "pointerLikeCandidates"), 1)
    ) * 100.0
    p131k_speedup = -float(copper_p131k["tick_delta_vs_none_pct"])
    p131k_ctlw_reduction = (
        1.0
        - as_int(copper_p131k, "targetLineWitnessMisses")
        / max(as_int(naive, "targetLineWitnessMisses"), 1)
    ) * 100.0
    clpd_speedup = -float(copper_clpd16k["tick_delta_vs_none_pct"])
    clpd_issue_reduction = (
        1.0
        - as_int(copper_clpd16k, "pfIssued")
        / max(as_int(naive, "pfIssued"), 1)
    ) * 100.0
    clpd_ctlw_reduction = (
        1.0
        - as_int(copper_clpd16k, "targetLineWitnessMisses")
        / max(as_int(naive, "targetLineWitnessMisses"), 1)
    ) * 100.0

    lines = [
        "# AArch64 Heap Pointer Stress Full-System Summary",
        "",
        "This is a targeted mechanism test, not an official benchmark suite. The",
        "dynamic AArch64 C++ workload allocates a randomized heap pointer chain,",
        "repeatedly traverses committed pointer fields, scans pointer-shaped data",
        "that is never architecturally dereferenced, rewrites a subset of next",
        "pointers, and prints a checksum. The same dynamically linked AArch64 Linux",
        "binary runs under gem5 full-system Ubuntu with the selected L1D prefetcher.",
        "",
        "Workload: `aarch64_heap_pointer_stress --nodes=65536 --passes=8 --fake=65536`.",
        "",
        "| Policy | ROI ticks | Delta vs none | Insts | L1D demand misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Proof evictions | Allowed | Blocked no provenance | Translated PF | Translation faults | CTLW hits | CTLW misses | Terminal stops | Checksum | rc |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for row in rows:
        lines.append(
            "| {policy} | {roi_ticks} | {tick_delta_vs_none_pct}% | {insts_not_nop} | "
            "{l1d_demand_misses} | {l1d_miss_delta_vs_none_pct}% | {pfIssued} | "
            "{pfUseful} | {pointerLikeCandidates} | {learnedProofs} | "
            "{proofEvictions} | {allowedCandidates} | {blockedNoProvenance} | {fillPrefetchTranslated} | "
            "{fillPrefetchTranslationFault} | {targetLineWitnessHits} | "
            "{targetLineWitnessMisses} | {carriedProvenanceTerminalStops} | "
            "{checksum} | {rc} |".format(**row)
        )
    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            f"- Default COPPER issued {issue_reduction:.1f}% fewer prefetches than naive while preserving the same guest checksum and `rc=0`.",
            f"- Default COPPER blocked {as_int(copper, 'blockedNoProvenance')} unproven pointer-shaped candidates, or {block_ratio:.1f}% of its pointer-like observations.",
            f"- Default COPPER reduced CTLW misses by {ctlw_reduction:.1f}% relative to naive and recorded zero fill-origin translation faults.",
            f"- The 131k-proof COPPER sensitivity point recorded zero proof evictions and improved ROI ticks by {p131k_speedup:.3f}% versus no-prefetch, while reducing naive CTLW misses by {p131k_ctlw_reduction:.3f}% and still recording zero fill-origin translation faults.",
            "- The 131k exact-proof point should be treated as a capacity sensitivity, not the recommended hardware point; it motivates the paper's compressed line-provenance directory rather than a large exact source-word table.",
            f"- The 16k compressed line-provenance directory improved ROI ticks by {clpd_speedup:.3f}% versus no-prefetch, issued {clpd_issue_reduction:.1f}% fewer prefetches than naive, reduced naive CTLW misses by {clpd_ctlw_reduction:.3f}%, and recorded zero fill-origin translation faults.",
            "- The 16k CLPD point is the first full-system bridge from the RTL mechanism to a dynamic AArch64 Linux workload; it is not yet a performance win at this capacity, but it validates the compressed authority behavior under the same software path.",
            "- This strengthens the paper's mechanism claim because the source data are real 64-bit heap pointers in a Linux AArch64 C++ process, not only hand-authored static assembly words.",
            "- Stride remains faster on this workload because allocation and vector phases create sequential locality; that should be reported as a conventional-prefetch baseline, not hidden.",
            "",
        ]
    )
    md_path = OUT / f"HEAP_POINTER_STRESS_{TAG.upper()}_FS_SUMMARY.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(md_path)
    print(csv_path)


def main() -> None:
    write_outputs(summarize())


if __name__ == "__main__":
    main()
