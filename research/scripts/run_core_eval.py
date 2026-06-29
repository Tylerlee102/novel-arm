#!/usr/bin/env python3
"""Run a deterministic core-integrated COPPER validation harness.

This is not gem5. It uses the same generated workload traces and prefetch
configs as the model/cycle flows, then places the memory behavior behind a
simple in-order core envelope with fetch/issue width, reorder-window pressure,
load-queue pressure, and branch penalties. Rows are labeled core_integrated.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "research"
RESULTS = RESEARCH / "results"
LOG_DIR = RESULTS / "logs" / "core_integrated"
sys.path.insert(0, str(RESEARCH / "scripts"))

from copper_eval_model import Result, Workload, run_config  # noqa: E402
from run_cycle_eval import CONFIGS, CYCLE_KWARGS, cycle_workloads  # noqa: E402


EVIDENCE = "core_integrated"
SIMULATOR = "deterministic_core_integrated_model"
CORE_KWARGS: dict[str, int | bool] = {
    "memory_latency": 96,
    "hit_latency": 4,
    "prefetch_latency": 24,
    "queue_size": 10,
    "enable_queue_filter": True,
}
CORE_PARAMS = {
    "fetch_width": 4,
    "issue_width": 3,
    "rob_entries": 96,
    "load_queue_entries": 24,
    "mlp_limit": 6,
    "branch_mispredict_penalty": 11,
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def result_key(result: Result) -> tuple[str, str, int]:
    return (result.benchmark, result.input_name, result.seed)


def grouped(results: list[Result]) -> dict[tuple[str, str, int], dict[str, Result]]:
    out: dict[tuple[str, str, int], dict[str, Result]] = defaultdict(dict)
    for result in results:
        out[result_key(result)][result.config] = result
    return out


def workload_branch_factor(workload: Workload) -> float:
    if "branchy" in workload.benchmark or workload.benchmark == "patricia":
        return 0.060
    if workload.category == "negative":
        return 0.015
    if workload.category == "stress":
        return 0.035
    return 0.025


def core_cycles(result: Result, workload: Workload) -> tuple[int, dict[str, int]]:
    fetch = math.ceil(result.instructions / CORE_PARAMS["fetch_width"])
    issue = math.ceil(result.instructions / CORE_PARAMS["issue_width"])
    memory = result.cycles
    rob_pressure = max(0, result.demand_misses - CORE_PARAMS["mlp_limit"]) * 7
    loadq_pressure = max(0, result.prefetches_issued - CORE_PARAMS["load_queue_entries"]) * 2
    branch_penalty = int(result.instructions * workload_branch_factor(workload) / 12) * CORE_PARAMS["branch_mispredict_penalty"]
    retired = max(fetch, issue, memory) + rob_pressure + loadq_pressure + branch_penalty
    return retired, {
        "fetch_cycles": fetch,
        "issue_cycles": issue,
        "memory_cycles": memory,
        "rob_pressure_cycles": rob_pressure,
        "loadq_pressure_cycles": loadq_pressure,
        "branch_penalty_cycles": branch_penalty,
    }


def accuracy(result: Result) -> str:
    if result.prefetches_issued == 0:
        return "NA"
    useful = min(result.useful_prefetches, result.prefetches_issued)
    return f"{useful / result.prefetches_issued:.6f}"


def coverage(result: Result, no_prefetch: Result) -> str:
    if no_prefetch.demand_misses == 0:
        return "NA"
    useful = min(result.useful_prefetches, no_prefetch.demand_misses)
    return f"{useful / no_prefetch.demand_misses:.6f}"


def lateness(result: Result) -> str:
    if result.prefetches_issued == 0:
        return "NA"
    return f"{result.late_prefetches / result.prefetches_issued:.6f}"


def traffic_overhead(result: Result, no_prefetch: Result) -> float:
    no_total = max(no_prefetch.demand_loads + no_prefetch.prefetches_issued, 1)
    total = result.demand_loads + result.prefetches_issued
    return (total / no_total - 1.0) * 100.0


def run_suite() -> tuple[list[Workload], list[Result], list[Result]]:
    workloads = cycle_workloads()
    core_results: list[Result] = []
    cycle_reference: list[Result] = []
    for workload in workloads:
        for config in CONFIGS:
            core_results.append(run_config(workload, config, **CORE_KWARGS))
            cycle_reference.append(run_config(workload, config, **CYCLE_KWARGS))
    return workloads, core_results, cycle_reference


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "core_integrated_eval.jsonl"
    workloads, results, cycle_reference = run_suite()
    workload_by_key = {(w.benchmark, w.input_name, w.seed): w for w in workloads}
    cycle_by_result = {(r.benchmark, r.input_name, r.seed, r.config): r for r in cycle_reference}
    by_group = grouped(results)
    core_cycle_by_result: dict[tuple[str, str, int, str], int] = {}
    breakdown_by_result: dict[tuple[str, str, int, str], dict[str, int]] = {}
    for result in results:
        workload = workload_by_key[result_key(result)]
        cycles, breakdown = core_cycles(result, workload)
        core_cycle_by_result[(*result_key(result), result.config)] = cycles
        breakdown_by_result[(*result_key(result), result.config)] = breakdown

    perf_rows: list[dict[str, object]] = []
    prefetch_rows: list[dict[str, object]] = []
    traffic_rows: list[dict[str, object]] = []
    with log_path.open("w", encoding="utf-8") as log:
        for result in results:
            key = result_key(result)
            peers = by_group[key]
            no = peers["no_prefetch"]
            no_cycles = core_cycle_by_result[(*key, "no_prefetch")]
            cycles = core_cycle_by_result[(*key, result.config)]
            best_baseline = min(core_cycle_by_result[(*key, cfg)] for cfg in peers if cfg != "copper")
            speedup_vs_no = no_cycles / cycles if cycles else 0.0
            speedup_vs_best = best_baseline / cycles if cycles else 0.0
            cycle_ref = cycle_by_result[(*key, result.config)]
            ref_delta = ((cycles - cycle_ref.cycles) / cycle_ref.cycles * 100.0) if cycle_ref.cycles else 0.0
            notes = (
                "Deterministic core_integrated validation with fetch/issue width, ROB pressure, "
                "load-queue pressure, branch penalty, and memory-system timing. Not gem5."
            )
            if result.config == "copper" and speedup_vs_best < 1.0:
                notes += " COPPER is slower than the best baseline on this row; regression is retained."
            log.write(
                json.dumps(
                    {
                        "benchmark": result.benchmark,
                        "input": result.input_name,
                        "seed": result.seed,
                        "config": result.config,
                        "core_params": CORE_PARAMS,
                        "memory_params": CORE_KWARGS,
                        "core_cycles": cycles,
                        "cycle_model_reference_cycles": cycle_ref.cycles,
                        "cycle_reference_delta_pct": round(ref_delta, 6),
                        "breakdown": breakdown_by_result[(*key, result.config)],
                    },
                    sort_keys=True,
                )
                + "\n"
            )
            perf_rows.append(
                {
                    "benchmark": result.benchmark,
                    "input": result.input_name,
                    "seed": result.seed,
                    "config": result.config,
                    "evidence_level": EVIDENCE,
                    "simulator": SIMULATOR,
                    "cycles": cycles,
                    "instructions": result.instructions,
                    "ipc": f"{result.instructions / cycles:.8f}" if cycles else "0.00000000",
                    "cache_misses": result.demand_misses,
                    "memory_stalls": result.demand_misses * int(CORE_KWARGS["memory_latency"]) + result.late_prefetches * int(CORE_KWARGS["memory_latency"]),
                    "speedup_vs_no_prefetch": f"{speedup_vs_no:.6f}",
                    "speedup_vs_best_baseline": f"{speedup_vs_best:.6f}",
                    "status": "PASS",
                    "log_path": rel(log_path),
                    "notes": notes,
                }
            )
            useful = min(result.useful_prefetches, result.prefetches_issued)
            prefetch_rows.append(
                {
                    "benchmark": result.benchmark,
                    "input": result.input_name,
                    "seed": result.seed,
                    "config": result.config,
                    "evidence_level": EVIDENCE,
                    "simulator": SIMULATOR,
                    "prefetches_issued": result.prefetches_issued,
                    "useful_prefetches": useful,
                    "useless_prefetches": max(result.prefetches_issued - useful, 0),
                    "late_prefetches": result.late_prefetches,
                    "queue_drops": result.queue_drops,
                    "coverage": coverage(result, no),
                    "accuracy": accuracy(result),
                    "lateness_rate": lateness(result),
                    "log_path": rel(log_path),
                    "notes": "NA means no prefetches or no no-prefetch misses for that denominator.",
                }
            )
            total = result.demand_loads + result.prefetches_issued
            traffic_rows.append(
                {
                    "benchmark": result.benchmark,
                    "input": result.input_name,
                    "seed": result.seed,
                    "config": result.config,
                    "evidence_level": EVIDENCE,
                    "simulator": SIMULATOR,
                    "demand_loads": result.demand_loads,
                    "prefetch_loads": result.prefetches_issued,
                    "total_memory_requests": total,
                    "traffic_overhead_pct": f"{traffic_overhead(result, no):.6f}",
                    "bandwidth_pressure_metric": f"{total / max(cycles / 1000.0, 1.0):.6f}",
                    "log_path": rel(log_path),
                    "notes": "Bandwidth pressure is total memory requests per 1000 modeled core cycles.",
                }
            )

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
    prefetch_fields = [
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
    write_csv(RESULTS / "core_integrated_performance.csv", perf_rows, perf_fields)
    write_csv(RESULTS / "core_integrated_prefetch_metrics.csv", prefetch_rows, prefetch_fields)
    write_csv(RESULTS / "core_integrated_memory_traffic.csv", traffic_rows, traffic_fields)
    print("wrote core-integrated evaluation CSVs under research/results")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
