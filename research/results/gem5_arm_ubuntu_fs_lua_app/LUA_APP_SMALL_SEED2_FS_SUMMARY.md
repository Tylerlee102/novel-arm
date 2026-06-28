# Lua AArch64 Full-System Runtime Summary

This is a public Lua 5.4.8 runtime workload: the binary embeds the Lua
interpreter and executes a table-heavy script with hash-table inserts,
map lookups, nested table payloads, linked traversal, updates, and GC steps.

Input tag: `app_small_seed2`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 18918349047 | 0.000% | 25737119 | 231084 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x4ea7ed5e | 0 |
| naive | 18621901125 | -1.567% | 25737880 | 222364 | -3.774% | 42675 | 9818 | 56455 | 2914 | 56455 | 0 | 13778 | 0 | 0 | 0x4ea7ed5e | 0 |
| copper_clpd64k_peb | 18573207201 | -1.824% | 25738242 | 217556 | -5.854% | 41838 | 14347 | 75666 | 2703 | 42458 | 33208 | 620 | 0 | 17958 | 0x4ea7ed5e | 0 |
| spp | 15435902979 | -18.408% | 25727370 | 88890 | -61.533% | 1070347 | 155078 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x4ea7ed5e | 0 |
| spp_copper_slack | 15531831288 | -17.901% | 25727241 | 91076 | -60.587% | 1022759 | 153099 | 134389 | 1855 | 13243 | 121146 | 206 | 0 | 10208 | 0x4ea7ed5e | 0 |

Interpretation:

- Checksum agreement: yes (0x4ea7ed5e).
- Naive DMP CTLW misses: 13778; COPPER CLPD-64K+PEB CTLW misses: 620; reduction: 95.5%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This workload adds a language-runtime/table-management point; it is still not a substitute for SPEC-like or production service workloads.
