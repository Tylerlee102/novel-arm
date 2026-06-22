# JSON+SQLite Medium Two-Seed Stability

Date: 2026-06-19

Scope: composed public yyjson plus SQLite AArch64 full-system workload, medium scale, key policies only for the new second seed. This is a service-composition stability check, not SPEC or a production database server.

| Tag | Seed | Naive CTLW | COPPER CTLW | COPPER reduction | Slack CTLW | Slack reduction | SPP delta | Slack delta | Slack gap vs SPP | COPPER faults | Slack faults | Checksum |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| app_medium | 3 | 14104 | 699 | 95.0% | 582 | 95.9% | -4.497% | -4.523% | -0.026 pp | 0 | 0 | 0xb8236aed9f7723ec |
| medium_seed1 | 1 | 14301 | 523 | 96.3% | 564 | 96.1% | -4.372% | -4.382% | -0.010 pp | 0 | 0 | 0x0ba31ab66d915ce3 |

Aggregate:

- Points: 2 medium JSON+SQLite seeds.
- COPPER CTLW reduction is at least 95.0% across the two seeds.
- SPP+COPPER slack CTLW reduction is at least 95.9% across the two seeds.
- Worst absolute SPP+COPPER slack tick gap versus SPP is 0.026 percentage points.
- COPPER and SPP+COPPER slack translation faults are zero across both seeds.
- All key-policy runs preserve checksum agreement and `rc=0`.

status=PASS
