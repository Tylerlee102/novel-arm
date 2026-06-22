# COPPER Artifact Reproduction Guide

Date: 2026-06-20

This guide records the local commands and expected outputs for the current COPPER artifact package. It is meant for reviewer-style reruns on a Windows workspace with the required external tools installed. It does not claim silicon signoff, top-tier acceptance, or one-command reproduction of the entire full-system campaign from a fresh clone.

For a concise clone-level reproducibility statement, see `REPRODUCIBILITY_STATUS.md`.

## Local Tool Paths

| Tool | Local path or command |
|---|---|
| Python | `python` |
| gem5 | `external\gem5\build\ARM\gem5.fast.exe` |
| Repo-local MSYS/UCRT runtime | `tools\msys64\ucrt64\bin`, `tools\msys64\usr\bin` |
| Vivado | `C:\AMDDesignTools\2025.2\Vivado\bin\vivado.bat` |
| Main audit | `research\verify_copper_artifacts.py` |
| Claim matrix | `research\build_copper_claim_evidence_matrix.py` |

## Fast Sanity Rerun

From `C:\Users\tyboy\OneDrive\Documents\novel-arm`:

```powershell
& 'python' -m py_compile `
  research\verify_copper_artifacts.py `
  research\build_copper_claim_evidence_matrix.py `
  research\summarize_openssl_cli_fixed_fs.py `
  research\summarize_openssl_cli_seed_stability.py `
  research\build_openssl_tls_socket_workload_aarch64.py `
  research\summarize_openssl_tls_socket_fs.py `
  research\build_sqlite_speedtest1_aarch64.py `
  research\summarize_sqlite_speedtest1_fs.py `
  research\build_pcre2_regex_workload_aarch64.py `
  research\summarize_pcre2_regex_app_fs.py `
  research\summarize_pcre2_seed_stability.py `
  research\build_mibench_patricia_workload_aarch64.py `
  research\summarize_mibench_patricia_fs.py `
  research\summarize_mibench_patricia_scale_portfolio.py `
  research\build_libxml2_xml_workload_aarch64.py `
  research\summarize_libxml2_xml_app_fs.py `
  research\build_libarchive_tar_workload_aarch64.py `
  research\summarize_libarchive_tar_app_fs.py `
  research\build_zstd_workload_aarch64.py `
  research\summarize_zstd_app_fs.py `
  research\build_zlib_workload_aarch64.py `
  research\summarize_zlib_app_fs.py `
  research\summarize_compression_seed_stability.py `
  research\analyze_openssl_tcp_process_metadata_toggle_bound.py `
  research\build_copper_tcp_process_clpd_replay.py `
  research\summarize_copper_tcp_process_clpd_activity_power.py `
  research\build_copper_public_artifact_manifest.py `
  research\build_copper_public_artifact_package.py

& 'python' research\build_copper_claim_evidence_matrix.py
& 'python' research\summarize_pcre2_seed_stability.py
& 'python' research\build_copper_public_artifact_manifest.py
& 'python' research\build_copper_public_artifact_package.py
& 'python' research\verify_copper_artifacts.py
```

Expected current result:

- `research\results\COPPER_CLAIM_EVIDENCE_MATRIX_20260617.md`
- `research\results\COPPER_TOP_TIER_GATE_AUDIT_20260617.md`
- `research\results\COPPER_PUBLIC_ARTIFACT_MANIFEST_20260620.md`
- `research\results\COPPER_PUBLIC_ARTIFACT_PACKAGE_BUILD_20260620.md`
- `research\results\COPPER_ARTIFACT_AUDIT_20260616.md`
- Artifact audit line: `Passed 177/177 artifact checks.`

Expected public artifact manifest:

- Manifest entries: 573.
- Missing referenced files: 0.
- Minimal-package files/bytes: 571 files / 6,096,123 bytes.
- External-store files/bytes: 2 files / 13,479,413 bytes.
- Heavy optional files: `research\results\copper_clpd_sram_workload_activity.saif` and `research\results\copper_clpd_sram_tcp_process_activity.saif`.
- `status=PASS`

Expected public artifact package build:

- Direct-package rows copied: 571.
- Generated metadata files copied: 4.
- Package files present: 575.
- Missing files: 0.
- Hash mismatches: 0.
- `status=PASS`

## Upstream SQLite speedtest1 JSON/Star/ORM Rerun

The current tractable upstream SQLite speedtest1 points use unmodified SQLite 3.53.2 `test/speedtest1.c` and the JSON, star-schema, and ORM-style testsets:

Runner: `research\run_sqlite_speedtest1_fs.sh`.

