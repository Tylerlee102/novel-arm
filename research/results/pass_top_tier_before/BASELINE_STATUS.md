# Phase 1 Preserved Evidence Snapshot

Baseline status from Phase 0:

- CI reproduction: PASS for PR run 28305482649 and push run 28305482024 on b17d9834ea288c505035d8921781ced3467aeadb.
- cycle_model: PASS; cycle_performance.csv, cycle_prefetch_metrics.csv, and cycle_memory_traffic.csv each have 630 rows in the final CI artifact.
- RTL unit simulation: PASS in CI with assertions_passed=15 and assertions_failed=0.
- Unit-level synthesis: PASS for matched unit-level open-source overhead rows.
- Paper build: PASS in CI; local Windows paper build is BLOCKED because latexmk/pdflatex are unavailable.
- Artifact: PASS in final CI artifact.
- gem5/core-integrated validation: missing for the baseline.
- full-core overhead/timing: missing for the baseline.
- calibrated power/energy: missing for the baseline.

See research/results/preflight_baseline_check.csv for the detailed Phase 0 verification rows.
