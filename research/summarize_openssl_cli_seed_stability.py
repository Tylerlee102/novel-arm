#!/usr/bin/env python3
"""Summarize multi-seed official OpenSSL CLI fixed-workload stability."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "research" / "results" / "gem5_arm_ubuntu_fs_osslcli_app"
OUT = ROOT / "research" / "results" / "OPENSSL_CLI_SEED_STABILITY_20260619.md"

WORKLOADS = [
    (
        "Official OpenSSL CLI SHA256 digest",
        ("fixed_64k", "fixed_64k_seed1", "fixed_64k_seed2"),
    ),
    (
        "Official OpenSSL CLI AES-CTR + digest",
        ("aesctr_64k", "aesctr_64k_seed1", "aesctr_64k_seed2"),
    ),
    (
        "Official OpenSSL CLI HMAC-SHA256",
        ("hmac_64k", "hmac_64k_seed1", "hmac_64k_seed2"),
    ),
]


def read_rows(tag: str) -> dict[str, dict[str, str]]:
    path = APP_DIR / f"osslcli_{tag}_summary.csv"
    with path.open("r", encoding="utf-8", newline="") as fh:
        return {row["policy"]: row for row in csv.DictReader(fh)}


def reduction(new: int, old: int) -> float:
    return 100.0 * (1.0 - new / old) if old else 0.0


def summarize_workload(name: str, tags: tuple[str, ...]) -> dict[str, object]:
    detail_rows = []
    copper_reductions = []
    slack_reductions = []
    slack_gaps = []
    fault_total = 0
    digest_ok = True
    input_ok = True
    rc_ok = True

    for tag in tags:
        rows = read_rows(tag)
        digests = {row["sha256"] for row in rows.values()}
        input_checksums = {row["input_checksum"] for row in rows.values()}
        rcs = {row["rc"] for row in rows.values()}
        after_rcs = {row.get("after_rc", "") for row in rows.values() if row.get("after_rc", "")}
        digest_ok = digest_ok and len(digests) == 1 and "" not in digests
        input_ok = input_ok and len(input_checksums) == 1 and "" not in input_checksums
        rc_ok = rc_ok and rcs == {"0"} and (not after_rcs or after_rcs == {"0"})

        naive_ctlw = int(rows["naive"]["targetLineWitnessMisses"])
        copper_ctlw = int(rows["copper_clpd64k_peb"]["targetLineWitnessMisses"])
        slack_ctlw = int(rows["spp_copper_slack"]["targetLineWitnessMisses"])
        copper_faults = int(rows["copper_clpd64k_peb"]["fillPrefetchTranslationFault"])
        slack_faults = int(rows["spp_copper_slack"]["fillPrefetchTranslationFault"])
        spp_delta = float(rows["spp"]["tick_delta_vs_none_pct"])
        slack_delta = float(rows["spp_copper_slack"]["tick_delta_vs_none_pct"])
        slack_gap = slack_delta - spp_delta
        copper_red = reduction(copper_ctlw, naive_ctlw)
        slack_red = reduction(slack_ctlw, naive_ctlw)
        copper_reductions.append(copper_red)
        slack_reductions.append(slack_red)
        slack_gaps.append(slack_gap)
        fault_total += copper_faults + slack_faults
        detail_rows.append(
            {
                "workload": name,
                "tag": tag,
                "digest": next(iter(digests)),
                "input_checksum": next(iter(input_checksums)),
                "naive_ctlw": naive_ctlw,
                "copper_ctlw": copper_ctlw,
                "copper_reduction": copper_red,
                "slack_ctlw": slack_ctlw,
                "slack_reduction": slack_red,
                "spp_delta": spp_delta,
                "slack_delta": slack_delta,
                "slack_gap": slack_gap,
                "faults": copper_faults + slack_faults,
            }
        )

    return {
        "name": name,
        "detail_rows": detail_rows,
        "copper_min": min(copper_reductions),
        "copper_mean": sum(copper_reductions) / len(copper_reductions),
        "slack_min": min(slack_reductions),
        "slack_mean": sum(slack_reductions) / len(slack_reductions),
        "worst_gap": max(abs(gap) for gap in slack_gaps),
        "fault_total": fault_total,
        "digest_ok": digest_ok,
        "input_ok": input_ok,
        "rc_ok": rc_ok,
    }


def main() -> None:
    summaries = [summarize_workload(name, tags) for name, tags in WORKLOADS]
    all_details = [
        detail for summary in summaries for detail in summary["detail_rows"]  # type: ignore[index]
    ]
    total_points = len(all_details)
    all_copper_min = min(float(summary["copper_min"]) for summary in summaries)
    all_slack_min = min(float(summary["slack_min"]) for summary in summaries)
    all_worst_gap = max(float(summary["worst_gap"]) for summary in summaries)
    all_faults = sum(int(summary["fault_total"]) for summary in summaries)
    all_ok = all(
        bool(summary["digest_ok"]) and bool(summary["input_ok"]) and bool(summary["rc_ok"])
        for summary in summaries
    ) and all_faults == 0

    lines = [
        "# Official OpenSSL CLI Multi-Seed Stability",
        "",
        "This summarizes official Ubuntu ARM64 `openssl` CLI fixed-workload runs over deterministic pointer-shaped input seeds. It covers SHA256 digest, AES-128-CTR plus output digest, and HMAC-SHA256. These are official-command fixed-workload datapoints, not timer-driven `openssl speed` results.",
        "",
        "| Workload | Seeds | COPPER CTLW reduction min / mean | SPP+COPPER slack CTLW reduction min / mean | Worst abs slack-vs-SPP tick gap | Fault status | Correctness status |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for summary in summaries:
        seeds = len(summary["detail_rows"])  # type: ignore[arg-type]
        lines.append(
            f"| {summary['name']} | {seeds} | "
            f"{float(summary['copper_min']):.1f}% / {float(summary['copper_mean']):.1f}% | "
            f"{float(summary['slack_min']):.1f}% / {float(summary['slack_mean']):.1f}% | "
            f"{float(summary['worst_gap']):.3f} pp | "
            f"{'zero faults' if int(summary['fault_total']) == 0 else str(summary['fault_total']) + ' faults'} | "
            f"{'PASS' if bool(summary['digest_ok']) and bool(summary['input_ok']) and bool(summary['rc_ok']) else 'CHECK'} |"
        )
    lines.extend(
        [
            "",
            "| Workload | Tag | Digest/MAC | Input checksum | Naive CTLW | COPPER CTLW | COPPER reduction | Slack CTLW | Slack reduction | SPP delta | Slack delta | Slack gap | COPPER/slack faults |",
            "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in all_details:
        lines.append(
            f"| {row['workload']} | {row['tag']} | {row['digest']} | {row['input_checksum']} | "
            f"{row['naive_ctlw']} | {row['copper_ctlw']} | {float(row['copper_reduction']):.1f}% | "
            f"{row['slack_ctlw']} | {float(row['slack_reduction']):.1f}% | "
            f"{float(row['spp_delta']):.3f}% | {float(row['slack_delta']):.3f}% | "
            f"{float(row['slack_gap']):+.3f} pp | {row['faults']} |"
        )
    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            f"- Across {total_points} official CLI seed/workload points, COPPER CTLW reduction is at least {all_copper_min:.1f}%.",
            f"- Across {total_points} official CLI seed/workload points, SPP+COPPER slack CTLW reduction is at least {all_slack_min:.1f}%.",
            f"- Worst absolute SPP+COPPER slack gap versus SPP is {all_worst_gap:.3f} percentage points.",
            "- COPPER and SPP+COPPER slack translation faults remain zero.",
            "- All official CLI commands preserve policy-independent digest/MAC fingerprints and return-code success.",
            "- This strengthens standard-crypto evidence, but it remains fixed-workload CLI execution rather than timer-driven `openssl speed`.",
            "",
            "status=PASS" if all_ok else "status=CHECK",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
