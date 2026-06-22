# OpenSSL libssl TLS Memory-BIO AArch64 Full-System Summary

This workload is a deterministic native AArch64 Linux ROI that calls
OpenSSL libssl's TLS 1.2 PSK handshake and TLS record read/write path
over paired memory BIOs while maintaining session hash/LRU metadata and
pointer-shaped ticket words loaded as data.

Input tag: `app_medium`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 37934604090 | 0.000% | 44778789 | 718441 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xacd4c41671f9f25b | 0 |
| naive | 37638742248 | -0.780% | 44778789 | 700158 | -2.545% | 102813 | 23808 | 161793 | 1090 | 161793 | 0 | 58980 | 0 | 0 | 0xacd4c41671f9f25b | 0 |
| copper_clpd64k_peb | 37651790853 | -0.746% | 44778789 | 698640 | -2.756% | 118008 | 25850 | 246588 | 418 | 118733 | 127855 | 725 | 0 | 0 | 0xacd4c41671f9f25b | 0 |
| spp | 37933564464 | -0.003% | 44778789 | 381858 | -46.849% | 3631644 | 462439 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xacd4c41671f9f25b | 0 |
| spp_copper_slack | 37845013770 | -0.236% | 44778789 | 382988 | -46.692% | 3641492 | 463471 | 548474 | 486 | 145806 | 402668 | 1664 | 0 | 0 | 0xacd4c41671f9f25b | 0 |

Interpretation:

- Checksum agreement: yes (0xacd4c41671f9f25b).
- Naive DMP CTLW misses: 58980; COPPER CLPD-64K+PEB CTLW misses: 725; reduction: 98.8%.
- SPP+COPPER slack CTLW misses: 1664; reduction versus naive DMP: 97.2%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is real libssl handshake and TLS record execution through the guest dynamic loader, but it remains an in-process memory-BIO service driver rather than a production networked TLS server.

status=PASS
