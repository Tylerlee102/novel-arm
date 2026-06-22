#!/usr/bin/env python3
"""Aggregate Lua medium full-system seed-sweep results."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from summarize_lua_table_app_fs import summarize


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "results" / "gem5_arm_ubuntu_fs_lua_app"
POLICIES = [
    "none",
    "naive",
    "copper_clpd64k_peb",
    "spp",
    "spp_copper_slack",
]
SEEDS = [
    (0, "app_medium"),
    (1, "app_medium_seed1"),
    (2, "app_medium_seed2"),
]


def pct_reduction(new: int, old: int) -> float:
    return 100.0 * (1.0 - (new / old)) if old else 0.0


def as_int(row: dict[str, str], key: str) -> int:
    value = row.get(key, "")
    return int(value) if value else 0


def as_float(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    return float(value) if value else 0.0


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows_by_seed: dict[int, list[dict[str, str]]] = {}
    for seed, tag in SEEDS:
        rows = summarize(tag, POLICIES)
        for row in rows:
            row["seed"] = str(seed)
            row["tag"] = tag
        rows_by_seed[seed] = rows

    all_rows = [row for seed, _tag in SEEDS for row in rows_by_seed[seed]]
    aggregates: dict[str, dict[str, object]] = {}
    by_policy: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in all_rows:
        by_policy[row["policy"]].append(row)

    for policy, policy_rows in by_policy.items():
        deltas = [as_float(row, "tick_delta_vs_none_pct") for row in policy_rows]
        aggregates[policy] = {
            "count": len(policy_rows),
            "mean": sum(deltas) / len(deltas),
            "min": min(deltas),
            "max": max(deltas),
            "ctlw": sum(as_int(row, "targetLineWitnessMisses") for row in policy_rows),
            "faults": sum(as_int(row, "fillPrefetchTranslationFault") for row in policy_rows),
        }

    checksum_ok = True
    rc_ok = True
    copper_beats_naive = True
    slack_close_to_spp = True
    max_slack_gap_pp = 0.0
    for seed, _tag in SEEDS:
        rows = rows_by_seed[seed]
        checksums = {row["checksum"] for row in rows}
        checksum_ok = checksum_ok and len(checksums) == 1 and "" not in checksums
        rc_ok = rc_ok and all(row["rc"] == "0" for row in rows)
        seed_rows = {row["policy"]: row for row in rows}
        copper_beats_naive = copper_beats_naive and (
            as_float(seed_rows["copper_clpd64k_peb"], "tick_delta_vs_none_pct")
            < as_float(seed_rows["naive"], "tick_delta_vs_none_pct")
        )
        gap = abs(
            as_float(seed_rows["spp_copper_slack"], "tick_delta_vs_none_pct")
            - as_float(seed_rows["spp"], "tick_delta_vs_none_pct")
        )
        max_slack_gap_pp = max(max_slack_gap_pp, gap)
        slack_close_to_spp = slack_close_to_spp and gap <= 1.0

    naive_ctlw = int(aggregates["naive"]["ctlw"])
    copper_ctlw = int(aggregates["copper_clpd64k_peb"]["ctlw"])
    slack_ctlw = int(aggregates["spp_copper_slack"]["ctlw"])
    faults_total = sum(int(item["faults"]) for item in aggregates.values())
    status = (
        "PASS"
        if checksum_ok
        and rc_ok
        and copper_beats_naive
        and slack_close_to_spp
        and faults_total == 0
        else "REVIEW"
    )

    lines = [
        "# Lua AArch64 Full-System Medium Seed Sweep",
        "",
        "Date: 2026-06-17",
        "",
        "This sweep repeats the public Lua 5.4.8 table/runtime workload across",
        "three medium-size layout seeds. Seed 0 is the prior `app_medium` run;",
        "seeds 1 and 2 use the workload `--seed` argument. Each run uses 2,048",
        "rows, 6,000 lookups, 2,048 updates, and 6,000 linked traversals under",
        "ARM64/Linux gem5 full-system timing.",
        "",
        "| Seed | Policy | Delta vs none | ROI ticks | L1D misses | PF issued | PF useful | Pointer-like | Allowed | Blocked | CTLW misses | Translation faults | Checksum | rc |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for seed, _tag in SEEDS:
        for row in rows_by_seed[seed]:
            lines.append(
                f"| {seed} | {row['policy']} | {row['tick_delta_vs_none_pct']}% | "
                f"{row['roi_ticks']} | {row['l1d_demand_misses']} | "
                f"{row['pfIssued']} | {row['pfUseful']} | "
                f"{row['pointerLikeCandidates']} | {row['allowedCandidates']} | "
                f"{row['blockedNoProvenance']} | {row['targetLineWitnessMisses']} | "
                f"{row['fillPrefetchTranslationFault']} | {row['checksum']} | {row['rc']} |"
            )

    lines.extend(
        [
            "",
            "Aggregate:",
            "",
            "| Policy | Seeds | Mean delta vs none | Min delta | Max delta | Total CTLW misses | Translation faults |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for policy in POLICIES:
        agg = aggregates[policy]
        lines.append(
            f"| {policy} | {agg['count']} | {agg['mean']:.3f}% | "
            f"{agg['min']:.3f}% | {agg['max']:.3f}% | {agg['ctlw']} | {agg['faults']} |"
        )

    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            f"- Checksum and `rc=0` agree within each seed across all policies: {'yes' if checksum_ok and rc_ok else 'no'}.",
            f"- COPPER CLPD-64K+PEB beats unsafe naive DMP on all three medium Lua layouts: {'yes' if copper_beats_naive else 'no'}.",
            f"- COPPER cuts aggregate naive CTLW misses by {pct_reduction(copper_ctlw, naive_ctlw):.3f}%.",
            f"- SPP+COPPER slack stays within {max_slack_gap_pp:.3f} percentage points of SPP across the medium seeds and cuts aggregate naive CTLW misses by {pct_reduction(slack_ctlw, naive_ctlw):.3f}%.",
            f"- Total fill-origin translation faults across the sweep: {faults_total}.",
            "- This improves application-layout stability evidence, but it remains a bounded language-runtime study rather than a SPEC-scale statistical campaign.",
            "",
            f"status={status}",
            "",
        ]
    )
    path = OUT / "LUA_APP_MEDIUM_SEED_SWEEP_SUMMARY.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
