# COPPER Synchronized Hardware Evidence Report

## Status

SUBMISSION-READY

## Main Result

The synchronized evidence pass supports a constrained COPPER artifact/mechanism submission. It includes scoped PicoRV32 tiny-SoC full-core mapped FPGA PPA, matched overhead, FPGA tool-estimated power where indexed, passing paper/claim audits, and a packaged artifact. It does not support production ARM/OoO integration, ASIC/foundry signoff, measured silicon power, or state-of-the-art claims.

## Commands Run

- `make fullcore-synth`
- `make mapped-ppa`
- `make power-evidence`
- `make sync-hardware-evidence`
- `make paper`
- `make paper-audit`
- `make artifact`
- GitHub Actions `COPPER Reproduction` parallel lanes: `full-readiness`, `fullcore-synth`, `mapped-ppa`, `power-evidence`, and `sync-docs-audit-package`.

## Lane A Full-Core/Core-Wrapper PPA

| scope | design | target | flow | environment | status | report_path |
| --- | --- | --- | --- | --- | --- | --- |
| full_core | full_core_baseline | picorv32_tiny_soc | yosys | local_windows | PASS | research/results/logs/fullcore_synthesis/full_core_baseline.log |
| full_core | full_core_plus_copper | picorv32_tiny_soc | yosys | local_windows | PASS | research/results/logs/fullcore_synthesis/full_core_plus_copper.log |
| accepted_core_wrapper | baseline_core_wrapper | picorv32_core_wrapper | yosys | local_windows | PASS | research/results/logs/fullcore_synthesis/baseline_core_wrapper.log |
| accepted_core_wrapper | core_wrapper_plus_baseline_prefetch | picorv32_core_wrapper | yosys | local_windows | PASS | research/results/logs/fullcore_synthesis/core_wrapper_plus_baseline_prefetch.log |
| accepted_core_wrapper | core_wrapper_plus_copper | picorv32_core_wrapper | yosys | local_windows | PASS | research/results/logs/fullcore_synthesis/core_wrapper_plus_copper.log |

## Lane B Mapped Timing/Area/Power

| scope | design | target | flow | environment | status | fmax_mhz | wns | tns | power_mw | report_path |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_core | full_core_baseline | vivado-xc7a35tcsg324-1 | vivado-impl | local_windows | PASS | 93.318 | 9.284 | 0.000 | 88.000 | research/results/logs/vivado/full_core_baseline.log |
| full_core | full_core_plus_copper | vivado-xc7a35tcsg324-1 | vivado-impl | local_windows | PASS | 99.950 | 9.995 | 0.000 | 87.000 | research/results/logs/vivado/full_core_plus_copper.log |
| accepted_core_wrapper | baseline_core_wrapper | vivado-xc7a35tcsg324-1 | vivado-impl | local_windows | PASS | 231.321 | 15.677 | 0.000 | 74.000 | research/results/logs/vivado/baseline_core_wrapper.log |
| accepted_core_wrapper | core_wrapper_plus_baseline_prefetch | vivado-xc7a35tcsg324-1 | vivado-impl | local_windows | PASS | 237.248 | 15.785 | 0.000 | 78.000 | research/results/logs/vivado/core_wrapper_plus_baseline_prefetch.log |
| accepted_core_wrapper | core_wrapper_plus_copper | vivado-xc7a35tcsg324-1 | vivado-impl | local_windows | PASS | 102.386 | 10.233 | 0.000 | 76.000 | research/results/logs/vivado/core_wrapper_plus_copper.log |
| full_core | full_core_baseline | ecp5-85k | yosys+nextpnr-ecp5 | local_windows | PASS | 73.59 | NA | NA | NA | research/results/logs/mapped_ppa/ecp5_full_core_baseline.log |
| full_core | full_core_plus_copper | ecp5-85k | yosys+nextpnr-ecp5 | local_windows | PASS | 65.92 | NA | NA | NA | research/results/logs/mapped_ppa/ecp5_full_core_plus_copper.log |
| accepted_core_wrapper | baseline_core_wrapper | ecp5-85k | yosys+nextpnr-ecp5 | local_windows | PASS | 227.63 | NA | NA | NA | research/results/logs/mapped_ppa/ecp5_baseline_core_wrapper.log |

