# zlib AArch64 Full-System Summary

This workload is a deterministic native AArch64 Linux ROI that calls
public zlib compression and decompression through the Ubuntu guest
library stack over buffers containing address-shaped words as data.

Input tag: `codex_raw_zlib_tiny`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 9642814533 | 0.000% | 35811793 | 114832 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x7dbec8e3fca9fb9b | 0 |
| stride | 9058843089 | -6.056% | 35435781 | 73422 | -36.061% | 43033 | 22075 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x7dbec8e3fca9fb9b | 0 |
| naive | 9638066286 | -0.049% | 35811793 | 114806 | -0.023% | 2108 | 357 | 10660 | 627 | 10660 | 0 | 8545 | 0 | 0 | 0x7dbec8e3fca9fb9b | 0 |
| copper_clpd64k_peb | 9642499182 | -0.003% | 35811945 | 114777 | -0.048% | 1075 | 196 | 11298 | 598 | 1119 | 10179 | 44 | 0 | 17733 | 0x7dbec8e3fca9fb9b | 0 |
| dcpt | 8412884694 | -12.755% | 35061029 | 70845 | -38.306% | 426584 | 41599 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x7dbec8e3fca9fb9b | 0 |
| spp | 8119250622 | -15.800% | 35258637 | 57202 | -50.186% | 359965 | 54325 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x7dbec8e3fca9fb9b | 0 |
| ampm | 8311111236 | -13.810% | 35050821 | 68983 | -39.927% | 510502 | 53600 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x7dbec8e3fca9fb9b | 0 |
| spp_copper_slack | 8113005873 | -15.865% | 35258845 | 57180 | -50.206% | 360740 | 54371 | 16493 | 411 | 812 | 15681 | 41 | 0 | 10172 | 0x7dbec8e3fca9fb9b | 0 |

Workload shape:

- Input bytes: 4096; rounds: 1; compression level: 1.
- Address-shaped input words: 128; total compressed bytes across rounds: 4082; zlib CRC aggregate: 0xe6242efa.

Interpretation:

- Checksum agreement: yes (0x7dbec8e3fca9fb9b).
- Return-code agreement: yes (0).
- Naive DMP CTLW misses: 8545; COPPER CLPD-64K+PEB CTLW misses: 44; reduction: 99.5%.
- SPP+COPPER slack CTLW misses: 41; reduction versus naive DMP: 99.5%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is a public compression-library point, not a production server workload.

status=PASS
