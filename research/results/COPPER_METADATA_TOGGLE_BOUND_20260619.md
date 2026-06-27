# COPPER Metadata Toggle Bound

Date: 2026-06-19

Purpose: give a rerunnable sensitivity bound for COPPER metadata access energy using measured full-system CLPD event counts. This is not ASIC signoff and does not replace instruction-level SAIF/VCD or a foundry-calibrated SRAM/compiler flow.

## Inputs

- Source traffic CSV: `research\results\copper_prefetch_traffic_overhead_20260616.csv`
- Source DRAM-energy CSV: `research\results\copper_dram_energy_scorecard_20260618.csv`
- Workload rows: 22 COPPER CLPD-64K+PEB public app/service/parser rows
- Learned-proof writes: 40,058
- CLPD source-proof reads: 1,407,655
- CTLW target-witness lookups charged as metadata reads: 20,046
- Total charged metadata reads: 1,427,701
- Total metadata events: 1,467,759
- Summed COPPER DRAM operation energy over matching rows: 20,821,519,417 pJ
- Summed COPPER total DRAM energy over matching rows: 1,711,953,194,328 pJ

## Sensitivity Table

| Scenario | Read pJ | Write pJ | Compare pJ/event | Metadata energy | % of DRAM op energy | % of total DRAM energy |
|---|---:|---:|---:|---:|---:|---:|
| low | 1.0 | 2.0 | 0.2 | 1.801 uJ | 0.0087% | 0.000105% |
| mid | 5.0 | 10.0 | 1.0 | 9.007 uJ | 0.0433% | 0.000526% |
| high | 20.0 | 40.0 | 5.0 | 37.495 uJ | 0.1801% | 0.002190% |

## Interpretation

- Even the deliberately high scenario is 0.1801% of matching COPPER DRAM operation energy.
- The charged-read total intentionally combines CLPD source-proof lookups with CTLW target-witness lookups; it should be cited as metadata authority lookups, not pure CLPD reads.
- This supports the narrow claim that metadata-table access energy is unlikely to dominate the measured memory-system energy story under these assumptions.
- This does not prove full-chip power, SRAM compiler energy, physical wire energy, or integrated clocking overhead.
- The paper should continue to describe this as a sensitivity bound, not calibrated silicon power.

CSV: `research\results\copper_metadata_toggle_bound_20260619.csv`

status=PASS
