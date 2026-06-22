# JSON-to-SQLite AArch64 Full-System Service-Style Summary

This workload composes two public engines in one native AArch64 Linux ROI:
yyjson parses request records, SQLite ingests them into indexed in-memory
tables, and the ROI performs point lookups, range/group queries, and updates.
Pointer-shaped JSON/SQL payload fields are read and stored but never used as
architectural addresses.

Input tag: `stress_seed1`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 72740471049 | 0.000% | 112261852 | 924421 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x140fe495c0a04aef | 0 |
| naive | 72663841422 | -0.105% | 112261468 | 911799 | -1.365% | 67139 | 21787 | 108409 | 956 | 108409 | 0 | 41268 | 0 | 0 | 0x140fe495c0a04aef | 0 |
| copper_clpd64k_peb | 72663901029 | -0.105% | 112261447 | 911964 | -1.348% | 62822 | 19675 | 116498 | 747 | 65168 | 51330 | 2346 | 0 | 19982 | 0x140fe495c0a04aef | 0 |
| spp | 70132594869 | -3.585% | 112254214 | 580971 | -37.153% | 5436005 | 709890 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x140fe495c0a04aef | 0 |
| spp_copper_slack | 70182727353 | -3.516% | 112254214 | 588778 | -36.308% | 5480508 | 710176 | 282976 | 421 | 55769 | 227207 | 1168 | 0 | 10690 | 0x140fe495c0a04aef | 0 |

Interpretation:

- Checksum agreement: yes (0x140fe495c0a04aef).
- Naive DMP CTLW misses: 41268; COPPER CLPD-64K+PEB CTLW misses: 2346; reduction: 94.3%.
- SPP+COPPER slack CTLW misses: 1168; reduction versus naive DMP: 97.2%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is still a bounded service-style micro-application, not SPEC or a production server, but it exercises a public parser plus database engine together.

status=PASS
