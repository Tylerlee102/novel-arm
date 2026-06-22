#!/usr/bin/env python3
"""Aggregate medium public-engine seed sweeps for SQLite, Lua, and Duktape."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from summarize_duktape_object_app_fs import summarize as summarize_duktape
from summarize_lua_table_app_fs import summarize as summarize_lua
from summarize_sqlite_pointer_app_fs import summarize as summarize_sqlite


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "results"
POLICIES = [
    "none",
    "naive",
    "copper_clpd64k_peb",
    "spp",
    "spp_copper_slack",
]
ENGINES = {
    "SQLite": summarize_sqlite,
    "Lua": summarize_lua,
    "Duktape": summarize_duktape,
}
SEEDS = [
    (0, "app_medium"),
    (1, "app_medium_seed1"),
    (2, "app_medium_seed2"),
]


def as_int(row: dict[str, str], key: str) -> int:
    value = row.get(key, "")
    return int(value) if value else 0


def as_float(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    return float(value) if value else 0.0


def pct_reduction(new: int, old: int) -> float:
    return 100.0 * (1.0 - (new / old)) if old else 0.0


def main() -> None:
    all_rows: list[dict[str, str]] = []
    for engine, summarizer in ENGINES.items():
        for seed, tag in SEEDS:
            rows = summarizer(tag, POLICIES)
            for row in rows:
                row["engine"] = engine
                row["seed"] = str(seed)
                row["tag"] = tag
            all_rows.extend(rows)

    checksum_ok = True
    rc_ok = True
    faults_total = 0
    max_slack_gap_pp = 0.0
    copper_beats_naive = 0
    points = 0
    by_engine_policy: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in all_rows:
        by_engine_policy[(row["engine"], row["policy"])].append(row)

    by_point: dict[tuple[str, str], dict[str, dict[str, str]]] = defaultdict(dict)
    for row in all_rows:
        by_point[(row["engine"], row["seed"])][row["policy"]] = row
        faults_total += as_int(row, "fillPrefetchTranslationFault")

    point_lines: list[str] = []
    for engine in ENGINES:
        for seed, _tag in SEEDS:
            point = by_point[(engine, str(seed))]
            checksums = {row["checksum"] for row in point.values()}
            checksum_ok = checksum_ok and len(checksums) == 1 and "" not in checksums
            rc_ok = rc_ok and all(row["rc"] == "0" for row in point.values())
            gap = abs(
                as_float(point["spp_copper_slack"], "tick_delta_vs_none_pct")
                - as_float(point["spp"], "tick_delta_vs_none_pct")
            )
            max_slack_gap_pp = max(max_slack_gap_pp, gap)
            if (
                as_float(point["copper_clpd64k_peb"], "tick_delta_vs_none_pct")
                < as_float(point["naive"], "tick_delta_vs_none_pct")
            ):
                copper_beats_naive += 1
            points += 1
            point_lines.append(
                f"| {engine} | {seed} | {point['none']['checksum']} | "
                f"{point['naive']['tick_delta_vs_none_pct']}% | "
                f"{point['copper_clpd64k_peb']['tick_delta_vs_none_pct']}% | "
                f"{point['spp']['tick_delta_vs_none_pct']}% | "
                f"{point['spp_copper_slack']['tick_delta_vs_none_pct']}% | "
                f"{gap:.3f} | {point['naive']['targetLineWitnessMisses']} | "
                f"{point['copper_clpd64k_peb']['targetLineWitnessMisses']} | "
                f"{point['spp_copper_slack']['targetLineWitnessMisses']} |"
            )

    aggregate_lines: list[str] = []
    overall_naive_ctlw = 0
    overall_copper_ctlw = 0
    overall_slack_ctlw = 0
    for engine in ENGINES:
        naive_rows = by_engine_policy[(engine, "naive")]
        copper_rows = by_engine_policy[(engine, "copper_clpd64k_peb")]
        spp_rows = by_engine_policy[(engine, "spp")]
        slack_rows = by_engine_policy[(engine, "spp_copper_slack")]
        naive_ctlw = sum(as_int(row, "targetLineWitnessMisses") for row in naive_rows)
        copper_ctlw = sum(as_int(row, "targetLineWitnessMisses") for row in copper_rows)
        slack_ctlw = sum(as_int(row, "targetLineWitnessMisses") for row in slack_rows)
        overall_naive_ctlw += naive_ctlw
        overall_copper_ctlw += copper_ctlw
        overall_slack_ctlw += slack_ctlw
        spp_mean = sum(as_float(row, "tick_delta_vs_none_pct") for row in spp_rows) / len(spp_rows)
        slack_mean = sum(as_float(row, "tick_delta_vs_none_pct") for row in slack_rows) / len(slack_rows)
        copper_mean = sum(as_float(row, "tick_delta_vs_none_pct") for row in copper_rows) / len(copper_rows)
        aggregate_lines.append(
            f"| {engine} | {copper_mean:.3f}% | {spp_mean:.3f}% | "
            f"{slack_mean:.3f}% | {naive_ctlw} | {copper_ctlw} | "
            f"{pct_reduction(copper_ctlw, naive_ctlw):.3f}% | {slack_ctlw} | "
            f"{pct_reduction(slack_ctlw, naive_ctlw):.3f}% |"
        )

    status = (
        "PASS"
        if checksum_ok and rc_ok and faults_total == 0 and max_slack_gap_pp <= 1.0
        else "REVIEW"
    )
    lines = [
        "# Public AArch64 Full-System Medium App Seed Sweep",
        "",
        "Date: 2026-06-17",
        "",
        "This artifact aggregates three public-engine medium workloads across three",
        "layout seeds: SQLite, Lua, and Duktape. Seed 0 is the existing app-medium",
        "run for each engine; seeds 1 and 2 use explicit workload seed arguments.",
        "The policy subset is `none`, `naive`, `copper_clpd64k_peb`, `spp`, and",
        "`spp_copper_slack`, chosen to test safety/performance coexistence after the",
        "full conventional baseline matrix already established SPP as the best",
        "ordinary address-stream baseline on the six medium/stress app points.",
        "",
        "| Engine | Seed | Checksum | Naive delta | COPPER delta | SPP delta | SPP+COPPER slack delta | Slack-SPP gap pp | Naive CTLW | COPPER CTLW | Slack CTLW |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        *point_lines,
        "",
        "Aggregate by engine:",
        "",
        "| Engine | Mean COPPER delta | Mean SPP delta | Mean SPP+COPPER slack delta | Naive CTLW | COPPER CTLW | COPPER CTLW reduction | Slack CTLW | Slack CTLW reduction |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        *aggregate_lines,
        "",
        "Overall:",
        "",
        f"- Correctness: checksum agreement per engine/seed = {'yes' if checksum_ok else 'no'}; `rc=0` for all rows = {'yes' if rc_ok else 'no'}.",
        f"- Translation faults across all rows: {faults_total}.",
        f"- Standalone COPPER beats unsafe naive DMP on {copper_beats_naive}/{points} engine-seed points.",
        f"- Overall COPPER CTLW reduction versus naive DMP: {pct_reduction(overall_copper_ctlw, overall_naive_ctlw):.3f}%.",
        f"- Overall SPP+COPPER slack CTLW reduction versus naive DMP: {pct_reduction(overall_slack_ctlw, overall_naive_ctlw):.3f}%.",
        f"- Worst absolute SPP+COPPER slack gap versus SPP: {max_slack_gap_pp:.3f} percentage points.",
        "- This is a broader repeated public-engine campaign than the Lua-only sweep, but it is still not SPEC-scale or production-service evidence.",
        "",
        f"status={status}",
        "",
    ]
    out = OUT / "COPPER_PUBLIC_APP_MEDIUM_SEED_SWEEP_20260617.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
