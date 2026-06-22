#!/usr/bin/env python3
"""Aggregate all repeated public-engine medium/stress seed evidence."""

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
SCALES = [
    ("medium", [(0, "app_medium"), (1, "app_medium_seed1"), (2, "app_medium_seed2")]),
    ("stress", [(0, "app_stress"), (1, "app_stress_seed1")]),
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
    missing: list[str] = []
    for scale, seeds in SCALES:
        for engine, summarizer in ENGINES.items():
            for seed, tag in seeds:
                try:
                    rows = summarizer(tag, POLICIES)
                except Exception as exc:
                    missing.append(f"{scale} {engine} seed={seed} tag={tag}: {exc}")
                    continue
                for row in rows:
                    row["scale"] = scale
                    row["engine"] = engine
                    row["seed"] = str(seed)
                    row["tag"] = tag
                all_rows.extend(rows)
    if missing:
        raise RuntimeError("missing repeated public-app seed data:\n" + "\n".join(missing))

    checksum_ok = True
    rc_ok = True
    faults_total = 0
    max_slack_gap_pp = 0.0
    copper_beats_naive = 0
    points = 0
    by_scale_policy: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    by_engine_policy: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    by_point: dict[tuple[str, str, str], dict[str, dict[str, str]]] = defaultdict(dict)

    for row in all_rows:
        by_scale_policy[(row["scale"], row["policy"])].append(row)
        by_engine_policy[(row["engine"], row["policy"])].append(row)
        by_point[(row["scale"], row["engine"], row["seed"])][row["policy"]] = row
        faults_total += as_int(row, "fillPrefetchTranslationFault")

    for point in by_point.values():
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

    def aggregate(rows: list[dict[str, str]]) -> tuple[int, int, int, float, float, float]:
        naive = [row for row in rows if row["policy"] == "naive"]
        copper = [row for row in rows if row["policy"] == "copper_clpd64k_peb"]
        spp = [row for row in rows if row["policy"] == "spp"]
        slack = [row for row in rows if row["policy"] == "spp_copper_slack"]
        naive_ctlw = sum(as_int(row, "targetLineWitnessMisses") for row in naive)
        copper_ctlw = sum(as_int(row, "targetLineWitnessMisses") for row in copper)
        slack_ctlw = sum(as_int(row, "targetLineWitnessMisses") for row in slack)
        copper_mean = sum(as_float(row, "tick_delta_vs_none_pct") for row in copper) / len(copper)
        spp_mean = sum(as_float(row, "tick_delta_vs_none_pct") for row in spp) / len(spp)
        slack_mean = sum(as_float(row, "tick_delta_vs_none_pct") for row in slack) / len(slack)
        return naive_ctlw, copper_ctlw, slack_ctlw, copper_mean, spp_mean, slack_mean

    scale_lines: list[str] = []
    for scale, _seeds in SCALES:
        rows = [row for row in all_rows if row["scale"] == scale]
        naive_ctlw, copper_ctlw, slack_ctlw, copper_mean, spp_mean, slack_mean = aggregate(rows)
        scale_lines.append(
            f"| {scale} | {len(rows) // len(POLICIES)} | {copper_mean:.3f}% | "
            f"{spp_mean:.3f}% | {slack_mean:.3f}% | {naive_ctlw} | "
            f"{copper_ctlw} | {pct_reduction(copper_ctlw, naive_ctlw):.3f}% | "
            f"{slack_ctlw} | {pct_reduction(slack_ctlw, naive_ctlw):.3f}% |"
        )

    engine_lines: list[str] = []
    for engine in ENGINES:
        rows = [row for row in all_rows if row["engine"] == engine]
        naive_ctlw, copper_ctlw, slack_ctlw, copper_mean, spp_mean, slack_mean = aggregate(rows)
        engine_lines.append(
            f"| {engine} | {len(rows) // len(POLICIES)} | {copper_mean:.3f}% | "
            f"{spp_mean:.3f}% | {slack_mean:.3f}% | {naive_ctlw} | "
            f"{copper_ctlw} | {pct_reduction(copper_ctlw, naive_ctlw):.3f}% | "
            f"{slack_ctlw} | {pct_reduction(slack_ctlw, naive_ctlw):.3f}% |"
        )

    naive_ctlw, copper_ctlw, slack_ctlw, copper_mean, spp_mean, slack_mean = aggregate(all_rows)
    status = (
        "PASS"
        if checksum_ok and rc_ok and faults_total == 0 and max_slack_gap_pp <= 1.0
        else "REVIEW"
    )

    lines = [
        "# Public AArch64 Full-System Repeated-Seed Portfolio",
        "",
        "Date: 2026-06-17",
        "",
        "This portfolio combines the repeated public-engine app evidence across",
        "medium and stress scales. It covers SQLite, Lua, and Duktape with three",
        "medium layout seeds and two stress layout seeds per engine, using the",
        "`none`, `naive`, `copper_clpd64k_peb`, `spp`, and `spp_copper_slack`",
        "policy subset. The intent is reviewer-facing stability evidence, not a",
        "replacement for SPEC-scale or production-service evaluation.",
        "",
        "Aggregate by scale:",
        "",
        "| Scale | Engine-seed points | Mean COPPER delta | Mean SPP delta | Mean SPP+COPPER slack delta | Naive CTLW | COPPER CTLW | COPPER CTLW reduction | Slack CTLW | Slack CTLW reduction |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        *scale_lines,
        "",
        "Aggregate by engine:",
        "",
        "| Engine | Scale-seed points | Mean COPPER delta | Mean SPP delta | Mean SPP+COPPER slack delta | Naive CTLW | COPPER CTLW | COPPER CTLW reduction | Slack CTLW | Slack CTLW reduction |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        *engine_lines,
        "",
        "Overall:",
        "",
        f"- Engine-seed points: {points}; policy rows: {len(all_rows)}.",
        f"- Correctness: checksum agreement per point = {'yes' if checksum_ok else 'no'}; `rc=0` for all rows = {'yes' if rc_ok else 'no'}.",
        f"- Translation faults across all rows: {faults_total}.",
        f"- Standalone COPPER beats unsafe naive DMP on {copper_beats_naive}/{points} engine-seed points.",
        f"- Mean COPPER delta: {copper_mean:.3f}%; mean SPP delta: {spp_mean:.3f}%; mean SPP+COPPER slack delta: {slack_mean:.3f}%.",
        f"- Overall COPPER CTLW reduction versus naive DMP: {pct_reduction(copper_ctlw, naive_ctlw):.3f}%.",
        f"- Overall SPP+COPPER slack CTLW reduction versus naive DMP: {pct_reduction(slack_ctlw, naive_ctlw):.3f}%.",
        f"- Worst absolute SPP+COPPER slack gap versus SPP: {max_slack_gap_pp:.3f} percentage points.",
        "- This closes the local medium-only repetition gap; it does not close the SPEC/production-service gap.",
        "",
        f"status={status}",
        "",
    ]
    out = OUT / "COPPER_PUBLIC_APP_REPEATED_SEED_PORTFOLIO_20260617.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
