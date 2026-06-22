# OpenSSL CLI TLS-Pair Feasibility Note

Date: 2026-06-20

## Purpose

This note records an attempted official OpenSSL `s_server`/`s_client` TLS-pair workload for the COPPER full-system AArch64 evaluation. It is intentionally not counted as performance evidence because the local gem5 runs did not complete.

## Completed Positive Probe

Path: `research/results/gem5_arm_ubuntu_fs_osslcli_guest_openssl_probe_none`

The guest completed a small full-system ROI using the new `--native-shell-command-file` runner path. The terminal contains:

- `COPPER_OPENSSL_GUEST_PROBE_START`
- `/usr/bin/openssl`
- `OpenSSL 3.0.13 30 Jan 2024 (Library: OpenSSL 3.0.13 30 Jan 2024)`
- `AARCH64_CLANG_SMOKE_OK`
- `COPPER_OPENSSL_GUEST_PROBE_DONE`
- `COPPER_FS_NATIVE_A64_DONE rc=0`

Conclusion: the Ubuntu ARM64 guest already contains an official OpenSSL CLI binary, so future CLI probes can use `/usr/bin/openssl` and avoid reinstalling the large host-provided OpenSSL binary into the guest readfile.

## Incomplete TLS-Pair Attempts

The script `research/openssl_cli_tls_pair_guest.sh` starts a private user/network namespace, raises loopback, starts `/usr/bin/openssl s_server`, and launches `/usr/bin/openssl s_client`.

Timing-mode smoke:

- Path: `research/results/gem5_arm_ubuntu_fs_osslcli_tlspair_guest_smoke_none`
- Last useful markers:
  - `COPPER_OPENSSL_CLI_TLS_PAIR_START`
  - `COPPER_OPENSSL_CLI_TLS_PAIR_NS_ENTER`
  - `COPPER_OPENSSL_CLI_TLS_PAIR_SERVER_PID 88`
- Missing markers:
  - `COPPER_OPENSSL_CLI_TLS_PAIR_CLIENT_DONE`
  - `COPPER_OPENSSL_CLI_TLS_PAIR_RESULT`
  - `COPPER_OPENSSL_CLI_TLS_PAIR_DONE`
- Outcome: stopped after exceeding the local host-time limit.

Atomic-mode functional smoke:

- Path: `research/results/gem5_arm_ubuntu_fs_osslcli_tlspair_guest_atomic_none`
- Last useful markers:
  - `COPPER_OPENSSL_CLI_TLS_PAIR_START`
  - `COPPER_OPENSSL_CLI_TLS_PAIR_NS_ENTER`
  - `COPPER_OPENSSL_CLI_TLS_PAIR_SERVER_PID 87`
- Missing markers:
  - `COPPER_OPENSSL_CLI_TLS_PAIR_CLIENT_DONE`
  - `COPPER_OPENSSL_CLI_TLS_PAIR_RESULT`
  - `COPPER_OPENSSL_CLI_TLS_PAIR_DONE`
- Outcome: stopped after exceeding the local host-time limit.

Earlier attempts that copied `research/bin/aarch64_ubuntu_openssl_cli` into the guest also failed to complete and were made obsolete by the later positive `/usr/bin/openssl` probe.

## Interpretation

This is not evidence against COPPER. It is a local benchmark-orchestration limitation: official OpenSSL CLI server/client pairing inside gem5 is too slow or blocks too long to use as a reliable benchmark in the current Windows-hosted setup. The completed process-separated TCP-loopback libssl workload remains the stronger TCP/TLS evidence because it completes across policies with matching checksums, zero child failures, and no COPPER/slack translation faults.

## How This Affects Claims

- Do not claim an official `openssl s_server`/`s_client` performance result.
- It is safe to claim the guest can execute official `/usr/bin/openssl` and that fixed OpenSSL CLI crypto workloads were already measured elsewhere.
- Continue to frame the TCP/TLS evidence as process-separated OpenSSL library execution over private-netns AF_INET loopback, not as a production OpenSSL CLI server deployment.

status=NEGATIVE_FEASIBILITY_RESULT_NOT_BENCHMARK_EVIDENCE
