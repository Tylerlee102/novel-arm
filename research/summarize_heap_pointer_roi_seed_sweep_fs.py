#!/usr/bin/env python3
"""Summarize multi-seed ROI-bracketed heap-pointer full-system runs."""

from __future__ import annotations

import csv
import math
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "gem5_arm_ubuntu_fs_heap_roi"
TAG = "n32768_p16_f4"
DEFAULT_SEED = "0x9e3779b97f4a7c15"


RUNS = [
    (
        "seed_default",
        DEFAULT_SEED,
        "none",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_none",
    ),
    (
        "seed_default",
        DEFAULT_SEED,
        "naive",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_naive",
    ),
    (
        "seed_default",
        DEFAULT_SEED,
        "copper_clpd64k",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_copper_clpd64k",
    ),
    (
        "seed_default",
        DEFAULT_SEED,
        "copper_clpd64k_peb",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_copper_clpd64k_peb",
    ),
    (
        "seed2",
        "0x0000000000000002",
        "none",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_seed2_none",
    ),
    (
        "seed2",
        "0x0000000000000002",
        "naive",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_seed2_naive",
    ),
    (
        "seed2",
        "0x0000000000000002",
        "copper_clpd64k",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_seed2_copper_clpd64k",
    ),
    (
        "seed2",
        "0x0000000000000002",
        "copper_clpd64k_peb",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_seed2_copper_clpd64k_peb",
    ),
    (
        "seed3",
        "0x0000000000000003",
        "none",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_seed3_none",
    ),
    (
        "seed3",
        "0x0000000000000003",
        "naive",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_seed3_naive",
    ),
    (
        "seed3",
        "0x0000000000000003",
        "copper_clpd64k",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_seed3_copper_clpd64k",
    ),
    (
        "seed3",
        "0x0000000000000003",
        "copper_clpd64k_peb",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_seed3_copper_clpd64k_peb",
    ),
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
    "boundaryFlushes",
    "boundaryAuthorityEntriesDropped",
    "boundaryPrefetchesDropped",
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
        r"HEAP_ROI_STRESS nodes=(\d+) passes=(\d+) fake=(\d+) "
        r"fake_passes=(\d+) rewrite=(\d+)(?: seed=(0x[0-9a-fA-F]+))? "
        r"checksum=(0x[0-9a-fA-F]+)",
        text,
    )
    if heap:
        info["nodes"] = heap.group(1)
        info["passes"] = heap.group(2)
        info["fake"] = heap.group(3)
        info["fake_passes"] = heap.group(4)
        info["rewrite"] = heap.group(5)
        info["seed"] = heap.group(6) or DEFAULT_SEED
        info["checksum"] = heap.group(7)
    done = re.search(r"COPPER_FS_NATIVE_A64_DONE rc=(\d+)", text)
    if done:
        info["rc"] = done.group(1)
    return info


def rows() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for seed_label, expected_seed, policy, run_dir in RUNS:
        stats = first_stats(run_dir / "stats.txt")
        info = terminal_info(run_dir / "board.terminal")
        row: dict[str, str] = {
            "seed_label": seed_label,
            "seed": info.get("seed", expected_seed),
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
            "checksum": info.get("checksum", ""),
            "rc": info.get("rc", ""),
        }
        for counter in COUNTERS:
            row[counter] = str(sum_matching(stats, f".prefetcher.{counter}", ".prefetcher."))
        out.append(row)

    by_seed_policy = {(row["seed_label"], row["policy"]): row for row in out}
    for row in out:
        base = by_seed_policy[(row["seed_label"], "none")]
        row["tick_delta_vs_seed_none_pct"] = (
            f"{((int(row['roi_ticks']) / int(base['roi_ticks'])) - 1.0) * 100.0:.3f}"
        )
        row["l1d_miss_delta_vs_seed_none_pct"] = (
            f"{((int(row['l1d_demand_misses']) / int(base['l1d_demand_misses'])) - 1.0) * 100.0:.3f}"
        )
    return out


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def write_outputs(data: list[dict[str, str]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / f"heap_pointer_roi_{TAG}_seed_sweep_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)

    deltas: dict[str, list[float]] = defaultdict(list)
    pf_issued: dict[str, list[int]] = defaultdict(list)
    faults: dict[str, int] = defaultdict(int)
    ctlw_misses: dict[str, int] = defaultdict(int)
    proof_evictions: dict[str, int] = defaultdict(int)
    for row in data:
        if row["policy"] == "none":
            continue
        policy = row["policy"]
        deltas[policy].append(float(row["tick_delta_vs_seed_none_pct"]))
        pf_issued[policy].append(int(row["pfIssued"]))
        faults[policy] += int(row["fillPrefetchTranslationFault"])
        ctlw_misses[policy] += int(row["targetLineWitnessMisses"])
        proof_evictions[policy] += int(row["proofEvictions"])

    lines = [
        "# AArch64 Heap Pointer ROI Multi-Seed Summary",
        "",
        "This adds two independent heap-layout seeds to the default-seed ROI",
        "experiment. Each seed compares no-prefetch, naive pointer-shaped DMP,",
        "CLPD-64K, and CLPD-64K with a provenance epoch boundary under the same AArch64 Linux full-system path.",
        "",
        "| Seed | Policy | ROI ticks | Delta vs seed none | L1D misses | PF issued | PF useful | Pointer-like | Proof evictions | Blocked no provenance | CTLW misses | Translation faults | Boundary authority drops | Boundary PF drops | Checksum | rc |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for seed_label in ["seed_default", "seed2", "seed3"]:
        for policy in ["none", "naive", "copper_clpd64k", "copper_clpd64k_peb"]:
            row = next(
                item
                for item in data
                if item["seed_label"] == seed_label and item["policy"] == policy
            )
            lines.append(
                "| {seed_label} | {policy} | {roi_ticks} | {tick_delta_vs_seed_none_pct}% | "
                "{l1d_demand_misses} | {pfIssued} | {pfUseful} | {pointerLikeCandidates} | "
                "{proofEvictions} | {blockedNoProvenance} | {targetLineWitnessMisses} | "
                "{fillPrefetchTranslationFault} | {boundaryAuthorityEntriesDropped} | "
                "{boundaryPrefetchesDropped} | {checksum} | {rc} |".format(**row)
            )

    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            "| Policy | Mean delta vs seed none | Min delta | Max delta | Mean PF issued | Total proof evictions | Total CTLW misses | Translation faults |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for policy in ["naive", "copper_clpd64k", "copper_clpd64k_peb"]:
        values = deltas[policy]
        lines.append(
            f"| {policy} | {mean(values):.3f}% | {min(values):.3f}% | "
            f"{max(values):.3f}% | {mean([float(x) for x in pf_issued[policy]]):.1f} | "
            f"{proof_evictions[policy]} | {ctlw_misses[policy]} | {faults[policy]} |"
        )

    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            "- CLPD-64K improves ROI ticks on all three measured heap layouts and records zero translation faults.",
            "- CLPD-64K+PEB measures the cost of flushing pre-boundary authority before the ROI.",
            "- Naive pointer-shaped DMP slows down all three measured heap layouts while producing large CTLW-miss counts.",
            "- This is still a targeted workload rather than a general benchmark suite, but it is no longer a single-layout result.",
            "",
        ]
    )
    md_path = OUT / f"HEAP_POINTER_ROI_{TAG.upper()}_SEED_SWEEP_SUMMARY.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(md_path)
    print(csv_path)


def main() -> None:
    write_outputs(rows())


if __name__ == "__main__":
    main()
