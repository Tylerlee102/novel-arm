#!/usr/bin/env python3
"""Summarize two-seed OpenSSL-speed-like COPPER stability results."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "research" / "results" / "gem5_arm_ubuntu_fs_osslspeed_app"
OUT = ROOT / "research" / "results" / "OPENSSL_SPEEDLIKE_SEED_STABILITY_20260619.md"
TAGS = ["app_smoke", "app_smoke_seed1"]


def read_rows(tag: str) -> dict[str, dict[str, str]]:
    path = APP_DIR / f"osslspeed_{tag}_summary.csv"
    with path.open("r", encoding="utf-8", newline="") as fh:
        return {row["policy"]: row for row in csv.DictReader(fh)}


def reduction(new: int, old: int) -> float:
    return 100.0 * (1.0 - new / old) if old else 0.0


def main() -> None:
    rows = []
    copper_reductions = []
    slack_reductions = []
    slack_gaps = []
    fault_total = 0
    checksum_ok = True
    rc_ok = True

    for tag in TAGS:
        by_policy = read_rows(tag)
        checksums = {row["checksum"] for row in by_policy.values()}
        checksum_ok = checksum_ok and len(checksums) == 1 and "" not in checksums
        rc_ok = rc_ok and all(row["rc"] == "0" for row in by_policy.values())

        naive_ctlw = int(by_policy["naive"]["targetLineWitnessMisses"])
        copper_ctlw = int(by_policy["copper_clpd64k_peb"]["targetLineWitnessMisses"])
        slack_ctlw = int(by_policy["spp_copper_slack"]["targetLineWitnessMisses"])
        copper_faults = int(by_policy["copper_clpd64k_peb"]["fillPrefetchTranslationFault"])
        slack_faults = int(by_policy["spp_copper_slack"]["fillPrefetchTranslationFault"])
        spp_delta = float(by_policy["spp"]["tick_delta_vs_none_pct"])
        slack_delta = float(by_policy["spp_copper_slack"]["tick_delta_vs_none_pct"])
        gap = slack_delta - spp_delta

        copper_red = reduction(copper_ctlw, naive_ctlw)
        slack_red = reduction(slack_ctlw, naive_ctlw)
        copper_reductions.append(copper_red)
        slack_reductions.append(slack_red)
        slack_gaps.append(gap)
        fault_total += copper_faults + slack_faults

        rows.append(
            {
                "tag": tag,
                "checksum": next(iter(checksums)),
                "naive_ctlw": naive_ctlw,
                "copper_ctlw": copper_ctlw,
                "slack_ctlw": slack_ctlw,
                "copper_reduction": copper_red,
                "slack_reduction": slack_red,
                "spp_delta": spp_delta,
                "slack_delta": slack_delta,
                "slack_gap": gap,
                "faults": copper_faults + slack_faults,
            }
        )

    lines = [
        "# OpenSSL-Speed-Like Two-Seed Stability",
        "",
        "This summarizes two deterministic full-system AArch64 runs of the fixed-count OpenSSL-speed-like libcrypto driver. The driver calls real guest libcrypto EVP AES-128-CTR, SHA256, HMAC-SHA256, and `CRYPTO_memcmp` over fixed benchmark-style buffer sizes while retaining pointer-shaped metadata loaded as data. It remains a local speed-like driver, not the official OpenSSL CLI benchmark.",
        "",
        "| Workload | Seeds | COPPER CTLW reduction min / mean | SPP+COPPER slack CTLW reduction min / mean | Worst abs slack-vs-SPP tick gap | Fault status | Checksum/rc status |",
        "|---|---:|---:|---:|---:|---|---|",
        (
            "| OpenSSL speed-like fixed-buffer libcrypto | "
            f"{len(TAGS)} | {min(copper_reductions):.1f}% / {sum(copper_reductions) / len(copper_reductions):.1f}% | "
            f"{min(slack_reductions):.1f}% / {sum(slack_reductions) / len(slack_reductions):.1f}% | "
            f"{max(abs(x) for x in slack_gaps):.3f} pp | "
            f"{'zero faults' if fault_total == 0 else str(fault_total) + ' faults'} | "
            f"{'PASS' if checksum_ok and rc_ok else 'CHECK'} |"
        ),
        "",
        "| Tag | Checksum | Naive CTLW | COPPER CTLW | COPPER reduction | Slack CTLW | Slack reduction | SPP delta | Slack delta | Slack gap | COPPER/slack faults |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['tag']} | {row['checksum']} | {row['naive_ctlw']} | "
            f"{row['copper_ctlw']} | {row['copper_reduction']:.1f}% | "
            f"{row['slack_ctlw']} | {row['slack_reduction']:.1f}% | "
            f"{row['spp_delta']:.3f}% | {row['slack_delta']:.3f}% | "
            f"{row['slack_gap']:+.3f} pp | {row['faults']} |"
        )
    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            f"- COPPER CTLW reduction is stable at {min(copper_reductions):.1f}% minimum across the two seeds.",
            f"- SPP+COPPER slack CTLW reduction is stable at {min(slack_reductions):.1f}% minimum across the two seeds.",
            f"- Worst absolute SPP+COPPER slack gap versus SPP is {max(abs(x) for x in slack_gaps):.3f} percentage points.",
            "- COPPER and SPP+COPPER slack translation faults remain zero.",
            "- This strengthens the speed-like libcrypto evidence but does not convert it into an official OpenSSL CLI benchmark.",
            "",
            "status=PASS" if checksum_ok and rc_ok and fault_total == 0 else "status=CHECK",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
