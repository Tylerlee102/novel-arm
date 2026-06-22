#!/usr/bin/env python3
"""Summarize the OpenSSL TCP process-server seed/scale portfolio."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
APP_DIR = RESULTS / "gem5_arm_ubuntu_fs_ossltlstcp_app"
SOURCES = [
    ("seed0", APP_DIR / "ossltlstcp_tcp_netns_process_key1_summary.csv"),
    ("seed1", APP_DIR / "ossltlstcp_tcp_netns_process_seed1_summary.csv"),
    ("scale2", APP_DIR / "ossltlstcp_tcp_netns_process_scale2_summary.csv"),
    ("scale3", APP_DIR / "ossltlstcp_tcp_netns_process_scale3_summary.csv"),
]
OUT = RESULTS / "OPENSSL_TCP_PROCESS_SCALE_PORTFOLIO_20260620.md"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def ii(row: dict[str, str], key: str) -> int:
    return int(float(row.get(key, "0") or "0"))


def ff(row: dict[str, str], key: str) -> float:
    return float(row.get(key, "0") or "0")


def pct_reduction(new: int, old: int) -> float:
    return 100.0 * (1.0 - (new / old)) if old else 0.0


def main() -> None:
    portfolio: list[dict[str, str]] = []
    for label, source in SOURCES:
        rows = read_rows(source)
        by = {row["policy"]: row for row in rows}
        required = {"none", "naive", "copper_clpd64k_peb", "spp", "spp_copper_slack"}
        missing = sorted(required - set(by))
        if missing:
            raise SystemExit(f"{source} missing policies: {missing}")
        checksums = {row["checksum"] for row in rows}
        transports = {row["transport"] for row in rows}
        if len(checksums) != 1 or "" in checksums:
            raise SystemExit(f"{source} checksum disagreement: {checksums}")
        if transports != {"tcp_loopback_netns_process"}:
            raise SystemExit(f"{source} bad transports: {transports}")
        child_failures = sum(ii(row, "child_failures") for row in rows)
        faults = (
            ii(by["copper_clpd64k_peb"], "fillPrefetchTranslationFault")
            + ii(by["spp_copper_slack"], "fillPrefetchTranslationFault")
        )
        naive_ctlw = ii(by["naive"], "targetLineWitnessMisses")
        copper_ctlw = ii(by["copper_clpd64k_peb"], "targetLineWitnessMisses")
        slack_ctlw = ii(by["spp_copper_slack"], "targetLineWitnessMisses")
        spp_delta = ff(by["spp"], "tick_delta_vs_none_pct")
        slack_delta = ff(by["spp_copper_slack"], "tick_delta_vs_none_pct")
        portfolio.append(
            {
                "label": label,
                "checksum": next(iter(checksums)),
                "sessions": by["none"]["sessions"],
                "handshakes": by["none"]["handshakes"],
                "records": by["none"]["records"],
                "scan_depth": by["none"]["scan_depth"],
                "process_pairs_total": str(sum(ii(row, "process_pairs") for row in rows)),
                "child_failures": str(child_failures),
                "naive_ctlw": str(naive_ctlw),
                "copper_ctlw": str(copper_ctlw),
                "copper_reduction": f"{pct_reduction(copper_ctlw, naive_ctlw):.1f}",
                "slack_ctlw": str(slack_ctlw),
                "slack_reduction": f"{pct_reduction(slack_ctlw, naive_ctlw):.1f}",
                "spp_delta": f"{spp_delta:.3f}",
                "slack_delta": f"{slack_delta:.3f}",
                "slack_gap": f"{slack_delta - spp_delta:.3f}",
                "faults": str(faults),
            }
        )

    total_pairs = sum(int(row["process_pairs_total"]) for row in portfolio)
    total_child_failures = sum(int(row["child_failures"]) for row in portfolio)
    total_faults = sum(int(row["faults"]) for row in portfolio)
    min_copper_reduction = min(float(row["copper_reduction"]) for row in portfolio)
    min_slack_reduction = min(float(row["slack_reduction"]) for row in portfolio)
    worst_slack_gap = max(abs(float(row["slack_gap"])) for row in portfolio)
    checksums = {row["checksum"] for row in portfolio}

    lines = [
        "# OpenSSL TCP Process-Server Scale Portfolio",
        "",
        "Date: 2026-06-20",
        "",
        "This artifact combines the two deterministic process-server seeds with scaled four-pair and eight-pair process-server points. Every point runs a forked TLS server process and parent TLS client process over AF_INET loopback inside a private user/network namespace under AArch64 full-system gem5. It is stronger than the original two one-pair seeds, but remains a bounded local server/client harness rather than a production TCP/TLS deployment.",
        "",
        "## Source Summaries",
        "",
    ]
    for _, source in SOURCES:
        lines.append(f"- `{source.relative_to(ROOT).as_posix()}`")
    lines.extend(
        [
            "",
            "## Portfolio Table",
            "",
            "| Point | Sessions | Handshakes | Records | Scan depth | Process pairs across policies | Checksum | Naive CTLW | COPPER CTLW | COPPER reduction | SPP+COPPER CTLW | SPP+COPPER reduction | SPP delta | Slack delta | Slack gap vs SPP | Child failures | COPPER/slack faults |",
            "|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in portfolio:
        lines.append(
            f"| {row['label']} | {row['sessions']} | {row['handshakes']} | "
            f"{row['records']} | {row['scan_depth']} | "
            f"{row['process_pairs_total']} | {row['checksum']} | "
            f"{row['naive_ctlw']} | {row['copper_ctlw']} | "
            f"{row['copper_reduction']}% | {row['slack_ctlw']} | "
            f"{row['slack_reduction']}% | {row['spp_delta']}% | "
            f"{row['slack_delta']}% | {row['slack_gap']} pp | "
            f"{row['child_failures']} | {row['faults']} |"
        )
    lines.extend(
        [
            "",
            "## Aggregate Interpretation",
            "",
            f"- Portfolio points: {len(portfolio)}.",
            f"- Distinct checksums: {len(checksums)}.",
            f"- Total forked process TCP pairs across policies/points: {total_pairs}.",
            f"- Child process failures across policies/points: {total_child_failures}.",
            f"- Minimum COPPER CTLW reduction versus naive DMP: {min_copper_reduction:.1f}%.",
            f"- Minimum SPP+COPPER slack CTLW reduction versus naive DMP: {min_slack_reduction:.1f}%.",
            f"- Worst absolute SPP+COPPER slack tick gap versus SPP: {worst_slack_gap:.3f} percentage points.",
            f"- COPPER/slack translation faults across portfolio: {total_faults}.",
            "",
            "status=PASS",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
