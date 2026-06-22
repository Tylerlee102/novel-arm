# JSON-to-SQLite AArch64 Full-System Service-Style Summary

This workload composes two public engines in one native AArch64 Linux ROI:
yyjson parses request records, SQLite ingests them into indexed in-memory
tables, and the ROI performs point lookups, range/group queries, and updates.
Pointer-shaped JSON/SQL payload fields are read and stored but never used as
architectural addresses.

Input tag: `medium_seed1`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 31575115944 | 0.000% | 43590541 | 337031 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x0ba31ab66d915ce3 | 0 |
| naive | 31562777961 | -0.039% | 43590550 | 335281 | -0.519% | 20587 | 5448 | 34890 | 762 | 34890 | 0 | 14301 | 0 | 0 | 0x0ba31ab66d915ce3 | 0 |
| copper_clpd64k_peb | 31570070661 | -0.016% | 43590564 | 334709 | -0.689% | 17103 | 4260 | 37791 | 652 | 17626 | 20165 | 523 | 0 | 19982 | 0x0ba31ab66d915ce3 | 0 |
| spp | 30194524251 | -4.372% | 43586144 | 250356 | -25.717% | 2087021 | 278769 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x0ba31ab66d915ce3 | 0 |
| spp_copper_slack | 30191372073 | -4.382% | 43586131 | 249656 | -25.925% | 2124619 | 280132 | 110739 | 397 | 23296 | 87443 | 564 | 0 | 10690 | 0x0ba31ab66d915ce3 | 0 |

Interpretation:

- Checksum agreement: yes (0x0ba31ab66d915ce3).
- Naive DMP CTLW misses: 14301; COPPER CLPD-64K+PEB CTLW misses: 523; reduction: 96.3%.
- SPP+COPPER slack CTLW misses: 564; reduction versus naive DMP: 96.1%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is still a bounded service-style micro-application, not SPEC or a production server, but it exercises a public parser plus database engine together.

status=PASS
