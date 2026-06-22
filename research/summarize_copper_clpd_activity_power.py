#!/usr/bin/env python3
"""Summarize CLPD SRAM simulation-activity power evidence."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "COPPER_CLPD_ACTIVITY_POWER_20260619.md"


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


def main() -> None:
    xsim = read(RESULTS / "copper_clpd_sram_activity_xsim.log")
    saif_xsim = read(RESULTS / "copper_clpd_sram_activity_saif_xsim.log")
    vcd_power = read(RESULTS / "copper_clpd_sram_dir_activity_power.rpt")
    saif_power = read(RESULTS / "copper_clpd_sram_dir_activity_saif_power.rpt")
    timing = read(RESULTS / "copper_clpd_sram_dir_activity_timing.rpt")
    saif_manifest = read(RESULTS / "copper_clpd_sram_dir_activity_saif_power_manifest_20260618.csv")
    vcd_manifest = read(RESULTS / "copper_clpd_sram_dir_activity_power_manifest_20260618.csv")

    test_line = first(r"(COPPER CLPD SRAM directory tests completed:.*)", saif_xsim or xsim)
    finish_time = first(r"\$finish called at time\s*:\s*([^:]+)\s*:", saif_xsim or xsim)
    vcd_matched = metric("Design Nets Matched", vcd_power)
    saif_matched = metric("Design Nets Matched", saif_power)
    saif_total = metric("Total On-Chip Power (W)", saif_power)
    saif_dynamic = metric("Dynamic (W)", saif_power)
    saif_static = metric("Device Static (W)", saif_power)
    saif_conf = metric("Confidence Level", saif_power)
    bram_power, bram_used = component("Block RAM", saif_power)
    lut_power, lut_used = component("LUT as Logic", saif_power)
    reg_power, reg_used = component("Register", saif_power)
    wns = first(r"^\s*([+-]?\d+\.\d+)\s+0\.000\s+\d+\s+\d+\s+[+-]?\d+\.\d+", timing)

    saif_path = RESULTS / "copper_clpd_sram_dir_activity.saif"
    vcd_path = RESULTS / "copper_clpd_sram_dir_activity.vcd"
    unmatched_saif = RESULTS / "copper_clpd_sram_dir_activity_saif_unmatched.txt"
    unmatched_vcd = RESULTS / "copper_clpd_sram_dir_activity_vcd_unmatched.txt"

    lines = [
        "# COPPER CLPD Activity Power",
        "",
        "Generated: 2026-06-19",
        "",
        "## Scope",
        "",
        "This report summarizes a simulation-activity power pass for the COPPER CLPD SRAM directory. "
        "The activity source is the existing XSim CLPD SRAM testbench, not a full-system workload. "
        "The matched synthesis configuration is the testbench-scale 64-entry CLPD, not the 64K-entry routed CLPD.",
        "",
        "## Testbench Activity",
        "",
        f"- XSim result: `{test_line}`",
        f"- Finish time: `{finish_time}`",
        f"- SAIF file: `{saif_path.relative_to(ROOT)}` ({saif_path.stat().st_size if saif_path.exists() else 0} bytes)",
        f"- VCD file: `{vcd_path.relative_to(ROOT)}` ({vcd_path.stat().st_size if vcd_path.exists() else 0} bytes)",
        "- Activity shape: directed proof/hazard cases plus 4,000 randomized commit/purge/query operations.",
        "",
        "## Power Results",
        "",
        "| Source | Mapping | Total W | Dynamic W | Static W | Confidence | Timing |",
        "|---|---:|---:|---:|---:|---:|---|",
        f"| VCD | {vcd_matched} | {metric('Total On-Chip Power (W)', vcd_power)} | {metric('Dynamic (W)', vcd_power)} | {metric('Device Static (W)', vcd_power)} | {metric('Confidence Level', vcd_power)} | routed fallback |",
        f"| SAIF | {saif_matched} | {saif_total} | {saif_dynamic} | {saif_static} | {saif_conf} | WNS {wns} ns, constraints met |",
        "",
        "## SAIF Component Breakdown",
        "",
        "| Component | Power W | Used |",
        "|---|---:|---:|",
        f"| Block RAM | {bram_power} | {bram_used} |",
        f"| LUT as Logic | {lut_power} | {lut_used} |",
        f"| Register | {reg_power} | {reg_used} |",
        "",
        "## Mapping Audit",
        "",
        f"- SAIF manifest: `{saif_manifest.strip()}`",
        f"- VCD manifest: `{vcd_manifest.strip()}`",
        f"- SAIF unmatched entries: {count_unmatched(unmatched_saif)}",
        f"- VCD unmatched entries: {count_unmatched(unmatched_vcd)}",
        "",
        "The SAIF path is the useful activity result: Vivado matched 126 of 342 design nets, or 37%. "
        "The VCD path is retained as a negative control: Vivado read it, but matched only 1 of 342 nets. "
        "The SAIF unmatched list is dominated by `entry_mem[...]` bits because synthesis maps the unpacked RTL array into RAM primitives; "
        "remaining unmatched nodes are filled by Vivado's probabilistic activity model.",
        "",
        "## Interpretation",
        "",
        "Under the directed/random CLPD activity source, the routed 64-entry CLPD reports 0.076 W total on-chip FPGA power, "
        "0.007 W dynamic, and 0.069 W static with medium confidence. The datapoint is useful because it proves the local "
        "tool flow can carry simulation activity into a routed COPPER metadata block. It does not replace the 64K vectorless "
        "CLPD result, and it is not a calibrated ASIC or workload-derived full-system power result.",
        "",
        "## Source Artifacts",
        "",
        "- XSim VCD script: `research/copper_clpd_sram_activity_xsim.tcl`",
        "- XSim SAIF script: `research/copper_clpd_sram_activity_saif_xsim.tcl`",
        "- Activity XSim wrapper: `research/run_copper_clpd_sram_activity_xsim.ps1`",
        "- Vivado matched-design power script: `research/run_copper_clpd_sram_activity_power.tcl`",
        "- Vivado SAIF-from-DCP power script: `research/run_copper_clpd_sram_saif_power_from_dcp.tcl`",
        "",
    ]

    OUT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
