# yyjson AArch64 Full-System Application Summary

This is a public yyjson JSON-parser workload. It builds a JSON document
with object arrays, pointer-shaped numeric payload fields, string keys,
and link fields, then parses and traverses the yyjson heap/tree as a native
AArch64 Linux binary under the same gem5 full-system path used by the
SQLite, Lua, Duktape, Olden, and GAPBS experiments.

Input tag: `app_medium`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 15039569709 | 0.000% | 21858029 | 139407 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x5913918638a88fc6 | 0 |
| stride | 14045137803 | -6.612% | 21840883 | 107212 | -23.094% | 54119 | 33336 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x5913918638a88fc6 | 0 |
| naive | 15024479148 | -0.100% | 21858007 | 138449 | -0.687% | 8026 | 1259 | 11883 | 448 | 11883 | 0 | 3855 | 0 | 0 | 0x5913918638a88fc6 | 0 |
| copper_clpd64k_peb | 15029157798 | -0.069% | 21858025 | 138486 | -0.661% | 6856 | 1103 | 12515 | 451 | 6899 | 5616 | 43 | 0 | 18349 | 0x5913918638a88fc6 | 0 |
| dcpt | 13360446180 | -11.165% | 21891937 | 92509 | -33.641% | 477933 | 51713 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x5913918638a88fc6 | 0 |
| spp | 12279671703 | -18.351% | 21887090 | 61852 | -55.632% | 665653 | 88240 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x5913918638a88fc6 | 0 |
| ampm | 12821854644 | -14.746% | 21887891 | 83556 | -40.063% | 925445 | 74623 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x5913918638a88fc6 | 0 |
| spp_copper_slack | 12281004369 | -18.342% | 21887065 | 61958 | -55.556% | 657957 | 88244 | 20511 | 356 | 1046 | 19465 | 59 | 0 | 10386 | 0x5913918638a88fc6 | 0 |

Interpretation:

- Checksum agreement: yes (0x5913918638a88fc6).
- Naive DMP CTLW misses: 3855; COPPER CLPD-64K+PEB CTLW misses: 43; reduction: 98.9%.
- SPP+COPPER slack CTLW misses: 59; reduction versus naive DMP: 98.5%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This strengthens the external-validity story with a fourth public application-style engine, but it still does not replace SPEC-like or production-service evaluation.

status=PASS
