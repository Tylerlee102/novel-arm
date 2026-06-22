#!/usr/bin/env python3
"""Guest-side graph/provenance workload for ARM64 full-system gem5.

The purpose is not to replace detailed gem5 prefetch timing. It runs inside the
ARM64 Linux guest and emits a reproducible graph workload checksum plus COPPER
policy metrics over the same CSR-like edge slots.
"""

from __future__ import annotations

import argparse
from collections import OrderedDict
from dataclasses import dataclass
import os
import platform
import random
import sys
import time


BASE = 0x4000_0000
NODE_STRIDE = 64
HIT = 4
MISS = 100
PREFETCH_FILL = 8


@dataclass
class Edge:
    slot: int
    target: int
    epoch: int = 0


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


class Policy:
    def __init__(self, name: str, cache_lines: int, proof_entries: int) -> None:
        self.name = name
        self.cache = LruCache(cache_lines)
        self.proofs: OrderedDict[tuple[int, int, int], None] = OrderedDict()
        self.source_only: OrderedDict[int, None] = OrderedDict()
        self.proof_entries = proof_entries
        self.cycles = 0
        self.demand_misses = 0
        self.prefetches = 0
        self.useful_hits = 0
        self.data_at_rest = 0
        self.stale_unproven = 0
        self.blocked = 0
        self.blocked_epoch_value = 0

    def remember(self, table: OrderedDict, key) -> None:
        if self.proof_entries <= 0:
            return
        table[key] = None
        table.move_to_end(key)
        while len(table) > self.proof_entries:
            table.popitem(last=False)

    def learn(self, edge: Edge) -> None:
        self.remember(self.source_only, edge.slot)
        self.remember(self.proofs, (edge.slot, edge.target, edge.epoch))

    def prefetch_edge(self, edge: Edge) -> None:
        if self.name == "disabled":
            return
        allowed = False
        stale = False
        if self.name == "naive":
            allowed = True
        elif self.name == "source_only":
            allowed = edge.slot in self.source_only
            stale = allowed and (edge.slot, edge.target, edge.epoch) not in self.proofs
        elif self.name == "copper_epoch":
            allowed = (edge.slot, edge.target, edge.epoch) in self.proofs
        else:
            raise ValueError(self.name)

        if not allowed:
            self.blocked += 1
            if self.name == "copper_epoch" and edge.slot in self.source_only:
                self.blocked_epoch_value += 1
            return
        self.prefetches += 1
        if stale:
            self.stale_unproven += 1
        if not self.cache.touch(edge.target):
            self.cycles += PREFETCH_FILL

    def prefetch_adversarial(self, value: int) -> None:
        if self.name == "disabled":
            return
        if self.name == "naive":
            self.prefetches += 1
            self.data_at_rest += 1
            if not self.cache.touch(value):
                self.cycles += PREFETCH_FILL
        else:
            self.blocked += 1

    def demand(self, addr: int) -> None:
        if self.cache.touch(addr):
            self.cycles += HIT
            self.useful_hits += 1
        else:
            self.cycles += MISS
            self.demand_misses += 1


