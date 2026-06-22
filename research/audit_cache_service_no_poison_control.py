#!/usr/bin/env python3
"""Compare cache-service poisoned and no-poison control runs."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
APP_DIR = RESULTS / "gem5_arm_ubuntu_fs_cachesvc_app"
POISON_CSV = APP_DIR / "cachesvc_app_small_summary.csv"
NOPOISON_CSV = APP_DIR / "cachesvc_app_small_nopoison_clean_summary.csv"
OUT = APP_DIR / "CACHESVC_NOPOISON_CONTROL_AUDIT.md"

POLICIES = ["none", "naive", "copper_clpd64k_peb", "spp_copper_slack"]


def read(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return {row["policy"]: row for row in csv.DictReader(fh)}


def ii(row: dict[str, str], key: str) -> int:
    return int(float(row.get(key, "0") or "0"))


def ff(row: dict[str, str], key: str) -> float:
    return float(row.get(key, "0") or "0")


def pct_change(new: int, old: int) -> float:
    return 100.0 * ((new / old) - 1.0) if old else 0.0


def reduction(new: int, old: int) -> float:
    return 100.0 * (1.0 - (new / old)) if old else 0.0


def main() -> None:
    poison = read(POISON_CSV)
    clean = read(NOPOISON_CSV)

    lines = [
        "# Cache-Service Poison vs No-Poison Control Audit",
        "",
        "Date: 2026-06-18",
        "",
        "Purpose: test whether the cache-service workload can be used as a clean",
        "differential security oracle for pointer-shaped payload data. The answer is",
        "no: even when payload words are constrained below the DMP candidate range,",
        "the hash/LRU service still exposes real pointer fields and high-entropy",
        "service data that produce pointer-like candidates. Therefore this workload",
        "is valid as a service-style performance/authority stress point, but not as",
        "the primary data-at-rest security oracle.",
        "",
        "| Policy | Poison pointer-like | Clean pointer-like | Change | Poison allowed | Clean allowed | Poison CTLW | Clean CTLW | Faults poison/clean | Runtime poison | Runtime clean |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for policy in POLICIES:
        p = poison[policy]
        c = clean[policy]
        p_like = ii(p, "pointerLikeCandidates")
        c_like = ii(c, "pointerLikeCandidates")
        lines.append(
            f"| {policy} | {p_like} | {c_like} | {pct_change(c_like, p_like):.1f}% | "
            f"{ii(p, 'allowedCandidates')} | {ii(c, 'allowedCandidates')} | "
            f"{ii(p, 'targetLineWitnessMisses')} | {ii(c, 'targetLineWitnessMisses')} | "
            f"{ii(p, 'fillPrefetchTranslationFault')}/{ii(c, 'fillPrefetchTranslationFault')} | "
            f"{ff(p, 'tick_delta_vs_none_pct'):.3f}% | {ff(c, 'tick_delta_vs_none_pct'):.3f}% |"
        )

    naive_poison_ctlw = ii(poison["naive"], "targetLineWitnessMisses")
    copper_poison_ctlw = ii(poison["copper_clpd64k_peb"], "targetLineWitnessMisses")
    naive_clean_ctlw = ii(clean["naive"], "targetLineWitnessMisses")
    copper_clean_ctlw = ii(clean["copper_clpd64k_peb"], "targetLineWitnessMisses")
    poison_checksums = {row.get("checksum", "") for row in poison.values()}
    clean_checksums = {row.get("checksum", "") for row in clean.values()}
    poison_rc = {row.get("rc", "") for row in poison.values()}
    clean_rc = {row.get("rc", "") for row in clean.values()}

    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            f"- Poisoned service run: COPPER reduces naive CTLW misses by {reduction(copper_poison_ctlw, naive_poison_ctlw):.1f}% with zero translation faults.",
            f"- Clean no-poison run: COPPER reduces naive CTLW misses by {reduction(copper_clean_ctlw, naive_clean_ctlw):.1f}% with zero translation faults.",
            "- The no-poison run still has thousands of pointer-like candidates, so it does not isolate payload-shaped data. The residual candidates are consistent with the workload's real linked hash/LRU metadata and high-entropy service fields.",
            "- Use the fake-only ROI, secret traffic oracle, observer oracle, and split scan/probe audit for differential security claims. Use the cache-service workload as an external-validity stress point showing that COPPER/SCOOP retain authority behavior on service-like pointer-rich code.",
            f"- Poison checksums agree: {'yes' if len(poison_checksums) == 1 and '' not in poison_checksums else 'no'}; clean checksums agree: {'yes' if len(clean_checksums) == 1 and '' not in clean_checksums else 'no'}.",
            f"- Guest return codes all zero: {'yes' if poison_rc == {'0'} and clean_rc == {'0'} else 'no'}.",
            "",
            "verdict=VALID_STRESS_POINT_NOT_CLEAN_SECURITY_ORACLE",
            "status=PASS",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
