# COPPER CLPD Activity Power

Generated: 2026-06-19

## Scope

This report summarizes a simulation-activity power pass for the COPPER CLPD SRAM directory. The activity source is the existing XSim CLPD SRAM testbench, not a full-system workload. The matched synthesis configuration is the testbench-scale 64-entry CLPD, not the 64K-entry routed CLPD.

## Testbench Activity

- XSim result: `COPPER CLPD SRAM directory tests completed: directed=18 random=4000 allowed=3 blocked=4011 no_entry=3970 word_unproven=5 stale_epoch=30 token=2 fault_perm=2 pending_update=2 merge=1 replace=2629 purge_match=17 purge_alias=887 errors=0`
- Finish time: `120916 ns`
- SAIF file: `research\results\copper_clpd_sram_dir_activity.saif` (285984 bytes)
- VCD file: `research\results\copper_clpd_sram_dir_activity.vcd` (2556797 bytes)
- Activity shape: directed proof/hazard cases plus 4,000 randomized commit/purge/query operations.

## Power Results

| Source | Mapping | Total W | Dynamic W | Static W | Confidence | Timing |
|---|---:|---:|---:|---:|---:|---|
| VCD | 0%   (1/342) | 0.075 | 0.007 | 0.069 | Medium | routed fallback |
| SAIF | 37%   (126/342) | 0.076 | 0.007 | 0.069 | Medium | WNS 2.208 ns, constraints met |

## SAIF Component Breakdown

| Component | Power W | Used |
|---|---:|---:|
| Block RAM | 0.005 | 2 |
| LUT as Logic | <0.001 | 95 |
| Register | <0.001 | 76 |

## Mapping Audit

- SAIF manifest: `status,message,dcp,saif,report,unmatched
READ_SAIF_OK,,research/results/copper_clpd_sram_dir_activity_impl.dcp,research/results/copper_clpd_sram_dir_activity.saif,research/results/copper_clpd_sram_dir_activity_saif_power.rpt,research/results/copper_clpd_sram_dir_activity_saif_unmatched.txt`
- VCD manifest: `activity_status,activity_message,vcd,report
READ_VCD_OK,,research/results/copper_clpd_sram_dir_activity.vcd,research/results/copper_clpd_sram_dir_activity_power.rpt`
- SAIF unmatched entries: 3089
- VCD unmatched entries: 657

The SAIF path is the useful activity result: Vivado matched 126 of 342 design nets, or 37%. The VCD path is retained as a negative control: Vivado read it, but matched only 1 of 342 nets. The SAIF unmatched list is dominated by `entry_mem[...]` bits because synthesis maps the unpacked RTL array into RAM primitives; remaining unmatched nodes are filled by Vivado's probabilistic activity model.

## Interpretation

Under the directed/random CLPD activity source, the routed 64-entry CLPD reports 0.076 W total on-chip FPGA power, 0.007 W dynamic, and 0.069 W static with medium confidence. The datapoint is useful because it proves the local tool flow can carry simulation activity into a routed COPPER metadata block. It does not replace the 64K vectorless CLPD result, and it is not a calibrated ASIC or workload-derived full-system power result.

## Source Artifacts

- XSim VCD script: `research/copper_clpd_sram_activity_xsim.tcl`
- XSim SAIF script: `research/copper_clpd_sram_activity_saif_xsim.tcl`
- Activity XSim wrapper: `research/run_copper_clpd_sram_activity_xsim.ps1`
- Vivado matched-design power script: `research/run_copper_clpd_sram_activity_power.tcl`
- Vivado SAIF-from-DCP power script: `research/run_copper_clpd_sram_saif_power_from_dcp.tcl`
