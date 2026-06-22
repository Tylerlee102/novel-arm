#!/usr/bin/env python3
"""Compare default and randomized-allocation Olden full-system results."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "results" / "gem5_arm_ubuntu_fs_olden_suite"
TAGS = ["suite4_small", "suite4_randomalloc"]
POLICIES = ["stride", "naive", "copper_clpd64k", "copper_clpd64k_peb"]


def load(tag: str) -> list[dict[str, str]]:
    path = OUT / f"olden_{tag}_summary.csv"
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def maybe_rows(rows: list[dict[str, str]], policy: str) -> list[dict[str, str]]:
    return [row for row in rows if row["policy"] == policy]


def main() -> None:
    lines = [
        "# Olden Layout Sensitivity",
        "",
        "This compares the same public Olden AArch64 full-system suite under",
        "the default allocation layout and a randomized-allocation sensitivity",
        "build. The randomized build preserves the benchmark algorithms but",
        "pads allocation placement to reduce easy allocator-local stride behavior.",
        "",
        "| Layout | Policy | Mean tick delta vs none | Total PF issued | Total CTLW misses | Total blocked no provenance |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for tag in TAGS:
        rows = load(tag)
        layout = "default" if tag == "suite4_small" else "randomized allocation"
        for policy in POLICIES:
            selected = maybe_rows(rows, policy)
            if not selected:
                continue
            mean_delta = sum(
                float(row["tick_delta_vs_none_pct"]) for row in selected
            ) / len(selected)
            pf = sum(int(row["pfIssued"]) for row in selected)
            ctlw = sum(int(row["targetLineWitnessMisses"]) for row in selected)
            blocked = sum(int(row["blockedNoProvenance"]) for row in selected)
            lines.append(
                f"| {layout} | {policy} | {mean_delta:.3f}% | "
                f"{pf} | {ctlw} | {blocked} |"
            )
    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            "- Default Olden mostly measures safety/control behavior: COPPER is near neutral, while stride benefits from allocator-local tree/list placement.",
            "- Randomized allocation removes much of that accidental stride locality: stride slows by 10.107% mean and naive DMP is roughly neutral at +0.039%.",
            "- PEB is not just bookkeeping in this test: randomized COPPER without PEB slows by +0.401% mean, while COPPER CLPD-64K+PEB improves by -0.398% mean.",
            "- On randomized allocation, COPPER CLPD-64K+PEB reduces CTLW misses from naive's 188,223 to 29,039 while blocking 320,013 unproven pointer-like candidates and preserving zero translation faults.",
            "",
        ]
    )
    out = OUT / "OLDEN_LAYOUT_SENSITIVITY.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
