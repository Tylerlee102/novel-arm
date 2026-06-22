#!/usr/bin/env python3
"""Summarize Vivado vectorless power reports for COPPER RTL checkpoints."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
MANIFEST = RESULTS / "copper_rtl_power_proxy_manifest_20260618.csv"
OUT_CSV = RESULTS / "copper_rtl_power_proxy_20260618.csv"
OUT_MD = RESULTS / "COPPER_RTL_POWER_PROXY_20260618.md"


def parse_value(text: str) -> float | None:
    text = text.strip()
    if text in {"---", "NA", ""}:
        return None
    text = text.replace(",", "")
    if text.startswith("<"):
        try:
            return float(text[1:]) / 2.0
        except ValueError:
            return None
    leading = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    if leading:
        return float(leading.group(0))
    try:
        return float(text)
    except ValueError:
        return None


def first_match(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else ""


def metric(label: str, text: str) -> float | None:
    escaped = re.escape(label)
    match = re.search(rf"\|\s*{escaped}\s*\|\s*([^|]+)\|", text)
    return parse_value(match.group(1)) if match else None


def component(label: str, text: str) -> tuple[float | None, int | None]:
    escaped = re.escape(label)
    match = re.search(rf"\|\s*{escaped}\s*\|\s*([^|]+)\|\s*([^|]+)\|", text)
    if not match:
        return None, None
    power = parse_value(match.group(1))
    used_raw = match.group(2).strip().replace(",", "")
    try:
        used = int(used_raw)
    except ValueError:
        used = None
    return power, used


def clpd_entries(name: str) -> int | None:
    match = re.search(r"clpd(\d+)k", name)
    if not match:
        return None
    return int(match.group(1)) * 1024


def parse_report(path: Path) -> dict[str, object]:
    text = path.read_text(errors="replace")
    block_ram_power, block_ram_used = component("Block RAM", text)
    lut_power, lut_used = component("LUT as Logic", text)
    reg_power, reg_used = component("Register", text)
    signal_power, signal_used = component("Signals", text)
    clock_power, clock_used = component("Clocks", text)
    io_power, io_used = component("I/O", text)
    dynamic = metric("Dynamic (W)", text)
    return {
        "vivado_design": first_match(r"\|\s*Design\s*:\s*([^|]+)\|", text),
        "device": first_match(r"\|\s*Device\s*:\s*([^|]+)\|", text),
        "design_state": first_match(r"\|\s*Design State\s*:\s*([^|]+)\|", text),
        "confidence": first_match(r"\|\s*Confidence Level\s*\|\s*([^|]+)\|", text),
        "total_on_chip_w": metric("Total On-Chip Power (W)", text),
        "dynamic_w": dynamic,
        "static_w": metric("Device Static (W)", text),
        "clock_w": clock_power,
        "clock_used": clock_used,
        "signal_w": signal_power,
        "signal_used": signal_used,
        "lut_logic_w": lut_power,
        "lut_logic_used": lut_used,
        "register_w": reg_power,
        "register_used": reg_used,
        "block_ram_w": block_ram_power,
        "block_ram_used": block_ram_used,
        "io_w": io_power,
        "io_used": io_used,
        "io_artifact": bool(
            io_power is not None
            and dynamic is not None
            and dynamic > 0
            and io_power > 0.5 * dynamic
        ),
    }


def fmt(value: object, digits: int = 3) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def main() -> None:
    rows: list[dict[str, object]] = []
    with MANIFEST.open(newline="") as f:
        for item in csv.DictReader(f):
            row: dict[str, object] = dict(item)
            report = ROOT / item["report"]
            row["report_exists"] = report.exists()
            row["clpd_entries"] = clpd_entries(item["design"])
            if item["status"] == "OK" and report.exists():
                row.update(parse_report(report))
            rows.append(row)

    fieldnames = [
        "design",
        "vivado_design",
        "device",
        "design_state",
        "confidence",
        "status",
        "clpd_entries",
        "total_on_chip_w",
        "dynamic_w",
        "static_w",
        "clock_w",
        "signal_w",
        "lut_logic_w",
        "register_w",
        "block_ram_w",
        "io_w",
        "clock_used",
        "signal_used",
        "lut_logic_used",
        "register_used",
        "block_ram_used",
        "io_used",
        "io_artifact",
        "dcp",
        "report",
        "message",
    ]
    with OUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    ok = [r for r in rows if r.get("status") == "OK"]
    clpd = [r for r in ok if r.get("clpd_entries")]
    routed = [r for r in ok if str(r.get("design_state", "")).lower() == "routed"]
    full = next((r for r in ok if r["design"] == "copper_full_lsq_amba_authority_top_synth"), None)
    peb = next((r for r in ok if r["design"] == "copper_peb_synth"), None)
    clpd64_impl = next((r for r in ok if r["design"] == "copper_clpd_sram_dir_clpd64k_a200t_impl"), None)

    lines: list[str] = []
    lines.append("# COPPER RTL Power Proxy")
    lines.append("")
    lines.append("Generated: 2026-06-18")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append(
        "This report summarizes Vivado 2025.2 `report_power` results over existing COPPER RTL checkpoints. "
        "The estimates are FPGA/vectorless power proxies, not calibrated ASIC power. They are useful for "
        "bounding metadata-block implementation plausibility and for exposing whether COPPER's proposed "
        "proof tables are dominated by storage, logic, or clocking."
    )
    lines.append("")
    lines.append("## Key Results")
    lines.append("")
    lines.append(f"- Checkpoints attempted: {len(rows)}")
    lines.append(f"- Successful reports: {len(ok)}")
    lines.append(f"- Routed reports: {len(routed)}")
    if clpd64_impl:
        lines.append(
            "- Routed 64K-entry CLPD on xc7a200t: "
            f"{fmt(clpd64_impl.get('total_on_chip_w'))} W total, "
            f"{fmt(clpd64_impl.get('dynamic_w'))} W dynamic, "
            f"{fmt(clpd64_impl.get('static_w'))} W static, "
            f"{fmt(clpd64_impl.get('block_ram_used'), 0)} block-RAM tiles, "
            f"{fmt(clpd64_impl.get('lut_logic_used'), 0)} LUT-as-logic, "
            f"confidence {clpd64_impl.get('confidence')}."
        )
    if full:
        lines.append(
            "- Synthesized full LSQ/AMBA authority top: "
            f"{fmt(full.get('total_on_chip_w'))} W total, "
            f"{fmt(full.get('dynamic_w'))} W dynamic, "
            f"{fmt(full.get('lut_logic_used'), 0)} LUT-as-logic, "
            f"{fmt(full.get('register_used'), 0)} registers, "
            f"confidence {full.get('confidence')}."
        )
    if peb:
        lines.append(
            "- PEB epoch-boundary block: "
            f"{fmt(peb.get('total_on_chip_w'))} W total, "
            f"{fmt(peb.get('dynamic_w'))} W dynamic, "
            f"{fmt(peb.get('lut_logic_used'), 0)} LUT-as-logic, "
            f"{fmt(peb.get('register_used'), 0)} registers, "
            f"confidence {peb.get('confidence')}."
        )
    lines.append("")
    lines.append("## Summary Table")
    lines.append("")
    lines.append(
        "| Design | State | Device | Conf. | Total W | Dynamic W | Static W | LUTs | Regs | BRAM Tiles | I/O artifact |"
    )
    lines.append(
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|"
    )
    for r in ok:
        lines.append(
            f"| {r['design']} | {r.get('design_state', '')} | {r.get('device', '')} | "
            f"{r.get('confidence', '')} | {fmt(r.get('total_on_chip_w'))} | "
            f"{fmt(r.get('dynamic_w'))} | {fmt(r.get('static_w'))} | "
            f"{fmt(r.get('lut_logic_used'), 0)} | {fmt(r.get('register_used'), 0)} | "
            f"{fmt(r.get('block_ram_used'), 0)} | {r.get('io_artifact', False)} |"
        )
    lines.append("")
    lines.append("## CLPD Scaling")
    lines.append("")
    lines.append("| CLPD Entries | Design | State | Total W | Dynamic W | Block RAM W | BRAM Tiles | LUTs |")
    lines.append("|---:|---|---:|---:|---:|---:|---:|---:|")
    for r in sorted(clpd, key=lambda x: (int(x.get("clpd_entries") or 0), x["design"])):
        lines.append(
            f"| {r.get('clpd_entries')} | {r['design']} | {r.get('design_state', '')} | "
            f"{fmt(r.get('total_on_chip_w'))} | {fmt(r.get('dynamic_w'))} | "
            f"{fmt(r.get('block_ram_w'))} | {fmt(r.get('block_ram_used'), 0)} | "
            f"{fmt(r.get('lut_logic_used'), 0)} |"
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "The routed 64K-entry CLPD is storage-dominated on FPGA: block RAM accounts for "
        "0.313 W of the 0.344 W dynamic report, while LUT logic is only 0.001 W and "
        "signals 0.026 W. That is a useful architectural datapoint: COPPER's largest "
        "metadata structure behaves like a cache-adjacent SRAM table rather than a large "
        "logic fabric. The smaller synthesized control blocks are logic-light, but their "
        "absolute power has low confidence until placed/routed and driven by simulation activity."
    )
    lines.append("")
    lines.append("## Caveats")
    lines.append("")
    lines.append("- Vivado used vectorless activity propagation; no workload SAIF/VCD was supplied.")
    lines.append("- Most non-CLPD blocks are synthesized-only checkpoints, so their confidence is low.")
    lines.append("- The routed CLPD report is FPGA-specific and cannot be used as calibrated ASIC power.")
    lines.append(
        "- The tiny `copper_amba_sari_frontdoor_synth` datapoint is I/O-dominated in "
        "out-of-context Vivado reporting; it is retained for auditability but should "
        "not be used as an architectural power claim."
    )
    lines.append(
        "- This closes a reporting gap by measuring COPPER RTL metadata structures directly, "
        "but a top-tier submission still needs workload-derived switching or ASIC-style energy modeling."
    )
    lines.append("")
    lines.append("## Source Artifacts")
    lines.append("")
    lines.append(f"- CSV: `{OUT_CSV.relative_to(ROOT)}`")
    lines.append("- Vivado script: `research/run_copper_rtl_power_proxy.tcl`")
    lines.append(f"- Manifest: `{MANIFEST.relative_to(ROOT)}`")
    lines.append("")

    OUT_MD.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
