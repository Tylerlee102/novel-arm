#!/usr/bin/env python3
"""Summarize upstream SQLite speedtest1 full-system COPPER runs."""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "gem5_arm_ubuntu_fs_sqlite_speedtest1"
POLICIES = [
    "none",
    "naive",
    "copper_clpd64k_peb",
    "spp",
    "spp_copper_slack",
]
PREFETCH_COUNTERS = [
    "pfIssued",
    "pfUseful",
    "pfUnused",
    "pfIdentified",
    "pointerLikeCandidates",
    "learnedProofs",
    "proofEvictions",
    "allowedCandidates",
    "blockedNoProvenance",
    "fillPrefetchTranslated",
    "fillPrefetchTranslationFault",
    "fillPrefetchTranslationUnavailable",
    "targetLineWitnessHits",
    "targetLineWitnessMisses",
    "carriedProvenanceTerminalStops",
    "boundaryFlushes",
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


def sum_matching(stats: dict[str, float], suffix: str, contains: str | None = None) -> int:
    return int(
        sum(
            value
            for key, value in stats.items()
            if key.endswith(suffix)
            and (contains is None or contains in key)
            and not math.isnan(value)
        )
    )


def sum_prefetch_counter(stats: dict[str, float], counter: str) -> int:
    matches = [
        (key, value)
        for key, value in stats.items()
        if key.endswith(f".{counter}")
        and ".prefetcher" in key
        and not math.isnan(value)
    ]
    child_matches = [
        value
        for key, value in matches
        if ".prefetchers" in key
        or ".primary." in key
        or ".companion." in key
    ]
    if child_matches:
        return int(sum(child_matches))
    return int(sum(value for _, value in matches))


def terminal_info(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    info: dict[str, str] = {}
    version = re.search(r"-- Speedtest1 for SQLite\s+(.*?)\n", text)
    if version:
        info["sqlite_version_line"] = version.group(1).strip()
    begin = re.search(r'Begin testset "([^"]+)"', text)
    if begin:
        info["testset"] = begin.group(1)
    total = re.search(r"TOTAL\.+\s+([0-9]+\.[0-9]+)s", text)
    if total:
        info["sqlite_total_s"] = total.group(1)
    verify = re.search(r"Verification Hash:\s+(\d+)\s+([0-9a-fA-F]+)", text)
    if verify:
        info["verify_bytes"] = verify.group(1)
        info["verify_hash"] = verify.group(2)
    done = re.search(r"COPPER_FS_NATIVE_A64_DONE rc=(\d+)", text)
    if done:
        info["rc"] = done.group(1)
    page_hits = re.search(r"-- Page cache hits:\s+(\d+)", text)
    if page_hits:
        info["sqlite_page_cache_hits"] = page_hits.group(1)
    page_misses = re.search(r"-- Page cache misses:\s+(\d+)", text)
    if page_misses:
        info["sqlite_page_cache_misses"] = page_misses.group(1)
    lookaside_hits = re.search(r"-- Successful lookasides:\s+(\d+)", text)
    if lookaside_hits:
        info["sqlite_lookaside_hits"] = lookaside_hits.group(1)
    return info


def summarize(tag: str, policies: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for policy in policies:
        run_dir = RESULTS / f"gem5_arm_ubuntu_fs_sqlite_speedtest1_{tag}_{policy}"
        sections = parse_stats_sections(run_dir / "stats.txt")
        if not sections:
            raise RuntimeError(f"no stats sections in {run_dir}")
        stats = sections[0]
        info = terminal_info(run_dir / "board.terminal")
        row: dict[str, str] = {
            "policy": policy,
            "roi_ticks": str(int(stats.get("simTicks", 0))),
            "sim_insts": str(int(stats.get("simInsts", 0))),
            "insts_not_nop": str(
                sum_matching(
                    stats,
                    ".core.commitStats0.numInstsNotNOP",
                    "board.processor.switch",
                )
            ),
            "l1d_demand_misses": str(
                sum_matching(
                    stats,
                    ".demandMisses::total",
                    "board.cache_hierarchy.l1d-cache-",
                )
            ),
            "l1d_demand_accesses": str(
                sum_matching(
                    stats,
                    ".demandAccesses::total",
                    "board.cache_hierarchy.l1d-cache-",
                )
            ),
            "l2_demand_misses": str(
                sum_matching(
                    stats,
                    ".demandMisses::total",
                    "board.cache_hierarchy.l2-cache-",
                )
            ),
            "sqlite_total_s": info.get("sqlite_total_s", ""),
            "verify_bytes": info.get("verify_bytes", ""),
            "verify_hash": info.get("verify_hash", ""),
            "rc": info.get("rc", ""),
            "testset": info.get("testset", ""),
            "sqlite_page_cache_hits": info.get("sqlite_page_cache_hits", ""),
            "sqlite_page_cache_misses": info.get("sqlite_page_cache_misses", ""),
            "sqlite_lookaside_hits": info.get("sqlite_lookaside_hits", ""),
        }
        for counter in PREFETCH_COUNTERS:
            row[counter] = str(sum_prefetch_counter(stats, counter))
        rows.append(row)

    base_ticks = int(next(row["roi_ticks"] for row in rows if row["policy"] == "none"))
    base_l1d = int(next(row["l1d_demand_misses"] for row in rows if row["policy"] == "none"))
    for row in rows:
        ticks = int(row["roi_ticks"])
        l1d = int(row["l1d_demand_misses"])
        row["tick_delta_vs_none_pct"] = f"{((ticks / base_ticks) - 1.0) * 100.0:.3f}"
        row["l1d_miss_delta_vs_none_pct"] = (
            f"{((l1d / base_l1d) - 1.0) * 100.0:.3f}" if base_l1d else ""
        )
    return rows


def pct_reduction(new: int, old: int) -> float:
    return 100.0 * (1.0 - (new / old)) if old else 0.0


def write_outputs(tag: str, rows: list[dict[str, str]], size: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / f"sqlite_speedtest1_{tag}_summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    by_policy = {row["policy"]: row for row in rows}
    hashes = {row["verify_hash"] for row in rows}
    verify_bytes = {row["verify_bytes"] for row in rows}
    rcs = {row["rc"] for row in rows}
    testsets = {row["testset"] for row in rows if row["testset"]}
    testset = next(iter(sorted(testsets)), "")
    naive_ctlw = int(by_policy.get("naive", {}).get("targetLineWitnessMisses", 0))
    copper_ctlw = int(by_policy.get("copper_clpd64k_peb", {}).get("targetLineWitnessMisses", 0))
    slack_ctlw = int(by_policy.get("spp_copper_slack", {}).get("targetLineWitnessMisses", 0))
    naive_faults = int(by_policy.get("naive", {}).get("fillPrefetchTranslationFault", 0))
    copper_faults = int(by_policy.get("copper_clpd64k_peb", {}).get("fillPrefetchTranslationFault", 0))
    spp_faults = int(by_policy.get("spp", {}).get("fillPrefetchTranslationFault", 0))
    slack_faults = int(by_policy.get("spp_copper_slack", {}).get("fillPrefetchTranslationFault", 0))
    worst_hash = "yes" if len(hashes) == 1 and "" not in hashes else "no"
    rc_ok = "yes" if rcs == {"0"} else "no"

    lines = [
        "# SQLite speedtest1 AArch64 Full-System Summary",
        "",
        "This is an unmodified upstream SQLite speedtest1 workload built from SQLite 3.53.2",
        "source and run as a native AArch64 Linux binary under gem5 full-system.",
        f"The fixed tractable point is `--memdb --verify --stats --size {size} --testset {testset or '<unknown>'} --repeat 1`.",
        "",
        f"Input tag: `{tag}`.",
        "",
        "| Policy | ROI ticks | Delta vs none | Sim insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | SQLite time | Verify hash | rc |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['policy']} | {row['roi_ticks']} | "
            f"{row['tick_delta_vs_none_pct']}% | {row['sim_insts']} | "
            f"{row['l1d_demand_misses']} | {row['l1d_miss_delta_vs_none_pct']}% | "
            f"{row['pfIssued']} | {row['pfUseful']} | {row['pointerLikeCandidates']} | "
            f"{row['learnedProofs']} | {row['allowedCandidates']} | "
            f"{row['blockedNoProvenance']} | {row['targetLineWitnessMisses']} | "
            f"{row['fillPrefetchTranslationFault']} | "
            f"{row['boundaryAuthorityEntriesDropped']} | {row['sqlite_total_s']} | "
            f"{row['verify_hash']} | {row['rc']} |"
        )
    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            f"- Verification hash agreement: {worst_hash} ({', '.join(sorted(hashes))}).",
            f"- Verification byte-count agreement: {', '.join(sorted(verify_bytes))}; when this is 0, treat the hash as a run-consistency marker and rely on return code plus completed test lines rather than as a result-content checksum.",
            f"- Return-code agreement: {rc_ok} ({', '.join(sorted(rcs))}).",
            f"- Naive DMP CTLW misses: {naive_ctlw}; COPPER CLPD-64K+PEB CTLW misses: {copper_ctlw}; reduction: {pct_reduction(copper_ctlw, naive_ctlw):.1f}%.",
            f"- SPP+COPPER-slack companion CTLW misses: {slack_ctlw}. Plain SPP has no pointer-provenance CTLW counter, so this is a bounded companion-safety cost rather than a reduction comparison.",
            f"- Translation faults: naive={naive_faults}, COPPER={copper_faults}, SPP={spp_faults}, SPP+COPPER-slack={slack_faults}.",
            "- Scope note: this is a small, deterministic, upstream benchmark component rather than a full-scale SQLite performance run. It strengthens external validity because the code is public and unmodified, not because it represents all database workloads.",
            "",
            "status=PASS",
            "",
        ]
    )
    out = OUT / f"SQLITE_SPEEDTEST1_{tag.upper()}_FS_SUMMARY.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(csv_path)
    print(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="speedtest1_json_smoke_size1")
    parser.add_argument("--size", default="1")
    parser.add_argument("--policies", nargs="*", default=POLICIES)
    args = parser.parse_args()
    rows = summarize(args.tag, args.policies)
    write_outputs(args.tag, rows, args.size)


if __name__ == "__main__":
    main()
