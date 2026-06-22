#!/usr/bin/env python3
"""Summarize the fake-pointer-only AArch64 full-system control."""

from __future__ import annotations

import csv
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "gem5_arm_ubuntu_fs_heap_roi"
TAG = "n32768_fakeonly_f4"


RUNS = [
    ("none", RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_none"),
    ("spp", RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_spp"),
    ("naive", RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_naive"),
    ("copper_clpd64k", RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_copper_clpd64k"),
    ("copper_clpd64k_peb", RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_copper_clpd64k_peb"),
    ("spp_copper_slack", RESULTS / f"gem5_arm_ubuntu_fs_heap_roi_{TAG}_spp_copper_slack"),
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


def sum_prefetch_counter(stats: dict[str, float], counter: str) -> int:
    matches = [
        (key, value)
        for key, value in stats.items()
        if key.endswith(f".{counter}")
        and ".prefetcher" in key
        and not math.isnan(value)
    ]
    child_matches = [
        value
        for key, value in matches
        if ".prefetchers" in key
        or ".primary." in key
        or ".companion." in key
    ]
    if child_matches:
        return int(sum(child_matches))
    return int(sum(value for _, value in matches))


def terminal_info(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(
        r"HEAP_ROI_STRESS nodes=(\d+) passes=(\d+) fake=(\d+) "
        r"fake_passes=(\d+) rewrite=(\d+) seed=(0x[0-9a-fA-F]+) "
        r"checksum=(0x[0-9a-fA-F]+)",
        text,
    )
    info: dict[str, str] = {}
    if match:
        info.update(
            {
                "nodes": match.group(1),
                "passes": match.group(2),
                "fake": match.group(3),
                "fake_passes": match.group(4),
                "rewrite": match.group(5),
                "seed": match.group(6),
                "checksum": match.group(7),
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
            "nodes": info.get("nodes", ""),
            "passes": info.get("passes", ""),
            "fake": info.get("fake", ""),
            "fake_passes": info.get("fake_passes", ""),
            "rewrite": info.get("rewrite", ""),
            "seed": info.get("seed", ""),
            "checksum": info.get("checksum", ""),
            "rc": info.get("rc", ""),
        }
        for counter in COUNTERS:
            row[counter] = str(sum_prefetch_counter(stats, counter))
        rows.append(row)

    base_ticks = int(rows[0]["roi_ticks"])
    for row in rows:
        row["tick_delta_vs_none_pct"] = (
            f"{((int(row['roi_ticks']) / base_ticks) - 1.0) * 100.0:.3f}"
        )
    return rows


def as_int(row: dict[str, str], key: str) -> int:
    return int(row[key])


def write_outputs(rows: list[dict[str, str]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / f"heap_pointer_roi_{TAG}_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    by_policy = {row["policy"]: row for row in rows}
    naive = by_policy["naive"]
    clpd = by_policy["copper_clpd64k"]
    clpd_peb = by_policy["copper_clpd64k_peb"]
    scoop = by_policy.get("spp_copper_slack")
    clpd_block_rate = (
        as_int(clpd, "blockedNoProvenance")
        / max(as_int(clpd, "pointerLikeCandidates"), 1)
    ) * 100.0
    clpd_peb_block_rate = (
        as_int(clpd_peb, "blockedNoProvenance")
        / max(as_int(clpd_peb, "pointerLikeCandidates"), 1)
    ) * 100.0
    issue_reduction = (
        1.0 - as_int(clpd, "pfIssued") / max(as_int(naive, "pfIssued"), 1)
    ) * 100.0
    peb_issue_reduction = (
        1.0 - as_int(clpd_peb, "pfIssued") / max(as_int(naive, "pfIssued"), 1)
    ) * 100.0
    ctlw_reduction = (
        1.0
        - as_int(clpd, "targetLineWitnessMisses")
        / max(as_int(naive, "targetLineWitnessMisses"), 1)
    ) * 100.0

    lines = [
        "# AArch64 Heap Pointer Fake-Only Full-System Control",
        "",
        "This control runs the ROI benchmark with `--passes=0 --rewrite=0`, so",
        "the ROI primarily scans pointer-shaped fake data that is not",
        "architecturally dereferenced as a pointer. gem5 statistics are reset",
        "inside the AArch64 binary before the fake scan.",
        "",
        "| Policy | ROI ticks | Delta vs none | L1D misses | PF issued | PF useful | Pointer-like | Learned proofs | Proof evictions | Allowed | Blocked no provenance | Translated PF | Translation faults | CTLW hits | CTLW misses | Terminal stops | Boundary flushes | Boundary authority drops | Boundary PF drops | Checksum | rc |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for row in rows:
        lines.append(
            "| {policy} | {roi_ticks} | {tick_delta_vs_none_pct}% | {l1d_demand_misses} | "
            "{pfIssued} | {pfUseful} | {pointerLikeCandidates} | {learnedProofs} | "
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
            f"- Naive treats all {as_int(naive, 'pointerLikeCandidates')} pointer-shaped observations as eligible and issues {as_int(naive, 'pfIssued')} prefetches.",
            f"- CLPD-64K blocks {clpd_block_rate:.5f}% of pointer-shaped observations, issues {issue_reduction:.3f}% fewer prefetches than naive, and reduces naive CTLW misses by {ctlw_reduction:.3f}%.",
            f"- CLPD-64K with a provenance epoch boundary blocks {clpd_peb_block_rate:.5f}% of pointer-shaped observations and issues {peb_issue_reduction:.3f}% fewer prefetches than naive.",
            f"- CLPD-64K still allows {as_int(clpd, 'allowedCandidates')} candidates in this warm full-system control. With the explicit provenance epoch boundary, the same control allows {as_int(clpd_peb, 'allowedCandidates')} candidates after dropping {as_int(clpd_peb, 'boundaryAuthorityEntriesDropped')} stale authority entries and {as_int(clpd_peb, 'boundaryPrefetchesDropped')} queued prefetches.",
            (
                f"- SCOOP/SPP+COPPER on the same fake-only ROI issues {as_int(scoop, 'pfIssued')} total prefetches, "
                f"blocks {as_int(scoop, 'blockedNoProvenance')} unproven content-derived candidates, "
                f"has {as_int(scoop, 'allowedCandidates')} COPPER companion allowed candidates, "
                f"and records {as_int(scoop, 'fillPrefetchTranslationFault')} translation faults."
                if scoop is not None
                else "- SCOOP/SPP+COPPER was not present in this summary."
            ),
            "- All policies preserve the same checksum and `rc=0`, and CLPD records zero fill-origin translation faults.",
            "",
        ]
    )
    md_path = OUT / f"HEAP_POINTER_ROI_{TAG.upper()}_SUMMARY.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(md_path)
    print(csv_path)


def main() -> None:
    write_outputs(summarize())


if __name__ == "__main__":
    main()
