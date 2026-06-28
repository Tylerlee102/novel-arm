# Lua AArch64 Full-System Runtime Summary

This is a public Lua 5.4.8 runtime workload: the binary embeds the Lua
interpreter and executes a table-heavy script with hash-table inserts,
map lookups, nested table payloads, linked traversal, updates, and GC steps.

Input tag: `app_medium_seed1`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 38162873925 | 0.000% | 46795326 | 393726 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xb0f65a6 | 0 |
| naive | 37429964568 | -1.920% | 46795483 | 378625 | -3.835% | 84132 | 17052 | 97148 | 5999 | 97148 | 0 | 13014 | 0 | 0 | 0xb0f65a6 | 0 |
| copper_clpd64k_peb | 37194868899 | -2.537% | 46791037 | 368926 | -6.299% | 96362 | 26399 | 137912 | 5498 | 97146 | 40766 | 784 | 0 | 17958 | 0xb0f65a6 | 0 |
| spp | 27504914220 | -27.928% | 46772514 | 156527 | -60.245% | 1943237 | 256618 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xb0f65a6 | 0 |
| spp_copper_slack | 27214588503 | -28.688% | 46771070 | 150543 | -61.765% | 1971855 | 263038 | 255314 | 2751 | 23297 | 232017 | 364 | 0 | 10208 | 0xb0f65a6 | 0 |

Interpretation:

- Checksum agreement: yes (0xb0f65a6).
- Naive DMP CTLW misses: 13014; COPPER CLPD-64K+PEB CTLW misses: 784; reduction: 94.0%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This workload adds a language-runtime/table-management point; it is still not a substitute for SPEC-like or production service workloads.
