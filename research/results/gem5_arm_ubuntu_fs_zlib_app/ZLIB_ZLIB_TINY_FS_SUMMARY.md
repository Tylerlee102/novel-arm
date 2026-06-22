# zlib AArch64 Full-System Summary

This workload is a deterministic native AArch64 Linux ROI that calls
public zlib compression and decompression through the Ubuntu guest
library stack over buffers containing address-shaped words as data.

Input tag: `zlib_tiny`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 11081529378 | 0.000% | 45106549 | 140246 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xf5b59076d62b0a4a | 0 |
| naive | 11064164094 | -0.157% | 45120573 | 140320 | 0.053% | 2146 | 391 | 13489 | 628 | 13489 | 0 | 11336 | 0 | 0 | 0xf5b59076d62b0a4a | 0 |
| copper_clpd64k_peb | 11055484116 | -0.235% | 45120645 | 140303 | 0.041% | 1177 | 218 | 14164 | 583 | 1242 | 12922 | 65 | 0 | 17734 | 0xf5b59076d62b0a4a | 0 |
| spp | 9555242526 | -13.773% | 44838038 | 76531 | -45.431% | 413112 | 60429 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xf5b59076d62b0a4a | 0 |
| spp_copper_slack | 9551254851 | -13.809% | 44840146 | 76452 | -45.487% | 413491 | 60506 | 22148 | 446 | 857 | 21291 | 58 | 0 | 10174 | 0xf5b59076d62b0a4a | 0 |

Workload shape:

- Input bytes: 8192; rounds: 2; compression level: 1.
- Address-shaped input words: 256; total compressed bytes across rounds: 16219; zlib CRC aggregate: 0xc42fee06.

Interpretation:

- Checksum agreement: yes (0xf5b59076d62b0a4a).
- Return-code agreement: yes (0).
- Naive DMP CTLW misses: 11336; COPPER CLPD-64K+PEB CTLW misses: 65; reduction: 99.4%.
- SPP+COPPER slack CTLW misses: 58; reduction versus naive DMP: 99.5%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is a public compression-library point, not a production server workload.

status=PASS
