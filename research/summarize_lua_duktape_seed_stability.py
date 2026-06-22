#!/usr/bin/env python3
"""Summarize Lua and Duktape medium/stress seed stability."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "LUA_DUKTAPE_MEDIUM_STRESS_SEED_STABILITY_20260619.md"

POINTS = [
    ("Lua", "medium", "app_medium", RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_medium_summary.csv"),
    ("Lua", "medium", "app_medium_seed1", RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_medium_seed1_summary.csv"),
    ("Lua", "medium", "app_medium_seed2", RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_medium_seed2_summary.csv"),
    ("Lua", "stress", "app_stress", RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_stress_summary.csv"),
    ("Lua", "stress", "app_stress_seed1", RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_stress_seed1_summary.csv"),
    ("Duktape", "medium", "app_medium", RESULTS / "gem5_arm_ubuntu_fs_duktape_app" / "duktape_app_medium_summary.csv"),
    ("Duktape", "medium", "app_medium_seed1", RESULTS / "gem5_arm_ubuntu_fs_duktape_app" / "duktape_app_medium_seed1_summary.csv"),
    ("Duktape", "medium", "app_medium_seed2", RESULTS / "gem5_arm_ubuntu_fs_duktape_app" / "duktape_app_medium_seed2_summary.csv"),
    ("Duktape", "stress", "app_stress", RESULTS / "gem5_arm_ubuntu_fs_duktape_app" / "duktape_app_stress_summary.csv"),
    ("Duktape", "stress", "app_stress_seed1", RESULTS / "gem5_arm_ubuntu_fs_duktape_app" / "duktape_app_stress_seed1_summary.csv"),
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


def summarize_point(
    engine: str, scale: str, tag: str, rows: dict[str, dict[str, str]]
) -> dict[str, object]:
    checksums = {rows[policy]["checksum"] for policy in KEY_POLICIES}
    rcs = {rows[policy]["rc"] for policy in KEY_POLICIES}
    naive_ctlw = i(rows["naive"], "targetLineWitnessMisses")
    copper_ctlw = i(rows["copper_clpd64k_peb"], "targetLineWitnessMisses")
    slack_ctlw = i(rows["spp_copper_slack"], "targetLineWitnessMisses")
    spp_delta = f(rows["spp"], "tick_delta_vs_none_pct")
    slack_delta = f(rows["spp_copper_slack"], "tick_delta_vs_none_pct")
    return {
        "engine": engine,
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


def reduction_range(items: list[dict[str, object]], key: str) -> str:
    values = [float(item[key]) for item in items]
    return f"{min(values):.1f}% to {max(values):.1f}%"


def summarize_group(label: str, items: list[dict[str, object]]) -> str:
    gaps = [abs(float(item["slack_gap"])) for item in items]
    return (
        f"- {label}: {len(items)} points; COPPER CTLW reduction "
        f"{reduction_range(items, 'copper_reduction')}; SPP+COPPER slack CTLW reduction "
        f"{reduction_range(items, 'slack_reduction')}; worst slack-vs-SPP gap "
        f"{max(gaps):.3f} percentage points."
    )


def main() -> None:
    summary = [
        summarize_point(engine, scale, tag, read_rows(path))
        for engine, scale, tag, path in POINTS
    ]
    status_ok = True
    for item in summary:
        status_ok = status_ok and item["checksum"] != "MISMATCH" and bool(item["rc_ok"])
        status_ok = status_ok and int(item["copper_faults"]) == 0 and int(item["slack_faults"]) == 0

    all_copper = [float(item["copper_reduction"]) for item in summary]
    all_slack = [float(item["slack_reduction"]) for item in summary]
    worst_gap = max(abs(float(item["slack_gap"])) for item in summary)
    status = "PASS" if status_ok else "FAIL"

    lines = [
        "# Lua/Duktape Medium/Stress Seed Stability",
        "",
        "Date: 2026-06-19",
        "",
        "Scope: public Lua-table and Duktape-object AArch64 full-system application workloads, three medium seeds and two stress seeds per engine, key policies only for repeated seeds. This is language-runtime-style external-validity evidence, not SPEC or browser-scale JavaScript/Lua execution.",
        "",
        "| Engine | Scale | Tag | Seed | Naive CTLW | COPPER CTLW | COPPER reduction | Slack CTLW | Slack reduction | SPP delta | Slack delta | Slack gap vs SPP | COPPER faults | Slack faults | Checksum |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in summary:
        lines.append(
            f"| {item['engine']} | {item['scale']} | {item['tag']} | {item['seed']} | "
            f"{item['naive_ctlw']} | {item['copper_ctlw']} | "
            f"{float(item['copper_reduction']):.1f}% | {item['slack_ctlw']} | "
            f"{float(item['slack_reduction']):.1f}% | {float(item['spp_delta']):.3f}% | "
            f"{float(item['slack_delta']):.3f}% | {float(item['slack_gap']):+.3f} pp | "
            f"{item['copper_faults']} | {item['slack_faults']} | {item['checksum']} |"
        )

    lines.extend(["", "Aggregate:", ""])
    for engine in ("Lua", "Duktape"):
        lines.append(summarize_group(engine, [item for item in summary if item["engine"] == engine]))
    for scale in ("medium", "stress"):
        lines.append(
            summarize_group(
                scale.title(), [item for item in summary if item["scale"] == scale]
            )
        )
    lines.extend(
        [
            f"- Across all {len(summary)} Lua/Duktape medium/stress seed points, COPPER CTLW reduction is at least {min(all_copper):.1f}%.",
            f"- Across all {len(summary)} Lua/Duktape medium/stress seed points, SPP+COPPER slack CTLW reduction is at least {min(all_slack):.1f}%.",
            f"- Worst absolute SPP+COPPER slack tick gap versus SPP is {worst_gap:.3f} percentage points.",
            "- COPPER and SPP+COPPER slack translation faults are zero across all Lua/Duktape seed points.",
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
