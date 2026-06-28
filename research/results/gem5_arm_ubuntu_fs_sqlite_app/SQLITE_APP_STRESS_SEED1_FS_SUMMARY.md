# SQLite AArch64 Full-System Application Summary

This is a public SQLite-amalgamation application-style workload:
in-memory B-tree insertions, point lookups, range scans, secondary-index
probes, updates, and pointer-shaped payload-table reads. It runs as a
native AArch64 Linux binary under the same gem5 full-system path used by
the COPPER heap, GAPBS, and Olden experiments.

Input tag: `app_stress_seed1`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 105062218281 | 0.000% | 124590299 | 1096959 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xa49d4f3a338e0034 | 0 |
| naive | 105060171330 | -0.002% | 124590349 | 1095239 | -0.157% | 93722 | 22916 | 134847 | 4137 | 134847 | 0 | 41123 | 0 | 0 | 0xa49d4f3a338e0034 | 0 |
| copper_clpd64k_peb | 105068657169 | 0.006% | 124590320 | 1094123 | -0.259% | 101589 | 22647 | 157721 | 2554 | 105565 | 52156 | 3976 | 0 | 19640 | 0xa49d4f3a338e0034 | 0 |
| spp | 102292526079 | -2.636% | 124572587 | 836291 | -23.763% | 2254187 | 471312 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xa49d4f3a338e0034 | 0 |
| spp_copper_slack | 102290137137 | -2.639% | 124572551 | 842007 | -23.242% | 2343311 | 480863 | 264023 | 1135 | 94450 | 169573 | 5581 | 0 | 10412 | 0xa49d4f3a338e0034 | 0 |

Interpretation:

- Checksum agreement: yes (0xa49d4f3a338e0034).
- Naive DMP CTLW misses: 41123; COPPER CLPD-64K+PEB CTLW misses: 3976; reduction: 90.3%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This workload is stronger external-validity evidence than generated pointer kernels, but it is still one application-style point and should not be oversold as representative of all database/runtime software.
