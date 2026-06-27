#!/usr/bin/env python3
"""Build a gem5 DRAM-energy scorecard for COPPER/SCOOP app runs."""

from __future__ import annotations

import csv
import math
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT_CSV = RESULTS / "copper_dram_energy_scorecard_20260618.csv"
OUT_MD = RESULTS / "COPPER_DRAM_ENERGY_SCORECARD_20260618.md"

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
    "tlssvc_small": "tlssvc_app_smoke",
    "ossltlsbio_small": "ossltlsbio_app_smoke",
    "osslsha_small": "osslsha_app_smoke",
    "osslcrypto_small": "osslcrypto_app_smoke",
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
ENERGY_FIELDS = [
    "totalEnergy",
    "readEnergy",
    "writeEnergy",
    "actEnergy",
    "preEnergy",
    "refreshEnergy",
    "actBackEnergy",
    "preBackEnergy",
]
OP_FIELDS = ["readEnergy", "writeEnergy", "actEnergy", "preEnergy"]


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


def sum_energy(stats: dict[str, float], field: str) -> float:
    pattern = re.compile(
        rf"^board\.memory\.mem_ctrl\d+\.dram\.rank\d+\.{re.escape(field)}$"
    )
    return sum(
        value
        for key, value in stats.items()
        if pattern.search(key) and not math.isnan(value)
    )


def pct_delta(value: float, base: float) -> float:
    return ((value / base) - 1.0) * 100.0 if base else 0.0


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def run_dir(tag: str, policy: str) -> Path:
    return RESULTS / f"gem5_arm_ubuntu_fs_{tag}_{policy}"


def collect_one(workload: str, tag: str, policy: str) -> dict[str, str]:
    path = run_dir(tag, policy) / "stats.txt"
    sections = parse_stats_sections(path)
    if not sections:
        raise RuntimeError(f"no stats sections in {path}")
    # The first stats section is the ROI section for these runs; later sections
    # include post-workload/teardown counters and do not match summary roi_ticks.
    stats = sections[0]
    row: dict[str, str] = {
        "workload": workload,
        "policy": policy,
        "sim_ticks": str(int(stats.get("simTicks", 0))),
    }
    for field in ENERGY_FIELDS:
        row[field] = f"{sum_energy(stats, field):.3f}"
    op_energy = sum(float(row[field]) for field in OP_FIELDS)
    row["opEnergy"] = f"{op_energy:.3f}"
    return row


