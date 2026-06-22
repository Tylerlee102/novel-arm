#!/usr/bin/env python3
"""
Toy model for Antichain-Compressed Order Witnesses (ACOW).

This is not a complete Arm memory model. It models the verification-relevant
core of the proposed mechanism: coherence and preserved-order events form a
directed graph, and a witness generator logs only edges that extend reachability
or close a cycle. Dropping a transitive edge should not reduce cycle detection.
"""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import random
from statistics import mean, median


@dataclass(frozen=True)
class Edge:
    src: int
    dst: int
    kind: str


class BaselineChecker:
    def __init__(self, nodes: int) -> None:
        self.nodes = nodes
        self.edges: list[Edge] = []

    def add(self, edge: Edge) -> bool:
        self.edges.append(edge)
        return False

    def has_cycle(self) -> bool:
        graph = [[] for _ in range(self.nodes)]
        for edge in self.edges:
            graph[edge.src].append(edge.dst)

        color = [0] * self.nodes

        def dfs(node: int) -> bool:
            color[node] = 1
            for nxt in graph[node]:
                if color[nxt] == 1:
                    return True
                if color[nxt] == 0 and dfs(nxt):
                    return True
            color[node] = 2
            return False

        return any(color[node] == 0 and dfs(node) for node in range(self.nodes))


class ACOWChecker:
    """Dynamic reachability witness with transitive-edge suppression."""

    def __init__(self, nodes: int) -> None:
        self.nodes = nodes
        self.reach = [0] * nodes
        self.logged_edges: list[Edge] = []
        self.dropped_edges = 0
        self.detected_cycle = False
        self.peak_bits_per_node = 0

    def add(self, edge: Edge) -> bool:
        src_bit = 1 << edge.src
        dst_bit = 1 << edge.dst

        if edge.src == edge.dst or (self.reach[edge.dst] & src_bit):
            self.logged_edges.append(edge)
            self.detected_cycle = True
            return True

        if self.reach[edge.src] & dst_bit:
            self.dropped_edges += 1
            return False

        delta = dst_bit | self.reach[edge.dst]
        affected = src_bit
        for node in range(self.nodes):
            if self.reach[node] & src_bit:
                affected |= 1 << node

        for node in range(self.nodes):
            if affected & (1 << node):
                self.reach[node] |= delta

        self.logged_edges.append(edge)
        self.peak_bits_per_node = max(
            self.peak_bits_per_node,
            max(bits.bit_count() for bits in self.reach),
        )
        return False


def node(thread: int, epoch: int, epochs: int) -> int:
    return thread * epochs + epoch


def generate_execution(
    rng: random.Random,
    threads: int,
    epochs: int,
    addresses: int,
    edge_density: float,
    inject_bug: bool,
) -> list[Edge]:
    ppo_edges: list[Edge] = []
    other_edges: list[Edge] = []

    for thread in range(threads):
        for distance in range(1, epochs):
            for earlier in range(epochs - distance):
                later = earlier + distance
                ppo_edges.append(Edge(node(thread, earlier, epochs), node(thread, later, epochs), "ppo"))

    writes_by_addr: dict[int, list[int]] = {addr: [] for addr in range(addresses)}
    reads_by_addr: dict[int, list[int]] = {addr: [] for addr in range(addresses)}

    for thread in range(threads):
        for epoch in range(epochs):
            n = node(thread, epoch, epochs)
            addr = rng.randrange(addresses)
            if rng.random() < 0.48:
                writes_by_addr[addr].append(n)
            else:
                reads_by_addr[addr].append(n)

    for addr in range(addresses):
        writes = sorted(set(writes_by_addr[addr]))
        reads = sorted(set(reads_by_addr[addr]))

        for left, right in zip(writes, writes[1:]):
            other_edges.append(Edge(left, right, "co"))

        for read in reads:
            earlier_writes = [write for write in writes if write < read]
            later_writes = [write for write in writes if write > read]
            if earlier_writes:
                rf_src = rng.choice(earlier_writes)
                other_edges.append(Edge(rf_src, read, "rf"))
            for write in later_writes[:2]:
                if rng.random() < edge_density:
                    other_edges.append(Edge(read, write, "fr"))

    nodes = threads * epochs
    for src in range(nodes):
        for dst in range(src + 1, nodes):
            if rng.random() < edge_density / nodes:
                other_edges.append(Edge(src, dst, "obs"))

    rng.shuffle(other_edges)
    edges = ppo_edges + other_edges

    if inject_bug:
        legal = ACOWChecker(nodes)
        for edge in edges:
            legal.add(edge)

        candidates: list[tuple[int, int]] = []
        for src in range(nodes):
            for dst in range(nodes):
                if src != dst and (legal.reach[dst] & (1 << src)):
                    candidates.append((src, dst))
        if candidates:
            src, dst = rng.choice(candidates)
            edges.insert(rng.randrange(len(edges) + 1), Edge(src, dst, "bug-backedge"))

    return edges


def run_trial(
    rng: random.Random,
    threads: int,
    epochs: int,
    addresses: int,
    edge_density: float,
    inject_bug: bool,
) -> dict[str, float | int | bool]:
    nodes = threads * epochs
    edges = generate_execution(rng, threads, epochs, addresses, edge_density, inject_bug)
    baseline = BaselineChecker(nodes)
    acow = ACOWChecker(nodes)

    for edge in edges:
        baseline.add(edge)
        acow.add(edge)

    baseline_cycle = baseline.has_cycle()
    return {
        "nodes": nodes,
        "baseline_edges": len(baseline.edges),
        "acow_edges": len(acow.logged_edges),
        "dropped_edges": acow.dropped_edges,
        "compression": len(baseline.edges) / max(1, len(acow.logged_edges)),
        "baseline_cycle": baseline_cycle,
        "acow_cycle": acow.detected_cycle,
        "peak_bits_per_node": acow.peak_bits_per_node,
    }


def summarize(results: list[dict[str, float | int | bool]]) -> dict[str, float]:
    cycles = [result for result in results if result["baseline_cycle"]]
    detected = [result for result in cycles if result["acow_cycle"]]
    return {
        "trials": len(results),
        "cycles": len(cycles),
        "coverage_pct": 100.0 * len(detected) / max(1, len(cycles)),
        "avg_baseline_edges": mean(float(r["baseline_edges"]) for r in results),
        "avg_acow_edges": mean(float(r["acow_edges"]) for r in results),
        "median_compression": median(float(r["compression"]) for r in results),
        "avg_compression": mean(float(r["compression"]) for r in results),
        "avg_peak_bits_per_node": mean(float(r["peak_bits_per_node"]) for r in results),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--addresses", type=int, default=16)
    parser.add_argument("--edge-density", type=float, default=0.35)
    parser.add_argument("--bug-rate", type=float, default=0.5)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    results = []
    for _ in range(args.trials):
        inject_bug = rng.random() < args.bug_rate
        results.append(
            run_trial(
                rng,
                args.threads,
                args.epochs,
                args.addresses,
                args.edge_density,
                inject_bug,
            )
        )

    summary = summarize(results)
    print("ACOW toy witness simulation")
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"{key}: {value:.3f}")
        else:
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
