# Duktape AArch64 Full-System Runtime Summary

This is a public Duktape 2.7.0 JavaScript-runtime workload: the binary
embeds Duktape and runs object-map, linked-object, update, traversal,
payload, and GC-heavy JavaScript code.

Input tag: `app_stress`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 202077116604 | 0.000% | 319029121 | 878862 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x3928cced | 0 |
| stride | 194787347670 | -3.607% | 319020820 | 670500 | -23.708% | 288145 | 211007 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x3928cced | 0 |
| naive | 201569925636 | -0.251% | 319013778 | 883809 | 0.563% | 164639 | 9690 | 180188 | 7706 | 180188 | 0 | 15547 | 0 | 0 | 0x3928cced | 0 |
| copper_clpd64k_peb | 201696158610 | -0.189% | 319013765 | 881694 | 0.322% | 107077 | 9089 | 174917 | 5523 | 108552 | 66365 | 1475 | 0 | 18375 | 0x3928cced | 0 |
| dcpt | 190147443219 | -5.904% | 318997139 | 573514 | -34.744% | 3312113 | 344258 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x3928cced | 0 |
| spp | 185132381634 | -8.385% | 318987525 | 547519 | -37.701% | 3218828 | 472305 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x3928cced | 0 |
| ampm | 189765881496 | -6.092% | 318996448 | 748877 | -14.790% | 2902560 | 376841 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x3928cced | 0 |
| spp_copper_slack | 184405728681 | -8.745% | 318993628 | 536633 | -38.940% | 3512078 | 502125 | 364636 | 3703 | 63201 | 301435 | 1559 | 0 | 10299 | 0x3928cced | 0 |

Interpretation:

- Checksum agreement: yes (0x3928cced).
- Naive DMP CTLW misses: 15547; COPPER CLPD-64K+PEB CTLW misses: 1475; reduction: 90.5%.
- This adds a third public runtime/application point beyond SQLite and Lua.
