# COPPER Final Submission Blockers

| Class | Blocker | Evidence | Required fix |
| --- | --- | --- | --- |
| SERIOUS BUT CAVEATABLE | Cycle-model evidence is synthetic rather than gem5/core-integrated. | cycle_performance.csv; cycle_prefetch_metrics.csv | Validate the trends in gem5 or a comparable core model before making broad architecture claims. |
| SERIOUS BUT CAVEATABLE | Full-core overhead and timing are absent. | synthesis.csv; synthesis_overhead.csv | Keep hardware claims unit-level or synthesize full-core baseline and COPPER variants in the same flow. |
| SERIOUS BUT CAVEATABLE | Power efficiency is not measured. | synthesis.csv; existing power proxy files | Do not claim power efficiency without a real report. |
| SERIOUS BUT CAVEATABLE | Some workloads regress versus the best baseline. | cycle_performance.csv | Discuss regressions directly and keep speedup claims per-row. |
| NICE TO HAVE | Gem5 rerun is still external-tool setup. | REPRODUCIBILITY_STATUS.md | Containerize or document the full simulator stack if broader claims are needed. |
| FUTURE WORK | ASIC-calibrated PPA is absent. | synthesis.csv; synthesis_overhead.csv | Add ASIC/OpenROAD-style reports if silicon-grade PPA is needed. |
