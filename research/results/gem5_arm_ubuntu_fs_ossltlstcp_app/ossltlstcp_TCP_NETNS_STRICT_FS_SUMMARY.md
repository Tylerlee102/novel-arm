# OpenSSL libssl TLS TCP Loopback AArch64 Full-System Summary

This workload is a deterministic native AArch64 Linux ROI that calls
OpenSSL libssl's TLS 1.2 PSK handshake and TLS record read/write path
over a nonblocking Linux TCP loopback connection when the guest permits it.
If the guest loopback device is unavailable, the driver first tries an explicitly tagged
private user/network-namespace TCP loopback path. If that is unavailable too, it uses an
explicitly tagged AF_UNIX
fallback so the TLS record path can still be measured without pretending that TCP worked.
The workload maintains session hash/LRU metadata and
pointer-shaped ticket words loaded as data.

Input tag: `tcp_netns_strict`.

| Policy | Transport | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | tcp_loopback_netns | 11286659376 | 0.000% | 12446637 | 128570 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xeb221e7bd6b9662b | 0 |
| naive | tcp_loopback_netns | 11241567513 | -0.400% | 12446376 | 126444 | -1.654% | 13493 | 2963 | 23138 | 529 | 23138 | 0 | 9645 | 0 | 0 | 0xeb221e7bd6b9662b | 0 |
| copper_clpd64k_peb | tcp_loopback_netns | 11236541544 | -0.444% | 12446430 | 126175 | -1.863% | 14761 | 3149 | 33940 | 403 | 14982 | 18958 | 221 | 0 | 0 | 0xeb221e7bd6b9662b | 0 |
| spp | tcp_loopback_netns | 10754086482 | -4.719% | 12436219 | 80112 | -37.690% | 432283 | 63509 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xeb221e7bd6b9662b | 0 |
| spp_copper_slack | tcp_loopback_netns | 10753432803 | -4.724% | 12436219 | 80342 | -37.511% | 443827 | 63466 | 59370 | 452 | 15000 | 44370 | 269 | 0 | 0 | 0xeb221e7bd6b9662b | 0 |

Interpretation:

- Checksum agreement: yes (0xeb221e7bd6b9662b).
- Transport modes observed: tcp_loopback_netns.
- Naive DMP CTLW misses: 9645; COPPER CLPD-64K+PEB CTLW misses: 221; reduction: 97.7%.
- SPP+COPPER slack CTLW misses: 269; reduction versus naive DMP: 97.2%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is real libssl handshake and TLS record execution through the guest dynamic loader. The transport tag determines how strongly the result can be claimed.

- All policies used AF_INET TCP loopback inside a private user/network namespace created by the benchmark process. This is real guest TCP socket execution and stronger than AF_UNIX fallback, but still an in-process loopback service driver rather than a production TCP/TLS server.

status=TCP_NETNS_PASS