def make_edges(nodes: int, degree: int, seed: int) -> tuple[list[int], list[Edge], list[int], list[int]]:
    rng = random.Random(seed)
    addrs = [BASE + index * NODE_STRIDE for index in range(nodes)]
    order = list(range(nodes))
    rng.shuffle(order)
    edges = []
    slot = 0
    for pos, _src in enumerate(order):
        for d in range(degree):
            target_index = order[(pos * 17 + d * 131 + seed) % nodes]
            edges.append(Edge(slot, addrs[target_index]))
            slot += 1
    adversarial = [addrs[(idx * 193 + seed * 17) % nodes] for idx in range(max(1, nodes // 2))]
    mutate = rng.sample(range(len(edges)), max(1, len(edges) // 20))
    return addrs, edges, adversarial, mutate


def run_guest_graph_kernel(edges: list[Edge], nodes: int, passes: int) -> int:
    ranks = [((i * 2654435761) & 0xFFFF) for i in range(nodes)]
    accum = 0
    for p in range(passes):
        for edge in edges:
            idx = ((edge.target - BASE) // NODE_STRIDE) % nodes
            ranks[idx] = (ranks[idx] + p + edge.slot) & 0xFFFF
            accum ^= ((ranks[idx] << (edge.slot & 7)) ^ edge.target) & 0xFFFFFFFF
    return accum


def run_policy(name: str, addrs: list[int], edges_in: list[Edge], adversarial: list[int],
               mutate_slots: list[int], passes: int, cache_lines: int,
               proof_entries: int) -> Policy:
    edges = [Edge(e.slot, e.target, e.epoch) for e in edges_in]
    policy = Policy(name, cache_lines, proof_entries)
    rng = random.Random(1000 + len(edges))
    for p in range(passes):
        if p == 2:
            for idx in mutate_slots:
                edge = edges[idx]
                edge.target = rng.choice(addrs)
                edge.epoch = (edge.epoch + 1) & 0xFF
        for value in adversarial:
            policy.prefetch_adversarial(value)
        for edge in edges:
            policy.prefetch_edge(edge)
            policy.demand(edge.target)
            policy.learn(edge)
    return policy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nodes", type=int, default=512)
    parser.add_argument("--degree", type=int, default=4)
    parser.add_argument("--passes", type=int, default=4)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--cache-lines", type=int, default=128)
    parser.add_argument("--proof-entries", type=int, default=8192)
    args = parser.parse_args()

    print("COPPER_FS_WORKLOAD_START", flush=True)
    print(
        "COPPER_FS_ENV "
        f"machine={platform.machine()} python={platform.python_version()} "
        f"pid={os.getpid()} byteorder={sys.byteorder}",
        flush=True,
    )

    totals: dict[str, dict[str, float]] = {}
    t0 = time.time()
    for seed in range(1, args.seeds + 1):
        addrs, edges, adversarial, mutate = make_edges(args.nodes, args.degree, seed)
        checksum = run_guest_graph_kernel(edges, args.nodes, args.passes)
        disabled = run_policy(
            "disabled", addrs, edges, adversarial, mutate, args.passes,
            args.cache_lines, args.proof_entries,
        )
        for name in ("naive", "source_only", "copper_epoch"):
            result = run_policy(
                name, addrs, edges, adversarial, mutate, args.passes,
                args.cache_lines, args.proof_entries,
            )
            speedup = disabled.cycles / result.cycles
            unsafe = result.data_at_rest + result.stale_unproven
            print(
                "COPPER_FS_POLICY "
                f"seed={seed} policy={name} speedup={speedup:.4f} "
                f"cycles={result.cycles} baseline_cycles={disabled.cycles} "
                f"demand_misses={result.demand_misses} prefetches={result.prefetches} "
                f"useful_hits={result.useful_hits} data_at_rest={result.data_at_rest} "
                f"stale_unproven={result.stale_unproven} blocked={result.blocked} "
                f"blocked_epoch_value={result.blocked_epoch_value} checksum={checksum}",
                flush=True,
            )
            entry = totals.setdefault(
                name,
                {
                    "speedup": 0.0,
                    "data_at_rest": 0.0,
                    "stale_unproven": 0.0,
                    "prefetches": 0.0,
                    "demand_misses": 0.0,
                },
            )
            entry["speedup"] += speedup
            entry["data_at_rest"] += result.data_at_rest
            entry["stale_unproven"] += result.stale_unproven
            entry["prefetches"] += result.prefetches
            entry["demand_misses"] += result.demand_misses

    elapsed = time.time() - t0
    for name, values in totals.items():
        n = float(args.seeds)
        print(
            "COPPER_FS_SUMMARY "
            f"policy={name} avg_speedup={values['speedup'] / n:.4f} "
            f"avg_prefetches={values['prefetches'] / n:.1f} "
            f"avg_demand_misses={values['demand_misses'] / n:.1f} "
            f"avg_data_at_rest={values['data_at_rest'] / n:.1f} "
            f"avg_stale_unproven={values['stale_unproven'] / n:.1f}",
            flush=True,
        )
    print(f"COPPER_FS_WORKLOAD_SECONDS {elapsed:.3f}", flush=True)
    print("COPPER_FS_WORKLOAD_DONE", flush=True)


if __name__ == "__main__":
    main()
