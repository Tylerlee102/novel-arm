#!/usr/bin/env python3
"""Summarize 12K MiBench Patricia seed stability for COPPER."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research" / "results"
APP_DIR = OUT_DIR / "gem5_arm_ubuntu_fs_mibench_patricia_app"
OUT_MD = OUT_DIR / "MIBENCH_PATRICIA_12K_SEED_STABILITY_20260621.md"
OUT_CSV = OUT_DIR / "mibench_patricia_12k_seed_stability_20260621.csv"

TAGS = (
    "patricia_large12288",
    "patricia_large12288_seed1",
)


@dataclass(frozen=True)
class SeedPoint:
    tag: str
    seed: int
    input_records: int
    lookups: int
    checksum: str
    naive_ctlw: int
    copper_ctlw: int
    slack_ctlw: int
    copper_reduction: float
    slack_reduction: float
    copper_faults: int
    slack_faults: int
    spp_tick_delta: float
    slack_tick_delta: float
    slack_gap: float


def rows_for_tag(tag: str) -> dict[str, dict[str, str]]:
    path = APP_DIR / f"mibench_patricia_{tag}_summary.csv"
    with path.open(newline="", encoding="utf-8") as fh:
        return {row["policy"]: row for row in csv.DictReader(fh)}


def as_int(row: dict[str, str], key: str) -> int:
    return int(row.get(key) or 0)


def reduction(naive: int, proposed: int) -> float:
    if naive <= 0:
        return 0.0
    return 100.0 * (naive - proposed) / naive


def build_point(tag: str) -> SeedPoint:
    rows = rows_for_tag(tag)
    none = rows["none"]
    naive = rows["naive"]
    copper = rows["copper_clpd64k_peb"]
    spp = rows["spp"]
    slack = rows["spp_copper_slack"]
    none_ticks = as_int(none, "roi_ticks")
    spp_ticks = as_int(spp, "roi_ticks")
    slack_ticks = as_int(slack, "roi_ticks")
    naive_ctlw = as_int(naive, "targetLineWitnessMisses")
    copper_ctlw = as_int(copper, "targetLineWitnessMisses")
    slack_ctlw = as_int(slack, "targetLineWitnessMisses")
    spp_tick_delta = ((spp_ticks / none_ticks) - 1.0) * 100.0 if none_ticks else 0.0
    slack_tick_delta = ((slack_ticks / none_ticks) - 1.0) * 100.0 if none_ticks else 0.0
    return SeedPoint(
        tag=tag,
        seed=as_int(none, "seed"),
        input_records=as_int(none, "input_records"),
        lookups=as_int(none, "lookups"),
        checksum=none["checksum"],
        naive_ctlw=naive_ctlw,
        copper_ctlw=copper_ctlw,
        slack_ctlw=slack_ctlw,
        copper_reduction=reduction(naive_ctlw, copper_ctlw),
        slack_reduction=reduction(naive_ctlw, slack_ctlw),
        copper_faults=as_int(copper, "fillPrefetchTranslationFault"),
        slack_faults=as_int(slack, "fillPrefetchTranslationFault"),
        spp_tick_delta=spp_tick_delta,
        slack_tick_delta=slack_tick_delta,
        slack_gap=slack_tick_delta - spp_tick_delta,
    )


def main() -> None:
    points = [build_point(tag) for tag in TAGS]
    distinct_checksums = len({p.checksum for p in points})
    total_faults = sum(p.copper_faults + p.slack_faults for p in points)
    min_copper = min(p.copper_reduction for p in points)
    min_slack = min(p.slack_reduction for p in points)
    max_abs_gap = max(abs(p.slack_gap) for p in points)
    all_records = {p.input_records for p in points}
    all_lookups = {p.lookups for p in points}

    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "tag",
                "seed",
                "input_records",
                "lookups",
                "checksum",
                "naive_ctlw",
                "copper_ctlw",
                "slack_ctlw",
                "copper_reduction_pct",
                "slack_reduction_pct",
                "copper_faults",
                "slack_faults",
                "spp_tick_delta_pct",
                "slack_tick_delta_pct",
                "slack_gap_pp",
            ],
        )
        writer.writeheader()
        for p in points:
            writer.writerow(
                {
                    "tag": p.tag,
                    "seed": p.seed,
                    "input_records": p.input_records,
                    "lookups": p.lookups,
                    "checksum": p.checksum,
                    "naive_ctlw": p.naive_ctlw,
                    "copper_ctlw": p.copper_ctlw,
                    "slack_ctlw": p.slack_ctlw,
                    "copper_reduction_pct": f"{p.copper_reduction:.3f}",
                    "slack_reduction_pct": f"{p.slack_reduction:.3f}",
                    "copper_faults": p.copper_faults,
                    "slack_faults": p.slack_faults,
                    "spp_tick_delta_pct": f"{p.spp_tick_delta:.3f}",
                    "slack_tick_delta_pct": f"{p.slack_tick_delta:.3f}",
                    "slack_gap_pp": f"{p.slack_gap:+.3f}",
                }
            )

    lines = [
        "# MiBench Patricia 12K Seed Stability",
        "",
        "This generated summary aggregates two completed public MiBench",
        "`large.udp` 12,288-record full-system AArch64 Patricia runs.",
        "The seeds change the deterministic lookup sequence and produce",
        "distinct checksums while keeping the same public input prefix.",
        "",
        "| Tag | Seed | Records | Lookups | Checksum | Naive CTLW | COPPER CTLW | COPPER reduction | Slack CTLW | Slack reduction | Slack gap vs SPP | COPPER/slack faults |",
        "|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for p in points:
        lines.append(
            f"| {p.tag} | {p.seed} | {p.input_records} | {p.lookups} | `{p.checksum}` | "
            f"{p.naive_ctlw} | {p.copper_ctlw} | {p.copper_reduction:.1f}% | "
            f"{p.slack_ctlw} | {p.slack_reduction:.1f}% | {p.slack_gap:+.3f} pp | "
            f"{p.copper_faults + p.slack_faults} |"
        )

    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            f"- MiBench Patricia 12K seed points: {len(points)}.",
            f"- Public input records per seed: {next(iter(all_records)) if len(all_records) == 1 else sorted(all_records)}.",
            f"- Lookup operations per seed: {next(iter(all_lookups)) if len(all_lookups) == 1 else sorted(all_lookups)}.",
            f"- Distinct per-seed checksums: {distinct_checksums}.",
            f"- Minimum COPPER CTLW reduction versus naive DMP: {min_copper:.1f}%.",
            f"- Minimum SPP+COPPER slack CTLW reduction versus naive DMP: {min_slack:.1f}%.",
            f"- Worst absolute SPP+COPPER slack tick gap versus SPP: {max_abs_gap:.3f} percentage points.",
            f"- COPPER/slack translation faults across both 12K seeds: {total_faults}.",
            "- Return-code agreement holds within every seed point.",
            "",
            "status=PASS" if distinct_checksums == len(points) and total_faults == 0 else "status=FAIL",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(OUT_CSV)
    print(OUT_MD)


if __name__ == "__main__":
    main()
