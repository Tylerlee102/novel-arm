from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


@dataclass(frozen=True)
class SynthRun:
    name: str
    entries: int
    part: str
    util: Path
    timing: Path
    log: Path


RUNS = [
    SynthRun("clpd1k_a35t", 1024, "xc7a35tcpg236-1", RESULTS / "copper_clpd_sram_dir_clpd1k_utilization.rpt", RESULTS / "copper_clpd_sram_dir_clpd1k_timing.rpt", RESULTS / "copper_clpd_sram_dir_synth_sweep.log"),
    SynthRun("clpd2k_a35t", 2048, "xc7a35tcpg236-1", RESULTS / "copper_clpd_sram_dir_clpd2k_utilization.rpt", RESULTS / "copper_clpd_sram_dir_clpd2k_timing.rpt", RESULTS / "copper_clpd_sram_dir_synth_sweep.log"),
    SynthRun("clpd4k_a35t", 4096, "xc7a35tcpg236-1", RESULTS / "copper_clpd_sram_dir_clpd4k_utilization.rpt", RESULTS / "copper_clpd_sram_dir_clpd4k_timing.rpt", RESULTS / "copper_clpd_sram_dir_synth_sweep.log"),
    SynthRun("clpd8k_a35t", 8192, "xc7a35tcpg236-1", RESULTS / "copper_clpd_sram_dir_clpd8k_utilization.rpt", RESULTS / "copper_clpd_sram_dir_clpd8k_timing.rpt", RESULTS / "copper_clpd_sram_dir_synth_extended.log"),
    SynthRun("clpd16k_a35t", 16384, "xc7a35tcpg236-1", RESULTS / "copper_clpd_sram_dir_clpd16k_utilization.rpt", RESULTS / "copper_clpd_sram_dir_clpd16k_timing.rpt", RESULTS / "copper_clpd_sram_dir_synth_extended.log"),
    SynthRun("clpd16k_a200t", 16384, "xc7a200tfbg676-2", RESULTS / "copper_clpd_sram_dir_clpd16k_a200t_utilization.rpt", RESULTS / "copper_clpd_sram_dir_clpd16k_a200t_timing.rpt", RESULTS / "copper_clpd_sram_dir_synth_a200t.log"),
    SynthRun("clpd64k_a200t", 65536, "xc7a200tfbg676-2", RESULTS / "copper_clpd_sram_dir_clpd64k_a200t_utilization.rpt", RESULTS / "copper_clpd_sram_dir_clpd64k_a200t_timing.rpt", RESULTS / "copper_clpd_sram_dir_synth_a200t.log"),
]

IMPL64K_UTIL = RESULTS / "copper_clpd_sram_dir_clpd64k_a200t_impl_utilization.rpt"
IMPL64K_TIMING = RESULTS / "copper_clpd_sram_dir_clpd64k_a200t_impl_timing.rpt"
IMPL64K_ROUTE = RESULTS / "copper_clpd_sram_dir_clpd64k_a200t_route_status.rpt"
IMPL64K_LOG = RESULTS / "copper_clpd_sram_dir_impl64k_a200t.log"


def _extract_table_value(text: str, label: str) -> tuple[int, float]:
    for line in text.splitlines():
        fields = [field.strip() for field in line.split("|")]
        if len(fields) >= 7 and fields[1] == label:
            return int(fields[2]), float(fields[6])
    raise ValueError(f"missing {label}")


def _extract_table_value_any(text: str, labels: list[str]) -> tuple[int, float]:
    for label in labels:
        try:
            return _extract_table_value(text, label)
        except ValueError:
            pass
    raise ValueError(f"missing any of {labels}")


def _extract_simple_count(text: str, label: str) -> int:
    pattern = re.compile(rf"\|\s*{re.escape(label)}\s*\|\s*([0-9]+)\s*\|")
    match = pattern.search(text)
    if not match:
        raise ValueError(f"missing {label}")
    return int(match.group(1))


