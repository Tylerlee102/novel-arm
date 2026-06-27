#!/usr/bin/env python3
"""Summarize OpenSSL libssl TCP-Loopback TLS full-system COPPER runs."""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "gem5_arm_ubuntu_fs_ossltlstcp_app"
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


def select_roi_stats_section(sections: list[dict[str, float]], run_dir: Path) -> tuple[int, dict[str, float]]:
    if not sections:
        raise RuntimeError(f"no stats sections in {run_dir}")
    # These native OpenSSL binaries use --native-self-roi and call m5_reset_stats
    # followed by m5_dump_stats inside the measured ROI. The wrapper may emit
    # later teardown dumps, so the first section is the paper-facing ROI.
    if len(sections) < 2:
        raise RuntimeError(f"expected ROI plus wrapper stats sections in {run_dir}")
    return 0, sections[0]


def terminal_info(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    info: dict[str, str] = {}
    result = re.search(
        r"OPENSSL_TLS_TCP_COPPER_RESULT\s+(?P<body>.*?)checksum=(?P<checksum>0x[0-9a-fA-F]+)",
        text,
    )
    if result:
        info["checksum"] = result.group("checksum")
        for key, value in re.findall(r"(\w+)=([0-9]+)", result.group("body")):
            info[key] = value
        transport = re.search(r"transport=([A-Za-z0-9_]+)", result.group("body"))
        if transport:
            info["transport"] = transport.group(1)
    done = re.search(r"COPPER_FS_NATIVE_A64_DONE rc=(\d+)", text)
    if done:
        info["rc"] = done.group(1)
    return info


def summarize(tag: str, policies: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for policy in policies:
        run_dir = RESULTS / f"gem5_arm_ubuntu_fs_ossltlstcp_{tag}_{policy}"
        sections = parse_stats_sections(run_dir / "stats.txt")
        stats_section_index, stats = select_roi_stats_section(sections, run_dir)
        info = terminal_info(run_dir / "board.terminal")
        row: dict[str, str] = {
            "policy": policy,
            "stats_section_index": str(stats_section_index),
            "stats_sections_total": str(len(sections)),
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
            "sessions": info.get("sessions", ""),
            "handshakes": info.get("handshakes", ""),
            "records": info.get("records", ""),
            "scan_depth": info.get("scan_depth", ""),
            "rounds": info.get("rounds", ""),
            "seed": info.get("seed", ""),
            "poison": info.get("poison", ""),
            "transport": info.get("transport", ""),
            "tcp_pairs": info.get("tcp_pairs", ""),
            "afunix_fallback_pairs": info.get("afunix_fallback_pairs", ""),
            "strict_tcp": info.get("strict_tcp", ""),
            "netns_loopback": info.get("netns_loopback", ""),
            "netns_errno": info.get("netns_errno", ""),
            "process_server": info.get("process_server", ""),
            "process_pairs": info.get("process_pairs", ""),
            "child_failures": info.get("child_failures", ""),
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
    csv_path = OUT / f"ossltlstcp_{tag}_summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    by = {row["policy"]: row for row in rows}
    checksums = {row["checksum"] for row in rows}
    naive_ctlw = int(by.get("naive", {}).get("targetLineWitnessMisses", "0"))
    copper_ctlw = int(by.get("copper_clpd64k_peb", {}).get("targetLineWitnessMisses", "0"))
    slack_ctlw = int(by.get("spp_copper_slack", {}).get("targetLineWitnessMisses", "0"))
    copper_faults = int(by.get("copper_clpd64k_peb", {}).get("fillPrefetchTranslationFault", "0"))
    naive_faults = int(by.get("naive", {}).get("fillPrefetchTranslationFault", "0"))
    all_success = (
        len(checksums) == 1
        and "" not in checksums
        and all(str(row["rc"]) == "0" for row in rows)
    )
    transports = {row.get("transport", "") for row in rows}
    all_tcp = all_success and transports == {"tcp_loopback"}
    all_tcp_netns = all_success and transports == {"tcp_loopback_netns"}
    all_tcp_process = all_success and transports == {"tcp_loopback_process"}
    all_tcp_netns_process = all_success and transports == {"tcp_loopback_netns_process"}
    all_fallback = all_success and transports == {"af_unix_fallback"}
    process_modes = {row.get("process_server", "") for row in rows}
    process_pairs = sum(int(row.get("process_pairs", "0") or "0") for row in rows)
    child_failures = sum(int(row.get("child_failures", "0") or "0") for row in rows)

    lines = [
        "# OpenSSL libssl TLS TCP Loopback AArch64 Full-System Summary",
        "",
        "This workload is a deterministic native AArch64 Linux ROI that calls",
        "OpenSSL libssl's TLS 1.2 PSK handshake and TLS record read/write path",
        "over a nonblocking Linux TCP loopback connection when the guest permits it.",
        "If the guest loopback device is unavailable, the driver first tries an explicitly tagged",
        "private user/network-namespace TCP loopback path. If that is unavailable too, it uses an",
        "explicitly tagged AF_UNIX",
        "fallback so the TLS record path can still be measured without pretending that TCP worked.",
        "The workload maintains session hash/LRU metadata and",
        "pointer-shaped ticket words loaded as data.",
        "",
        f"Input tag: `{tag}`.",
        "",
        "| Policy | Transport | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['policy']} | {row['transport']} | {row['roi_ticks']} | "
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
            f"- Transport modes observed: {', '.join(sorted(transports)) if transports else 'none'}.",
        ]
    )
    if all_tcp or all_tcp_netns or all_tcp_process or all_tcp_netns_process or all_fallback:
        lines.extend(
            [
                f"- Naive DMP CTLW misses: {naive_ctlw}; COPPER CLPD-64K+PEB CTLW misses: {copper_ctlw}; reduction: {pct_reduction(copper_ctlw, naive_ctlw):.1f}%.",
                f"- SPP+COPPER slack CTLW misses: {slack_ctlw}; reduction versus naive DMP: {pct_reduction(slack_ctlw, naive_ctlw):.1f}%.",
                f"- Naive DMP translation faults: {naive_faults}; COPPER CLPD-64K+PEB translation faults: {copper_faults}.",
                "- This is real libssl handshake and TLS record execution through the guest dynamic loader. The transport tag determines how strongly the result can be claimed.",
                "",
            ]
        )
        if all_tcp:
            lines.extend(
                [
                    "- All policies used Linux TCP loopback. This is stronger than the memory-BIO and AF_UNIX socketpair paths, but still an in-process loopback service driver rather than a production TCP/TLS server.",
                    "",
                    "status=PASS",
                    "",
                ]
            )
        elif all_tcp_process:
            lines.extend(
                [
                    f"- All policies used process-separated AF_INET TCP loopback with a forked TLS server process. Process-server flag values: {', '.join(sorted(process_modes))}; process TCP pairs: {process_pairs}; child failures: {child_failures}. This is stronger than the in-process loopback service driver, but still a bounded local server/client harness rather than a production deployment.",
                    "",
                    "status=TCP_PROCESS_PASS",
                    "",
                ]
            )
        elif all_tcp_netns_process:
            lines.extend(
                [
                    f"- All policies used process-separated AF_INET TCP loopback inside a private user/network namespace with a forked TLS server process. Process-server flag values: {', '.join(sorted(process_modes))}; process TCP pairs: {process_pairs}; child failures: {child_failures}. This is stronger than the in-process loopback service driver, but still a bounded local server/client harness rather than a production deployment.",
                    "",
                    "status=TCP_NETNS_PROCESS_PASS",
                    "",
                ]
            )
        elif all_tcp_netns:
            lines.extend(
                [
                    "- All policies used AF_INET TCP loopback inside a private user/network namespace created by the benchmark process. This is real guest TCP socket execution and stronger than AF_UNIX fallback, but still an in-process loopback service driver rather than a production TCP/TLS server.",
                    "",
                    "status=TCP_NETNS_PASS",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "- The guest loopback interface was unavailable, so all policies used the explicit AF_UNIX fallback. Count this as tagged socket-backed libssl evidence and environment diagnosis, not as TCP-loopback benchmark evidence.",
                    "",
                    "status=AF_UNIX_FALLBACK_PASS",
                    "",
                ]
            )
    else:
        lines.extend(
            [
                "- Transport setup or policy validation did not complete successfully in at least one policy run; these rows are diagnostic environment evidence, not benchmark evidence.",
                "- Do not cite CTLW, speed, or checksum comparisons from this summary as COPPER results.",
                "",
                "status=ENVIRONMENT_FAILURE",
                "",
            ]
        )
    md_path = OUT / f"ossltlstcp_{tag.upper()}_FS_SUMMARY.md"
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

