# SQLite AArch64 Full-System Application Summary

This is a public SQLite-amalgamation application-style workload:
in-memory B-tree insertions, point lookups, range scans, secondary-index
probes, updates, and pointer-shaped payload-table reads. It runs as a
native AArch64 Linux binary under the same gem5 full-system path used by
the COPPER heap, GAPBS, and Olden experiments.

Input tag: `app_medium_seed1`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 52381638927 | 0.000% | 63143295 | 539124 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xa30dd416ccc0683e | 0 |
| naive | 52389029862 | 0.014% | 63143295 | 539102 | -0.004% | 40372 | 9832 | 58415 | 2256 | 58415 | 0 | 18041 | 0 | 0 | 0xa30dd416ccc0683e | 0 |
| copper_clpd64k_peb | 52384060503 | 0.005% | 63143502 | 536916 | -0.410% | 45695 | 10510 | 71681 | 1271 | 47394 | 24287 | 1699 | 0 | 19640 | 0xa30dd416ccc0683e | 0 |
| spp | 50528393028 | -3.538% | 63139236 | 405271 | -24.828% | 1159080 | 237352 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xa30dd416ccc0683e | 0 |
| spp_copper_slack | 50552614449 | -3.492% | 63139218 | 408449 | -24.238% | 1204166 | 241875 | 118485 | 745 | 44405 | 74080 | 2353 | 0 | 10412 | 0xa30dd416ccc0683e | 0 |

Interpretation:

- Checksum agreement: yes (0xa30dd416ccc0683e).
- Naive DMP CTLW misses: 18041; COPPER CLPD-64K+PEB CTLW misses: 1699; reduction: 90.6%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This workload is stronger external-validity evidence than generated pointer kernels, but it is still one application-style point and should not be oversold as representative of all database/runtime software.
