# Lua AArch64 Full-System Runtime Summary

This is a public Lua 5.4.8 runtime workload: the binary embeds the Lua
interpreter and executes a table-heavy script with hash-table inserts,
map lookups, nested table payloads, linked traversal, updates, and GC steps.

Input tag: `app_stress`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 74495345085 | 0.000% | 88813935 | 716247 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x7c4170c4 | 0 |
| stride | 65833541226 | -11.627% | 88800382 | 522398 | -27.065% | 288936 | 195723 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x7c4170c4 | 0 |
| naive | 72687976929 | -2.426% | 88799735 | 682761 | -4.675% | 183611 | 36039 | 206951 | 10855 | 206951 | 0 | 23338 | 0 | 0 | 0x7c4170c4 | 0 |
| copper_clpd64k_peb | 72409611906 | -2.800% | 88799717 | 673615 | -5.952% | 185704 | 45125 | 311484 | 10430 | 191097 | 120387 | 5393 | 0 | 17961 | 0x7c4170c4 | 0 |
| dcpt | 58573568799 | -21.373% | 88789166 | 352826 | -50.740% | 4069737 | 371512 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x7c4170c4 | 0 |
| spp | 51109467705 | -31.392% | 88774497 | 273903 | -61.759% | 3821249 | 474760 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x7c4170c4 | 0 |
| ampm | 58222210509 | -21.844% | 88796006 | 397866 | -44.451% | 2696060 | 357037 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x7c4170c4 | 0 |
| spp_copper_slack | 51312254049 | -31.120% | 88769306 | 282992 | -60.490% | 3829031 | 465854 | 699463 | 3881 | 43778 | 655685 | 871 | 0 | 10211 | 0x7c4170c4 | 0 |

Interpretation:

- Checksum agreement: yes (0x7c4170c4).
- Naive DMP CTLW misses: 23338; COPPER CLPD-64K+PEB CTLW misses: 5393; reduction: 76.9%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This workload adds a language-runtime/table-management point; it is still not a substitute for SPEC-like or production service workloads.
