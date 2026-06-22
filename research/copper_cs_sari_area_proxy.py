#!/usr/bin/env python3
"""Structural cost proxy for SARI versus conflict-scoped SARI.

Vivado XSIM can run in the local environment, but Vivado batch synthesis fails
before synth_design during Tcl app initialization. This script provides a
transparent fallback: count retained state bits and compare-bit slices implied
by the RTL parameters. These are not FPGA LUT counts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import math


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research" / "results" / "cs_sari_area_proxy"
CSV_OUT = OUT_DIR / "cs_sari_area_proxy.csv"
MD_OUT = OUT_DIR / "CS_SARI_AREA_PROXY.md"


@dataclass(frozen=True)
class Config:
    name: str
    src_line_w: int
    tgt_line_w: int
    token_w: int
    depth: int
    count_w: int


def ceil_log2(value: int) -> int:
    return 0 if value <= 1 else math.ceil(math.log2(value))


def estimate(config: Config) -> dict[str, int | str]:
    queue_bits = config.depth * config.src_line_w
    state_bits = queue_bits + config.count_w + 1

    global_compare_bits = 0
    scoped_queue_cam_bits = config.depth * config.src_line_w
    scoped_incoming_source_bits = 3 * config.src_line_w
    scoped_remap_bits = config.tgt_line_w + config.token_w
    scoped_tlbi_bits = config.token_w
    scoped_compare_bits = (
        scoped_queue_cam_bits
        + scoped_incoming_source_bits
        + scoped_remap_bits
        + scoped_tlbi_bits
    )

    source_conflict_terms = config.depth + 3
    source_cmp_depth = ceil_log2(config.src_line_w) + ceil_log2(source_conflict_terms)
    remap_cmp_depth = ceil_log2(config.tgt_line_w + config.token_w)
    tlbi_cmp_depth = ceil_log2(config.token_w)
    target_or_depth = max(remap_cmp_depth, tlbi_cmp_depth) + 2
    scoped_hold_depth = max(source_cmp_depth, target_or_depth) + 2
    global_hold_depth = ceil_log2(5) + 1

    return {
        "config": config.name,
        "src_line_w": config.src_line_w,
        "tgt_line_w": config.tgt_line_w,
        "token_w": config.token_w,
        "depth": config.depth,
        "state_bits_global": state_bits,
        "state_bits_scoped": state_bits,
        "extra_state_bits": 0,
        "global_compare_bits": global_compare_bits,
        "scoped_compare_bits": scoped_compare_bits,
        "extra_compare_bits": scoped_compare_bits - global_compare_bits,
        "queue_cam_compare_bits": scoped_queue_cam_bits,
        "incoming_source_compare_bits": scoped_incoming_source_bits,
        "target_compare_bits": scoped_remap_bits + scoped_tlbi_bits,
        "global_hold_depth_proxy": global_hold_depth,
        "scoped_hold_depth_proxy": scoped_hold_depth,
        "extra_depth_proxy": scoped_hold_depth - global_hold_depth,
    }


def main() -> None:
    configs = [
        Config("xsim_tb", src_line_w=8, tgt_line_w=12, token_w=4, depth=8, count_w=4),
        Config("l1_line_tag_32b_pa", src_line_w=26, tgt_line_w=26, token_w=12, depth=8, count_w=4),
        Config("l1_line_tag_48b_pa", src_line_w=42, tgt_line_w=42, token_w=16, depth=8, count_w=4),
        Config("deeper_queue_48b_pa", src_line_w=42, tgt_line_w=42, token_w=16, depth=16, count_w=5),
    ]
    rows = [estimate(config) for config in configs]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# CS-SARI Structural Cost Proxy",
        "",
        "Date: 2026-06-12",
        "",
        "Vivado batch synthesis for CS-SARI was attempted but did not reach",
        "`synth_design` because Vivado failed during Tcl app initialization.",
        "This file therefore reports a structural proxy, not FPGA LUT/timing",
        "numbers.",
        "",
        "| Config | Source line bits | Target line bits | Token bits | Queue depth | State bits global | State bits scoped | Extra state bits | Extra compare bits | Queue CAM bits | Source-event compare bits | Target compare bits | Global depth proxy | Scoped depth proxy | Extra depth proxy |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {config} | {src_line_w} | {tgt_line_w} | {token_w} | {depth} | {state_bits_global} | {state_bits_scoped} | {extra_state_bits} | {extra_compare_bits} | {queue_cam_compare_bits} | {incoming_source_compare_bits} | {target_compare_bits} | {global_hold_depth_proxy} | {scoped_hold_depth_proxy} | {extra_depth_proxy} |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "Interpretation: CS-SARI adds no retained state versus SARI for the",
            "same queue depth. Its cost is a shallow candidate-conflict CAM over",
            "the pending source-revocation queue plus incoming source/target",
            "comparators. In an ARM-ish 48-bit physical-address line-tag point",
            "with depth 8, the proxy is 0 extra state bits and 536 compare-bit",
            "slices. The expected timing concern is the queue CAM reduction into",
            "the DMP issue-valid gate; a production design would pipeline or bank",
            "this if the prefetch issue stage is already timing-critical.",
            "",
        ]
    )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(MD_OUT)
    print(CSV_OUT)


if __name__ == "__main__":
    main()
