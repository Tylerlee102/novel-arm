# OpenSSL libssl TLS TCP Loopback AArch64 Full-System Summary

This workload is a deterministic native AArch64 Linux ROI that calls
OpenSSL libssl's TLS 1.2 PSK handshake and TLS record read/write path
over a nonblocking Linux TCP loopback connection when the guest permits it.
If the guest loopback device is unavailable, the driver uses an explicitly tagged AF_UNIX
fallback so the TLS record path can still be measured without pretending that TCP worked.
The workload maintains session hash/LRU metadata and
pointer-shaped ticket words loaded as data.

Input tag: `tcp_fallback_probe`.

| Policy | Transport | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | af_unix_fallback | 6736297626 | 0.000% | 6223377 | 102959 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xeb221e7bd6b9662b | 0 |
| naive | af_unix_fallback | 6686185788 | -0.744% | 6223377 | 100811 | -2.086% | 13629 | 3029 | 22468 | 535 | 22468 | 0 | 8839 | 0 | 0 | 0xeb221e7bd6b9662b | 0 |
| copper_clpd64k_peb | af_unix_fallback | 6687868104 | -0.719% | 6223377 | 100647 | -2.246% | 14609 | 3131 | 32931 | 404 | 14786 | 18145 | 177 | 0 | 0 | 0xeb221e7bd6b9662b | 0 |
| spp | af_unix_fallback | 6526342458 | -3.117% | 6223377 | 62894 | -38.914% | 334346 | 52305 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xeb221e7bd6b9662b | 0 |
| spp_copper_slack | af_unix_fallback | 6537473982 | -2.952% | 6223377 | 63386 | -38.436% | 350087 | 52147 | 57853 | 453 | 14465 | 43388 | 245 | 0 | 0 | 0xeb221e7bd6b9662b | 0 |

Interpretation:

- Checksum agreement: yes (0xeb221e7bd6b9662b).
- Transport modes observed: af_unix_fallback.
- Naive DMP CTLW misses: 8839; COPPER CLPD-64K+PEB CTLW misses: 177; reduction: 98.0%.
- SPP+COPPER slack CTLW misses: 245; reduction versus naive DMP: 97.2%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is real libssl handshake and TLS record execution through the guest dynamic loader. The transport tag determines how strongly the result can be claimed.

- The guest loopback interface was unavailable, so all policies used the explicit AF_UNIX fallback. Count this as tagged socket-backed libssl evidence and environment diagnosis, not as TCP-loopback benchmark evidence.

status=AF_UNIX_FALLBACK_PASS
