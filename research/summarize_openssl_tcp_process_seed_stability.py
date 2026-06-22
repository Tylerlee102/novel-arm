#!/usr/bin/env python3
"""Summarize two-seed OpenSSL libssl process-server TCP-netns stability."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
APP_DIR = RESULTS / "gem5_arm_ubuntu_fs_ossltlstcp_app"
OUT = RESULTS / "OPENSSL_TCP_PROCESS_SEED_STABILITY_20260620.md"
CSV_OUT = RESULTS / "openssl_tcp_process_seed_stability_20260620.csv"

POINTS = (
    ("seed0", APP_DIR / "ossltlstcp_tcp_netns_process_key1_summary.csv"),
    ("seed1", APP_DIR / "ossltlstcp_tcp_netns_process_seed1_summary.csv"),
)


def read_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return {row["policy"]: row for row in csv.DictReader(fh)}


def pct_reduction(new: int, old: int) -> float:
    return 100.0 * (1.0 - (new / old)) if old else 0.0


def main() -> None:
    rows: list[dict[str, str]] = []
    for label, csv_path in POINTS:
        by = read_rows(csv_path)
        none = by["none"]
        naive = by["naive"]
        copper = by["copper_clpd64k_peb"]
        spp = by["spp"]
        slack = by["spp_copper_slack"]

        naive_ctlw = int(naive["targetLineWitnessMisses"])
        copper_ctlw = int(copper["targetLineWitnessMisses"])
        slack_ctlw = int(slack["targetLineWitnessMisses"])
        spp_delta = float(spp["tick_delta_vs_none_pct"])
        slack_delta = float(slack["tick_delta_vs_none_pct"])
        checksums = {row["checksum"] for row in by.values()}
        rcs = {row["rc"] for row in by.values()}
        transports = {row["transport"] for row in by.values()}

        rows.append(
            {
                "seed_label": label,
                "input_seed": none["seed"],
                "checksum": none["checksum"],
                "checksum_clean": "yes" if len(checksums) == 1 else "no",
                "rc_clean": "yes" if rcs == {"0"} else "no",
                "transports": ",".join(sorted(transports)),
                "process_pairs_total": str(
                    sum(int(row["process_pairs"]) for row in by.values())
                ),
                "child_failures_total": str(
                    sum(int(row["child_failures"]) for row in by.values())
                ),
                "naive_ctlw": str(naive_ctlw),
                "copper_ctlw": str(copper_ctlw),
                "slack_ctlw": str(slack_ctlw),
                "copper_reduction_pct": f"{pct_reduction(copper_ctlw, naive_ctlw):.3f}",
                "slack_reduction_pct": f"{pct_reduction(slack_ctlw, naive_ctlw):.3f}",
                "copper_faults": copper["fillPrefetchTranslationFault"],
                "slack_faults": slack["fillPrefetchTranslationFault"],
                "none_ticks": none["roi_ticks"],
                "copper_delta_pct": copper["tick_delta_vs_none_pct"],
                "spp_delta_pct": spp["tick_delta_vs_none_pct"],
                "slack_delta_pct": slack["tick_delta_vs_none_pct"],
                "slack_gap_vs_spp_pp": f"{slack_delta - spp_delta:.3f}",
            }
        )

    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    min_copper = min(float(row["copper_reduction_pct"]) for row in rows)
    min_slack = min(float(row["slack_reduction_pct"]) for row in rows)
    max_gap = max(abs(float(row["slack_gap_vs_spp_pp"])) for row in rows)
    total_faults = sum(
        int(row["copper_faults"]) + int(row["slack_faults"]) for row in rows
    )
    total_child_failures = sum(int(row["child_failures_total"]) for row in rows)
    total_process_pairs = sum(int(row["process_pairs_total"]) for row in rows)
    all_clean = all(
        row["checksum_clean"] == "yes"
        and row["rc_clean"] == "yes"
        and row["transports"] == "tcp_loopback_netns_process"
        for row in rows
    )
    distinct_checksums = len({row["checksum"] for row in rows})

    lines = [
        "# OpenSSL TCP Process-Server Seed Stability",
        "",
        "Date: 2026-06-20",
        "",
        "This artifact aggregates two deterministic seeds for the OpenSSL libssl",
        "process-separated TCP-netns workload. Each point runs a forked TLS server",
        "process and parent TLS client process over AF_INET loopback inside a",
        "private user/network namespace under AArch64 full-system gem5.",
        "It is stronger than in-process loopback evidence, but remains a bounded",
        "local server/client harness rather than a production TCP/TLS deployment.",
        "",
        "| Seed | Checksum | Naive CTLW | COPPER CTLW | COPPER reduction | SPP+COPPER CTLW | SPP+COPPER reduction | COPPER delta | SPP delta | Slack delta | Slack gap vs SPP | Process pairs | Child failures | Faults |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        faults = int(row["copper_faults"]) + int(row["slack_faults"])
        lines.append(
            f"| {row['input_seed']} | {row['checksum']} | "
            f"{row['naive_ctlw']} | {row['copper_ctlw']} | "
            f"{float(row['copper_reduction_pct']):.1f}% | "
            f"{row['slack_ctlw']} | {float(row['slack_reduction_pct']):.1f}% | "
            f"{row['copper_delta_pct']}% | {row['spp_delta_pct']}% | "
            f"{row['slack_delta_pct']}% | {row['slack_gap_vs_spp_pp']} pp | "
            f"{row['process_pairs_total']} | {row['child_failures_total']} | "
            f"{faults} |"
        )

    lines.extend(
        [
            "",
            "Aggregate interpretation:",
            "",
            f"- Process-server seed points: {len(rows)}.",
            f"- Distinct seed checksums: {distinct_checksums}.",
            f"- All rows used `tcp_loopback_netns_process`: {'yes' if all_clean else 'no'}.",
            f"- Total forked process TCP pairs across policies/seeds: {total_process_pairs}.",
            f"- Child process failures across policies/seeds: {total_child_failures}.",
            f"- Minimum COPPER CTLW reduction versus naive DMP: {min_copper:.1f}%.",
            f"- Minimum SPP+COPPER slack CTLW reduction versus naive DMP: {min_slack:.1f}%.",
            f"- Worst absolute SPP+COPPER slack tick gap versus SPP: {max_gap:.3f} percentage points.",
            f"- COPPER/slack translation faults across both seeds: {total_faults}.",
            "",
            "status=PASS"
            if all_clean and total_faults == 0 and total_child_failures == 0
            else "status=FAIL",
            "",
        ]
    )

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(CSV_OUT)
    print(OUT)


if __name__ == "__main__":
    main()
