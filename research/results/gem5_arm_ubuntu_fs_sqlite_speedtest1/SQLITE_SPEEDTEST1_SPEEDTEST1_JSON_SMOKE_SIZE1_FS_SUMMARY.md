# SQLite speedtest1 AArch64 Full-System Summary

This is an unmodified upstream SQLite speedtest1 workload built from SQLite 3.53.2
source and run as a native AArch64 Linux binary under gem5 full-system.
The fixed tractable point is `--memdb --verify --stats --size 1 --testset json --repeat 1`.

Input tag: `speedtest1_json_smoke_size1`.

| Policy | ROI ticks | Delta vs none | Sim insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | SQLite time | Verify hash | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 69176582505 | 0.000% | 55959513 | 1176159 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.060 | 0e12171d242c353f364c455d6c648193a69cc0d6ed18f85c | 0 |
| naive | 69162313788 | -0.021% | 55959788 | 1175836 | -0.027% | 13899 | 1894 | 26703 | 1769 | 26703 | 0 | 12802 | 0 | 0 | 0.060 | 0e12171d242c353f364c455d6c648193a69cc0d6ed18f85c | 0 |
| copper_clpd64k_peb | 69204938454 | 0.041% | 55959750 | 1176344 | 0.016% | 20585 | 2113 | 39630 | 1324 | 21568 | 18062 | 983 | 0 | 19677 | 0.060 | 0e12171d242c353f364c455d6c648193a69cc0d6ed18f85c | 0 |
| spp | 45153251883 | -34.728% | 55884423 | 437967 | -62.763% | 5513281 | 790133 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.036 | 0e12171d242c353f364c455d6c648193a69cc0d6ed18f85c | 0 |
| spp_copper_slack | 45150711759 | -34.731% | 55884504 | 442133 | -62.409% | 5466196 | 789327 | 70641 | 1024 | 20829 | 49812 | 1470 | 0 | 10448 | 0.036 | 0e12171d242c353f364c455d6c648193a69cc0d6ed18f85c | 0 |

Interpretation:

- Verification hash agreement: yes (0e12171d242c353f364c455d6c648193a69cc0d6ed18f85c).
- Verification byte-count agreement: 0; when this is 0, treat the hash as a run-consistency marker and rely on return code plus completed test lines rather than as a result-content checksum.
- Return-code agreement: yes (0).
- Naive DMP CTLW misses: 12802; COPPER CLPD-64K+PEB CTLW misses: 983; reduction: 92.3%.
- SPP+COPPER-slack companion CTLW misses: 1470. Plain SPP has no pointer-provenance CTLW counter, so this is a bounded companion-safety cost rather than a reduction comparison.
- Translation faults: naive=0, COPPER=0, SPP=0, SPP+COPPER-slack=0.
- Scope note: this is a small, deterministic, upstream benchmark component rather than a full-scale SQLite performance run. It strengthens external validity because the code is public and unmodified, not because it represents all database workloads.

status=PASS
