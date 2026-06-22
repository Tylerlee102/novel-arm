# COPPER RTL Power Proxy

Generated: 2026-06-18

## Scope

This report summarizes Vivado 2025.2 `report_power` results over existing COPPER RTL checkpoints. The estimates are FPGA/vectorless power proxies, not calibrated ASIC power. They are useful for bounding metadata-block implementation plausibility and for exposing whether COPPER's proposed proof tables are dominated by storage, logic, or clocking.

## Key Results

- Checkpoints attempted: 15
- Successful reports: 15
- Routed reports: 1
- Routed 64K-entry CLPD on xc7a200t: 0.479 W total, 0.344 W dynamic, 0.135 W static, 260 block-RAM tiles, 636 LUT-as-logic, confidence Medium.
- Synthesized full LSQ/AMBA authority top: 0.118 W total, 0.047 W dynamic, 4692 LUT-as-logic, 3547 registers, confidence Low.
- PEB epoch-boundary block: 0.089 W total, 0.019 W dynamic, 346 LUT-as-logic, 147 registers, confidence Low.

## Summary Table

| Design | State | Device | Conf. | Total W | Dynamic W | Static W | LUTs | Regs | BRAM Tiles | I/O artifact |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| copper_clpd_sram_dir_clpd1k_synth | synthesized | xc7a35tcpg236-1 | Low | 0.089 | 0.018 | 0.070 | 191 | 144 | 4 | False |
| copper_clpd_sram_dir_clpd2k_synth | synthesized | xc7a35tcpg236-1 | Low | 0.101 | 0.030 | 0.071 | 198 | 146 | 8 | False |
| copper_clpd_sram_dir_clpd4k_synth | synthesized | xc7a35tcpg236-1 | Low | 0.121 | 0.050 | 0.071 | 200 | 148 | 15 | False |
| copper_clpd_sram_dir_clpd8k_synth | synthesized | xc7a35tcpg236-1 | Low | 0.174 | 0.102 | 0.072 | 229 | 150 | 33 | False |
| copper_clpd_sram_dir_clpd16k_a200t_synth | synthesized | xc7a200tfbg676-2 | Low | 0.326 | 0.191 | 0.134 | 283 | 152 | 65 | False |
| copper_clpd_sram_dir_clpd64k_a200t_synth | synthesized | xc7a200tfbg676-2 | Low | 0.882 | 0.737 | 0.145 | 629 | 156 | 260 | False |
| copper_clpd_sram_dir_clpd64k_a200t_impl | routed | xc7a200tfbg676-2 | Medium | 0.479 | 0.344 | 0.135 | 636 | 170 | 260 | False |
| copper_peb_synth | synthesized | xc7a35tcpg236-1 | Low | 0.089 | 0.019 | 0.070 | 346 | 147 |  | True |
| copper_tlb_coherence_authority_filter_synth | synthesized | xc7a35tcpg236-1 | Low | 0.089 | 0.019 | 0.070 | 332 | 167 |  | True |
| copper_lsq_source_tag_tracker_synth | synthesized | xc7a35tcpg236-1 | Low | 0.087 | 0.017 | 0.070 | 217 | 312 |  | True |
| copper_lsq_cepf_line_e2e_top_synth | synthesized | xc7a35tcpg236-1 | Low | 0.092 | 0.022 | 0.070 | 1960 | 1336 |  | False |
| copper_amba_sari_frontdoor_synth | synthesized | xc7a35tcpg236-1 | Low | 20.835 | 20.351 | 0.485 | 7 |  |  | True |
| copper_amba_sari_frontdoor_regslice_synth | synthesized | xc7a35tcpg236-1 | Low | 0.094 | 0.024 | 0.070 | 8 | 160 |  | True |
| copper_amba_sari_authority_bridge_top_synth | synthesized | xc7a35tcpg236-1 | Low | 0.115 | 0.045 | 0.070 | 4106 | 3130 |  | False |
| copper_full_lsq_amba_authority_top_synth | synthesized | xc7a35tcpg236-1 | Low | 0.118 | 0.047 | 0.070 | 4692 | 3547 |  | False |

## CLPD Scaling

| CLPD Entries | Design | State | Total W | Dynamic W | Block RAM W | BRAM Tiles | LUTs |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1024 | copper_clpd_sram_dir_clpd1k_synth | synthesized | 0.089 | 0.018 | 0.013 | 4 | 191 |
| 2048 | copper_clpd_sram_dir_clpd2k_synth | synthesized | 0.101 | 0.030 | 0.024 | 8 | 198 |
| 4096 | copper_clpd_sram_dir_clpd4k_synth | synthesized | 0.121 | 0.050 | 0.044 | 15 | 200 |
| 8192 | copper_clpd_sram_dir_clpd8k_synth | synthesized | 0.174 | 0.102 | 0.095 | 33 | 229 |
| 16384 | copper_clpd_sram_dir_clpd16k_a200t_synth | synthesized | 0.326 | 0.191 | 0.183 | 65 | 283 |
| 65536 | copper_clpd_sram_dir_clpd64k_a200t_impl | routed | 0.479 | 0.344 | 0.313 | 260 | 636 |
| 65536 | copper_clpd_sram_dir_clpd64k_a200t_synth | synthesized | 0.882 | 0.737 | 0.719 | 260 | 629 |

## Interpretation

The routed 64K-entry CLPD is storage-dominated on FPGA: block RAM accounts for 0.313 W of the 0.344 W dynamic report, while LUT logic is only 0.001 W and signals 0.026 W. That is a useful architectural datapoint: COPPER's largest metadata structure behaves like a cache-adjacent SRAM table rather than a large logic fabric. The smaller synthesized control blocks are logic-light, but their absolute power has low confidence until placed/routed and driven by simulation activity.

## Caveats

- Vivado used vectorless activity propagation; no workload SAIF/VCD was supplied.
- Most non-CLPD blocks are synthesized-only checkpoints, so their confidence is low.
- The routed CLPD report is FPGA-specific and cannot be used as calibrated ASIC power.
- The tiny `copper_amba_sari_frontdoor_synth` datapoint is I/O-dominated in out-of-context Vivado reporting; it is retained for auditability but should not be used as an architectural power claim.
- This closes a reporting gap by measuring COPPER RTL metadata structures directly, but a top-tier submission still needs workload-derived switching or ASIC-style energy modeling.

## Source Artifacts

- CSV: `research\results\copper_rtl_power_proxy_20260618.csv`
- Vivado script: `research/run_copper_rtl_power_proxy.tcl`
- Manifest: `research\results\copper_rtl_power_proxy_manifest_20260618.csv`
