# COPPER Final Reviewer Report

## Computer Architecture Reviewer

Leaning: workshop accept / top-tier reject. Strengths: clear committed-provenance invariant, CI-proven RTL unit simulation, source workload build path, deterministic cycle-model rows, and deterministic core-integrated rows across positive, negative, and stress workloads. Weaknesses: Phase 0 confirms gem5 is not runnable in this environment; the core-integrated harness is deterministic and repo-local, not an independent simulator. Fatal blockers: no real gem5 or comparable external core simulator campaign. Required fixes: validate the same workload/config matrix in gem5 or another independent core simulator. Claim risks: performance claims must stay per-row and evidence-level scoped. Phase 0 discrepancy check: claimed PR/push evidence matched; main-branch Actions state was not verifiable because the API returned no main runs, so main-branch status must not be cited.

## Prefetching And Memory-Systems Reviewer

Leaning: weak accept for scoped mechanism, reject for replacement claims. Strengths: committed pointer-source authority is crisp; cycle and core-integrated tables include accuracy, coverage, lateness, queue drops, traffic, negative workloads, and sensitivity. Weaknesses: several COPPER rows trail the best baseline, and gem5 remains BLOCKED. Fatal blockers: any universal-speedup or broad-dominance language would be fatal. Required fixes: keep regression discussion visible and compare per workload/configuration. Claim risks: do not imply COPPER replaces stride/stream/unsafe pointer-chase prefetchers. Phase 0 discrepancy check: no claimed metric row-count mismatch found.

## Hardware Implementation Reviewer

Leaning: artifact accept / architecture-paper reject. Strengths: SystemVerilog unit, CI-proven open-source simulation, matched unit-level synthesis, and an added near-core-stub synthesis target. Weaknesses: Phase 0 found no local Yosys/Vivado; CI is the proof environment. Near-core-stub evidence is not full-core implementation, and generic Yosys has no mapped timing or power. Fatal blockers: full-core overhead/timing and measured power are unsupported. Required fixes: integrate into a real core or accepted open-source core wrapper and close timing under a mapped flow. Claim risks: near-core-stub must never be called full-core. Phase 0 discrepancy check: existing Vivado scratch directories do not imply runnable Vivado.

## Evaluation And Statistics Reviewer

Leaning: workshop accept if scoped, top-tier weak reject. Strengths: deterministic cycle and core-integrated rows cover seeds 1-3, multiple input sizes, and both positive/control/stress workloads; regressions are retained. Weaknesses: the core-integrated model is deterministic and shares workload/model ancestry with the cycle model, so it is not independent validation. Fatal blockers: no independent simulator statistics. Required fixes: add external simulator runs and confidence intervals from those runs. Claim risks: robust speedup must be described per benchmark/configuration, not as a suite-wide win. Phase 0 discrepancy check: row counts matched claimed 630/630/630.

## Artifact Evaluation Reviewer

Leaning: accept for artifact if final branch CI passes. Strengths: Phase 0 preserved prior CI proof, the pass adds explicit preflight/tooling evidence, source workload build scripts, core-integrated logs, near-core-stub synthesis scripts, and proxy energy ledgers. Weaknesses: local Windows cannot build paper, RTL, Yosys, or workloads; GitHub Actions/Docker/Codespaces is the intended proof path. Fatal blockers: final branch CI failure or package failure. Required fixes: keep artifact uploads and dashboards tied to the current run. Claim risks: local generated BLOCKED rows must not be promoted over CI PASS rows. Phase 0 discrepancy check: main branch Actions status was not verifiable.

## Skeptical Novelty Reviewer

Leaning: reject for broad novelty, acceptable for a narrow artifact/mechanism paper. Strengths: the committed-provenance authority invariant is concrete and has model, cycle-model, core-integrated, RTL-unit, and synthesis-scope support. Weaknesses: adjacent pointer-chase, taint, capability, dependence, and DMP-defense work is crowded; this pass did not perform a fresh literature audit. Fatal blockers: any first/priority/state-of-the-art language would be fatal. Required fixes: update the related-work matrix before aiming at a top-tier venue. Claim risks: paper must not imply gem5, full-core, measured power, or universal superiority. Phase 0 discrepancy check: unresolved main-branch status is at least SERIOUS BUT CAVEATABLE for release claims.
