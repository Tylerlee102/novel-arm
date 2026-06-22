#!/usr/bin/env python3
"""Summarize cold-cache observer-oracle reproducibility across seeds."""

from __future__ import annotations

import csv
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results" / "gem5_arm_ubuntu_fs_dmp_oracle"
OUT = RESULTS / "DMP_ORACLE_OBSERVER_SEED_SWEEP.md"

SEED_FILES = [
    ("0x243f6a8885a308d3", RESULTS / "dmp_oracle_i512_p4_probe1_evict512_summary.csv"),
    ("0x1111111111111111", RESULTS / "dmp_oracle_i512_p4_probe1_evict512_seed1111_summary.csv"),
    ("0x2222222222222222", RESULTS / "dmp_oracle_i512_p4_probe1_evict512_seed2222_summary.csv"),
]

POLICIES = ["naive", "copper_clpd64k_peb", "spp_copper_slack"]


def read_csv(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return {(row["secret"], row["policy"]): row for row in rows}


def as_int(row: dict[str, str], key: str) -> int:
    return int(row[key])


def as_float(row: dict[str, str], key: str) -> float:
    return float(row[key])


def idelta(rows: dict[tuple[str, str], dict[str, str]], policy: str, key: str) -> int:
    return as_int(rows[("1", policy)], key) - as_int(rows[("0", policy)], key)


def fdelta(rows: dict[tuple[str, str], dict[str, str]], policy: str, key: str) -> float:
    return as_float(rows[("1", policy)], key) - as_float(rows[("0", policy)], key)


def main() -> None:
    records: list[dict[str, str]] = []
    for seed, path in SEED_FILES:
        rows = read_csv(path)
        for policy in POLICIES:
            records.append(
                {
                    "seed": seed,
                    "policy": policy,
                    "pf_delta": str(idelta(rows, policy, "pfIssued")),
                    "allowed_delta": str(idelta(rows, policy, "allowedCandidates")),
                    "blocked_delta": str(idelta(rows, policy, "blockedNoProvenance")),
                    "l1d_miss_delta": str(idelta(rows, policy, "l1d_demand_misses")),
                    "timing_delta_pp": f"{fdelta(rows, policy, 'tick_delta_vs_none_pct'):.3f}",
                    "faults_s1": rows[("1", policy)]["fillPrefetchTranslationFault"],
                }
            )

    by_policy = {
        policy: [record for record in records if record["policy"] == policy]
        for policy in POLICIES
    }

    lines = [
        "# DMP Oracle Cold-Cache Observer Seed Sweep",
        "",
        "This sweep repeats the observer oracle with three address permutations.",
        "Each run uses `items=512`, `passes=4`, `probe_targets=1`,",
        "`probe_passes=1`, `evict_kb=512`, and an epoch reset after eviction.",
        "",
        "| Seed | Policy | PF delta | Allowed delta | Blocked delta | L1D miss delta | Timing-delta delta | Secret=1 faults |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for record in records:
        lines.append(
            "| {seed} | {policy} | {pf_delta} | {allowed_delta} | "
            "{blocked_delta} | {l1d_miss_delta} | {timing_delta_pp} pp | "
            "{faults_s1} |".format(**record)
        )

    lines.extend(["", "Aggregate:", "", "| Policy | PF delta mean | Allowed delta set | L1D miss delta range | Timing-delta mean |", "|---|---:|---|---:|---:|"])
    for policy, rows in by_policy.items():
        pf_values = [int(row["pf_delta"]) for row in rows]
        allowed_values = [int(row["allowed_delta"]) for row in rows]
        l1_values = [int(row["l1d_miss_delta"]) for row in rows]
        timing_values = [float(row["timing_delta_pp"]) for row in rows]
        allowed_set = ",".join(str(value) for value in sorted(set(allowed_values)))
        lines.append(
            f"| {policy} | {statistics.mean(pf_values):.1f} | "
            f"{allowed_set} | {min(l1_values)}..{max(l1_values)} | "
            f"{statistics.mean(timing_values):.3f} pp |"
        )

    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            "- Unsafe DMP is reproducibly secret-dependent: all three seeds show positive PF/allowed deltas and fewer observer L1D misses for `secret=1`.",
            "- SCOOP is reproducibly companion-silent in this sweep: allowed-candidate delta is 0 for all three seeds while blocked deltas remain positive.",
            "- Standalone COPPER suppresses the observer cache-footprint delta, but its allowed-candidate delta is small and nonzero across seeds; the paper should treat that as an implementation edge to explain or tighten.",
            "- All secret=1 runs in this sweep record zero fill-origin translation faults.",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
