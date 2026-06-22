#!/usr/bin/env python3
"""Summarize official OpenSSL CLI fixed-workload full-system COPPER runs."""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "gem5_arm_ubuntu_fs_osslcli_app"
POLICIES = ["none", "naive", "copper_clpd64k_peb", "spp", "spp_copper_slack"]
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
        if ".prefetchers" in key or ".primary." in key or ".companion." in key
    ]
    if child_matches:
        return int(sum(child_matches))
    return int(sum(value for _, value in matches))


def terminal_info(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    info: dict[str, str] = {}
    preload = re.search(
        r"COPPER_FS_NATIVE_PRELOAD_DONE\s+path=(?P<path>\S+)\s+bytes=(?P<bytes>\d+)\s+seed=(?P<seed>\d+)\s+checksum=(?P<checksum>0x[0-9a-fA-F]+)",
        text,
    )
    if preload:
        info.update(
            {
                "input_path": preload.group("path"),
                "input_bytes": preload.group("bytes"),
                "seed": preload.group("seed"),
                "input_checksum": preload.group("checksum"),
            }
        )
    digests = re.findall(r"=\s*([0-9a-fA-F]{64})", text)
    if digests:
        info["sha256"] = digests[-1].lower()
    done = re.search(r"COPPER_FS_NATIVE_A64_DONE rc=(\d+)", text)
    if done:
        info["rc"] = done.group(1)
    after_done = re.search(r"COPPER_FS_NATIVE_AFTER_A64_DONE rc=(\d+)", text)
    if after_done:
        info["after_rc"] = after_done.group(1)
    return info


def summarize(tag: str, policies: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for policy in policies:
        run_dir = RESULTS / f"gem5_arm_ubuntu_fs_osslcli_{tag}_{policy}"
        sections = parse_stats_sections(run_dir / "stats.txt")
        if not sections:
            raise RuntimeError(f"no stats sections in {run_dir}")
        stats = sections[0]
        info = terminal_info(run_dir / "board.terminal")
        row: dict[str, str] = {
            "policy": policy,
            "roi_ticks": str(int(stats.get("simTicks", 0))),
            "insts_not_nop": str(
                sum_matching(stats, ".core.commitStats0.numInstsNotNOP", "board.processor.switch")
            ),
            "l1d_demand_misses": str(
                sum_matching(stats, ".demandMisses::total", "board.cache_hierarchy.l1d-cache-")
            ),
            "sha256": info.get("sha256", ""),
            "rc": info.get("rc", ""),
            "after_rc": info.get("after_rc", ""),
            "input_path": info.get("input_path", ""),
            "input_bytes": info.get("input_bytes", ""),
            "seed": info.get("seed", ""),
            "input_checksum": info.get("input_checksum", ""),
        }
        for counter in COUNTERS:
            row[counter] = str(sum_prefetch_counter(stats, counter))
        rows.append(row)

    base_ticks = int(next(row["roi_ticks"] for row in rows if row["policy"] == "none"))
    base_l1d = int(next(row["l1d_demand_misses"] for row in rows if row["policy"] == "none"))
    for row in rows:
        row["tick_delta_vs_none_pct"] = f"{((int(row['roi_ticks']) / base_ticks) - 1.0) * 100.0:.3f}"
        row["l1d_miss_delta_vs_none_pct"] = (
            f"{((int(row['l1d_demand_misses']) / base_l1d) - 1.0) * 100.0:.3f}"
            if base_l1d
            else ""
        )
    return rows


def pct_reduction(new: int, old: int) -> float:
    return 100.0 * (1.0 - (new / old)) if old else 0.0


def write_outputs(tag: str, rows: list[dict[str, str]], mode: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / f"osslcli_{tag}_summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    by = {row["policy"]: row for row in rows}
    digests = {row["sha256"] for row in rows}
    rcs = {row["rc"] for row in rows}
    after_rcs = {row["after_rc"] for row in rows if row["after_rc"]}
    input_checksums = {row["input_checksum"] for row in rows}
    naive_ctlw = int(by.get("naive", {}).get("targetLineWitnessMisses", "0"))
    copper_ctlw = int(by.get("copper_clpd64k_peb", {}).get("targetLineWitnessMisses", "0"))
    slack_ctlw = int(by.get("spp_copper_slack", {}).get("targetLineWitnessMisses", "0"))
    copper_faults = int(by.get("copper_clpd64k_peb", {}).get("fillPrefetchTranslationFault", "0"))
    slack_faults = int(by.get("spp_copper_slack", {}).get("fillPrefetchTranslationFault", "0"))
    spp_gap = float(by["spp_copper_slack"]["tick_delta_vs_none_pct"]) - float(by["spp"]["tick_delta_vs_none_pct"])

    if mode == "aes_ctr":
        title = "Official OpenSSL CLI AES-CTR Fixed-Workload AArch64 Full-System Summary"
        description = "This workload injects the official Ubuntu ARM64 `openssl` CLI binary, creates a deterministic pointer-shaped guest input file before ROI, then measures `openssl enc -aes-128-ctr` and an official `openssl dgst -sha256` fingerprint of the encrypted output under timing-mode full-system gem5. It is an official CLI fixed-workload datapoint, not the timer-driven `openssl speed` benchmark."
        workload_note = "- This is official-command AES-CTR plus output digest evidence, but still not the timer-driven `openssl speed` benchmark."
    elif mode == "hmac":
        title = "Official OpenSSL CLI HMAC-SHA256 Fixed-Workload AArch64 Full-System Summary"
        description = "This workload injects the official Ubuntu ARM64 `openssl` CLI binary, creates a deterministic pointer-shaped guest input file before ROI, then measures `openssl dgst -sha256 -hmac` under timing-mode full-system gem5. It is an official CLI fixed-workload MAC datapoint, not the timer-driven `openssl speed` benchmark."
        workload_note = "- This is official-command HMAC-SHA256 evidence, but still not the timer-driven `openssl speed` benchmark."
    else:
        title = "Official OpenSSL CLI Fixed-Workload AArch64 Full-System Summary"
        description = "This workload injects the official Ubuntu ARM64 `openssl` CLI binary, creates a deterministic pointer-shaped guest input file before ROI, then measures `openssl dgst -sha256 /tmp/openssl_cli_input.bin` under timing-mode full-system gem5. It is an official CLI fixed-workload datapoint, not the timer-driven `openssl speed` benchmark."
        workload_note = "- This is stronger official-command evidence than a local libcrypto driver, but it is still a fixed-workload CLI digest rather than the official timer-driven `openssl speed` benchmark."

    lines = [
        f"# {title}",
        "",
        description,
        "",
        f"Input tag: `{tag}`.",
        "",
        "| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | SHA256 | rc | after rc |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['policy']} | {row['roi_ticks']} | {row['tick_delta_vs_none_pct']}% | "
            f"{row['insts_not_nop']} | {row['l1d_demand_misses']} | {row['l1d_miss_delta_vs_none_pct']}% | "
            f"{row['pfIssued']} | {row['pfUseful']} | {row['pointerLikeCandidates']} | "
            f"{row['learnedProofs']} | {row['allowedCandidates']} | {row['blockedNoProvenance']} | "
            f"{row['targetLineWitnessMisses']} | {row['fillPrefetchTranslationFault']} | "
            f"{row['boundaryAuthorityEntriesDropped']} | {row['sha256']} | {row['rc']} | {row['after_rc']} |"
        )
    after_rc_line = (
        f"- Native after-command return-code agreement: {'yes' if after_rcs == {'0'} else 'no'} ({', '.join(sorted(after_rcs))})."
        if after_rcs
        else "- Native after-command return-code agreement: not used."
    )
    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            f"- SHA256 agreement: {'yes' if len(digests) == 1 and '' not in digests else 'no'} ({', '.join(sorted(digests))}).",
            f"- Input checksum agreement: {'yes' if len(input_checksums) == 1 and '' not in input_checksums else 'no'} ({', '.join(sorted(input_checksums))}).",
            f"- Native return-code agreement: {'yes' if rcs == {'0'} else 'no'} ({', '.join(sorted(rcs))}).",
            after_rc_line,
            f"- Naive DMP CTLW misses: {naive_ctlw}; COPPER CLPD-64K+PEB CTLW misses: {copper_ctlw}; reduction: {pct_reduction(copper_ctlw, naive_ctlw):.1f}%.",
            f"- SPP+COPPER slack CTLW misses: {slack_ctlw}; reduction versus naive DMP: {pct_reduction(slack_ctlw, naive_ctlw):.1f}%.",
            f"- COPPER translation faults: {copper_faults}; SPP+COPPER slack translation faults: {slack_faults}.",
            f"- SPP+COPPER slack tick gap versus SPP: {spp_gap:+.3f} percentage points.",
            workload_note,
            "",
            "status=PASS" if len(digests) == 1 and "" not in digests and rcs == {"0"} and (not after_rcs or after_rcs == {"0"}) else "status=CHECK",
            "",
        ]
    )
    md_path = OUT / f"OSSLCLI_{tag.upper()}_FS_SUMMARY.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(csv_path)
    print(md_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="fixed_64k")
    parser.add_argument("--mode", choices=["sha256", "aes_ctr", "hmac"], default="sha256")
    parser.add_argument("--policies", nargs="*", default=POLICIES)
    args = parser.parse_args()
    write_outputs(args.tag, summarize(args.tag, args.policies), args.mode)


if __name__ == "__main__":
    main()