```powershell
& 'python' research\build_sqlite_speedtest1_aarch64.py

$env:TAG='speedtest1_json_smoke_size1'
$env:SIZE='1'
$env:TESTSET='json'
$env:POLICY_LIST='none naive copper_clpd64k_peb spp spp_copper_slack'
& tools\msys64\usr\bin\bash.exe -lc 'cd /c/Users/tyboy/OneDrive/Documents/novel-arm && ./research/run_sqlite_speedtest1_fs.sh'

& 'python' research\summarize_sqlite_speedtest1_fs.py --tag speedtest1_json_smoke_size1

$env:TAG='speedtest1_star_smoke_size1'
$env:SIZE='1'
$env:TESTSET='star'
$env:POLICY_LIST='none naive copper_clpd64k_peb spp spp_copper_slack'
& tools\msys64\usr\bin\bash.exe -lc 'cd /c/Users/tyboy/OneDrive/Documents/novel-arm && ./research/run_sqlite_speedtest1_fs.sh'

& 'python' research\summarize_sqlite_speedtest1_fs.py --tag speedtest1_star_smoke_size1

$env:TAG='speedtest1_orm_smoke_size1'
$env:SIZE='1'
$env:TESTSET='orm'
$env:POLICY_LIST='none naive copper_clpd64k_peb spp spp_copper_slack'
& tools\msys64\usr\bin\bash.exe -lc 'cd /c/Users/tyboy/OneDrive/Documents/novel-arm && ./research/run_sqlite_speedtest1_fs.sh'

& 'python' research\summarize_sqlite_speedtest1_fs.py --tag speedtest1_orm_smoke_size1
& 'python' research\summarize_sqlite_speedtest1_components.py
```

Expected aggregate:

- `research\results\gem5_arm_ubuntu_fs_sqlite_speedtest1\SQLITE_SPEEDTEST1_SPEEDTEST1_JSON_SMOKE_SIZE1_FS_SUMMARY.md`
- `research\results\gem5_arm_ubuntu_fs_sqlite_speedtest1\SQLITE_SPEEDTEST1_SPEEDTEST1_STAR_SMOKE_SIZE1_FS_SUMMARY.md`
- `research\results\gem5_arm_ubuntu_fs_sqlite_speedtest1\SQLITE_SPEEDTEST1_SPEEDTEST1_ORM_SMOKE_SIZE1_FS_SUMMARY.md`
- `research\results\SQLITE_SPEEDTEST1_COMPONENTS_20260619.md`
- Minimum COPPER CTLW reduction versus naive DMP: 92.3%.
- Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 88.5%.
- Translation faults across key policies and components: 0.

## MiBench Patricia Rerun

This point uses the public MiBench network/patricia Patricia trie implementation and public MiBench packet-field inputs. The COPPER-specific code is a small AArch64 driver that emits checksum and return-code fields for full-system measurement. The input file is staged before ROI through `--native-pre-command-file`, so the timed region measures the Patricia trie execution rather than a guest-side input decode. The runner now uses compressed pre-ROI staging by default (`STAGE_COMPRESSED=1`), which is the recommended path for larger public `large.udp` prefixes; set `STAGE_COMPRESSED=0` only to reproduce the older raw base64 staging path.

Runner: `research\run_mibench_patricia_fs.sh`.

```powershell
& 'python' research\build_mibench_patricia_workload_aarch64.py

$env:TAG='patricia_large12288'
$env:LIMIT='12288'
$env:LOOKUPS='24576'
$env:ROUNDS='1'
$env:SEED='0'
$env:INPUT_FILE='external/mibench_network/network/patricia/large.udp'
$env:POLICY_LIST='none naive copper_clpd64k_peb spp spp_copper_slack'
& tools\msys64\usr\bin\bash.exe -lc 'cd /c/Users/tyboy/OneDrive/Documents/novel-arm && ./research/run_mibench_patricia_fs.sh'

& 'python' research\summarize_mibench_patricia_fs.py --tag patricia_large12288
& 'python' research\summarize_mibench_patricia_scale_portfolio.py
```

Expected summary:

- `research\results\gem5_arm_ubuntu_fs_mibench_patricia_app\MIBENCH_PATRICIA_PATRICIA_LARGE12288_FS_SUMMARY.md`
- `research\results\MIBENCH_PATRICIA_SCALE_PORTFOLIO_20260620.md`
- Public input records consumed: 12288 of limit 12288.
- COPPER CTLW reduction versus naive DMP: 97.9%.
- SPP+COPPER slack CTLW reduction versus naive DMP: 96.6%.
- SPP+COPPER slack tick gap versus SPP: +0.035 percentage points.
- Scale portfolio points: 4.
- Scale portfolio minimum COPPER CTLW reduction: 97.9%.
- Scale portfolio minimum SPP+COPPER slack CTLW reduction: 96.6%.
- Scale portfolio worst absolute SPP+COPPER slack gap versus SPP: 0.050 percentage points.
- Checksum agreement: yes.
- Translation faults across key policies: 0.
- `status=PASS`