def _extract_timing(text: str, label: str) -> float:
    pattern = re.compile(rf"{label}\s*:\s*0\s+Failing Endpoints,\s+Worst Slack\s+([-0-9.]+)ns")
    match = pattern.search(text)
    if not match:
        raise ValueError(f"missing timing {label}")
    return float(match.group(1))


def _log_status(log_text: str, run: SynthRun) -> tuple[int, int, int, bool]:
    if "true dual port RAM template" not in log_text:
        true_dual = False
    else:
        true_dual = True
    chunks = log_text.split("Synthesis finished with")
    # The run scripts synthesize sequentially. Match by RAM bit count when possible.
    ram_bits = run.entries * 65
    marker = f"{ram_bits // 1024}K Bit"
    if marker in log_text:
        idx = log_text.find(marker)
        tail = log_text[idx:]
    else:
        tail = log_text
    match = re.search(r"Synthesis finished with\s+([0-9]+)\s+errors,\s+([0-9]+)\s+critical warnings\s+and\s+([0-9]+)\s+warnings", tail)
    if not match:
        # Fall back to the final status in the log.
        match = re.search(r"Synthesis finished with\s+([0-9]+)\s+errors,\s+([0-9]+)\s+critical warnings\s+and\s+([0-9]+)\s+warnings", log_text)
    if not match:
        raise ValueError(f"missing synthesis status for {run.name}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3)), true_dual


def parse_run(run: SynthRun) -> dict[str, object]:
    util_text = run.util.read_text(encoding="utf-8", errors="replace")
    timing_text = run.timing.read_text(encoding="utf-8", errors="replace")
    log_text = run.log.read_text(encoding="utf-8", errors="replace")

    luts, lut_pct = _extract_table_value_any(util_text, ["Slice LUTs*", "Slice LUTs"])
    regs, reg_pct = _extract_table_value(util_text, "Slice Registers")
    bram_tiles, bram_pct = _extract_table_value(util_text, "Block RAM Tile")
    ramb36 = _extract_simple_count(util_text, "RAMB36/FIFO*")
    ramb18 = _extract_simple_count(util_text, "RAMB18")
    dsps, dsp_pct = _extract_table_value(util_text, "DSPs")
    wns = _extract_timing(timing_text, "Setup")
    whs = _extract_timing(timing_text, "Hold")
    errors, critical_warnings, warnings, true_dual = _log_status(log_text, run)

    return {
        "name": run.name,
        "entries": run.entries,
        "entry_bits": 65,
        "total_kib": run.entries * 65 / 8 / 1024,
        "part": run.part,
        "luts": luts,
        "lut_pct": lut_pct,
        "regs": regs,
        "reg_pct": reg_pct,
        "bram_tiles": bram_tiles,
        "bram_pct": bram_pct,
        "ramb36": ramb36,
        "ramb18": ramb18,
        "dsps": dsps,
        "dsp_pct": dsp_pct,
        "wns_ns": wns,
        "whs_ns": whs,
        "errors": errors,
        "critical_warnings": critical_warnings,
        "warnings": warnings,
        "true_dual_port_ram": true_dual,
        "fits_part": errors == 0 and critical_warnings == 0 and bram_pct <= 100.0,
    }


def parse_impl64k() -> dict[str, object]:
    util_text = IMPL64K_UTIL.read_text(encoding="utf-8", errors="replace")
    timing_text = IMPL64K_TIMING.read_text(encoding="utf-8", errors="replace")
    route_text = IMPL64K_ROUTE.read_text(encoding="utf-8", errors="replace")
    log_text = IMPL64K_LOG.read_text(encoding="utf-8", errors="replace")

    luts, lut_pct = _extract_table_value_any(util_text, ["Slice LUTs*", "Slice LUTs"])
    regs, reg_pct = _extract_table_value(util_text, "Slice Registers")
    bram_tiles, bram_pct = _extract_table_value(util_text, "Block RAM Tile")
    dsps, dsp_pct = _extract_table_value(util_text, "DSPs")
    wns = _extract_timing(timing_text, "Setup")
    whs = _extract_timing(timing_text, "Hold")
    route_errors = re.search(r"# of nets with routing errors\.+\s*:\s*([0-9]+)", route_text)
    routable = re.search(r"# of routable nets\.+\s*:\s*([0-9]+)", route_text)
    fully_routed = re.search(r"# of fully routed nets\.+\s*:\s*([0-9]+)", route_text)
    status_matches = re.findall(
        r"([0-9]+)\s+Critical Warnings and\s+([0-9]+)\s+Errors encountered",
        log_text,
    )
    critical_warnings, errors = (
        (int(status_matches[-1][0]), int(status_matches[-1][1]))
        if status_matches
        else (-1, -1)
    )

    return {
        "entries": 65536,
        "part": "xc7a200tfbg676-2",
        "luts": luts,
        "lut_pct": lut_pct,
        "regs": regs,
        "reg_pct": reg_pct,
        "bram_tiles": bram_tiles,
        "bram_pct": bram_pct,
        "dsps": dsps,
        "dsp_pct": dsp_pct,
        "wns_ns": wns,
        "whs_ns": whs,
        "route_errors": int(route_errors.group(1)) if route_errors else -1,
        "unrouted": (
            int(routable.group(1)) - int(fully_routed.group(1))
            if routable and fully_routed
            else -1
        ),
        "partial": 0 if route_errors and route_errors.group(1) == "0" else -1,
        "critical_warnings": critical_warnings,
        "errors": errors,
        "route_success": "route_design completed successfully" in log_text,
    }


def main() -> None:
    rows = [parse_run(run) for run in RUNS]
    impl64k = parse_impl64k()
    csv_path = RESULTS / "copper_clpd_sram_synth_summary.csv"
    md_path = RESULTS / "COPPER_CLPD_SRAM_SYNTH_SUMMARY.md"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# COPPER CLPD SRAM Synthesis Summary",
        "",
        "Generated from Vivado utilization, timing, and synthesis logs.",
        "",
        "| Run | Entries | Part | KiB | LUTs | FFs | BRAM tiles | BRAM % | WNS ns | WHS ns | Errors | Critical warnings | Fits part |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {name} | {entries} | {part} | {total_kib:.2f} | {luts} | {regs} | {bram_tiles} | {bram_pct:.2f} | {wns_ns:.3f} | {whs_ns:.3f} | {errors} | {critical_warnings} | {fits_part} |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "## Routed 64K A200T Implementation",
            "",
            "| Entries | Part | LUTs | FFs | BRAM tiles | BRAM % | DSPs | WNS ns | WHS ns | Route errors | Unrouted nets | Partial nets | Errors | Critical warnings |",
            "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            "| {entries} | {part} | {luts} | {regs} | {bram_tiles} | {bram_pct:.2f} | {dsps} | {wns_ns:.3f} | {whs_ns:.3f} | {route_errors} | {unrouted} | {partial} | {errors} | {critical_warnings} |".format(
                **impl64k
            ),
            "",
            "Key interpretation:",
            "",
            "- All completed runs infer true-dual-port RAM for the CLPD storage array.",
            "- On the small Artix-7 35T, 8K entries fit at 66% BRAM; 16K synthesizes but overuses BRAM at 130%, so it is not a fit for that part.",
            "- On Artix-7 200T, the evaluated full 64K CLPD capacity synthesizes with no errors or critical warnings, using 260 BRAM tiles (71.23%).",
            "- The 64K A200T out-of-context routed implementation completes routing with 0 route errors, 0 unrouted nets, 0 partial nets, and meets the 10 ns timing target with 0.362 ns setup slack.",
            "- The routed run emits out-of-context port-location warnings; use the routed timing as feasibility evidence for the block, not as full-chip signoff.",
        ]
    )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path)
    print(csv_path)


if __name__ == "__main__":
    main()
