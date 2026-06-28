# zlib AArch64 Full-System Summary

This workload is a deterministic native AArch64 Linux ROI that calls
public zlib compression and decompression through the Ubuntu guest
library stack over buffers containing address-shaped words as data.

Input tag: `codex_raw_zlib_tiny`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 9642814533 | 0.000% | 35811793 | 114832 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x7dbec8e3fca9fb9b | 0 |
| copper_clpd64k_peb | 9642499182 | -0.003% | 35811945 | 114777 | -0.048% | 1075 | 196 | 11298 | 598 | 1119 | 10179 | 44 | 0 | 17733 | 0x7dbec8e3fca9fb9b | 0 |

Workload shape:

- Input bytes: 4096; rounds: 1; compression level: 1.
- Address-shaped input words: 128; total compressed bytes across rounds: 4082; zlib CRC aggregate: 0xe6242efa.

Interpretation:

- Checksum agreement: yes (0x7dbec8e3fca9fb9b).
- Return-code agreement: yes (0).
- Naive DMP CTLW misses: not run; COPPER CLPD-64K+PEB CTLW misses: 44; reduction: NA (comparison row absent).
- SPP+COPPER slack CTLW misses: not run; reduction versus naive DMP: NA (comparison row absent).
- Naive DMP translation faults: not run; COPPER CLPD-64K+PEB translation faults: 0.
- This is a public compression-library point, not a production server workload.

status=PASS
