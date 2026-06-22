#!/usr/bin/env python3
"""Summarize Olden AArch64 full-system gem5 suite runs."""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "gem5_arm_ubuntu_fs_olden_suite"

DEFAULT_KERNELS = ["treeadd", "bisort", "mst", "health"]
PREFETCH_COUNTERS = [
    "pfIssued",
    "pfUseful",
    "pfUnused",
    "pfIdentified",
    "pointerLikeCandidates",
    "learnedProofs",
    "proofEvictions",
    "allowedCandidates",
    "blockedNoProvenance",
    "fillPrefetchTranslated",
    "fillPrefetchTranslationFault",
    "fillPrefetchTranslationUnavailable",
    "targetLineWitnessHits",
    "targetLineWitnessMisses",
    "carriedProvenanceTerminalStops",
    "boundaryFlushes",
    "boundaryAuthorityEntriesDropped",
    "boundaryPrefetchesDropped",
]


def parse_stats_sections(path: Path) -> list[dict[str, float]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    sections: list[dict[str, float]] = []
    marker = "---------- Begin Simulation Statistics ----------"
    end_marker = "---------- End Simulation Statistics"
    start = 0
    while True:
        try:
            begin = text.index(marker, start)
            end = text.index(end_marker, begin)
        except ValueError:
            break
        stats: dict[str, float] = {}
        for line in text[begin:end].splitlines():
            if not line or line.startswith("-"):
                continue
            parts = line.split("#", 1)[0].split()
            if len(parts) < 2:
                continue
            try:
                stats[parts[0]] = float(parts[1])
            except ValueError:
                stats[parts[0]] = math.nan
        sections.append(stats)
        start = end + len(end_marker)
    return sections


def sum_matching(stats: dict[str, float], suffix: str, contains: str | None = None) -> int:
    return int(
        sum(
            value
            for key, value in stats.items()
            if key.endswith(suffix)
            and (contains is None or contains in key)
            and not math.isnan(value)
        )
    )


def sum_prefetch_counter(stats: dict[str, float], counter: str) -> int:
    matches = [
        (key, value)
        for key, value in stats.items()
        if key.endswith(f".{counter}")
        and ".prefetcher" in key
        and not math.isnan(value)
    ]
    child_matches = [
        value
        for key, value in matches
        if ".prefetchers" in key
        or ".primary." in key
        or ".companion." in key
    ]
    if child_matches:
        return int(sum(child_matches))
    return int(sum(value for _, value in matches))


def parse_terminal(path: Path, kernels: list[str]) -> dict[str, dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    info: dict[str, dict[str, str]] = {kernel: {} for kernel in kernels}
    pattern = re.compile(
        r"COPPER_FS_NATIVE_JOB_START olden_(?P<kernel>\w+)(?P<body>.*?)"
        r"COPPER_FS_NATIVE_JOB_DONE olden_(?P=kernel) rc=(?P<rc>\d+)",
        re.DOTALL,
    )
    for match in pattern.finditer(text):
        kernel = match.group("kernel")
        if kernel not in info:
            continue
        body = match.group("body")
        info[kernel]["rc"] = match.group("rc")
        checks = [
            ("treeadd_result", r"Received result of\s+([0-9-]+)"),
            ("mst_cost", r"MST has cost\s+([0-9-]+)"),
            ("health_patients", r"# of people treated:\s+([0-9.]+)"),
            ("health_stay", r"Average length of stay:\s+([0-9.]+)"),
        ]
        for name, regex in checks:
            found = re.search(regex, body)
            if found:
                info[kernel][name] = found.group(1)
    return info


def stats_for_jobs(sections: list[dict[str, float]], kernels: list[str]) -> list[dict[str, float]]:
    if len(sections) >= len(kernels):
        return sections[: len(kernels)]
    raise RuntimeError(
        f"Only {len(sections)} stats sections found; expected at least {len(kernels)}"
    )


def make_runs(tag: str, extra_runs: list[str] | None = None) -> list[tuple[str, Path]]:
    labels = ["none", "stride", "naive", "copper_clpd64k_peb"]
    runs = [
        (label, RESULTS / f"gem5_arm_ubuntu_fs_olden_{tag}_{label}")
        for label in labels
    ]
    for spec in extra_runs or []:
        policy, raw_path = spec.split("=", 1)
        path = Path(raw_path)
        if not path.is_absolute():
            path = ROOT / path
        runs.append((policy, path))
    return runs


def summarize(tag: str, kernels: list[str], extra_runs: list[str] | None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for policy, run_dir in make_runs(tag, extra_runs):
        sections = stats_for_jobs(parse_stats_sections(run_dir / "stats.txt"), kernels)
        terminal = parse_terminal(run_dir / "board.terminal", kernels)
        for kernel, stats in zip(kernels, sections):
            row: dict[str, str] = {
                "kernel": kernel,
                "policy": policy,
                "roi_ticks": str(int(stats.get("simTicks", 0))),
                "insts_not_nop": str(
                    sum_matching(
                        stats,
                        ".core.commitStats0.numInstsNotNOP",
                        "board.processor.switch",
                    )
                ),
                "l1d_demand_misses": str(
                    sum_matching(
                        stats,
                        ".demandMisses::total",
                        "board.cache_hierarchy.l1d-cache-",
                    )
                ),
                "l1d_demand_accesses": str(
                    sum_matching(
                        stats,
                        ".demandAccesses::total",
                        "board.cache_hierarchy.l1d-cache-",
                    )
                ),
                "l2_demand_misses": str(
                    sum_matching(
                        stats,
                        ".demandMisses::total",
                        "board.cache_hierarchy.l2-cache-",
                    )
                ),
                "rc": terminal[kernel].get("rc", ""),
                "treeadd_result": terminal[kernel].get("treeadd_result", ""),
                "mst_cost": terminal[kernel].get("mst_cost", ""),
                "health_patients": terminal[kernel].get("health_patients", ""),
                "health_stay": terminal[kernel].get("health_stay", ""),
            }
            for counter in PREFETCH_COUNTERS:
                row[counter] = str(sum_prefetch_counter(stats, counter))
            rows.append(row)

    base_ticks = {
        row["kernel"]: int(row["roi_ticks"])
        for row in rows
        if row["policy"] == "none"
    }
    for row in rows:
        base = base_ticks.get(row["kernel"], 0)
        ticks = int(row["roi_ticks"])
        row["tick_delta_vs_none_pct"] = (
            f"{((ticks / base) - 1.0) * 100.0:.3f}" if base else ""
        )
    return rows


def write_outputs(tag: str, rows: list[dict[str, str]], input_label: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / f"olden_{tag}_summary.csv"
    fields = list(rows[0].keys())
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    aggregate: dict[str, dict[str, float]] = {}
    for row in rows:
        entry = aggregate.setdefault(
            row["policy"],
            {"ticks": 0.0, "pf": 0.0, "ctlw_miss": 0.0, "fault": 0.0, "n": 0.0},
        )
        entry["ticks"] += float(row["tick_delta_vs_none_pct"] or 0.0)
        entry["pf"] += float(row["pfIssued"])
        entry["ctlw_miss"] += float(row["targetLineWitnessMisses"])
        entry["fault"] += float(row["fillPrefetchTranslationFault"])
        entry["n"] += 1.0

    lines = [
        f"# Olden AArch64 Full-System Summary ({tag})",
        "",
        "This summarizes public Olden pointer-intensive benchmarks cross-built",
        "for AArch64 Linux and run under gem5 full-system with the L1D",
        f"prefetcher path. Input preset: {input_label}.",
        "",
        "| Kernel | Policy | ROI ticks | Delta vs none | PF issued | Pointer-like | Allowed | Blocked | CTLW misses | Faults | Boundary drops | rc |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['kernel']} | {row['policy']} | {row['roi_ticks']} | "
            f"{row['tick_delta_vs_none_pct']}% | {row['pfIssued']} | "
            f"{row['pointerLikeCandidates']} | {row['allowedCandidates']} | "
            f"{row['blockedNoProvenance']} | {row['targetLineWitnessMisses']} | "
            f"{row['fillPrefetchTranslationFault']} | "
            f"{row['boundaryAuthorityEntriesDropped']} | {row['rc']} |"
        )
    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            "| Policy | Mean tick delta vs none | Total PF issued | Total CTLW misses | Total faults |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for policy, vals in aggregate.items():
        n = max(vals["n"], 1.0)
        lines.append(
            f"| {policy} | {vals['ticks'] / n:.3f}% | {int(vals['pf'])} | "
            f"{int(vals['ctlw_miss'])} | {int(vals['fault'])} |"
        )
    lines.append("")
    (OUT / f"OLDEN_{tag.upper()}_FS_SUMMARY.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(csv_path)
    print(OUT / f"OLDEN_{tag.upper()}_FS_SUMMARY.md")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="suite4_small")
    parser.add_argument("--kernels", nargs="*", default=DEFAULT_KERNELS)
    parser.add_argument("--extra-run", action="append", default=[])
    parser.add_argument(
        "--input-label",
        default="small (`treeadd 16 1`, `bisort 4096 1 0`, `mst 512`, `health 4 60 7`)",
    )
    args = parser.parse_args()
    rows = summarize(args.tag, args.kernels, args.extra_run)
    write_outputs(args.tag, rows, args.input_label)


if __name__ == "__main__":
    main()
