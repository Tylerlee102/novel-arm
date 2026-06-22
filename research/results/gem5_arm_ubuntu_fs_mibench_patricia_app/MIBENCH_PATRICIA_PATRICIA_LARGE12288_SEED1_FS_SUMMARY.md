# MiBench Patricia AArch64 Full-System Summary

This workload uses the public MiBench network/patricia Patricia trie
implementation and a public MiBench packet-field input selected by
the run script. The
driver is COPPER-specific only in that it emits a deterministic
checksum and clean return code for gem5 full-system evaluation.

Input tag: `patricia_large12288_seed1`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 79932817836 | 0.000% | 369220137 | 1201292 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xe4dc12fd1dcd52b0 | 0 |
| naive | 80054884980 | 0.153% | 369257737 | 1062165 | -11.581% | 187538 | 1393 | 205456 | 18329 | 205456 | 0 | 17909 | 0 | 0 | 0xe4dc12fd1dcd52b0 | 0 |
| copper_clpd64k_peb | 80055004860 | 0.153% | 369244981 | 1064120 | -11.419% | 170570 | 1099 | 209336 | 12892 | 170968 | 38368 | 398 | 0 | 18558 | 0xe4dc12fd1dcd52b0 | 0 |
| spp | 68434692804 | -14.385% | 368899809 | 671627 | -44.091% | 2450616 | 434972 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xe4dc12fd1dcd52b0 | 0 |
| spp_copper_slack | 68411091429 | -14.414% | 368928557 | 624340 | -48.028% | 2511367 | 435891 | 507888 | 8172 | 60782 | 447106 | 567 | 0 | 10451 | 0xe4dc12fd1dcd52b0 | 0 |

Workload shape:

- Public input records consumed: 12288 of limit 12288.
- Inserted trie nodes: 12288; duplicates: 0.
- Lookup operations: 24576; rounds: 1; found: 24576; misses: 0.

Interpretation:

- Checksum agreement: yes (0xe4dc12fd1dcd52b0).
- Return-code agreement: yes (0).
- Naive DMP CTLW misses: 17909; COPPER CLPD-64K+PEB CTLW misses: 398; reduction: 97.8%.
- SPP+COPPER slack CTLW misses: 567; reduction versus naive DMP: 96.8%.
- SPP+COPPER slack tick gap versus SPP: -0.030 percentage points.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is public MiBench Patricia trie benchmark-family evidence, not SPEC and not production network routing software.

status=PASS
