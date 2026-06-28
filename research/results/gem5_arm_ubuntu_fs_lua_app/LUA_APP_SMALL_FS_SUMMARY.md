# Lua AArch64 Full-System Runtime Summary

This is a public Lua 5.4.8 runtime workload: the binary embeds the Lua
interpreter and executes a table-heavy script with hash-table inserts,
map lookups, nested table payloads, linked traversal, updates, and GC steps.

Input tag: `app_small`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 18737577333 | 0.000% | 25454012 | 229875 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xa39a7f | 0 |
| stride | 17330249736 | -7.511% | 25445015 | 173720 | -24.428% | 78592 | 57286 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xa39a7f | 0 |
| bop | 16452927270 | -12.193% | 25431278 | 151664 | -34.023% | 181133 | 92539 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xa39a7f | 0 |
| naive | 18550028403 | -1.001% | 25454368 | 221855 | -3.489% | 39359 | 8926 | 50445 | 2793 | 50445 | 0 | 11084 | 0 | 0 | 0xa39a7f | 0 |
| copper_clpd64k_peb | 18507081726 | -1.230% | 25454574 | 217998 | -5.167% | 44859 | 12730 | 75887 | 2865 | 47169 | 28718 | 2310 | 0 | 17964 | 0xa39a7f | 0 |
| dcpt | 16218598500 | -13.443% | 25446462 | 128464 | -44.116% | 1116863 | 106035 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xa39a7f | 0 |
| spp | 15299270415 | -18.350% | 25472943 | 90192 | -60.765% | 1041255 | 152643 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xa39a7f | 0 |
| spp_copper | 15277322718 | -18.467% | 25471693 | 89282 | -61.161% | 1041730 | 153669 | 126383 | 1841 | 14925 | 111458 | 768 | 0 | 10172 | 0xa39a7f | 0 |
| spp_copper_slack | 15278586453 | -18.460% | 25471695 | 89276 | -61.163% | 1043688 | 153663 | 127066 | 1850 | 14936 | 112130 | 766 | 0 | 10172 | 0xa39a7f | 0 |
| ampm | 16141415760 | -13.855% | 25443809 | 134176 | -41.631% | 975649 | 116450 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xa39a7f | 0 |

Interpretation:

- Checksum agreement: yes (0xa39a7f).
- Naive DMP CTLW misses: 11084; COPPER CLPD-64K+PEB CTLW misses: 2310; reduction: 79.2%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This workload adds a language-runtime/table-management point; it is still not a substitute for SPEC-like or production service workloads.
