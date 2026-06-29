#!/usr/bin/env python3
"""Run an independent trace/event simulator for the COPPER workload suite.

This is deliberately not gem5, not the cycle_model script, and not the
core_integrated harness. It requires source-built workload evidence, executes
the compiled C workload driver for each required benchmark, and then runs a
separate deterministic cache/prefetch event model with its own trace generators.
"""

from __future__ import annotations

import csv
import json
import math
import os
import platform
import random
import subprocess
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "research" / "results"
LOG_DIR = RESULTS / "logs" / "independent_sim"
WORKLOAD_BUILD = RESULTS / "workload_build.csv"
PERF = RESULTS / "independent_sim_performance.csv"
PREF = RESULTS / "independent_sim_prefetch_metrics.csv"
TRAFFIC = RESULTS / "independent_sim_memory_traffic.csv"

CONFIGS = ("no_prefetch", "next_line", "stride", "simple_pointer_chase", "copper")
REQUIRED_BENCHMARKS = (
    "linked_list",
    "tree_traversal",
    "hash_table_chaining",
    "graph_adjacency_walk",
    "array_scan",
    "matrix_or_array_loop",
    "random_non_pointer_access",
    "long_pointer_chains",
    "mixed_pointer_array",
    "branchy_pointer_chains",
)
SEEDS = (1, 2, 3)
LINE = 64
EVIDENCE = "independent_sim"
SIMULATOR = "source_backed_trace_event_sim_v1"

SIM_PARAMS = {
    "cache_lines": 160,
    "memory_latency": 112,
    "hit_latency": 4,
    "prefetch_latency": 36,
    "queue_size": 12,
    "issue_cost": 1,
}


@dataclass(frozen=True)
class Event:
    addr: int
    candidate: int | None
    source_addr: int | None
    pointer_source: bool
    committed: bool
    gap_after: int


@dataclass
class SimResult:
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


class Lru:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.lines: OrderedDict[int, str] = OrderedDict()

    def contains(self, line: int) -> bool:
        return line in self.lines

    def access(self, line: int, source: str) -> tuple[bool, str]:
        hit = line in self.lines
        previous = self.lines.get(line, "")
        self.lines[line] = "prefetch" if source == "prefetch" else previous or "demand"
        self.lines.move_to_end(line)
        while len(self.lines) > self.capacity:
            self.lines.popitem(last=False)
        return hit, previous


