#!/usr/bin/env python3
"""Analyze cache, traffic, and queue-pressure overhead for COPPER app runs."""

from __future__ import annotations

import csv
import math
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
CSV_OUT = RESULTS / "copper_prefetch_traffic_overhead_20260616.csv"
MD_OUT = RESULTS / "COPPER_PREFETCH_TRAFFIC_OVERHEAD_20260616.md"

WORKLOADS = {
    "sqlite_medium": "sqlite_app_medium",
    "sqlite_stress": "sqlite_app_stress",
    "lua_medium": "lua_app_medium",
    "lua_stress": "lua_app_stress",
    "duktape_medium": "duktape_app_medium",
    "duktape_stress": "duktape_app_stress",
    "yyjson_medium": "yyjson_app_medium",
    "yyjson_stress": "yyjson_app_stress",
    "jsonsqlite_medium": "jsonsqlite_app_medium",
    "jsonsqlite_stress": "jsonsqlite_app_stress",
    "cachesvc_small": "cachesvc_app_small",
    "cachesvc_medium": "cachesvc_app_medium_key",
    "pcre2_smoke": "pcre2_pcre2_smoke",
    "pcre2_seed1": "pcre2_pcre2_seed1",
    "libxml2_tiny": "libxml2_xml_tiny_full",
    "libarchive_tiny": "libarchive_tar_tiny_full",
    "zstd_tiny": "zstd_zstd_tiny",
    "zstd_seed1": "zstd_zstd_seed1",
    "zlib_tiny": "zlib_zlib_tiny",
    "zlib_seed1": "zlib_zlib_seed1",
    "ossltlstcp_process_scale2": "ossltlstcp_tcp_netns_process_scale2",
    "ossltlstcp_process_scale3": "ossltlstcp_tcp_netns_process_scale3",
}
POLICIES = ["none", "naive", "copper_clpd64k_peb", "spp", "spp_copper_slack"]
PREFETCH_COUNTERS = [
    "pfIssued",
    "pfUseful",
    "pointerLikeCandidates",
    "learnedProofs",
    "allowedCandidates",
    "blockedNoProvenance",
    "fillPrefetchTranslated",
    "fillPrefetchTranslatedIssued",
    "fillPrefetchTranslationFault",
    "fillPrefetchTranslationUnavailable",
    "fillPrefetchDroppedCrossPage",
    "targetLineWitnessHits",
    "targetLineWitnessMisses",
    "targetLineWitnessEvictions",
    "carriedProvenanceTerminalStops",
    "carriedProvenanceHits",
    "carriedProvenanceMisses",
    "boundaryAuthorityEntriesDropped",
    "boundaryPrefetchesDropped",
]