For the second 12K seed, run `research\run_mibench_patricia_large12288_seed1_campaign.sh`, summarize with `--tag patricia_large12288_seed1`, then run:

```powershell
& 'python' research\summarize_mibench_patricia_seed_stability.py
```

Expected seed-stability summary:

- `research\results\gem5_arm_ubuntu_fs_mibench_patricia_app\MIBENCH_PATRICIA_PATRICIA_LARGE12288_SEED1_FS_SUMMARY.md`
- `research\results\MIBENCH_PATRICIA_12K_SEED_STABILITY_20260621.md`
- MiBench Patricia 12K seed points: 2.
- Distinct per-seed checksums: 2.
- Minimum COPPER CTLW reduction versus naive DMP: 97.8%.
- Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 96.6%.
- Worst absolute SPP+COPPER slack tick gap versus SPP: 0.035 percentage points.
- COPPER/slack translation faults across both 12K seeds: 0.
- `status=PASS`

For a faster public-input smoke rerun, use `TAG=patricia_small8192`, `LIMIT=8192`, `LOOKUPS=16384`, and the default `small.udp` input; the expected summary is `research\results\gem5_arm_ubuntu_fs_mibench_patricia_app\MIBENCH_PATRICIA_PATRICIA_SMALL8192_FS_SUMMARY.md`. The 12,288-record `large.udp` point is the strongest completed five-policy local Patricia point, and the two-seed artifact is the stronger stability claim.

Larger-scale public `large.udp` feasibility notes:

- `research\results\MIBENCH_PATRICIA_LARGE16384_FEASIBILITY_20260620.md`
- `research\results\MIBENCH_PATRICIA_LARGE32768_FEASIBILITY_20260620.md`
- `research\results\MIBENCH_PATRICIA_LARGE62721_FEASIBILITY_20260620.md`

These notes are intentionally not benchmark-result claims. They show that compressed staging works and that no-prefetch baselines complete for 16,384, 32,768, and 62,721 public input records, with valid checksums and return code 0. They also show that larger naive/COPPER policy comparisons did not complete within the local interactive gem5 budget. The completed five-policy public-input frontier is the 12,288-record point above.

## PCRE2 Regex Rerun

This point calls the public PCRE2 8-bit regex compiler and matcher through the Ubuntu ARM64 guest library stack. It is a parser/matcher-library benchmark driver, not production log-processing software.

Runner: `research\run_pcre2_regex_app_fs.sh`.

```powershell
& 'python' research\build_pcre2_regex_workload_aarch64.py

$env:TAG='pcre2_smoke'
$env:RECORDS='512'
$env:LOOKUPS='1500'
$env:SCAN_DEPTH='4'
$env:ROUNDS='1'
$env:SEED='0'
$env:POLICY_LIST='none naive copper_clpd64k_peb spp spp_copper_slack'
& tools\msys64\usr\bin\bash.exe -lc 'cd /c/Users/tyboy/OneDrive/Documents/novel-arm && bash research/run_pcre2_regex_app_fs.sh'

& 'python' research\summarize_pcre2_regex_app_fs.py --tag pcre2_smoke --policies none naive copper_clpd64k_peb spp spp_copper_slack

$env:TAG='pcre2_seed1'
$env:RECORDS='512'
$env:LOOKUPS='1500'
$env:SCAN_DEPTH='4'
$env:ROUNDS='1'
$env:SEED='1'
$env:POLICY_LIST='none naive copper_clpd64k_peb spp spp_copper_slack'
& tools\msys64\usr\bin\bash.exe -lc 'cd /c/Users/tyboy/OneDrive/Documents/novel-arm && bash research/run_pcre2_regex_app_fs.sh'

& 'python' research\summarize_pcre2_regex_app_fs.py --tag pcre2_seed1 --policies none naive copper_clpd64k_peb spp spp_copper_slack
& 'python' research\summarize_pcre2_seed_stability.py
```

Expected summary:

- `research\results\gem5_arm_ubuntu_fs_pcre2_app\PCRE2_PCRE2_SMOKE_FS_SUMMARY.md`
- `research\results\gem5_arm_ubuntu_fs_pcre2_app\PCRE2_PCRE2_SEED1_FS_SUMMARY.md`
- `research\results\PCRE2_REGEX_SEED_STABILITY_20260620.md`
- Minimum COPPER CTLW reduction versus naive DMP across both seeds: 99.3%.
- Minimum SPP+COPPER slack CTLW reduction versus naive DMP across both seeds: 98.9%.
- Checksum agreement: yes.
- Translation faults across key policies: 0.

## libxml2 XML Rerun

This point calls the public libxml2 XML parser and serializer through the Ubuntu ARM64 guest library stack over deterministic in-memory XML records containing address-shaped words as data. It is a parser/serializer-library benchmark driver, not a production XML service.

Runner: `research\run_libxml2_xml_app_fs.sh`.

