# JSON-to-SQLite AArch64 Full-System Service-Style Summary

This workload composes two public engines in one native AArch64 Linux ROI:
yyjson parses request records, SQLite ingests them into indexed in-memory
tables, and the ROI performs point lookups, range/group queries, and updates.
Pointer-shaped JSON/SQL payload fields are read and stored but never used as
architectural addresses.

Input tag: `app_stress`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 72752492016 | 0.000% | 112229717 | 933617 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x349368bc3162ec49 | 0 |
| stride | 72164640123 | -0.808% | 112228575 | 908107 | -2.732% | 55752 | 27984 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x349368bc3162ec49 | 0 |
| naive | 72677932650 | -0.102% | 112226125 | 925283 | -0.893% | 74485 | 18032 | 107690 | 998 | 107690 | 0 | 33203 | 0 | 0 | 0x349368bc3162ec49 | 0 |
| copper_clpd64k_peb | 72694647918 | -0.080% | 112226177 | 926323 | -0.781% | 66385 | 15412 | 114186 | 773 | 69246 | 44940 | 2861 | 0 | 19975 | 0x349368bc3162ec49 | 0 |
| dcpt | 71744139711 | -1.386% | 112228253 | 950652 | 1.825% | 1205545 | 110537 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x349368bc3162ec49 | 0 |
| spp | 70141908879 | -3.588% | 112214382 | 596699 | -36.087% | 5530146 | 707152 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x349368bc3162ec49 | 0 |
| ampm | 71403711480 | -1.854% | 112225228 | 898132 | -3.801% | 3293827 | 430210 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x349368bc3162ec49 | 0 |
| spp_copper_slack | 70116427053 | -3.623% | 112218855 | 584460 | -37.398% | 5483115 | 702639 | 280232 | 414 | 58166 | 222066 | 1144 | 0 | 10659 | 0x349368bc3162ec49 | 0 |

Interpretation:

- Checksum agreement: yes (0x349368bc3162ec49).
- Naive DMP CTLW misses: 33203; COPPER CLPD-64K+PEB CTLW misses: 2861; reduction: 91.4%.
- SPP+COPPER slack CTLW misses: 1144; reduction versus naive DMP: 96.6%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is still a bounded service-style micro-application, not SPEC or a production server, but it exercises a public parser plus database engine together.

status=PASS
