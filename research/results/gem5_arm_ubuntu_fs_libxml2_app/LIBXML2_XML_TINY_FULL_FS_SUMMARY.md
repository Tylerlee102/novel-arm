# libxml2 XML AArch64 Full-System Summary

This workload is a deterministic native AArch64 Linux ROI that calls
the public libxml2 XML parser and serializer through the Ubuntu guest
library stack over XML records containing address-shaped words as data.

Input tag: `xml_tiny_full`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 18092312577 | 0.000% | 71467594 | 208708 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x45392e595faf2f7d | 0 |
| naive | 18102255291 | 0.055% | 71467734 | 208586 | -0.058% | 5066 | 729 | 17831 | 1012 | 17831 | 0 | 12758 | 0 | 0 | 0x45392e595faf2f7d | 0 |
| copper_clpd64k_peb | 18099782766 | 0.041% | 71468170 | 208541 | -0.080% | 2949 | 496 | 19221 | 918 | 3088 | 16133 | 139 | 0 | 17742 | 0x45392e595faf2f7d | 0 |
| spp | 15583091310 | -13.869% | 71471273 | 118118 | -43.405% | 615404 | 96084 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x45392e595faf2f7d | 0 |
| spp_copper_slack | 15589464930 | -13.834% | 71472025 | 117947 | -43.487% | 617751 | 96653 | 30199 | 597 | 2821 | 27378 | 136 | 0 | 10256 | 0x45392e595faf2f7d | 0 |

Workload shape:

- XML records: 16; rounds: 1; parse/dump scans per round: 1.
- XML bytes generated: 3286; serialized bytes observed: 3270; address-shaped XML words: 32.

Interpretation:

- Checksum agreement: yes (0x45392e595faf2f7d).
- Return-code agreement: yes (0).
- Naive DMP CTLW misses: 12758; COPPER CLPD-64K+PEB CTLW misses: 139; reduction: 98.9%.
- SPP+COPPER slack CTLW misses: 136; reduction versus naive DMP: 98.9%.
- SPP tick delta: -13.869%; SPP+COPPER slack tick delta: -13.834%; slack gap: 0.035 percentage points.
- COPPER CLPD-64K+PEB translation faults: 0; SPP+COPPER slack translation faults: 0.
- This is a public XML parser/serializer library point. It is stronger than a generated parser microbenchmark, but it is still a bounded in-memory XML harness rather than a production XML service.

status=PASS
