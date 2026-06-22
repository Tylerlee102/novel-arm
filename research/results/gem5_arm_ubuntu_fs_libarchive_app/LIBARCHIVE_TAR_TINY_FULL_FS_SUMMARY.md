# libarchive TAR AArch64 Full-System Summary

This workload is a deterministic native AArch64 Linux ROI that calls
the public libarchive TAR parser through the Ubuntu guest library
stack over in-memory archive entries containing address-shaped words as data.

Input tag: `tar_tiny_full`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 23272878492 | 0.000% | 85766702 | 309768 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x950941dc0c18ee4d | 0 |
| naive | 23230361718 | -0.183% | 85689770 | 308594 | -0.379% | 9625 | 2032 | 26723 | 886 | 26723 | 0 | 17091 | 0 | 0 | 0x950941dc0c18ee4d | 0 |
| copper_clpd64k_peb | 23241292110 | -0.136% | 85714610 | 307714 | -0.663% | 6490 | 1739 | 28308 | 756 | 6831 | 21477 | 341 | 0 | 17720 | 0x950941dc0c18ee4d | 0 |
| spp | 19570984092 | -15.906% | 85060418 | 197910 | -36.110% | 874677 | 126876 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x950941dc0c18ee4d | 0 |
| spp_copper_slack | 19570029048 | -15.911% | 85060202 | 196366 | -36.609% | 882654 | 128422 | 49172 | 581 | 7417 | 41755 | 233 | 0 | 10240 | 0x950941dc0c18ee4d | 0 |

Workload shape:

- TAR entries: 16; rounds: 1; archive scans per round: 1.
- Archive bytes generated: 17408; payload bytes read: 3302; address-shaped archive words: 32.

Interpretation:

- Checksum agreement: yes (0x950941dc0c18ee4d).
- Return-code agreement: yes (0).
- Naive DMP CTLW misses: 17091; COPPER CLPD-64K+PEB CTLW misses: 341; reduction: 98.0%.
- SPP+COPPER slack CTLW misses: 233; reduction versus naive DMP: 98.6%.
- SPP tick delta: -15.906%; SPP+COPPER slack tick delta: -15.911%; slack gap: -0.004 percentage points.
- COPPER CLPD-64K+PEB translation faults: 0; SPP+COPPER slack translation faults: 0.
- This is a public archive-parser library point. It is stronger than a generated parser microbenchmark, but it is still a bounded in-memory TAR harness rather than a production archive extraction service.

status=PASS
