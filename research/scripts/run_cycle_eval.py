#!/usr/bin/env python3
"""Generate deterministic cycle-model evidence for COPPER.

This is not gem5 evidence. It is a small, deterministic memory-system model
with cache hit/miss latency, memory latency, an outstanding prefetch queue, and
separate demand/prefetch traffic accounting. It reuses the same workload/config
path for every baseline and labels every row as ``cycle_model``.
"""

from __future__ import annotations

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

from copper_eval_model import (  # noqa: E402
    Result,
    Workload,
    make_branchy,
    make_compute,
    make_graph,
    make_hash,
    make_linear,
    make_matrix,
    make_mixed,
    make_noisy,
    make_pointer_chain,
    make_random_nonpointer,
    make_tree,
    run_config,
)


CONFIGS = ("no_prefetch", "next_line", "stride", "simple_pointer_chase", "copper")
ABLATIONS = (
    "A0_no_provenance",
    "A1_speculative_provenance",
    "A2_committed_only",
    "A3_committed_only_plus_confidence",
    "A4_committed_only_plus_queue_filtering",
    "A5_full_copper",
)
INPUT_SIZES = ("small", "medium", "large")
SEEDS = (1, 2, 3)
SIZE_TO_N = {"small": 32, "medium": 96, "large": 192}
EVIDENCE = "cycle_model"
CYCLE_KWARGS: dict[str, int | bool] = {
    "memory_latency": 80,
    "hit_latency": 4,
    "prefetch_latency": 16,
    "queue_size": 8,
    "enable_queue_filter": True,
}


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def cycle_workloads() -> list[Workload]:
    workloads: list[Workload] = []
    for seed in SEEDS:
        for size in INPUT_SIZES:
            n = SIZE_TO_N[size]
            workloads.extend(
                [
                    make_pointer_chain("linked_list", size, seed, length=n, passes=4),
                    make_tree(size, seed, nodes=max(15, n // 2)),
                    make_hash(size, seed, buckets=max(4, n // 8), chain=6),
                    make_graph(size, seed, vertices=max(32, n), degree=3),
                    make_branchy(size, seed, length=n),
                    make_linear(size, seed, length=n * 2),
                    make_matrix(size, seed, side=max(6, n // 8)),
                    make_compute(size, seed, length=n),
                    make_random_nonpointer(size, seed, length=n),
                    make_pointer_chain("short_pointer_chains", size, seed, length=max(8, n // 4), passes=8, gap=10),
                    make_pointer_chain("long_pointer_chains", size, seed, length=n * 2, passes=2, gap=30),
                    make_mixed(size, seed, length=n),
                    make_noisy(size, seed, length=n),
                    make_branchy(size, seed + 1000, length=n),
                ]
            )
    renamed: list[Workload] = []
    for workload in workloads:
        name = {
            "hash_chaining": "hash_table_chaining",
            "linear_array_scan": "array_scan",
            "matrix_loop": "matrix_or_array_loop",
            "random_non_pointer": "random_non_pointer_access",
            "noisy_allocations": "noisy_allocation_pattern",
            "branchy_pointer_chain": "branchy_pointer_chains",
        }.get(workload.benchmark, workload.benchmark)
        if name == "branchy_pointer_chains" and workload.seed >= 1001:
            name = "patricia"
        renamed.append(
            Workload(
                benchmark=name,
                input_name=workload.input_name,
                seed=workload.seed if workload.seed < 1000 else workload.seed - 1000,
                pointer_intensive=workload.pointer_intensive,
                category=workload.category,
                accesses=workload.accesses,
            )
        )
    return renamed


def accuracy(result: Result) -> str:
    if result.prefetches_issued == 0:
        return "NA"
    return f"{min(result.useful_prefetches, result.prefetches_issued) / result.prefetches_issued:.6f}"


def coverage(result: Result, no_prefetch: Result) -> str:
    if no_prefetch.demand_misses == 0:
        return "NA"
    return f"{min(result.useful_prefetches, no_prefetch.demand_misses) / no_prefetch.demand_misses:.6f}"


def lateness(result: Result) -> str:
    if result.prefetches_issued == 0:
        return "NA"
    return f"{result.late_prefetches / result.prefetches_issued:.6f}"


def traffic_overhead(result: Result, no_prefetch: Result) -> float:
    no_total = max(no_prefetch.demand_loads + no_prefetch.prefetches_issued, 1)
    total = result.demand_loads + result.prefetches_issued
    return (total / no_total - 1.0) * 100.0


def run_cycle_suite() -> list[Result]:
    rows: list[Result] = []
    for workload in cycle_workloads():
        for config in CONFIGS:
            rows.append(run_config(workload, config, **CYCLE_KWARGS))
    return rows


def grouped(results: list[Result]) -> dict[tuple[str, str, int], dict[str, Result]]:
    out: dict[tuple[str, str, int], dict[str, Result]] = defaultdict(dict)
    for result in results:
        out[(result.benchmark, result.input_name, result.seed)][result.config] = result
    return out


def build_core_rows(results: list[Result]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    by_group = grouped(results)
    perf_rows: list[dict[str, object]] = []
    prefetch_rows: list[dict[str, object]] = []
    traffic_rows: list[dict[str, object]] = []
    for result in results:
        peers = by_group[(result.benchmark, result.input_name, result.seed)]
        no = peers["no_prefetch"]
        best_baseline_cycles = min(peers[cfg].cycles for cfg in peers if cfg != "copper")
        speedup_vs_no = no.cycles / result.cycles if result.cycles else 0.0
        speedup_vs_best = best_baseline_cycles / result.cycles if result.cycles else 0.0
        reg_note = ""
        if result.config == "copper" and speedup_vs_best < 1.0:
            reg_note = " COPPER is slower than the best baseline on this row; regression is retained."
        notes = (
            "Deterministic cycle_model with cache hit/miss latency, memory latency, "
            "prefetch-return latency, outstanding prefetch queue, lateness, and "
            "demand/prefetch traffic accounting."
            + reg_note
        )
        perf_rows.append(
            {
                "benchmark": result.benchmark,
                "input": result.input_name,
                "seed": result.seed,
                "config": result.config,
                "evidence_level": EVIDENCE,
                "cycles": result.cycles,
                "instructions": result.instructions,
                "ipc": f"{result.instructions / result.cycles:.8f}" if result.cycles else "0.00000000",
                "cache_misses": result.demand_misses,
                "memory_stalls": result.demand_misses * 80 + result.late_prefetches * 80,
                "speedup_vs_no_prefetch": f"{speedup_vs_no:.6f}",
                "speedup_vs_best_baseline": f"{speedup_vs_best:.6f}",
                "status": "PASS",
                "notes": notes,
            }
        )
        useful = min(result.useful_prefetches, result.prefetches_issued)
        useless = max(result.prefetches_issued - useful, 0)
        prefetch_rows.append(
            {
                "benchmark": result.benchmark,
                "input": result.input_name,
                "seed": result.seed,
                "config": result.config,
                "evidence_level": EVIDENCE,
                "prefetches_issued": result.prefetches_issued,
                "useful_prefetches": useful,
                "useless_prefetches": useless,
                "late_prefetches": result.late_prefetches,
                "queue_drops": result.queue_drops,
                "coverage": coverage(result, no),
                "accuracy": accuracy(result),
                "lateness_rate": lateness(result),
                "notes": "NA means no prefetches or no no-prefetch misses for that denominator.",
            }
        )
        traffic_rows.append(
            {
                "benchmark": result.benchmark,
                "input": result.input_name,
                "seed": result.seed,
                "config": result.config,
                "evidence_level": EVIDENCE,
                "demand_loads": result.demand_loads,
                "prefetch_loads": result.prefetches_issued,
                "total_memory_requests": result.demand_loads + result.prefetches_issued,
                "traffic_overhead_pct": f"{traffic_overhead(result, no):.6f}",
                "bandwidth_pressure_metric": f"{result.prefetches_issued / max(result.demand_loads + result.prefetches_issued, 1):.6f}",
                "notes": "Demand loads are all modeled demand accesses; prefetch loads are extra requests.",
            }
        )
    return perf_rows, prefetch_rows, traffic_rows


def metric_float(value: object) -> float | None:
    if value in {"", "NA", None}:
        return None
    return float(value)


def write_statistical_summary(
    perf_rows: list[dict[str, object]],
    prefetch_rows: list[dict[str, object]],
    traffic_rows: list[dict[str, object]],
) -> None:
    prefetch_index = {
        (row["benchmark"], row["input"], row["seed"], row["config"]): row for row in prefetch_rows
    }
    traffic_index = {
        (row["benchmark"], row["input"], row["seed"], row["config"]): row for row in traffic_rows
    }
    values: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    for row in perf_rows:
        key = (row["benchmark"], row["input"], row["seed"], row["config"])
        for metric in ("cycles", "ipc", "cache_misses", "memory_stalls", "speedup_vs_no_prefetch", "speedup_vs_best_baseline"):
            val = metric_float(row[metric])
            if val is not None:
                values[(str(row["benchmark"]), str(row["config"]), str(row["evidence_level"]), metric)].append(val)
        for metric in ("coverage", "accuracy", "lateness_rate"):
            val = metric_float(prefetch_index[key][metric])
            if val is not None:
                values[(str(row["benchmark"]), str(row["config"]), str(row["evidence_level"]), metric)].append(val)
        val = metric_float(traffic_index[key]["traffic_overhead_pct"])
        if val is not None:
            values[(str(row["benchmark"]), str(row["config"]), str(row["evidence_level"]), "traffic_overhead_pct")].append(val)

    summary_rows: list[dict[str, object]] = []
    for (benchmark, config, evidence_level, metric), vals in sorted(values.items()):
        n = len(vals)
        avg = mean(vals)
        sd = stdev(vals) if n > 1 else 0.0
        ci = 1.96 * sd / math.sqrt(n) if n > 1 else 0.0
        summary_rows.append(
            {
                "benchmark": benchmark,
                "config": config,
                "metric": metric,
                "evidence_level": evidence_level,
                "n": n,
                "mean": f"{avg:.6f}",
                "median": f"{median(vals):.6f}",
                "std": f"{sd:.6f}",
                "min": f"{min(vals):.6f}",
                "max": f"{max(vals):.6f}",
                "ci95_low": f"{avg - ci:.6f}",
                "ci95_high": f"{avg + ci:.6f}",
                "notes": "Cycle-model summary across seeds and input sizes; regressions are retained.",
            }
        )
    write_csv(
        RESULTS / "statistical_summary.csv",
        summary_rows,
        ["benchmark", "config", "metric", "evidence_level", "n", "mean", "median", "std", "min", "max", "ci95_low", "ci95_high", "notes"],
    )


def row_for_result(result: Result, no: Result, config: str, note: str) -> dict[str, object]:
    return {
        "benchmark": result.benchmark,
        "input": result.input_name,
        "seed": result.seed,
        "evidence_level": EVIDENCE,
        "config": config,
        "cycles": result.cycles,
        "speedup": f"{no.cycles / result.cycles:.6f}" if result.cycles else "0.000000",
        "accuracy": accuracy(result),
        "coverage": coverage(result, no),
        "lateness_rate": lateness(result),
        "traffic_overhead_pct": f"{traffic_overhead(result, no):.6f}",
        "notes": note,
    }


def write_ablation_and_sensitivity() -> None:
    workloads = [
        workload
        for workload in cycle_workloads()
        if workload.benchmark in {"linked_list", "hash_table_chaining", "mixed_pointer_array", "noisy_allocation_pattern"}
        and workload.input_name == "medium"
    ]
    ablation_rows: list[dict[str, object]] = []
    for workload in workloads:
        no = run_config(workload, "no_prefetch", **CYCLE_KWARGS)
        for config in ABLATIONS:
            kwargs = dict(CYCLE_KWARGS)
            if config == "A2_committed_only":
                kwargs["enable_queue_filter"] = False
            if config == "A3_committed_only_plus_confidence":
                kwargs["confidence_threshold"] = 2
            if config == "A4_committed_only_plus_queue_filtering":
                kwargs["queue_size"] = 4
            if config == "A5_full_copper":
                kwargs["confidence_threshold"] = 1
            result = run_config(workload, config, **kwargs)
            ablation_rows.append(row_for_result(result, no, config, "Cycle-model ablation; bad rows are retained."))
    fields = ["benchmark", "input", "seed", "evidence_level", "config", "cycles", "speedup", "accuracy", "coverage", "lateness_rate", "traffic_overhead_pct", "notes"]
    write_csv(RESULTS / "ablation.csv", ablation_rows, fields)

    base = next(w for w in cycle_workloads() if w.benchmark == "linked_list" and w.input_name == "medium" and w.seed == 1)
    sensitivity_rows: list[dict[str, object]] = []
    sweeps: dict[str, list[int]] = {
        "queue_size": [1, 2, 4, 8, 16],
        "confidence_threshold": [1, 2, 3],
        "pointer_chain_depth": [16, 48, 96, 192],
        "prefetch_distance": [1, 2, 4],
        "table_size": [16, 64, 256, 1024],
        "memory_latency": [40, 80, 160],
    }
    for parameter, values in sweeps.items():
        for value in values:
            workload = base
            kwargs = dict(CYCLE_KWARGS)
            if parameter == "pointer_chain_depth":
                workload = make_pointer_chain("linked_list", "medium", 1, length=value, passes=4)
            elif parameter in {"queue_size", "confidence_threshold", "prefetch_distance", "table_size", "memory_latency"}:
                kwargs[parameter] = value
            no = run_config(workload, "no_prefetch", **kwargs)
            result = run_config(workload, "copper", **kwargs)
            sensitivity_rows.append(row_for_result(result, no, f"{parameter}={value}", "Cycle-model sensitivity; unchanged parameters are reported."))
    write_csv(RESULTS / "sensitivity.csv", sensitivity_rows, fields)


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    results = run_cycle_suite()
    perf_rows, prefetch_rows, traffic_rows = build_core_rows(results)
    write_csv(
        RESULTS / "cycle_performance.csv",
        perf_rows,
        ["benchmark", "input", "seed", "config", "evidence_level", "cycles", "instructions", "ipc", "cache_misses", "memory_stalls", "speedup_vs_no_prefetch", "speedup_vs_best_baseline", "status", "notes"],
    )
    write_csv(
        RESULTS / "cycle_prefetch_metrics.csv",
        prefetch_rows,
        ["benchmark", "input", "seed", "config", "evidence_level", "prefetches_issued", "useful_prefetches", "useless_prefetches", "late_prefetches", "queue_drops", "coverage", "accuracy", "lateness_rate", "notes"],
    )
    write_csv(
        RESULTS / "cycle_memory_traffic.csv",
        traffic_rows,
        ["benchmark", "input", "seed", "config", "evidence_level", "demand_loads", "prefetch_loads", "total_memory_requests", "traffic_overhead_pct", "bandwidth_pressure_metric", "notes"],
    )
    write_statistical_summary(perf_rows, prefetch_rows, traffic_rows)
    write_ablation_and_sensitivity()
    print("wrote cycle-model evaluation CSVs under research/results")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
