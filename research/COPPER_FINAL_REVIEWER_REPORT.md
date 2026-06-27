# COPPER Final Reviewer Report

## Computer Architecture Reviewer

Leaning: workshop accept / conference reject. Strengths: clear invariant, real model evidence, useful full-system summaries, and an open-source RTL-unit path. Weaknesses: raw performance is not consistently better than conventional stream prefetching, and CI proof has not been collected. Fatal blockers: no full portable benchmark rerun. Required fixes: collect CI/Docker/Codespaces hardware and paper evidence, then expand workloads. Claim risks: raw-speed claims must remain per-workload.

## Prefetching And Memory-Systems Reviewer

Leaning: workshop accept. Strengths: committed pointer-source authority is a crisp selectivity idea. Weaknesses: lateness, queue behavior, and confidence sensitivities are incomplete. Fatal blockers: missing lateness and queue-capacity metrics for the normalized table. Required fixes: add direct prefetch timeliness and pollution counters. Claim risks: do not present COPPER as a universal prefetcher replacement.

## Hardware Implementation Reviewer

Leaning: weak reject for full conference. Strengths: SystemVerilog units, open-source smoke targets, and existing Vivado summaries exist. Weaknesses: no full-core integration, no ASIC PPA, no CI-proven RTL/synthesis run yet, and no CI-proven baseline overhead computation. Fatal blockers: full overhead and timing story is incomplete. Required fixes: synthesize baseline and COPPER units under the same open-source flow and collect logs/artifacts. Claim risks: unit-level FPGA evidence must stay unit-level.

## Evaluation And Statistics Reviewer

Leaning: workshop only. Strengths: seed ledgers and public workload summaries exist. Weaknesses: several public points have only two seeds and some results are model-level. Fatal blockers: broad statistical stability is incomplete. Required fixes: expand seeds and input sizes for positive and negative workloads. Claim risks: robust speedup cannot be claimed from limited seeds.

## Artifact Evaluation Reviewer

Leaning: conditional accept for artifact after CI proof. Strengths: one-command local model path, manifest, Docker/CI/Codespaces setup, web-triggerable workflow, and explicit blockers. Weaknesses: full gem5/Vivado reruns depend on external setup, and local Windows remains editing-only for proof gates. Fatal blockers: licensed/local tool reruns are not portable. Required fixes: run the workflow and import logs/artifacts. Claim risks: clone-local reproducibility must not be confused with full campaign reproducibility.

## Skeptical Novelty Reviewer

Leaning: reject until related-work story is sharpened. Strengths: the invariant is concrete and distinguishable. Weaknesses: adjacent pointer-chase, taint, capability, and DMP-defense work is crowded. Fatal blockers: no fresh formal literature review in this pass. Required fixes: keep distinction language and avoid priority language. Claim risks: priority claims remain TODO.
