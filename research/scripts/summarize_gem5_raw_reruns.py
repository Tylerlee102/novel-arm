#!/usr/bin/env python3
"""Summarize fresh local raw gem5 rerun statistics.

This ledger is intentionally narrower than gem5_statistical_summary.csv: it
uses only rows recorded in gem5_raw_rerun_manifest.csv. Repeated raw samples
receive PASS statistics; one-off smoke rows remain SINGLE_SAMPLE.
"""

from __future__ import annotations

import csv
import math
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, stdev


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "research" / "results"
MANIFEST = RESULTS / "gem5_raw_rerun_manifest.csv"
OUT = RESULTS / "gem5_raw_rerun_statistical_summary.csv"

METRICS = ("roi_ticks", "instructions", "l1d_demand_misses")
FIELDS = [
    "raw_group",
    "policy",
    "metric",
    "status",
    "n",
    "mean",
    "median",
    "std",
    "min",
    "max",
    "ci95_low",
    "ci95_high",
    "source_tags",
    "source_rows",
    "notes",
]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def raw_group(tag: str) -> str:
    return re.sub(r"_seed\d+$", "", tag)


def number(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt(value: float) -> str:
    return f"{value:.6f}"


def summarize() -> list[dict[str, str]]:
    values: dict[tuple[str, str, str], list[tuple[float, str]]] = defaultdict(list)
    for row in read_csv(MANIFEST):
        if row.get("status") != "PASS":
            continue
        group = raw_group(row.get("tag", ""))
        policy = row.get("policy", "")
        if not group or not policy:
            continue
        for metric in METRICS:
            value = number(row.get(metric, ""))
            if value is not None:
                values[(group, policy, metric)].append((value, row.get("tag", "")))

    rows: list[dict[str, str]] = []
    for (group, policy, metric), samples in sorted(values.items()):
        vals = [sample[0] for sample in samples]
        tags = sorted({sample[1] for sample in samples if sample[1]})
        n = len(vals)
        avg = mean(vals)
        sd = stdev(vals) if n > 1 else 0.0
        ci = 1.96 * sd / math.sqrt(n) if n > 1 else 0.0
        rows.append(
            {
                "raw_group": group,
                "policy": policy,
                "metric": metric,
                "status": "PASS" if n > 1 else "SINGLE_SAMPLE",
                "n": str(n),
                "mean": fmt(avg),
                "median": fmt(median(vals)),
                "std": fmt(sd),
                "min": fmt(min(vals)),
                "max": fmt(max(vals)),
                "ci95_low": fmt(avg - ci),
                "ci95_high": fmt(avg + ci),
                "source_tags": ";".join(tags),
                "source_rows": str(len(samples)),
                "notes": (
                    "Fresh local raw gem5 full-system rerun statistics from "
                    f"{rel(MANIFEST)} only; PASS requires at least two raw samples. "
                    "This is not a full workload/config campaign unless the raw_group "
                    "covers the final matrix."
                ),
            }
        )
    return rows


def main() -> int:
    rows = summarize()
    if not rows:
        rows = [
            {
                "raw_group": "ALL",
                "policy": "NA",
                "metric": "NA",
                "status": "BLOCKED",
                "n": "0",
                "mean": "NA",
                "median": "NA",
                "std": "NA",
                "min": "NA",
                "max": "NA",
                "ci95_low": "NA",
                "ci95_high": "NA",
                "source_tags": "",
                "source_rows": "0",
                "notes": f"No PASS raw rerun rows found in {rel(MANIFEST)}.",
            }
        ]
    write_csv(OUT, rows)
    print(f"wrote {rel(OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
