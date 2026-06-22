# Public AArch64 Full-System Stress App Seed Sweep

Date: 2026-06-17

This artifact extends repeated public-engine evaluation beyond the medium
scale. It aggregates SQLite, Lua, and Duktape stress workloads for seed 0
and seed 1 under `none`, `naive`, `copper_clpd64k_peb`, `spp`, and
`spp_copper_slack`. Seed 0 is the existing stress baseline; seed 1 uses
explicit workload seed arguments added to the public-engine binaries.

| Engine | Seed | Checksum | Naive delta | COPPER delta | SPP delta | SPP+COPPER slack delta | Slack-SPP gap pp | Naive CTLW | COPPER CTLW | Slack CTLW |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SQLite | 0 | 0xc91843372c7ddc37 | -0.007% | -0.037% | -2.587% | -2.549% | 0.038 | 43226 | 2543 | 4224 |
| SQLite | 1 | 0xa49d4f3a338e0034 | -0.002% | 0.006% | -2.636% | -2.639% | 0.003 | 41123 | 3976 | 5581 |
| Lua | 0 | 0x7c4170c4 | -2.426% | -2.800% | -31.392% | -31.120% | 0.272 | 23338 | 5393 | 871 |
| Lua | 1 | 0x55b97fa9 | -2.401% | -2.772% | -31.918% | -31.267% | 0.651 | 23170 | 5389 | 707 |
| Duktape | 0 | 0x3928cced | -0.251% | -0.189% | -8.385% | -8.745% | 0.360 | 15547 | 1475 | 1559 |
| Duktape | 1 | 0xa2dd29e | -0.172% | -0.250% | -7.851% | -7.740% | 0.111 | 27110 | 441 | 4078 |

Aggregate by engine:

| Engine | Mean COPPER delta | Mean SPP delta | Mean SPP+COPPER slack delta | Naive CTLW | COPPER CTLW | COPPER CTLW reduction | Slack CTLW | Slack CTLW reduction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SQLite | -0.015% | -2.612% | -2.594% | 84349 | 6519 | 92.271% | 9805 | 88.376% |
| Lua | -2.786% | -31.655% | -31.194% | 46508 | 10782 | 76.817% | 1578 | 96.607% |
| Duktape | -0.220% | -8.118% | -8.242% | 42657 | 1916 | 95.508% | 5637 | 86.785% |

Overall:

- Correctness: checksum agreement per engine/seed = yes; `rc=0` for all rows = yes.
- Translation faults across all rows: 0.
- Standalone COPPER beats unsafe naive DMP on 4/6 stress engine-seed points.
- Overall COPPER CTLW reduction versus naive DMP: 88.925%.
- Overall SPP+COPPER slack CTLW reduction versus naive DMP: 90.191%.
- Worst absolute SPP+COPPER slack gap versus SPP: 0.651 percentage points.
- This materially extends repeated public-engine evidence beyond medium scale, but it is still not SPEC-scale or production-service evidence.

status=PASS
