#!/usr/bin/env python3
"""Summarize randomized Olden results with gem5 built-in prefetch baselines."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "results" / "gem5_arm_ubuntu_fs_olden_suite"
TAGS = {
    "small randomized suite": "suite4_randomalloc",
    "medium randomized subset": "suite3_medium_randomalloc",
}
POLICIES = [
    "none",
    "stride",
    "bop",
    "spp",
    "spp_copper",
    "spp_copper_slack",
    "dcpt",
    "ampm",
    "indirect",
    "isb",
    "naive",
    "copper_clpd64k_peb",
]


def main() -> None:
    lines = [
        "# Olden Built-In Prefetcher Baselines",
        "",
        "This compares COPPER against gem5 built-in prefetchers on public",
        "randomized-allocation Olden workloads. BOP, SPP, DCPT, AMPM,",
        "indirect-memory, and ISB are conventional address-stream/correlation",
        "prefetchers; they are not content-derived DMP mechanisms and therefore",
        "do not exercise COPPER's source-proof/target-witness safety counters.",
        "The `spp_copper` and `spp_copper_slack` rows are different: they",
        "keep SPP while adding COPPER as a safe content-derived companion lane.",
        "",
        "| Workload | Policy | Mean tick delta vs none | Total PF issued | PF per 1K insts | CTLW misses | Translation faults |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    by_workload: dict[str, dict[str, dict[str, float]]] = {}
    for workload, tag in TAGS.items():
        with (OUT / f"olden_{tag}_summary.csv").open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        by_workload[workload] = {}
        for policy in POLICIES:
            selected = [row for row in rows if row["policy"] == policy]
            if not selected:
                continue
            mean_delta = sum(float(row["tick_delta_vs_none_pct"]) for row in selected) / len(selected)
            pf = sum(int(row["pfIssued"]) for row in selected)
            insts = sum(int(row["insts_not_nop"]) for row in selected)
            ctlw = sum(int(row["targetLineWitnessMisses"]) for row in selected)
            faults = sum(int(row["fillPrefetchTranslationFault"]) for row in selected)
            pf_per_kinst = (pf / insts * 1000.0) if insts else 0.0
            by_workload[workload][policy] = {
                "mean_delta": mean_delta,
                "pf": pf,
                "pf_per_kinst": pf_per_kinst,
                "ctlw": ctlw,
                "faults": faults,
            }
            lines.append(
                f"| {workload} | {policy} | {mean_delta:.3f}% | {pf} | "
                f"{pf_per_kinst:.3f} | {ctlw} | {faults} |"
            )

    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            "- DCPT and SPP are the best measured pure conventional baselines on both Olden points: DCPT is -5.742% small / -7.025% medium, and SPP is -2.963% small / -5.870% medium.",
            "- On the small randomized suite, hybrid SPP+COPPER reaches -3.245% with stock Multi arbitration and -3.192% with the slack-only companion arbiter, slightly better than SPP alone while exercising COPPER's authority path with zero translation faults.",
            "- COPPER CLPD-64K+PEB is not the fastest policy on Olden (-0.398% small / -2.616% medium), but it is the only policy in this table that evaluates content-derived pointer candidates under committed provenance and target-witness authority.",
            "- Naive DMP produces 188,223 small-suite and 123,516 medium-subset CTLW misses; COPPER cuts those to 29,039 and 47,145 while preserving zero translation faults.",
            "- BOP/SPP/DCPT/AMPM/indirect/ISB should be presented as conventional-performance baselines, not as safety baselines for data-dependent pointer chasing.",
            "",
        ]
    )
    out = OUT / "OLDEN_BUILTIN_BASELINES.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
