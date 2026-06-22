#!/usr/bin/env python3
"""Audit cache-service seed stability for key COPPER/SCOOP policies."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
APP_DIR = RESULTS / "gem5_arm_ubuntu_fs_cachesvc_app"
OUT = APP_DIR / "CACHESVC_SEED_STABILITY_AUDIT.md"

SEEDS = [
    ("seed2", APP_DIR / "cachesvc_app_small_summary.csv"),
    ("seed3", APP_DIR / "cachesvc_app_small_seed3_summary.csv"),
]
POLICIES = ["none", "naive", "copper_clpd64k_peb", "spp_copper_slack"]


def read(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        rows = {row["policy"]: row for row in csv.DictReader(fh)}
    missing = [policy for policy in POLICIES if policy not in rows]
    if missing:
        raise RuntimeError(f"{path} missing policies: {', '.join(missing)}")
    return rows


def ii(row: dict[str, str], key: str) -> int:
    return int(float(row.get(key, "0") or "0"))


def ff(row: dict[str, str], key: str) -> float:
    return float(row.get(key, "0") or "0")


def reduction(new: int, old: int) -> float:
    return 100.0 * (1.0 - (new / old)) if old else 0.0


def main() -> None:
    per_seed = [(label, read(path)) for label, path in SEEDS]
    lines = [
        "# Cache-Service Seed Stability Audit",
        "",
        "Date: 2026-06-18",
        "",
        "Purpose: check whether the cache-service result is a one-layout accident.",
        "This audit uses the same native AArch64 hash/LRU service workload at the",
        "same small scale, but with two independent layout/data seeds and the key",
        "authority policies: none, naive DMP, COPPER CLPD-64K+PEB, and",
        "SPP+COPPER slack.",
        "",
        "| Seed | Policy | Runtime delta | Pointer-like | Allowed | Blocked | CTLW misses | Faults | Checksum | rc |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    all_rc_ok = True
    all_seed_checksums_ok = True
    copper_reductions: list[float] = []
    slack_reductions: list[float] = []
    copper_faults = 0
    slack_faults = 0

    for seed, rows in per_seed:
        checksums = {row.get("checksum", "") for row in rows.values()}
        rcs = {row.get("rc", "") for row in rows.values()}
        all_seed_checksums_ok = all_seed_checksums_ok and len(checksums) == 1 and "" not in checksums
        all_rc_ok = all_rc_ok and rcs == {"0"}

        naive_ctlw = ii(rows["naive"], "targetLineWitnessMisses")
        copper_ctlw = ii(rows["copper_clpd64k_peb"], "targetLineWitnessMisses")
        slack_ctlw = ii(rows["spp_copper_slack"], "targetLineWitnessMisses")
        copper_reductions.append(reduction(copper_ctlw, naive_ctlw))
        slack_reductions.append(reduction(slack_ctlw, naive_ctlw))
        copper_faults += ii(rows["copper_clpd64k_peb"], "fillPrefetchTranslationFault")
        slack_faults += ii(rows["spp_copper_slack"], "fillPrefetchTranslationFault")

        for policy in POLICIES:
            row = rows[policy]
            lines.append(
                f"| {seed} | {policy} | {ff(row, 'tick_delta_vs_none_pct'):.3f}% | "
                f"{ii(row, 'pointerLikeCandidates')} | {ii(row, 'allowedCandidates')} | "
                f"{ii(row, 'blockedNoProvenance')} | {ii(row, 'targetLineWitnessMisses')} | "
                f"{ii(row, 'fillPrefetchTranslationFault')} | {row.get('checksum', '')} | {row.get('rc', '')} |"
            )

    min_copper = min(copper_reductions)
    max_copper = max(copper_reductions)
    min_slack = min(slack_reductions)
    max_slack = max(slack_reductions)
    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            f"- COPPER CTLW reduction versus naive DMP is stable across {len(per_seed)} seeds: {min_copper:.1f}% to {max_copper:.1f}%.",
            f"- SPP+COPPER slack CTLW reduction versus naive DMP is stable across {len(per_seed)} seeds: {min_slack:.1f}% to {max_slack:.1f}%.",
            f"- COPPER and SPP+COPPER slack translation faults across the seed audit: {copper_faults + slack_faults}.",
            f"- Checksums agree within each seed: {'yes' if all_seed_checksums_ok else 'no'}; guest return codes all zero: {'yes' if all_rc_ok else 'no'}.",
            "- This is still a two-seed bounded service-style audit, not a production cache-server campaign, but it reduces the risk that the cache-service result is a single layout accident.",
            "",
            "seed_stability_status=PASS" if all_seed_checksums_ok and all_rc_ok and copper_faults + slack_faults == 0 else "seed_stability_status=FAIL",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
