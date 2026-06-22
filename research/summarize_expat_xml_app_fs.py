#!/usr/bin/env python3
"""Summarize Expat XML full-system COPPER runs."""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "gem5_arm_ubuntu_fs_expat_app"
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
    "allowedCandidates",
    "blockedNoProvenance",
    "fillPrefetchTranslationFault",
    "targetLineWitnessMisses",
    "boundaryAuthorityEntriesDropped",
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
        r"EXPAT_COPPER_RESULT\s+(?P<body>.*?)checksum=(?P<checksum>0x[0-9a-fA-F]+)",
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
        run_dir = RESULTS / f"gem5_arm_ubuntu_fs_expat_{tag}_{policy}"
        sections = parse_stats_sections(run_dir / "stats.txt")
        if len(sections) < 2:
            raise RuntimeError(f"expected at least two stats sections in {run_dir}")
        stats = sections[-1]
        info = terminal_info(run_dir / "board.terminal")
        row = {
            "policy": policy,
            "roi_ticks": str(int(stats.get("simTicks", 0))),
            "insts_not_nop": str(sum_matching(stats, ".numInsts")),
            "l1d_demand_misses": str(
                sum_matching(stats, ".demandMshrMisses::total", "l1d-cache")
            ),
            "checksum": info.get("checksum", ""),
            "rc": info.get("rc", ""),
            "records": info.get("records", ""),
            "attrs": info.get("attrs", ""),
            "rounds": info.get("rounds", ""),
            "seed": info.get("seed", ""),
            "chunk": info.get("chunk", ""),
            "xml_bytes": info.get("xml_bytes", ""),
            "elements": info.get("elements", ""),
            "attr_count": info.get("attr_count", ""),
            "pointer_like_attrs": info.get("pointer_like_attrs", ""),
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
            if base_l1d
            else ""
        )
    return rows


def pct_reduction(new: int, old: int) -> float:
    return 100.0 * (1.0 - (new / old)) if old else 0.0


def write_outputs(tag: str, rows: list[dict[str, str]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / f"expat_{tag}_summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    by = {row["policy"]: row for row in rows}
    checksums = {row["checksum"] for row in rows}
    rcs = {row["rc"] for row in rows}
    naive_ctlw = int(by.get("naive", {}).get("targetLineWitnessMisses", "0"))
    copper_ctlw = int(by.get("copper_clpd64k_peb", {}).get("targetLineWitnessMisses", "0"))
    slack_ctlw = int(by.get("spp_copper_slack", {}).get("targetLineWitnessMisses", "0"))
    copper_faults = int(by.get("copper_clpd64k_peb", {}).get("fillPrefetchTranslationFault", "0"))
    naive_faults = int(by.get("naive", {}).get("fillPrefetchTranslationFault", "0"))

    lines = [
        "# Expat XML AArch64 Full-System Summary",
        "",
        "This workload is a deterministic native AArch64 Linux ROI that calls",
        "the public libexpat XML parser through the Ubuntu guest library stack",
        "while parsing nested XML records containing address-shaped attributes",
        "loaded as ordinary data.",
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
            "Workload shape:",
            "",
            f"- Records: {by['none'].get('records', '')}; attributes per record: {by['none'].get('attrs', '')}; rounds: {by['none'].get('rounds', '')}; XML bytes: {by['none'].get('xml_bytes', '')}.",
            f"- Parsed elements: {by['none'].get('elements', '')}; parsed attributes: {by['none'].get('attr_count', '')}; address-shaped attributes: {by['none'].get('pointer_like_attrs', '')}.",
            "",
            "Interpretation:",
            "",
            f"- Checksum agreement: {'yes' if len(checksums) == 1 and '' not in checksums else 'no'} ({', '.join(sorted(checksums))}).",
            f"- Return-code agreement: {'yes' if rcs == {'0'} else 'no'} ({', '.join(sorted(rcs))}).",
            f"- Naive DMP CTLW misses: {naive_ctlw}; COPPER CLPD-64K+PEB CTLW misses: {copper_ctlw}; reduction: {pct_reduction(copper_ctlw, naive_ctlw):.1f}%.",
            f"- SPP+COPPER slack CTLW misses: {slack_ctlw}; reduction versus naive DMP: {pct_reduction(slack_ctlw, naive_ctlw):.1f}%.",
            f"- Naive DMP translation faults: {naive_faults}; COPPER CLPD-64K+PEB translation faults: {copper_faults}.",
            "- This is a public XML parser-library point, not a production browser or service workload.",
            "",
            "status=PASS" if len(checksums) == 1 and "" not in checksums and rcs == {"0"} else "status=CHECKSUM_OR_RC_MISMATCH",
            "",
        ]
    )
    md_path = OUT / f"EXPAT_{tag.upper()}_FS_SUMMARY.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(csv_path)
    print(md_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="app_smoke")
    parser.add_argument("--policies", nargs="*", default=POLICIES)
    args = parser.parse_args()
    write_outputs(args.tag, summarize(args.tag, args.policies))


if __name__ == "__main__":
    main()
