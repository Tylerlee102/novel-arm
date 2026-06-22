#!/usr/bin/env python3
"""Summarize Duktape JavaScript runtime full-system COPPER runs."""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "gem5_arm_ubuntu_fs_duktape_app"
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
COUNTERS = [
    "pfIssued",
    "pfUseful",
    "pointerLikeCandidates",
    "learnedProofs",
    "proofEvictions",
    "allowedCandidates",
    "blockedNoProvenance",
    "fillPrefetchTranslated",
    "fillPrefetchTranslationFault",
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
        r"DUKTAPE_COPPER_RESULT\s+(?P<body>.*?)checksum=(?P<checksum>0x[0-9a-fA-F]+)",
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
        run_dir = RESULTS / f"gem5_arm_ubuntu_fs_duktape_{tag}_{policy}"
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
            "checksum": info.get("checksum", ""),
            "rc": info.get("rc", ""),
            "rows": info.get("rows", ""),
            "lookups": info.get("lookups", ""),
            "updates": info.get("updates", ""),
            "traversals": info.get("traversals", ""),
            "seed": info.get("seed", ""),
            "poison": info.get("poison", ""),
        }
        for counter in COUNTERS:
            row[counter] = str(sum_prefetch_counter(stats, counter))
        rows.append(row)

    base_ticks = int(next(row["roi_ticks"] for row in rows if row["policy"] == "none"))
    base_l1d = int(next(row["l1d_demand_misses"] for row in rows if row["policy"] == "none"))
    for row in rows:
        row["tick_delta_vs_none_pct"] = (
            f"{((int(row['roi_ticks']) / base_ticks) - 1.0) * 100.0:.3f}"
        )
        row["l1d_miss_delta_vs_none_pct"] = (
            f"{((int(row['l1d_demand_misses']) / base_l1d) - 1.0) * 100.0:.3f}"
        )
    return rows


def write_outputs(tag: str, rows: list[dict[str, str]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / f"duktape_{tag}_summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    by = {row["policy"]: row for row in rows}
    checksums = {row["checksum"] for row in rows}
    naive_ctlw = int(by.get("naive", {}).get("targetLineWitnessMisses", "0"))
    copper_ctlw = int(by.get("copper_clpd64k_peb", {}).get("targetLineWitnessMisses", "0"))
    reduction = 100.0 * (1.0 - copper_ctlw / naive_ctlw) if naive_ctlw else 0.0

    lines = [
        "# Duktape AArch64 Full-System Runtime Summary",
        "",
        "This is a public Duktape 2.7.0 JavaScript-runtime workload: the binary",
        "embeds Duktape and runs object-map, linked-object, update, traversal,",
        "payload, and GC-heavy JavaScript code.",
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
            f"- Naive DMP CTLW misses: {naive_ctlw}; COPPER CLPD-64K+PEB CTLW misses: {copper_ctlw}; reduction: {reduction:.1f}%.",
            "- This adds a third public runtime/application point beyond SQLite and Lua.",
            "",
        ]
    )
    md_path = OUT / f"DUKTAPE_{tag.upper()}_FS_SUMMARY.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(csv_path)
    print(md_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="app_small")
    parser.add_argument("--policies", nargs="*", default=POLICIES)
    args = parser.parse_args()
    write_outputs(args.tag, summarize(args.tag, args.policies))


if __name__ == "__main__":
    main()
