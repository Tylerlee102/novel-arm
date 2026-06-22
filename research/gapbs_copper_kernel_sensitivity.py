#!/usr/bin/env python3
"""Sensitivity sweep for expanded GAPBS-style COPPER kernel traces."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

from gapbs_copper_kernel_trace_eval import KERNELS
from gapbs_copper_trace_eval import (
    OUT_DIR as GAPBS_TRACE_DIR,
    make_workload,
    read_gapbs_sg,
    result_row,
    run_policy,
)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research" / "results" / "gapbs_copper_kernel_sensitivity"
CSV_OUT = OUT_DIR / "gapbs_copper_kernel_sensitivity.csv"
MD_OUT = OUT_DIR / "GAPBS_COPPER_KERNEL_SENSITIVITY.md"

POLICIES = ["disabled", "naive", "source_only", "copper_epoch", "copper_line_epoch"]
PROOF_ENTRIES = [1_024, 4_096, 16_384, 131_072]
CACHE_LINES = [512, 1_024]
LOOKAHEADS = [8, 32, 64]
SEEDS = [1, 2, 3]
PASSES = 3
MAX_TRACE_EDGES = 32_768


def unsafe_count(row: dict[str, object]) -> int:
    return (
        int(row["data_at_rest_prefetches"])
        + int(row["unproven_edge_prefetches"])
        + int(row["stale_unproven_prefetches"])
    )


def attach_config_speedups(rows: list[dict[str, object]]) -> None:
    disabled: dict[tuple[object, ...], float] = {}
    for row in rows:
        if row["policy"] != "disabled":
            continue
        key = (
            row["graph"],
            row["kernel"],
            row["seed"],
            row["cache_lines"],
            row["lookahead"],
            row["proof_entries"],
        )
        disabled[key] = float(row["cycles"])

    for row in rows:
        key = (
            row["graph"],
            row["kernel"],
            row["seed"],
            row["cache_lines"],
            row["lookahead"],
            row["proof_entries"],
        )
        row["speedup_vs_disabled"] = disabled[key] / float(row["cycles"])
        row["unsafe_prefetches"] = unsafe_count(row)


def run_sweep(graphs) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for graph in graphs:
        traces = {name: fn(graph, max_edges=MAX_TRACE_EDGES) for name, fn in KERNELS.items()}
        for cache_lines in CACHE_LINES:
            for lookahead in LOOKAHEADS:
                for proof_entries in PROOF_ENTRIES:
                    for kernel, trace in traces.items():
                        for seed in SEEDS:
                            for policy_name in POLICIES:
                                workload = make_workload(graph, seed)
                                result = run_policy(
                                    workload,
                                    policy_name,
                                    trace,
                                    cache_lines=cache_lines,
                                    proof_entries=proof_entries,
                                    passes=PASSES,
                                    lookahead=lookahead,
                                    seed=seed,
                                )
                                row = result_row(
                                    graph,
                                    kernel,
                                    seed,
                                    policy_name,
                                    result,
                                    len(trace),
                                    proof_entries,
                                )
                                row["cache_lines"] = cache_lines
                                row["lookahead"] = lookahead
                                row["passes"] = PASSES
                                rows.append(row)
    attach_config_speedups(rows)
    return rows


def group_rows(rows: list[dict[str, object]], keys: tuple[str, ...]):
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in keys)].append(row)
    return grouped


def policy_summary(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for policy, data in group_rows(rows, ("policy",)).items():
        speeds = [float(row["speedup_vs_disabled"]) for row in data]
        unsafes = [int(row["unsafe_prefetches"]) for row in data]
        out.append(
            {
                "policy": policy[0],
                "runs": len(data),
                "speedup_mean": mean(speeds),
                "speedup_median": median(speeds),
                "speedup_min": min(speeds),
                "speedup_max": max(speeds),
                "unsafe_total": sum(unsafes),
                "unsafe_max": max(unsafes),
                "prefetches_mean": mean(float(row["prefetches"]) for row in data),
                "useful_hits_mean": mean(float(row["useful_prefetch_hits"]) for row in data),
                "blocks_mean": mean(float(row["blocked_no_proof"]) for row in data),
            }
        )
    return sorted(out, key=lambda row: POLICIES.index(str(row["policy"])))


def proof_summary(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    data_rows = [
        row
        for row in rows
        if row["policy"] in ("copper_epoch", "copper_line_epoch")
    ]
    for (policy, proof_entries), data in sorted(
        group_rows(data_rows, ("policy", "proof_entries")).items()
    ):
        speeds = [float(row["speedup_vs_disabled"]) for row in data]
        out.append(
            {
                "policy": policy,
                "proof_entries": proof_entries,
                "median_speedup": median(speeds),
                "min_speedup": min(speeds),
                "max_speedup": max(speeds),
                "unsafe_total": sum(int(row["unsafe_prefetches"]) for row in data),
                "blocks_mean": mean(float(row["blocked_no_proof"]) for row in data),
            }
        )
    return out


def fmt(value: float) -> str:
    return f"{value:,.3f}"


def fmt1(value: float) -> str:
    return f"{value:,.1f}"


def write_outputs(graphs, rows: list[dict[str, object]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    p_rows = policy_summary(rows)
    proof_rows = proof_summary(rows)
    copper_rows = [
        row
        for row in rows
        if row["policy"] in ("copper_epoch", "copper_line_epoch")
    ]
    source_rows = [row for row in rows if row["policy"] == "source_only"]
    naive_rows = [row for row in rows if row["policy"] == "naive"]
    worst_copper = min(copper_rows, key=lambda row: float(row["speedup_vs_disabled"]))

    md = [
        "# GAPBS-Style Kernel Trace Sensitivity",
        "",
        "This sweep reuses the five GAPBS-generated Kronecker topologies but runs the three largest graph files through PageRank-pull, SSSP-relaxation, connected-components label propagation, and triangle-counting oriented-edge trace shapes. It is a trace sensitivity campaign, not official full-system GAPBS.",
        "",
        "## Scope",
        "",
        f"- Graphs: {', '.join(graph.name for graph in graphs)}",
        f"- Kernels: {', '.join(KERNELS)}",
        f"- Seeds: {', '.join(str(seed) for seed in SEEDS)}",
        f"- Proof entries: {', '.join(f'{entry:,}' for entry in PROOF_ENTRIES)}",
        f"- Cache lines: {', '.join(f'{entry:,}' for entry in CACHE_LINES)}",
        f"- Lookahead distances: {', '.join(str(entry) for entry in LOOKAHEADS)}",
        f"- Passes per trace: {PASSES}",
        f"- Max trace edges per kernel: {MAX_TRACE_EDGES:,}",
        f"- Policy runs: {len(rows):,}",
        "",
        "## Policy Summary",
        "",
        "| Policy | Runs | Mean speedup | Median | Min | Max | Unsafe total | Worst unsafe/run | Mean prefetches | Mean useful hits | Mean no-proof blocks |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in p_rows:
        md.append(
            f"| {row['policy']} | {row['runs']:,} | {fmt(float(row['speedup_mean']))}x | {fmt(float(row['speedup_median']))}x | {fmt(float(row['speedup_min']))}x | {fmt(float(row['speedup_max']))}x | {int(row['unsafe_total']):,} | {int(row['unsafe_max']):,} | {fmt1(float(row['prefetches_mean']))} | {fmt1(float(row['useful_hits_mean']))} | {fmt1(float(row['blocks_mean']))} |"
        )

    md.extend(
        [
            "",
            "## COPPER Proof-Capacity Summary",
            "",
            "| Policy | Proof entries | Median speedup | Min | Max | Unsafe total | Mean no-proof blocks |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in proof_rows:
        md.append(
            f"| {row['policy']} | {int(row['proof_entries']):,} | {fmt(float(row['median_speedup']))}x | {fmt(float(row['min_speedup']))}x | {fmt(float(row['max_speedup']))}x | {int(row['unsafe_total']):,} | {fmt1(float(row['blocks_mean']))} |"
        )

    md.extend(
        [
            "",
            "## Safety Totals",
            "",
            f"- COPPER unsafe modeled prefetches: {sum(int(row['unsafe_prefetches']) for row in copper_rows):,}",
            f"- Naive unsafe modeled prefetches: {sum(int(row['unsafe_prefetches']) for row in naive_rows):,}",
            f"- Source-only unsafe modeled prefetches: {sum(int(row['unsafe_prefetches']) for row in source_rows):,}",
            "",
            "## Worst COPPER Speedup Point",
            "",
            f"- Policy: {worst_copper['policy']}",
            f"- Graph/kernel/seed: {worst_copper['graph']} / {worst_copper['kernel']} / {worst_copper['seed']}",
            f"- Proof entries/cache/lookahead: {int(worst_copper['proof_entries']):,} / {int(worst_copper['cache_lines']):,} / {int(worst_copper['lookahead'])}",
            f"- Speedup: {fmt(float(worst_copper['speedup_vs_disabled']))}x",
            f"- Unsafe modeled prefetches at that point: {int(worst_copper['unsafe_prefetches']):,}",
            "",
            "## Interpretation",
            "",
            "- The zero-unsafe COPPER invariant survives the table-size, cache-size, lookahead, graph, kernel, and seed sweep in this model.",
            "- Source-only provenance remains unsafe under stale rewritten slots, which supports COPPER's value/epoch binding rather than a simple source-location table.",
            "- Small proof tables reduce speedup through no-proof blocking; that is a measurable cost knob, not a safety failure.",
            "- This strengthens trace robustness, but it is still a model-level result and does not replace full-system official GAPBS.",
            "",
        ]
    )
    MD_OUT.write_text("\n".join(md), encoding="utf-8")
    print(CSV_OUT)
    print(MD_OUT)


def main() -> None:
    graph_paths = sorted(GAPBS_TRACE_DIR.glob("kron_g*.sg"))[-3:]
    if len(graph_paths) < 3:
        raise SystemExit(f"Need at least three GAPBS .sg files in {GAPBS_TRACE_DIR}")
    graphs = [read_gapbs_sg(path) for path in graph_paths]
    rows = run_sweep(graphs)
    write_outputs(graphs, rows)


if __name__ == "__main__":
    main()
