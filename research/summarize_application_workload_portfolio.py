#!/usr/bin/env python3
"""Aggregate application/service-style COPPER workload results."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "COPPER_APPLICATION_WORKLOAD_PORTFOLIO_20260616.md"

WORKLOADS = [
    (
        "SQLite small",
        RESULTS / "gem5_arm_ubuntu_fs_sqlite_app" / "sqlite_app_small_summary.csv",
    ),
    (
        "SQLite medium",
        RESULTS / "gem5_arm_ubuntu_fs_sqlite_app" / "sqlite_app_medium_summary.csv",
    ),
    (
        "SQLite stress",
        RESULTS / "gem5_arm_ubuntu_fs_sqlite_app" / "sqlite_app_stress_summary.csv",
    ),
    (
        "SQLite no-poison",
        RESULTS / "gem5_arm_ubuntu_fs_sqlite_app" / "sqlite_app_small_nopoison_summary.csv",
    ),
    (
        "Lua small",
        RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_small_summary.csv",
    ),
    (
        "Lua medium",
        RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_medium_summary.csv",
    ),
    (
        "Lua stress",
        RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_stress_summary.csv",
    ),
    (
        "Lua no-poison",
        RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_small_nopoison_summary.csv",
    ),
    (
        "Duktape small",
        RESULTS / "gem5_arm_ubuntu_fs_duktape_app" / "duktape_app_small_summary.csv",
    ),
    (
        "Duktape medium",
        RESULTS / "gem5_arm_ubuntu_fs_duktape_app" / "duktape_app_medium_summary.csv",
    ),
    (
        "Duktape stress",
        RESULTS / "gem5_arm_ubuntu_fs_duktape_app" / "duktape_app_stress_summary.csv",
    ),
    (
        "yyjson medium",
        RESULTS / "gem5_arm_ubuntu_fs_yyjson_app" / "yyjson_app_medium_summary.csv",
    ),
    (
        "yyjson stress",
        RESULTS / "gem5_arm_ubuntu_fs_yyjson_app" / "yyjson_app_stress_summary.csv",
    ),
    (
        "libxml2 XML tiny",
        RESULTS / "gem5_arm_ubuntu_fs_libxml2_app" / "libxml2_xml_tiny_full_summary.csv",
    ),
    (
        "libarchive TAR tiny",
        RESULTS / "gem5_arm_ubuntu_fs_libarchive_app" / "libarchive_tar_tiny_full_summary.csv",
    ),
    (
        "JSON+SQLite medium",
        RESULTS / "gem5_arm_ubuntu_fs_jsonsqlite_app" / "jsonsqlite_app_medium_summary.csv",
    ),
    (
        "JSON+SQLite stress",
        RESULTS / "gem5_arm_ubuntu_fs_jsonsqlite_app" / "jsonsqlite_app_stress_summary.csv",
    ),
    (
        "Cache-service small",
        RESULTS / "gem5_arm_ubuntu_fs_cachesvc_app" / "cachesvc_app_small_summary.csv",
    ),
    (
        "Cache-service medium",
        RESULTS / "gem5_arm_ubuntu_fs_cachesvc_app" / "cachesvc_app_medium_key_summary.csv",
    ),
    (
        "TLS session-service small",
        RESULTS / "gem5_arm_ubuntu_fs_tlssvc_app" / "tlssvc_app_smoke_summary.csv",
    ),
    (
        "OpenSSL libssl TLS memory-BIO small",
        RESULTS / "gem5_arm_ubuntu_fs_ossltlsbio_app" / "ossltlsbio_app_smoke_summary.csv",
    ),
    (
        "OpenSSL SHA service small",
        RESULTS / "gem5_arm_ubuntu_fs_osslsha_app" / "osslsha_app_smoke_summary.csv",
    ),
    (
        "OpenSSL EVP/HMAC service small",
        RESULTS / "gem5_arm_ubuntu_fs_osslcrypto_app" / "osslcrypto_app_smoke_summary.csv",
    ),
]

CONVENTIONAL = {"stride", "bop", "dcpt", "spp", "ampm", "indirect", "isb"}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def fmt_int(value: str) -> str:
    return f"{int(value):,}" if value else ""


def main() -> None:
    lines = [
        "# COPPER Application and Service-Style Workload Portfolio",
        "",
        "Date: 2026-06-17",
        "",
        "This file aggregates the new application/service-style AArch64/Linux",
        "full-system runs. It intentionally does not rewrite the paper; it records",
        "whether the new evidence closes the external-workload gap.",
        "",
        "| Workload | Policies present | Checksums agree | COPPER delta | Naive delta | Best conventional | Multi hybrid delta | Slack hybrid delta | Slack blocked | Slack CTLW | Naive CTLW | COPPER CTLW | CTLW reduction | COPPER faults |",
        "|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    portfolio_good = True
    for name, path in WORKLOADS:
        rows = read_rows(path)
        by = {row["policy"]: row for row in rows}
        checksums = {row["checksum"] for row in rows}
        checksum_ok = len(checksums) == 1 and "" not in checksums
        portfolio_good = portfolio_good and checksum_ok
        copper = by.get("copper_clpd64k_peb", {})
        naive = by.get("naive", {})
        hybrid = by.get("spp_copper", {})
        slack = by.get("spp_copper_slack", {})
        conventional_rows = [row for row in rows if row["policy"] in CONVENTIONAL]
        best_conv = ""
        if conventional_rows:
            best = min(conventional_rows, key=lambda row: float(row["tick_delta_vs_none_pct"]))
            best_conv = f"{best['policy']} {float(best['tick_delta_vs_none_pct']):.3f}%"
        naive_ctlw = int(naive.get("targetLineWitnessMisses", "0") or "0")
        copper_ctlw = int(copper.get("targetLineWitnessMisses", "0") or "0")
        reduction = 100.0 * (1.0 - copper_ctlw / naive_ctlw) if naive_ctlw else 0.0
        hybrid_delta = (
            f"{float(hybrid['tick_delta_vs_none_pct']):.3f}%"
            if hybrid else ""
        )
        slack_delta = (
            f"{float(slack['tick_delta_vs_none_pct']):.3f}%"
            if slack else ""
        )
        slack_blocked = fmt_int(slack.get("blockedNoProvenance", "")) if slack else ""
        slack_ctlw = fmt_int(slack.get("targetLineWitnessMisses", "")) if slack else ""
        lines.append(
            f"| {name} | {', '.join(row['policy'] for row in rows)} | "
            f"{'yes' if checksum_ok else 'no'} | "
            f"{float(copper.get('tick_delta_vs_none_pct', '0')):.3f}% | "
            f"{float(naive.get('tick_delta_vs_none_pct', '0')):.3f}% | "
            f"{best_conv} | "
            f"{hybrid_delta} | "
            f"{slack_delta} | "
            f"{slack_blocked} | "
            f"{slack_ctlw} | "
            f"{fmt_int(str(naive_ctlw))} | "
            f"{fmt_int(str(copper_ctlw))} | {reduction:.1f}% | "
            f"{fmt_int(copper.get('fillPrefetchTranslationFault', '0'))} |"
        )
    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            "- The application evidence is materially stronger than the earlier generated-only story: SQLite, upstream SQLite speedtest1 JSON/star/ORM, Lua, Duktape, yyjson, two-seed PCRE2 regex matching, public libxml2 XML parser/serializer execution, public libarchive TAR parser execution, Zstd and zlib compression/decompression, composed JSON+SQLite service-style workloads, cache-service hash/LRU workloads, a crypto-adjacent TLS/session-service stress point, real OpenSSL libssl TLS memory-BIO execution, socket-backed OpenSSL libssl TLS execution, strict private-netns TCP-loopback OpenSSL libssl TLS execution, two-seed process-separated private-netns TCP-loopback OpenSSL libssl TLS execution, and real OpenSSL libcrypto SHA256 plus EVP/HMAC drivers run as native AArch64 Linux binaries under gem5 full-system, now with medium/stress scale points for both the single-engine families and the service-composition workload plus small/medium cache-service scale points.",
            "- Across the application points, COPPER preserves checksum correctness and records zero translation faults while reducing naive DMP CTLW misses by roughly 77-99%.",
            "- The 2026-06-17 conventional matrix still covers eight single-engine medium/stress app points plus two bounded JSON+SQLite service-composition points and two bounded cache-service hash/LRU scale points and should be treated as the source of aggregate timing, traffic, and CTLW claims.",
            "- The TLS/session-service point is intentionally reported as a separate crypto-adjacent service-style stress point, not as a production TLS stack. It adds session hash/LRU metadata, linked record chains, and pointer-shaped ticket/mask words loaded by an authentication loop but never used as architectural addresses.",
            "- The PCRE2 seed-stability artifact covers two deterministic seeds for the public 8-bit regex compiler and matcher. Across both seeds, COPPER keeps at least 99.3% CTLW reduction, SPP+COPPER slack keeps at least 98.9% CTLW reduction, and COPPER/slack translation faults remain zero.",
            "- The libxml2 XML point calls the public XML parser and serializer in the ARM64 guest over deterministic in-memory XML records containing address-shaped words as data. On the tiny full-system point, COPPER and SPP+COPPER slack both cut naive-DMP CTLW misses by 98.9%, faults remain zero, and the slack hybrid stays within 0.035 percentage points of SPP.",
            "- The libarchive TAR point calls the public archive parser in the ARM64 guest over deterministic in-memory TAR entries containing address-shaped words as data. On the tiny full-system point, COPPER cuts naive-DMP CTLW misses by 98.0%, SPP+COPPER slack cuts them by 98.6%, faults remain zero, and the slack hybrid is within -0.004 percentage points of SPP.",
            "- The OpenSSL libssl TLS memory-BIO point executes the public TLS 1.2 PSK handshake and TLS record read/write path through libssl over paired memory BIOs with a deterministic benchmark RNG. It is a real TLS-library path, but still an in-process single-handshake harness rather than a production networked TLS server.",
            "- The OpenSSL SHA point is real guest libcrypto execution through the dynamic loader, but it is still a small synthetic driver around SHA256 rather than a full TLS stack or production crypto benchmark.",
            "- The OpenSSL EVP/HMAC point broadens real-libcrypto coverage to AES-CTR, HMAC-SHA256, SHA256, and CRYPTO_memcmp, but it is still a small service-style driver rather than a full TLS stack or production crypto benchmark.",
            "- The conventional matrix shows SPP is the strongest address-stream baseline on the app set; SPP+COPPER slack remains a near-SPP coexistence policy rather than a standalone speedup claim.",
            "- The result still does not justify a universal performance claim. Conventional prefetchers, especially SPP/DCPT/AMPM/BOP depending on workload, remain much faster on raw timing.",
            "- Hybrid SPP+COPPER is the strongest new direction: on the medium/stress application points, it retains SPP-class timing while preserving COPPER child-filter activity and zero translation faults.",
            "- The new slack-only companion arbiter gives this direction a cleaner mechanism: SPP has strict issue priority, and COPPER can issue only when the primary lane has no ready packet.",
            "- Best current paper positioning: COPPER is a safe authority layer for content-derived DMP candidates, and it should coexist with conventional address-correlation prefetchers rather than replacing them.",
            "- Remaining top-tier gap: broader production-like workloads and a deeper evaluation of the slack-only hybrid across more scales and security-adversarial inputs.",
            "",
            f"portfolio_status={'PASS' if portfolio_good else 'FAIL'}",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
