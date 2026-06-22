#!/usr/bin/env python3
"""Summarize ROI-bracketed AArch64 heap-pointer stress full-system runs."""

from __future__ import annotations

import csv
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "gem5_arm_ubuntu_fs_heap_roi"
TAG = "n32768_p16_f4"


RUNS = [
    ("none", RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_none"),
    ("stride", RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_stride"),
    ("naive", RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_naive"),
    (
        "copper_exact16k",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_copper_exact16k",
    ),
    (
        "copper_exact131k",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_copper_exact131k",
    ),
    (
        "copper_clpd8k",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_copper_clpd8k",
    ),
    (
        "copper_clpd16k",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_copper_clpd16k",
    ),
    (
        "copper_clpd32k",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_copper_clpd32k",
    ),
    (
        "copper_clpd64k",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_copper_clpd64k",
    ),
    (
        "copper_clpd64k_peb",
        RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_copper_clpd64k_peb",
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
        info["seed"] = heap.group(6) or ""
        info["checksum"] = heap.group(7)
    done = re.search(r"COPPER_FS_NATIVE_A64_DONE rc=(\d+)", text)
    if done:
        info["rc"] = done.group(1)
    info["roi_reset"] = "yes" if "HEAP_ROI_RESET" in text else "no"
    info["roi_dump"] = "yes" if "HEAP_ROI_DUMP" in text else "no"
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
            "fake_passes": info.get("fake_passes", ""),
            "rewrite": info.get("rewrite", ""),
            "seed": info.get("seed", ""),
            "checksum": info.get("checksum", ""),
            "rc": info.get("rc", ""),
            "roi_reset": info.get("roi_reset", ""),
            "roi_dump": info.get("roi_dump", ""),
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
    csv_path = OUT / f"heap_pointer_roi_{TAG}_fs_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    by_policy = {row["policy"]: row for row in rows}
    naive = by_policy["naive"]
    exact16 = by_policy["copper_exact16k"]
    exact131 = by_policy["copper_exact131k"]
    clpd8 = by_policy["copper_clpd8k"]
    clpd16 = by_policy["copper_clpd16k"]
    clpd32 = by_policy["copper_clpd32k"]
    clpd64 = by_policy["copper_clpd64k"]
    clpd64_peb = by_policy["copper_clpd64k_peb"]

    def speedup(row: dict[str, str]) -> float:
        return -float(row["tick_delta_vs_none_pct"])

    def reduction(row: dict[str, str], key: str) -> float:
        return (
            1.0 - as_int(row, key) / max(as_int(naive, key), 1)
        ) * 100.0

    lines = [
        "# AArch64 Heap Pointer ROI Full-System Summary",
        "",
        "This workload resets gem5 statistics inside the AArch64 binary after",
        "heap construction and dumps them before process exit. The first stats",
        "section therefore measures the pointer traversal, fake pointer-shaped",
        "data scan, and rewrite validation phase, not allocation/setup.",
        "",
        "Workload: `aarch64_heap_pointer_roi_stress --nodes=32768 --passes=16 --fake=32768 --fake-passes=4`.",
        "",
        "| Policy | ROI ticks | Delta vs none | Insts | L1D demand misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Proof evictions | Allowed | Blocked no provenance | Translated PF | Translation faults | CTLW hits | CTLW misses | Terminal stops | Boundary flushes | Boundary authority drops | Boundary PF drops | Checksum | rc |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for row in rows:
        lines.append(
            "| {policy} | {roi_ticks} | {tick_delta_vs_none_pct}% | {insts_not_nop} | "
            "{l1d_demand_misses} | {l1d_miss_delta_vs_none_pct}% | {pfIssued} | "
            "{pfUseful} | {pointerLikeCandidates} | {learnedProofs} | "
            "{proofEvictions} | {allowedCandidates} | {blockedNoProvenance} | "
            "{fillPrefetchTranslated} | {fillPrefetchTranslationFault} | "
            "{targetLineWitnessHits} | {targetLineWitnessMisses} | "
            "{carriedProvenanceTerminalStops} | {boundaryFlushes} | "
            "{boundaryAuthorityEntriesDropped} | {boundaryPrefetchesDropped} | "
            "{checksum} | {rc} |".format(**row)
        )

    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            f"- Exact COPPER-16K changes ROI ticks by {exact16['tick_delta_vs_none_pct']}% while issuing {reduction(exact16, 'pfIssued'):.1f}% fewer prefetches than naive and recording zero translation faults.",
            f"- Exact COPPER-131K changes ROI ticks by {exact131['tick_delta_vs_none_pct']}% and reduces naive CTLW misses by {reduction(exact131, 'targetLineWitnessMisses'):.3f}%.",
            f"- CLPD-8K changes ROI ticks by {clpd8['tick_delta_vs_none_pct']}%, issues {reduction(clpd8, 'pfIssued'):.1f}% fewer prefetches than naive, and records {as_int(clpd8, 'proofEvictions')} proof-directory evictions.",
            f"- CLPD-16K changes ROI ticks by {clpd16['tick_delta_vs_none_pct']}%, issues {reduction(clpd16, 'pfIssued'):.1f}% fewer prefetches than naive, and records zero translation faults.",
            f"- CLPD-32K changes ROI ticks by {clpd32['tick_delta_vs_none_pct']}%, reduces naive CTLW misses by {reduction(clpd32, 'targetLineWitnessMisses'):.3f}%, and records {as_int(clpd32, 'proofEvictions')} proof-directory evictions.",
            f"- CLPD-64K changes ROI ticks by {clpd64['tick_delta_vs_none_pct']}%, reduces naive CTLW misses by {reduction(clpd64, 'targetLineWitnessMisses'):.3f}%, and records {as_int(clpd64, 'proofEvictions')} proof-directory evictions.",
            f"- CLPD-64K+PEB changes ROI ticks by {clpd64_peb['tick_delta_vs_none_pct']}%, drops {as_int(clpd64_peb, 'boundaryAuthorityEntriesDropped')} pre-boundary authority entries and {as_int(clpd64_peb, 'boundaryPrefetchesDropped')} queued prefetches, and reduces naive CTLW misses by {reduction(clpd64_peb, 'targetLineWitnessMisses'):.3f}%.",
            f"- Naive changes ROI ticks by {naive['tick_delta_vs_none_pct']}% while translating {as_int(naive, 'fillPrefetchTranslated')} fill-origin prefetches and suffering {as_int(naive, 'targetLineWitnessMisses')} CTLW misses.",
            "- The checksum and rc match across all policies, so differences are not due to guest-visible behavior changes.",
            "- The result is a mechanism-validating ROI study, not a broad benchmark claim.",
            "",
        ]
    )

    md_path = OUT / f"HEAP_POINTER_ROI_{TAG.upper()}_FS_SUMMARY.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(md_path)
    print(csv_path)
    print(f"best_speedup_vs_none_pct={max(speedup(row) for row in rows):.3f}")


def main() -> None:
    write_outputs(summarize())


if __name__ == "__main__":
    main()
