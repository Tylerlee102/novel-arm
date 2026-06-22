# OpenSSL libssl TLS Memory-BIO AArch64 Full-System Summary

This workload is a deterministic native AArch64 Linux ROI that calls
OpenSSL libssl's TLS 1.2 PSK handshake and TLS record read/write path
over paired memory BIOs while maintaining session hash/LRU metadata and
pointer-shaped ticket words loaded as data.

Input tag: `app_smoke`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 1866003795 | 0.000% | 1915254 | 28832 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x204756e92baedd9b | 0 |
| stride | 1879706745 | 0.734% | 1915254 | 27442 | -4.821% | 4402 | 1408 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x204756e92baedd9b | 0 |
| naive | 1856394081 | -0.515% | 1915254 | 28252 | -2.012% | 3546 | 781 | 5957 | 350 | 5957 | 0 | 2411 | 0 | 0 | 0x204756e92baedd9b | 0 |
| copper_clpd64k_peb | 1857241566 | -0.470% | 1915254 | 28171 | -2.293% | 3284 | 777 | 8394 | 326 | 3313 | 5081 | 29 | 0 | 0 | 0x204756e92baedd9b | 0 |
| dcpt | 1817420094 | -2.604% | 1915254 | 25614 | -11.161% | 39937 | 3485 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x204756e92baedd9b | 0 |
| spp | 1817222625 | -2.614% | 1915254 | 20610 | -28.517% | 65719 | 10787 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x204756e92baedd9b | 0 |
| ampm | 1837881945 | -1.507% | 1915254 | 23877 | -17.186% | 93172 | 8804 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x204756e92baedd9b | 0 |
| spp_copper_slack | 1817420094 | -2.604% | 1915254 | 20645 | -28.396% | 66542 | 10781 | 12835 | 346 | 2838 | 9997 | 54 | 0 | 0 | 0x204756e92baedd9b | 0 |

Interpretation:

- Checksum agreement: yes (0x204756e92baedd9b).
- Naive DMP CTLW misses: 2411; COPPER CLPD-64K+PEB CTLW misses: 29; reduction: 98.8%.
- SPP+COPPER slack CTLW misses: 54; reduction versus naive DMP: 97.8%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is real libssl handshake and TLS record execution through the guest dynamic loader, but it remains an in-process memory-BIO service driver rather than a production networked TLS server.

status=PASS
