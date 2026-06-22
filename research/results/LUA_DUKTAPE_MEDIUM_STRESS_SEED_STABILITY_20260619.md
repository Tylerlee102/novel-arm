# Lua/Duktape Medium/Stress Seed Stability

Date: 2026-06-19

Scope: public Lua-table and Duktape-object AArch64 full-system application workloads, three medium seeds and two stress seeds per engine, key policies only for repeated seeds. This is language-runtime-style external-validity evidence, not SPEC or browser-scale JavaScript/Lua execution.

| Engine | Scale | Tag | Seed | Naive CTLW | COPPER CTLW | COPPER reduction | Slack CTLW | Slack reduction | SPP delta | Slack delta | Slack gap vs SPP | COPPER faults | Slack faults | Checksum |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Lua | medium | app_medium | base | 31209 | 2706 | 91.3% | 966 | 96.9% | -29.532% | -29.240% | +0.292 pp | 0 | 0 | 0x1087e661 |
| Lua | medium | app_medium_seed1 | 1 | 13014 | 784 | 94.0% | 364 | 97.2% | -27.928% | -28.688% | -0.760 pp | 0 | 0 | 0xb0f65a6 |
| Lua | medium | app_medium_seed2 | 2 | 13266 | 853 | 93.6% | 397 | 97.0% | -27.757% | -28.355% | -0.598 pp | 0 | 0 | 0x40166f35 |
| Lua | stress | app_stress | 0 | 23338 | 5393 | 76.9% | 871 | 96.3% | -31.392% | -31.120% | +0.272 pp | 0 | 0 | 0x7c4170c4 |
| Lua | stress | app_stress_seed1 | 1 | 23170 | 5389 | 76.7% | 707 | 96.9% | -31.918% | -31.267% | +0.651 pp | 0 | 0 | 0x55b97fa9 |
| Duktape | medium | app_medium | base | 13457 | 1241 | 90.8% | 1140 | 91.5% | -6.732% | -6.950% | -0.218 pp | 0 | 0 | 0x2e53ef0 |
| Duktape | medium | app_medium_seed1 | 1 | 13364 | 330 | 97.5% | 740 | 94.5% | -6.955% | -6.677% | +0.278 pp | 0 | 0 | 0x74d2383b |
| Duktape | medium | app_medium_seed2 | 2 | 13538 | 288 | 97.9% | 706 | 94.8% | -6.904% | -6.861% | +0.043 pp | 0 | 0 | 0x1366b30f |
| Duktape | stress | app_stress | base | 15547 | 1475 | 90.5% | 1559 | 90.0% | -8.385% | -8.745% | -0.360 pp | 0 | 0 | 0x3928cced |
| Duktape | stress | app_stress_seed1 | 1 | 27110 | 441 | 98.4% | 4078 | 85.0% | -7.851% | -7.740% | +0.111 pp | 0 | 0 | 0xa2dd29e |

Aggregate:

- Lua: 5 points; COPPER CTLW reduction 76.7% to 94.0%; SPP+COPPER slack CTLW reduction 96.3% to 97.2%; worst slack-vs-SPP gap 0.760 percentage points.
- Duktape: 5 points; COPPER CTLW reduction 90.5% to 98.4%; SPP+COPPER slack CTLW reduction 85.0% to 94.8%; worst slack-vs-SPP gap 0.360 percentage points.
- Medium: 6 points; COPPER CTLW reduction 90.8% to 97.9%; SPP+COPPER slack CTLW reduction 91.5% to 97.2%; worst slack-vs-SPP gap 0.760 percentage points.
- Stress: 4 points; COPPER CTLW reduction 76.7% to 98.4%; SPP+COPPER slack CTLW reduction 85.0% to 96.9%; worst slack-vs-SPP gap 0.651 percentage points.
- Across all 10 Lua/Duktape medium/stress seed points, COPPER CTLW reduction is at least 76.7%.
- Across all 10 Lua/Duktape medium/stress seed points, SPP+COPPER slack CTLW reduction is at least 85.0%.
- Worst absolute SPP+COPPER slack tick gap versus SPP is 0.760 percentage points.
- COPPER and SPP+COPPER slack translation faults are zero across all Lua/Duktape seed points.
- All key-policy runs preserve checksum agreement and `rc=0`.

status=PASS
