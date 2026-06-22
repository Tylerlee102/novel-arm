# MiBench Patricia AArch64 Full-System Summary

This workload uses the public MiBench network/patricia Patricia trie
implementation and the public `small.udp` packet-field input. The
driver is COPPER-specific only in that it emits a deterministic
checksum and clean return code for gem5 full-system evaluation.

Input tag: `patricia_small8192`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 54803550924 | 0.000% | 258895374 | 808671 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xd4f96d52a9711657 | 0 |
| naive | 54840336435 | 0.067% | 258911078 | 725045 | -10.341% | 116431 | 1156 | 132919 | 12502 | 132919 | 0 | 16478 | 0 | 0 | 0xd4f96d52a9711657 | 0 |
| copper_clpd64k_peb | 54835676766 | 0.059% | 258897106 | 725984 | -10.225% | 104197 | 769 | 135607 | 8920 | 104442 | 31165 | 245 | 0 | 17973 | 0xd4f96d52a9711657 | 0 |
| spp | 47488079718 | -13.349% | 258749678 | 457216 | -43.461% | 1699627 | 304565 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xd4f96d52a9711657 | 0 |
| spp_copper_slack | 47515387383 | -13.299% | 258749590 | 428648 | -46.994% | 1739081 | 304467 | 325361 | 6129 | 39627 | 285734 | 379 | 0 | 10185 | 0xd4f96d52a9711657 | 0 |

Workload shape:

- Public input records consumed: 8192 of limit 8192.
- Inserted trie nodes: 8192; duplicates: 0.
- Lookup operations: 16384; rounds: 1; found: 16384; misses: 0.

Interpretation:

- Checksum agreement: yes (0xd4f96d52a9711657).
- Return-code agreement: yes (0).
- Naive DMP CTLW misses: 16478; COPPER CLPD-64K+PEB CTLW misses: 245; reduction: 98.5%.
- SPP+COPPER slack CTLW misses: 379; reduction versus naive DMP: 97.7%.
- SPP+COPPER slack tick gap versus SPP: +0.050 percentage points.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is public MiBench Patricia trie benchmark-family evidence, not SPEC and not production network routing software.

status=PASS
