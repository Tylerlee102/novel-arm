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

Input tag: `tcp_netns_process_key1`.

| Policy | Transport | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | tcp_loopback_netns_process | 7411208040 | 0.000% | 13298365 | 83836 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x57e171797b39f199 | 0 |
| naive | tcp_loopback_netns_process | 7464677184 | 0.721% | 13316465 | 83367 | -0.559% | 4233 | 926 | 11418 | 811 | 11418 | 0 | 7185 | 0 | 0 | 0x57e171797b39f199 | 0 |
| copper_clpd64k_peb | tcp_loopback_netns_process | 7413905673 | 0.036% | 13279767 | 82911 | -1.103% | 3525 | 894 | 14057 | 765 | 3636 | 10421 | 111 | 0 | 0 | 0x57e171797b39f199 | 0 |
| spp | tcp_loopback_netns_process | 6686127513 | -9.784% | 12895746 | 57719 | -31.152% | 213870 | 31736 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x57e171797b39f199 | 0 |
| spp_copper_slack | tcp_loopback_netns_process | 6678665649 | -9.884% | 12889814 | 57570 | -31.330% | 216083 | 31949 | 19944 | 615 | 3175 | 16769 | 131 | 0 | 0 | 0x57e171797b39f199 | 0 |

Interpretation:

- Checksum agreement: yes (0x57e171797b39f199).
- Transport modes observed: tcp_loopback_netns_process.
- Naive DMP CTLW misses: 7185; COPPER CLPD-64K+PEB CTLW misses: 111; reduction: 98.5%.
- SPP+COPPER slack CTLW misses: 131; reduction versus naive DMP: 98.2%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is real libssl handshake and TLS record execution through the guest dynamic loader. The transport tag determines how strongly the result can be claimed.

- All policies used process-separated AF_INET TCP loopback inside a private user/network namespace with a forked TLS server process. Process-server flag values: 1; process TCP pairs: 5; child failures: 0. This is stronger than the in-process loopback service driver, but still a bounded local server/client harness rather than a production deployment.

status=TCP_NETNS_PROCESS_PASS
