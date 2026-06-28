# SQLite AArch64 Full-System Application Summary

This is a public SQLite-amalgamation application-style workload:
in-memory B-tree insertions, point lookups, range scans, secondary-index
probes, updates, and pointer-shaped payload-table reads. It runs as a
native AArch64 Linux binary under the same gem5 full-system path used by
the COPPER heap, GAPBS, and Olden experiments.

Input tag: `app_medium`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 52394114439 | 0.000% | 63163423 | 563217 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x6f120768e4acf50e | 0 |
| stride | 51940140867 | -0.866% | 63161241 | 535418 | -4.936% | 56415 | 29647 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x6f120768e4acf50e | 0 |
| naive | 52388923635 | -0.010% | 63163222 | 560830 | -0.424% | 42507 | 12243 | 58835 | 2038 | 58835 | 0 | 16326 | 0 | 0 | 0x6f120768e4acf50e | 0 |
| copper_clpd64k_peb | 52394046840 | -0.000% | 63163364 | 560745 | -0.439% | 46041 | 11605 | 72328 | 1235 | 47252 | 25076 | 1211 | 0 | 19725 | 0x6f120768e4acf50e | 0 |
| dcpt | 51351458805 | -1.990% | 63146455 | 523387 | -7.072% | 713882 | 64900 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x6f120768e4acf50e | 0 |
| spp | 50495726727 | -3.623% | 63156836 | 425168 | -24.511% | 1177907 | 239401 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x6f120768e4acf50e | 0 |
| ampm | 51521464629 | -1.666% | 63153608 | 612082 | 8.676% | 2333124 | 248325 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x6f120768e4acf50e | 0 |
| spp_copper_slack | 50499202248 | -3.617% | 63156820 | 425977 | -24.367% | 1214598 | 245244 | 115335 | 720 | 42823 | 72512 | 1778 | 0 | 10458 | 0x6f120768e4acf50e | 0 |

Interpretation:

- Checksum agreement: yes (0x6f120768e4acf50e).
- Naive DMP CTLW misses: 16326; COPPER CLPD-64K+PEB CTLW misses: 1211; reduction: 92.6%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This workload is stronger external-validity evidence than generated pointer kernels, but it is still one application-style point and should not be oversold as representative of all database/runtime software.