```powershell
& 'python' research\build_libxml2_xml_workload_aarch64.py

$env:TAG='xml_tiny_full'
$env:RECORDS='16'
$env:ROUNDS='1'
$env:SCAN_DEPTH='1'
$env:SEED='0'
$env:POLICY_LIST='none naive copper_clpd64k_peb spp spp_copper_slack'
& tools\msys64\usr\bin\bash.exe -lc 'cd /c/Users/tyboy/OneDrive/Documents/novel-arm && bash research/run_libxml2_xml_app_fs.sh'

& 'python' research\summarize_libxml2_xml_app_fs.py --tag xml_tiny_full --policies none naive copper_clpd64k_peb spp spp_copper_slack
```

Expected summary:

- `research\results\gem5_arm_ubuntu_fs_libxml2_app\LIBXML2_XML_TINY_FULL_FS_SUMMARY.md`
- COPPER CTLW reduction versus naive DMP: 98.9%.
- SPP+COPPER slack CTLW reduction versus naive DMP: 98.9%.
- SPP+COPPER slack gap versus SPP: 0.035 percentage points.
- Checksum agreement: yes.
- Translation faults across key policies: 0.

## libarchive TAR Rerun

This point calls the public libarchive TAR parser through the Ubuntu ARM64 guest library stack over deterministic in-memory archive entries containing address-shaped words as data. It is an archive-parser-library benchmark driver, not a production archive extraction service.

Runner: `research\run_libarchive_tar_app_fs.sh`.

```powershell
& 'python' research\build_libarchive_tar_workload_aarch64.py

$env:TAG='tar_tiny_full'
$env:ENTRIES='16'
$env:ROUNDS='1'
$env:SCANS='1'
$env:SEED='0'
$env:POLICY_LIST='none naive copper_clpd64k_peb spp spp_copper_slack'
& tools\msys64\usr\bin\bash.exe -lc 'cd /c/Users/tyboy/OneDrive/Documents/novel-arm && bash research/run_libarchive_tar_app_fs.sh'

& 'python' research\summarize_libarchive_tar_app_fs.py --tag tar_tiny_full --policies none naive copper_clpd64k_peb spp spp_copper_slack
```

Expected summary:

- `research\results\gem5_arm_ubuntu_fs_libarchive_app\LIBARCHIVE_TAR_TINY_FULL_FS_SUMMARY.md`
- COPPER CTLW reduction versus naive DMP: 98.0%.
- SPP+COPPER slack CTLW reduction versus naive DMP: 98.6%.
- SPP+COPPER slack gap versus SPP: -0.004 percentage points.
- Checksum agreement: yes.
- Translation faults across key policies: 0.

## Zstd Compression Rerun

This point calls public libzstd compression/decompression through the Ubuntu ARM64 guest library stack over buffers containing address-shaped words as data. It is a compression-library benchmark driver, not a production storage or network compression service.

Runner: `research\run_zstd_app_fs.sh`.

```powershell
& 'python' research\build_zstd_workload_aarch64.py

$env:TAG='zstd_tiny'
$env:BYTES='8192'
$env:ROUNDS='2'
$env:SEED='0'
$env:LEVEL='1'
$env:POLICY_LIST='none naive copper_clpd64k_peb spp spp_copper_slack'
& tools\msys64\usr\bin\bash.exe -lc 'cd /c/Users/tyboy/OneDrive/Documents/novel-arm && bash research/run_zstd_app_fs.sh'

& 'python' research\summarize_zstd_app_fs.py --tag zstd_tiny --policies none naive copper_clpd64k_peb spp spp_copper_slack
```

Expected summary:

- `research\results\gem5_arm_ubuntu_fs_zstd_app\ZSTD_ZSTD_TINY_FS_SUMMARY.md`
- COPPER CTLW reduction versus naive DMP: 99.5%.
- SPP+COPPER slack CTLW reduction versus naive DMP: 99.4%.
- Checksum agreement: yes.
- Translation faults across key policies: 0.

## zlib Compression Rerun

This point calls public zlib compression/decompression through the Ubuntu ARM64 guest library stack over buffers containing address-shaped words as data. It is a compression-library benchmark driver, not a production storage or network compression service.

Runner: `research\run_zlib_app_fs.sh`.

```powershell
& 'python' research\build_zlib_workload_aarch64.py

$env:TAG='zlib_tiny'
$env:BYTES='8192'
$env:ROUNDS='2'
$env:SEED='0'
$env:LEVEL='1'
$env:POLICY_LIST='none naive copper_clpd64k_peb spp spp_copper_slack'
& tools\msys64\usr\bin\bash.exe -lc 'cd /c/Users/tyboy/OneDrive/Documents/novel-arm && bash research/run_zlib_app_fs.sh'

& 'python' research\summarize_zlib_app_fs.py --tag zlib_tiny --policies none naive copper_clpd64k_peb spp spp_copper_slack
```

