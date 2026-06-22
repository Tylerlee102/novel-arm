# JSON+SQLite Stress Two-Seed Stability

Date: 2026-06-19

Scope: composed public yyjson plus SQLite AArch64 full-system workload, stress scale, key policies only for the new second seed. This is a service-composition stability check, not SPEC or a production database server.

| Tag | Seed | Naive CTLW | COPPER CTLW | COPPER reduction | Slack CTLW | Slack reduction | SPP delta | Slack delta | Slack gap vs SPP | COPPER faults | Slack faults | Checksum |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| app_stress | 4 | 33203 | 2861 | 91.4% | 1144 | 96.6% | -3.588% | -3.623% | -0.035 pp | 0 | 0 | 0x349368bc3162ec49 |
| stress_seed1 | 5 | 41268 | 2346 | 94.3% | 1168 | 97.2% | -3.585% | -3.516% | +0.069 pp | 0 | 0 | 0x140fe495c0a04aef |

Aggregate:

- Points: 2 stress JSON+SQLite seeds.
- COPPER CTLW reduction is at least 91.4% across the two stress seeds.
- SPP+COPPER slack CTLW reduction is at least 96.6% across the two stress seeds.
- Worst absolute SPP+COPPER slack tick gap versus SPP is 0.069 percentage points.
- COPPER and SPP+COPPER slack translation faults are zero across both stress seeds.
- All key-policy runs preserve checksum agreement and `rc=0`.

status=PASS
