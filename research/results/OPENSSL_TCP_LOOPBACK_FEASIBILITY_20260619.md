# OpenSSL TCP Loopback Feasibility Note

Date: 2026-06-20

Purpose: record the attempt to move from OpenSSL libssl memory-BIO and
AF_UNIX socketpair evidence to a TCP loopback TLS path under the same ARM64
full-system gem5 boot, including the later private user/network namespace
workaround that succeeded in strict TCP mode.

## What Was Built

- Source: `research/aarch64_openssl_tls_tcp_workload.c`.
- Builder: `research/build_openssl_tls_tcp_workload_aarch64.py`.
- Binary: `research/bin/aarch64_openssl_tls_tcp_workload`.
- Build result: `build_status=PASS`.
- Runner controls added during diagnosis:
  `--native-pre-command` in `research/gem5_arm_ubuntu_fs_copper_workload.py`
  and `NATIVE_PRE_COMMAND`/`NO_SYSTEMD` in
  `research/run_openssl_tls_tcp_fs.sh`.
- Strict TCP controls added after the initial failures:
  `--strict-tcp`, `--no-netns-loopback`, `STRICT_TCP`,
  `NO_NETNS_LOOPBACK`, and `EXTRA_TCP_ARGS`.

The workload uses OpenSSL libssl TLS 1.2 PSK handshake and record I/O, session
hash/LRU metadata, pointer-shaped ticket words, and guest ROI markers. The new
transport setup tries to create a TCP listener and client connection before the
ROI, then hands the connected file descriptors to OpenSSL with `SSL_set_fd`.

## Local Full-System Attempts

| Tag | Transport setup | Result |
|---|---|---|
| `tcp_smoke` | Initial 127.0.0.1 bind/connect path | Failed before TLS exchange; no errno instrumentation in this first attempt. |
| `tcp_smoke2` | Blocking connect/accept on 127.0.0.1 | `TCP loopback failed errno=99`; guest returned `rc=1`. |
| `tcp_smoke3` | Best-effort `lo` bring-up with `SIOCSIFFLAGS`, then 127.0.0.1 | `TCP loopback failed errno=99`; guest returned `rc=1`. |
| `tcp_smoke4` | Wildcard bind, connect to 127.0.0.1 | `TCP loopback failed errno=101`; guest returned `rc=1`. |
| `tcp_smoke5` | Wildcard bind and wildcard local connect | `TCP loopback failed errno=101`; guest returned `rc=1`. |
| `tcp_diag_lo` | Guest pre-command tries `ip link set lo up`, records routes/interfaces, then runs TCP workload | `RTNETLINK answers: Operation not permitted`; `lo` remains `state DOWN`; route table is empty; `TCP loopback failed errno=101`; guest returned `rc=1`. |
| `tcp_diag_systemd` | Re-ran without `no_systemd=true` to let normal startup bring up networking | Systemd boot started, including `systemd-networkd.socket`, but did not reach the readfile workload within a 20-minute wall-clock timeout on this host; run was stopped and is not counted. |
| `tcp_fallback_probe` | Host-namespace TCP attempt plus explicit AF_UNIX fallback | All key policies completed with `transport=af_unix_fallback`; this is counted only as tagged socket-backed TLS-library fallback evidence, not TCP-loopback evidence. |
| `tcp_netns_strict` | Strict TCP mode; benchmark process creates a private user namespace, then a private network namespace, raises `lo`, and uses AF_INET TCP loopback | All key policies completed with `transport=tcp_loopback_netns`, `strict_tcp=1`, `afunix_fallback_pairs=0`, checksum `0xeb221e7bd6b9662b`, and `rc=0`. COPPER reduced naive-DMP CTLW misses from 9,645 to 221; SPP+COPPER slack reduced them to 269; both had zero translation faults. |
| `tcp_netns_process_key1` | Strict process-server TCP mode; benchmark process creates a private user/network namespace, then forks a TLS server process and runs the parent as TLS client over AF_INET loopback | All key policies completed with `transport=tcp_loopback_netns_process`, `process_server=1`, `process_pairs=1`, `child_failures=0`, `afunix_fallback_pairs=0`, checksum `0x57e171797b39f199`, and `rc=0`. COPPER reduced naive-DMP CTLW misses from 7,185 to 111; SPP+COPPER slack reduced them to 131; both had zero translation faults. |
| `OPENSSL_TCP_PROCESS_SEED_STABILITY_20260620.md` | Two independent strict process-server TCP seeds | Two distinct checksums, 10 total forked TCP pairs, 0 child failures, 98.5% minimum COPPER CTLW reduction, 98.1% minimum SPP+COPPER slack CTLW reduction, 0 COPPER/slack translation faults, and 0.130 percentage-point worst slack gap versus SPP. |

## Interpretation

The current no-systemd ARM64 gem5 guest can run AF_UNIX socketpairs, memory BIOs,
and OpenSSL libssl/libcrypto paths, but its host network namespace starts with
`lo` down and no local route. Direct host-namespace TCP loopback attempts fail
before TLS exchange and before any COPPER policy comparison, so those runs are
not counted as benchmark evidence or benchmark results.

The fuller systemd boot begins normal Linux startup, but it is not locally
tractable for this artifact loop on the current Windows/gem5 setup. The private
user/network namespace workaround is locally tractable: it gives the unprivileged
benchmark process a private network namespace where loopback can be enabled, then
executes OpenSSL libssl over real guest AF_INET TCP loopback sockets. The newer
process-server variant additionally separates the TLS server and client into
forked guest processes. These are now counted as TCP-loopback library-driver
evidence.

This strengthens the artifact beyond the earlier AF_UNIX fallback, but it still
does not replace a production TCP/TLS server evaluation. A production TCP/TLS
result should still be gathered with a real server/client process pair, broader
traffic, and a faster full-system or hardware setup.

host_namespace_tcp_loopback_status=NOT_LOCALLY_TRACTABLE_UNDER_CURRENT_GEM5_BOOT
private_netns_tcp_loopback_status=PASS
private_netns_process_tcp_loopback_status=PASS

not counted as benchmark results
