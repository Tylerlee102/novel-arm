# COPPER Related Work Matrix

This matrix states distinctions without using broad priority claims.

| Area | What prior work does | What COPPER does differently | What COPPER does not claim | Evidence supporting distinction |
| --- | --- | --- | --- | --- |
| stride prefetchers | Predict regular address deltas. | Uses committed pointer-source evidence for data-derived candidates. | COPPER does not replace stride on sequential kernels. | baseline_inventory.csv; performance.csv |
| next-line prefetchers | Fetch adjacent cache lines. | Targets pointer-derived streams rather than adjacency. | Does not claim next-line is broadly dominated. | baseline_inventory.csv |
| stream prefetchers | Track streams and correlations. | Can coexist as SPP plus COPPER slack in existing summaries. | COPPER does not claim better raw timing than SPP. | performance.csv |
| pointer-chase prefetchers | Follow linked structures or indirect addresses. | Requires committed source-word proof before data-derived issue. | Does not claim pointer prefetching itself is new. | model_tests.csv; COPPER_PRIOR_ART.md |
| dependence/provenance-based prefetching | Uses dependence or provenance-like information to guide prefetch. | Narrows provenance to committed source-word authority for DMP issue. | Does not claim all provenance mechanisms are new. | COPPER_PRIOR_ART.md |
| prefetch filtering/confidence mechanisms | Filter low-confidence prefetches. | Filters by architectural proof, not just usefulness confidence. | Confidence-threshold sensitivity remains TODO. | sensitivity.csv |
| runahead execution | Executes ahead to expose misses. | Allows recursive carried provenance only with committed source proof. | Not a general runahead engine. | COPPER_FULL_PAPER.md |
| helper-thread prefetching | Uses software or hardware helpers. | Keeps policy in the prefetch authority path. | Does not claim helper-thread comparison evidence. | COPPER_RELATED_WORK_MATRIX.md |
| memory-dependence prediction | Predicts memory ordering/dependence behavior. | Uses committed pointer-source facts to gate prefetch issue. | Not a memory-order predictor. | COPPER_PRIOR_ART.md |
| hardware/software cooperative prefetching | Uses software hints or compiler/runtime cooperation. | Requires no source transformation in the modeled mechanism. | Does not claim compiler approaches are obsolete. | COPPER_PRIOR_ART.md |
