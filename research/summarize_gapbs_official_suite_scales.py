#!/usr/bin/env python3
"""Compare official GAPBS full-system suite summaries across graph scales."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "results" / "gem5_arm_ubuntu_fs_gapbs_official_suite"
SCALES = [10, 12, 14]
POLICIES = ["none", "naive", "copper"]


def read_rows(scale: int) -> list[dict[str, str]]:
    path = OUT / f"gapbs_official_suite_g{scale}_fs_summary.csv"
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def total(rows: list[dict[str, str]], policy: str, key: str) -> int:
    return sum(int(row[key]) for row in rows if row["policy"] == policy)


def pct(num: float) -> str:
    return f"{num:.3f}%"


def main() -> None:
    lines = [
        "# Official GAPBS Full-System Cross-Scale Summary",
        "",
        "This file compares the official GAPBS AArch64 full-system suite at the three",
        "scales currently run locally. The numbers aggregate BFS, CC, PR, and SSSP",
        "within each policy.",
        "",
        "| Scale | Policy | Total ROI ticks | Delta vs none | L1D demand misses | L1D miss delta | PF issued | PF useful rate | Pointer-like | Blocked no provenance | Translated PF | Translation faults | CTLW misses | CTLW miss reduction vs naive |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for scale in SCALES:
        rows = read_rows(scale)
        base_ticks = total(rows, "none", "roi_ticks")
        base_misses = total(rows, "none", "l1d_demand_misses")
        naive_ctlw = max(total(rows, "naive", "targetLineWitnessMisses"), 1)
        for policy in POLICIES:
            ticks = total(rows, policy, "roi_ticks")
            misses = total(rows, policy, "l1d_demand_misses")
            issued = total(rows, policy, "pfIssued")
            useful = total(rows, policy, "pfUseful")
            pointer_like = total(rows, policy, "pointerLikeCandidates")
            blocked = total(rows, policy, "blockedNoProvenance")
            translated = total(rows, policy, "fillPrefetchTranslated")
            faults = total(rows, policy, "fillPrefetchTranslationFault")
            ctlw_misses = total(rows, policy, "targetLineWitnessMisses")
            useful_rate = (useful / issued * 100.0) if issued else 0.0
            ctlw_reduction = (
                (1.0 - ctlw_misses / naive_ctlw) * 100.0
                if policy == "copper"
                else 0.0
            )
            lines.append(
                f"| {scale} | {policy} | {ticks} | "
                f"{pct((ticks / base_ticks - 1.0) * 100.0)} | {misses} | "
                f"{pct((misses / base_misses - 1.0) * 100.0)} | {issued} | "
                f"{pct(useful_rate)} | {pointer_like} | {blocked} | {translated} | "
                f"{faults} | {ctlw_misses} | {pct(ctlw_reduction)} |"
            )

    lines.extend(
        [
            "",
            "Key readout:",
            "",
            "- The official suite now scales from 1024-node to 16384-node generated GAPBS graphs under full-system AArch64 Linux.",
            "- COPPER's performance movement remains near zero on these integer-edge graph kernels, so the paper should not sell GAPBS as the speedup centerpiece.",
            "- COPPER's safety/control behavior scales: it blocks unproven pointer-shaped candidates, keeps fill-origin translation faults at zero, and suppresses almost all naive cross-page CTLW misses.",
            "- The strongest conference-facing use of official GAPBS is external validity and negative-control evidence; pointer-heavy microbenchmarks and targeted security traces remain the right place to show the main mechanism's benefit.",
            "",
        ]
    )

    out_path = OUT / "GAPBS_OFFICIAL_SUITE_CROSS_SCALE_SUMMARY.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
