# COPPER Workload-Derived CLPD Activity Power

Generated: 2026-06-19

## Scope

This report summarizes a workload-derived RTL activity power pass for the COPPER CLPD SRAM directory. The driver is not an instruction-by-instruction full-system waveform; it is a transaction-level replay whose operation mix is scaled from measured gem5 full-system COPPER counters across public app/service/parser workloads. This is stronger than a random testbench SAIF, but it remains an FPGA power proxy rather than ASIC-calibrated power.

## Replay Source

- Source CSV: `research\results\copper_prefetch_traffic_overhead_20260616.csv`
- Source policy: `copper_clpd64k_peb`
- Workload rows: 20
- Raw driver events: 1,318,318
- Replay events: 120,000
- Scale factor: 0.091025079
- Pointer-like candidates in source rows: 1,265,236
- Prefetches issued in source rows: 704,430
- Boundary authority entries dropped in source rows: 366,140

## Raw To Replay Counts

| Event class | Raw count | Replay count | Replay mix |
|---|---:|---:|---:|
| Learned proofs / commits | 34,131 | 3,107 | 2.6% |
| Allowed candidates / allow queries | 723,381 | 65,846 | 54.9% |
| Blocked no provenance / no-entry queries | 541,855 | 49,322 | 41.1% |
| Target witness misses / fault-permission queries | 18,951 | 1,725 | 1.4% |

## RTL Replay

- XSim result: `COPPER CLPD workload activity replay completed: source_label=app_service_copper_clpd64k_peb rows=20 raw_total=1318318 scaled_total=120000 commits=3107 allow=65846 block=49322 fault=1725 observed_allow=65846 observed_block=51047 no_entry=49322 word_unproven=0 stale_epoch=0 token_mismatch=0 fault_perm=1725 pending_update=0 errors=0`
- Finish time: `1241445 ns`
- SAIF file: `research\results\copper_clpd_sram_workload_activity.saif` (6680592 bytes)
- CLPD configuration: 1K-entry banked SRAM directory, 32-bit line tag, 8-bit token, 8-bit epoch.
- Replay discipline: commits install proven words; allow/fault queries are selected from live scoreboard proofs; no-provenance queries intentionally miss source provenance.

## Vivado Power Result

| Source | Mapping | Total W | Dynamic W | Static W | Confidence | Timing |
|---|---:|---:|---:|---:|---:|---|
| Workload-derived SAIF | 37%   (226/611) | 0.083 | 0.014 | 0.069 | Medium | WNS 1.807 ns |

## Component Breakdown

| Component | Power W | Used |
|---|---:|---:|
| Block RAM | 0.012 | 4 |
| LUT as Logic | <0.001 | 151 |
| Register | <0.001 | 144 |

## Mapping Audit

- SAIF manifest: `status,message,saif,report,unmatched
READ_SAIF_OK,,research/results/copper_clpd_sram_workload_activity.saif,research/results/copper_clpd_sram_workload_activity_saif_power.rpt,research/results/copper_clpd_sram_workload_activity_saif_unmatched.txt`
- SAIF unmatched entries: 67546

The key evidence improvement is that the CLPD switching data is now tied to measured full-system COPPER event ratios, not just synthetic directed/random activity. It still does not prove final silicon power or a production integrated SoC timing point. It does, however, make the metadata-energy claim more defensible because the same measured workload portfolio now feeds both the performance counters and the RTL activity estimate.

## Source Artifacts

- Replay count builder: `research/build_copper_workload_clpd_replay.py`
- RTL replay testbench: `research/copper_clpd_sram_workload_activity_tb.sv`
- XSim SAIF script: `research/copper_clpd_sram_workload_activity_saif_xsim.tcl`
- XSim wrapper: `research/run_copper_clpd_sram_workload_activity_xsim.ps1`
- Vivado SAIF power script: `research/run_copper_clpd_sram_workload_saif_power.tcl`
