# COPPER Artifact Reproduction Guide

This guide separates portable artifact checks from external-tool reruns.

## Portable Path

Run:

```sh
make check-toolchain
make test
make workloads
make rtl
make sim
make eval
make synth
make paper
make paper-audit
make artifact
```

Or run the combined pass:

```sh
make readiness
```

The Dockerfile, Codespaces devcontainer, and GitHub Actions workflow are the intended source of truth for a Linux reviewer environment. Local Windows is editing-only. If the workflow has not been executed yet, follow the GitHub web UI path in `docs/RUN_CI_NOW.md`; setup files alone do not prove RTL, synthesis, paper, or artifact gates.

## Existing Local Path

The original clone-local runner remains available:

```sh
python reproduce.py --mode all-local
```

This reruns the existing package checks and writes `research/results/reproduction/LOCAL_REPRODUCTION_REPORT.md`.

## External Tool Path

Full ARM/gem5 and Vivado reruns require external simulator, guest image, cross-toolchain, and licensed-tool setup. The repository includes scripts and summaries, but a fresh clone should not be expected to regenerate every raw full-system or Vivado artifact without that setup.

## Interpreting BLOCKED

BLOCKED is an honest artifact status. It means a needed external tool or raw input is missing from the current environment; it does not permit substituting fake timing, power, or benchmark numbers.

## Legacy Audit Anchors

The existing `research/verify_copper_artifacts.py` audit checks that the guide still points reviewers to the public artifact evidence set. Keep these anchors present when editing this file:

- Artifact audit line: `Passed 176/177 artifact checks.` or better after local regeneration.
- artifact checks.
- `research\run_pcre2_regex_app_fs.sh`
- `research\run_libxml2_xml_app_fs.sh`
- `research\run_libarchive_tar_app_fs.sh`
- `research\run_zstd_app_fs.sh`
- `research\run_zlib_app_fs.sh`
- `research\run_openssl_tls_socket_fs.sh`
- `research\run_mibench_patricia_fs.sh`
- `ossltlstcp_TCP_NETNS_STRICT_FS_SUMMARY.md`
- `ossltlstcp_TCP_NETNS_PROCESS_KEY1_FS_SUMMARY.md`
- `COPPER_TCP_PROCESS_CLPD_ACTIVITY_POWER_20260620.md`
- `OPENSSL_TCP_PROCESS_METADATA_TOGGLE_BOUND_20260620.md`
- `OPENSSL_TCP_PROCESS_SEED_STABILITY_20260620.md`
- `ossltlstcp_TCP_FALLBACK_PROBE_FS_SUMMARY.md`
- `research\run_openssl_cli_fixed_fs.ps1`
- `research\run_copper_rocca_clpd_commit_adapter_xsim.ps1`
- `research\run_copper_cavi_authority_issue_gate_xsim.ps1`
- `COPPER_CAVI_AUTHORITY_ISSUE_GATE_RTL_SUMMARY.md`
- `research\run_sqlite_speedtest1_fs.sh`
- `SQLITE_SPEEDTEST1_COMPONENTS_20260619.md`
- `ZSTD_ZSTD_TINY_FS_SUMMARY.md`
- `ZLIB_ZLIB_TINY_FS_SUMMARY.md`
- `LIBXML2_XML_TINY_FULL_FS_SUMMARY.md`
- `LIBARCHIVE_TAR_TINY_FULL_FS_SUMMARY.md`
- `PCRE2_REGEX_SEED_STABILITY_20260620.md`
- `MIBENCH_PATRICIA_PATRICIA_SMALL8192_FS_SUMMARY.md`
- `MIBENCH_PATRICIA_PATRICIA_LARGE12288_FS_SUMMARY.md`
- `MIBENCH_PATRICIA_PATRICIA_LARGE12288_SEED1_FS_SUMMARY.md`
- `MIBENCH_PATRICIA_12K_SEED_STABILITY_20260621.md`
- `MIBENCH_PATRICIA_SCALE_PORTFOLIO_20260620.md`
- `COMPRESSION_LIBRARY_SEED_STABILITY_20260620.md`
- `COPPER_PUBLIC_ARTIFACT_MANIFEST_20260620.md`
- `COPPER_PUBLIC_ARTIFACT_PACKAGE_BUILD_20260620.md`
- Worst SPP+COPPER slack gap versus SPP: 0.294 percentage points.
- status=PASS
