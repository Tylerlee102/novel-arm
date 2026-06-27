# COPPER Final Submission Blockers

| Class | Blocker | Evidence | Required fix |
| --- | --- | --- | --- |
| FATAL | Full campaign is not one-command reproducible from a fresh clone. | REPRODUCIBILITY_STATUS.md; CONFERENCE_READINESS_DASHBOARD.md | Provide containerized gem5/workload inputs or narrow submission claims to portable evidence. |
| FATAL | GitHub Actions/Docker/Codespaces proof has not been collected. | ci_status.csv; docs/RUN_CI_NOW.md | Run the workflow from the GitHub web UI or Docker/Codespaces path and import logs/artifacts. |
| FATAL | No complete baseline-vs-COPPER hardware overhead table. | synthesis_overhead.csv | Synthesize matched baseline and COPPER units under the same flow. |
| SERIOUS BUT CAVEATABLE | Lateness and queue-capacity metrics are model-level rather than full-system counters. | prefetch_metrics.csv | Keep the paper wording model-level or add full-system simulator counters. |
| SERIOUS BUT CAVEATABLE | Statistical stability is uneven across workload families. | statistical_summary.csv | Add at least three seeds and multiple sizes for key positive and negative workloads. |
| SERIOUS BUT CAVEATABLE | Conventional prefetchers can win raw timing. | performance.csv | Frame COPPER as selectivity/safety authority and coexistence, not universal speed. |
| NICE TO HAVE | Open-source synthesis is blocked when Yosys is unavailable locally. | synthesis.csv | Use CI/Docker/Codespaces for the open-source synthesis pass; local Windows is editing-only for final proof. |
| FUTURE WORK | ASIC-calibrated power and full-core timing are absent. | synthesis.csv; existing power proxy files | Run an ASIC or OpenROAD-style flow if the claim needs silicon-grade PPA. |
