#!/usr/bin/env python3
"""Summarize local gem5 COPPER experiments."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"

STAT_NAMES = {
    "simTicks": "sim_ticks",
    "simInsts": "sim_insts",
    "system.cpu.numCycles": "cycles",
    "system.cpu.dcache.overallMisses::total": "dcache_misses",
    "system.cpu.dcache.overallMissRate::total": "dcache_miss_rate",
    "system.cpu.dcache.demandMshrMisses::total": "demand_mshr_misses",
    "system.cpu.dcache.HardPFReq.mshrMisses::total": "hardpf_mshr_misses",
    "system.cpu.dcache.prefetcher.pfIssued": "pf_issued",
    "system.cpu.dcache.prefetcher.pfUseful": "pf_useful",
    "system.cpu.dcache.prefetcher.pfUnused": "pf_unused",
    "system.cpu.dcache.prefetcher.pfUsefulButMiss": "pf_useful_but_miss",
    "system.cpu.dcache.prefetcher.pfIdentified": "pf_identified",
    "system.cpu.dcache.prefetcher.candidateLoads": "candidate_loads",
    "system.cpu.dcache.prefetcher.pointerLikeCandidates": "pointer_like",
    "system.cpu.dcache.prefetcher.learnedProofs": "learned_proofs",
    "system.cpu.dcache.prefetcher.allowedCandidates": "allowed_candidates",
    "system.cpu.dcache.prefetcher.blockedNoProvenance": "blocked_no_provenance",
    "system.cpu.dcache.prefetcher.retainedEvictionProofs": "retained_eviction_proofs",
    "system.cpu.dcache.prefetcher.prefetchFillCandidates": "prefetch_fill_candidates",
    "system.cpu.dcache.prefetcher.fillPrefetchQueued": "fill_prefetch_queued",
    "system.cpu.dcache.prefetcher.fillPrefetchIssued": "fill_prefetch_issued",
    "system.cpu.dcache.prefetcher.fillPrefetchDroppedCrossPage": "fill_prefetch_drop_cross_page",
    "system.cpu.dcache.prefetcher.fillPrefetchTranslated": "fill_prefetch_translated",
    "system.cpu.dcache.prefetcher.fillPrefetchTranslatedIssued": "fill_prefetch_translated_issued",
    "system.cpu.dcache.prefetcher.fillPrefetchTranslationUnavailable": "fill_prefetch_translation_unavailable",
    "system.cpu.dcache.prefetcher.carriedProvenanceHits": "carried_provenance_hits",
    "system.cpu.dcache.prefetcher.carriedProvenanceMisses": "carried_provenance_misses",
    "system.cpu.dcache.prefetcher.carriedProvenanceEvictions": "carried_provenance_evictions",
    "system.l2cache.overallMisses::total": "l2_overall_misses",
    "system.l2cache.overallAccesses::total": "l2_overall_accesses",
    "system.l2cache.demandMisses::total": "l2_demand_misses",
    "system.l2cache.demandMisses::cpu.data": "l2_demand_misses_cpu_data",
    "system.mem_ctrl.dram.bytesRead::total": "dram_bytes_read",
    "system.mem_ctrl.dram.bytesWritten::total": "dram_bytes_written",
    "system.mem_ctrl.dram.avgRdBW": "dram_avg_rd_bw",
    "system.l2bus.pktCount::total": "l2bus_pkt_count",
    "system.l2bus.pktSize::total": "l2bus_pkt_size",
    "system.cpu.numRecvRespBytes": "cpu_recv_resp_bytes",
}

EXPERIMENTS = [
    ("sequential_full", "none", "gem5_copper_none"),
    ("sequential_full", "naive", "gem5_copper_naive"),
    ("sequential_full", "copper_cptq", "gem5_sequential_copper_cptq"),
    ("sequential_full", "copper_rec", "gem5_sequential_copper_rec"),
    ("sequential_full", "stride", "gem5_copper_stride"),
    ("pageperm_seed7", "none", "gem5_pageperm_none"),
    ("pageperm_seed7", "naive", "gem5_pageperm_naive"),
    ("pageperm_seed7", "copper_cptq", "gem5_pageperm_s7_copper_cptq"),
    ("pageperm_seed7", "copper_rec", "gem5_pageperm_s7_copper_rec"),
    ("pageperm_seed7", "stride", "gem5_pageperm_stride"),
    ("random_seed1", "none", "gem5_random_s1_none"),
    ("random_seed1", "copper_samepage", "gem5_random_s1_copper"),
    ("random_seed1", "copper_cptq", "gem5_random_s1_copper_cptq"),
    ("random_seed1", "copper_rec", "gem5_random_s1_copper_rec"),
    ("random_seed1", "stride", "gem5_random_s1_stride"),
    ("medium_256_pageperm", "none", "gem5_med_pageperm_none"),
    ("medium_256_pageperm", "copper_cptq", "gem5_med_pageperm_copper_cptq"),
    ("medium_256_pageperm", "copper_rec", "gem5_med_pageperm_copper_rec"),
    ("medium_256_pageperm", "stride", "gem5_med_pageperm_stride"),
    ("aarch64_256_pageperm", "none", "gem5_a64_small_none"),
    ("aarch64_256_pageperm", "copper_rec", "gem5_a64_small_copper_rec"),
    ("aarch64_256_pageperm", "stride", "gem5_a64_small_stride"),
    ("aarch64_256_random", "none", "gem5_a64_random_small_none"),
    ("aarch64_256_random", "copper_rec", "gem5_a64_random_small_copper_rec"),
    ("aarch64_256_random", "stride", "gem5_a64_random_small_stride"),
    ("aarch64_pageperm", "none", "gem5_a64_pageperm_none"),
    ("aarch64_pageperm", "copper_rec", "gem5_a64_pageperm_copper_rec"),
    ("aarch64_pageperm", "stride", "gem5_a64_pageperm_stride"),
    ("aarch64_random", "none", "gem5_a64_random_none"),
    ("aarch64_random", "copper_rec", "gem5_a64_random_copper_rec"),
    ("aarch64_random", "stride", "gem5_a64_random_stride"),
    ("aarch64_pageperm_minor", "none", "gem5_a64_pageperm_minor_none"),
    ("aarch64_pageperm_minor", "copper_rec", "gem5_a64_pageperm_minor_copper_rec"),
    ("aarch64_pageperm_minor", "stride", "gem5_a64_pageperm_minor_stride"),
    ("aarch64_random_minor", "none", "gem5_a64_random_minor_none"),
    ("aarch64_random_minor", "copper_rec", "gem5_a64_random_minor_copper_rec"),
    ("aarch64_random_minor", "stride", "gem5_a64_random_minor_stride"),
    ("aarch64_pageperm_o3", "none", "gem5_a64_pageperm_o3_none"),
    ("aarch64_pageperm_o3", "copper_rec", "gem5_a64_pageperm_o3_copper_rec"),
    ("aarch64_pageperm_o3", "stride", "gem5_a64_pageperm_o3_stride"),
    ("aarch64_random_o3", "none", "gem5_a64_random_o3_none"),
    ("aarch64_random_o3", "copper_rec", "gem5_a64_random_o3_copper_rec"),
    ("aarch64_random_o3", "stride", "gem5_a64_random_o3_stride"),
]

for seed in range(1, 6):
    EXPERIMENTS.extend(
        [
            (f"pageperm_seed{seed}", "none", f"gem5_pageperm_s{seed}_none"),
            (f"pageperm_seed{seed}", "copper", f"gem5_pageperm_s{seed}_copper"),
            (f"pageperm_seed{seed}", "copper_rec", f"gem5_pageperm_s{seed}_copper_rec"),
            (f"pageperm_seed{seed}", "stride", f"gem5_pageperm_s{seed}_stride"),
        ]
    )

for seed in range(2, 4):
    EXPERIMENTS.extend(
        [
            (f"random_seed{seed}", "none", f"gem5_random_s{seed}_none"),
            (f"random_seed{seed}", "copper_rec", f"gem5_random_s{seed}_copper_rec"),
            (f"random_seed{seed}", "stride", f"gem5_random_s{seed}_stride"),
        ]
    )


def parse_stats(path: Path) -> dict[str, float]:
    stats: dict[str, float] = {}
    if not path.exists() or path.stat().st_size == 0:
        return stats

    stat_re = re.compile(r"^(\S+)\s+([-+0-9.eE]+)\s")
    for line in path.read_text(errors="replace").splitlines():
        match = stat_re.match(line)
        if not match:
            continue
        name, value = match.groups()
        if name in STAT_NAMES:
            parsed = float(value)
            if parsed.is_integer():
                parsed = int(parsed)
            stats[STAT_NAMES[name]] = parsed
    return stats


def main() -> None:
    rows = []
    for workload, prefetcher, directory in EXPERIMENTS:
        stats = parse_stats(RESULTS / directory / "stats.txt")
        if not stats:
            continue
        row = {
            "workload": workload,
            "prefetcher": prefetcher,
            "result_dir": directory,
        }
        for key in STAT_NAMES.values():
            row[key] = stats.get(key, 0)
        rows.append(row)

    baseline_ticks = {
        row["workload"]: row["sim_ticks"]
        for row in rows
        if row["prefetcher"] == "none"
    }
    for row in rows:
        base = baseline_ticks.get(row["workload"])
        ticks = row["sim_ticks"]
        row["speedup_vs_none_pct"] = 0 if not base else (base / ticks - 1.0) * 100.0

    columns = [
        "workload",
        "prefetcher",
        "speedup_vs_none_pct",
        "sim_ticks",
        "cycles",
        "sim_insts",
        "dcache_misses",
        "dcache_miss_rate",
        "demand_mshr_misses",
        "hardpf_mshr_misses",
        "pf_issued",
        "pf_useful",
        "pf_unused",
        "pf_useful_but_miss",
        "pf_identified",
        "candidate_loads",
        "pointer_like",
        "learned_proofs",
        "allowed_candidates",
        "blocked_no_provenance",
        "retained_eviction_proofs",
        "prefetch_fill_candidates",
        "fill_prefetch_queued",
        "fill_prefetch_issued",
        "fill_prefetch_drop_cross_page",
        "fill_prefetch_translated",
        "fill_prefetch_translated_issued",
        "fill_prefetch_translation_unavailable",
        "carried_provenance_hits",
        "carried_provenance_misses",
        "carried_provenance_evictions",
        "l2_overall_misses",
        "l2_overall_accesses",
        "l2_demand_misses",
        "l2_demand_misses_cpu_data",
        "dram_bytes_read",
        "dram_bytes_written",
        "dram_avg_rd_bw",
        "l2bus_pkt_count",
        "l2bus_pkt_size",
        "cpu_recv_resp_bytes",
        "result_dir",
    ]

    csv_path = RESULTS / "gem5_copper_summary.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    md_path = RESULTS / "GEM5_COPPER_SUMMARY.md"
    lines = [
        "# gem5 COPPER Summary",
        "",
        "All runs use ARM syscall-emulation mode with private L1I/L1D, L2, and DDR3 timing memory. Most ARM32/AArch64 headline runs use `ArmTimingSimpleCPU`; the CPU-model sensitivity rows additionally use `ArmMinorCPU` and `ArmO3CPU`.",
        "",
        "## Headline Results",
        "",
        "| Workload | Prefetcher | Speedup vs none | Ticks | D$ misses | Demand MSHR misses | PF MSHR misses | PF issued | Fill candidates | Carried hits | Translated PF | Translation drops | COPPER proofs | COPPER allowed |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    headline = {
        "sequential_full",
        "pageperm_seed7",
        "random_seed1",
        "medium_256_pageperm",
        "aarch64_256_pageperm",
        "aarch64_256_random",
        "aarch64_pageperm",
        "aarch64_random",
        "aarch64_pageperm_minor",
        "aarch64_random_minor",
        "aarch64_pageperm_o3",
        "aarch64_random_o3",
    }
    for row in rows:
        if row["workload"] not in headline:
            continue
        lines.append(
            "| {workload} | {prefetcher} | {speedup:.2f}% | {ticks} | {misses} | {demand_mshr} | {hardpf_mshr} | {pf} | {fill_candidates} | {carried_hits} | {translated} | {tdrop} | {proofs} | {allowed} |".format(
                workload=row["workload"],
                prefetcher=row["prefetcher"],
                speedup=row["speedup_vs_none_pct"],
                ticks=row["sim_ticks"],
                misses=row["dcache_misses"],
                demand_mshr=row["demand_mshr_misses"],
                hardpf_mshr=row["hardpf_mshr_misses"],
                pf=row["pf_issued"],
                fill_candidates=row["prefetch_fill_candidates"],
                carried_hits=row["carried_provenance_hits"],
                translated=row["fill_prefetch_translated_issued"],
                tdrop=row["fill_prefetch_translation_unavailable"],
                proofs=row["learned_proofs"],
                allowed=row["allowed_candidates"],
            )
        )

    seed_rows = [
        row
        for row in rows
        if row["workload"].startswith("pageperm_seed")
        and row["prefetcher"] in {"copper", "copper_cptq", "copper_rec", "stride"}
    ]
    copper_speedups = [
        row["speedup_vs_none_pct"] for row in seed_rows if row["prefetcher"] == "copper_rec"
    ]
    stride_speedups = [
        row["speedup_vs_none_pct"] for row in seed_rows if row["prefetcher"] == "stride"
    ]
    if copper_speedups and stride_speedups:
        lines.extend(
            [
                "",
                "## Five-Seed Page-Permute Stability",
                "",
                f"Recursive COPPER speedup range: {min(copper_speedups):.2f}% to {max(copper_speedups):.2f}%.",
                f"Stride speedup range: {min(stride_speedups):.2f}% to {max(stride_speedups):.2f}%.",
            ]
        )

    random_seed_rows = [
        row
        for row in rows
        if row["workload"].startswith("random_seed")
        and row["prefetcher"] in {"copper_rec", "stride"}
    ]
    random_copper_speedups = [
        row["speedup_vs_none_pct"] for row in random_seed_rows if row["prefetcher"] == "copper_rec"
    ]
    random_stride_speedups = [
        row["speedup_vs_none_pct"] for row in random_seed_rows if row["prefetcher"] == "stride"
    ]
    if random_copper_speedups and random_stride_speedups:
        lines.extend(
            [
                "",
                "## Three-Seed Random Stability",
                "",
                f"Recursive COPPER speedup range: {min(random_copper_speedups):.2f}% to {max(random_copper_speedups):.2f}%.",
                f"Stride speedup range: {min(random_stride_speedups):.2f}% to {max(random_stride_speedups):.2f}%.",
            ]
        )

    aarch64_rows = [
        row
        for row in rows
        if row["workload"].startswith("aarch64_")
        and row["prefetcher"] in {"copper_rec", "stride"}
    ]
    if aarch64_rows:
        lines.extend(
            [
                "",
                "## AArch64 Smoke, Full-List, and CPU-Model Runs",
                "",
                "| Workload | Prefetcher | Speedup vs none | Ticks | Demand MSHR misses | PF MSHR misses | Carried hits |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in aarch64_rows:
            lines.append(
                "| {workload} | {prefetcher} | {speedup:.2f}% | {ticks} | {demand_mshr} | {hardpf_mshr} | {carried_hits} |".format(
                    workload=row["workload"],
                    prefetcher=row["prefetcher"],
                    speedup=row["speedup_vs_none_pct"],
                    ticks=row["sim_ticks"],
                    demand_mshr=row["demand_mshr_misses"],
                    hardpf_mshr=row["hardpf_mshr_misses"],
                    carried_hits=row["carried_provenance_hits"],
                )
            )

    cpu_model_rows = [
        row
        for row in rows
        if row["workload"] in {
            "aarch64_pageperm",
            "aarch64_random",
            "aarch64_pageperm_minor",
            "aarch64_random_minor",
            "aarch64_pageperm_o3",
            "aarch64_random_o3",
        }
        and row["prefetcher"] in {"copper_rec", "stride"}
    ]
    if cpu_model_rows:
        lines.extend(
            [
                "",
                "## AArch64 CPU-Model Sensitivity",
                "",
                "| CPU model/workload | COPPER speedup | Stride speedup |",
                "|---|---:|---:|",
            ]
        )
        by_workload: dict[str, dict[str, float]] = {}
        for row in cpu_model_rows:
            by_workload.setdefault(row["workload"], {})[row["prefetcher"]] = row[
                "speedup_vs_none_pct"
            ]
        for workload in [
            "aarch64_pageperm",
            "aarch64_random",
            "aarch64_pageperm_minor",
            "aarch64_random_minor",
            "aarch64_pageperm_o3",
            "aarch64_random_o3",
        ]:
            values = by_workload.get(workload, {})
            if "copper_rec" not in values or "stride" not in values:
                continue
            lines.append(
                f"| {workload} | {values['copper_rec']:.2f}% | {values['stride']:.2f}% |"
            )

    traffic_workloads = [
        "aarch64_pageperm",
        "aarch64_random",
        "aarch64_pageperm_minor",
        "aarch64_random_minor",
        "aarch64_pageperm_o3",
        "aarch64_random_o3",
    ]
    traffic_rows = [
        row
        for row in rows
        if row["workload"] in traffic_workloads
        and row["prefetcher"] in {"none", "copper_rec", "stride"}
    ]
    if traffic_rows:
        lines.extend(
            [
                "",
                "## AArch64 Traffic and Waste Proxy",
                "",
                "| Workload | Prefetcher | Speedup | L2 misses | DRAM read bytes | L2 bus bytes | PF unused |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for workload in traffic_workloads:
            for prefetcher in ["none", "copper_rec", "stride"]:
                row = next(
                    (
                        item
                        for item in traffic_rows
                        if item["workload"] == workload
                        and item["prefetcher"] == prefetcher
                    ),
                    None,
                )
                if not row:
                    continue
                lines.append(
                    "| {workload} | {prefetcher} | {speedup:.2f}% | {l2_misses} | {dram_read} | {l2bus_bytes} | {pf_unused} |".format(
                        workload=row["workload"],
                        prefetcher=row["prefetcher"],
                        speedup=row["speedup_vs_none_pct"],
                        l2_misses=row["l2_overall_misses"],
                        dram_read=row["dram_bytes_read"],
                        l2bus_bytes=row["l2bus_pkt_size"],
                        pf_unused=row["pf_unused"],
                    )
                )

        by_pair = {
            (row["workload"], row["prefetcher"]): row for row in traffic_rows
        }
        lines.extend(["", "Traffic deltas for recursive COPPER versus no prefetcher:"])
        for workload in traffic_workloads:
            none = by_pair.get((workload, "none"))
            copper = by_pair.get((workload, "copper_rec"))
            if not none or not copper:
                continue
            base_bytes = none["dram_bytes_read"]
            copper_bytes = copper["dram_bytes_read"]
            byte_delta_pct = (
                0
                if not base_bytes
                else (copper_bytes / base_bytes - 1.0) * 100.0
            )
            l2_delta = copper["l2_overall_misses"] - none["l2_overall_misses"]
            lines.append(
                f"- {workload}: {copper['speedup_vs_none_pct']:.2f}% speedup with {byte_delta_pct:.2f}% DRAM-read-byte delta and {l2_delta:+} L2 misses."
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Sequential lists are not a favorable headline for COPPER because a stride prefetcher can infer the layout without provenance.",
            "- Page-permuted lists are a better COPPER stress test: stride loses most of its advantage, while recursive COPPER retains a repeatable speedup.",
            "- Fully random lists exposed two prototype limitations. CPTQ removed the same-page-only issue path, and recursive carried provenance then allowed prefetched pointer lines to seed more proof-gated prefetches.",
            "- Recursive carried provenance is still proof-gated: a prefetched line can seed a new dereference only when the source word/value already has committed provenance in the ledger.",
            "- `pfUseful` remains low in gem5's counter accounting because many benefits appear as demand-visible MSHR misses converted into prefetch-origin MSHR misses rather than ordinary cache-hit conversions.",
            "- The observed timing gain comes from converting demand-visible MSHR misses into prefetch-origin MSHR misses, not from reducing the raw D-cache miss count.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n")

    print(csv_path)
    print(md_path)


if __name__ == "__main__":
    main()
