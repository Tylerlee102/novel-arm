# COPPER Reviewer Response Notes

## 1. What hardware evidence backs the submission?

The artifact has unit evidence, near-core-stub evidence, accepted-core-wrapper evidence, and PicoRV32 tiny-SoC full-core rows only where the generated CSVs mark those rows PASS. This supports the conference package at those evidence levels. It is not production ARM/OoO evidence.

## 2. Is the power measured or estimated?

Estimated/proxy only. Vivado rows are FPGA tool estimates, OpenROAD/ASIC-Liberty rows are tool estimates when indexed, and McPAT/memory-energy rows are proxy evidence. The repo has no measured silicon power claim.

## 3. Why is this not silicon-proven?

No. There is no PASS fabricated-silicon manifest, no tapeout/fabrication/package/bring-up evidence, and no post-silicon validation. The stronger-claim audit blocks unqualified silicon wording.

## 4. Is the comparison to prior work fair?

Yes only within the stated evidence level. The paper compares generated model, cycle-model, core-integrated, independent-sim, imported gem5, FPGA PPA, and proxy/tool-power rows separately. It does not compare FPGA/tool estimates against silicon-measured prior work as if they were equivalent.

## 5. Are negative/regression cases shown?

Yes. The CSVs retain per-workload rows, including cases where COPPER trails the best baseline. This blocks a universal-speedup claim.

## 6. Can the artifact reproduce the claims?

For the evidence-bounded claims, yes when the CI/Docker/Codespaces path is used. The expected checks are paper build, artifact package, claim/number/TODO/stronger-claim audits, RTL unit simulation, independent simulator rows, and hardware evidence ledgers.

## 7. What exactly is novel?

The contribution is the committed pointer-provenance authority rule for data-derived prefetch issue: a candidate must be backed by committed source-word evidence and must survive invalidation, permission, and context checks before issue. The paper does not claim pointer prefetching itself is new.

## Current Readiness

SUBMISSION-READY for the evidence-bounded COPPER conference submission package.
