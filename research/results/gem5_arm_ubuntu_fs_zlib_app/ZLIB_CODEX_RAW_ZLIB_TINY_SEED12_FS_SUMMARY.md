# zlib AArch64 Full-System Summary

This workload is a deterministic native AArch64 Linux ROI that calls
public zlib compression and decompression through the Ubuntu guest
library stack over buffers containing address-shaped words as data.

Input tag: `codex_raw_zlib_tiny_seed12`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 9643846167 | 0.000% | 35794629 | 114800 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x4f26c4a660462fc1 | 0 |
| stride | 9059823108 | -6.056% | 35418545 | 73404 | -36.059% | 43004 | 22001 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x4f26c4a660462fc1 | 0 |
| naive | 9642168513 | -0.017% | 35795237 | 114789 | -0.010% | 2109 | 357 | 10596 | 628 | 10596 | 0 | 8480 | 0 | 0 | 0x4f26c4a660462fc1 | 0 |
| copper_clpd64k_peb | 9642222792 | -0.017% | 35795509 | 114767 | -0.029% | 1073 | 197 | 11239 | 596 | 1114 | 10125 | 41 | 0 | 17733 | 0x4f26c4a660462fc1 | 0 |
| dcpt | 8412813099 | -12.765% | 35043865 | 70811 | -38.318% | 426857 | 41633 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x4f26c4a660462fc1 | 0 |
| spp | 8118388818 | -15.818% | 35240849 | 57180 | -50.192% | 360678 | 54218 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x4f26c4a660462fc1 | 0 |
| ampm | 8311180833 | -13.819% | 35033657 | 68969 | -39.922% | 507601 | 53548 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x4f26c4a660462fc1 | 0 |
| spp_copper_slack | 8110767780 | -15.897% | 35241681 | 57173 | -50.198% | 362728 | 54365 | 16390 | 411 | 817 | 15573 | 44 | 0 | 10172 | 0x4f26c4a660462fc1 | 0 |

Workload shape:

- Input bytes: 4096; rounds: 1; compression level: 1.
- Address-shaped input words: 128; total compressed bytes across rounds: 4076; zlib CRC aggregate: 0xf1945caa.

Interpretation:

- Checksum agreement: yes (0x4f26c4a660462fc1).
- Return-code agreement: yes (0).
- Naive DMP CTLW misses: 8480; COPPER CLPD-64K+PEB CTLW misses: 41; reduction: 99.5%.
- SPP+COPPER slack CTLW misses: 44; reduction versus naive DMP: 99.5%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is a public compression-library point, not a production server workload.

status=PASS
