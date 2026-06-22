#!/usr/bin/env python3
"""Aggregate PCRE2 regex seed-stability summaries for COPPER."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
APP_DIR = RESULTS / "gem5_arm_ubuntu_fs_pcre2_app"
OUT = RESULTS / "PCRE2_REGEX_SEED_STABILITY_20260620.md"
CSV_OUT = RESULTS / "pcre2_regex_seed_stability_20260620.csv"
KEY_POLICIES = ("none", "naive", "copper_clpd64k_peb", "spp", "spp_copper_slack")


@dataclass(frozen=True)
class Point:
    label: str
    csv_path: Path


POINTS = (
    Point("seed0", APP_DIR / "pcre2_pcre2_smoke_summary.csv"),
    Point("seed1", APP_DIR / "pcre2_pcre2_seed1_summary.csv"),
)


def read_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        rows = {row["policy"]: row for row in csv.DictReader(fh)}
    missing = [policy for policy in KEY_POLICIES if policy not in rows]
    if missing:
        raise RuntimeError(f"{path} missing policies: {', '.join(missing)}")
    return rows


def pct_reduction(new: int, old: int) -> float:
    return 100.0 * (1.0 - new / old) if old else 0.0


def i(row: dict[str, str], key: str) -> int:
    return int(float(row[key]))


def f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def main() -> None:
    out_rows: list[dict[str, str]] = []
    status_ok = True

    for point in POINTS:
        rows = read_rows(point.csv_path)
        checksums = {rows[policy]["checksum"] for policy in KEY_POLICIES}
        rcs = {rows[policy]["rc"] for policy in KEY_POLICIES}
        naive = rows["naive"]
        copper = rows["copper_clpd64k_peb"]
        spp = rows["spp"]
        slack = rows["spp_copper_slack"]
        naive_ctlw = i(naive, "targetLineWitnessMisses")
        copper_ctlw = i(copper, "targetLineWitnessMisses")
        slack_ctlw = i(slack, "targetLineWitnessMisses")
        spp_delta = f(spp, "tick_delta_vs_none_pct")
        slack_delta = f(slack, "tick_delta_vs_none_pct")
        checksum = next(iter(checksums)) if len(checksums) == 1 else "MISMATCH"
        row = {
            "seed_label": point.label,
            "input_seed": rows["none"].get("seed", ""),
            "checksum": checksum,
            "rc_ok": "yes" if rcs == {"0"} else "no",
            "naive_ctlw": str(naive_ctlw),
            "copper_ctlw": str(copper_ctlw),
            "slack_ctlw": str(slack_ctlw),
            "copper_ctlw_reduction_pct": f"{pct_reduction(copper_ctlw, naive_ctlw):.3f}",
            "slack_ctlw_reduction_pct": f"{pct_reduction(slack_ctlw, naive_ctlw):.3f}",
            "copper_faults": copper["fillPrefetchTranslationFault"],
            "slack_faults": slack["fillPrefetchTranslationFault"],
            "spp_delta_pct": spp["tick_delta_vs_none_pct"],
            "slack_delta_pct": slack["tick_delta_vs_none_pct"],
            "slack_gap_vs_spp_points": f"{slack_delta - spp_delta:.3f}",
            "records": rows["none"].get("records", ""),
            "lookups": rows["none"].get("lookups", ""),
            "scan_depth": rows["none"].get("scan_depth", ""),
            "rounds": rows["none"].get("rounds", ""),
            "matches": rows["none"].get("matches", ""),
        }
        status_ok = status_ok and checksum != "MISMATCH" and rcs == {"0"}
        status_ok = (
            status_ok
            and int(row["copper_faults"]) == 0
            and int(row["slack_faults"]) == 0
        )
        out_rows.append(row)

    with CSV_OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)

    min_copper = min(float(row["copper_ctlw_reduction_pct"]) for row in out_rows)
    min_slack = min(float(row["slack_ctlw_reduction_pct"]) for row in out_rows)
    max_abs_gap = max(abs(float(row["slack_gap_vs_spp_points"])) for row in out_rows)
    fault_total = sum(
        int(row["copper_faults"]) + int(row["slack_faults"]) for row in out_rows
    )
    distinct_checksums = len({row["checksum"] for row in out_rows})
    status = "PASS" if status_ok else "FAIL"

    lines = [
        "# PCRE2 Regex Seed Stability",
        "",
        "Date: 2026-06-20",
        "",
        "Scope: public PCRE2 8-bit regex compiler/matcher AArch64 full-system",
        "workload, two deterministic input seeds, key policies only for the",
        "new repeated seed. This is parser/matcher-library external-validity",
        "evidence, not production log-processing service evidence.",
        "",
        "| Seed label | Input seed | Checksum | Naive CTLW | COPPER CTLW | COPPER reduction | Slack CTLW | Slack reduction | SPP delta | Slack delta | Slack gap vs SPP | COPPER faults | Slack faults |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in out_rows:
        lines.append(
            f"| {row['seed_label']} | {row['input_seed']} | {row['checksum']} | "
            f"{row['naive_ctlw']} | {row['copper_ctlw']} | "
            f"{float(row['copper_ctlw_reduction_pct']):.1f}% | "
            f"{row['slack_ctlw']} | {float(row['slack_ctlw_reduction_pct']):.1f}% | "
            f"{float(row['spp_delta_pct']):.3f}% | "
            f"{float(row['slack_delta_pct']):.3f}% | "
            f"{float(row['slack_gap_vs_spp_points']):+.3f} pp | "
            f"{row['copper_faults']} | {row['slack_faults']} |"
        )

    lines.extend(
        [
            "",
            "Aggregate interpretation:",
            "",
            f"- PCRE2 seed points: {len(out_rows)}.",
            f"- Distinct per-seed checksums: {distinct_checksums}.",
            "- All key-policy runs preserve checksum agreement and `rc=0` within each seed.",
            f"- Minimum COPPER CTLW reduction versus naive DMP: {min_copper:.1f}%.",
            f"- Minimum SPP+COPPER slack CTLW reduction versus naive DMP: {min_slack:.1f}%.",
            f"- Worst absolute SPP+COPPER slack tick gap versus SPP: {max_abs_gap:.3f} percentage points.",
            f"- COPPER/slack translation faults across both seed points: {fault_total}.",
            "- This strengthens public parser/matcher breadth and seed stability, but does not replace production log-processing or browser-scale evaluation.",
            "",
            f"status={status}",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(CSV_OUT)
    print(OUT)
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
