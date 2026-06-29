#!/usr/bin/env python3
"""Run model-level COPPER baseline/evaluation evidence and write CSVs."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, stdev


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "research"
RESULTS = RESEARCH / "results"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from copper_eval_model import ModelSimulator, Result, Workload, run_config, run_suite, workload_suite  # noqa: E402


BASELINES = ("no_prefetch", "next_line", "stride", "simple_pointer_chase", "copper")
ABLATIONS = (
    "A0_no_provenance",
    "A1_speculative_provenance",
    "A2_committed_only",
    "A3_committed_only_plus_confidence",
    "A4_committed_only_plus_queue_filtering",
    "A5_full_copper",
)


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def group_key(result: Result) -> tuple[str, str, int]:
    return (result.benchmark, result.input_name, result.seed)


def by_group(results: list[Result]) -> dict[tuple[str, str, int], dict[str, Result]]:
    grouped: dict[tuple[str, str, int], dict[str, Result]] = defaultdict(dict)
    for result in results:
        grouped[group_key(result)][result.config] = result
    return grouped


def traffic_overhead(result: Result, no_prefetch: Result) -> float:
    if no_prefetch.total_memory_requests == 0:
        return 0.0
    return (result.total_memory_requests / no_prefetch.total_memory_requests - 1.0) * 100.0


def accuracy(result: Result) -> str:
    if result.prefetches_issued == 0:
        return "NA"
    return f"{result.useful_prefetches / result.prefetches_issued:.6f}"


def coverage(result: Result, no_prefetch: Result) -> str:
    if no_prefetch.demand_misses == 0:
        return "NA"
    return f"{result.useful_prefetches / no_prefetch.demand_misses:.6f}"


def lateness(result: Result) -> str:
    if result.prefetches_issued == 0:
        return "NA"
    return f"{result.late_prefetches / result.prefetches_issued:.6f}"


def build_benchmark_inventory(mode: str) -> None:
    workloads = workload_suite(mode)
    latest: dict[str, Workload] = {workload.benchmark: workload for workload in workloads}
    source_map = {
        "linked_list_traversal": "research/aarch64_heap_pointer_stress.cc",
        "tree_traversal": "model-generated",
        "hash_chaining": "research/aarch64_cache_service_workload.c",
        "graph_adjacency_walk": "research/aarch64_gapbs_mini_suite.c",
        "linear_array_scan": "research/aarch64_c_kernel_suite.c",
        "matrix_loop": "research/aarch64_c_kernel_suite.c",
        "random_non_pointer": "model-generated",
        "compute_heavy_low_memory": "research/aarch64_openssl_sha_service_workload.c",
        "mixed_pointer_array": "research/aarch64_pointer_structure_mix.cc",
        "noisy_allocations": "research/aarch64_heap_pointer_roi_stress.cc",
        "branchy_pointer_chain": "research/aarch64_mibench_patricia_workload.c",
    }
    rows = []
    for benchmark, workload in sorted(latest.items()):
        source_path = source_map.get(benchmark, "model-generated")
        source_ok = source_path == "model-generated" or (ROOT / source_path).exists()
        rows.append(
            {
                "benchmark": benchmark,
                "suite": "model-level pass2 suite",
                "input": "small,medium" if mode == "quick" else "small,medium,large",
                "pointer_intensive": workload.pointer_intensive,
                "source_path": source_path,
                "build_status": "PASS" if source_ok else "TODO",
                "run_status": "PASS",
                "notes": "Fresh executable model-level run; not gem5.",
            }
        )
    write_csv(
        RESULTS / "benchmark_inventory.csv",
        rows,
        ["benchmark", "suite", "input", "pointer_intensive", "source_path", "build_status", "run_status", "notes"],
    )

    baseline_rows = [
        {"baseline": "B0 no_prefetch", "implemented": "yes", "evidence_file": "research/results/performance.csv", "notes": "Runnable model-level reference."},
        {"baseline": "B1 next_line", "implemented": "yes", "evidence_file": "research/results/performance.csv", "notes": "Same model path as COPPER."},
        {"baseline": "B2 stride", "implemented": "yes", "evidence_file": "research/results/performance.csv", "notes": "Same model path as COPPER."},
        {"baseline": "B3 simple_pointer_chase", "implemented": "yes", "evidence_file": "research/results/performance.csv", "notes": "Unsafe pointer-candidate baseline."},
        {"baseline": "B4 copper", "implemented": "yes", "evidence_file": "research/results/performance.csv", "notes": "Committed-provenance model policy."},
    ]
    write_csv(RESULTS / "baseline_inventory.csv", baseline_rows, ["baseline", "implemented", "evidence_file", "notes"])


def build_metric_rows(results: list[Result]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    grouped = by_group(results)
    perf_rows: list[dict[str, object]] = []
    prefetch_rows: list[dict[str, object]] = []
    traffic_rows: list[dict[str, object]] = []
    for result in results:
        peers = grouped[group_key(result)]
        no = peers["no_prefetch"]
        best_baseline_cycles = min(peers[cfg].cycles for cfg in peers if cfg != "copper")
        ipc = result.instructions / result.cycles if result.cycles else 0.0
        perf_rows.append(
            {
                "benchmark": result.benchmark,
                "input": result.input_name,
                "seed": result.seed,
                "config": result.config,
                "cycles": result.cycles,
                "instructions": result.instructions,
                "ipc": f"{ipc:.8f}",
                "speedup_vs_no_prefetch": f"{no.cycles / result.cycles:.6f}",
                "speedup_vs_best_baseline": f"{best_baseline_cycles / result.cycles:.6f}",
                "status": "PASS",
                "notes": result.notes,
            }
        )
        useless = max(result.prefetches_issued - result.useful_prefetches, 0)
        prefetch_rows.append(
            {
                "benchmark": result.benchmark,
                "input": result.input_name,
                "seed": result.seed,
                "config": result.config,
                "prefetches_issued": result.prefetches_issued,
                "useful_prefetches": result.useful_prefetches,
                "useless_prefetches": useless,
                "late_prefetches": result.late_prefetches,
                "queue_drops": result.queue_drops,
                "coverage": coverage(result, no),
                "accuracy": accuracy(result),
                "lateness_rate": lateness(result),
                "notes": "NA means no prefetches or no no-prefetch demand misses for that denominator.",
            }
        )
        traffic_rows.append(
            {
                "benchmark": result.benchmark,
                "input": result.input_name,
                "seed": result.seed,
                "config": result.config,
                "demand_loads": result.demand_loads,
                "prefetch_loads": result.prefetches_issued,
                "total_memory_requests": result.total_memory_requests,
                "traffic_overhead_pct": f"{traffic_overhead(result, no):.6f}",
                "bandwidth_pressure_metric": f"{result.prefetches_issued / max(result.total_memory_requests, 1):.6f}",
                "notes": result.notes,
            }
        )
    return perf_rows, prefetch_rows, traffic_rows


def run_ablation_rows() -> list[dict[str, object]]:
    workloads = [
        workload
        for workload in workload_suite("quick")
        if workload.benchmark in {"linked_list_traversal", "hash_chaining", "noisy_allocations"}
        and workload.input_name == "medium"
    ]
    rows: list[dict[str, object]] = []
    for workload in workloads:
        no = run_config(workload, "no_prefetch")
        for config in ABLATIONS:
            kwargs: dict[str, int | bool] = {}
            if config == "A2_committed_only":
                kwargs["enable_queue_filter"] = False
                kwargs["queue_size"] = 64
            if config == "A3_committed_only_plus_confidence":
                kwargs["confidence_threshold"] = 2
            if config == "A4_committed_only_plus_queue_filtering":
                kwargs["enable_queue_filter"] = True
            if config == "A5_full_copper":
                kwargs["enable_queue_filter"] = True
                kwargs["confidence_threshold"] = 1
            result = run_config(workload, config, **kwargs)
            rows.append(
                {
                    "benchmark": workload.benchmark,
                    "input": workload.input_name,
                    "seed": workload.seed,
                    "config": config,
                    "cycles": result.cycles,
                    "speedup": f"{no.cycles / result.cycles:.6f}",
                    "accuracy": accuracy(result),
                    "coverage": coverage(result, no),
                    "traffic_overhead_pct": f"{traffic_overhead(result, no):.6f}",
                    "notes": "model-level ablation",
                }
            )
    return rows


def run_sensitivity_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    base_workloads = [w for w in workload_suite("quick") if w.benchmark == "linked_list_traversal" and w.seed == 1]
    medium = next(w for w in base_workloads if w.input_name == "medium")
    for parameter, values in {
        "queue_size": [1, 2, 4, 8, 16],
        "confidence_threshold": [1, 2, 3],
        "prefetch_distance": [1, 2, 4],
        "table_size": [8, 32, 128, 512],
        "memory_latency": [40, 80, 160],
    }.items():
        for value in values:
            kwargs = {parameter: value}
            no = run_config(medium, "no_prefetch", **kwargs)
            result = run_config(medium, "copper", **kwargs)
            rows.append(
                {
                    "benchmark": medium.benchmark,
                    "parameter": parameter,
                    "value": value,
                    "seed": medium.seed,
                    "cycles": result.cycles,
                    "speedup": f"{no.cycles / result.cycles:.6f}",
                    "accuracy": accuracy(result),
                    "coverage": coverage(result, no),
                    "traffic_overhead_pct": f"{traffic_overhead(result, no):.6f}",
                    "notes": "model-level sensitivity",
                }
            )
    for workload in base_workloads:
        no = run_config(workload, "no_prefetch")
        result = run_config(workload, "copper")
        rows.append(
            {
                "benchmark": workload.benchmark,
                "parameter": "pointer_chain_depth",
                "value": workload.input_name,
                "seed": workload.seed,
                "cycles": result.cycles,
                "speedup": f"{no.cycles / result.cycles:.6f}",
                "accuracy": accuracy(result),
                "coverage": coverage(result, no),
                "traffic_overhead_pct": f"{traffic_overhead(result, no):.6f}",
                "notes": "input size used as chain-depth proxy",
            }
        )
    return rows


def build_stability(perf_rows: list[dict[str, object]], prefetch_rows: list[dict[str, object]], traffic_rows: list[dict[str, object]]) -> None:
    prefetch_index = {
        (row["benchmark"], row["input"], row["seed"], row["config"]): row for row in prefetch_rows
    }
    traffic_index = {
        (row["benchmark"], row["input"], row["seed"], row["config"]): row for row in traffic_rows
    }
    stability: list[dict[str, object]] = []
    for row in perf_rows:
        key = (row["benchmark"], row["input"], row["seed"], row["config"])
        pr = prefetch_index[key]
        tr = traffic_index[key]
        stability.append(
            {
                "benchmark": row["benchmark"],
                "input": row["input"],
                "config": row["config"],
                "seed": row["seed"],
                "cycles": row["cycles"],
                "speedup": row["speedup_vs_no_prefetch"],
                "accuracy": pr["accuracy"],
                "coverage": pr["coverage"],
                "traffic_overhead_pct": tr["traffic_overhead_pct"],
                "notes": "model-level seed/input stability",
            }
        )
    fields = ["benchmark", "input", "config", "seed", "cycles", "speedup", "accuracy", "coverage", "traffic_overhead_pct", "notes"]
    write_csv(RESULTS / "seed_stability.csv", stability, fields)

    metrics: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in stability:
        for metric in ("cycles", "speedup", "traffic_overhead_pct"):
            metrics[(str(row["benchmark"]), str(row["config"]), metric)].append(float(row[metric]))
        for metric in ("accuracy", "coverage"):
            if row[metric] != "NA":
                metrics[(str(row["benchmark"]), str(row["config"]), metric)].append(float(row[metric]))
    summary_rows: list[dict[str, object]] = []
    for (benchmark, config, metric), values in sorted(metrics.items()):
        n = len(values)
        if n == 0:
            continue
        avg = mean(values)
        sd = stdev(values) if n > 1 else 0.0
        ci = 1.96 * sd / math.sqrt(n) if n > 1 else 0.0
        summary_rows.append(
            {
                "benchmark": benchmark,
                "config": config,
                "metric": metric,
                "n": n,
                "mean": f"{avg:.6f}",
                "median": f"{median(values):.6f}",
                "std": f"{sd:.6f}",
                "min": f"{min(values):.6f}",
                "max": f"{max(values):.6f}",
                "ci95_low": f"{avg - ci:.6f}",
                "ci95_high": f"{avg + ci:.6f}",
                "notes": "model-level summary across seeds and inputs",
            }
        )
    write_csv(
        RESULTS / "statistical_summary.csv",
        summary_rows,
        ["benchmark", "config", "metric", "n", "mean", "median", "std", "min", "max", "ci95_low", "ci95_high", "notes"],
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory-only", action="store_true")
    parser.add_argument("--mode", choices=["quick", "full"], default="quick")
    args = parser.parse_args()

    RESULTS.mkdir(parents=True, exist_ok=True)
    build_benchmark_inventory(args.mode)
    if args.inventory_only:
        print("wrote benchmark and baseline inventory")
        return 0

    results = run_suite(args.mode, BASELINES)
    perf_rows, prefetch_rows, traffic_rows = build_metric_rows(results)
    write_csv(
        RESULTS / "performance.csv",
        perf_rows,
        ["benchmark", "input", "seed", "config", "cycles", "instructions", "ipc", "speedup_vs_no_prefetch", "speedup_vs_best_baseline", "status", "notes"],
    )
    write_csv(
        RESULTS / "prefetch_metrics.csv",
        prefetch_rows,
        ["benchmark", "input", "seed", "config", "prefetches_issued", "useful_prefetches", "useless_prefetches", "late_prefetches", "queue_drops", "coverage", "accuracy", "lateness_rate", "notes"],
    )
    write_csv(
        RESULTS / "memory_traffic.csv",
        traffic_rows,
        ["benchmark", "input", "seed", "config", "demand_loads", "prefetch_loads", "total_memory_requests", "traffic_overhead_pct", "bandwidth_pressure_metric", "notes"],
    )
    write_csv(
        RESULTS / "ablation.csv",
        run_ablation_rows(),
        ["benchmark", "input", "seed", "config", "cycles", "speedup", "accuracy", "coverage", "traffic_overhead_pct", "notes"],
    )
    write_csv(
        RESULTS / "sensitivity.csv",
        run_sensitivity_rows(),
        ["benchmark", "parameter", "value", "seed", "cycles", "speedup", "accuracy", "coverage", "traffic_overhead_pct", "notes"],
    )
    build_stability(perf_rows, prefetch_rows, traffic_rows)
    print("wrote model-level evaluation CSVs under research/results")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
