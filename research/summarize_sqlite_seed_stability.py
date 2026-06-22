#!/usr/bin/env python3
"""Summarize SQLite medium/stress seed stability."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
APP_DIR = RESULTS / "gem5_arm_ubuntu_fs_sqlite_app"
OUT = RESULTS / "SQLITE_MEDIUM_STRESS_SEED_STABILITY_20260619.md"

POINTS = [
    ("medium", "app_medium", APP_DIR / "sqlite_app_medium_summary.csv"),
    ("medium", "app_medium_seed1", APP_DIR / "sqlite_app_medium_seed1_summary.csv"),
    ("medium", "app_medium_seed2", APP_DIR / "sqlite_app_medium_seed2_summary.csv"),
    ("stress", "app_stress", APP_DIR / "sqlite_app_stress_summary.csv"),
    ("stress", "app_stress_seed1", APP_DIR / "sqlite_app_stress_seed1_summary.csv"),
]
KEY_POLICIES = ("none", "naive", "copper_clpd64k_peb", "spp", "spp_copper_slack")


def read_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        rows = {row["policy"]: row for row in csv.DictReader(fh)}
    missing = [policy for policy in KEY_POLICIES if policy not in rows]
    if missing:
        raise RuntimeError(f"{path} missing policies: {', '.join(missing)}")
    return rows


def pct_reduction(new: int, old: int) -> float:
    return 100.0 * (1.0 - new / old) if old else 0.0


def f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def i(row: dict[str, str], key: str) -> int:
    return int(float(row[key]))


def seed_from_tag(tag: str, rows: dict[str, dict[str, str]]) -> str:
    if rows["none"].get("seed"):
        return rows["none"]["seed"]
    match = re.search(r"_seed(\d+)$", tag)
    return match.group(1) if match else "base"


def summarize_point(scale: str, tag: str, rows: dict[str, dict[str, str]]) -> dict[str, object]:
    checksums = {rows[policy]["checksum"] for policy in KEY_POLICIES}
    rcs = {rows[policy]["rc"] for policy in KEY_POLICIES}
    naive_ctlw = i(rows["naive"], "targetLineWitnessMisses")
    copper_ctlw = i(rows["copper_clpd64k_peb"], "targetLineWitnessMisses")
    slack_ctlw = i(rows["spp_copper_slack"], "targetLineWitnessMisses")
    spp_delta = f(rows["spp"], "tick_delta_vs_none_pct")
    slack_delta = f(rows["spp_copper_slack"], "tick_delta_vs_none_pct")
    return {
        "scale": scale,
        "tag": tag,
        "seed": seed_from_tag(tag, rows),
        "checksum": next(iter(checksums)) if len(checksums) == 1 else "MISMATCH",
        "rc_ok": rcs == {"0"},
        "naive_ctlw": naive_ctlw,
        "copper_ctlw": copper_ctlw,
        "slack_ctlw": slack_ctlw,
        "copper_reduction": pct_reduction(copper_ctlw, naive_ctlw),
        "slack_reduction": pct_reduction(slack_ctlw, naive_ctlw),
        "copper_faults": i(rows["copper_clpd64k_peb"], "fillPrefetchTranslationFault"),
        "slack_faults": i(rows["spp_copper_slack"], "fillPrefetchTranslationFault"),
        "spp_delta": spp_delta,
        "slack_delta": slack_delta,
        "slack_gap": slack_delta - spp_delta,
    }


def format_range(values: list[float]) -> str:
    return f"{min(values):.1f}% to {max(values):.1f}%"


def main() -> None:
    summary = [summarize_point(scale, tag, read_rows(path)) for scale, tag, path in POINTS]
    status_ok = True
    for item in summary:
        status_ok = status_ok and item["checksum"] != "MISMATCH" and bool(item["rc_ok"])
        status_ok = status_ok and int(item["copper_faults"]) == 0 and int(item["slack_faults"]) == 0

    by_scale = {
        scale: [item for item in summary if item["scale"] == scale]
        for scale in sorted({str(item["scale"]) for item in summary})
    }
    all_copper = [float(item["copper_reduction"]) for item in summary]
    all_slack = [float(item["slack_reduction"]) for item in summary]
    worst_gap = max(abs(float(item["slack_gap"])) for item in summary)
    status = "PASS" if status_ok else "FAIL"

    lines = [
        "# SQLite Medium/Stress Seed Stability",
        "",
        "Date: 2026-06-19",
        "",
        "Scope: public SQLite amalgamation AArch64 full-system application workload, three medium seeds and two stress seeds, key policies only for repeated seeds. This is database-style external-validity evidence, not a production database-server campaign.",
        "",
        "| Scale | Tag | Seed | Naive CTLW | COPPER CTLW | COPPER reduction | Slack CTLW | Slack reduction | SPP delta | Slack delta | Slack gap vs SPP | COPPER faults | Slack faults | Checksum |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in summary:
        lines.append(
            f"| {item['scale']} | {item['tag']} | {item['seed']} | {item['naive_ctlw']} | "
            f"{item['copper_ctlw']} | {float(item['copper_reduction']):.1f}% | "
            f"{item['slack_ctlw']} | {float(item['slack_reduction']):.1f}% | "
            f"{float(item['spp_delta']):.3f}% | {float(item['slack_delta']):.3f}% | "
            f"{float(item['slack_gap']):+.3f} pp | {item['copper_faults']} | "
            f"{item['slack_faults']} | {item['checksum']} |"
        )

    lines.extend(["", "Aggregate:", ""])
    for scale, items in by_scale.items():
        copper = [float(item["copper_reduction"]) for item in items]
        slack = [float(item["slack_reduction"]) for item in items]
        gaps = [abs(float(item["slack_gap"])) for item in items]
        lines.append(
            f"- {scale.title()} points: {len(items)} seeds; COPPER CTLW reduction {format_range(copper)}; "
            f"SPP+COPPER slack CTLW reduction {format_range(slack)}; worst slack-vs-SPP gap {max(gaps):.3f} percentage points."
        )
    lines.extend(
        [
            f"- Across all {len(summary)} SQLite medium/stress seed points, COPPER CTLW reduction is at least {min(all_copper):.1f}%.",
            f"- Across all {len(summary)} SQLite medium/stress seed points, SPP+COPPER slack CTLW reduction is at least {min(all_slack):.1f}%.",
            f"- Worst absolute SPP+COPPER slack tick gap versus SPP is {worst_gap:.3f} percentage points.",
            "- COPPER and SPP+COPPER slack translation faults are zero across all SQLite seed points.",
            "- All key-policy runs preserve checksum agreement and `rc=0`.",
            "",
            f"status={status}",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
