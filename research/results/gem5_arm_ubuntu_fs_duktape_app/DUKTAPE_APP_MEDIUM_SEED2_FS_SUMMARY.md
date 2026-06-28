# Duktape AArch64 Full-System Runtime Summary

This is a public Duktape 2.7.0 JavaScript-runtime workload: the binary
embeds Duktape and runs object-map, linked-object, update, traversal,
payload, and GC-heavy JavaScript code.

Input tag: `app_medium_seed2`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 108702667854 | 0.000% | 173950803 | 540140 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x1366b30f | 0 |
| naive | 108431949177 | -0.249% | 173950821 | 543048 | 0.538% | 84617 | 10549 | 98157 | 3977 | 98157 | 0 | 13538 | 0 | 0 | 0x1366b30f | 0 |
| copper_clpd64k_peb | 108447933843 | -0.234% | 173950821 | 537878 | -0.419% | 66472 | 10520 | 105293 | 3230 | 66760 | 38533 | 288 | 0 | 18376 | 0x1366b30f | 0 |
| spp | 101198000034 | -6.904% | 173933739 | 330493 | -38.813% | 2349003 | 320898 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x1366b30f | 0 |
| spp_copper_slack | 101244553434 | -6.861% | 173930577 | 334451 | -38.081% | 2347531 | 322780 | 231564 | 2546 | 37951 | 193613 | 706 | 0 | 10328 | 0x1366b30f | 0 |

Interpretation:

- Checksum agreement: yes (0x1366b30f).
- Naive DMP CTLW misses: 13538; COPPER CLPD-64K+PEB CTLW misses: 288; reduction: 97.9%.
- This adds a third public runtime/application point beyond SQLite and Lua.
