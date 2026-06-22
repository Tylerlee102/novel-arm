# SQLite speedtest1 Component Summary

This file aggregates the tractable upstream SQLite 3.53.2 speedtest1
components run under full-system AArch64 gem5: JSON, star-schema, and
ORM-style wide-row storage. The speedtest source is unmodified; only the
selected `--testset` and fixed `--size 1` make the runs locally tractable.

| Component | Verify bytes | Verify hash | Naive CTLW | COPPER CTLW | Slack CTLW | COPPER reduction | Slack reduction vs naive | COPPER delta | SPP delta | Slack delta | Slack-SPP gap pp |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| json | 0 | 0e12171d242c353f364c455d6c648193a69cc0d6ed18f85c | 12802 | 983 | 1470 | 92.3% | 88.5% | 0.041% | -34.728% | -34.731% | -0.003 |
| star | 0 | 0e12171d242c353f364c455d6c648193a69cc0d6ed18f85c | 6844 | 340 | 285 | 95.0% | 95.8% | 0.125% | -5.880% | -7.109% | -1.229 |
| orm | 408505 | 35f60ec9604b50618f587a604e45a6146aaf0e60930b18be | 38552 | 1197 | 222 | 96.9% | 99.4% | -0.145% | -8.773% | -8.826% | -0.053 |

Aggregate interpretation:

- Components: 3.
- Policy return codes all zero: yes.
- Per-component verification hash agreement across policies: yes.
- Components with zero verification byte count: json, star. Zero-byte speedtest hashes are run-consistency markers, not result-content checksums.
- Minimum COPPER CTLW reduction versus naive DMP: 92.3%.
- Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 88.5%.
- Worst SPP+COPPER slack slowdown versus SPP: 0.000 percentage points.
- Translation faults across key policies and components: 0.
- Scope note: these are small speedtest1 components, not production database throughput benchmarks.

status=PASS
