# COPPER Reproducibility Status

This repository is a compact public artifact package, not a complete virtual
machine or one-command full-system artifact.

## Reproducible From This Repository

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
