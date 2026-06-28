# Cache-Service AArch64 Full-System Service-Style Summary

This workload is a deterministic memcached-like native AArch64 Linux ROI:
a hash table, doubly-linked hash chains, an LRU list, hit/miss updates,
evictions, and bounded hot-list scans. Payload fields contain pointer-shaped 64-bit words that are loaded and checksummed but never used as architectural addresses.

Input tag: `codex_raw_smoke_seed8`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 4130730468 | 0.000% | 3613698 | 52374 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x2dcec9e2a2c74de5 | 0 |
| copper_clpd64k_peb | 4127315886 | -0.083% | 3613698 | 52351 | -0.044% | 664 | 119 | 5498 | 410 | 686 | 4812 | 22 | 0 | 17742 | 0x2dcec9e2a2c74de5 | 0 |

Interpretation:

- Checksum agreement: yes (0x2dcec9e2a2c74de5).
- Naive DMP CTLW misses: 0; COPPER CLPD-64K+PEB CTLW misses: 22; reduction: 0.0%.
- SPP+COPPER slack CTLW misses: 0; reduction versus naive DMP: 0.0%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is a bounded service-style micro-application, not a production memcached server, but it exercises a cache-service hash/LRU update pattern that is distinct from the parser/database workload.

status=PASS
