#!/usr/bin/env python3
"""Audit cache-service small-to-medium scale sensitivity."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
APP_DIR = RESULTS / "gem5_arm_ubuntu_fs_cachesvc_app"
OUT = APP_DIR / "CACHESVC_SCALE_SENSITIVITY_AUDIT.md"

SCALES = [
    ("small", 256, 512, 32, APP_DIR / "cachesvc_app_small_summary.csv"),
    ("medium", 512, 1024, 64, APP_DIR / "cachesvc_app_medium_key_summary.csv"),
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
    per_scale = [(label, items, reqs, scan, read(path)) for label, items, reqs, scan, path in SCALES]
    lines = [
        "# Cache-Service Scale Sensitivity Audit",
        "",
        "Date: 2026-06-18",
        "",
        "Purpose: test whether the cache-service authority result survives a larger",
        "service state. The medium point doubles item count, request count, and",
        "hot-list scan depth relative to the small point, while keeping the key",
        "authority policies fixed: none, naive DMP, COPPER CLPD-64K+PEB, and",
        "SPP+COPPER slack.",
        "",
        "| Scale | Items | Requests | Scan depth | Policy | Runtime delta | Pointer-like | Allowed | Blocked | CTLW misses | Faults | Checksum | rc |",
        "|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    all_rc_ok = True
    all_scale_checksums_ok = True
    copper_reductions: list[float] = []
    slack_reductions: list[float] = []
    copper_faults = 0
    slack_faults = 0

    for scale, items, requests, scan_depth, rows in per_scale:
        checksums = {row.get("checksum", "") for row in rows.values()}
        rcs = {row.get("rc", "") for row in rows.values()}
        all_scale_checksums_ok = all_scale_checksums_ok and len(checksums) == 1 and "" not in checksums
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
                f"| {scale} | {items} | {requests} | {scan_depth} | {policy} | "
                f"{ff(row, 'tick_delta_vs_none_pct'):.3f}% | "
                f"{ii(row, 'pointerLikeCandidates')} | {ii(row, 'allowedCandidates')} | "
                f"{ii(row, 'blockedNoProvenance')} | {ii(row, 'targetLineWitnessMisses')} | "
                f"{ii(row, 'fillPrefetchTranslationFault')} | {row.get('checksum', '')} | {row.get('rc', '')} |"
            )

    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            f"- COPPER CTLW reduction versus naive DMP across scales: {min(copper_reductions):.1f}% to {max(copper_reductions):.1f}%.",
            f"- SPP+COPPER slack CTLW reduction versus naive DMP across scales: {min(slack_reductions):.1f}% to {max(slack_reductions):.1f}%.",
            f"- COPPER and SPP+COPPER slack translation faults across the scale audit: {copper_faults + slack_faults}.",
            f"- Checksums agree within each scale: {'yes' if all_scale_checksums_ok else 'no'}; guest return codes all zero: {'yes' if all_rc_ok else 'no'}.",
            "- This is still a bounded micro-service scale audit, not a production cache-server campaign. It does reduce the risk that COPPER's cache-service authority behavior only appears at the smallest service state.",
            "",
            "scale_sensitivity_status=PASS" if all_scale_checksums_ok and all_rc_ok and copper_faults + slack_faults == 0 else "scale_sensitivity_status=FAIL",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
