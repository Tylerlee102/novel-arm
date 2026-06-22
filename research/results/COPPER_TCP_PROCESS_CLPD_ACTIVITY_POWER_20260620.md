# COPPER TCP Process-Server CLPD Activity Power

Generated: 2026-06-20

## Scope

This report summarizes a TCP process-server-derived RTL activity power pass for the COPPER CLPD SRAM directory. The operation mix comes from the process-separated OpenSSL libssl AF_INET TCP-loopback runs inside a private user/network namespace, including scaled four-pair and eight-pair points. It is still a transaction-level replay and FPGA power proxy, not instruction-level full-system switching or ASIC-calibrated power.

## Replay Source

- Source CSV: `research/results/gem5_arm_ubuntu_fs_ossltlstcp_app/ossltlstcp_tcp_netns_process_key1_summary.csv`
- Source CSV: `research/results/gem5_arm_ubuntu_fs_ossltlstcp_app/ossltlstcp_tcp_netns_process_seed1_summary.csv`
- Source CSV: `research/results/gem5_arm_ubuntu_fs_ossltlstcp_app/ossltlstcp_tcp_netns_process_scale2_summary.csv`
- Source CSV: `research/results/gem5_arm_ubuntu_fs_ossltlstcp_app/ossltlstcp_tcp_netns_process_scale3_summary.csv`
- Source policy: `spp_copper_slack`
- Policy choice: SPP+COPPER slack gates the larger candidate stream in the TCP process-server run, so it is the conservative CLPD activity replay mix.
- Seed points: 4
- Raw driver events: 268,494
- Replay events: 268,494
- Scale factor: 1.000000000
- Pointer-like candidates in source rows: 261,979
- Prefetches issued in source rows: 2,636,271
- Useful prefetches in source rows: 410,725
- Process TCP pairs in selected rows: 14
- Child failures in selected rows: 0
- Translation faults in selected rows: 0

## Raw To Replay Counts

| Event class | Raw count | Replay count | Replay mix |
|---|---:|---:|---:|
| Learned proofs / commits | 5,293 | 5,293 | 2.0% |
| Allowed candidates / allow queries | 39,024 | 39,024 | 14.5% |
| Blocked no provenance / no-entry queries | 222,955 | 222,955 | 83.0% |
| Target witness misses / fault-permission queries | 1,222 | 1,222 | 0.5% |

## RTL Replay

- XSim result: `COPPER CLPD workload activity replay completed: source_label=tcp_process_spp_copper_slack rows=4 raw_total=268494 scaled_total=268494 commits=5293 allow=39024 block=222955 fault=1222 observed_allow=39024 observed_block=224177 no_entry=222955 word_unproven=0 stale_epoch=0 token_mismatch=0 fault_perm=1222 pending_update=0 errors=0`
- Finish time: `2748245 ns`
- SAIF file: `research\results\copper_clpd_sram_tcp_process_activity.saif` (6798821 bytes)
- CLPD configuration: 1K-entry banked SRAM directory, 32-bit line tag, 8-bit token, 8-bit epoch.

## Vivado Power Result

| Source | Mapping | Total W | Dynamic W | Static W | Confidence | Timing |
|---|---:|---:|---:|---:|---:|---|
| TCP process-server SAIF | 37%   (226/611) | 0.083 | 0.014 | 0.069 | Medium | WNS 1.807 ns |

## Component Breakdown

| Component | Power W | Used |
|---|---:|---:|
| Block RAM | 0.012 | 4 |
| LUT as Logic | <0.001 | 151 |
| Register | <0.001 | 144 |

## Mapping Audit

- SAIF manifest: `status,message,saif,report,unmatched
READ_SAIF_OK,,research/results/copper_clpd_sram_tcp_process_activity.saif,research/results/copper_clpd_sram_tcp_process_activity_saif_power.rpt,research/results/copper_clpd_sram_tcp_process_activity_saif_unmatched.txt`
- SAIF unmatched entries: 67546

## Interpretation

- This is stronger than only pJ/access accounting for the TCP process-server rows because the measured counter mix drives the RTL activity path and Vivado SAIF power flow.
- It is still not a calibrated ASIC result, not a production SoC power result, and not instruction-by-instruction full-system switching.
- The source policy is the conservative SPP+COPPER slack case for this workload because it gates the larger candidate stream.

## Source Artifacts

- Replay count builder: `research/build_copper_tcp_process_clpd_replay.py`
- RTL replay testbench: `research/copper_clpd_sram_workload_activity_tb.sv`
- XSim SAIF script: `research/copper_clpd_sram_tcp_process_activity_saif_xsim.tcl`
- XSim wrapper: `research/run_copper_clpd_sram_tcp_process_activity_xsim.ps1`
- Vivado SAIF power script: `research/run_copper_clpd_sram_tcp_process_saif_power.tcl`

status=PASS