Expected summary:

- `research\results\gem5_arm_ubuntu_fs_zlib_app\ZLIB_ZLIB_TINY_FS_SUMMARY.md`
- COPPER CTLW reduction versus naive DMP: 99.4%.
- SPP+COPPER slack CTLW reduction versus naive DMP: 99.5%.
- Checksum agreement: yes.
- Translation faults across key policies: 0.

## Compression Seed Stability

After running the two listed Zstd and zlib seeds, regenerate the aggregate stability report:

```powershell
& 'python' research\summarize_zstd_app_fs.py --tag zstd_seed1 --policies none naive copper_clpd64k_peb spp spp_copper_slack
& 'python' research\summarize_zlib_app_fs.py --tag zlib_seed1 --policies none naive copper_clpd64k_peb spp spp_copper_slack
& 'python' research\summarize_compression_seed_stability.py
```

Expected aggregate:

- `research\results\COMPRESSION_LIBRARY_SEED_STABILITY_20260620.md`
- Seed/library points: 4.
- Minimum COPPER CTLW reduction versus naive DMP: 99.4%.
- Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 99.4%.
- Worst SPP+COPPER slack gap versus SPP: 0.183 percentage points.
- COPPER/slack translation faults across all seed points: 0.

## Official OpenSSL CLI Fixed-Workload Reruns

The Bash dependency for this path is removed. Use the PowerShell-native runner:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File research\run_openssl_cli_fixed_fs.ps1 `
  -Mode sha256 -Tag fixed_64k_seed2 -InputBytes 65536 -Seed 2

powershell -NoProfile -ExecutionPolicy Bypass -File research\run_openssl_cli_fixed_fs.ps1 `
  -Mode aesctr -Tag aesctr_64k_seed2 -InputBytes 65536 -Seed 2

powershell -NoProfile -ExecutionPolicy Bypass -File research\run_openssl_cli_fixed_fs.ps1 `
  -Mode hmac -Tag hmac_64k_seed2 -InputBytes 65536 -Seed 2
```

Each command runs five policies: `none`, `naive`, `copper_clpd64k_peb`, `spp`, and `spp_copper_slack`. These are full-system timing gem5 runs and can take a long time.

After reruns, regenerate summaries:

```powershell
& 'python' research\summarize_openssl_cli_fixed_fs.py --tag fixed_64k_seed2 --mode sha256
& 'python' research\summarize_openssl_cli_fixed_fs.py --tag aesctr_64k_seed2 --mode aes_ctr
& 'python' research\summarize_openssl_cli_fixed_fs.py --tag hmac_64k_seed2 --mode hmac
& 'python' research\summarize_openssl_cli_seed_stability.py
```

Expected aggregate:

- `research\results\OPENSSL_CLI_SEED_STABILITY_20260619.md`
- 9 official CLI seed/workload points.
- COPPER CTLW reduction at least 95.5%.
- SPP+COPPER slack CTLW reduction at least 95.2%.
- Worst SPP+COPPER slack gap versus SPP: 0.294 percentage points.
- COPPER and SPP+COPPER slack translation faults: 0.

Official CLI TLS-pair caveat:

- `research\results\OPENSSL_CLI_TLS_PAIR_FEASIBILITY_20260620.md`
- `research\openssl_guest_probe.sh`
- `research\openssl_cli_tls_pair_guest.sh`
- `research\gem5_arm_ubuntu_fs_copper_workload.py` now supports `--native-shell-command-file` to avoid fragile Windows quoting for multi-line guest ROI scripts.
- The guest probe completes and confirms `/usr/bin/openssl` is available as OpenSSL 3.0.13.
- The official `openssl s_server`/`s_client` pair reaches private-netns entry and server launch, but does not complete locally within the host-time limits in timing or atomic gem5 modes. It is therefore a negative feasibility result and is not counted as benchmark evidence.

## OpenSSL libssl Socket-Backed TLS Rerun

This is the tractable socket-backed TLS-library point. It runs OpenSSL libssl TLS 1.2 PSK handshake and record I/O over a nonblocking Linux AF_UNIX socketpair, not a memory BIO. It is still not a production TCP/TLS server.

Runner: `research\run_openssl_tls_socket_fs.sh`.

```powershell
& 'python' research\build_openssl_tls_socket_workload_aarch64.py

$env:TAG='socket_smoke'
$env:SESSIONS='16'
$env:HANDSHAKES='8'
$env:RECORDS='1'
$env:SCAN_DEPTH='4'
$env:ROUNDS='1'
$env:SEED='0'
$env:POLICY_LIST='none naive copper_clpd64k_peb spp spp_copper_slack'
& tools\msys64\usr\bin\bash.exe /c/Users/tyboy/OneDrive/Documents/novel-arm/research/run_openssl_tls_socket_fs.sh

& 'python' research\summarize_openssl_tls_socket_fs.py --tag socket_smoke --policies none naive copper_clpd64k_peb spp spp_copper_slack
```

