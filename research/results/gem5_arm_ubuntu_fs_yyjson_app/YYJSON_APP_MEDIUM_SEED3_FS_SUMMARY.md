# yyjson AArch64 Full-System Application Summary

This is a public yyjson JSON-parser workload. It builds a JSON document
with object arrays, pointer-shaped numeric payload fields, string keys,
and link fields, then parses and traverses the yyjson heap/tree as a native
AArch64 Linux binary under the same gem5 full-system path used by the
SQLite, Lua, Duktape, Olden, and GAPBS experiments.

Input tag: `app_medium_seed3`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 14655426237 | 0.000% | 21932355 | 139743 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x36a08ae1ee1a75c2 | 0 |
| naive | 14649147189 | -0.043% | 21932333 | 139473 | -0.193% | 8313 | 486 | 12216 | 465 | 12216 | 0 | 3901 | 0 | 0 | 0x36a08ae1ee1a75c2 | 0 |
| copper_clpd64k_peb | 14654955375 | -0.003% | 21932333 | 139506 | -0.170% | 7191 | 349 | 12900 | 460 | 7235 | 5665 | 44 | 0 | 18356 | 0x36a08ae1ee1a75c2 | 0 |
| spp | 12304612071 | -16.041% | 21971458 | 59620 | -57.336% | 655385 | 91060 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x36a08ae1ee1a75c2 | 0 |
| spp_copper_slack | 12305581434 | -16.034% | 21971458 | 59616 | -57.339% | 670354 | 90914 | 20471 | 267 | 733 | 19738 | 54 | 0 | 10358 | 0x36a08ae1ee1a75c2 | 0 |

Interpretation:

- Checksum agreement: yes (0x36a08ae1ee1a75c2).
- Naive DMP CTLW misses: 3901; COPPER CLPD-64K+PEB CTLW misses: 44; reduction: 98.9%.
- SPP+COPPER slack CTLW misses: 54; reduction versus naive DMP: 98.6%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This strengthens the external-validity story with a fourth public application-style engine, but it still does not replace SPEC-like or production-service evaluation.

status=PASS
