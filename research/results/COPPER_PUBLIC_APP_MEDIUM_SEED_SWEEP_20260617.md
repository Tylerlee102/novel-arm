# Public AArch64 Full-System Medium App Seed Sweep

Date: 2026-06-17

This artifact aggregates three public-engine medium workloads across three
layout seeds: SQLite, Lua, and Duktape. Seed 0 is the existing app-medium
run for each engine; seeds 1 and 2 use explicit workload seed arguments.
The policy subset is `none`, `naive`, `copper_clpd64k_peb`, `spp`, and
`spp_copper_slack`, chosen to test safety/performance coexistence after the
full conventional baseline matrix already established SPP as the best
ordinary address-stream baseline on the six medium/stress app points.

| Engine | Seed | Checksum | Naive delta | COPPER delta | SPP delta | SPP+COPPER slack delta | Slack-SPP gap pp | Naive CTLW | COPPER CTLW | Slack CTLW |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SQLite | 0 | 0x6f120768e4acf50e | -0.010% | -0.000% | -3.623% | -3.617% | 0.006 | 16326 | 1211 | 1778 |
| SQLite | 1 | 0xa30dd416ccc0683e | 0.014% | 0.005% | -3.538% | -3.492% | 0.046 | 18041 | 1699 | 2353 |
| SQLite | 2 | 0x7a0f81952b38dd17 | 0.000% | -0.001% | -3.556% | -3.500% | 0.056 | 19212 | 1871 | 2139 |
| Lua | 0 | 0x1087e661 | -1.929% | -2.153% | -29.532% | -29.240% | 0.292 | 31209 | 2706 | 966 |
| Lua | 1 | 0xb0f65a6 | -1.920% | -2.537% | -27.928% | -28.688% | 0.760 | 13014 | 784 | 364 |
| Lua | 2 | 0x40166f35 | -2.005% | -2.601% | -27.757% | -28.355% | 0.598 | 13266 | 853 | 397 |
| Duktape | 0 | 0x2e53ef0 | -0.157% | -0.135% | -6.732% | -6.950% | 0.218 | 13457 | 1241 | 1140 |
| Duktape | 1 | 0x74d2383b | -0.255% | -0.220% | -6.955% | -6.677% | 0.278 | 13364 | 330 | 740 |
| Duktape | 2 | 0x1366b30f | -0.249% | -0.234% | -6.904% | -6.861% | 0.043 | 13538 | 288 | 706 |

Aggregate by engine:

| Engine | Mean COPPER delta | Mean SPP delta | Mean SPP+COPPER slack delta | Naive CTLW | COPPER CTLW | COPPER CTLW reduction | Slack CTLW | Slack CTLW reduction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SQLite | 0.001% | -3.572% | -3.536% | 53579 | 4781 | 91.077% | 6270 | 88.298% |
| Lua | -2.430% | -28.406% | -28.761% | 57489 | 4343 | 92.446% | 1727 | 96.996% |
| Duktape | -0.196% | -6.864% | -6.829% | 40359 | 1859 | 95.394% | 2586 | 93.593% |

Overall:

- Correctness: checksum agreement per engine/seed = yes; `rc=0` for all rows = yes.
- Translation faults across all rows: 0.
- Standalone COPPER beats unsafe naive DMP on 5/9 engine-seed points.
- Overall COPPER CTLW reduction versus naive DMP: 92.747%.
- Overall SPP+COPPER slack CTLW reduction versus naive DMP: 93.011%.
- Worst absolute SPP+COPPER slack gap versus SPP: 0.760 percentage points.
- This is a broader repeated public-engine campaign than the Lua-only sweep, but it is still not SPEC-scale or production-service evidence.

status=PASS
