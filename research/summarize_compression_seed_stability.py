#!/usr/bin/env python3
"""Aggregate Zstd/zlib seed-stability summaries for COPPER."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "COMPRESSION_LIBRARY_SEED_STABILITY_20260620.md"
CSV_OUT = RESULTS / "compression_library_seed_stability_20260620.csv"


@dataclass(frozen=True)
class Point:
    library: str
    seed_label: str
    csv_path: Path


POINTS = (
    Point(
        "Zstd",
        "seed0",
        RESULTS / "gem5_arm_ubuntu_fs_zstd_app" / "zstd_zstd_tiny_summary.csv",
    ),
    Point(
        "Zstd",
        "seed1",
        RESULTS / "gem5_arm_ubuntu_fs_zstd_app" / "zstd_zstd_seed1_summary.csv",
    ),
    Point(
        "zlib",
        "seed0",
        RESULTS / "gem5_arm_ubuntu_fs_zlib_app" / "zlib_zlib_tiny_summary.csv",
    ),
    Point(
        "zlib",
        "seed1",
        RESULTS / "gem5_arm_ubuntu_fs_zlib_app" / "zlib_zlib_seed1_summary.csv",
    ),
)


def pct_reduction(new: int, old: int) -> float:
    return 100.0 * (1.0 - (new / old)) if old else 0.0


def load_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return {row["policy"]: row for row in csv.DictReader(fh)}


def main() -> None:
    rows: list[dict[str, str]] = []
    for point in POINTS:
        by_policy = load_rows(point.csv_path)
        none = by_policy["none"]
        naive = by_policy["naive"]
        copper = by_policy["copper_clpd64k_peb"]
        spp = by_policy["spp"]
        slack = by_policy["spp_copper_slack"]
        naive_ctlw = int(naive["targetLineWitnessMisses"])
        copper_ctlw = int(copper["targetLineWitnessMisses"])
        slack_ctlw = int(slack["targetLineWitnessMisses"])
        row = {
            "library": point.library,
            "seed_label": point.seed_label,
            "input_seed": none["seed"],
            "checksum": none["checksum"],
            "rcs": ",".join(sorted({r["rc"] for r in by_policy.values()})),
            "naive_ctlw": str(naive_ctlw),
            "copper_ctlw": str(copper_ctlw),
            "slack_ctlw": str(slack_ctlw),
            "copper_ctlw_reduction_pct": f"{pct_reduction(copper_ctlw, naive_ctlw):.3f}",
            "slack_ctlw_reduction_pct": f"{pct_reduction(slack_ctlw, naive_ctlw):.3f}",
            "copper_faults": copper["fillPrefetchTranslationFault"],
            "slack_faults": slack["fillPrefetchTranslationFault"],
            "spp_delta_pct": spp["tick_delta_vs_none_pct"],
            "slack_delta_pct": slack["tick_delta_vs_none_pct"],
            "slack_gap_vs_spp_points": f"{float(slack['tick_delta_vs_none_pct']) - float(spp['tick_delta_vs_none_pct']):.3f}",
            "bytes": none["bytes"],
            "rounds": none["rounds"],
            "level": none["level"],
            "pointer_like_words": none["pointer_like_words"],
            "total_compressed": none["total_compressed"],
        }
        rows.append(row)

    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    min_copper = min(float(r["copper_ctlw_reduction_pct"]) for r in rows)
    min_slack = min(float(r["slack_ctlw_reduction_pct"]) for r in rows)
    max_abs_gap = max(abs(float(r["slack_gap_vs_spp_points"])) for r in rows)
    fault_total = sum(int(r["copper_faults"]) + int(r["slack_faults"]) for r in rows)
    rcs_ok = all(r["rcs"] == "0" for r in rows)
    checksums_unique = len({(r["library"], r["checksum"]) for r in rows})

    lines = [
        "# Compression-Library Seed Stability",
        "",
        "Date: 2026-06-20",
        "",
        "This artifact aggregates two deterministic input seeds each for public",
        "Zstd and zlib AArch64 Linux full-system workloads. The workloads call",
        "the guest Ubuntu ARM64 library ABI over buffers containing",
        "address-shaped words as data. They are library-driver evidence, not",
        "production storage or network compression services.",
        "",
        "| Library | Seed | Checksum | Naive CTLW | COPPER CTLW | COPPER reduction | SPP+COPPER CTLW | SPP+COPPER reduction | SPP delta | Slack delta | Slack gap vs SPP | Faults |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        faults = int(row["copper_faults"]) + int(row["slack_faults"])
        lines.append(
            f"| {row['library']} | {row['input_seed']} | {row['checksum']} | "
            f"{row['naive_ctlw']} | {row['copper_ctlw']} | "
            f"{row['copper_ctlw_reduction_pct']}% | {row['slack_ctlw']} | "
            f"{row['slack_ctlw_reduction_pct']}% | {row['spp_delta_pct']}% | "
            f"{row['slack_delta_pct']}% | {row['slack_gap_vs_spp_points']} | {faults} |"
        )

    lines.extend(
        [
            "",
            "Aggregate interpretation:",
            "",
            f"- Seed/library points: {len(rows)}.",
            f"- Distinct library-checksum pairs: {checksums_unique}.",
            f"- Return-code agreement across all policies: {'yes' if rcs_ok else 'no'}.",
            f"- Minimum COPPER CTLW reduction versus naive DMP: {min_copper:.1f}%.",
            f"- Minimum SPP+COPPER slack CTLW reduction versus naive DMP: {min_slack:.1f}%.",
            f"- Worst absolute SPP+COPPER slack tick gap versus SPP: {max_abs_gap:.3f} percentage points.",
            f"- COPPER/slack translation faults across all seed points: {fault_total}.",
            "- The compression-library evidence strengthens public-library breadth, but does not replace SPEC-like, production server, or production compression-service evaluation.",
            "",
            "status=PASS" if rcs_ok and fault_total == 0 else "status=FAIL",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(CSV_OUT)
    print(OUT)


if __name__ == "__main__":
    main()
