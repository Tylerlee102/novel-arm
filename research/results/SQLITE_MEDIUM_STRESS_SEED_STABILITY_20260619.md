# SQLite Medium/Stress Seed Stability

Date: 2026-06-19

Scope: public SQLite amalgamation AArch64 full-system application workload, three medium seeds and two stress seeds, key policies only for repeated seeds. This is database-style external-validity evidence, not a production database-server campaign.

| Scale | Tag | Seed | Naive CTLW | COPPER CTLW | COPPER reduction | Slack CTLW | Slack reduction | SPP delta | Slack delta | Slack gap vs SPP | COPPER faults | Slack faults | Checksum |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| medium | app_medium | base | 16326 | 1211 | 92.6% | 1778 | 89.1% | -3.623% | -3.617% | +0.006 pp | 0 | 0 | 0x6f120768e4acf50e |
| medium | app_medium_seed1 | 1 | 18041 | 1699 | 90.6% | 2353 | 87.0% | -3.538% | -3.492% | +0.046 pp | 0 | 0 | 0xa30dd416ccc0683e |
| medium | app_medium_seed2 | 2 | 19212 | 1871 | 90.3% | 2139 | 88.9% | -3.556% | -3.500% | +0.056 pp | 0 | 0 | 0x7a0f81952b38dd17 |
| stress | app_stress | base | 43226 | 2543 | 94.1% | 4224 | 90.2% | -2.587% | -2.549% | +0.038 pp | 0 | 0 | 0xc91843372c7ddc37 |
| stress | app_stress_seed1 | 1 | 41123 | 3976 | 90.3% | 5581 | 86.4% | -2.636% | -2.639% | -0.003 pp | 0 | 0 | 0xa49d4f3a338e0034 |

Aggregate:

- Medium points: 3 seeds; COPPER CTLW reduction 90.3% to 92.6%; SPP+COPPER slack CTLW reduction 87.0% to 89.1%; worst slack-vs-SPP gap 0.056 percentage points.
- Stress points: 2 seeds; COPPER CTLW reduction 90.3% to 94.1%; SPP+COPPER slack CTLW reduction 86.4% to 90.2%; worst slack-vs-SPP gap 0.038 percentage points.
- Across all 5 SQLite medium/stress seed points, COPPER CTLW reduction is at least 90.3%.
- Across all 5 SQLite medium/stress seed points, SPP+COPPER slack CTLW reduction is at least 86.4%.
- Worst absolute SPP+COPPER slack tick gap versus SPP is 0.056 percentage points.
- COPPER and SPP+COPPER slack translation faults are zero across all SQLite seed points.
- All key-policy runs preserve checksum agreement and `rc=0`.

status=PASS
