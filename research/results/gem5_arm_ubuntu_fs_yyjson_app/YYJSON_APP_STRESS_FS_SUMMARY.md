# yyjson AArch64 Full-System Application Summary

This is a public yyjson JSON-parser workload. It builds a JSON document
with object arrays, pointer-shaped numeric payload fields, string keys,
and link fields, then parses and traverses the yyjson heap/tree as a native
AArch64 Linux binary under the same gem5 full-system path used by the
SQLite, Lua, Duktape, Olden, and GAPBS experiments.

Input tag: `app_stress`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 26521231887 | 0.000% | 39946448 | 218987 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xa79b34679333f240 | 0 |
| stride | 24682011615 | -6.935% | 39952921 | 166943 | -23.766% | 83107 | 53839 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xa79b34679333f240 | 0 |
| naive | 26513927532 | -0.028% | 39946430 | 216838 | -0.981% | 15232 | 2422 | 19557 | 570 | 19557 | 0 | 4323 | 0 | 0 | 0xa79b34679333f240 | 0 |
| copper_clpd64k_peb | 26507541591 | -0.052% | 39946452 | 216903 | -0.952% | 12992 | 2221 | 20641 | 577 | 13039 | 7602 | 47 | 0 | 18349 | 0xa79b34679333f240 | 0 |
| dcpt | 23641404597 | -10.859% | 39984958 | 144599 | -33.969% | 706857 | 80419 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xa79b34679333f240 | 0 |
| spp | 20660957028 | -22.097% | 39973506 | 86372 | -60.558% | 1131291 | 147255 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xa79b34679333f240 | 0 |
| ampm | 22440914622 | -15.385% | 39970967 | 129234 | -40.986% | 1498025 | 115972 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xa79b34679333f240 | 0 |
| spp_copper_slack | 20637296712 | -22.186% | 39973506 | 85984 | -60.736% | 1137790 | 147696 | 43488 | 477 | 2080 | 41408 | 112 | 0 | 10386 | 0xa79b34679333f240 | 0 |

Interpretation:

- Checksum agreement: yes (0xa79b34679333f240).
- Naive DMP CTLW misses: 4323; COPPER CLPD-64K+PEB CTLW misses: 47; reduction: 98.9%.
- SPP+COPPER slack CTLW misses: 112; reduction versus naive DMP: 97.4%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This strengthens the external-validity story with a fourth public application-style engine, but it still does not replace SPEC-like or production-service evaluation.

status=PASS
