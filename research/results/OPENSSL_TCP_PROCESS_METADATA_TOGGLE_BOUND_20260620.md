# OpenSSL TCP Process-Server Metadata Toggle Bound

Date: 2026-06-20

Purpose: bound COPPER metadata-table activity for the OpenSSL libssl TCP process-server workload, including the scaled process-pair point. This is a pJ/access sensitivity check over measured AArch64 full-system counters, not calibrated ASIC power, SRAM compiler power, or an instruction-by-instruction switching trace.

## Inputs

- Source CSV: `research/results/gem5_arm_ubuntu_fs_ossltlstcp_app/ossltlstcp_tcp_netns_process_key1_summary.csv`
- Source CSV: `research/results/gem5_arm_ubuntu_fs_ossltlstcp_app/ossltlstcp_tcp_netns_process_seed1_summary.csv`
- Source CSV: `research/results/gem5_arm_ubuntu_fs_ossltlstcp_app/ossltlstcp_tcp_netns_process_scale2_summary.csv`
- Source CSV: `research/results/gem5_arm_ubuntu_fs_ossltlstcp_app/ossltlstcp_tcp_netns_process_scale3_summary.csv`
- Selected policies: copper_clpd64k_peb, spp_copper_slack
- Selected policy rows: 8
- All selected rows use `tcp_loopback_netns_process`: yes.
- All selected rows have `process_server=1`: yes.
- Child process failures across selected rows: 0.
- Translation faults across selected rows: 0.
- Matching gem5 DRAM rank-energy rows: found for every selected seed/policy row.

## Counter Totals

| Policy | Seed points | Process pairs | Pointer-like candidates | Prefetches issued | Useful prefetches | Metadata reads | Metadata writes | Metadata events | DRAM op energy | Total DRAM energy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| copper_clpd64k_peb | 4 | 14 | 170,564 | 50,821 | 12,063 | 171,881 | 7,462 | 179,343 | 3739.698 uJ | 139.535 mJ |
| spp_copper_slack | 4 | 14 | 261,979 | 2,636,271 | 410,725 | 263,201 | 5,293 | 268,494 | 4514.881 uJ | 125.973 mJ |

## Sensitivity Table

| Policy | Scenario | Read pJ | Write pJ | Compare pJ/event | Metadata energy | Metadata / DRAM op | Metadata / total DRAM |
|---|---|---:|---:|---:|---:|---:|---:|
| copper_clpd64k_peb | low | 1.0 | 2.0 | 0.2 | 0.223 uJ | 0.0060% | 0.000160% |
| copper_clpd64k_peb | mid | 5.0 | 10.0 | 1.0 | 1.113 uJ | 0.0298% | 0.000798% |
| copper_clpd64k_peb | high | 20.0 | 40.0 | 5.0 | 4.633 uJ | 0.1239% | 0.003320% |
| spp_copper_slack | low | 1.0 | 2.0 | 0.2 | 0.327 uJ | 0.0073% | 0.000260% |
| spp_copper_slack | mid | 5.0 | 10.0 | 1.0 | 1.637 uJ | 0.0363% | 0.001300% |
| spp_copper_slack | high | 20.0 | 40.0 | 5.0 | 6.818 uJ | 0.1510% | 0.005412% |

## Interpretation

- The deliberately high scenario remains below 6.818 uJ across the selected process-server points for either policy.
- In the same high scenario, the maximum normalized metadata bound is 0.1510% of matching DRAM operation energy and 0.005412% of matching total DRAM energy.
- Standalone COPPER has fewer metadata events than SPP+COPPER slack on this workload because the slack path gates a larger SPP candidate stream.
- This supports a narrow side-effect claim: the process-separated TCP evidence does not create a large metadata-access-energy signal under these assumptions.
- This does not prove full-chip power, wire energy, SRAM-compiler energy, or production TCP/TLS behavior.

CSV: `research/results/openssl_tcp_process_metadata_toggle_bound_20260620.csv`

status=PASS
