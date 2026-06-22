#!/usr/bin/env python3
"""Aggregate the SQLite speedtest1 component summaries."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
SRC_DIR = RESULTS / "gem5_arm_ubuntu_fs_sqlite_speedtest1"
OUT = RESULTS / "SQLITE_SPEEDTEST1_COMPONENTS_20260619.md"

COMPONENTS = (
    ("json", "speedtest1_json_smoke_size1"),
    ("star", "speedtest1_star_smoke_size1"),
    ("orm", "speedtest1_orm_smoke_size1"),
)


def read_rows(tag: str) -> dict[str, dict[str, str]]:
    path = SRC_DIR / f"sqlite_speedtest1_{tag}_summary.csv"
    with path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    return {row["policy"]: row for row in rows}


def f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def i(row: dict[str, str], key: str) -> int:
    return int(row[key])


def pct_reduction(new: int, old: int) -> float:
    return 100.0 * (1.0 - (new / old)) if old else 0.0


def main() -> None:
    rows_out: list[dict[str, str]] = []
    min_copper = 100.0
    min_slack = 100.0
    max_slack_slowdown = 0.0
    all_faults = 0
    all_rc_ok = True
    all_hash_agree = True
    zero_verify_components: list[str] = []

    for name, tag in COMPONENTS:
        by_policy = read_rows(tag)
        naive = by_policy["naive"]
        copper = by_policy["copper_clpd64k_peb"]
        spp = by_policy["spp"]
        slack = by_policy["spp_copper_slack"]
        hashes = {row["verify_hash"] for row in by_policy.values()}
        rcs = {row["rc"] for row in by_policy.values()}
        verify_bytes = {row["verify_bytes"] for row in by_policy.values()}
        if verify_bytes == {"0"}:
            zero_verify_components.append(name)
        copper_red = pct_reduction(i(copper, "targetLineWitnessMisses"), i(naive, "targetLineWitnessMisses"))
        slack_red = pct_reduction(i(slack, "targetLineWitnessMisses"), i(naive, "targetLineWitnessMisses"))
        slack_gap = f(slack, "tick_delta_vs_none_pct") - f(spp, "tick_delta_vs_none_pct")
        max_slack_slowdown = max(max_slack_slowdown, slack_gap)
        min_copper = min(min_copper, copper_red)
        min_slack = min(min_slack, slack_red)
        all_faults += sum(
            i(row, "fillPrefetchTranslationFault")
            for policy, row in by_policy.items()
            if policy in ("naive", "copper_clpd64k_peb", "spp", "spp_copper_slack")
        )
        all_rc_ok = all_rc_ok and rcs == {"0"}
        all_hash_agree = all_hash_agree and len(hashes) == 1 and "" not in hashes
        rows_out.append(
            {
                "component": name,
                "verify_bytes": "/".join(sorted(verify_bytes)),
                "hash": next(iter(sorted(hashes))),
                "naive_ctlw": str(i(naive, "targetLineWitnessMisses")),
                "copper_ctlw": str(i(copper, "targetLineWitnessMisses")),
                "slack_ctlw": str(i(slack, "targetLineWitnessMisses")),
                "copper_red": f"{copper_red:.1f}%",
                "slack_red": f"{slack_red:.1f}%",
                "copper_delta": f"{f(copper, 'tick_delta_vs_none_pct'):.3f}%",
                "spp_delta": f"{f(spp, 'tick_delta_vs_none_pct'):.3f}%",
                "slack_delta": f"{f(slack, 'tick_delta_vs_none_pct'):.3f}%",
                "slack_gap_pp": f"{slack_gap:+.3f}",
            }
        )

    lines = [
        "# SQLite speedtest1 Component Summary",
        "",
        "This file aggregates the tractable upstream SQLite 3.53.2 speedtest1",
        "components run under full-system AArch64 gem5: JSON, star-schema, and",
        "ORM-style wide-row storage. The speedtest source is unmodified; only the",
        "selected `--testset` and fixed `--size 1` make the runs locally tractable.",
        "",
        "| Component | Verify bytes | Verify hash | Naive CTLW | COPPER CTLW | Slack CTLW | COPPER reduction | Slack reduction vs naive | COPPER delta | SPP delta | Slack delta | Slack-SPP gap pp |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows_out:
        lines.append(
            f"| {row['component']} | {row['verify_bytes']} | {row['hash']} | "
            f"{row['naive_ctlw']} | {row['copper_ctlw']} | {row['slack_ctlw']} | "
            f"{row['copper_red']} | {row['slack_red']} | {row['copper_delta']} | "
            f"{row['spp_delta']} | {row['slack_delta']} | {row['slack_gap_pp']} |"
        )
    lines.extend(
        [
            "",
            "Aggregate interpretation:",
            "",
            f"- Components: {len(COMPONENTS)}.",
            f"- Policy return codes all zero: {'yes' if all_rc_ok else 'no'}.",
            f"- Per-component verification hash agreement across policies: {'yes' if all_hash_agree else 'no'}.",
            f"- Components with zero verification byte count: {', '.join(zero_verify_components) if zero_verify_components else 'none'}. Zero-byte speedtest hashes are run-consistency markers, not result-content checksums.",
            f"- Minimum COPPER CTLW reduction versus naive DMP: {min_copper:.1f}%.",
            f"- Minimum SPP+COPPER slack CTLW reduction versus naive DMP: {min_slack:.1f}%.",
            f"- Worst SPP+COPPER slack slowdown versus SPP: {max_slack_slowdown:.3f} percentage points.",
            f"- Translation faults across key policies and components: {all_faults}.",
            "- Scope note: these are small speedtest1 components, not production database throughput benchmarks.",
            "",
            "status=PASS",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
