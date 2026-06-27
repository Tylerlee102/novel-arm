# COPPER Conference Readiness Dashboard

This dashboard is intentionally strict. PASS means the current artifact has reproducible evidence for that gate. PARTIAL means useful evidence exists but is not yet enough for a full conference submission.

Local Windows is editing-only. GitHub Actions/Codespaces/Docker is the intended evidence environment for open-source hardware and paper gates.

| Gate | Required for full submission? | Current status | Evidence file/script | Pass condition | Blocker |
| --- | --- | --- | --- | --- | --- |
| G1. Open-source CI/Docker reproduction | Yes | PARTIAL | Makefile; Dockerfile; .github/workflows/reproduce.yml; .devcontainer/devcontainer.json; research/results/ci_status.csv | make readiness completes in GitHub Actions, Docker, or Codespaces with logs/artifacts | CI/Docker/Codespaces proof has not been imported. Local Windows is editing-only. |
| G2. Toolchain detection | Yes | PASS | research/scripts/check_toolchain.py; research/results/toolchain_status.csv | Required tools are detected and missing tools are explicit |  |
| G3. Functional model tests | Yes | PASS | research/results/model_tests.csv; research/scripts/copper_eval_model.py | Directed tests pass and unmodeled behaviors are labeled |  |
| G4. SystemVerilog RTL compile | Yes | BLOCKED | research/results/rtl_compile.csv; research/results/logs/rtl/ | Open-source smoke compile passes in GitHub Actions, Docker, or Codespaces | No CI/Docker/Codespaces PASS row has been collected yet. |
| G5. RTL simulation | Yes | BLOCKED | research/results/rtl_simulation.csv; research/results/logs/rtl/ | Directed RTL smoke simulation passes in GitHub Actions, Docker, or Codespaces | No CI/Docker/Codespaces PASS row has been collected yet. |
| G6. C benchmark/workload build | Yes | PARTIAL | research/results/benchmark_inventory.csv; research/aarch64_* | Workload sources and builders are inventoried | Fresh cross/full-system builds require external toolchain. |
| G7. Benchmark execution | Yes | PARTIAL | research/results/performance.csv; research/results/*_SEED_STABILITY*.md | Existing execution summaries are normalized | Not all raw runs are fresh-clone reproducible. |
| G8. Baseline prefetcher implementation | Yes | PASS | research/results/baseline_inventory.csv | No-prefetch, next-line, stride, simple pointer-chase, and COPPER run through the same model path |  |
| G9. COPPER prefetcher implementation | Yes | PASS | research/scripts/copper_eval_model.py; research/copper_prefetch_unit_open.sv; research/results/performance.csv | Model and RTL-unit implementation exist | Not a production core integration. |
| G10. Prefetch usefulness/accuracy/coverage metrics | Yes | PASS | research/results/prefetch_metrics.csv | Issued/useful/useless/late/queue/coverage/accuracy metrics are generated |  |
| G11. Speedup/performance metrics | Yes | PARTIAL | research/results/performance.csv | Per-workload speedup versus no-prefetch is reported | No claim of broad benchmark-suite win. |
| G12. Memory traffic/bandwidth overhead metrics | Yes | PASS | research/results/memory_traffic.csv | Traffic overhead is generated from model memory-request counts |  |
| G13. Sensitivity studies | Yes | PASS | research/results/sensitivity.csv | Queue, confidence, chain depth, distance, table size, and latency sensitivities are captured |  |
| G14. Ablation studies | Yes | PASS | research/results/ablation.csv | A0-A5 model-level ablations are generated |  |
| G15. Area/resource/timing synthesis | Yes | PARTIAL | research/results/synthesis.csv; research/results/synthesis_overhead.csv; research/results/logs/synthesis/ | Matched unit-level overhead exists from the same GitHub Actions, Docker, or Codespaces flow | No open-environment matched overhead row has been collected yet. |
| G16. Power/energy proxy or measured estimate | Yes | PARTIAL | research/results/COPPER_RTL_POWER_PROXY_20260618.md; research/results/copper_rtl_power_proxy_20260618.csv | Proxy evidence is identified | Not calibrated full-chip power. |
| G17. Statistical stability across seeds/input sizes | Yes | PASS | research/results/seed_stability.csv; research/results/statistical_summary.csv | Model stability covers seeds 1-3 and multiple input sizes |  |
| G18. Artifact package | Yes | PARTIAL | dist/copper-artifact.zip; research/results/artifact_manifest.csv; research/results/ci_artifacts_manifest.csv | Package regenerates in GitHub Actions, Docker, or Codespaces and the zip appears in imported artifacts | Local package output is not final packaging proof. |
| G19. Paper build | Yes | BLOCKED | research/paper/main.tex; research/results/paper_build_status.csv | PDF builds in GitHub Actions, Docker, or Codespaces | No CI/Docker/Codespaces paper PASS row has been collected yet. |
| G20. Claim audit | Yes | PASS | research/scripts/audit_claims.py; research/scripts/audit_numbers.py; research/scripts/audit_todos.py | Audits pass |  |
| G21. Related work/novelty matrix | Yes | PASS | research/COPPER_RELATED_WORK_MATRIX.md | Matrix exists and avoids first/novel overclaim |  |
| G22. Reviewer attack response matrix | Yes | PASS | research/COPPER_FINAL_REVIEWER_REPORT.md | Reviewer panel and blockers exist |  |
