# COPPER Phase 0 Tooling Availability

## Python

Present. Command: `C:\Users\tyboy\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe --version`. Observed: `Python 3.12.13`. Path: `C:\Users\tyboy\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`. Platform: `Windows-11-10.0.26200-SP0`.

## GitHub CLI

Absent. Command: `gh --version`. Result is captured in `research/results/preflight_logs/gh_version.txt`. GitHub REST API was used for run verification instead.

## gem5

Not usable in this Windows session.
Command checks: `Get-Command gem5`, `Get-Command gem5.opt`, and temporary execution probe of `external/gem5/build/ARM/gem5.opt --help`.
Local source/scratch exists: `True`.
Built-looking binary exists: `True` at `external/gem5/build/ARM/gem5.opt`.
Execution probe failed because the binary is not a valid application for this OS platform. WSL is present as a command but no Linux distribution is installed.
Conclusion: gem5 evaluation is unavailable locally; building from source is not practical in this pass because local make/compiler toolchains are absent and the existing binary cannot run here.
Evidence: `research/results/preflight_logs/gem5_probe.txt` and `research/results/preflight_logs/tool_probe.txt`.

## RTL sim

Absent locally. Commands checked: `Get-Command iverilog` and `Get-Command vvp`; both absent. CI artifact still proves RTL simulation PASS for the baseline. Evidence: `research/results/preflight_logs/tool_probe.txt` and `research/results/preflight_logs/ci_vvp_copper_prefetch_unit_open_tb.log`.

## Yosys

Absent locally. Command checked: `Get-Command yosys`; absent. CI artifact proves unit-level synthesis PASS. Evidence: `research/results/preflight_logs/tool_probe.txt`.

## Vivado/vendor

No usable Vivado/vendor executable found locally. Commands checked: `vivado`, `xvlog`, `xelab`, `xsim`; all absent. Local `2025.2/` and `.Xil/` scratch directories exist, but no runnable vendor tool was found. Evidence: `research/results/preflight_logs/tool_probe.txt`.

## Compiler/workload build

No local C compiler or build tool found. Commands checked: `make`, `gcc`, `g++`, `clang`, `cl`, `cmake`, and `ninja`; all absent. Fresh workload builds should be attempted in CI/Docker/Codespaces, not this Windows editing shell. Evidence: `research/results/preflight_logs/tool_probe.txt`.

## Power/energy

No measured power tool is available locally. Vivado power analysis is unavailable because Vivado is absent. A future energy result in this environment can only be a clearly labeled proxy unless CI or another tool produces a real power report. Evidence: `research/results/preflight_logs/tool_probe.txt`.
