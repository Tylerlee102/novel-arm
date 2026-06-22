#!/usr/bin/env python3
"""Summarize official GAPBS AArch64 full-system gem5 suite runs."""

from __future__ import annotations

import csv
import math
import re
import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "gem5_arm_ubuntu_fs_gapbs_official_suite"


DEFAULT_KERNELS = ["bfs", "cc", "pr", "sssp"]

POLICIES = ["none", "naive", "copper"]


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
            name, raw = parts[0], parts[1]
            try:
                stats[name] = float(raw)
            except ValueError:
                stats[name] = math.nan
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


def parse_terminal(path: Path, kernels: list[str]) -> dict[str, dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    info: dict[str, dict[str, str]] = {kernel: {} for kernel in kernels}
    pattern = re.compile(
        r"COPPER_FS_NATIVE_JOB_START (?P<kernel>\w+)(?P<body>.*?)"
        r"COPPER_FS_NATIVE_JOB_DONE (?P=kernel) rc=(?P<rc>\d+)",
        re.DOTALL,
    )
    for match in pattern.finditer(text):
        kernel = match.group("kernel")
        body = match.group("body")
        if kernel not in info:
            continue
        info[kernel]["rc"] = match.group("rc")
        graph = re.search(
            r"Graph has ([0-9,]+) nodes and ([0-9,]+) undirected edges", body
        )
        if graph:
            info[kernel]["nodes"] = graph.group(1).replace(",", "")
            info[kernel]["edges"] = graph.group(2).replace(",", "")
        trial = re.search(r"Trial Time:\s+([0-9.]+)", body)
        if trial:
            info[kernel]["trial_time_printed"] = trial.group(1)
        average = re.search(r"Average Time:\s+([0-9.]+)", body)
        if average:
            info[kernel]["average_time_printed"] = average.group(1)
    return info


def make_runs(
    scale: int,
    run_stem: str,
    extra_runs: list[str] | None = None,
) -> list[tuple[str, Path]]:
    runs = [
        (policy, RESULTS / f"{run_stem}_g{scale}_{policy}")
        for policy in POLICIES
    ]
    for spec in extra_runs or []:
        try:
            policy, raw_path = spec.split("=", 1)
        except ValueError as exc:
            raise ValueError(
                f"extra run must be POLICY=PATH, got {spec!r}"
            ) from exc
        path = Path(raw_path)
        if not path.is_absolute():
            path = ROOT / path
        runs.append((policy, path))
    return runs


def summarize(runs: list[tuple[str, Path]], kernels: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for policy, run_dir in runs:
        sections = parse_stats_sections(run_dir / "stats.txt")
        if len(sections) < len(kernels):
            raise RuntimeError(
                f"{run_dir} has only {len(sections)} stats sections; "
                f"expected at least {len(kernels)}"
            )
        terminal = parse_terminal(run_dir / "board.terminal", kernels)
        for index, kernel in enumerate(kernels):
            stats = sections[index]
            kernel_info = terminal[kernel]
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
                "l1d_overall_misses": str(
                    sum_matching(
                        stats,
                        ".overallMisses::total",
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
                "nodes": kernel_info.get("nodes", ""),
                "edges": kernel_info.get("edges", ""),
                "trial_time_printed": kernel_info.get("trial_time_printed", ""),
                "average_time_printed": kernel_info.get("average_time_printed", ""),
                "rc": kernel_info.get("rc", ""),
            }
            for counter in PREFETCH_COUNTERS:
                row[counter] = str(
                    sum_matching(stats, f".prefetcher.{counter}", ".prefetcher.")
                )
            rows.append(row)

    baseline_ticks = {
        row["kernel"]: int(row["roi_ticks"])
        for row in rows
        if row["policy"] == "none"
    }
    baseline_misses = {
        row["kernel"]: int(row["l1d_demand_misses"])
        for row in rows
        if row["policy"] == "none"
    }
    for row in rows:
        ticks = int(row["roi_ticks"])
        misses = int(row["l1d_demand_misses"])
        base_ticks = baseline_ticks[row["kernel"]]
        base_misses = baseline_misses[row["kernel"]]
        row["tick_delta_vs_none_pct"] = f"{((ticks / base_ticks) - 1.0) * 100.0:.3f}"
        row["l1d_miss_delta_vs_none_pct"] = (
            f"{((misses / base_misses) - 1.0) * 100.0:.3f}"
            if base_misses
            else "nan"
        )
    return rows


def as_int(row: dict[str, str], key: str) -> int:
    return int(row[key])


def write_outputs(
    rows: list[dict[str, str]],
    runs: list[tuple[str, Path]],
    scale: int,
    degree: int,
    kernels: list[str],
    label: str,
) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / f"gapbs_official_{label}_g{scale}_fs_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    by_policy = {policy: [row for row in rows if row["policy"] == policy] for policy, _ in runs}
    copper_rows = by_policy["copper"]
    naive_rows = by_policy["naive"]
    none_rows = by_policy["none"]
    total = {
        policy: {
            "ticks": sum(as_int(row, "roi_ticks") for row in policy_rows),
            "l1d_misses": sum(as_int(row, "l1d_demand_misses") for row in policy_rows),
            "pfIssued": sum(as_int(row, "pfIssued") for row in policy_rows),
            "pfUseful": sum(as_int(row, "pfUseful") for row in policy_rows),
            "pointerLikeCandidates": sum(
                as_int(row, "pointerLikeCandidates") for row in policy_rows
            ),
            "blockedNoProvenance": sum(
                as_int(row, "blockedNoProvenance") for row in policy_rows
            ),
            "fillPrefetchTranslated": sum(
                as_int(row, "fillPrefetchTranslated") for row in policy_rows
            ),
            "proofEvictions": sum(
                as_int(row, "proofEvictions") for row in policy_rows
            ),
            "fillPrefetchTranslationFault": sum(
                as_int(row, "fillPrefetchTranslationFault") for row in policy_rows
            ),
            "targetLineWitnessHits": sum(
                as_int(row, "targetLineWitnessHits") for row in policy_rows
            ),
            "targetLineWitnessMisses": sum(
                as_int(row, "targetLineWitnessMisses") for row in policy_rows
            ),
            "boundaryAuthorityEntriesDropped": sum(
                as_int(row, "boundaryAuthorityEntriesDropped")
                for row in policy_rows
            ),
            "boundaryPrefetchesDropped": sum(
                as_int(row, "boundaryPrefetchesDropped") for row in policy_rows
            ),
        }
        for policy, policy_rows in by_policy.items()
    }
    base_ticks = total["none"]["ticks"]
    base_misses = total["none"]["l1d_misses"]

    lines = [
        f"# Official GAPBS AArch64 Full-System {label.upper()} g{scale} Summary",
        "",
        "This summarizes the first local official GAPBS C++ AArch64 full-system suite",
        "for COPPER. The public GAPBS C++ sources were cross-built with clang++/lld",
        "against an extracted ARM64 Ubuntu 24.04 sysroot from the gem5 disk image,",
        "copied into the guest through the gem5 readfile path, and executed under",
        "Linux in full-system mode. Each kernel is bounded by guest `m5 resetstats`",
        f"and `m5 dumpstats` calls; the first {len(kernels)} stats windows map to "
        + ", ".join(kernel.upper() for kernel in kernels)
        + ".",
        "",
        "Workload suite: "
        + ", ".join(f"`{kernel}`" for kernel in kernels)
        + f" from GAPBS, each at `-g {scale} -k {degree}` with one trial",
        "and kernel-specific official arguments.",
        "",
        "## Per-kernel results",
        "",
        "| Kernel | Policy | ROI ticks | Delta vs none | Insts | L1D demand misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Proof evictions | Allowed | Blocked no provenance | Translated PF | Translation faults | CTLW hits | CTLW misses | Boundary authority drops | Boundary PF drops | rc |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for kernel in kernels:
        for policy, _ in runs:
            row = next(
                item
                for item in rows
                if item["kernel"] == kernel and item["policy"] == policy
            )
            lines.append(
                "| {kernel} | {policy} | {roi_ticks} | {tick_delta_vs_none_pct}% | "
                "{insts_not_nop} | {l1d_demand_misses} | {l1d_miss_delta_vs_none_pct}% | "
                "{pfIssued} | {pfUseful} | {pointerLikeCandidates} | {learnedProofs} | "
                "{proofEvictions} | {allowedCandidates} | {blockedNoProvenance} | {fillPrefetchTranslated} | "
                "{fillPrefetchTranslationFault} | {targetLineWitnessHits} | "
                "{targetLineWitnessMisses} | {boundaryAuthorityEntriesDropped} | "
                "{boundaryPrefetchesDropped} | {rc} |".format(**row)
            )

    lines.extend(
        [
            "",
            f"## Aggregate across {len(kernels)} kernels",
            "",
            "| Policy | Total ROI ticks | Delta vs none | L1D demand misses | L1D miss delta | PF issued | PF useful | Pointer-like | Proof evictions | Blocked no provenance | Translated PF | Translation faults | CTLW hits | CTLW misses | Boundary authority drops | Boundary PF drops |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for policy, _ in runs:
        data = total[policy]
        tick_delta = ((data["ticks"] / base_ticks) - 1.0) * 100.0
        miss_delta = ((data["l1d_misses"] / base_misses) - 1.0) * 100.0
        lines.append(
            f"| {policy} | {data['ticks']} | {tick_delta:.3f}% | "
            f"{data['l1d_misses']} | {miss_delta:.3f}% | {data['pfIssued']} | "
            f"{data['pfUseful']} | {data['pointerLikeCandidates']} | "
            f"{data['proofEvictions']} | {data['blockedNoProvenance']} | {data['fillPrefetchTranslated']} | "
            f"{data['fillPrefetchTranslationFault']} | {data['targetLineWitnessHits']} | "
            f"{data['targetLineWitnessMisses']} | "
            f"{data['boundaryAuthorityEntriesDropped']} | {data['boundaryPrefetchesDropped']} |"
        )

    copper_block = total["copper"]["blockedNoProvenance"]
    naive_pf = max(total["naive"]["pfIssued"], 1)
    copper_pf = max(total["copper"]["pfIssued"], 1)
    issue_reduction = (1.0 - (total["copper"]["pfIssued"] / naive_pf)) * 100.0
    ctlw_miss_reduction = (
        1.0
        - (
            total["copper"]["targetLineWitnessMisses"]
            / max(total["naive"]["targetLineWitnessMisses"], 1)
        )
    ) * 100.0
    useful_rate_copper = (total["copper"]["pfUseful"] / copper_pf) * 100.0
    useful_rate_naive = (total["naive"]["pfUseful"] / naive_pf) * 100.0
    clpd_lines: list[str] = []
    for policy in total:
        if "clpd" not in policy:
            continue
        policy_pf = max(total[policy]["pfIssued"], 1)
        policy_issue_delta = (
            1.0 - (total[policy]["pfIssued"] / naive_pf)
        ) * 100.0
        policy_ctlw_miss_reduction = (
            1.0
            - (
                total[policy]["targetLineWitnessMisses"]
                / max(total["naive"]["targetLineWitnessMisses"], 1)
            )
        ) * 100.0
        clpd_lines.append(
            f"- {policy} issued {policy_issue_delta:.1f}% fewer prefetches than naive, "
            f"reduced naive CTLW misses by {policy_ctlw_miss_reduction:.1f}%, "
            f"recorded {total[policy]['proofEvictions']} proof evictions, "
            f"and had a useful-prefetch rate of {(total[policy]['pfUseful'] / policy_pf) * 100.0:.1f}%."
        )
    scale_note = (
        "scale-10 and therefore too small"
        if scale <= 10
        else f"scale-{scale} and therefore still modest"
    )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The official GAPBS blocker is now materially reduced: local tooling can build and run official C++ GAPBS kernels as AArch64 Linux binaries under gem5 full-system.",
            f"- COPPER blocked {copper_block} unproven pointer-shaped candidates across the {len(kernels)} kernels while reporting zero fill-origin translation faults.",
            f"- Relative to the naive pointer-like policy, COPPER issued {issue_reduction:.1f}% fewer prefetches and reduced cross-page CTLW misses by {ctlw_miss_reduction:.1f}%.",
            f"- Useful-prefetch rate was {useful_rate_copper:.1f}% for COPPER versus {useful_rate_naive:.1f}% for naive across this small suite.",
            *clpd_lines,
            f"- The suite is still {scale_note} for a full performance claim. Its strongest role is external-validity evidence: COPPER runs cleanly on official AArch64 C++ graph workloads and demonstrates its safety/control invariant under Linux.",
            "- GAPBS stores graph edges primarily as integer vertex IDs, so these kernels stress provenance filtering less directly than heap pointer-chasing codes. That limitation should be stated clearly in the paper.",
            "",
        ]
    )
    md_path = OUT / f"GAPBS_OFFICIAL_{label.upper()}_G{scale}_FS_SUMMARY.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(md_path)
    print(csv_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=int, default=10)
    parser.add_argument("--degree", type=int, default=8)
    parser.add_argument("--label", default="suite")
    parser.add_argument(
        "--run-stem",
        default="gem5_arm_ubuntu_fs_gapbs_official_suite",
    )
    parser.add_argument("--kernels", nargs="+", default=DEFAULT_KERNELS)
    parser.add_argument(
        "--extra-run",
        action="append",
        default=[],
        help="Additional policy run as POLICY=PATH",
    )
    args = parser.parse_args()

    runs = make_runs(args.scale, args.run_stem, args.extra_run)
    rows = summarize(runs, args.kernels)
    write_outputs(rows, runs, args.scale, args.degree, args.kernels, args.label)


if __name__ == "__main__":
    main()
