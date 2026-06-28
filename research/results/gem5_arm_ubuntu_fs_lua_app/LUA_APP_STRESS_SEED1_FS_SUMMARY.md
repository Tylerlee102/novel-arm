# Lua AArch64 Full-System Runtime Summary

This is a public Lua 5.4.8 runtime workload: the binary embeds the Lua
interpreter and executes a table-heavy script with hash-table inserts,
map lookups, nested table payloads, linked traversal, updates, and GC steps.

Input tag: `app_stress_seed1`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 74484882891 | 0.000% | 88814289 | 716232 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x55b97fa9 | 0 |
| naive | 72696734163 | -2.401% | 88800110 | 682461 | -4.715% | 183671 | 36446 | 206843 | 10873 | 206843 | 0 | 23170 | 0 | 0 | 0x55b97fa9 | 0 |
| copper_clpd64k_peb | 72419922918 | -2.772% | 88800092 | 673680 | -5.941% | 185364 | 45153 | 310536 | 10381 | 190753 | 119783 | 5389 | 0 | 17961 | 0x55b97fa9 | 0 |
| spp | 50710656249 | -31.918% | 88774382 | 264211 | -63.111% | 4145184 | 484160 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x55b97fa9 | 0 |
| spp_copper_slack | 51195464955 | -31.267% | 88774711 | 274991 | -61.606% | 4132152 | 474261 | 692596 | 3727 | 43494 | 649102 | 707 | 0 | 10211 | 0x55b97fa9 | 0 |

Interpretation:

- Checksum agreement: yes (0x55b97fa9).
- Naive DMP CTLW misses: 23170; COPPER CLPD-64K+PEB CTLW misses: 5389; reduction: 76.7%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This workload adds a language-runtime/table-management point; it is still not a substitute for SPEC-like or production service workloads.
