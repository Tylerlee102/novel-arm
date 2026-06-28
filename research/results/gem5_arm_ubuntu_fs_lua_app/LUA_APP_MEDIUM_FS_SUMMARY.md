# Lua AArch64 Full-System Runtime Summary

This is a public Lua 5.4.8 runtime workload: the binary embeds the Lua
interpreter and executes a table-heavy script with hash-table inserts,
map lookups, nested table payloads, linked traversal, updates, and GC steps.

Input tag: `app_medium`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 38222677395 | 0.000% | 46304997 | 396700 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x1087e661 | 0 |
| stride | 34394045193 | -10.017% | 46783432 | 293562 | -25.999% | 140547 | 101897 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x1087e661 | 0 |
| naive | 37485191286 | -1.929% | 46298728 | 385791 | -2.750% | 74914 | 12522 | 106125 | 4486 | 106125 | 0 | 31209 | 0 | 0 | 0x1087e661 | 0 |
| copper_clpd64k_peb | 37399695201 | -2.153% | 46298911 | 381455 | -3.843% | 73613 | 16745 | 147770 | 4334 | 76319 | 71451 | 2706 | 0 | 17964 | 0x1087e661 | 0 |
| dcpt | 30844798992 | -19.302% | 46778386 | 204210 | -48.523% | 2145233 | 195777 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x1087e661 | 0 |
| spp | 26934731640 | -29.532% | 46267099 | 150510 | -62.059% | 1911196 | 264160 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x1087e661 | 0 |
| ampm | 30505119012 | -20.191% | 46780163 | 222046 | -44.027% | 1614607 | 199777 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x1087e661 | 0 |
| spp_copper_slack | 27046477116 | -29.240% | 46263871 | 152897 | -61.458% | 1858545 | 261573 | 272364 | 2696 | 25216 | 247148 | 966 | 0 | 10172 | 0x1087e661 | 0 |

Interpretation:

- Checksum agreement: yes (0x1087e661).
- Naive DMP CTLW misses: 31209; COPPER CLPD-64K+PEB CTLW misses: 2706; reduction: 91.3%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This workload adds a language-runtime/table-management point; it is still not a substitute for SPEC-like or production service workloads.
