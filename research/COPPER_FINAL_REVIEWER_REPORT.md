# COPPER Final Reviewer Report

## Computer Architecture Reviewer

Leaning: borderline workshop-to-conference artifact, not top-tier-ready without a stronger simulator campaign. Strengths: clear invariant, CI-proven RTL unit simulation, CI-proven paper/artifact path, model evidence, cycle-model rows across positive, negative, and stress workloads, and matched unit-level synthesis evidence. Weaknesses: the new timing evidence is a deterministic cycle model, not gem5 or a production-core integration. Fatal blockers: none for a scoped artifact paper; serious blocker for MICRO/ISCA-style submission is lack of a fresh gem5 or core-integrated run. Required fixes: validate the cycle trends in gem5 or a comparable core model. Claim risks: raw-speed claims must remain per-workload and evidence-level scoped.

## Prefetching And Memory-Systems Reviewer

Leaning: weak accept for a scoped artifact, reject for broad replacement claims. Strengths: committed pointer-source authority is crisp, and the cycle-model tables now include lateness, queue drops, traffic, negative workloads, and sensitivity. Weaknesses: some rows show COPPER slower than the best baseline or less useful than unsafe pointer chasing. Fatal blockers: none if the paper keeps the scope narrow. Required fixes: discuss regressions directly. Claim risks: do not present COPPER as a universal prefetcher replacement.

## Hardware Implementation Reviewer

Leaning: artifact accept / architecture-paper weak reject. Strengths: SystemVerilog unit, CI-proven open-source simulation, and matched Yosys/nextpnr unit-level overhead rows. Weaknesses: no full-core integration, no ASIC PPA, and no power report. Fatal blockers: full-core overhead and timing claims remain unsupported. Required fixes: synthesize a full-core baseline and COPPER variant under the same flow if the paper needs full-core cost. Claim risks: unit-level FPGA evidence must stay unit-level.

## Evaluation And Statistics Reviewer

Leaning: weak accept if scoped as model plus cycle-model evidence. Strengths: cycle-model statistics now cover seeds 1-3 and small/medium/large inputs, and regressions are not hidden. Weaknesses: the confidence intervals are from a deterministic synthetic cycle model, not independent hardware measurements. Fatal blockers: none for a scoped artifact; gem5 remains needed for a stronger claim. Required fixes: add gem5 validation. Claim risks: robust speedup must be described per benchmark/configuration.

## Artifact Evaluation Reviewer

Leaning: accept for artifact. Strengths: GitHub Actions passes, CI evidence is imported, artifact packaging includes the generated evidence, and local Windows remains clearly marked editing-only. Weaknesses: full gem5/Vivado reruns still depend on external setup. Fatal blockers: none for the open-source artifact path. Required fixes: keep CI artifact imports current after major evidence changes. Claim risks: clone-local reproducibility must not be confused with the long external-tool campaign.

## Skeptical Novelty Reviewer

Leaning: weak reject for broad novelty, acceptable for narrow mechanism. Strengths: the committed-provenance authority invariant is concrete and now has model, cycle-model, RTL, and synthesis support. Weaknesses: adjacent pointer-chase, taint, capability, and DMP-defense work is crowded. Fatal blockers: no fresh formal literature review in this pass. Required fixes: keep distinction language and avoid priority language. Claim risks: priority claims remain forbidden.
