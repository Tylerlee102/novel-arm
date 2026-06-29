#!/usr/bin/env python3
"""Small executable COPPER prefetch-evaluation model.

This is model-level evidence, not gem5 or RTL evidence. It exists to make the
conference-facing CSVs reproducible for baseline comparison, queue behavior,
lateness, seed stability, and ablation/sensitivity studies.
"""

from __future__ import annotations

from collections import OrderedDict, defaultdict
from dataclasses import dataclass
import random


LINE = 64


@dataclass(frozen=True)
class Access:
    addr: int
    candidate: int | None = None
    source_addr: int | None = None
    committed: bool = True
    pointer_source: bool = True
    gap_after: int = 24


@dataclass(frozen=True)
class Workload:
    benchmark: str
    input_name: str
    seed: int
    pointer_intensive: str
    category: str
    accesses: tuple[Access, ...]


@dataclass
class Result:
    benchmark: str
    input_name: str
    seed: int
    config: str
    cycles: int
    instructions: int
    demand_loads: int
    demand_misses: int
    prefetches_issued: int
    useful_prefetches: int
    late_prefetches: int
    queue_drops: int
    duplicate_suppressed: int
    total_memory_requests: int
    checksum: int
    notes: str


class LruCache:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.data: OrderedDict[int, str] = OrderedDict()

    def contains(self, line: int) -> bool:
        return line in self.data

    def touch(self, line: int, source: str) -> tuple[bool, str | None]:
        hit = line in self.data
        previous = self.data.get(line)
        self.data[line] = source if source == "prefetch" else previous or source
        self.data.move_to_end(line)
        if len(self.data) > self.capacity:
            self.data.popitem(last=False)
        return hit, previous


