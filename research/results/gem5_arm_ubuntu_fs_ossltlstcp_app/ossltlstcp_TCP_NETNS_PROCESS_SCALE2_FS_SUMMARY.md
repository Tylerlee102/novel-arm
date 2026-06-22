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

Input tag: `tcp_netns_process_scale2`.

| Policy | Transport | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | tcp_loopback_netns_process | 17672403906 | 0.000% | 31092924 | 258108 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x703cb54ece76864c | 0 |
| naive | tcp_loopback_netns_process | 17630520498 | -0.237% | 31084894 | 255644 | -0.955% | 15809 | 3446 | 39689 | 2256 | 39689 | 0 | 23880 | 0 | 0 | 0x703cb54ece76864c | 0 |
| copper_clpd64k_peb | tcp_loopback_netns_process | 17602881165 | -0.393% | 31002161 | 254936 | -1.229% | 14551 | 3413 | 50313 | 2066 | 14936 | 35377 | 385 | 0 | 0 | 0x703cb54ece76864c | 0 |
| spp | tcp_loopback_netns_process | 15665880105 | -11.354% | 29927043 | 163330 | -36.720% | 709759 | 113755 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x703cb54ece76864c | 0 |
| spp_copper_slack | tcp_loopback_netns_process | 15647120883 | -11.460% | 29894225 | 163345 | -36.714% | 715847 | 113965 | 74109 | 1520 | 11221 | 62888 | 364 | 0 | 0 | 0x703cb54ece76864c | 0 |

Interpretation:

- Checksum agreement: yes (0x703cb54ece76864c).
- Transport modes observed: tcp_loopback_netns_process.
- Naive DMP CTLW misses: 23880; COPPER CLPD-64K+PEB CTLW misses: 385; reduction: 98.4%.
- SPP+COPPER slack CTLW misses: 364; reduction versus naive DMP: 98.5%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is real libssl handshake and TLS record execution through the guest dynamic loader. The transport tag determines how strongly the result can be claimed.

- All policies used process-separated AF_INET TCP loopback inside a private user/network namespace with a forked TLS server process. Process-mode rows: 1; process TCP pairs: 20; child failures: 0. This is stronger than the in-process loopback service driver, but still a bounded local server/client harness rather than a production deployment.

status=TCP_NETNS_PROCESS_PASS
