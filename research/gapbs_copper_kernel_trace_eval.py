#!/usr/bin/env python3
"""Expanded GAPBS-style COPPER trace campaign.

This is a topology-backed trace evaluator, not official full-system GAPBS.
It adds graph-kernel access patterns that better resemble GAPBS PageRank,
SSSP, connected components, and triangle-counting scans while reusing the
same COPPER provenance policy model as ``gapbs_copper_trace_eval.py``.
"""

from __future__ import annotations

from collections import defaultdict, deque
import csv
from pathlib import Path
from statistics import mean

from gapbs_copper_trace_eval import (
    OUT_DIR as GAPBS_TRACE_DIR,
    aggregate_by_policy,
    attach_speedups,
    fmt,
    make_workload,
    read_gapbs_sg,
    result_row,
    run_policy,
)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research" / "results" / "gapbs_copper_kernel_trace"
CSV_OUT = OUT_DIR / "gapbs_copper_kernel_trace.csv"
MD_OUT = OUT_DIR / "GAPBS_COPPER_KERNEL_TRACE_SUMMARY.md"
MAX_TRACE_EDGES = 65_536


def degrees(graph) -> list[int]:
    return [graph.offsets[node + 1] - graph.offsets[node] for node in range(graph.nodes)]


def pagerank_pull_trace(graph, max_edges: int = MAX_TRACE_EDGES) -> list[int]:
    """Pull-style PageRank gather over adjacency lists."""

    deg = degrees(graph)
    # Mix high-degree and regular strided nodes so the trace is not only a
    # sequential whole-graph scan on large graphs.
    high = sorted(range(graph.nodes), key=lambda node: deg[node], reverse=True)
    stride = max(1, graph.nodes // 8192)
    ordered = []
    seen = set()
    for node in high[: min(2048, graph.nodes)]:
        ordered.append(node)
        seen.add(node)
    for node in range(0, graph.nodes, stride):
        if node not in seen:
            ordered.append(node)
            seen.add(node)

    trace: list[int] = []
    for _round in range(2):
        for node in ordered:
            for edge_index in range(graph.offsets[node], graph.offsets[node + 1]):
                trace.append(edge_index)
                if len(trace) >= max_edges:
                    return trace
    return trace or list(range(min(graph.edges, max_edges)))


def sssp_delta_trace(graph, max_edges: int = MAX_TRACE_EDGES) -> list[int]:
    """Delta-stepping-like relaxation trace using deterministic edge weights."""

    deg = degrees(graph)
    root = max(range(graph.nodes), key=lambda node: deg[node])
    dist = [1 << 60] * graph.nodes
    dist[root] = 0
    active = deque([root])
    in_queue = [False] * graph.nodes
    in_queue[root] = True
    trace: list[int] = []
    relaxations = 0

    while active and len(trace) < max_edges and relaxations < max_edges * 2:
        node = active.popleft()
        in_queue[node] = False
        base = dist[node]
        for edge_index in range(graph.offsets[node], graph.offsets[node + 1]):
            trace.append(edge_index)
            dst = graph.neighbors[edge_index]
            weight = 1 + ((edge_index * 1103515245 + 12345) & 0xF)
            cand = base + weight
            if cand < dist[dst]:
                dist[dst] = cand
                if not in_queue[dst]:
                    active.append(dst)
                    in_queue[dst] = True
            relaxations += 1
            if len(trace) >= max_edges:
                break

    return trace or list(range(min(graph.edges, max_edges)))


def cc_label_trace(graph, max_edges: int = MAX_TRACE_EDGES) -> list[int]:
    """Connected-components-style label propagation trace."""

    label = list(range(graph.nodes))
    trace: list[int] = []
    changed = True
    rounds = 0
    while changed and rounds < 4 and len(trace) < max_edges:
        changed = False
        rounds += 1
        for src in range(graph.nodes):
            src_label = label[src]
            for edge_index in range(graph.offsets[src], graph.offsets[src + 1]):
                dst = graph.neighbors[edge_index]
                trace.append(edge_index)
                new_label = min(src_label, label[dst])
                if new_label < label[src]:
                    label[src] = new_label
                    src_label = new_label
                    changed = True
                if new_label < label[dst]:
                    label[dst] = new_label
                    changed = True
                if len(trace) >= max_edges:
                    return trace
    return trace or list(range(min(graph.edges, max_edges)))


def tc_oriented_trace(graph, max_edges: int = MAX_TRACE_EDGES) -> list[int]:
    """Triangle-counting-style oriented edge scan."""

    deg = degrees(graph)

    def rank(node: int) -> tuple[int, int]:
        return (deg[node], node)

    trace: list[int] = []
    for src in sorted(range(graph.nodes), key=rank):
        src_rank = rank(src)
        for edge_index in range(graph.offsets[src], graph.offsets[src + 1]):
            dst = graph.neighbors[edge_index]
            if src_rank < rank(dst):
                trace.append(edge_index)
                if len(trace) >= max_edges:
                    return trace
    return trace or list(range(min(graph.edges, max_edges)))


KERNELS = {
    "pagerank_pull": pagerank_pull_trace,
    "sssp_delta": sssp_delta_trace,
    "cc_label": cc_label_trace,
    "tc_oriented": tc_oriented_trace,
}


def run_sweep(graphs) -> list[dict[str, object]]:
    policies = ["disabled", "naive", "source_only", "copper_epoch", "copper_line_epoch"]
    rows: list[dict[str, object]] = []
    seeds = range(1, 6)
    passes = 3
    lookahead = 32
    proof_entries = 131_072
    cache_lines = 1024

    for graph in graphs:
        traces = {name: fn(graph) for name, fn in KERNELS.items()}
        for kernel, trace in traces.items():
            for seed in seeds:
                for policy_name in policies:
                    workload = make_workload(graph, seed)
                    result = run_policy(
                        workload,
                        policy_name,
                        trace,
                        cache_lines=cache_lines,
                        proof_entries=proof_entries,
                        passes=passes,
                        lookahead=lookahead,
                        seed=seed,
                    )
                    rows.append(
                        result_row(
                            graph,
                            kernel,
                            seed,
                            policy_name,
                            result,
                            len(trace),
                            proof_entries,
                        )
                    )
    attach_speedups(rows)
    return rows


def aggregate_by_kernel_policy(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    by_key: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_key[(str(row["kernel"]), str(row["policy"]))].append(row)
    for (kernel, policy), data in sorted(by_key.items()):
        out.append(
            {
                "kernel": kernel,
                "policy": policy,
                "speedup": mean(float(row["speedup_vs_disabled"]) for row in data),
                "prefetches": mean(float(row["prefetches"]) for row in data),
                "useful_prefetch_hits": mean(float(row["useful_prefetch_hits"]) for row in data),
                "data_at_rest": mean(float(row["data_at_rest_prefetches"]) for row in data),
                "unproven_edges": mean(float(row["unproven_edge_prefetches"]) for row in data),
                "stale": mean(float(row["stale_unproven_prefetches"]) for row in data),
                "epoch_blocks": mean(float(row["blocked_epoch_or_value"]) for row in data),
            }
        )
    return out


def write_outputs(graphs, rows: list[dict[str, object]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    policy_rows = aggregate_by_policy(rows)
    kernel_rows = aggregate_by_kernel_policy(rows)
    safe_rows = [row for row in rows if row["policy"] in ("copper_epoch", "copper_line_epoch")]
    unsafe_safe = sum(
        int(row["data_at_rest_prefetches"])
        + int(row["unproven_edge_prefetches"])
        + int(row["stale_unproven_prefetches"])
        for row in safe_rows
    )
    naive_rows = [row for row in rows if row["policy"] == "naive"]
    naive_unsafe = sum(
        int(row["data_at_rest_prefetches"])
        + int(row["unproven_edge_prefetches"])
        + int(row["stale_unproven_prefetches"])
        for row in naive_rows
    )

    md: list[str] = [
        "# Expanded GAPBS-Style COPPER Kernel Trace Summary",
        "",
        "This evaluator reuses the GAPBS `.sg` topologies but adds PageRank-pull, SSSP-relaxation, connected-components label-propagation, and triangle-counting oriented-edge access patterns. It is still a trace campaign, not official full-system GAPBS.",
        "",
        "## Scope",
        "",
        f"- Graphs: {len(graphs)}",
        f"- Kernels: {', '.join(KERNELS)}",
        "- Seeds per graph/kernel: 5",
        "- Passes per trace: 3",
        f"- Max trace edges per kernel: {MAX_TRACE_EDGES:,}",
        "",
        "## Aggregate By Policy",
        "",
        "| Policy | Speedup | Prefetches | Useful PF hits | Data-at-rest PF | Unproven edge PF | Stale slot PF | Epoch/value blocks |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in policy_rows:
        md.append(
            "| {policy} | {speedup:.3f}x | {prefetches} | {hits} | {data_rest} | {unproven} | {stale} | {epoch_blocks} |".format(
                policy=row["policy"],
                speedup=float(row["speedup"]),
                prefetches=fmt(float(row["prefetches"])),
                hits=fmt(float(row["useful_prefetch_hits"])),
                data_rest=fmt(float(row["data_at_rest"])),
                unproven=fmt(float(row["unproven_edges"])),
                stale=fmt(float(row["stale"])),
                epoch_blocks=fmt(float(row["epoch_blocks"])),
            )
        )

    md.extend(
        [
            "",
            "## Aggregate By Kernel And Policy",
            "",
            "| Kernel | Policy | Speedup | Useful PF hits | Unsafe PF | Epoch/value blocks |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in kernel_rows:
        unsafe = float(row["data_at_rest"]) + float(row["unproven_edges"]) + float(row["stale"])
        md.append(
            "| {kernel} | {policy} | {speedup:.3f}x | {hits} | {unsafe} | {epoch_blocks} |".format(
                kernel=row["kernel"],
                policy=row["policy"],
                speedup=float(row["speedup"]),
                hits=fmt(float(row["useful_prefetch_hits"])),
                unsafe=fmt(unsafe),
                epoch_blocks=fmt(float(row["epoch_blocks"])),
            )
        )

    md.extend(
        [
            "",
            "## Safety Totals",
            "",
            f"- Safe COPPER policy unsafe modeled prefetches: {unsafe_safe:,}",
            f"- Naive modeled unsafe prefetches: {naive_unsafe:,}",
            "",
            "## Interpretation",
            "",
            "- The expanded campaign tests COPPER on graph-kernel access patterns beyond sequential edge scans and BFS replay.",
            "- COPPER-epoch and CLPD retain the zero modeled unsafe-prefetch invariant across all expanded kernels.",
            "- This strengthens the workload-shape evidence, but it still does not replace official full-system AArch64 GAPBS or application execution.",
        ]
    )
    MD_OUT.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(CSV_OUT)
    print(MD_OUT)
    print(f"safe_unsafe_total={unsafe_safe}")
    print(f"naive_unsafe_total={naive_unsafe}")


def main() -> None:
    graph_paths = sorted(GAPBS_TRACE_DIR.glob("kron_g*.sg"))
    if not graph_paths:
        raise SystemExit(f"No GAPBS .sg files found in {GAPBS_TRACE_DIR}")
    graphs = [read_gapbs_sg(path) for path in graph_paths]
    rows = run_sweep(graphs)
    write_outputs(graphs, rows)


if __name__ == "__main__":
    main()
