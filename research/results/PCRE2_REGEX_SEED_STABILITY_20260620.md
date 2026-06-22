# PCRE2 Regex Seed Stability

Date: 2026-06-20

Scope: public PCRE2 8-bit regex compiler/matcher AArch64 full-system
workload, two deterministic input seeds, key policies only for the
new repeated seed. This is parser/matcher-library external-validity
evidence, not production log-processing service evidence.

| Seed label | Input seed | Checksum | Naive CTLW | COPPER CTLW | COPPER reduction | Slack CTLW | Slack reduction | SPP delta | Slack delta | Slack gap vs SPP | COPPER faults | Slack faults |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| seed0 | 0 | 0x70905e0adac9ac17 | 9406 | 62 | 99.3% | 79 | 99.2% | -8.100% | -8.054% | +0.046 pp | 0 | 0 |
| seed1 | 1 | 0xfc469fc668f4c38c | 9394 | 59 | 99.4% | 107 | 98.9% | -8.101% | -8.100% | +0.001 pp | 0 | 0 |

Aggregate interpretation:

- PCRE2 seed points: 2.
- Distinct per-seed checksums: 2.
- All key-policy runs preserve checksum agreement and `rc=0` within each seed.
- Minimum COPPER CTLW reduction versus naive DMP: 99.3%.
- Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 98.9%.
- Worst absolute SPP+COPPER slack tick gap versus SPP: 0.046 percentage points.
- COPPER/slack translation faults across both seed points: 0.
- This strengthens public parser/matcher breadth and seed stability, but does not replace production log-processing or browser-scale evaluation.

status=PASS
