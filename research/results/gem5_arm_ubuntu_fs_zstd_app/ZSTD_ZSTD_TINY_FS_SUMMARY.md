# Zstd AArch64 Full-System Summary

This workload is a deterministic native AArch64 Linux ROI that calls
public libzstd compression and decompression through the Ubuntu guest
library stack over buffers containing address-shaped words as data.

Input tag: `zstd_tiny`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 9725094504 | 0.000% | 37163139 | 115602 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x93d05761620949ad | 0 |
| naive | 9716717889 | -0.086% | 37163211 | 115534 | -0.059% | 2116 | 371 | 11595 | 625 | 11595 | 0 | 9239 | 0 | 0 | 0x93d05761620949ad | 0 |
| copper_clpd64k_peb | 9723338262 | -0.018% | 37164083 | 115576 | -0.022% | 1094 | 202 | 12215 | 585 | 1143 | 11072 | 49 | 0 | 17737 | 0x93d05761620949ad | 0 |
| spp | 8175813336 | -15.931% | 36432583 | 54519 | -52.839% | 379701 | 58289 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x93d05761620949ad | 0 |
| spp_copper_slack | 8193562236 | -15.748% | 36432531 | 54429 | -52.917% | 382426 | 58380 | 17266 | 409 | 822 | 16444 | 51 | 0 | 10172 | 0x93d05761620949ad | 0 |

Workload shape:

- Input bytes: 8192; rounds: 2; compression level: 1.
- Address-shaped input words: 256; total compressed bytes across rounds: 16084.

Interpretation:

- Checksum agreement: yes (0x93d05761620949ad).
- Return-code agreement: yes (0).
- Naive DMP CTLW misses: 9239; COPPER CLPD-64K+PEB CTLW misses: 49; reduction: 99.5%.
- SPP+COPPER slack CTLW misses: 51; reduction versus naive DMP: 99.4%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is a public compression-library point, not a production server workload.

status=PASS
