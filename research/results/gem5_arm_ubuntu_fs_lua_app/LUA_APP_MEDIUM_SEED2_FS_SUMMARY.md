# Lua AArch64 Full-System Runtime Summary

This is a public Lua 5.4.8 runtime workload: the binary embeds the Lua
interpreter and executes a table-heavy script with hash-table inserts,
map lookups, nested table payloads, linked traversal, updates, and GC steps.

Input tag: `app_medium_seed2`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 38170423701 | 0.000% | 46795391 | 393792 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x40166f35 | 0 |
| naive | 37405089135 | -2.005% | 46795564 | 378496 | -3.884% | 84283 | 17083 | 97551 | 5996 | 97551 | 0 | 13266 | 0 | 0 | 0x40166f35 | 0 |
| copper_clpd64k_peb | 37177757361 | -2.601% | 46791288 | 368923 | -6.315% | 96715 | 26413 | 138549 | 5501 | 97568 | 40981 | 853 | 0 | 17958 | 0x40166f35 | 0 |
| spp | 27575606457 | -27.757% | 46772579 | 157093 | -60.108% | 1918292 | 256291 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x40166f35 | 0 |
| spp_copper_slack | 27347018274 | -28.355% | 46772450 | 153046 | -61.135% | 1977186 | 260359 | 253697 | 2733 | 22566 | 231131 | 397 | 0 | 10208 | 0x40166f35 | 0 |

Interpretation:

- Checksum agreement: yes (0x40166f35).
- Naive DMP CTLW misses: 13266; COPPER CLPD-64K+PEB CTLW misses: 853; reduction: 93.6%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This workload adds a language-runtime/table-management point; it is still not a substitute for SPEC-like or production service workloads.
