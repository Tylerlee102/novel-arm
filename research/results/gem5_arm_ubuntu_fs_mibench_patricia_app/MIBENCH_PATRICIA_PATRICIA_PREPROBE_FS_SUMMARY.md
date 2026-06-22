# MiBench Patricia AArch64 Full-System Summary

This workload uses the public MiBench network/patricia Patricia trie
implementation and the public `small.udp` packet-field input. The
driver is COPPER-specific only in that it emits a deterministic
checksum and clean return code for gem5 full-system evaluation.

Input tag: `patricia_preprobe`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 14915580489 | 0.000% | 53237424 | 183984 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xe9324f49c2b21a34 | 0 |
| naive | 14912787285 | -0.019% | 53237696 | 183799 | -0.101% | 3967 | 685 | 15968 | 1239 | 15968 | 0 | 11992 | 0 | 0 | 0xe9324f49c2b21a34 | 0 |
| copper_clpd64k_peb | 14922776286 | 0.048% | 53237844 | 183874 | -0.060% | 1982 | 353 | 17159 | 1201 | 2067 | 15092 | 85 | 0 | 17973 | 0xe9324f49c2b21a34 | 0 |
| spp | 12555689742 | -15.822% | 53110756 | 88950 | -51.653% | 600438 | 93564 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xe9324f49c2b21a34 | 0 |
| spp_copper_slack | 12551815620 | -15.848% | 53110756 | 88887 | -51.688% | 601092 | 93658 | 25121 | 791 | 1481 | 23640 | 102 | 0 | 10185 | 0xe9324f49c2b21a34 | 0 |

Workload shape:

- Public input records consumed: 128 of limit 128.
- Inserted trie nodes: 128; duplicates: 0.
- Lookup operations: 256; rounds: 1; found: 256; misses: 0.

Interpretation:

- Checksum agreement: yes (0xe9324f49c2b21a34).
- Return-code agreement: yes (0).
- Naive DMP CTLW misses: 11992; COPPER CLPD-64K+PEB CTLW misses: 85; reduction: 99.3%.
- SPP+COPPER slack CTLW misses: 102; reduction versus naive DMP: 99.1%.
- SPP+COPPER slack tick gap versus SPP: -0.026 percentage points.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is public MiBench Patricia trie benchmark-family evidence, not SPEC and not production network routing software.

status=PASS
