#!/usr/bin/env python3
"""Summarize SQLite application full-system COPPER runs."""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "gem5_arm_ubuntu_fs_sqlite_app"
POLICIES = [
    "none",
    "stride",
    "naive",
    "copper_clpd64k_peb",
    "dcpt",
    "spp",
    "ampm",
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
    result = re.search(
        r"SQLITE_COPPER_RESULT\s+(?P<body>.*?)checksum=(?P<checksum>0x[0-9a-fA-F]+)",
        text,
    )
    if result:
        info["checksum"] = result.group("checksum")
        for key, value in re.findall(r"(\w+)=([0-9]+)", result.group("body")):
            info[key] = value
    done = re.search(r"COPPER_FS_NATIVE_A64_DONE rc=(\d+)", text)
    if done:
        info["rc"] = done.group(1)
    return info


def summarize(tag: str, policies: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for policy in policies:
        run_dir = RESULTS / f"gem5_arm_ubuntu_fs_sqlite_{tag}_{policy}"
        sections = parse_stats_sections(run_dir / "stats.txt")
        if not sections:
            raise RuntimeError(f"no stats sections in {run_dir}")
        stats = sections[0]
        info = terminal_info(run_dir / "board.terminal")
        row: dict[str, str] = {
            "policy": policy,
            "roi_ticks": str(int(stats.get("simTicks", 0))),
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
            "checksum": info.get("checksum", ""),
            "rc": info.get("rc", ""),
            "rows": info.get("rows", ""),
            "lookups": info.get("lookups", ""),
            "ranges": info.get("ranges", ""),
            "updates": info.get("updates", ""),
            "payload_rows": info.get("payload_rows", ""),
            "seed": info.get("seed", ""),
            "poison": info.get("poison", ""),
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


def write_outputs(tag: str, rows: list[dict[str, str]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / f"sqlite_{tag}_summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    by_policy = {row["policy"]: row for row in rows}
    checksums = {row["checksum"] for row in rows}
    naive_ctlw = int(by_policy.get("naive", {}).get("targetLineWitnessMisses", 0))
    copper_ctlw = int(by_policy.get("copper_clpd64k_peb", {}).get("targetLineWitnessMisses", 0))
    naive_faults = int(by_policy.get("naive", {}).get("fillPrefetchTranslationFault", 0))
    copper_faults = int(by_policy.get("copper_clpd64k_peb", {}).get("fillPrefetchTranslationFault", 0))

    lines = [
        "# SQLite AArch64 Full-System Application Summary",
        "",
        "This is a public SQLite-amalgamation application-style workload:",
        "in-memory B-tree insertions, point lookups, range scans, secondary-index",
        "probes, updates, and pointer-shaped payload-table reads. It runs as a",
        "native AArch64 Linux binary under the same gem5 full-system path used by",
        "the COPPER heap, GAPBS, and Olden experiments.",
        "",
        f"Input tag: `{tag}`.",
        "",
        "| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['policy']} | {row['roi_ticks']} | "
            f"{row['tick_delta_vs_none_pct']}% | {row['insts_not_nop']} | "
            f"{row['l1d_demand_misses']} | {row['l1d_miss_delta_vs_none_pct']}% | "
            f"{row['pfIssued']} | {row['pfUseful']} | {row['pointerLikeCandidates']} | "
            f"{row['learnedProofs']} | {row['allowedCandidates']} | "
            f"{row['blockedNoProvenance']} | {row['targetLineWitnessMisses']} | "
            f"{row['fillPrefetchTranslationFault']} | "
            f"{row['boundaryAuthorityEntriesDropped']} | {row['checksum']} | {row['rc']} |"
        )
    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            f"- Checksum agreement: {'yes' if len(checksums) == 1 and '' not in checksums else 'no'} ({', '.join(sorted(checksums))}).",
            f"- Naive DMP CTLW misses: {naive_ctlw}; COPPER CLPD-64K+PEB CTLW misses: {copper_ctlw}; reduction: {pct_reduction(copper_ctlw, naive_ctlw):.1f}%.",
            f"- Naive DMP translation faults: {naive_faults}; COPPER CLPD-64K+PEB translation faults: {copper_faults}.",
            "- This workload is stronger external-validity evidence than generated pointer kernels, but it is still one application-style point and should not be oversold as representative of all database/runtime software.",
            "",
        ]
    )
    out = OUT / f"SQLITE_{tag.upper()}_FS_SUMMARY.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(csv_path)
    print(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="app_small")
    parser.add_argument("--policies", nargs="*", default=POLICIES)
    args = parser.parse_args()
    rows = summarize(args.tag, args.policies)
    write_outputs(args.tag, rows)


if __name__ == "__main__":
    main()
