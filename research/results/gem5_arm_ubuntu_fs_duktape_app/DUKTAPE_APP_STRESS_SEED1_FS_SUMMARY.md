# Duktape AArch64 Full-System Runtime Summary

This is a public Duktape 2.7.0 JavaScript-runtime workload: the binary
embeds Duktape and runs object-map, linked-object, update, traversal,
payload, and GC-heavy JavaScript code.

Input tag: `app_stress_seed1`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 214446893778 | 0.000% | 338110825 | 933693 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xa2dd29e | 0 |
| naive | 214077448593 | -0.172% | 338112066 | 943625 | 1.064% | 140754 | 12438 | 167866 | 6566 | 167866 | 0 | 27110 | 0 | 0 | 0xa2dd29e | 0 |
| copper_clpd64k_peb | 213910777431 | -0.250% | 338096582 | 933800 | 0.011% | 114755 | 12611 | 169243 | 5356 | 115196 | 54047 | 441 | 0 | 18376 | 0xa2dd29e | 0 |
| spp | 197610189003 | -7.851% | 338070207 | 599693 | -35.772% | 4579336 | 568336 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xa2dd29e | 0 |
| spp_copper_slack | 197849382903 | -7.740% | 338067210 | 620348 | -33.560% | 4193676 | 566789 | 411404 | 3694 | 78150 | 333254 | 4078 | 0 | 10328 | 0xa2dd29e | 0 |

Interpretation:

- Checksum agreement: yes (0xa2dd29e).
- Naive DMP CTLW misses: 27110; COPPER CLPD-64K+PEB CTLW misses: 441; reduction: 98.4%.
- This adds a third public runtime/application point beyond SQLite and Lua.