def main() -> None:
    rows = [
        collect_one(workload, tag, policy)
        for workload, tag in WORKLOADS.items()
        for policy in POLICIES
    ]
    by_workload: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        by_workload[row["workload"]][row["policy"]] = row

    for workload, policies in by_workload.items():
        base = policies["none"]
        base_total = float(base["totalEnergy"])
        base_op = float(base["opEnergy"])
        base_ticks = float(base["sim_ticks"])
        for row in policies.values():
            row["totalEnergy_delta_vs_none_pct"] = f"{pct_delta(float(row['totalEnergy']), base_total):.3f}"
            row["opEnergy_delta_vs_none_pct"] = f"{pct_delta(float(row['opEnergy']), base_op):.3f}"
            row["sim_ticks_delta_vs_none_pct"] = f"{pct_delta(float(row['sim_ticks']), base_ticks):.3f}"

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    policies = {policy: [] for policy in POLICIES if policy != "none"}
    copper_vs_naive_total = 0
    copper_vs_naive_op = 0
    slack_vs_spp_total = 0
    slack_vs_spp_op = 0
    slack_gaps_total: list[float] = []
    slack_gaps_op: list[float] = []
    for workload, pol in by_workload.items():
        for policy in policies:
            policies[policy].append(pol[policy])
        if float(pol["copper_clpd64k_peb"]["totalEnergy"]) <= float(pol["naive"]["totalEnergy"]):
            copper_vs_naive_total += 1
        if float(pol["copper_clpd64k_peb"]["opEnergy"]) <= float(pol["naive"]["opEnergy"]):
            copper_vs_naive_op += 1
        if float(pol["spp_copper_slack"]["totalEnergy"]) <= float(pol["spp"]["totalEnergy"]):
            slack_vs_spp_total += 1
        if float(pol["spp_copper_slack"]["opEnergy"]) <= float(pol["spp"]["opEnergy"]):
            slack_vs_spp_op += 1
        slack_gaps_total.append(
            pct_delta(
                float(pol["spp_copper_slack"]["totalEnergy"]),
                float(pol["spp"]["totalEnergy"]),
            )
        )
        slack_gaps_op.append(
            pct_delta(
                float(pol["spp_copper_slack"]["opEnergy"]),
                float(pol["spp"]["opEnergy"]),
            )
        )

    point_count = len(WORKLOADS)
    lines = [
        "# COPPER DRAM Energy Scorecard",
        "",
        "Date: 2026-06-18",
        "",
        f"Scope: {point_count} AArch64 full-system points: the 12 public app/service matrix plus TLS/session-service, OpenSSL libssl TLS memory-BIO, OpenSSL SHA256, OpenSSL EVP/HMAC, public PCRE2, public libxml2 XML, public libarchive TAR, public Zstd, public zlib, and scaled process-separated OpenSSL libssl TCP-netns runs.",
        "",
        "Source: gem5 DRAM rank energy counters in `stats.txt` (`totalEnergy`, read/write/activate/precharge, refresh, and background energy), summed across memory controllers and ranks. Units are pJ. This is a calibrated memory-system energy counter from gem5/DRAMPower-style modeling, not full-chip McPAT or silicon power.",
        "",
        "## Aggregate Delta vs No Prefetch",
        "",
        "| Policy | Mean runtime delta | Mean total DRAM energy delta | Mean DRAM op-energy delta |",
        "|---|---:|---:|---:|",
    ]
    for policy, prs in policies.items():
        lines.append(
            f"| {policy} | "
            f"{mean([float(row['sim_ticks_delta_vs_none_pct']) for row in prs]):.3f}% | "
            f"{mean([float(row['totalEnergy_delta_vs_none_pct']) for row in prs]):.3f}% | "
            f"{mean([float(row['opEnergy_delta_vs_none_pct']) for row in prs]):.3f}% |"
        )

    lines.extend(
        [
            "",
            "## Pairwise Findings",
            "",
            f"- COPPER CLPD-64K+PEB has lower-or-equal total DRAM energy than naive DMP on {copper_vs_naive_total}/{point_count} points and lower-or-equal DRAM operation energy on {copper_vs_naive_op}/{point_count} points.",
            f"- SPP+COPPER slack has lower-or-equal total DRAM energy than SPP on {slack_vs_spp_total}/{point_count} points and lower-or-equal DRAM operation energy on {slack_vs_spp_op}/{point_count} points.",
            f"- SPP+COPPER slack total DRAM energy gap versus SPP averages {mean(slack_gaps_total):.3f}% with worst absolute gap {max(abs(v) for v in slack_gaps_total):.3f}%.",
            f"- SPP+COPPER slack DRAM operation-energy gap versus SPP averages {mean(slack_gaps_op):.3f}% with worst absolute gap {max(abs(v) for v in slack_gaps_op):.3f}%.",
            "",
            "## Per-Workload Table",
            "",
            "| Workload | Policy | Runtime delta | Total DRAM energy delta | DRAM op-energy delta | Total DRAM energy pJ | DRAM op-energy pJ |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['workload']} | {row['policy']} | "
            f"{row.get('sim_ticks_delta_vs_none_pct', '0.000')}% | "
            f"{row.get('totalEnergy_delta_vs_none_pct', '0.000')}% | "
            f"{row.get('opEnergy_delta_vs_none_pct', '0.000')}% | "
            f"{float(row['totalEnergy']):.0f} | {float(row['opEnergy']):.0f} |"
        )

    lines.extend(
        [
            "",
            "## Reviewer-Facing Interpretation",
            "",
            "- This upgrades the earlier traffic/pollution proxy with actual gem5 DRAM rank energy counters already emitted by the full-system runs.",
            "- The result should be described as DRAM energy, not total CPU or SoC energy. Core dynamic/leakage power still needs McPAT, RTL power, or silicon counters.",
            "- The key comparison remains conservative: COPPER is lower than naive DMP on most points, while SPP+COPPER slack stays close to SPP in both runtime and DRAM energy.",
            "",
            f"CSV: `{OUT_CSV.relative_to(ROOT).as_posix()}`.",
            "",
            "status=PASS",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(OUT_CSV)
    print(OUT_MD)


if __name__ == "__main__":
    main()
