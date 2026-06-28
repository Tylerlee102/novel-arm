# JSON-to-SQLite AArch64 Full-System Service-Style Summary

This workload composes two public engines in one native AArch64 Linux ROI:
yyjson parses request records, SQLite ingests them into indexed in-memory
tables, and the ROI performs point lookups, range/group queries, and updates.
Pointer-shaped JSON/SQL payload fields are read and stored but never used as
architectural addresses.

Input tag: `app_medium`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 31474136025 | 0.000% | 43463692 | 328639 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xb8236aed9f7723ec | 0 |
| stride | 30896212527 | -1.836% | 43452964 | 306629 | -6.697% | 43624 | 23508 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xb8236aed9f7723ec | 0 |
| naive | 31468886280 | -0.017% | 43463687 | 327438 | -0.365% | 18062 | 4500 | 32168 | 698 | 32168 | 0 | 14104 | 0 | 0 | 0xb8236aed9f7723ec | 0 |
| copper_clpd64k_peb | 31462594578 | -0.037% | 43463672 | 326074 | -0.780% | 14196 | 3532 | 34334 | 623 | 14895 | 19439 | 699 | 0 | 19974 | 0xb8236aed9f7723ec | 0 |
| dcpt | 30566890845 | -2.883% | 43452946 | 325659 | -0.907% | 641656 | 54451 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xb8236aed9f7723ec | 0 |
| spp | 30058835076 | -4.497% | 43453276 | 241766 | -26.434% | 1952087 | 269968 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xb8236aed9f7723ec | 0 |
| ampm | 30669149817 | -2.558% | 43454438 | 369676 | 12.487% | 1552212 | 193046 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xb8236aed9f7723ec | 0 |
| spp_copper_slack | 30050573679 | -4.523% | 43450184 | 240835 | -26.717% | 1944994 | 268653 | 98360 | 376 | 19500 | 78860 | 582 | 0 | 10696 | 0xb8236aed9f7723ec | 0 |

Interpretation:

- Checksum agreement: yes (0xb8236aed9f7723ec).
- Naive DMP CTLW misses: 14104; COPPER CLPD-64K+PEB CTLW misses: 699; reduction: 95.0%.
- SPP+COPPER slack CTLW misses: 582; reduction versus naive DMP: 95.9%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is still a bounded service-style micro-application, not SPEC or a production server, but it exercises a public parser plus database engine together.

status=PASS
