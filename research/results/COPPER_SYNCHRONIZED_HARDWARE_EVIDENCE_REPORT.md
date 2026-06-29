# COPPER Synchronized Hardware Evidence Report

## Status

SUBMISSION-READY

## Main Result

The synchronized hardware-evidence pass supports a scoped COPPER artifact/mechanism submission. It has accepted-core-wrapper or stronger mapped timing, matched baseline/COPPER overhead, fpga_tool_estimate or stronger power evidence, passing paper/audit/artifact gates, and explicit machine-readable blockers for stronger production-core, signoff, silicon, or top-tier claims.

## Commands Run

- `make fullcore-synth`
- `make mapped-ppa`
- `make power-evidence`
- `make sync-hardware-evidence`
- `make paper`
- `make paper-audit`
- `make artifact`
- GitHub Actions parallel lanes: `full-readiness`, `fullcore-synth`, `mapped-ppa`, `power-evidence`, `sync-docs-audit-package`.

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
| accepted_core_wrapper | core_wrapper_plus_baseline_prefetch | ecp5-85k | yosys+nextpnr-ecp5 | local_windows | PASS | 170.82 | NA | NA | NA | research/results/logs/mapped_ppa/ecp5_core_wrapper_plus_baseline_prefetch.log |
| accepted_core_wrapper | core_wrapper_plus_copper | ecp5-85k | yosys+nextpnr-ecp5 | local_windows | PASS | 86.15 | NA | NA | NA | research/results/logs/mapped_ppa/ecp5_core_wrapper_plus_copper.log |

## Lane C Power Classification

| scope | design | target | measurement_type | available | power_mw | full_core | signoff_grade | silicon_measured | report_path |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_core | full_core_plus_copper | vivado-xc7a35tcsg324-1 | fpga_tool_estimate | yes | 87.000 | yes | no | no | research/results/logs/vivado/full_core_plus_copper.log |
| unit | mcpat_activity_proxy | unit_proxy | activity_proxy | yes | NA | no | no | no | research/results/COPPER_MCPAT_SENSITIVITY_20260618.md |
| unit | proxy_assumed_memory_energy | memory_traffic_proxy_v1 | memory_energy_proxy | yes | NA | no | no | no | research/results/energy_proxy.csv |

## Sync Gate Status

| gate | status | severity | blocker | observed_evidence |
| --- | --- | --- | --- | --- |
| schema_integrity | PASS | INFO |  | all checked ledgers have required columns |
| accepted_or_full_mapped_timing | PASS | INFO |  | mapped_full_core_full_core_plus_copper_vivado_xc7a35tcsg324_1_vivado_impl_local_windows |
| matched_overhead | PASS | INFO |  | mapped_overhead_full_core_lut_vivado_xc7a35tcsg324_1_vivado_impl_full_core_baseline_full_core_plus_copper_local_windows |
| power_evidence | PASS | INFO |  | fpga_tool_estimate |
| full_core_absent | PASS | INFO |  | mapped_full_core_full_core_plus_copper_vivado_xc7a35tcsg324_1_vivado_impl_local_windows |
| silicon_signoff_power_absent | BLOCKER | BLOCKER | silicon/signoff power absent | none |
| paper_audits_artifact | PASS | INFO |  | paper=PASS; audit=PASS; artifact=PASS |
| overall_status | SUBMISSION-READY | INFO | production/full-system full-core and silicon/signoff blockers remain for stronger claims | SUBMISSION-READY |

## Paper/Audit/Artifact Status

PASS: paper_build_status.csv contains a PASS row; claim, number, and todo audits pass; artifact zip and manifest exist

## Claims Allowed Now

| gate | scope | claim_allowed | evidence_id | source_csv |
| --- | --- | --- | --- | --- |
| mapped_timing | full_core | PicoRV32 tiny-SoC full-core mapped timing | mapped_full_core_full_core_plus_copper_vivado_xc7a35tcsg324_1_vivado_impl_local_windows | research/results/mapped_ppa.csv |
| matched_overhead | full_core | matched overhead for the listed scope | mapped_overhead_full_core_lut_vivado_xc7a35tcsg324_1_vivado_impl_full_core_baseline_full_core_plus_copper_local_windows | research/results/mapped_ppa_overhead.csv; research/results/fullcore_synthesis_overhead.csv |
| power_classification | full_core | fpga_tool_estimate power evidence | power_fpga_tool_estimate_full_core_full_core_plus_copper_vivado_xc7a35tcsg324_1_vivado_impl_local_windows | research/results/power_report_index.csv |
| paper_audit_artifact | artifact | scoped paper/artifact claims |  | research/results/claim_audit.csv; research/results/number_audit.csv; research/results/todo_audit.csv; research/results/paper_build_status.csv; research/results/artifact_manifest.csv |

## Claims Still Forbidden

- silicon/signoff/full-core power unless measurement_type proves it
- unscoped or production-core full-core PPA; generic Yosys timing; unmapped Fmax
- unscoped or production-core overhead
- unsupported paper claims; failed artifact package

## Exact Remaining Blocker

silicon/signoff power absent: Tool estimates are not signoff-grade or silicon measurements.

## Recommendation

Submit
