#!/usr/bin/env python3
"""Graph-style COPPER evaluation with provenance-aware CSR edge slots.

This is not a full GAPBS replacement. It is a small, reproducible trace model
for graph-like pointer arrays: each edge slot stores a node address, repeated
passes create reusable committed provenance, and an adversarial side array holds
pointer-shaped values that must not authorize DMP dereference.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import csv
import random
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research" / "results" / "graph_copper"
BASE = 0x4000_0000
NODE_STRIDE = 64
HIT = 4
MISS = 100
PREFETCH_FILL = 8


@dataclass
class EdgeSlot:
    slot_id: int
    target: int
    epoch: int = 0
    domain: int = 0


@dataclass
class GraphWorkload:
    node_addrs: list[int]
    edges: list[EdgeSlot]
    adversarial_values: list[int]
    mutate_slots: list[int]


class LruCache:
    def __init__(self, lines: int) -> None:
        self.lines = lines
        self.data: OrderedDict[int, None] = OrderedDict()

    def touch(self, addr: int) -> bool:
        line = addr // NODE_STRIDE
        hit = line in self.data
        if hit:
            self.data.move_to_end(line)
        else:
            self.data[line] = None
            if len(self.data) > self.lines:
                self.data.popitem(last=False)
        return hit


class GraphPolicy:
    def __init__(self, name: str, cache_lines: int, proof_entries: int) -> None:
        self.name = name
        self.cache = LruCache(cache_lines)
        self.proofs: OrderedDict[tuple[int, int, int], None] = OrderedDict()
        self.source_only_proofs: OrderedDict[int, None] = OrderedDict()
        self.proof_entries = proof_entries
        self.cycles = 0
        self.demand_misses = 0
        self.prefetches = 0
        self.useful_prefetch_hits = 0
        self.data_at_rest_prefetches = 0
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

    def learn_edge(self, edge: EdgeSlot) -> None:
        self._remember(self.source_only_proofs, edge.slot_id)
        self._remember(self.proofs, (edge.slot_id, edge.target, edge.epoch))

    def mutate_edge(self, edge: EdgeSlot, new_target: int) -> None:
        edge.target = new_target
        edge.epoch = (edge.epoch + 1) & 0xFF

    def maybe_prefetch_edge(self, edge: EdgeSlot) -> None:
        if self.name == "disabled":
            return

        allowed = False
        unsafe_stale = False
        if self.name == "naive":
            allowed = True
        elif self.name == "source_only":
            allowed = edge.slot_id in self.source_only_proofs
            unsafe_stale = allowed and (edge.slot_id, edge.target, edge.epoch) not in self.proofs
        elif self.name == "copper_epoch":
            allowed = (edge.slot_id, edge.target, edge.epoch) in self.proofs
        else:
            raise ValueError(self.name)

        if not allowed:
            self.blocked_no_proof += 1
            if self.name == "copper_epoch" and edge.slot_id in self.source_only_proofs:
                self.blocked_epoch_or_value += 1
            return

        self.prefetches += 1
        if unsafe_stale:
            self.stale_unproven_prefetches += 1
        if not self.cache.touch(edge.target):
            self.cycles += PREFETCH_FILL

    def maybe_prefetch_adversarial(self, value: int) -> None:
        if self.name == "disabled":
            return
        if self.name == "naive":
            self.prefetches += 1
            self.data_at_rest_prefetches += 1
            if not self.cache.touch(value):
                self.cycles += PREFETCH_FILL
            return
        self.blocked_no_proof += 1

    def demand_node(self, addr: int) -> None:
        if self.cache.touch(addr):
            self.cycles += HIT
            self.useful_prefetch_hits += 1
        else:
            self.cycles += MISS
            self.demand_misses += 1


def make_workload(
    seed: int,
    nodes: int = 4096,
    degree: int = 8,
    adversarial_count: int = 2048,
    mutate_fraction: float = 0.05,
) -> GraphWorkload:
    rng = random.Random(seed)
    node_addrs = [BASE + index * NODE_STRIDE for index in range(nodes)]
    order = list(range(nodes))
    rng.shuffle(order)

    edges: list[EdgeSlot] = []
    slot_id = 0
    for src_position, src in enumerate(order):
        for d in range(degree):
            target_index = order[(src_position * 17 + d * 131 + seed) % nodes]
            edges.append(EdgeSlot(slot_id=slot_id, target=node_addrs[target_index]))
            slot_id += 1

    adversarial_values = [
        node_addrs[(index * 193 + seed * 17) % nodes]
        for index in range(adversarial_count)
    ]

    mutate_count = int(len(edges) * mutate_fraction)
    mutate_slots = rng.sample(range(len(edges)), mutate_count)
    return GraphWorkload(node_addrs, edges, adversarial_values, mutate_slots)


def run_policy(
    workload: GraphWorkload,
    policy_name: str,
    cache_lines: int,
    proof_entries: int,
    passes: int,
) -> GraphPolicy:
    policy = GraphPolicy(policy_name, cache_lines, proof_entries)
    rng = random.Random(1000 + len(workload.edges))

    for pass_index in range(passes):
        if pass_index == 2:
            for edge_index in workload.mutate_slots:
                edge = workload.edges[edge_index]
                edge_target = rng.choice(workload.node_addrs)
                policy.mutate_edge(edge, edge_target)

        for value in workload.adversarial_values:
            policy.maybe_prefetch_adversarial(value)

        for edge in workload.edges:
            policy.maybe_prefetch_edge(edge)
            policy.demand_node(edge.target)
            policy.learn_edge(edge)

    return policy


def run_sweep() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    policies = ["disabled", "naive", "source_only", "copper_epoch"]
    rows: list[dict[str, object]] = []
    seeds = range(1, 11)
    for seed in seeds:
        for policy in policies:
            wl = make_workload(seed)
            result = run_policy(
                wl,
                policy,
                cache_lines=512,
                proof_entries=65536,
                passes=5,
            )
            rows.append(
                {
                    "seed": seed,
                    "policy": policy,
                    "cycles": result.cycles,
                    "demand_misses": result.demand_misses,
                    "prefetches": result.prefetches,
                    "useful_prefetch_hits": result.useful_prefetch_hits,
                    "data_at_rest_prefetches": result.data_at_rest_prefetches,
                    "stale_unproven_prefetches": result.stale_unproven_prefetches,
                    "blocked_no_proof": result.blocked_no_proof,
                    "blocked_epoch_or_value": result.blocked_epoch_or_value,
                }
            )

    capacity_rows: list[dict[str, object]] = []
    for entries in [0, 1024, 4096, 16384, 32768, 49152, 65536]:
        seed_rows = []
        for seed in seeds:
            wl = make_workload(seed)
            result = run_policy(
                wl,
                "copper_epoch",
                cache_lines=512,
                proof_entries=entries,
                passes=5,
            )
            seed_rows.append(result)
        capacity_rows.append(
            {
                "proof_entries": entries,
                "cycles": mean(row.cycles for row in seed_rows),
                "prefetches": mean(row.prefetches for row in seed_rows),
                "blocked_no_proof": mean(row.blocked_no_proof for row in seed_rows),
                "blocked_epoch_or_value": mean(
                    row.blocked_epoch_or_value for row in seed_rows
                ),
            }
        )

    return rows, capacity_rows


def write_outputs(rows: list[dict[str, object]], capacity_rows: list[dict[str, object]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "graph_copper_summary.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    cap_csv = OUT_DIR / "graph_copper_capacity.csv"
    with cap_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(capacity_rows[0].keys()))
        writer.writeheader()
        writer.writerows(capacity_rows)

    by_policy: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        by_policy.setdefault(str(row["policy"]), []).append(row)
    disabled_cycles = mean(float(row["cycles"]) for row in by_policy["disabled"])

    md = [
        "# COPPER Graph-Style Workload Summary",
        "",
        "This provenance-aware trace model uses CSR-like graph edge slots. Each edge slot stores a node address, repeated graph passes let committed demand traversal prove edge slots, an adversarial side array holds pointer-shaped data-at-rest values, and 5% of edge slots are rewritten after warmup.",
        "",
        "## Ten-Seed Policy Results",
        "",
        "| Policy | Speedup vs disabled | Demand misses | Prefetches | Useful demand hits | Data-at-rest PF | Stale/unproven PF | Epoch/value blocks |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for policy in ["disabled", "naive", "source_only", "copper_epoch"]:
        data = by_policy[policy]
        cycles = mean(float(row["cycles"]) for row in data)
        md.append(
            "| {policy} | {speedup:.3f}x | {misses:.1f} | {prefetches:.1f} | {hits:.1f} | {data_rest:.1f} | {stale:.1f} | {epoch_blocks:.1f} |".format(
                policy=policy,
                speedup=disabled_cycles / cycles,
                misses=mean(float(row["demand_misses"]) for row in data),
                prefetches=mean(float(row["prefetches"]) for row in data),
                hits=mean(float(row["useful_prefetch_hits"]) for row in data),
                data_rest=mean(float(row["data_at_rest_prefetches"]) for row in data),
                stale=mean(float(row["stale_unproven_prefetches"]) for row in data),
                epoch_blocks=mean(float(row["blocked_epoch_or_value"]) for row in data),
            )
        )

    md.extend(
        [
            "",
            "## Proof-Ledger Capacity Sweep",
            "",
            "| COPPER proof entries | Speedup vs disabled | Prefetches | No-proof blocks | Epoch/value blocks |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    for row in capacity_rows:
        md.append(
            "| {entries} | {speedup:.3f}x | {prefetches:.1f} | {blocked:.1f} | {epoch_blocks:.1f} |".format(
                entries=row["proof_entries"],
                speedup=disabled_cycles / float(row["cycles"]),
                prefetches=float(row["prefetches"]),
                blocked=float(row["blocked_no_proof"]),
                epoch_blocks=float(row["blocked_epoch_or_value"]),
            )
        )

    md.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Naive DMP is fastest in this trace but prefetches every adversarial pointer-shaped data value.",
            "- Source-only provenance recovers performance but is unsafe after edge rewrites: previously proven slots can authorize changed values.",
            "- COPPER-epoch/value provenance blocks both data-at-rest and stale rewritten edge slots while preserving most of the repeated graph-pass speedup.",
            "- This is still a trace model, not full-system GAPBS. Its value is that it exercises a graph-shaped access pattern and the CEPF stale-tag concern that linked-list loops do not expose well.",
        ]
    )
    md_path = OUT_DIR / "GRAPH_COPPER_SUMMARY.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(csv_path)
    print(cap_csv)
    print(md_path)


def main() -> None:
    rows, capacity_rows = run_sweep()
    write_outputs(rows, capacity_rows)


if __name__ == "__main__":
    main()
