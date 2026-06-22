#!/usr/bin/env python3
"""COPPER trace evaluation over public GAPBS serialized graph files.

This is not a full-system GAPBS run. It is a topology-backed trace evaluator:
the edge streams come from GAPBS-generated ``.sg`` CSR graphs, and the policy
under test decides whether a data-memory-dependent prefetch may dereference the
edge slot's node ID as a node-property address.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import csv
import random
import struct
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research" / "results" / "gapbs_copper_trace"
BASE = 0x5000_0000
NODE_STRIDE = 64
SOURCE_LINE_BYTES = 64
SOURCE_SLOT_BYTES = 4
SOURCE_SLOTS_PER_LINE = SOURCE_LINE_BYTES // SOURCE_SLOT_BYTES
HIT = 4
MISS = 100
PREFETCH_FILL = 8


@dataclass(frozen=True)
class GapbsGraph:
    name: str
    directed: bool
    nodes: int
    edges: int
    offsets: list[int]
    neighbors: list[int]


@dataclass
class TraceWorkload:
    graph: GapbsGraph
    targets: list[int]
    epochs: list[int]
    line_epochs: list[int]
    adversarial_values: list[int]
    mutate_slots: list[int]


class LruCache:
    def __init__(self, lines: int) -> None:
        self.lines = lines
        self.data: OrderedDict[int, bool] = OrderedDict()

    def prefetch(self, addr: int) -> bool:
        line = addr // NODE_STRIDE
        if line in self.data:
            self.data.move_to_end(line)
            return False
        self.data[line] = True
        if len(self.data) > self.lines:
            self.data.popitem(last=False)
        return True

    def demand(self, addr: int) -> tuple[bool, bool]:
        line = addr // NODE_STRIDE
        if line in self.data:
            prefetched = self.data[line]
            self.data[line] = False
            self.data.move_to_end(line)
            return True, prefetched
        self.data[line] = False
        if len(self.data) > self.lines:
            self.data.popitem(last=False)
        return False, False


class GraphPolicy:
    def __init__(
        self,
        name: str,
        workload: TraceWorkload,
        cache_lines: int,
        proof_entries: int,
    ) -> None:
        self.name = name
        self.workload = workload
        self.cache = LruCache(cache_lines)
        self.proofs: OrderedDict[tuple[int, int, int], None] = OrderedDict()
        self.source_only_proofs: OrderedDict[int, None] = OrderedDict()
        self.line_proofs: OrderedDict[tuple[int, int], int] = OrderedDict()
        self.line_seen: set[int] = set()
        self.proof_entries = proof_entries
        self.cycles = 0
        self.demand_misses = 0
        self.demand_hits = 0
        self.prefetches = 0
        self.prefetch_fills = 0
        self.useful_prefetch_hits = 0
        self.data_at_rest_prefetches = 0
        self.unproven_edge_prefetches = 0
        self.stale_unproven_prefetches = 0
        self.blocked_no_proof = 0
        self.blocked_epoch_or_value = 0

    def _remember(self, table: OrderedDict, key) -> None:
        if self.proof_entries <= 0:
            return
        table[key] = None
        table.move_to_end(key)
        while len(table) > self.proof_entries:
            table.popitem(last=False)

    def _full_key(self, edge_index: int) -> tuple[int, int, int]:
        return (
            edge_index,
            self.workload.targets[edge_index],
            self.workload.epochs[edge_index],
        )

    def _line_id(self, edge_index: int) -> int:
        return edge_index // SOURCE_SLOTS_PER_LINE

    def _line_bit(self, edge_index: int) -> int:
        return edge_index % SOURCE_SLOTS_PER_LINE

    def _line_key(self, edge_index: int) -> tuple[int, int]:
        line_id = self._line_id(edge_index)
        return (line_id, self.workload.line_epochs[line_id])

    def _remember_line(self, edge_index: int) -> None:
        if self.proof_entries <= 0:
            return
        key = self._line_key(edge_index)
        bit = 1 << self._line_bit(edge_index)
        self.line_proofs[key] = self.line_proofs.get(key, 0) | bit
        self.line_proofs.move_to_end(key)
        self.line_seen.add(key[0])
        while len(self.line_proofs) > self.proof_entries:
            self.line_proofs.popitem(last=False)

    def _line_proven(self, edge_index: int) -> bool:
        key = self._line_key(edge_index)
        bit = 1 << self._line_bit(edge_index)
        return bool(self.line_proofs.get(key, 0) & bit)

    def learn_edge(self, edge_index: int) -> None:
        self._remember(self.source_only_proofs, edge_index)
        self._remember(self.proofs, self._full_key(edge_index))
        self._remember_line(edge_index)

    def mutate_edge(self, edge_index: int, new_target: int) -> None:
        old_target = self.workload.targets[edge_index]
        if new_target == old_target:
            new_target += NODE_STRIDE
        self.workload.targets[edge_index] = new_target
        self.workload.epochs[edge_index] = (self.workload.epochs[edge_index] + 1) & 0xFF
        line_id = self._line_id(edge_index)
        self.workload.line_epochs[line_id] = (
            self.workload.line_epochs[line_id] + 1
        ) & 0xFF

    def maybe_prefetch_edge(self, edge_index: int) -> None:
        if self.name == "disabled":
            return

        source_proven = edge_index in self.source_only_proofs
        full_proven = self._full_key(edge_index) in self.proofs
        line_proven = self._line_proven(edge_index)
        allowed = False
        if self.name == "naive":
            allowed = True
        elif self.name == "source_only":
            allowed = source_proven
        elif self.name == "copper_epoch":
            allowed = full_proven
        elif self.name == "copper_line_epoch":
            allowed = line_proven
            full_proven = line_proven
        else:
            raise ValueError(self.name)

        if not allowed:
            self.blocked_no_proof += 1
            if self.name == "copper_epoch" and source_proven:
                self.blocked_epoch_or_value += 1
            if self.name == "copper_line_epoch" and self._line_id(edge_index) in self.line_seen:
                self.blocked_epoch_or_value += 1
            return

        if not full_proven:
            self.unproven_edge_prefetches += 1
            if source_proven:
                self.stale_unproven_prefetches += 1

        self.prefetches += 1
        if self.cache.prefetch(self.workload.targets[edge_index]):
            self.prefetch_fills += 1
            self.cycles += PREFETCH_FILL

    def maybe_prefetch_adversarial(self, value: int) -> None:
        if self.name == "disabled":
            return
        if self.name == "naive":
            self.prefetches += 1
            self.data_at_rest_prefetches += 1
            if self.cache.prefetch(value):
                self.prefetch_fills += 1
                self.cycles += PREFETCH_FILL
            return
        self.blocked_no_proof += 1

    def demand_edge_target(self, edge_index: int) -> None:
        hit, prefetched = self.cache.demand(self.workload.targets[edge_index])
        if hit:
            self.cycles += HIT
            self.demand_hits += 1
            if prefetched:
                self.useful_prefetch_hits += 1
        else:
            self.cycles += MISS
            self.demand_misses += 1
        self.learn_edge(edge_index)


def read_gapbs_sg(path: Path) -> GapbsGraph:
    raw = path.read_bytes()
    if len(raw) < 17:
        raise ValueError(f"{path} is too small to be a GAPBS .sg file")

    directed = bool(raw[0])
    edges, nodes = struct.unpack_from("<qq", raw, 1)
    if nodes <= 0 or edges < 0:
        raise ValueError(f"{path} has invalid header nodes={nodes} edges={edges}")

    offset_start = 17
    offset_bytes = (nodes + 1) * 8
    neighbor_start = offset_start + offset_bytes
    neighbor_bytes = edges * 4
    expected = neighbor_start + neighbor_bytes
    if directed:
        expected += offset_bytes + neighbor_bytes
    if len(raw) != expected:
        raise ValueError(
            f"{path} size mismatch: got {len(raw)} bytes, expected {expected}"
        )

    offsets = list(struct.unpack_from(f"<{nodes + 1}q", raw, offset_start))
    neighbors = list(struct.unpack_from(f"<{edges}i", raw, neighbor_start))
    if offsets[0] != 0 or offsets[-1] != edges:
        raise ValueError(f"{path} has invalid CSR offsets")
    if any(offsets[i] > offsets[i + 1] for i in range(nodes)):
        raise ValueError(f"{path} has decreasing CSR offsets")
    if any(neighbor < 0 or neighbor >= nodes for neighbor in neighbors):
        raise ValueError(f"{path} has neighbor IDs outside node range")

    return GapbsGraph(
        name=path.stem,
        directed=directed,
        nodes=nodes,
        edges=edges,
        offsets=offsets,
        neighbors=neighbors,
    )


def make_workload(
    graph: GapbsGraph,
    seed: int,
    adversarial_count: int = 4096,
    mutate_fraction: float = 0.02,
) -> TraceWorkload:
    rng = random.Random(seed)
    node_addrs = [BASE + index * NODE_STRIDE for index in range(graph.nodes + 1)]
    targets = [node_addrs[neighbor] for neighbor in graph.neighbors]
    epochs = [0] * graph.edges
    line_count = (graph.edges + SOURCE_SLOTS_PER_LINE - 1) // SOURCE_SLOTS_PER_LINE
    line_epochs = [0] * line_count
    adversarial_values = [
        node_addrs[rng.randrange(graph.nodes)] for _ in range(adversarial_count)
    ]
    mutate_count = max(1, int(graph.edges * mutate_fraction))
    mutate_slots = rng.sample(range(graph.edges), min(mutate_count, graph.edges))
    return TraceWorkload(graph, targets, epochs, line_epochs, adversarial_values, mutate_slots)


def edge_scan_trace(graph: GapbsGraph) -> list[int]:
    return list(range(graph.edges))


def bfs_replay_trace(graph: GapbsGraph, max_edges: int = 65536) -> list[int]:
    degrees = [graph.offsets[node + 1] - graph.offsets[node] for node in range(graph.nodes)]
    roots = sorted(range(graph.nodes), key=lambda node: degrees[node], reverse=True)[:8]
    visited = [False] * graph.nodes
    trace: list[int] = []

    for root in roots:
        if visited[root]:
            continue
        frontier = [root]
        visited[root] = True
        while frontier and len(trace) < max_edges:
            next_frontier: list[int] = []
            for src in frontier:
                begin = graph.offsets[src]
                end = graph.offsets[src + 1]
                for edge_index in range(begin, end):
                    trace.append(edge_index)
                    dst = graph.neighbors[edge_index]
                    if not visited[dst]:
                        visited[dst] = True
                        next_frontier.append(dst)
                    if len(trace) >= max_edges:
                        break
                if len(trace) >= max_edges:
                    break
            frontier = next_frontier
        if len(trace) >= max_edges:
            break

    if not trace:
        return list(range(min(graph.edges, max_edges)))
    return trace


def run_policy(
    workload: TraceWorkload,
    policy_name: str,
    trace: list[int],
    cache_lines: int,
    proof_entries: int,
    passes: int,
    lookahead: int,
    seed: int,
) -> GraphPolicy:
    policy = GraphPolicy(policy_name, workload, cache_lines, proof_entries)
    rng = random.Random(10000 + seed + workload.graph.edges)
    node_count = workload.graph.nodes

    for pass_index in range(passes):
        if pass_index == 2:
            for edge_index in workload.mutate_slots:
                new_node = rng.randrange(node_count)
                policy.mutate_edge(edge_index, BASE + new_node * NODE_STRIDE)

        for value in workload.adversarial_values:
            policy.maybe_prefetch_adversarial(value)

        for pos, edge_index in enumerate(trace):
            pf_pos = pos + lookahead
            if pf_pos < len(trace):
                policy.maybe_prefetch_edge(trace[pf_pos])
            policy.demand_edge_target(edge_index)

    return policy


def result_row(
    graph: GapbsGraph,
    kernel: str,
    seed: int,
    policy_name: str,
    result: GraphPolicy,
    trace_len: int,
    proof_entries: int,
) -> dict[str, object]:
    return {
        "graph": graph.name,
        "nodes": graph.nodes,
        "edges": graph.edges,
        "directed": int(graph.directed),
        "kernel": kernel,
        "trace_edges": trace_len,
        "seed": seed,
        "policy": policy_name,
        "proof_entries": proof_entries,
        "cycles": result.cycles,
        "demand_misses": result.demand_misses,
        "demand_hits": result.demand_hits,
        "prefetches": result.prefetches,
        "prefetch_fills": result.prefetch_fills,
        "useful_prefetch_hits": result.useful_prefetch_hits,
        "data_at_rest_prefetches": result.data_at_rest_prefetches,
        "unproven_edge_prefetches": result.unproven_edge_prefetches,
        "stale_unproven_prefetches": result.stale_unproven_prefetches,
        "blocked_no_proof": result.blocked_no_proof,
        "blocked_epoch_or_value": result.blocked_epoch_or_value,
    }


def run_main_sweep(graphs: list[GapbsGraph]) -> list[dict[str, object]]:
    policies = ["disabled", "naive", "source_only", "copper_epoch", "copper_line_epoch"]
    rows: list[dict[str, object]] = []
    seeds = range(1, 6)
    passes = 4
    lookahead = 32
    proof_entries = 131072
    cache_lines = 1024

    for graph in graphs:
        traces = {
            "edge_scan": edge_scan_trace(graph),
            "bfs_replay": bfs_replay_trace(graph),
        }
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


def run_capacity_sweep(graph: GapbsGraph) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    trace = edge_scan_trace(graph)
    seed = 1
    passes = 4
    lookahead = 32
    cache_lines = 1024
    for policy_name in ["copper_epoch", "copper_line_epoch"]:
        for entries in [0, 512, 1024, 2048, 4096, 8192, 16384, 65536, 131072]:
            workload = make_workload(graph, seed)
            result = run_policy(
                workload,
                policy_name,
                trace,
                cache_lines=cache_lines,
                proof_entries=entries,
                passes=passes,
                lookahead=lookahead,
                seed=seed,
            )
            row = result_row(
                graph,
                "edge_scan",
                seed,
                policy_name,
                result,
                len(trace),
                entries,
            )
            rows.append(row)
    attach_speedups(rows, disabled_cycles=None, graph_for_baseline=graph)
    return rows


def attach_speedups(
    rows: list[dict[str, object]],
    disabled_cycles: dict[tuple[str, str, int], float] | None = None,
    graph_for_baseline: GapbsGraph | None = None,
) -> None:
    if disabled_cycles is None:
        disabled_cycles = {}
        for row in rows:
            if row["policy"] == "disabled":
                key = (str(row["graph"]), str(row["kernel"]), int(row["seed"]))
                disabled_cycles[key] = float(row["cycles"])
        if graph_for_baseline is not None:
            baseline_workload = make_workload(graph_for_baseline, 1)
            baseline = run_policy(
                baseline_workload,
                "disabled",
                edge_scan_trace(graph_for_baseline),
                cache_lines=1024,
                proof_entries=0,
                passes=4,
                lookahead=32,
                seed=1,
            )
            disabled_cycles[(graph_for_baseline.name, "edge_scan", 1)] = float(
                baseline.cycles
            )

    for row in rows:
        key = (str(row["graph"]), str(row["kernel"]), int(row["seed"]))
        base = disabled_cycles.get(key, float(row["cycles"]))
        row["speedup_vs_disabled"] = base / float(row["cycles"])


def aggregate_by_policy(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    policies = ["disabled", "naive", "source_only", "copper_epoch", "copper_line_epoch"]
    for policy in policies:
        data = [row for row in rows if row["policy"] == policy]
        out.append(
            {
                "policy": policy,
                "speedup": mean(float(row["speedup_vs_disabled"]) for row in data),
                "demand_misses": mean(float(row["demand_misses"]) for row in data),
                "prefetches": mean(float(row["prefetches"]) for row in data),
                "useful_prefetch_hits": mean(
                    float(row["useful_prefetch_hits"]) for row in data
                ),
                "data_at_rest": mean(
                    float(row["data_at_rest_prefetches"]) for row in data
                ),
                "unproven_edges": mean(
                    float(row["unproven_edge_prefetches"]) for row in data
                ),
                "stale": mean(float(row["stale_unproven_prefetches"]) for row in data),
                "epoch_blocks": mean(
                    float(row["blocked_epoch_or_value"]) for row in data
                ),
            }
        )
    return out


def fmt(value: float) -> str:
    return f"{value:,.1f}"


def write_outputs(
    graphs: list[GapbsGraph],
    rows: list[dict[str, object]],
    capacity_rows: list[dict[str, object]],
) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "gapbs_copper_trace_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    cap_csv = OUT_DIR / "gapbs_copper_trace_capacity.csv"
    with cap_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(capacity_rows[0].keys()))
        writer.writeheader()
        writer.writerows(capacity_rows)

    policy_rows = aggregate_by_policy(rows)
    md: list[str] = [
        "# GAPBS-Backed COPPER Trace Summary",
        "",
        "This evaluator parses public GAPBS serialized `.sg` CSR files and replays edge-scan and BFS-replay graph streams over the actual generated topology. It is not an official full-system GAPBS result; its purpose is to connect COPPER's proof rule to GAPBS graph structure while measuring unsafe DMP behavior that full-system timing alone does not expose.",
        "",
        "## Parsed Graphs",
        "",
        "| Graph | Directed | Nodes | Directed edge slots |",
        "|---|---:|---:|---:|",
    ]
    for graph in graphs:
        md.append(
            f"| {graph.name} | {int(graph.directed)} | {graph.nodes:,} | {graph.edges:,} |"
        )

    md.extend(
        [
            "",
            "## Policy Results",
            "",
            "Averages cover all parsed graphs, two graph kernels, and five mutation/adversarial seeds. Speedup is a trace-level latency proxy versus disabled DMP for the same graph, kernel, and seed.",
            "",
            "| Policy | Speedup | Demand misses | Prefetches | Useful PF hits | Data-at-rest PF | Unproven edge PF | Stale slot PF | Epoch/value blocks |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in policy_rows:
        md.append(
            "| {policy} | {speedup:.3f}x | {misses} | {prefetches} | {hits} | {data_rest} | {unproven} | {stale} | {epoch_blocks} |".format(
                policy=row["policy"],
                speedup=float(row["speedup"]),
                misses=fmt(float(row["demand_misses"])),
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
            "## COPPER Capacity Sweep",
            "",
            f"Capacity sweep uses `{capacity_rows[0]['graph']}` edge_scan, seed 1, four passes, and 32-edge prefetch lookahead. `copper_epoch` stores one proof per edge slot/value/epoch; `copper_line_epoch` is a compressed line-provenance directory that stores a proof mask per source cache line and invalidates the whole line on a write epoch change.",
            "",
            "| Policy | Proof entries | Speedup | Prefetches | Useful PF hits | Epoch/value blocks | No-proof blocks |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in capacity_rows:
        md.append(
            "| {policy} | {entries:,} | {speedup:.3f}x | {prefetches:,} | {hits:,} | {epoch_blocks:,} | {blocked:,} |".format(
                policy=row["policy"],
                entries=int(row["proof_entries"]),
                speedup=float(row["speedup_vs_disabled"]),
                prefetches=int(row["prefetches"]),
                hits=int(row["useful_prefetch_hits"]),
                epoch_blocks=int(row["blocked_epoch_or_value"]),
                blocked=int(row["blocked_no_proof"]),
            )
        )

    md.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Naive DMP gains performance in the trace proxy, but it dereferences pointer-shaped data-at-rest and unproven edge values.",
            "- The source-only weakened variant blocks data-at-rest, but after edge-slot rewrites it still authorizes stale slot values because the proof is tied only to the source location.",
            "- COPPER-epoch blocks data-at-rest and stale rewritten-edge dereferences while preserving most repeated graph-stream benefit once committed traversal has established proof.",
            "- This strengthens the artifact by using GAPBS-generated topology, but it does not replace official full-system AArch64 GAPBS execution.",
        ]
    )
    md_path = OUT_DIR / "GAPBS_COPPER_TRACE_SUMMARY.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(csv_path)
    print(cap_csv)
    print(md_path)


def main() -> None:
    graph_paths = sorted(OUT_DIR.glob("kron_g*.sg"))
    if not graph_paths:
        raise SystemExit(f"No GAPBS .sg files found in {OUT_DIR}")
    graphs = [read_gapbs_sg(path) for path in graph_paths]
    rows = run_main_sweep(graphs)
    middle_graph = next((graph for graph in graphs if graph.name == "kron_g12"), graphs[-1])
    capacity_rows = run_capacity_sweep(middle_graph)
    write_outputs(graphs, rows, capacity_rows)


if __name__ == "__main__":
    main()