## Lane C Power Classification

| scope | design | target | measurement_type | available | power_mw | full_core | signoff_grade | silicon_measured | report_path |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_core | full_core_plus_copper | vivado-xc7a35tcsg324-1 | fpga_tool_estimate | yes | 87.000 | yes | no | no | research/results/logs/vivado/full_core_plus_copper.log |
| unit | mcpat_activity_proxy | unit_proxy | activity_proxy | yes | NA | no | no | no | research/results/COPPER_MCPAT_SENSITIVITY_20260618.md |
| unit | proxy_assumed_memory_energy | memory_traffic_proxy_v1 | memory_energy_proxy | yes | NA | no | no | no | research/results/energy_proxy.csv |

## Sync Gate Status

| Gate | Status | Blocker | Observed evidence |
| --- | --- | --- | --- |
| schema_integrity | PASS |  | all checked ledgers have required columns |
| accepted_or_full_mapped_timing | PASS |  | mapped_full_core_full_core_plus_copper_vivado_xc7a35tcsg324_1_vivado_impl_local_windows |
| matched_overhead | PASS |  | mapped_overhead_full_core_lut_vivado_xc7a35tcsg324_1_vivado_impl_full_core_baseline_full_core_plus_copper_local_windows |
| power_evidence | PASS |  | fpga_tool_estimate |
| full_core_absent | PASS |  | mapped_full_core_full_core_plus_copper_vivado_xc7a35tcsg324_1_vivado_impl_local_windows |
| silicon_signoff_power_absent | BLOCKER | silicon/signoff power absent | none |
| paper_audits_artifact | PASS |  | paper=PASS; audit=PASS; artifact=PASS |
| overall_status | SUBMISSION-READY | production/full-system full-core and silicon/signoff blockers remain for stronger claims | SUBMISSION-READY |

## Paper/Audit/Artifact Status

- Paper/audit/artifact gate: PASS
- Claim audit, number audit, and TODO audit must all remain PASS before release.
- Artifact package is generated by `make artifact` and checked by `sync_hardware_evidence.py`.

## Claims Allowed Now

