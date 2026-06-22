# yyjson Medium/Stress Seed Stability

Date: 2026-06-19

Scope: public yyjson JSON-parser AArch64 full-system application workload, two medium seeds and two stress seeds, key policies only for the new repeated seed. This is parser-engine external-validity evidence, not a browser or production-service workload.

| Scale | Tag | Seed | Naive CTLW | COPPER CTLW | COPPER reduction | Slack CTLW | Slack reduction | SPP delta | Slack delta | Slack gap vs SPP | COPPER faults | Slack faults | Checksum |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| medium | app_medium | 2 | 3855 | 43 | 98.9% | 59 | 98.5% | -18.351% | -18.342% | +0.009 pp | 0 | 0 | 0x5913918638a88fc6 |
| medium | app_medium_seed3 | 3 | 3901 | 44 | 98.9% | 54 | 98.6% | -16.041% | -16.034% | +0.007 pp | 0 | 0 | 0x36a08ae1ee1a75c2 |
| stress | app_stress | 2 | 4323 | 47 | 98.9% | 112 | 97.4% | -22.097% | -22.186% | -0.089 pp | 0 | 0 | 0xa79b34679333f240 |
| stress | app_stress_seed3 | 3 | 4388 | 35 | 99.2% | 106 | 97.6% | -17.440% | -17.520% | -0.080 pp | 0 | 0 | 0x9fd47fcc9c9a69df |

Aggregate:

- Medium points: 2 seeds; COPPER CTLW reduction 98.9% to 98.9%; SPP+COPPER slack CTLW reduction 98.5% to 98.6%; worst slack-vs-SPP gap 0.009 percentage points.
- Stress points: 2 seeds; COPPER CTLW reduction 98.9% to 99.2%; SPP+COPPER slack CTLW reduction 97.4% to 97.6%; worst slack-vs-SPP gap 0.089 percentage points.
- Across all 4 yyjson medium/stress seed points, COPPER CTLW reduction is at least 98.9%.
- Across all 4 yyjson medium/stress seed points, SPP+COPPER slack CTLW reduction is at least 97.4%.
- Worst absolute SPP+COPPER slack tick gap versus SPP is 0.089 percentage points.
- COPPER and SPP+COPPER slack translation faults are zero across all yyjson seed points.
- All key-policy runs preserve checksum agreement and `rc=0`.

status=PASS
