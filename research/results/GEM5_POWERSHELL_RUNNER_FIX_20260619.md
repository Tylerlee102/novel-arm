# gem5 PowerShell Runner Fix

Date: 2026-06-19

Purpose: remove the local dependency on an interactive Bash shell for the official OpenSSL CLI gem5 full-system runs.

Problem found:

- `bash` is not visible in the current PowerShell session.
- `wsl.exe` is present, but the existing OpenSSL CLI runners are Bash scripts with MSYS-style paths.
- Direct PowerShell execution of `external/gem5/build/ARM/gem5.fast.exe` initially failed with exit code `-1073741515`, consistent with missing runtime DLLs before gem5 could print a useful error.
- The Bash runners were implicitly adding the MSYS/UCRT runtime path.

Fix implemented:

- Added `research/run_openssl_cli_fixed_fs.ps1`.
- The runner supports `sha256`, `aesctr`, and `hmac` official OpenSSL CLI fixed-workload modes.
- It accepts tag, input byte count, seed, input/output path, key material, and policy-list parameters.
- It automatically prepends `tools/msys64/ucrt64/bin` and `tools/msys64/usr/bin` to `PATH` when the repo-local MSYS runtime exists.
- It invokes gem5 through `Start-Process` with direct stdout/stderr redirection, avoiding PowerShell's native stderr error-record wrapping.

Validation:

| Check | Result |
|---|---|
| Dry-run command construction | PASS |
| Repo-local MSYS/UCRT runtime path detected | PASS |
| Direct gem5 launch from PowerShell | PASS |
| Smoke workload | `sha256`, tag `ps_smoke2_1k_seed2`, seed 2, 1024-byte pointer-shaped input, policy `none` |
| Host markers | `COPPER_FS_HOST_SWITCH_TO_TIMING`, `COPPER_FS_HOST_WORKEND` |
| gem5 stats file | `research/results/gem5_arm_ubuntu_fs_osslcli_ps_smoke2_1k_seed2_none/stats.txt` |
| Smoke simTicks | 15,711,063,876 |
| Smoke simInsts | 18,135,009 |
| Smoke L1D demand misses | 27,752 |

Interpretation:

- The gem5/Bash blocker is fixed for the official OpenSSL CLI fixed-workload path: future runs can be launched directly from PowerShell.
- This is a reproducibility/workflow fix, not a new benchmark result and not a paper performance claim by itself.

status=PASS
