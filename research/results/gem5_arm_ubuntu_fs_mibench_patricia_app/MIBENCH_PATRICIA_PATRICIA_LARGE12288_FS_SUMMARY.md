# MiBench Patricia AArch64 Full-System Summary

This workload uses the public MiBench network/patricia Patricia trie
implementation and a public MiBench packet-field input selected by
the run script. The
driver is COPPER-specific only in that it emits a deterministic
checksum and clean return code for gem5 full-system evaluation.

Input tag: `patricia_large12288`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 79942105539 | 0.000% | 369239185 | 1196911 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x60874357358c1fc4 | 0 |
| naive | 80059188006 | 0.146% | 369273217 | 1059190 | -11.506% | 184656 | 1451 | 203119 | 18281 | 203119 | 0 | 18454 | 0 | 0 | 0x60874357358c1fc4 | 0 |
| copper_clpd64k_peb | 80064448407 | 0.153% | 369260389 | 1061146 | -11.343% | 167486 | 1103 | 207633 | 12894 | 167867 | 39766 | 381 | 0 | 18558 | 0x60874357358c1fc4 | 0 |
| spp | 68532940458 | -14.272% | 368944021 | 673883 | -43.698% | 2429559 | 428396 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x60874357358c1fc4 | 0 |
| spp_copper_slack | 68560875828 | -14.237% | 368944193 | 625181 | -47.767% | 2499727 | 429498 | 510209 | 8321 | 64119 | 446090 | 635 | 0 | 10451 | 0x60874357358c1fc4 | 0 |

Workload shape:

- Public input records consumed: 12288 of limit 12288.
- Inserted trie nodes: 12288; duplicates: 0.
- Lookup operations: 24576; rounds: 1; found: 24576; misses: 0.

Interpretation:

- Checksum agreement: yes (0x60874357358c1fc4).
- Return-code agreement: yes (0).
- Naive DMP CTLW misses: 18454; COPPER CLPD-64K+PEB CTLW misses: 381; reduction: 97.9%.
- SPP+COPPER slack CTLW misses: 635; reduction versus naive DMP: 96.6%.
- SPP+COPPER slack tick gap versus SPP: +0.035 percentage points.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is public MiBench Patricia trie benchmark-family evidence, not SPEC and not production network routing software.

status=PASS
