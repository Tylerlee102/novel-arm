# OpenSSL CLI Full-System Feasibility Note

Date: 2026-06-19

This note records an attempt to move from the local OpenSSL-speed-like driver to the official Ubuntu ARM64 `openssl` command-line binary under the same gem5 ARM64 full-system path.

## Binary

- Package source: `http://ports.ubuntu.com/ubuntu-ports/pool/main/o/openssl/openssl_3.0.13-0ubuntu3_arm64.deb`
- Local package copy: `research/downloads/openssl_arm64/openssl_3.0.13-0ubuntu3_arm64.deb`
- Extracted binary: `research/bin/aarch64_ubuntu_openssl_cli`
- Binary type observed with `file`: `ELF 64-bit LSB pie executable, ARM aarch64`, interpreter `/lib/ld-linux-aarch64.so.1`
- Binary size: 1,017,208 bytes
- SHA-256: `69A8D0012954B19E24E51292DDEECC9665345C77B4F9D38B3FF9701AE6106194`

## Successful Compatibility Run

Output directory: `research/results/gem5_arm_ubuntu_fs_openssl_cli_version_none_retry`

The native full-system run injected the official ARM64 CLI binary and executed:

```text
openssl version
```

Observed guest terminal evidence:

```text
OpenSSL 3.0.13 30 Jan 2024 (Library: OpenSSL 3.0.13 30 Jan 2024)
COPPER_FS_NATIVE_A64_DONE rc=0
```

compatibility_status=PASS

## Official `openssl speed` Attempt

Output directory: `research/results/gem5_arm_ubuntu_fs_openssl_cli_speed_sha256_64_none`

Command attempted:

```text
openssl speed -elapsed -seconds 1 -bytes 64 sha256
```

Observed guest terminal evidence:

```text
You have chosen to measure elapsed time instead of user CPU time.
Doing sha256 for 1s on 64 size blocks:
```

The run remained inside the official timer-driven speed loop after a 30-minute local wall-clock limit and produced no completed ROI statistics or final OpenSSL speed table. The process was stopped manually. This is not counted as a benchmark result.

official_speed_status=NOT_LOCALLY_TRACTABLE_UNDER_TIMING_GEM5

## Interpretation

The official Ubuntu ARM64 OpenSSL CLI is executable in the guest image, but the official `openssl speed` benchmark is timer-driven and is not locally tractable in this timing-mode gem5 setup at even the smallest honest one-second interval. The fixed-count OpenSSL-speed-like driver remains the practical local substitute because it executes the same libcrypto APIs over benchmark-style buffer sizes with deterministic completion. The paper must continue to state that this is not the official OpenSSL CLI benchmark.
