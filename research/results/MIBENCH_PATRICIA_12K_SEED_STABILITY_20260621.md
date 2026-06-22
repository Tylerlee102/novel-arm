# MiBench Patricia 12K Seed Stability

This generated summary aggregates two completed public MiBench
`large.udp` 12,288-record full-system AArch64 Patricia runs.
The seeds change the deterministic lookup sequence and produce
distinct checksums while keeping the same public input prefix.

| Tag | Seed | Records | Lookups | Checksum | Naive CTLW | COPPER CTLW | COPPER reduction | Slack CTLW | Slack reduction | Slack gap vs SPP | COPPER/slack faults |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| patricia_large12288 | 0 | 12288 | 24576 | `0x60874357358c1fc4` | 18454 | 381 | 97.9% | 635 | 96.6% | +0.035 pp | 0 |
| patricia_large12288_seed1 | 1 | 12288 | 24576 | `0xe4dc12fd1dcd52b0` | 17909 | 398 | 97.8% | 567 | 96.8% | -0.030 pp | 0 |

Interpretation:

- MiBench Patricia 12K seed points: 2.
- Public input records per seed: 12288.
- Lookup operations per seed: 24576.
- Distinct per-seed checksums: 2.
- Minimum COPPER CTLW reduction versus naive DMP: 97.8%.
- Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 96.6%.
- Worst absolute SPP+COPPER slack tick gap versus SPP: 0.035 percentage points.
- COPPER/slack translation faults across both 12K seeds: 0.
- Return-code agreement holds within every seed point.

status=PASS