Expected summary:

- `research\results\gem5_arm_ubuntu_fs_ossltlssocket_app\OSSLTLSSOCKET_SOCKET_SMOKE_FS_SUMMARY.md`
- COPPER CTLW reduction versus naive DMP: 99.1%.
- SPP+COPPER slack CTLW reduction versus naive DMP: 98.2%.
- Checksum agreement: yes.
- Translation faults across key policies: 0.

TCP loopback note:

- `research\results\OPENSSL_TCP_LOOPBACK_FEASIBILITY_20260619.md`
- Direct host-namespace TCP loopback under the current no-systemd ARM64 gem5 boot is not counted as benchmark evidence; local attempts fail before TLS exchange with errno 99 or errno 101.
- A guest pre-command diagnostic records that the readfile workload runs without permission to raise host `lo`; the loopback interface remains down with no route. A fuller systemd boot begins normal networking startup but did not reach the workload within the local 20-minute timeout.
- The patched TCP harness also supports an explicit fallback mode. In this environment the fallback diagnostic records `transport=af_unix_fallback`, so that result is socket-backed libssl evidence and environment diagnosis, not TCP-loopback benchmark evidence.
- The strict TCP-netns run is counted as TCP-loopback library-driver evidence. It creates a private user/network namespace inside the guest process, raises loopback there, and records `transport=tcp_loopback_netns`, `strict_tcp=1`, and `afunix_fallback_pairs=0` across all key policies. It is still an in-process loopback service driver, not a production TCP/TLS server.
- The process-server TCP-netns run is counted as stronger process-separated TCP-loopback library-driver evidence. It creates the same private user/network namespace, then forks a TLS server process while the parent acts as TLS client over AF_INET loopback. It records `transport=tcp_loopback_netns_process`, `process_server=1`, `process_pairs=1`, `child_failures=0`, and `afunix_fallback_pairs=0` across all key policies. It is still a bounded local harness rather than a production deployment.

PowerShell-safe TCP diagnostic rerun:

```powershell
$env:TAG='tcp_diag_lo'
$env:POLICY_LIST='none'
$env:SESSIONS='16'
$env:HANDSHAKES='4'
$env:RECORDS='1'
$env:SCAN_DEPTH='4'
$env:ROUNDS='1'
$env:SEED='0'
$env:NATIVE_PRE_COMMAND='ip link set lo up || true; ifconfig lo up || true; ip addr add 127.0.0.1/8 dev lo || true; ip addr show || true; ip route show || true; cat /proc/net/dev || true; cat /proc/net/route || true'
& tools\msys64\usr\bin\bash.exe -lc 'cd /c/Users/tyboy/OneDrive/Documents/novel-arm && bash research/run_openssl_tls_tcp_fs.sh'

& 'python' research\summarize_openssl_tls_tcp_fs.py --tag tcp_diag_lo --policies none
```

Tagged fallback rerun:

```powershell
& 'python' research\build_openssl_tls_tcp_workload_aarch64.py

$env:TAG='tcp_fallback_probe'
$env:SESSIONS='16'
$env:HANDSHAKES='4'
$env:RECORDS='1'
$env:SCAN_DEPTH='4'
$env:ROUNDS='1'
$env:SEED='0'
$env:POLICY_LIST='none naive copper_clpd64k_peb spp spp_copper_slack'
& tools\msys64\usr\bin\bash.exe -lc 'cd /c/Users/tyboy/OneDrive/Documents/novel-arm && bash research/run_openssl_tls_tcp_fs.sh'

& 'python' research\summarize_openssl_tls_tcp_fs.py --tag tcp_fallback_probe --policies none naive copper_clpd64k_peb spp spp_copper_slack
```

Expected fallback summary:

- `research\results\gem5_arm_ubuntu_fs_ossltlstcp_app\ossltlstcp_TCP_FALLBACK_PROBE_FS_SUMMARY.md`
- Transport mode: `af_unix_fallback`.
- COPPER CTLW reduction versus naive DMP: 98.0%.
- SPP+COPPER slack CTLW reduction versus naive DMP: 97.2%.
- Checksum agreement: yes.
- COPPER and SPP+COPPER slack translation faults: 0.
- `status=AF_UNIX_FALLBACK_PASS`

Strict TCP-netns rerun:

