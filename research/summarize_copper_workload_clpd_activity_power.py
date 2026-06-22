#!/usr/bin/env python3
"""Summarize workload-derived CLPD activity power evidence."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "COPPER_WORKLOAD_CLPD_ACTIVITY_POWER_20260619.md"


def read(path: Path) -> str:
    return path.read_text(errors="replace") if path.exists() else ""


def first(pattern: str, text: str, default: str = "") -> str:
    match = re.search(pattern, text, flags=re.MULTILINE)
    return match.group(1).strip() if match else default


def metric(label: str, text: str) -> str:
    label_re = re.escape(label)
    return first(rf"\|\s*{label_re}\s*\|\s*([^|]+)\|", text)


def component(label: str, text: str) -> tuple[str, str]:
    label_re = re.escape(label)
    match = re.search(rf"\|\s*{label_re}\s*\|\s*([^|]+)\|\s*([^|]+)\|", text)
    if not match:
        return "", ""
    return match.group(1).strip(), match.group(2).strip()


def count_unmatched(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(errors="replace").splitlines() if line and not line.startswith("---"))


def pct(part: int, whole: int) -> str:
    if whole == 0:
        return "0.0%"
    return f"{100.0 * part / whole:.1f}%"


def main() -> None:
    counts_path = RESULTS / "copper_clpd_workload_replay_counts_20260619.json"
    counts = json.loads(counts_path.read_text(encoding="utf-8"))
    xsim = read(RESULTS / "copper_clpd_sram_workload_activity_xsim.log")
    power = read(RESULTS / "copper_clpd_sram_workload_activity_saif_power.rpt")
    timing = read(RESULTS / "copper_clpd_sram_workload_activity_timing.rpt")
    manifest = read(RESULTS / "copper_clpd_sram_workload_activity_saif_power_manifest_20260619.csv")

    replay_line = first(r"(COPPER CLPD workload activity replay completed:.*)", xsim)
    finish_time = first(r"\$finish called at time\s*:\s*([^:]+)\s*:", xsim)
    matched = metric("Design Nets Matched", power)
    total_power = metric("Total On-Chip Power (W)", power)
    dynamic_power = metric("Dynamic (W)", power)
    static_power = metric("Device Static (W)", power)
    confidence = metric("Confidence Level", power)
    bram_power, bram_used = component("Block RAM", power)
    lut_power, lut_used = component("LUT as Logic", power)
    reg_power, reg_used = component("Register", power)
    wns = first(r"^\s*([+-]?\d+\.\d+)\s+0\.000\s+\d+\s+\d+\s+[+-]?\d+\.\d+", timing)

    raw = counts["raw"]
    replay = counts["replay"]
    raw_driver_total = (
        raw["learned_proofs"]
        + raw["allowed_candidates"]
        + raw["blocked_no_provenance"]
        + raw["target_line_witness_misses"]
    )
    scaled_total = counts["replay_total_ops"]
    saif = RESULTS / "copper_clpd_sram_workload_activity.saif"
    unmatched = RESULTS / "copper_clpd_sram_workload_activity_saif_unmatched.txt"

    lines = [
        "# COPPER Workload-Derived CLPD Activity Power",
        "",
        "Generated: 2026-06-19",
        "",
        "## Scope",
        "",
        "This report summarizes a workload-derived RTL activity power pass for the COPPER CLPD SRAM directory. "
        "The driver is not an instruction-by-instruction full-system waveform; it is a transaction-level replay "
        "whose operation mix is scaled from measured gem5 full-system COPPER counters across public app/service/parser workloads. "
        "This is stronger than a random testbench SAIF, but it remains an FPGA power proxy rather than ASIC-calibrated power.",
        "",
        "## Replay Source",
        "",
        f"- Source CSV: `{counts['source_csv']}`",
        f"- Source policy: `{counts['policy']}`",
        f"- Workload rows: {counts['workload_rows']}",
        f"- Raw driver events: {raw_driver_total:,}",
        f"- Replay events: {scaled_total:,}",
        f"- Scale factor: {counts['scale_factor']:.9f}",
        f"- Pointer-like candidates in source rows: {raw['pointer_like_candidates']:,}",
        f"- Prefetches issued in source rows: {raw['pf_issued']:,}",
        f"- Boundary authority entries dropped in source rows: {raw['boundary_authority_entries_dropped']:,}",
        "",
        "## Raw To Replay Counts",
        "",
        "| Event class | Raw count | Replay count | Replay mix |",
        "|---|---:|---:|---:|",
        f"| Learned proofs / commits | {raw['learned_proofs']:,} | {replay['commit_ops']:,} | {pct(replay['commit_ops'], scaled_total)} |",
        f"| Allowed candidates / allow queries | {raw['allowed_candidates']:,} | {replay['allow_queries']:,} | {pct(replay['allow_queries'], scaled_total)} |",
        f"| Blocked no provenance / no-entry queries | {raw['blocked_no_provenance']:,} | {replay['block_queries']:,} | {pct(replay['block_queries'], scaled_total)} |",
        f"| Target witness misses / fault-permission queries | {raw['target_line_witness_misses']:,} | {replay['fault_queries']:,} | {pct(replay['fault_queries'], scaled_total)} |",
        "",
        "## RTL Replay",
        "",
        f"- XSim result: `{replay_line}`",
        f"- Finish time: `{finish_time}`",
        f"- SAIF file: `{saif.relative_to(ROOT)}` ({saif.stat().st_size if saif.exists() else 0} bytes)",
        "- CLPD configuration: 1K-entry banked SRAM directory, 32-bit line tag, 8-bit token, 8-bit epoch.",
        "- Replay discipline: commits install proven words; allow/fault queries are selected from live scoreboard proofs; no-provenance queries intentionally miss source provenance.",
        "",
        "## Vivado Power Result",
        "",
        "| Source | Mapping | Total W | Dynamic W | Static W | Confidence | Timing |",
        "|---|---:|---:|---:|---:|---:|---|",
        f"| Workload-derived SAIF | {matched} | {total_power} | {dynamic_power} | {static_power} | {confidence} | WNS {wns} ns |",
        "",
        "## Component Breakdown",
        "",
        "| Component | Power W | Used |",
        "|---|---:|---:|",
        f"| Block RAM | {bram_power} | {bram_used} |",
        f"| LUT as Logic | {lut_power} | {lut_used} |",
        f"| Register | {reg_power} | {reg_used} |",
        "",
        "## Mapping Audit",
        "",
        f"- SAIF manifest: `{manifest.strip()}`",
        f"- SAIF unmatched entries: {count_unmatched(unmatched)}",
        "",
        "The key evidence improvement is that the CLPD switching data is now tied to measured full-system COPPER event ratios, "
        "not just synthetic directed/random activity. It still does not prove final silicon power or a production integrated SoC timing point. "
        "It does, however, make the metadata-energy claim more defensible because the same measured workload portfolio now feeds both the performance counters and the RTL activity estimate.",
        "",
        "## Source Artifacts",
        "",
        "- Replay count builder: `research/build_copper_workload_clpd_replay.py`",
        "- RTL replay testbench: `research/copper_clpd_sram_workload_activity_tb.sv`",
        "- XSim SAIF script: `research/copper_clpd_sram_workload_activity_saif_xsim.tcl`",
        "- XSim wrapper: `research/run_copper_clpd_sram_workload_activity_xsim.ps1`",
        "- Vivado SAIF power script: `research/run_copper_clpd_sram_workload_saif_power.tcl`",
        "",
    ]

    OUT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
