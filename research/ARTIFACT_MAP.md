# COPPER Artifact Map

## Source

Source includes the Python model and analysis scripts under `research/*.py` and `research/scripts/*.py`, SystemVerilog RTL and testbenches under `research/*.sv`, C/C++ workload sources under `research/aarch64_*`, reproduction wrappers at the repository root, and the paper source under `research/paper`.

## Generated

Generated evidence lives under `research/results`. The new conference-facing generated CSVs are `toolchain_status.csv`, `model_tests.csv`, `rtl_compile.csv`, `rtl_simulation.csv`, `benchmark_inventory.csv`, `baseline_inventory.csv`, `performance.csv`, `prefetch_metrics.csv`, `memory_traffic.csv`, `ablation.csv`, `sensitivity.csv`, `seed_stability.csv`, `statistical_summary.csv`, `synthesis.csv`, `synthesis_overhead.csv`, `ci_status.csv`, `ci_artifacts_manifest.csv`, `ci_failure_summary.csv`, `artifact_inventory.csv`, and `artifact_manifest.csv`. Tool logs for open-source hardware gates are written under `research/results/logs/`.

## Evidence

Evidence used by the paper and dashboard comes from generated CSVs, existing gem5 summary CSVs, existing Vivado reports, and explicit logs. Paper claims are controlled by `research/COPPER_CLAIM_LEDGER.md`.

## Old Or Local-Only

Large simulator outputs, Vivado scratch directories, DCP files, WDB files, SAIF/VCD waveforms, and raw gem5 folders are treated as local-only unless they are small summary files or explicitly listed in the package manifest. The package script records excluded heavy artifacts rather than hiding them.

## First Reviewer Command

Run `make check-toolchain` to see the local tool state, then `make readiness` in Docker/CI or Codespaces for the complete portable pass. Local Windows is editing-only for the final hardware and paper gates. If GitHub CLI or Docker is unavailable locally, use the GitHub web UI path in `docs/RUN_CI_NOW.md`. If a tool is missing, the relevant gate should read BLOCKED or PARTIAL instead of silently passing.
