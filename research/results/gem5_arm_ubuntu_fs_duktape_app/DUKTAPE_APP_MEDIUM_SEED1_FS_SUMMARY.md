# Duktape AArch64 Full-System Runtime Summary

This is a public Duktape 2.7.0 JavaScript-runtime workload: the binary
embeds Duktape and runs object-map, linked-object, update, traversal,
payload, and GC-heavy JavaScript code.

Input tag: `app_medium_seed1`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 108669896658 | 0.000% | 173931594 | 540011 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x74d2383b | 0 |
| naive | 108393201630 | -0.255% | 173931416 | 543214 | 0.593% | 85111 | 10561 | 98477 | 3994 | 98477 | 0 | 13364 | 0 | 0 | 0x74d2383b | 0 |
| copper_clpd64k_peb | 108430686108 | -0.220% | 173931408 | 537910 | -0.389% | 66974 | 10557 | 106334 | 3240 | 67304 | 39030 | 330 | 0 | 18376 | 0x74d2383b | 0 |
| spp | 101112067719 | -6.955% | 173914355 | 325775 | -39.673% | 2264408 | 317874 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x74d2383b | 0 |
| spp_copper_slack | 101413939545 | -6.677% | 173911144 | 339660 | -37.101% | 2247587 | 314104 | 230497 | 2579 | 38223 | 192274 | 740 | 0 | 10328 | 0x74d2383b | 0 |

Interpretation:

- Checksum agreement: yes (0x74d2383b).
- Naive DMP CTLW misses: 13364; COPPER CLPD-64K+PEB CTLW misses: 330; reduction: 97.5%.
- This adds a third public runtime/application point beyond SQLite and Lua.
