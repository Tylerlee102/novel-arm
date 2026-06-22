# COPPER Metadata Toggle Bound

Date: 2026-06-19

Purpose: give a rerunnable sensitivity bound for COPPER metadata access energy using measured full-system CLPD event counts. This is not ASIC signoff and does not replace instruction-level SAIF/VCD or a foundry-calibrated SRAM/compiler flow.

## Inputs

- Source traffic CSV: `research\results\copper_prefetch_traffic_overhead_20260616.csv`
- Source DRAM-energy CSV: `research\results\copper_dram_energy_scorecard_20260618.csv`
- Workload rows: 20 COPPER CLPD-64K+PEB public app/service/parser rows
- Learned-proof writes: 34,131
- CLPD authority reads: 1,284,187
- Total metadata events: 1,318,318
- Summed COPPER DRAM operation energy over matching rows: 17,823,940,933 pJ
- Summed COPPER total DRAM energy over matching rows: 1,604,319,502,803 pJ

## Sensitivity Table

| Scenario | Read pJ | Write pJ | Compare pJ/event | Metadata energy | % of DRAM op energy | % of total DRAM energy |
|---|---:|---:|---:|---:|---:|---:|
| low | 1.0 | 2.0 | 0.2 | 1.616 uJ | 0.0091% | 0.000101% |
| mid | 5.0 | 10.0 | 1.0 | 8.081 uJ | 0.0453% | 0.000504% |
| high | 20.0 | 40.0 | 5.0 | 33.641 uJ | 0.1887% | 0.002097% |

## Interpretation

- Even the deliberately high scenario is 0.1887% of matching COPPER DRAM operation energy.
- This supports the narrow claim that metadata-table access energy is unlikely to dominate the measured memory-system energy story under these assumptions.
- This does not prove full-chip power, SRAM compiler energy, physical wire energy, or integrated clocking overhead.
- The paper should continue to describe this as a sensitivity bound, not calibrated silicon power.

CSV: `research\results\copper_metadata_toggle_bound_20260619.csv`

status=PASS
