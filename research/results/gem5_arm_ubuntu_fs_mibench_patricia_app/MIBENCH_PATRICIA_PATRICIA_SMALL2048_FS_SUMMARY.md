# MiBench Patricia AArch64 Full-System Summary

This workload uses the public MiBench network/patricia Patricia trie
implementation and the public `small.udp` packet-field input. The
driver is COPPER-specific only in that it emits a deterministic
checksum and clean return code for gem5 full-system evaluation.

Input tag: `patricia_small2048`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 21899607138 | 0.000% | 101016983 | 302886 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x11f999a2549d757f | 0 |
| naive | 21922426296 | 0.104% | 100989719 | 288912 | -4.614% | 24325 | 809 | 38349 | 3906 | 38349 | 0 | 14014 | 0 | 0 | 0x11f999a2549d757f | 0 |
| copper_clpd64k_peb | 21924058995 | 0.112% | 100989927 | 289122 | -4.544% | 19952 | 452 | 40071 | 3039 | 20133 | 19938 | 181 | 0 | 17973 | 0x11f999a2549d757f | 0 |
| spp | 19206605169 | -12.297% | 100781679 | 165429 | -45.382% | 805468 | 137362 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x11f999a2549d757f | 0 |
| spp_copper_slack | 19213131303 | -12.267% | 100781679 | 162138 | -46.469% | 810973 | 137420 | 83933 | 1985 | 6588 | 77345 | 422 | 0 | 10185 | 0x11f999a2549d757f | 0 |

Workload shape:

- Public input records consumed: 2048 of limit 2048.
- Inserted trie nodes: 2048; duplicates: 0.
- Lookup operations: 4096; rounds: 1; found: 4096; misses: 0.

Interpretation:

- Checksum agreement: yes (0x11f999a2549d757f).
- Return-code agreement: yes (0).
- Naive DMP CTLW misses: 14014; COPPER CLPD-64K+PEB CTLW misses: 181; reduction: 98.7%.
- SPP+COPPER slack CTLW misses: 422; reduction versus naive DMP: 97.0%.
- SPP+COPPER slack tick gap versus SPP: +0.030 percentage points.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is public MiBench Patricia trie benchmark-family evidence, not SPEC and not production network routing software.

status=PASS
