# COPPER Final Submission Blockers

| Class | Blocker | Evidence | Required fix |
| --- | --- | --- | --- |
| SERIOUS BUT CAVEATABLE | Gem5 remains unavailable; independent_sim is source-backed trace/event validation, not a full-system external simulator. | gem5_performance.csv; independent_sim_performance.csv; independent_sim_prefetch_metrics.csv; independent_sim_memory_traffic.csv | Run the same workload/config matrix in gem5 or another accepted external simulator before making top-tier architecture claims. |
| FATAL | No full-core matched timing/area/power result. | fullcore_synthesis.csv; fullcore_synthesis_overhead.csv; mapped_ppa.csv | Integrate baseline and COPPER into the same real core or accepted core wrapper and close a mapped flow. |
| SERIOUS BUT CAVEATABLE | Near-core-stub synthesis is not full-core overhead. | fullcore_synthesis_overhead.csv; mapped_ppa.csv | Keep the scope labeled near_core_stub everywhere. |
| SERIOUS BUT CAVEATABLE | Energy evidence is proxy/model based, not silicon measurement or RTL signoff power. | energy_proxy.csv; energy_summary.csv; power_report_index.csv; copper_mcpat_sensitivity_20260618.csv | Add a real power report before claiming measured power efficiency. |
| SERIOUS BUT CAVEATABLE | Some workloads regress versus the best baseline. | cycle_performance.csv; core_integrated_performance.csv | Discuss regressions directly and keep speedup claims per-row. |
| SERIOUS BUT CAVEATABLE | Main-branch Actions status was not verifiable in Phase 0. | preflight_baseline_check.csv | Verify main branch separately before release claims. |
| NICE TO HAVE | Local Windows cannot run paper/RTL/synthesis/workload compilers. | tooling_availability.md | Use Docker/Codespaces/GitHub Actions as the proof environment. |
| FUTURE WORK | ASIC-calibrated PPA is absent. | synthesis.csv; fullcore_synthesis.csv; mapped_ppa.csv | Add ASIC/OpenROAD-style reports if silicon-grade PPA is needed. |
