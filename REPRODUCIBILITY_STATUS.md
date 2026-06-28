# COPPER Reproducibility Status

This repository is a compact public artifact package, not a complete virtual
machine or one-command full-system artifact.

## Reproducible From This Repository

- `reproduce.ps1`, `reproduce.sh`, or `python reproduce.py --mode all-local`
  reruns the clone-local reproduction path and writes
  `research/results/reproduction/LOCAL_REPRODUCTION_REPORT.md`.
- In a Linux container, Codespaces, or GitHub Actions runner with the Dockerfile
  dependencies, the open-source flow runs through `make check-toolchain`,
  `make test`, `make rtl`, `make sim`, `make eval`, `make synth`,
  `make paper`, `make paper-audit`, and `make artifact`.
- The model-level evaluation regenerates same-path baselines for
  `no_prefetch`, `next_line`, `stride`, `simple_pointer_chase`, and `copper`,
  including queue drops, lateness, accuracy, coverage, traffic overhead,
  ablations, sensitivity, and seed/input stability.
- The deterministic cycle-model evaluation regenerates `cycle_performance.csv`,
  `cycle_prefetch_metrics.csv`, and `cycle_memory_traffic.csv` for the same
  baseline names. It models cache hit/miss latency, memory latency, outstanding
  prefetches, queue drops, lateness, and demand/prefetch traffic, but it is not
  gem5.
- `make workloads` builds the public C workload driver from source when a C
  compiler is available and records one row per required workload in
  `research/results/workload_build.csv`.
- `research/scripts/run_independent_sim_eval.py` requires PASS source-workload
  build rows, executes the compiled workload driver for each required
  benchmark, and writes `independent_sim_*` CSVs from a separate trace/event
  simulator. This is independent of the cycle-model and core-integrated
  harnesses, but it is not gem5.
- The top-tier pass adds deterministic `core_integrated` CSVs. This is a
  core-envelope validation harness with fetch/issue, reorder-window,
  load-queue, branch, and memory timing parameters. It is not gem5 and does not
  replace a full-system simulator campaign.
- `gem5_*.csv` files are allowed to be BLOCKED. A BLOCKED gem5 row is not
  performance evidence; it records that gem5 was unavailable or not runnable in
  the current environment.
- `fullcore_synthesis*.csv` records unit and near-core-stub synthesis scope.
  Near-core-stub rows must not be described as full-core overhead, mapped
  timing, or measured power.
- `mapped_ppa.csv` and `mapped_ppa_overhead.csv` are the only open-source
  mapped-PPA ledgers. They record BLOCKED when Yosys, nextpnr, OpenROAD, Vivado,
  or required platform data are unavailable, FAIL when a real mapping attempt
  does not complete, and PASS only when a mapped flow finishes with timing
  fields from the tool report. Missing timing or power fields are recorded as
  `NA`, not inferred.
- `energy_proxy.csv`, `energy_summary.csv`, `power_report_index.csv`,
  `mapped_ppa.csv`, and `copper_mcpat_sensitivity_20260618.csv` separate
  assumption-based memory energy, activity-based McPAT proxy evidence, and
  Vivado `report_power` rows when Vivado is available. Vivado power rows are
  tool-estimated FPGA power for the stated mapped target, not measured silicon,
  ASIC signoff power, or full-core power.
- Paper-facing documents, tables, summaries, RTL sources, testbenches, and
  reproduction scripts are included with stable relative paths.
- The Python audit and summary scripts can be rerun with a local Python 3
  interpreter, subject to normal package availability.
- Included measured-summary files can be checked against the claim matrix and
  artifact manifest.
- MiBench Patricia source and public inputs used by the 12K seed-stability
  result are included under `external/`.
- Vivado RTL simulations and synthesis scripts are included, but require a
  local Vivado installation and may need path edits for the installed version.
- Local Windows is editing-only for final open-source RTL, Yosys synthesis,
  paper PDF, and artifact-package proof. It may edit files, run Python syntax
  checks, commit, push, or trigger CI, but it must not decide final PASS status
  for those gates.
- GitHub Actions, Docker, and Codespaces are the intended source of truth for
  the open-source hardware and paper gates. Missing local tools are not a
  license to substitute fake reports.
- This checkout includes imported GitHub Actions proof for the open-source RTL,
  synthesis, paper, audit, and artifact-packaging gates. Future evidence changes
  should still be imported with `research/scripts/import_ci_artifacts.py` before
  promoting new CI-backed claims.

## Requires External Setup

- Full-system AArch64/gem5 reruns require a local gem5 build, guest/runtime
  setup, cross-compilation support, and workload staging environment. Those
  large toolchain and simulator artifacts are not stored in this compact repo.
- The repo includes result summaries and runner scripts for the full-system
  points, but a fresh clone alone is not sufficient to regenerate every raw
  gem5 run.
- Two large SAIF power-activity files are intentionally excluded from the compact
  package and recorded by SHA-256 in the public artifact manifest.

## Honest Interpretation

Reviewers can audit the reported evidence, rerun many Python and RTL checks with
standard tools, and reproduce selected public-workload points after installing
the external simulator/toolchain stack. They should not expect a fresh clone to
reproduce the entire long-running full-system campaign without that setup.

The model-level, cycle-model, core-integrated, and independent-sim evidence
improve baseline discipline but do not replace real gem5/full-system evidence.
Claims in the paper and claim ledger must identify model-level, cycle-model,
core-integrated, independent-sim, RTL-level, unit-synthesis,
near-core-stub synthesis, mapped-PPA, proxy-energy, existing-Vivado, and
external summary evidence separately.

The clone-local runner is intended to make this boundary explicit: it should pass
from a fresh clone after Python dependencies are installed, while full gem5 and
Vivado reruns remain external-tool modes.
