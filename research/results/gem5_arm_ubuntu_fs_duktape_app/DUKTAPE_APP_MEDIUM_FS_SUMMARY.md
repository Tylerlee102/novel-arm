# Duktape AArch64 Full-System Runtime Summary

This is a public Duktape 2.7.0 JavaScript-runtime workload: the binary
embeds Duktape and runs object-map, linked-object, update, traversal,
payload, and GC-heavy JavaScript code.

Input tag: `app_medium`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 101740935888 | 0.000% | 164177814 | 502848 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x2e53ef0 | 0 |
| stride | 98612452170 | -3.075% | 164183403 | 390898 | -22.263% | 159433 | 114046 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x2e53ef0 | 0 |
| naive | 101580798519 | -0.157% | 164177814 | 502763 | -0.017% | 87880 | 7865 | 101339 | 4212 | 101339 | 0 | 13457 | 0 | 0 | 0x2e53ef0 | 0 |
| copper_clpd64k_peb | 101603853774 | -0.135% | 164177801 | 501448 | -0.278% | 60140 | 7282 | 101181 | 3083 | 61381 | 39800 | 1241 | 0 | 18375 | 0x2e53ef0 | 0 |
| dcpt | 96922417230 | -4.736% | 164164100 | 335180 | -33.344% | 1835191 | 188156 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x2e53ef0 | 0 |
| spp | 94892165181 | -6.732% | 164162240 | 301029 | -40.135% | 1836666 | 273072 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x2e53ef0 | 0 |
| ampm | 97044557967 | -4.616% | 164160890 | 448634 | -10.781% | 2024342 | 230109 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x2e53ef0 | 0 |
| spp_copper_slack | 94670430471 | -6.950% | 164165269 | 298929 | -40.553% | 2012765 | 281826 | 197314 | 2496 | 34237 | 163077 | 1140 | 0 | 10299 | 0x2e53ef0 | 0 |

Interpretation:

- Checksum agreement: yes (0x2e53ef0).
- Naive DMP CTLW misses: 13457; COPPER CLPD-64K+PEB CTLW misses: 1241; reduction: 90.8%.
- This adds a third public runtime/application point beyond SQLite and Lua.
