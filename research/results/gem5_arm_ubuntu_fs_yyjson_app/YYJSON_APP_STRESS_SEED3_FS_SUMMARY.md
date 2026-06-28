# yyjson AArch64 Full-System Application Summary

This is a public yyjson JSON-parser workload. It builds a JSON document
with object arrays, pointer-shaped numeric payload fields, string keys,
and link fields, then parses and traverses the yyjson heap/tree as a native
AArch64 Linux binary under the same gem5 full-system path used by the
SQLite, Lua, Duktape, Olden, and GAPBS experiments.

Input tag: `app_stress_seed3`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 25078093803 | 0.000% | 40027649 | 219785 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x9fd47fcc9c9a69df | 0 |
| naive | 25021646640 | -0.225% | 40028985 | 219138 | -0.294% | 15423 | 780 | 19813 | 587 | 19813 | 0 | 4388 | 0 | 0 | 0x9fd47fcc9c9a69df | 0 |
| copper_clpd64k_peb | 25034395212 | -0.174% | 40028967 | 219171 | -0.279% | 13592 | 648 | 20930 | 589 | 13627 | 7303 | 35 | 0 | 18356 | 0x9fd47fcc9c9a69df | 0 |
| spp | 20704439835 | -17.440% | 40050298 | 82109 | -62.641% | 1206817 | 152308 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x9fd47fcc9c9a69df | 0 |
| spp_copper_slack | 20684435859 | -17.520% | 40050305 | 81610 | -62.868% | 1189205 | 152771 | 41613 | 279 | 1132 | 40481 | 106 | 0 | 10358 | 0x9fd47fcc9c9a69df | 0 |

Interpretation:

- Checksum agreement: yes (0x9fd47fcc9c9a69df).
- Naive DMP CTLW misses: 4388; COPPER CLPD-64K+PEB CTLW misses: 35; reduction: 99.2%.
- SPP+COPPER slack CTLW misses: 106; reduction versus naive DMP: 97.6%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This strengthens the external-validity story with a fourth public application-style engine, but it still does not replace SPEC-like or production-service evaluation.

status=PASS
