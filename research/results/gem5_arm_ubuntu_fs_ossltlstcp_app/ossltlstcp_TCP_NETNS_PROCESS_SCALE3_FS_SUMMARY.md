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

Input tag: `tcp_netns_process_scale3`.

| Policy | Transport | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | tcp_loopback_netns_process | 31539975120 | 0.000% | 54768776 | 489192 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x46e083abee222484 | 0 |
| naive | tcp_loopback_netns_process | 31419564318 | -0.382% | 54634883 | 485515 | -0.752% | 31177 | 6845 | 71154 | 4242 | 71154 | 0 | 39977 | 0 | 0 | 0x46e083abee222484 | 0 |
| copper_clpd64k_peb | tcp_loopback_netns_process | 31371553044 | -0.534% | 54466212 | 481765 | -1.518% | 29195 | 6855 | 92106 | 3861 | 29905 | 62201 | 710 | 0 | 0 | 0x46e083abee222484 | 0 |
| spp | tcp_loopback_netns_process | 27514734723 | -12.762% | 51952386 | 294257 | -39.848% | 1484756 | 233020 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x46e083abee222484 | 0 |
| spp_copper_slack | tcp_loopback_netns_process | 27512517276 | -12.769% | 51913605 | 294099 | -39.881% | 1487927 | 232460 | 148024 | 2539 | 21449 | 126575 | 591 | 0 | 0 | 0x46e083abee222484 | 0 |

Interpretation:

- Checksum agreement: yes (0x46e083abee222484).
- Transport modes observed: tcp_loopback_netns_process.
- Naive DMP CTLW misses: 39977; COPPER CLPD-64K+PEB CTLW misses: 710; reduction: 98.2%.
- SPP+COPPER slack CTLW misses: 591; reduction versus naive DMP: 98.5%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is real libssl handshake and TLS record execution through the guest dynamic loader. The transport tag determines how strongly the result can be claimed.

- All policies used process-separated AF_INET TCP loopback inside a private user/network namespace with a forked TLS server process. Process-mode rows: 1; process TCP pairs: 40; child failures: 0. This is stronger than the in-process loopback service driver, but still a bounded local server/client harness rather than a production deployment.

status=TCP_NETNS_PROCESS_PASS