class ModelSimulator:
    def __init__(
        self,
        *,
        config: str,
        cache_lines: int = 128,
        queue_size: int = 8,
        memory_latency: int = 80,
        hit_latency: int = 4,
        prefetch_latency: int = 48,
        prefetch_distance: int = 1,
        table_size: int = 256,
        confidence_threshold: int = 1,
        enable_queue_filter: bool = True,
    ) -> None:
        self.config = config
        self.cache = LruCache(cache_lines)
        self.queue_size = queue_size
        self.memory_latency = memory_latency
        self.hit_latency = hit_latency
        self.prefetch_latency = prefetch_latency
        self.prefetch_distance = prefetch_distance
        self.table_size = table_size
        self.confidence_threshold = confidence_threshold
        self.enable_queue_filter = enable_queue_filter
        self.provenance: OrderedDict[tuple[int, int], int] = OrderedDict()
        self.inflight: OrderedDict[int, int] = OrderedDict()
        self.last_addr: int | None = None
        self.last_delta: int | None = None
        self.cycles = 0
        self.instructions = 0
        self.demand_loads = 0
        self.demand_misses = 0
        self.prefetches_issued = 0
        self.useful_prefetches = 0
        self.late_prefetches = 0
        self.queue_drops = 0
        self.duplicate_suppressed = 0
        self.checksum = 0

    def _complete_prefetches(self) -> None:
        ready = [line for line, ready_cycle in self.inflight.items() if ready_cycle <= self.cycles]
        for line in ready:
            self.cache.touch(line, "prefetch")
            del self.inflight[line]

    def _remember_proof(self, source: int, target: int) -> None:
        key = (source, target)
        self.provenance[key] = self.provenance.get(key, 0) + 1
        self.provenance.move_to_end(key)
        while len(self.provenance) > self.table_size:
            self.provenance.popitem(last=False)

    def _has_proof(self, source: int, target: int) -> bool:
        count = self.provenance.get((source, target), 0)
        return count >= self.confidence_threshold

    def _issue(self, target: int | None) -> None:
        if target is None:
            return
        line = target // LINE
        if self.enable_queue_filter and (self.cache.contains(line) or line in self.inflight):
            self.duplicate_suppressed += 1
            return
        if len(self.inflight) >= self.queue_size:
            self.queue_drops += 1
            return
        self.inflight[line] = self.cycles + self.prefetch_latency
        self.prefetches_issued += 1

    def _candidate_for(self, access: Access) -> int | None:
        if self.config == "no_prefetch":
            return None
        if self.config == "next_line":
            return access.addr + LINE * self.prefetch_distance
        if self.config == "stride":
            if self.last_addr is None:
                return None
            delta = access.addr - self.last_addr
            target = None
            if self.last_delta is not None and delta == self.last_delta:
                target = access.addr + delta * self.prefetch_distance
            return target
        if self.config in {
            "simple_pointer_chase",
            "A0_no_provenance",
            "A1_speculative_provenance",
        }:
            return access.candidate
        if self.config in {
            "copper",
            "A2_committed_only",
            "A3_committed_only_plus_confidence",
            "A4_committed_only_plus_queue_filtering",
            "A5_full_copper",
        }:
            if access.candidate is None or not access.pointer_source:
                return None
            return access.candidate if self._has_proof(access.addr, access.candidate) else None
        return None

    def run(self, workload: Workload) -> Result:
        for access in workload.accesses:
            self._complete_prefetches()
            line = access.addr // LINE
            self.demand_loads += 1
            self.instructions += 6
            self.checksum = ((self.checksum * 1315423911) ^ access.addr) & 0xFFFFFFFFFFFFFFFF

            if line in self.inflight:
                if self.inflight[line] > self.cycles:
                    self.late_prefetches += 1
                    self.cycles += self.memory_latency
                else:
                    self.useful_prefetches += 1
                    self.cycles += self.hit_latency
                del self.inflight[line]
                self.cache.touch(line, "demand")
            else:
                hit, previous = self.cache.touch(line, "demand")
                if hit:
                    if previous == "prefetch":
                        self.useful_prefetches += 1
                    self.cycles += self.hit_latency
                else:
                    self.demand_misses += 1
                    self.cycles += self.memory_latency

            if access.source_addr is not None:
                if access.committed or self.config == "A1_speculative_provenance":
                    self._remember_proof(access.source_addr, access.addr)

            target = self._candidate_for(access)
            self._issue(target)

            if self.last_addr is not None:
                self.last_delta = access.addr - self.last_addr
            self.last_addr = access.addr
            self.cycles += access.gap_after
            self.instructions += max(1, access.gap_after // 2)

        self._complete_prefetches()
        return Result(
            benchmark=workload.benchmark,
            input_name=workload.input_name,
            seed=workload.seed,
            config=self.config,
            cycles=self.cycles,
            instructions=self.instructions,
            demand_loads=self.demand_loads,
            demand_misses=self.demand_misses,
            prefetches_issued=self.prefetches_issued,
            useful_prefetches=self.useful_prefetches,
            late_prefetches=self.late_prefetches,
            queue_drops=self.queue_drops,
            duplicate_suppressed=self.duplicate_suppressed,
            total_memory_requests=self.demand_misses + self.prefetches_issued,
            checksum=self.checksum,
            notes="model-level executable simulation",
        )


def make_pointer_chain(name: str, size: str, seed: int, *, length: int, passes: int, gap: int = 24) -> Workload:
    rng = random.Random(seed)
    nodes = [0x100000 + i * LINE * 3 + rng.randrange(0, 2) * LINE for i in range(length)]
    accesses: list[Access] = []
    for _ in range(passes):
        prev: int | None = None
        for idx, addr in enumerate(nodes):
            candidate = nodes[idx + 1] if idx + 1 < len(nodes) else None
            accesses.append(Access(addr=addr, candidate=candidate, source_addr=prev, gap_after=gap))
            prev = addr
    return Workload(name, size, seed, "yes", "positive", tuple(accesses))


def make_tree(size: str, seed: int, *, nodes: int) -> Workload:
    base = 0x200000 + seed * 0x10000
    order: list[int] = []

    def visit(index: int) -> None:
        if index >= nodes:
            return
        order.append(base + index * LINE * 5)
        visit(index * 2 + 1)
        visit(index * 2 + 2)

    visit(0)
    accesses = []
    for pass_id in range(3):
        prev = None
        for idx, addr in enumerate(order):
            candidate = order[idx + 1] if idx + 1 < len(order) else None
            accesses.append(Access(addr=addr, candidate=candidate, source_addr=prev, gap_after=18 + pass_id))
            prev = addr
    return Workload("tree_traversal", size, seed, "yes", "positive", tuple(accesses))


def make_hash(size: str, seed: int, *, buckets: int, chain: int) -> Workload:
    rng = random.Random(seed)
    base = 0x300000 + seed * 0x20000
    chains = [[base + (b * chain + i) * LINE * 7 for i in range(chain)] for b in range(buckets)]
    accesses: list[Access] = []
    for _ in range(4):
        for _ in range(buckets * 2):
            chain_nodes = chains[rng.randrange(buckets)]
            prev = None
            for idx, addr in enumerate(chain_nodes):
                candidate = chain_nodes[idx + 1] if idx + 1 < len(chain_nodes) else None
                accesses.append(Access(addr=addr, candidate=candidate, source_addr=prev, gap_after=16))
                prev = addr
    return Workload("hash_chaining", size, seed, "yes", "positive", tuple(accesses))


def make_graph(size: str, seed: int, *, vertices: int, degree: int) -> Workload:
    rng = random.Random(seed)
    base = 0x400000 + seed * 0x30000
    adjacency = {
        v: [base + rng.randrange(vertices) * LINE * 11 for _ in range(degree)]
        for v in range(vertices)
    }
    accesses: list[Access] = []
    frontier = list(range(min(vertices, 16)))
    for _ in range(5):
        next_frontier: list[int] = []
        prev = None
        for v in frontier:
            addr = base + v * LINE * 11
            candidate = adjacency[v][0] if adjacency[v] else None
            accesses.append(Access(addr=addr, candidate=candidate, source_addr=prev, gap_after=20))
            prev = addr
            next_frontier.extend((target - base) // (LINE * 11) % vertices for target in adjacency[v][:2])
        frontier = next_frontier[: max(8, len(frontier))]
    return Workload("graph_adjacency_walk", size, seed, "yes", "positive", tuple(accesses))


def make_linear(size: str, seed: int, *, length: int) -> Workload:
    base = 0x500000 + seed * 0x10000
    accesses = [Access(addr=base + i * LINE, pointer_source=False, gap_after=8) for i in range(length)]
    return Workload("linear_array_scan", size, seed, "no", "negative", tuple(accesses))


def make_matrix(size: str, seed: int, *, side: int) -> Workload:
    base = 0x600000 + seed * 0x10000
    accesses = [Access(addr=base + (r * side + c) * LINE, pointer_source=False, gap_after=6) for r in range(side) for c in range(side)]
    return Workload("matrix_loop", size, seed, "no", "negative", tuple(accesses))


def make_random_nonpointer(size: str, seed: int, *, length: int) -> Workload:
    rng = random.Random(seed)
    base = 0x700000 + seed * 0x20000
    accesses = [Access(addr=base + rng.randrange(length * 8) * LINE, pointer_source=False, gap_after=10) for _ in range(length)]
    return Workload("random_non_pointer", size, seed, "no", "negative", tuple(accesses))


def make_compute(size: str, seed: int, *, length: int) -> Workload:
    base = 0x800000 + seed * 0x10000
    accesses = [Access(addr=base + (i % 8) * LINE, pointer_source=False, gap_after=120) for i in range(length)]
    return Workload("compute_heavy_low_memory", size, seed, "no", "negative", tuple(accesses))


def make_mixed(size: str, seed: int, *, length: int) -> Workload:
    chain = list(make_pointer_chain("mixed_pointer_array", size, seed, length=length, passes=3).accesses)
    linear = list(make_linear(size, seed, length=length).accesses)
    accesses: list[Access] = []
    for a, b in zip(chain, linear):
        accesses.append(a)
        accesses.append(b)
    return Workload("mixed_pointer_array", size, seed, "mixed", "stress", tuple(accesses))


def make_noisy(size: str, seed: int, *, length: int) -> Workload:
    rng = random.Random(seed)
    chain = list(make_pointer_chain("noisy_allocations", size, seed, length=length, passes=3, gap=12).accesses)
    fake_base = 0x900000 + seed * 0x20000
    noise = [
        Access(
            addr=fake_base + i * LINE,
            candidate=fake_base + rng.randrange(length * 4) * LINE,
            pointer_source=False,
            gap_after=7,
        )
        for i in range(length)
    ]
    accesses: list[Access] = []
    for idx, access in enumerate(chain):
        accesses.append(access)
        if idx < len(noise):
            accesses.append(noise[idx])
    return Workload("noisy_allocations", size, seed, "stress", "stress", tuple(accesses))


def make_branchy(size: str, seed: int, *, length: int) -> Workload:
    rng = random.Random(seed)
    base = 0xA00000 + seed * 0x30000
    nodes = [base + i * LINE * 13 for i in range(length)]
    accesses: list[Access] = []
    for _ in range(4):
        prev = None
        idx = rng.randrange(max(1, length // 4))
        for _step in range(length // 2):
            addr = nodes[idx]
            next_idx = (idx * 3 + seed + 1) % length
            candidate = nodes[next_idx]
            accesses.append(Access(addr=addr, candidate=candidate, source_addr=prev, gap_after=14))
            prev = addr
            idx = next_idx
    return Workload("branchy_pointer_chain", size, seed, "yes", "stress", tuple(accesses))


def workload_suite(mode: str = "quick") -> list[Workload]:
    sizes = {
        "small": 32,
        "medium": 96,
        "large": 192,
    }
    selected_sizes = ("small", "medium") if mode == "quick" else ("small", "medium", "large")
    workloads: list[Workload] = []
    for seed in (1, 2, 3):
        for size in selected_sizes:
            n = sizes[size]
            workloads.extend(
                [
                    make_pointer_chain("linked_list_traversal", size, seed, length=n, passes=4),
                    make_tree(size, seed, nodes=max(15, n // 2)),
                    make_hash(size, seed, buckets=max(4, n // 8), chain=6),
                    make_graph(size, seed, vertices=max(32, n), degree=3),
                    make_linear(size, seed, length=n * 2),
                    make_matrix(size, seed, side=max(6, n // 8)),
                    make_random_nonpointer(size, seed, length=n),
                    make_compute(size, seed, length=n),
                    make_mixed(size, seed, length=n),
                    make_noisy(size, seed, length=n),
                    make_branchy(size, seed, length=n),
                ]
            )
    return workloads


def run_config(workload: Workload, config: str, **kwargs: int | bool) -> Result:
    sim = ModelSimulator(config=config, **kwargs)
    return sim.run(workload)


def run_suite(mode: str = "quick", configs: tuple[str, ...] = ("no_prefetch", "next_line", "stride", "simple_pointer_chase", "copper")) -> list[Result]:
    results: list[Result] = []
    for workload in workload_suite(mode):
        for config in configs:
            kwargs = {}
            if config == "copper":
                kwargs["enable_queue_filter"] = True
            results.append(run_config(workload, config, **kwargs))
    return results


def grouped_results(results: list[Result]) -> dict[tuple[str, str, int], dict[str, Result]]:
    grouped: dict[tuple[str, str, int], dict[str, Result]] = defaultdict(dict)
    for result in results:
        grouped[(result.benchmark, result.input_name, result.seed)][result.config] = result
    return grouped