| C1 | COPPER tracks committed pointer provenance. | ALLOWED | research/results/model_tests.csv; research/copper_prefetch_unit_open.sv | model; rtl-unit only when GitHub Actions/Codespaces/Docker rtl_compile.csv and rtl_simulation.csv are PASS | Allowed for the executable model; RTL wording requires open-environment PASS rows. |
| C2 | COPPER issues prefetches based on committed provenance rather than arbitrary speculation. | ALLOWED | research/results/model_tests.csv; research/results/rtl_simulation.csv | model; rtl-unit only when GitHub Actions/Codespaces/Docker rtl_simulation.csv is PASS | Do not extend to a production core without integration evidence. |
| C3 | COPPER improves prefetch usefulness on exact measured model, cycle-model, core-integrated, independent-sim, or gem5 workloads where generated rows show improvement. | ALLOWED | research/results/prefetch_metrics.csv; research/results/cycle_prefetch_metrics.csv; research/results/core_integrated_prefetch_metrics.csv; research/results/independent_sim_prefetch_metrics.csv; research/results/gem5_prefetch_metrics.csv | model; cycle_model; core_integrated; independent_sim; gem5_full_system when PASS | Allowed only per generated row; current gem5 scope is 178 validated gem5 ARM-system PASS rows across 11 benchmark families and 29 benchmark/input groups, including 56 COPPER-family rows; raw rerun scope is 661 local raw gem5 full-system rerun rows across 155 tags and policies ampm, bop, copper, copper_clpd16k, copper_clpd32k, copper_clpd64k, copper_clpd64k_peb, copper_clpd64k_rerun, copper_clpd8k, copper_ctlw, copper_ctlw_terminal, copper_ctw, copper_exact131k, copper_exact16k, copper_proof131k, copper_tpw, dcpt, indirect, isb, naive, none, none_retry, spp, spp_copper, spp_copper_slack, stride, not a fresh clone-local rerun of every raw simulation. |
| C4 | COPPER reports accuracy, coverage, lateness, queue drops, and traffic overhead versus shared baselines. | ALLOWED | research/results/prefetch_metrics.csv; research/results/memory_traffic.csv; research/results/cycle_prefetch_metrics.csv; research/results/cycle_memory_traffic.csv; research/results/core_integrated_prefetch_metrics.csv; research/results/core_integrated_memory_traffic.csv; research/results/independent_sim_prefetch_metrics.csv; research/results/independent_sim_memory_traffic.csv | model; cycle_model; core_integrated; independent_sim | Use per-workload language and report where overhead increases. |
| C5 | COPPER improves performance/speedup on exact measured workloads where performance CSVs show speedup. | ALLOWED | research/results/performance.csv; research/results/cycle_performance.csv; research/results/core_integrated_performance.csv; research/results/independent_sim_performance.csv | model; cycle_model; core_integrated; independent_sim | Do not claim universal speedup or superiority over every baseline. |
| C6 | COPPER avoids architectural output changes in the executable model. | ALLOWED | research/results/model_tests.csv; research/results/seed_stability.csv; research/results/rtl_simulation.csv | model; rtl-unit only when GitHub Actions/Codespaces/Docker rtl_simulation.csv is PASS | Checksum equality is model-level, and RTL smoke coverage is unit-level, not a formal ISA proof. |
| C7 | COPPER has matched unit-level generic-synthesis overhead. | ALLOWED | research/results/synthesis.csv; research/results/synthesis_overhead.csv | unit synthesis | Allowed only if an open-environment Yosys flow produced matched overhead rows; not full-core overhead. |
| C8 | COPPER has matched near-core-stub generic-synthesis overhead. | ALLOWED | research/results/fullcore_synthesis.csv; research/results/fullcore_synthesis_overhead.csv | near_core_stub | Allowed only when scope is called near_core_stub; not full-core overhead or mapped timing. |
| C9 | COPPER generalizes across the evaluated model, cycle-model, core-integrated, and independent-sim workload suite. | ALLOWED | research/results/benchmark_inventory.csv; research/results/cycle_performance.csv; research/results/core_integrated_performance.csv; research/results/independent_sim_performance.csv; research/results/statistical_summary.csv | model; cycle_model; core_integrated; independent_sim | Breadth is still not a gem5 campaign or production-core result. |
| C10 | COPPER has scoped OpenROAD post-route, ASIC-Liberty/FPGA tool-power, and proxy/model energy results where indexed PASS. | ALLOWED | research/results/openroad_postroute_power.csv; research/results/openroad_postroute_power_overhead.csv; research/results/asic_power.csv; research/results/asic_power_overhead.csv; research/results/energy_proxy.csv; research/results/energy_summary.csv; research/results/power_report_index.csv; research/results/mapped_ppa.csv; research/results/copper_mcpat_sensitivity_20260618.csv | fpga_tool_estimate; proxy_activity; proxy_assumed_memory_energy | Vivado report_power is tool-estimated FPGA power for the mapped target; do not call it silicon measurement or ASIC signoff. |
| C12 | COPPER has matched near-core-stub mapped timing. | ALLOWED | research/results/mapped_ppa.csv; research/results/mapped_ppa_overhead.csv | near_core_stub mapped PPA | Allowed only when baseline and COPPER near-core-stub rows PASS in the same mapped flow with timing fields from nextpnr, Vivado, or OpenROAD; not full-core PPA. |
| C13 | COPPER has matched PicoRV32 accepted core-wrapper mapped FPGA PPA. | ALLOWED | research/results/mapped_ppa.csv; research/results/mapped_ppa_overhead.csv | accepted_core_wrapper mapped PPA | Allowed only when baseline and COPPER PicoRV32 accepted-core-wrapper rows PASS in the same mapped flow with timing fields from nextpnr, Vivado, or OpenROAD; not full-core, ARM-core, ASIC, or silicon PPA. |
| C14 | COPPER has matched PicoRV32 accepted core-wrapper generic-synthesis overhead. | ALLOWED | research/results/fullcore_synthesis.csv; research/results/fullcore_synthesis_overhead.csv | accepted_core_wrapper | Allowed only when scope is called accepted_core_wrapper; not full-core overhead or ASIC timing. |
| C15 | COPPER has validated gem5 ARM-system evidence across multiple benchmark families. | ALLOWED | research/results/gem5_validation.csv; research/results/gem5_performance.csv; research/results/gem5_prefetch_metrics.csv; research/results/gem5_memory_traffic.csv; research/results/gem5_statistical_summary.csv; research/results/gem5_raw_rerun_manifest.csv; research/results/gem5_raw_rerun_statistical_summary.csv; research/results/logs/gem5/gem5_import.log | gem5_full_system | Allowed only for summary groups with a no-prefetch baseline, a COPPER-family row, matching checksums, rc=0, and positive tick counts; current scope is 178 validated gem5 ARM-system PASS rows across 11 benchmark families and 29 benchmark/input groups, including 56 COPPER-family rows. Local raw rerun scope is 661 local raw gem5 full-system rerun rows across 155 tags and policies ampm, bop, copper, copper_clpd16k, copper_clpd32k, copper_clpd64k, copper_clpd64k_peb, copper_clpd64k_rerun, copper_clpd8k, copper_ctlw, copper_ctlw_terminal, copper_ctw, copper_exact131k, copper_exact16k, copper_proof131k, copper_tpw, dcpt, indirect, isb, naive, none, none_retry, spp, spp_copper, spp_copper_slack, stride; raw-only repeated-stat scope is 354 repeated local raw gem5 statistic rows across 24 raw group(s) and policies ampm, copper_clpd64k, copper_clpd64k_peb, dcpt, naive, none, spp, spp_copper_slack, stride. gem5_statistical_summary.csv is still summary-derived and the raw-only statistics are not a full-matrix confidence interval unless the raw group covers the final matrix. |
| C16 | COPPER has matched PicoRV32 tiny-SoC full-core generic-synthesis overhead. | ALLOWED | research/results/fullcore_synthesis.csv; research/results/fullcore_synthesis_overhead.csv | full_core | Allowed only for the open-source PicoRV32 tiny-SoC full-core harness; not production ARM, OoO, silicon, or signoff evidence. |
| C17 | COPPER has matched PicoRV32 tiny-SoC full-core mapped FPGA PPA. | ALLOWED | research/results/mapped_ppa.csv; research/results/mapped_ppa_overhead.csv | full_core mapped PPA | Allowed only when baseline and COPPER PicoRV32 tiny-SoC full-core rows PASS in the same mapped flow with real timing fields; not production ARM, ASIC signoff, or silicon PPA. |

## Claims Still Forbidden

- Silicon power.
- ASIC or foundry signoff.
- Measured silicon power.
- Production ARM/OoO integration.
- State-of-the-art or universal speedup.
- Calling generic Yosys mapped timing.
- Calling accepted-core-wrapper or near-core-stub rows full-core.

## Exact Remaining Blocker

silicon/signoff power absent: Tool estimates are not signoff-grade or silicon measurements.

## Recommendation

Submit as a scoped artifact/mechanism package.
