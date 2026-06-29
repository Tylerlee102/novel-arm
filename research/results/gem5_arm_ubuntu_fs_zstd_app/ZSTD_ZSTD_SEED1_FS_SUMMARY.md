# Zstd AArch64 Full-System Summary

This workload is a deterministic native AArch64 Linux ROI that calls
public libzstd compression and decompression through the Ubuntu guest
library stack over buffers containing address-shaped words as data.

Input tag: `zstd_seed1`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 9726151113 | 0.000% | 37163891 | 115631 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x22c3e1e7b9a49990 | 0 |
| naive | 9723079521 | -0.032% | 37163891 | 115535 | -0.083% | 2118 | 370 | 11597 | 626 | 11597 | 0 | 9239 | 0 | 0 | 0x22c3e1e7b9a49990 | 0 |
| copper_clpd64k_peb | 9710575371 | -0.160% | 37150751 | 115316 | -0.272% | 1095 | 202 | 12205 | 582 | 1144 | 11061 | 49 | 0 | 17737 | 0x22c3e1e7b9a49990 | 0 |
| spp | 8183902239 | -15.857% | 36432391 | 54563 | -52.813% | 379269 | 58197 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x22c3e1e7b9a49990 | 0 |
| spp_copper_slack | 8177698782 | -15.921% | 36432391 | 54444 | -52.916% | 380091 | 58426 | 17275 | 408 | 827 | 16448 | 51 | 0 | 10172 | 0x22c3e1e7b9a49990 | 0 |

Workload shape:

- Input bytes: 8192; rounds: 2; compression level: 1.
- Address-shaped input words: 256; total compressed bytes across rounds: 16097.

Interpretation:

- Checksum agreement: yes (0x22c3e1e7b9a49990).
- Return-code agreement: yes (0).
- Naive DMP CTLW misses: 9239; COPPER CLPD-64K+PEB CTLW misses: 49; reduction: 99.5%.
- SPP+COPPER slack CTLW misses: 51; reduction versus naive DMP: 99.4%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is a public compression-library point, not a production server workload.

status=PASS