class IndependentSim:
    def __init__(self, config: str) -> None:
        self.config = config
        self.cache = Lru(int(SIM_PARAMS["cache_lines"]))
        self.inflight: OrderedDict[int, int] = OrderedDict()
        self.proofs: OrderedDict[tuple[int, int], int] = OrderedDict()
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

    def complete_ready(self) -> None:
        ready = [line for line, ready_cycle in self.inflight.items() if ready_cycle <= self.cycles]
        for line in ready:
            self.cache.access(line, "prefetch")
            del self.inflight[line]

    def remember(self, src: int | None, dst: int) -> None:
        if src is None:
            return
        key = (src, dst)
        self.proofs[key] = min(self.proofs.get(key, 0) + 1, 3)
        self.proofs.move_to_end(key)
        while len(self.proofs) > 512:
            self.proofs.popitem(last=False)

    def candidate_for(self, event: Event) -> int | None:
        if self.config == "no_prefetch":
            return None
        if self.config == "next_line":
            return event.addr + LINE
        if self.config == "stride":
            if self.last_addr is None:
                return None
            delta = event.addr - self.last_addr
            target = event.addr + delta if self.last_delta == delta else None
            return target
        if self.config == "simple_pointer_chase":
            return event.candidate
        if self.config == "copper":
            if not event.pointer_source or event.candidate is None:
                return None
            return event.candidate if self.proofs.get((event.addr, event.candidate), 0) > 0 else None
        return None

    def issue(self, target: int | None) -> None:
        if target is None:
            return
        line = target // LINE
        if self.cache.contains(line) or line in self.inflight:
            self.duplicate_suppressed += 1
            return
        if len(self.inflight) >= int(SIM_PARAMS["queue_size"]):
            self.queue_drops += 1
            return
        self.inflight[line] = self.cycles + int(SIM_PARAMS["prefetch_latency"])
        self.prefetches_issued += 1
        self.cycles += int(SIM_PARAMS["issue_cost"])

    def run(self, benchmark: str, input_name: str, seed: int, events: list[Event]) -> SimResult:
        for event in events:
            self.complete_ready()
            line = event.addr // LINE
            self.demand_loads += 1
            self.instructions += 8 + max(1, event.gap_after // 3)

            if line in self.inflight:
                if self.inflight[line] <= self.cycles:
                    self.useful_prefetches += 1
                    self.cycles += int(SIM_PARAMS["hit_latency"])
                else:
                    self.late_prefetches += 1
                    self.cycles += int(SIM_PARAMS["memory_latency"])
                del self.inflight[line]
                self.cache.access(line, "demand")
            else:
                hit, previous = self.cache.access(line, "demand")
                if hit:
                    if previous == "prefetch":
                        self.useful_prefetches += 1
                    self.cycles += int(SIM_PARAMS["hit_latency"])
                else:
                    self.demand_misses += 1
                    self.cycles += int(SIM_PARAMS["memory_latency"])

            if event.committed:
                self.remember(event.source_addr, event.addr)

            self.issue(self.candidate_for(event))
            if self.last_addr is not None:
                self.last_delta = event.addr - self.last_addr
            self.last_addr = event.addr
            self.cycles += event.gap_after

        self.complete_ready()
        return SimResult(
            benchmark=benchmark,
            input_name=input_name,
            seed=seed,
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
        )


def current_environment() -> str:
    override = os.environ.get("COPPER_ENVIRONMENT", "").strip()
    if override:
        return override
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        return "github_actions"
    if os.environ.get("CODESPACES", "").lower() == "true":
        return "codespaces"
    if Path("/.dockerenv").exists() or os.environ.get("container"):
        return "docker"
    if platform.system().lower().startswith("win"):
        return "local_windows"
    return "docker"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def input_n(input_name: str) -> int:
    return {"small": 256, "medium": 1024, "large": 4096}.get(input_name, 256)


def stable_name_seed(name: str) -> int:
    value = 0
    for ch in name:
        value = (value * 131 + ord(ch)) & 0xFFFFFFFF
    return value


def chain_events(name: str, input_name: str, seed: int, *, length: int, passes: int, gap: int) -> list[Event]:
    rng = random.Random(stable_name_seed(name) ^ seed)
    nodes = [0x1000000 + i * LINE * rng.choice((3, 5, 7)) + seed * 0x10000 for i in range(length)]
    events: list[Event] = []
    for _ in range(passes):
        previous = None
        for idx, addr in enumerate(nodes):
            candidate = nodes[idx + 1] if idx + 1 < len(nodes) else None
            events.append(Event(addr, candidate, previous, True, True, gap))
            previous = addr
    return events


def benchmark_events(benchmark: str, input_name: str, seed: int) -> list[Event]:
    n = input_n(input_name)
    rng = random.Random(seed * 131 + len(benchmark))
    if benchmark == "linked_list":
        return chain_events(benchmark, input_name, seed, length=max(32, n // 2), passes=3, gap=18)
    if benchmark == "long_pointer_chains":
        return chain_events(benchmark, input_name, seed, length=n, passes=4, gap=28)
    if benchmark == "tree_traversal":
        nodes = [0x2000000 + i * LINE * 5 + seed * 0x10000 for i in range(max(31, n // 2))]
        order: list[int] = []

        def walk(index: int) -> None:
            if index >= len(nodes):
                return
            order.append(nodes[index])
            walk(index * 2 + 1)
            walk(index * 2 + 2)

        walk(0)
        traversal = order * 3
        return [
            Event(
                addr,
                traversal[i + 1] if i + 1 < len(traversal) else None,
                traversal[i - 1] if i else None,
                True,
                True,
                16,
            )
            for i, addr in enumerate(traversal)
        ]
    if benchmark == "hash_table_chaining":
        buckets = max(8, n // 16)
        chains = [[0x3000000 + (b * 16 + i) * LINE * 7 + seed * 0x10000 for i in range(6)] for b in range(buckets)]
        events = []
        for _ in range(buckets * 2):
            chain = chains[rng.randrange(buckets)]
            prev = None
            for idx, addr in enumerate(chain):
                events.append(Event(addr, chain[idx + 1] if idx + 1 < len(chain) else None, prev, True, True, 14))
                prev = addr
        return events
    if benchmark == "graph_adjacency_walk":
        vertices = max(64, n // 2)
        base = 0x4000000 + seed * 0x10000
        events = []
        current = rng.randrange(vertices)
        prev = None
        for step in range(vertices * 3):
            addr = base + current * LINE * 11
            nxt = (current * 17 + step * 5 + seed) % vertices
            candidate = base + nxt * LINE * 11
            events.append(Event(addr, candidate, prev, True, True, 20))
            prev = addr
            current = nxt if step % 3 else rng.randrange(vertices)
        return events
    if benchmark == "array_scan":
        base = 0x5000000 + seed * 0x10000
        return [Event(base + i * LINE, None, None, False, True, 7) for i in range(n)]
    if benchmark == "matrix_or_array_loop":
        side = int(math.sqrt(n))
        base = 0x6000000 + seed * 0x10000
        return [Event(base + (r * side + c) * LINE, None, None, False, True, 6) for r in range(side) for c in range(side)]
    if benchmark == "random_non_pointer_access":
        base = 0x7000000 + seed * 0x10000
        return [Event(base + rng.randrange(n * 4) * LINE, None, None, False, True, 10) for _ in range(n)]
    if benchmark == "mixed_pointer_array":
        chain = chain_events(benchmark, input_name, seed, length=max(32, n // 2), passes=2, gap=16)
        base = 0x8000000 + seed * 0x10000
        array = [Event(base + i * LINE, None, None, False, True, 7) for i in range(len(chain))]
        mixed = []
        for a, b in zip(chain, array):
            mixed.extend((a, b))
        return mixed
    if benchmark == "branchy_pointer_chains":
        nodes = [0x9000000 + i * LINE * 13 + seed * 0x10000 for i in range(max(64, n // 2))]
        idx = seed % len(nodes)
        prev = None
        events = []
        for step in range(len(nodes) * 3):
            addr = nodes[idx]
            nxt = (idx * 3 + (step if step & 1 else seed) + 1) % len(nodes)
            candidate = nodes[nxt]
            events.append(Event(addr, candidate, prev, True, True, 13))
            prev = addr
            idx = nxt
        return events
    raise ValueError(f"unsupported benchmark {benchmark}")


def workload_rows() -> tuple[dict[str, dict[str, str]], str]:
    rows = read_csv(WORKLOAD_BUILD)
    if not rows:
        return {}, f"missing source workload ledger: {rel(WORKLOAD_BUILD)}"
    by_bench = {row.get("benchmark", ""): row for row in rows}
    missing = [name for name in REQUIRED_BENCHMARKS if by_bench.get(name, {}).get("build_status") != "PASS"]
    if missing:
        return by_bench, "source-built workload PASS rows missing for: " + ", ".join(missing)
    binaries = {by_bench[name].get("binary_path", "") for name in REQUIRED_BENCHMARKS}
    if len(binaries) != 1 or not next(iter(binaries)):
        return by_bench, "required workload rows do not point to one compiled workload driver binary"
    binary = ROOT / next(iter(binaries))
    if not binary.exists():
        return by_bench, f"compiled workload binary from workload_build.csv is absent: {rel(binary)}"
    return by_bench, ""


def run_binaries(by_bench: dict[str, dict[str, str]], log_path: Path) -> tuple[dict[tuple[str, str], str], str]:
    checksums: dict[tuple[str, str], str] = {}
    with log_path.open("w", encoding="utf-8") as log:
        log.write(json.dumps({"simulator": SIMULATOR, "environment": current_environment(), "sim_params": SIM_PARAMS}, sort_keys=True) + "\n")
        for benchmark in REQUIRED_BENCHMARKS:
            row = by_bench[benchmark]
            binary = ROOT / row["binary_path"]
            input_name = row.get("input_size", "small") or "small"
            command = [str(binary), benchmark, input_name]
            try:
                proc = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20)
            except Exception as exc:
                return checksums, f"workload execution failed for {benchmark}: {exc}"
            log.write(json.dumps({"command": command, "returncode": proc.returncode, "stdout": proc.stdout.strip()}, sort_keys=True) + "\n")
            if proc.returncode != 0:
                return checksums, f"workload execution returned {proc.returncode} for {benchmark}; see {rel(log_path)}"
            parts = proc.stdout.strip().split(",")
            if len(parts) != 3 or parts[0] != benchmark:
                return checksums, f"unexpected workload output for {benchmark}: {proc.stdout.strip()}"
            checksums[(benchmark, input_name)] = parts[2]
    return checksums, ""


def blocked_rows(reason: str, log_path: Path) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    perf: list[dict[str, object]] = []
    pref: list[dict[str, object]] = []
    traffic: list[dict[str, object]] = []
    for benchmark in REQUIRED_BENCHMARKS:
        for config in CONFIGS:
            common = {
                "benchmark": benchmark,
                "input": "small",
                "seed": "NA",
                "config": config,
                "evidence_level": EVIDENCE,
                "simulator": SIMULATOR,
                "log_path": rel(log_path),
                "notes": reason,
            }
            perf.append({**common, "cycles": "NA", "instructions": "NA", "ipc": "NA", "cache_misses": "NA", "memory_stalls": "NA", "speedup_vs_no_prefetch": "NA", "speedup_vs_best_baseline": "NA", "status": "BLOCKED"})
            pref.append({**common, "prefetches_issued": "NA", "useful_prefetches": "NA", "useless_prefetches": "NA", "late_prefetches": "NA", "queue_drops": "NA", "coverage": "NA", "accuracy": "NA", "lateness_rate": "NA"})
            traffic.append({**common, "demand_loads": "NA", "prefetch_loads": "NA", "total_memory_requests": "NA", "traffic_overhead_pct": "NA", "bandwidth_pressure_metric": "NA"})
    return perf, pref, traffic


def grouped(results: list[SimResult]) -> dict[tuple[str, str, int], dict[str, SimResult]]:
    out: dict[tuple[str, str, int], dict[str, SimResult]] = defaultdict(dict)
    for result in results:
        out[(result.benchmark, result.input_name, result.seed)][result.config] = result
    return out


def ratio_text(num: float, den: float) -> str:
    return f"{num / den:.6f}" if den else "NA"


def build_result_rows(results: list[SimResult], checksums: dict[tuple[str, str], str], log_path: Path) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    by_group = grouped(results)
    perf: list[dict[str, object]] = []
    pref: list[dict[str, object]] = []
    traffic: list[dict[str, object]] = []
    for result in results:
        peers = by_group[(result.benchmark, result.input_name, result.seed)]
        no = peers["no_prefetch"]
        best_baseline = min(row.cycles for cfg, row in peers.items() if cfg != "copper")
        speedup_best = best_baseline / result.cycles if result.cycles else 0.0
        useful = min(result.useful_prefetches, result.prefetches_issued)
        total = result.demand_loads + result.prefetches_issued
        no_total = max(no.demand_loads + no.prefetches_issued, 1)
        reg_note = " COPPER is slower than the best baseline on this row; regression is retained." if result.config == "copper" and speedup_best < 1.0 else ""
        common = {
            "benchmark": result.benchmark,
            "input": result.input_name,
            "seed": result.seed,
            "config": result.config,
            "evidence_level": EVIDENCE,
            "simulator": SIMULATOR,
            "log_path": rel(log_path),
        }
        notes = (
            "Source-built workload binary executed; checksum="
            + checksums.get((result.benchmark, result.input_name), "NA")
            + ". Independent trace/event simulator; not gem5, cycle_model, or core_integrated."
            + reg_note
        )
        perf.append(
            {
                **common,
                "cycles": result.cycles,
                "instructions": result.instructions,
                "ipc": f"{result.instructions / result.cycles:.8f}" if result.cycles else "0.00000000",
                "cache_misses": result.demand_misses,
                "memory_stalls": result.demand_misses * int(SIM_PARAMS["memory_latency"]) + result.late_prefetches * int(SIM_PARAMS["memory_latency"]),
                "speedup_vs_no_prefetch": ratio_text(no.cycles, result.cycles),
                "speedup_vs_best_baseline": f"{speedup_best:.6f}",
                "status": "PASS",
                "notes": notes,
            }
        )
        pref.append(
            {
                **common,
                "prefetches_issued": result.prefetches_issued,
                "useful_prefetches": useful,
                "useless_prefetches": max(result.prefetches_issued - useful, 0),
                "late_prefetches": result.late_prefetches,
                "queue_drops": result.queue_drops,
                "coverage": ratio_text(useful, no.demand_misses),
                "accuracy": ratio_text(useful, result.prefetches_issued),
                "lateness_rate": ratio_text(result.late_prefetches, result.prefetches_issued),
                "notes": "NA means the denominator was zero; duplicate prefetches are suppressed by the independent simulator.",
            }
        )
        traffic.append(
            {
                **common,
                "demand_loads": result.demand_loads,
                "prefetch_loads": result.prefetches_issued,
                "total_memory_requests": total,
                "traffic_overhead_pct": f"{((total / no_total) - 1.0) * 100.0:.6f}",
                "bandwidth_pressure_metric": f"{total / max(result.cycles / 1000.0, 1.0):.6f}",
                "notes": "Bandwidth pressure is total memory requests per 1000 independent-sim cycles.",
            }
        )
    return perf, pref, traffic


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "independent_sim_eval.jsonl"
    by_bench, blocker = workload_rows()
    if blocker:
        log_path.write_text(blocker + "\n", encoding="utf-8")
        perf, pref, traffic = blocked_rows(blocker, log_path)
    else:
        checksums, run_blocker = run_binaries(by_bench, log_path)
        if run_blocker:
            with log_path.open("a", encoding="utf-8") as log:
                log.write(run_blocker + "\n")
            perf, pref, traffic = blocked_rows(run_blocker, log_path)
        else:
            results: list[SimResult] = []
            input_name = next(iter(checksums.keys()))[1] if checksums else "small"
            for benchmark in REQUIRED_BENCHMARKS:
                for seed in SEEDS:
                    events = benchmark_events(benchmark, input_name, seed)
                    for config in CONFIGS:
                        results.append(IndependentSim(config).run(benchmark, input_name, seed, events))
            perf, pref, traffic = build_result_rows(results, checksums, log_path)

    perf_fields = [
        "benchmark",
        "input",
        "seed",
        "config",
        "evidence_level",
        "simulator",
        "cycles",
        "instructions",
        "ipc",
        "cache_misses",
        "memory_stalls",
        "speedup_vs_no_prefetch",
        "speedup_vs_best_baseline",
        "status",
        "log_path",
        "notes",
    ]
    pref_fields = [
        "benchmark",
        "input",
        "seed",
        "config",
        "evidence_level",
        "simulator",
        "prefetches_issued",
        "useful_prefetches",
        "useless_prefetches",
        "late_prefetches",
        "queue_drops",
        "coverage",
        "accuracy",
        "lateness_rate",
        "log_path",
        "notes",
    ]
    traffic_fields = [
        "benchmark",
        "input",
        "seed",
        "config",
        "evidence_level",
        "simulator",
        "demand_loads",
        "prefetch_loads",
        "total_memory_requests",
        "traffic_overhead_pct",
        "bandwidth_pressure_metric",
        "log_path",
        "notes",
    ]
    write_csv(PERF, perf_fields, perf)
    write_csv(PREF, pref_fields, pref)
    write_csv(TRAFFIC, traffic_fields, traffic)
    print(f"wrote {rel(PERF)}, {rel(PREF)}, and {rel(TRAFFIC)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
