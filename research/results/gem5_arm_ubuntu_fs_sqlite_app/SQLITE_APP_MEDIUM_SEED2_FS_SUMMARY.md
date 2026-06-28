# SQLite AArch64 Full-System Application Summary

This is a public SQLite-amalgamation application-style workload:
in-memory B-tree insertions, point lookups, range scans, secondary-index
probes, updates, and pointer-shaped payload-table reads. It runs as a
native AArch64 Linux binary under the same gem5 full-system path used by
the COPPER heap, GAPBS, and Olden experiments.

Input tag: `app_medium_seed2`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 52357757166 | 0.000% | 62972508 | 533136 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x7a0f81952b38dd17 | 0 |
| naive | 52357882374 | 0.000% | 62972508 | 532180 | -0.179% | 39312 | 10084 | 58526 | 2272 | 58526 | 0 | 19212 | 0 | 0 | 0x7a0f81952b38dd17 | 0 |
| copper_clpd64k_peb | 52357131126 | -0.001% | 62972508 | 531281 | -0.348% | 42948 | 10408 | 69197 | 1265 | 44819 | 24378 | 1871 | 0 | 19640 | 0x7a0f81952b38dd17 | 0 |
| spp | 50496133320 | -3.556% | 62968525 | 402656 | -24.474% | 1146139 | 234445 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x7a0f81952b38dd17 | 0 |
| spp_copper_slack | 50525333424 | -3.500% | 62968514 | 405940 | -23.858% | 1177629 | 237465 | 115693 | 728 | 40816 | 74877 | 2139 | 0 | 10412 | 0x7a0f81952b38dd17 | 0 |

Interpretation:

- Checksum agreement: yes (0x7a0f81952b38dd17).
- Naive DMP CTLW misses: 19212; COPPER CLPD-64K+PEB CTLW misses: 1871; reduction: 90.3%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This workload is stronger external-validity evidence than generated pointer kernels, but it is still one application-style point and should not be oversold as representative of all database/runtime software.
