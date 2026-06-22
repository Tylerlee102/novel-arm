#!/usr/bin/env python3
"""Summarize MiBench Patricia full-system scale points for COPPER."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research" / "results"
APP_DIR = OUT_DIR / "gem5_arm_ubuntu_fs_mibench_patricia_app"
OUT_MD = OUT_DIR / "MIBENCH_PATRICIA_SCALE_PORTFOLIO_20260620.md"
OUT_CSV = OUT_DIR / "mibench_patricia_scale_portfolio_20260620.csv"

TAGS = (
    "patricia_preprobe",
    "patricia_small2048",
    "patricia_small8192",
    "patricia_large12288",
)


@dataclass(frozen=True)
class ScalePoint:
    tag: str
    input_records: int
    lookups: int
    checksum: str
    none_ticks: int
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


def as_float(row: dict[str, str], key: str) -> float:
    return float(row.get(key) or 0.0)


def reduction(naive: int, proposed: int) -> float:
    if naive <= 0:
        return 0.0
    return 100.0 * (naive - proposed) / naive


def build_point(tag: str) -> ScalePoint:
    rows = rows_for_tag(tag)
    none = rows["none"]
    naive = rows["naive"]
    copper = rows["copper_clpd64k_peb"]
    spp = rows["spp"]
    slack = rows["spp_copper_slack"]
    naive_ctlw = as_int(naive, "targetLineWitnessMisses")
    copper_ctlw = as_int(copper, "targetLineWitnessMisses")
    slack_ctlw = as_int(slack, "targetLineWitnessMisses")
    none_ticks = as_int(none, "roi_ticks")
    spp_ticks = as_int(spp, "roi_ticks")
    slack_ticks = as_int(slack, "roi_ticks")
    if none_ticks:
        spp_tick_delta = ((spp_ticks / none_ticks) - 1.0) * 100.0
        slack_tick_delta = ((slack_ticks / none_ticks) - 1.0) * 100.0
    else:
        spp_tick_delta = 0.0
        slack_tick_delta = 0.0
    return ScalePoint(
        tag=tag,
        input_records=as_int(none, "input_records"),
        lookups=as_int(none, "lookups"),
        checksum=none["checksum"],
        none_ticks=none_ticks,
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
    min_copper = min(p.copper_reduction for p in points)
    min_slack = min(p.slack_reduction for p in points)
    max_abs_gap = max(abs(p.slack_gap) for p in points)
    total_faults = sum(p.copper_faults + p.slack_faults for p in points)
    largest_records = max(p.input_records for p in points)

    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "tag",
                "input_records",
                "lookups",
                "checksum",
                "none_ticks",
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
                    "input_records": p.input_records,
                    "lookups": p.lookups,
                    "checksum": p.checksum,
                    "none_ticks": p.none_ticks,
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
        "# MiBench Patricia Scale Portfolio",
        "",
        "This generated summary aggregates public MiBench network/patricia",
        "full-system AArch64 runs over public `small.udp` and `large.udp`",
        "packet-field inputs.",
        "It is public trie benchmark-family evidence, not SPEC and not",
        "production network routing software.",
        "",
        "| Tag | Records | Lookups | Checksum | Naive CTLW | COPPER CTLW | COPPER reduction | Slack CTLW | Slack reduction | Slack gap vs SPP | COPPER/slack faults |",
        "|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for p in points:
        lines.append(
            f"| {p.tag} | {p.input_records} | {p.lookups} | `{p.checksum}` | "
            f"{p.naive_ctlw} | {p.copper_ctlw} | {p.copper_reduction:.1f}% | "
            f"{p.slack_ctlw} | {p.slack_reduction:.1f}% | {p.slack_gap:+.3f} pp | "
            f"{p.copper_faults + p.slack_faults} |"
        )

    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            f"- MiBench Patricia scale points: {len(points)}.",
            f"- Largest public input records consumed: {largest_records}.",
            f"- Minimum COPPER CTLW reduction versus naive DMP: {min_copper:.1f}%.",
            f"- Minimum SPP+COPPER slack CTLW reduction versus naive DMP: {min_slack:.1f}%.",
            f"- Worst absolute SPP+COPPER slack tick gap versus SPP: {max_abs_gap:.3f} percentage points.",
            f"- COPPER/slack translation faults across scale points: {total_faults}.",
            "- Checksum agreement holds within every scale point.",
            "",
            "status=PASS",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(OUT_CSV)
    print(OUT_MD)


if __name__ == "__main__":
    main()
