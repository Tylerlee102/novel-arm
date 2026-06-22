#!/usr/bin/env python3
"""Summarize two-seed JSON+SQLite stress service-composition stability."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
APP_DIR = RESULTS / "gem5_arm_ubuntu_fs_jsonsqlite_app"
OUT = RESULTS / "JSONSQLITE_STRESS_SEED_STABILITY_20260619.md"

POINTS = [
    ("app_stress", APP_DIR / "jsonsqlite_app_stress_summary.csv"),
    ("stress_seed1", APP_DIR / "jsonsqlite_stress_seed1_summary.csv"),
]
KEY_POLICIES = ["none", "naive", "copper_clpd64k_peb", "spp", "spp_copper_slack"]


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


def main() -> None:
    point_rows = [(tag, read_rows(path)) for tag, path in POINTS]
    summary: list[dict[str, object]] = []
    all_status_ok = True
    for tag, rows in point_rows:
        checksums = {rows[policy]["checksum"] for policy in KEY_POLICIES}
        rcs = {rows[policy]["rc"] for policy in KEY_POLICIES}
        naive_ctlw = i(rows["naive"], "targetLineWitnessMisses")
        copper_ctlw = i(rows["copper_clpd64k_peb"], "targetLineWitnessMisses")
        slack_ctlw = i(rows["spp_copper_slack"], "targetLineWitnessMisses")
        copper_faults = i(rows["copper_clpd64k_peb"], "fillPrefetchTranslationFault")
        slack_faults = i(rows["spp_copper_slack"], "fillPrefetchTranslationFault")
        spp_delta = f(rows["spp"], "tick_delta_vs_none_pct")
        slack_delta = f(rows["spp_copper_slack"], "tick_delta_vs_none_pct")
        item = {
            "tag": tag,
            "seed": rows["none"]["seed"],
            "checksum": next(iter(checksums)) if len(checksums) == 1 else "MISMATCH",
            "rc_ok": rcs == {"0"},
            "naive_ctlw": naive_ctlw,
            "copper_ctlw": copper_ctlw,
            "slack_ctlw": slack_ctlw,
            "copper_reduction": pct_reduction(copper_ctlw, naive_ctlw),
            "slack_reduction": pct_reduction(slack_ctlw, naive_ctlw),
            "copper_faults": copper_faults,
            "slack_faults": slack_faults,
            "spp_delta": spp_delta,
            "slack_delta": slack_delta,
            "slack_gap": slack_delta - spp_delta,
        }
        all_status_ok = all_status_ok and item["checksum"] != "MISMATCH" and item["rc_ok"]
        all_status_ok = all_status_ok and copper_faults == 0 and slack_faults == 0
        summary.append(item)

    min_copper = min(float(item["copper_reduction"]) for item in summary)
    min_slack = min(float(item["slack_reduction"]) for item in summary)
    worst_gap = max(abs(float(item["slack_gap"])) for item in summary)
    status = "PASS" if all_status_ok else "FAIL"

    lines = [
        "# JSON+SQLite Stress Two-Seed Stability",
        "",
        "Date: 2026-06-19",
        "",
        "Scope: composed public yyjson plus SQLite AArch64 full-system workload, stress scale, key policies only for the new second seed. This is a service-composition stability check, not SPEC or a production database server.",
        "",
        "| Tag | Seed | Naive CTLW | COPPER CTLW | COPPER reduction | Slack CTLW | Slack reduction | SPP delta | Slack delta | Slack gap vs SPP | COPPER faults | Slack faults | Checksum |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in summary:
        lines.append(
            f"| {item['tag']} | {item['seed']} | {item['naive_ctlw']} | "
            f"{item['copper_ctlw']} | {float(item['copper_reduction']):.1f}% | "
            f"{item['slack_ctlw']} | {float(item['slack_reduction']):.1f}% | "
            f"{float(item['spp_delta']):.3f}% | {float(item['slack_delta']):.3f}% | "
            f"{float(item['slack_gap']):+.3f} pp | {item['copper_faults']} | "
            f"{item['slack_faults']} | {item['checksum']} |"
        )
    lines.extend(
        [
            "",
            "Aggregate:",
            "",
            f"- Points: {len(summary)} stress JSON+SQLite seeds.",
            f"- COPPER CTLW reduction is at least {min_copper:.1f}% across the two stress seeds.",
            f"- SPP+COPPER slack CTLW reduction is at least {min_slack:.1f}% across the two stress seeds.",
            f"- Worst absolute SPP+COPPER slack tick gap versus SPP is {worst_gap:.3f} percentage points.",
            "- COPPER and SPP+COPPER slack translation faults are zero across both stress seeds.",
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
