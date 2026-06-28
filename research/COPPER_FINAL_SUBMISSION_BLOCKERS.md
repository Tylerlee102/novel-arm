# COPPER Final Submission Blockers

| Class | Blocker | Evidence | Required fix |
| --- | --- | --- | --- |
| SERIOUS BUT CAVEATABLE | Gem5 evidence is limited to imported MiBench Patricia ARM-system summaries; independent_sim remains source-backed trace/event validation. | gem5_performance.csv; gem5_prefetch_metrics.csv; gem5_memory_traffic.csv; independent_sim_performance.csv; independent_sim_prefetch_metrics.csv; independent_sim_memory_traffic.csv | Run the same full workload/config matrix in gem5 or another accepted external simulator before making top-tier architecture claims. |
| TOP-TIER BLOCKER | No full-core matched timing/area/power result. PicoRV32 core-wrapper rows are stronger than near-core stubs but still not full-core. | fullcore_synthesis.csv; fullcore_synthesis_overhead.csv; mapped_ppa.csv | Integrate baseline and COPPER into the actual target core/full-core wrapper before making full-core claims. |
| SERIOUS BUT CAVEATABLE | Near-core-stub synthesis is not full-core overhead. | fullcore_synthesis_overhead.csv; mapped_ppa.csv | Keep the scope labeled near_core_stub everywhere. |
| TOP-TIER BLOCKER | Power evidence is Vivado FPGA tool-estimated power plus proxy/model energy, not silicon measurement, ASIC signoff, or full-core signoff power. | mapped_ppa.csv; energy_proxy.csv; energy_summary.csv; power_report_index.csv; copper_mcpat_sensitivity_20260618.csv | Add full-core or ASIC-calibrated power before claiming full-system power efficiency. |
| SERIOUS BUT CAVEATABLE | Some workloads regress versus the best baseline. | cycle_performance.csv; core_integrated_performance.csv | Discuss regressions directly and keep speedup claims per-row. |
| SERIOUS BUT CAVEATABLE | Main-branch Actions status was not verifiable in Phase 0. | preflight_baseline_check.csv | Verify main branch separately before release claims. |
| NICE TO HAVE | Local Windows cannot run paper/RTL/synthesis/workload compilers. | tooling_availability.md | Use Docker/Codespaces/GitHub Actions as the proof environment. |
| FUTURE WORK | ASIC-calibrated PPA is absent. | synthesis.csv; fullcore_synthesis.csv; mapped_ppa.csv | Add ASIC/OpenROAD-style reports if silicon-grade PPA is needed. |