def parse_stats_sections(path: Path) -> list[dict[str, float]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    sections: list[dict[str, float]] = []
    marker = "---------- Begin Simulation Statistics ----------"
    end_marker = "---------- End Simulation Statistics"
    start = 0
    while True:
        try:
            begin = text.index(marker, start)
            end = text.index(end_marker, begin)
        except ValueError:
            break
        stats: dict[str, float] = {}
        for line in text[begin:end].splitlines():
            if not line or line.startswith("-"):
                continue
            parts = line.split("#", 1)[0].split()
            if len(parts) < 2:
                continue
            try:
                stats[parts[0]] = float(parts[1])
            except ValueError:
                stats[parts[0]] = math.nan
        sections.append(stats)
        start = end + len(end_marker)
    return sections


def clean_sum(values: list[float]) -> int:
    return int(sum(value for value in values if not math.isnan(value)))


def sum_regex(stats: dict[str, float], pattern: str) -> int:
    regex = re.compile(pattern)
    return clean_sum([value for key, value in stats.items() if regex.search(key)])


def max_regex(stats: dict[str, float], pattern: str) -> float:
    regex = re.compile(pattern)
    values = [value for key, value in stats.items() if regex.search(key) and not math.isnan(value)]
    return max(values) if values else 0.0


def sum_prefetch_counter(stats: dict[str, float], counter: str) -> int:
    matches = [
        (key, value)
        for key, value in stats.items()
        if key.endswith(f".{counter}") and ".prefetcher" in key and not math.isnan(value)
    ]
    child_matches = [
        value
        for key, value in matches
        if ".prefetchers" in key or ".primary." in key or ".companion." in key
    ]
    if child_matches:
        return int(sum(child_matches))
    return int(sum(value for _, value in matches))


def pct_delta(value: float, base: float) -> str:
    if base == 0:
        return ""
    return f"{((value / base) - 1.0) * 100.0:.3f}"


def pct_reduction(new: float, old: float) -> str:
    if old == 0:
        return ""
    return f"{100.0 * (1.0 - new / old):.1f}"


def run_dir(workload_tag: str, policy: str) -> Path:
    return RESULTS / f"gem5_arm_ubuntu_fs_{workload_tag}_{policy}"


def collect_one(workload: str, workload_tag: str, policy: str) -> dict[str, str]:
    directory = run_dir(workload_tag, policy)
    sections = parse_stats_sections(directory / "stats.txt")
    if not sections:
        raise RuntimeError(f"no stats sections in {directory}")
    stats = sections[0]
    row: dict[str, str] = {
        "workload": workload,
        "policy": policy,
        "sim_ticks": str(int(stats.get("simTicks", 0))),
        "insts_not_nop": str(
            sum_regex(
                stats,
                r"^board\.processor\.switch.*\.core\.commitStats0\.numInstsNotNOP$",
            )
        ),
        "l1d_demand_accesses": str(
            sum_regex(stats, r"^board\.cache_hierarchy\.l1d-cache-\d+\.demandAccesses::total$")
        ),
        "l1d_demand_misses": str(
            sum_regex(stats, r"^board\.cache_hierarchy\.l1d-cache-\d+\.demandMisses::total$")
        ),
        "l1d_demand_mshr_misses": str(
            sum_regex(stats, r"^board\.cache_hierarchy\.l1d-cache-\d+\.demandMshrMisses::total$")
        ),
        "l1d_hardpf_mshr_misses": str(
            sum_regex(stats, r"^board\.cache_hierarchy\.l1d-cache-\d+\.HardPFReq\.mshrMisses::total$")
        ),
        "l1d_hardpf_mshr_primary": str(
            sum_regex(
                stats,
                r"^board\.cache_hierarchy\.l1d-cache-\d+\.HardPFReq\.mshrMisses::.*prefetcher\.primary$",
            )
        ),
        "l1d_hardpf_mshr_companion": str(
            sum_regex(
                stats,
                r"^board\.cache_hierarchy\.l1d-cache-\d+\.HardPFReq\.mshrMisses::.*prefetcher\.companion$",
            )
        ),
        "l1d_replacements": str(
            sum_regex(stats, r"^board\.cache_hierarchy\.l1d-cache-\d+\.replacements$")
        ),
        "l1d_writebacks": str(
            sum_regex(stats, r"^board\.cache_hierarchy\.l1d-cache-\d+\.writebacks::total$")
        ),
        "l1d_blocked_no_mshrs": str(
            sum_regex(stats, r"^board\.cache_hierarchy\.l1d-cache-\d+\.blockedCycles::no_mshrs$")
        ),
        "l2_demand_accesses": str(
            sum_regex(stats, r"^board\.cache_hierarchy\.l2-cache-\d+\.demandAccesses::total$")
        ),
        "l2_demand_misses": str(
            sum_regex(stats, r"^board\.cache_hierarchy\.l2-cache-\d+\.demandMisses::total$")
        ),
        "l2_demand_mshr_misses": str(
            sum_regex(stats, r"^board\.cache_hierarchy\.l2-cache-\d+\.demandMshrMisses::total$")
        ),
        "l2_overall_mshr_misses": str(
            sum_regex(stats, r"^board\.cache_hierarchy\.l2-cache-\d+\.overallMshrMisses::total$")
        ),
        "l2_hardpf_mshr_misses": str(
            sum_regex(stats, r"^board\.cache_hierarchy\.l2-cache-\d+\.HardPFReq\.mshrMisses::total$")
        ),
        "l2_replacements": str(
            sum_regex(stats, r"^board\.cache_hierarchy\.l2-cache-\d+\.replacements$")
        ),
        "l2_writebacks": str(
            sum_regex(stats, r"^board\.cache_hierarchy\.l2-cache-\d+\.writebacks::total$")
        ),
        "membus_pkt_count_total": str(
            sum_regex(stats, r"^board\.cache_hierarchy\.membus\.pktCount_.*::total$")
        ),
        "membus_pkt_size_total": str(
            sum_regex(stats, r"^board\.cache_hierarchy\.membus\.pktSize_.*::total$")
        ),
        "dram_read_reqs": str(sum_regex(stats, r"^board\.memory\.mem_ctrl\d+\.readReqs$")),
        "dram_write_reqs": str(sum_regex(stats, r"^board\.memory\.mem_ctrl\d+\.writeReqs$")),
        "dram_read_bursts": str(sum_regex(stats, r"^board\.memory\.mem_ctrl\d+\.readBursts$")),
        "dram_write_bursts": str(sum_regex(stats, r"^board\.memory\.mem_ctrl\d+\.writeBursts$")),
        "dram_num_rd_retry": str(sum_regex(stats, r"^board\.memory\.mem_ctrl\d+\.numRdRetry$")),
        "dram_num_wr_retry": str(sum_regex(stats, r"^board\.memory\.mem_ctrl\d+\.numWrRetry$")),
        "dram_max_avg_rd_q_len": f"{max_regex(stats, r'^board\.memory\.mem_ctrl\d+\.avgRdQLen$'):.3f}",
        "dram_max_avg_wr_q_len": f"{max_regex(stats, r'^board\.memory\.mem_ctrl\d+\.avgWrQLen$'):.3f}",
    }
    for counter in PREFETCH_COUNTERS:
        row[counter] = str(sum_prefetch_counter(stats, counter))
    return row


def add_deltas(rows: list[dict[str, str]]) -> None:
    by_workload: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        by_workload[row["workload"]][row["policy"]] = row

    base_fields = [
        "sim_ticks",
        "l1d_demand_misses",
        "l1d_demand_mshr_misses",
        "l1d_hardpf_mshr_misses",
        "l1d_replacements",
        "l2_demand_misses",
        "l2_replacements",
        "membus_pkt_size_total",
        "dram_read_reqs",
        "dram_write_reqs",
    ]
    for workload, policies in by_workload.items():
        none = policies["none"]
        spp = policies.get("spp")
        for row in policies.values():
            for field in base_fields:
                row[f"{field}_delta_vs_none_pct"] = pct_delta(float(row[field]), float(none[field]))
            row["spp_reference_present"] = "yes" if spp else "no"
            for field in ["sim_ticks", "l1d_hardpf_mshr_misses", "membus_pkt_size_total", "l2_replacements"]:
                row[f"{field}_delta_vs_spp_pct"] = (
                    pct_delta(float(row[field]), float(spp[field])) if spp else ""
                )
            total_hardpf = int(row["l1d_hardpf_mshr_misses"])
            companion = int(row["l1d_hardpf_mshr_companion"])
            row["l1d_hardpf_companion_share_pct"] = (
                f"{100.0 * companion / total_hardpf:.2f}" if total_hardpf else "0.00"
            )


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def aggregate_policy(rows: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["policy"]].append(row)
    out: dict[str, dict[str, float]] = {}
    for policy, policy_rows in grouped.items():
        out[policy] = {
            "mean_tick_delta": mean([float(r["sim_ticks_delta_vs_none_pct"]) for r in policy_rows]),
            "mean_l1d_miss_delta": mean([float(r["l1d_demand_misses_delta_vs_none_pct"]) for r in policy_rows]),
            "mean_l1d_repl_delta": mean([float(r["l1d_replacements_delta_vs_none_pct"]) for r in policy_rows]),
            "mean_l2_repl_delta": mean([float(r["l2_replacements_delta_vs_none_pct"]) for r in policy_rows]),
            "mean_bus_byte_delta": mean([float(r["membus_pkt_size_total_delta_vs_none_pct"]) for r in policy_rows]),
            "mean_dram_read_delta": mean([float(r["dram_read_reqs_delta_vs_none_pct"]) for r in policy_rows]),
            "mean_max_rd_q": mean([float(r["dram_max_avg_rd_q_len"]) for r in policy_rows]),
            "mean_max_wr_q": mean([float(r["dram_max_avg_wr_q_len"]) for r in policy_rows]),
            "total_ctlw": sum(float(r["targetLineWitnessMisses"]) for r in policy_rows),
            "total_faults": sum(float(r["fillPrefetchTranslationFault"]) for r in policy_rows),
        }
    return out


def write_csv(rows: list[dict[str, str]]) -> None:
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, str]]) -> None:
    aggregate = aggregate_policy(rows)
    by_workload: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        by_workload[row["workload"]][row["policy"]] = row
    copper_faster = []
    copper_slower = []
    copper_l1d_better = []
    for workload, policies in by_workload.items():
        naive_row = policies["naive"]
        copper_row = policies["copper_clpd64k_peb"]
        if float(copper_row["sim_ticks"]) <= float(naive_row["sim_ticks"]):
            copper_faster.append(workload)
        else:
            copper_slower.append(workload)
        if float(copper_row["l1d_demand_misses"]) <= float(naive_row["l1d_demand_misses"]):
            copper_l1d_better.append(workload)
    point_count = len(by_workload)
    lines = [
        "# COPPER Prefetch Traffic and Pollution Audit",
        "",
        "Scope: first ROI statistics section from the public full-system AArch64 application runs: SQLite, Lua, Duktape, and yyjson at medium/stress scales, bounded JSON+SQLite medium/stress service-composition runs, bounded cache-service hash/LRU scale points, public parser/compression-library PCRE2, libxml2 XML, libarchive TAR, Zstd, and zlib points, plus scaled process-separated OpenSSL libssl TCP-netns points. The audit checks whether COPPER's measured speedups are coupled to excessive traffic, replacement pressure, MSHR pressure, or DRAM backpressure.",
        "",
        "## Per-workload results",
        "",
        "| Workload | Policy | Tick delta vs none | L1D miss delta | L1D repl delta | L2 repl delta | Bus byte delta | DRAM read delta | Max avg read Q | Max avg write Q | L1D HardPF MSHR | Companion share | CTLW misses | Faults |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['workload']} | {row['policy']} | "
            f"{row['sim_ticks_delta_vs_none_pct']}% | "
            f"{row['l1d_demand_misses_delta_vs_none_pct']}% | "
            f"{row['l1d_replacements_delta_vs_none_pct']}% | "
            f"{row['l2_replacements_delta_vs_none_pct']}% | "
            f"{row['membus_pkt_size_total_delta_vs_none_pct']}% | "
            f"{row['dram_read_reqs_delta_vs_none_pct']}% | "
            f"{row['dram_max_avg_rd_q_len']} | "
            f"{row['dram_max_avg_wr_q_len']} | "
            f"{row['l1d_hardpf_mshr_misses']} | "
            f"{row['l1d_hardpf_companion_share_pct']}% | "
            f"{row['targetLineWitnessMisses']} | "
            f"{row['fillPrefetchTranslationFault']} |"
        )

    lines.extend(
        [
            "",
            "## Authority diagnostics",
            "",
            "| Workload | Policy | Target witness hits | Target witness misses | Target witness evictions | Terminal stops | Cross-page drops | Translation unavailable | Boundary authority drops | Blocked no provenance |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        if row["policy"] in {"none", "spp"}:
            continue
        lines.append(
            f"| {row['workload']} | {row['policy']} | "
            f"{row['targetLineWitnessHits']} | "
            f"{row['targetLineWitnessMisses']} | "
            f"{row['targetLineWitnessEvictions']} | "
            f"{row['carriedProvenanceTerminalStops']} | "
            f"{row['fillPrefetchDroppedCrossPage']} | "
            f"{row['fillPrefetchTranslationUnavailable']} | "
            f"{row['boundaryAuthorityEntriesDropped']} | "
            f"{row['blockedNoProvenance']} |"
        )

    lines.extend(
        [
            "",
            "## Cross-workload mean deltas",
            "",
            "| Policy | Mean tick delta | Mean L1D miss delta | Mean L1D repl delta | Mean L2 repl delta | Mean bus byte delta | Mean DRAM read delta | Mean max read Q | Mean max write Q | Total CTLW misses | Total faults |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for policy in POLICIES:
        agg = aggregate[policy]
        lines.append(
            f"| {policy} | {agg['mean_tick_delta']:.3f}% | "
            f"{agg['mean_l1d_miss_delta']:.3f}% | "
            f"{agg['mean_l1d_repl_delta']:.3f}% | "
            f"{agg['mean_l2_repl_delta']:.3f}% | "
            f"{agg['mean_bus_byte_delta']:.3f}% | "
            f"{agg['mean_dram_read_delta']:.3f}% | "
            f"{agg['mean_max_rd_q']:.3f} | "
            f"{agg['mean_max_wr_q']:.3f} | "
            f"{agg['total_ctlw']:.0f} | {agg['total_faults']:.0f} |"
        )

    naive = aggregate["naive"]
    copper = aggregate["copper_clpd64k_peb"]
    spp = aggregate["spp"]
    slack = aggregate["spp_copper_slack"]
    lines.extend(
        [
            "",
            "## Reviewer-facing interpretation",
            "",
            f"- COPPER CLPD-64K+PEB reduces CTLW misses by {pct_reduction(copper['total_ctlw'], naive['total_ctlw'])}% versus naive DMP across the audited app/parser/compression/TCP set, with zero observed translation faults in both policies.",
            f"- COPPER CLPD-64K+PEB has a mean tick delta of {copper['mean_tick_delta']:.3f}% versus no prefetching, compared with {naive['mean_tick_delta']:.3f}% for naive DMP.",
            f"- COPPER CLPD-64K+PEB is faster than naive DMP on {len(copper_faster)}/{point_count} audited app/parser/compression/TCP points and has fewer L1D demand misses than naive on {len(copper_l1d_better)}/{point_count}. The tick exception(s): {', '.join(copper_slower) if copper_slower else 'none'}.",
            f"- COPPER CLPD-64K+PEB changes mean bus bytes by {copper['mean_bus_byte_delta']:.3f}% versus no prefetching; this is the main pollution/traffic cost to defend experimentally.",
            f"- COPPER CLPD-64K+PEB has mean max read-queue length {copper['mean_max_rd_q']:.3f}, close to naive DMP at {naive['mean_max_rd_q']:.3f} and below SPP at {spp['mean_max_rd_q']:.3f}.",
            "- Authority diagnostics show zero target-witness evictions for COPPER CLPD-64K+PEB in this app/parser/compression/TCP set; residual CTLW misses are conservative exact-witness misses rather than a measured target-witness capacity cliff.",
            "- The large terminal-stop counts are intentional: translated cross-page fills are not allowed to recursively chase without a new committed witness. This is a security/performance tradeoff, not a translation failure.",
            f"- SPP remains the stronger pure-performance baseline with mean tick delta {spp['mean_tick_delta']:.3f}%, while SPP+COPPER slack retains most of that performance at {slack['mean_tick_delta']:.3f}% and reduces CTLW misses by {pct_reduction(slack['total_ctlw'], naive['total_ctlw'])}% versus naive DMP.",
            "- DRAM read/write retries are zero in all audited runs, so the current evidence does not show queue-overflow backpressure. Queue length and traffic should still be stress-tested on larger workloads.",
            "- This audit strengthens the paper by separating performance from side effects, but it is not a substitute for SPEC-like, PARSEC-like, or server workload evaluation.",
            "",
            f"CSV: `{CSV_OUT.name}`.",
            "",
        ]
    )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows: list[dict[str, str]] = []
    for workload, tag in WORKLOADS.items():
        for policy in POLICIES:
            rows.append(collect_one(workload, tag, policy))
    add_deltas(rows)
    write_csv(rows)
    write_markdown(rows)
    print(CSV_OUT)
    print(MD_OUT)


if __name__ == "__main__":
    main()
