# COPPER Stronger-Claim Evidence Blockers

This file records the stronger-claim tier separately from the scoped artifact
claim. It is intentionally conservative: the current repository supports
PicoRV32 tiny-SoC mapped FPGA evidence, FPGA/tool power estimates, proxy energy
rows, gem5 ARM-system summary evidence, and RTL contract blocks. It does not
support silicon, foundry signoff, production ARM/OoO integration, measured
silicon power, or SOTA silicon-efficiency claims.

| Claim tier | Status | Current strongest evidence | Missing evidence before claim is allowed |
| --- | --- | --- | --- |
| Scoped ASIC/OpenROAD tool estimates | PARTIAL | Archived/imported core-wrapper Nangate45 OpenROAD/ASIC-Liberty rows may exist; current top-level `openroad_postroute_power.csv` and `asic_power.csv` are BLOCKED in this workspace. | Current PASS rows, full-core ASIC post-route rows, OpenROAD/OpenSTA availability, complete report paths, and clear non-signoff labels. |
| Fabricated chip, tapeout, or post-silicon validation | BLOCKED | No tapeout, shuttle, foundry, package, die, bring-up, or measured-chip artifacts found. | `fabricated_silicon_manifest.csv` with PASS rows for final GDS/OAS, clean DRC/LVS/antenna, shuttle/foundry acceptance, fabrication lot, package/board record, photos, and bring-up log. |
| ASIC or foundry signoff | BLOCKED | OpenROAD/ASIC-Liberty flows are tool estimates when PASS; they are not foundry signoff. | `asic_signoff_manifest.csv` with PASS signoff-grade timing, area, power, DRC, LVS, antenna/ERC/PEX, multi-corner STA, extracted parasitics, PDK/library/RC-corner manifest, and hashes. |
| Measured silicon power | BLOCKED | `power_report_index.csv` currently promotes FPGA/tool and proxy rows only; `silicon_measured=no`. | `power_report_index.csv` PASS row with `measurement_type=measured_silicon`, `silicon_measured=yes`, positive `power_mw`, raw rail logs, calibration manifest, board/chip ID, workload window markers, and analysis script. |
| Production ARM/OoO integration | BLOCKED | gem5 ARM-system prefetcher-path evidence, PicoRV32 tiny-SoC RTL, and RTL contract/interface blocks. | `production_arm_integration.csv` with PASS artifacts for OoO LSQ binding, TLB/MMU, caches, coherence, interrupts, exceptions, DMA/I/O, memory-system backpressure, replay/squash, context switches, and adversarial full-system tests. |
| SOTA silicon efficiency or SOTA power comparison | BLOCKED | Fair FPGA/tool/proxy comparison frame only; no comparable COPPER silicon/signoff number. | Requires PASS rows in the SOTA comparison manifest where COPPER and prior work use the same ASIC signoff or measured-silicon basis, normalized metric, primary source, and artifact path. |

## Blocked Tapeout And Fabrication Plan

1. Freeze RTL, constraints, and a top-level SoC target with documented memories,
   clocks, reset, test access, and I/O.
2. Run an ASIC physical-design flow that emits final netlist, DEF, SPEF, SDF,
   reports, and final GDS/OAS with reproducible scripts and tool versions.
3. Run signoff checks for DRC, LVS, antenna/ERC, extracted multi-corner STA, and
   activity-backed power. Archive all reports with hashes.
4. Submit through a named shuttle/foundry path and archive the accepted design
   name, run identifier, date, receipt, and process/PDK version.
5. Archive package/assembly records, board files, firmware, lab notebook,
   photos, bring-up logs, raw measurements, and summarized results.

## Blocked Measurement Plan

1. Build matched baseline and COPPER images for the same board/chip, clock,
   constraints, workload, firmware, and tool version.
2. Instrument core and relevant auxiliary rails with calibrated equipment such
   as SMU, power analyzer, Joulescope, Monsoon, PMBus/INA readings validated by
   an external meter, or equivalent lab gear.
3. Record idle, warmup, ROI start, ROI end, cooldown, trigger state,
   temperature, board/chip ID, instrument serial, and calibration date.
4. Save raw timestamped CSVs for voltage, current, power, trigger state, and
   workload metadata. Keep baseline and COPPER raw logs separate.
5. Analyze per-rail and total energy over matched ROI windows with idle/static
   subtraction, repetitions, confidence intervals, and an immutable manifest.

## Fair Comparison Frame

Use two tables rather than blending unlike evidence.

| Table | Allowed measurement classes | Required columns |
| --- | --- | --- |
| FPGA/tool/proxy estimates | `fpga_mapped_ppa`, `fpga_tool_power`, `openroad_postroute_tool_estimate`, `asic_liberty_tool_estimate`, `mcpat_proxy`, `metadata_toggle_bound`, `gem5_full_system` | work, scope, target, flow, metric, value, unit, delta, evidence path, allowed claim, forbidden claim |
| ASIC signoff and silicon | `asic_signoff`, `silicon_measured` only | work, process, voltage, frequency, temperature, metric, value, unit, signoff grade, silicon measured, source, evidence path |

Do not rank FPGA/tool/proxy rows against measured-silicon or signoff rows as if
they were the same evidence class.