```powershell
& 'python' research\build_openssl_tls_tcp_workload_aarch64.py

$env:TAG='tcp_netns_strict'
$env:SESSIONS='16'
$env:HANDSHAKES='4'
$env:RECORDS='1'
$env:SCAN_DEPTH='4'
$env:ROUNDS='1'
$env:SEED='0'
$env:STRICT_TCP='1'
$env:POLICY_LIST='none naive copper_clpd64k_peb spp spp_copper_slack'
& tools\msys64\usr\bin\bash.exe -lc 'cd /c/Users/tyboy/OneDrive/Documents/novel-arm && bash research/run_openssl_tls_tcp_fs.sh'

& 'python' research\summarize_openssl_tls_tcp_fs.py --tag tcp_netns_strict --policies none naive copper_clpd64k_peb spp spp_copper_slack
```

Expected strict TCP-netns summary:

- `research\results\gem5_arm_ubuntu_fs_ossltlstcp_app\ossltlstcp_TCP_NETNS_STRICT_FS_SUMMARY.md`
- Transport mode: `tcp_loopback_netns`.
- `strict_tcp=1`.
- `afunix_fallback_pairs=0`.
- COPPER CTLW reduction versus naive DMP: 97.7%.
- SPP+COPPER slack CTLW reduction versus naive DMP: 97.2%.
- Checksum agreement: yes.
- COPPER and SPP+COPPER slack translation faults: 0.
- `status=TCP_NETNS_PASS`

Process-server TCP-netns rerun:

```powershell
& 'python' research\build_openssl_tls_tcp_workload_aarch64.py

$env:TAG='tcp_netns_process_key1'
$env:SESSIONS='16'
$env:HANDSHAKES='1'
$env:RECORDS='1'
$env:SCAN_DEPTH='4'
$env:ROUNDS='1'
$env:SEED='0'
$env:STRICT_TCP='1'
$env:PROCESS_SERVER='1'
$env:POLICY_LIST='none naive copper_clpd64k_peb spp spp_copper_slack'
& tools\msys64\usr\bin\bash.exe -lc 'cd /c/Users/tyboy/OneDrive/Documents/novel-arm && bash research/run_openssl_tls_tcp_fs.sh'

& 'python' research\summarize_openssl_tls_tcp_fs.py --tag tcp_netns_process_key1 --policies none naive copper_clpd64k_peb spp spp_copper_slack
```

Expected process-server TCP-netns summary:

- `research\results\gem5_arm_ubuntu_fs_ossltlstcp_app\ossltlstcp_TCP_NETNS_PROCESS_KEY1_FS_SUMMARY.md`
- Transport mode: `tcp_loopback_netns_process`.
- `process_server=1`.
- `process_pairs=1`.
- `child_failures=0`.
- `afunix_fallback_pairs=0`.
- COPPER CTLW reduction versus naive DMP: 98.5%.
- SPP+COPPER slack CTLW reduction versus naive DMP: 98.2%.
- Checksum agreement: yes.
- COPPER and SPP+COPPER slack translation faults: 0.
- `status=TCP_NETNS_PROCESS_PASS`

Second process-server seed and aggregate:

```powershell
$env:TAG='tcp_netns_process_seed1'
$env:SESSIONS='16'
$env:HANDSHAKES='1'
$env:RECORDS='1'
$env:SCAN_DEPTH='4'
$env:ROUNDS='1'
$env:SEED='1'
$env:STRICT_TCP='1'
$env:PROCESS_SERVER='1'
$env:POLICY_LIST='none naive copper_clpd64k_peb spp spp_copper_slack'
& tools\msys64\usr\bin\bash.exe -lc 'cd /c/Users/tyboy/OneDrive/Documents/novel-arm && bash research/run_openssl_tls_tcp_fs.sh'

& 'python' research\summarize_openssl_tls_tcp_fs.py --tag tcp_netns_process_seed1 --policies none naive copper_clpd64k_peb spp spp_copper_slack
& 'python' research\summarize_openssl_tcp_process_seed_stability.py
```

Expected process-server seed-stability summary:

- `research\results\OPENSSL_TCP_PROCESS_SEED_STABILITY_20260620.md`
- Process-server seed points: 2.
- Distinct seed checksums: 2.
- Total forked process TCP pairs across policies/seeds: 10.
- Child process failures across policies/seeds: 0.
- Minimum COPPER CTLW reduction versus naive DMP: 98.5%.
- Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 98.1%.
- COPPER/slack translation faults across both seeds: 0.
- `status=PASS`

Process-server metadata-toggle side-effect bound:

```powershell
& 'python' research\analyze_openssl_tcp_process_metadata_toggle_bound.py
```

Expected process-server metadata summary:

- `research\results\OPENSSL_TCP_PROCESS_METADATA_TOGGLE_BOUND_20260620.md`
- Selected policy rows: 8.
- All selected rows use `tcp_loopback_netns_process`: yes.
- COPPER CLPD-64K+PEB metadata events: 179,343.
- SPP+COPPER slack metadata events: 268,494.
- High scenario metadata energy: 4.633 uJ for COPPER and 6.818 uJ for SPP+COPPER slack.
- Matching gem5 DRAM rank-energy rows are found for every selected seed/policy row.
- High scenario normalized metadata bound: at most 0.1510% of matching DRAM operation energy and 0.005412% of matching total DRAM energy.
- `status=PASS`

