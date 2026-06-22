# OpenSSL libssl TLS Socket AArch64 Full-System Summary

This workload is a deterministic native AArch64 Linux ROI that calls
OpenSSL libssl's TLS 1.2 PSK handshake and TLS record read/write path
over a nonblocking Linux AF_UNIX socketpair while maintaining session hash/LRU metadata and
pointer-shaped ticket words loaded as data.

Input tag: `socket_smoke`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 11359378251 | 0.000% | 11481715 | 193905 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xab75647a27a441b7 | 0 |
| naive | 11285084286 | -0.654% | 11481679 | 189584 | -2.228% | 26796 | 6016 | 43350 | 685 | 43350 | 0 | 16554 | 0 | 0 | 0xab75647a27a441b7 | 0 |
| copper_clpd64k_peb | 11275915131 | -0.735% | 11481661 | 189140 | -2.457% | 29342 | 6360 | 64180 | 416 | 29486 | 34694 | 144 | 0 | 0 | 0xab75647a27a441b7 | 0 |
| spp | 11111643567 | -2.181% | 11478465 | 109564 | -43.496% | 748403 | 109119 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xab75647a27a441b7 | 0 |
| spp_copper_slack | 11107247967 | -2.220% | 11478554 | 109454 | -43.553% | 773613 | 109610 | 122551 | 480 | 31590 | 90961 | 296 | 0 | 0 | 0xab75647a27a441b7 | 0 |

Interpretation:

- Checksum agreement: yes (0xab75647a27a441b7).
- Naive DMP CTLW misses: 16554; COPPER CLPD-64K+PEB CTLW misses: 144; reduction: 99.1%.
- SPP+COPPER slack CTLW misses: 296; reduction versus naive DMP: 98.2%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is real libssl handshake and TLS record execution through the guest dynamic loader over Linux sockets. It is stronger than the memory-BIO path, but still an in-process socketpair service driver rather than a production TCP/TLS server.

status=PASS
