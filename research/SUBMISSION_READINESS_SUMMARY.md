# COPPER Submission Readiness Summary

## Target Submission Type

Regular conference paper with an artifact/reproducibility package. The paper should be framed as an evidence-bounded reproducible hardware mechanism study.

## Strongest Supported Claims

- COPPER is a committed pointer-provenance prefetch mechanism.
- CI/Docker/Codespaces reproduce the open-source checks when the workflow passes.
- RTL unit simulation, model tests, independent simulator evidence, raw gem5 full-system provenance where retained, and validated imported gem5 ARM-system rows support the evidence-bounded evaluation.
- Accepted-core-wrapper/PicoRV32 tiny-SoC full-core FPGA mapped PPA may be cited only where generated rows PASS.
- FPGA tool-estimated power and proxy energy may be cited with caveats.

## Claims Still Forbidden

- Do not claim silicon-proven, taped-out, fabricated-chip, or post-silicon validation.
- Do not claim ASIC/foundry signoff or full silicon PPA.
- Do not claim measured silicon power.
- Do not claim production ARM/OoO/TLB/cache/coherence/interrupt integration.
- Do not claim state-of-the-art silicon efficiency, universal speedup, or production-ready status.

## Exact CI Run

Last imported artifact evidence: GitHub Actions run 28321186683 imported at 20260628_051002. Final release evidence is the GitHub Actions run for the submitted commit; attach that run URL at submission time.

## Artifact Path

`dist/copper-artifact.zip` if present after `make artifact`.

## Paper Path

`research/paper/main.pdf` if present after `make paper`.

## Remaining Limitations

- Full gem5 raw reruns are not clone-local for every imported summary row.
- PicoRV32 tiny-SoC evidence is the open-source full-core harness, not production ARM/OoO integration.
- Power is tool-estimated or proxy/model based, not measured silicon.
- Stronger silicon/signoff/commercial-production claims remain blocked by missing physical evidence.

## Recommendation

Submit as an evidence-bounded regular conference or artifact-track package after the final main-branch CI run for the submitted commit is attached.
