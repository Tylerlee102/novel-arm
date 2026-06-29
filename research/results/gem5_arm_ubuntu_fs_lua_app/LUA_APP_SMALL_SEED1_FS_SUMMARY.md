# Lua AArch64 Full-System Runtime Summary

This is a public Lua 5.4.8 runtime workload: the binary embeds the Lua
interpreter and executes a table-heavy script with hash-table inserts,
map lookups, nested table payloads, linked traversal, updates, and GC steps.

Input tag: `app_small_seed1`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 18915096969 | 0.000% | 25736651 | 231053 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x5e756776 | 0 |
| naive | 18613851183 | -1.593% | 25737816 | 222194 | -3.834% | 42492 | 9871 | 55957 | 2927 | 55957 | 0 | 13463 | 0 | 0 | 0x5e756776 | 0 |
| copper_clpd64k_peb | 18551022741 | -1.925% | 25737325 | 217470 | -5.879% | 41641 | 14299 | 74931 | 2706 | 42116 | 32815 | 475 | 0 | 17958 | 0x5e756776 | 0 |
| spp | 15468764751 | -18.220% | 25726929 | 89707 | -61.175% | 1032778 | 154055 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x5e756776 | 0 |
| spp_copper_slack | 15544831275 | -17.818% | 25726800 | 91290 | -60.490% | 1038199 | 152965 | 136916 | 1864 | 13830 | 123086 | 186 | 0 | 10208 | 0x5e756776 | 0 |

Interpretation:

- Checksum agreement: yes (0x5e756776).
- Naive DMP CTLW misses: 13463; COPPER CLPD-64K+PEB CTLW misses: 475; reduction: 96.5%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This workload adds a language-runtime/table-management point; it is still not a substitute for SPEC-like or production service workloads.
