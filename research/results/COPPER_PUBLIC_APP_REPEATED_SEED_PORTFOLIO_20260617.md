# Public AArch64 Full-System Repeated-Seed Portfolio

Date: 2026-06-17

This portfolio combines the repeated public-engine app evidence across
medium and stress scales. It covers SQLite, Lua, and Duktape with three
medium layout seeds and two stress layout seeds per engine, using the
`none`, `naive`, `copper_clpd64k_peb`, `spp`, and `spp_copper_slack`
policy subset. The intent is reviewer-facing stability evidence, not a
replacement for SPEC-scale or production-service evaluation.

Aggregate by scale:

| Scale | Engine-seed points | Mean COPPER delta | Mean SPP delta | Mean SPP+COPPER slack delta | Naive CTLW | COPPER CTLW | COPPER CTLW reduction | Slack CTLW | Slack CTLW reduction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| medium | 9 | -0.875% | -12.947% | -13.042% | 151427 | 10983 | 92.747% | 10583 | 93.011% |
| stress | 6 | -1.007% | -14.128% | -14.010% | 173514 | 19217 | 88.925% | 17020 | 90.191% |

Aggregate by engine:

| Engine | Scale-seed points | Mean COPPER delta | Mean SPP delta | Mean SPP+COPPER slack delta | Naive CTLW | COPPER CTLW | COPPER CTLW reduction | Slack CTLW | Slack CTLW reduction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SQLite | 5 | -0.005% | -3.188% | -3.159% | 137928 | 11300 | 91.807% | 16075 | 88.345% |
| Lua | 5 | -2.573% | -29.705% | -29.734% | 103997 | 15125 | 85.456% | 3305 | 96.822% |
| Duktape | 5 | -0.206% | -7.365% | -7.395% | 83016 | 3775 | 95.453% | 8223 | 90.095% |

Overall:

- Engine-seed points: 15; policy rows: 75.
- Correctness: checksum agreement per point = yes; `rc=0` for all rows = yes.
- Translation faults across all rows: 0.
- Standalone COPPER beats unsafe naive DMP on 9/15 engine-seed points.
- Mean COPPER delta: -0.928%; mean SPP delta: -13.420%; mean SPP+COPPER slack delta: -13.429%.
- Overall COPPER CTLW reduction versus naive DMP: 90.706%.
- Overall SPP+COPPER slack CTLW reduction versus naive DMP: 91.505%.
- Worst absolute SPP+COPPER slack gap versus SPP: 0.760 percentage points.
- This closes the local medium-only repetition gap; it does not close the SPEC/production-service gap.

status=PASS
