# SQLite speedtest1 AArch64 Full-System Summary

This is an unmodified upstream SQLite speedtest1 workload built from SQLite 3.53.2
source and run as a native AArch64 Linux binary under gem5 full-system.
The fixed tractable point is `--memdb --verify --stats --size 1 --testset star --repeat 1`.

Input tag: `speedtest1_star_smoke_size1`.

| Policy | ROI ticks | Delta vs none | Sim insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | SQLite time | Verify hash | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 14282182188 | 0.000% | 12950264 | 145908 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.004 | 0e12171d242c353f364c455d6c648193a69cc0d6ed18f85c | 0 |
| naive | 14298558462 | 0.115% | 12950041 | 145515 | -0.269% | 6116 | 1179 | 12962 | 1309 | 12962 | 0 | 6844 | 0 | 0 | 0.004 | 0e12171d242c353f364c455d6c648193a69cc0d6ed18f85c | 0 |
| copper_clpd64k_peb | 14300078274 | 0.125% | 12953382 | 145424 | -0.332% | 5904 | 1231 | 16749 | 916 | 6244 | 10505 | 340 | 0 | 19677 | 0.004 | 0e12171d242c353f364c455d6c648193a69cc0d6ed18f85c | 0 |
| spp | 13442325885 | -5.880% | 12965185 | 91844 | -37.053% | 427494 | 73827 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.008 | 0e12171d242c353f364c455d6c648193a69cc0d6ed18f85c | 0 |
| spp_copper_slack | 13266827559 | -7.109% | 12876511 | 90489 | -37.982% | 426650 | 73937 | 27569 | 659 | 5427 | 22142 | 285 | 0 | 10448 | 0.008 | 0e12171d242c353f364c455d6c648193a69cc0d6ed18f85c | 0 |

Interpretation:

- Verification hash agreement: yes (0e12171d242c353f364c455d6c648193a69cc0d6ed18f85c).
- Verification byte-count agreement: 0; when this is 0, treat the hash as a run-consistency marker and rely on return code plus completed test lines rather than as a result-content checksum.
- Return-code agreement: yes (0).
- Naive DMP CTLW misses: 6844; COPPER CLPD-64K+PEB CTLW misses: 340; reduction: 95.0%.
- SPP+COPPER-slack companion CTLW misses: 285. Plain SPP has no pointer-provenance CTLW counter, so this is a bounded companion-safety cost rather than a reduction comparison.
- Translation faults: naive=0, COPPER=0, SPP=0, SPP+COPPER-slack=0.
- Scope note: this is a small, deterministic, upstream benchmark component rather than a full-scale SQLite performance run. It strengthens external validity because the code is public and unmodified, not because it represents all database workloads.

status=PASS
