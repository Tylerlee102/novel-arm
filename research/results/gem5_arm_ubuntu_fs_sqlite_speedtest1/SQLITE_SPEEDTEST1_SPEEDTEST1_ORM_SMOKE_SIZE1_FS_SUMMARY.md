# SQLite speedtest1 AArch64 Full-System Summary

This is an unmodified upstream SQLite speedtest1 workload built from SQLite 3.53.2
source and run as a native AArch64 Linux binary under gem5 full-system.
The fixed tractable point is `--memdb --verify --stats --size 1 --testset orm --repeat 1`.

Input tag: `speedtest1_orm_smoke_size1`.

| Policy | ROI ticks | Delta vs none | Sim insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | SQLite time | Verify hash | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 28573715682 | 0.000% | 42331137 | 556750 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.020 | 35f60ec9604b50618f587a604e45a6146aaf0e60930b18be | 0 |
| naive | 28532754018 | -0.143% | 42330465 | 552685 | -0.730% | 65177 | 10613 | 103732 | 1725 | 103732 | 0 | 38552 | 0 | 0 | 0.020 | 35f60ec9604b50618f587a604e45a6146aaf0e60930b18be | 0 |
| copper_clpd64k_peb | 28532246193 | -0.145% | 42330409 | 551396 | -0.962% | 45736 | 11949 | 116410 | 1153 | 46933 | 69477 | 1197 | 0 | 19677 | 0.020 | 35f60ec9604b50618f587a604e45a6146aaf0e60930b18be | 0 |
| spp | 26067080493 | -8.773% | 41608290 | 211124 | -62.079% | 2849517 | 427987 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.020 | 35f60ec9604b50618f587a604e45a6146aaf0e60930b18be | 0 |
| spp_copper_slack | 26051789799 | -8.826% | 41608237 | 211446 | -62.021% | 2853321 | 428527 | 189821 | 828 | 27598 | 162223 | 222 | 0 | 10448 | 0.020 | 35f60ec9604b50618f587a604e45a6146aaf0e60930b18be | 0 |

Interpretation:

- Verification hash agreement: yes (35f60ec9604b50618f587a604e45a6146aaf0e60930b18be).
- Verification byte-count agreement: 408505; when this is 0, treat the hash as a run-consistency marker and rely on return code plus completed test lines rather than as a result-content checksum.
- Return-code agreement: yes (0).
- Naive DMP CTLW misses: 38552; COPPER CLPD-64K+PEB CTLW misses: 1197; reduction: 96.9%.
- SPP+COPPER-slack companion CTLW misses: 222. Plain SPP has no pointer-provenance CTLW counter, so this is a bounded companion-safety cost rather than a reduction comparison.
- Translation faults: naive=0, COPPER=0, SPP=0, SPP+COPPER-slack=0.
- Scope note: this is a small, deterministic, upstream benchmark component rather than a full-scale SQLite performance run. It strengthens external validity because the code is public and unmodified, not because it represents all database workloads.

status=PASS