Process-server CLPD activity replay and Vivado SAIF power:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File research\run_copper_clpd_sram_tcp_process_activity_xsim.ps1
& 'C:\AMDDesignTools\2025.2\Vivado\bin\vivado.bat' -mode batch -source research\run_copper_clpd_sram_tcp_process_saif_power.tcl
& 'python' research\summarize_copper_tcp_process_clpd_activity_power.py
```

Expected process-server CLPD activity-power summary:

- `research\results\COPPER_TCP_PROCESS_CLPD_ACTIVITY_POWER_20260620.md`
- Source policy: `spp_copper_slack`.
- Raw driver events: 268,494.
- Replay events: 268,494.
- Source points: 4 selected SPP+COPPER slack process-server rows, including scaled four-pair and eight-pair points.
- XSim replay contains `errors=0`.
- Vivado SAIF mapping: 37% (226/611).
- Vivado power: 0.083 W total, 0.014 W dynamic, 0.069 W static.
- Timing: WNS 1.807 ns.
- `status=PASS`

## RTL/Vivado Evidence

The current paper-facing RTL evidence is already captured in:

- `research\COPPER_VIVADO_SUMMARY.md`
- `research\results\COPPER_CLPD_SRAM_SYNTH_SUMMARY.md`
- `research\results\COPPER_CLPD_SRAM_IMPL64K_A200T_SUMMARY.md`
- `research\results\COPPER_CLPD_ACTIVITY_POWER_20260619.md`
- `research\results\COPPER_WORKLOAD_CLPD_ACTIVITY_POWER_20260619.md`
- `research\results\COPPER_TCP_PROCESS_CLPD_ACTIVITY_POWER_20260620.md`
- `research\results\COPPER_ROCCA_CLPD_COMMIT_ADAPTER_RTL_SUMMARY.md`
- `research\results\COPPER_CAVI_AUTHORITY_ISSUE_GATE_RTL_SUMMARY.md`
- `research\results\COPPER_TLB_COHERENCE_AUTHORITY_FILTER_RTL_SUMMARY.md`

Representative XSim rerunners include:

- `research\run_copper_full_authority_sva_xsim.ps1`
- `research\run_copper_cepf_line_e2e_xsim.ps1`
- `research\run_copper_ctlw_witness_xsim.ps1`
- `research\run_copper_clpd_ctlw_authority_e2e_xsim.ps1`
- `research\run_copper_sari_scoped_authority_e2e_xsim.ps1`
- `research\run_copper_full_lsq_amba_authority_xsim.ps1`
- `research\run_copper_rocca_clpd_commit_adapter_xsim.ps1`
- `research\run_copper_cavi_authority_issue_gate_xsim.ps1`
- `research\run_copper_tlb_coherence_authority_filter_xsim.ps1`

Vivado batch runs should use:

```powershell
& 'C:\AMDDesignTools\2025.2\Vivado\bin\vivado.bat' -mode batch -source <script.tcl>
```

ROCCA-to-CLPD proof-write boundary rerun:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File research\run_copper_rocca_clpd_commit_adapter_xsim.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File research\run_copper_rocca_clpd_commit_adapter_synth.ps1
```

Expected ROCCA summary:

- `research\results\COPPER_ROCCA_CLPD_COMMIT_ADAPTER_RTL_SUMMARY.md`
- XSim: 11 directed plus 20,000 randomized cycles, 0 errors.
- Same-cycle clear-wins blocks: 1,598.
- ROCCA+64-entry CLPD wrapper: 4,302 LUTs, 2,624 FFs, 0 BRAM/DSP.
- Timing: WNS 1.149 ns at 10 ns.
- `status=PASS`

CAVI final authority issue interlock rerun:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File research\run_copper_cavi_authority_issue_gate_xsim.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File research\run_copper_cavi_authority_issue_gate_synth.ps1
```

Expected CAVI summary:

- `research\results\COPPER_CAVI_AUTHORITY_ISSUE_GATE_RTL_SUMMARY.md`
- XSim: 14 directed plus 20,000 randomized trials, 0 errors.
- Random clear-wins proof suppressions: 2,021.
- Random target revocation conflicts: 3,996.
- CAVI wrapper: 4,591 LUTs, 2,791 FFs, 0 BRAM/DSP.
- Timing: WNS 1.149 ns at 10 ns.
- `status=PASS`

## What This Guide Does Not Prove

- It does not prove top-tier acceptance.
- It does not replace SPEC-like, browser, production database, production TCP/TLS, or official timer-driven `openssl speed` workloads.
- It does not provide ASIC-calibrated full-chip power.
- It does not provide a production ARM backend, TLB, or AMBA CHI integration proof.

status=PASS

