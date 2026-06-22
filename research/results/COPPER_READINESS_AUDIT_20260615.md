# COPPER Readiness Audit, 2026-06-15

## What Improved In This Pass

- Added public Olden AArch64 full-system evaluation for `treeadd`, `bisort`,
  `mst`, and `health`.
- Added randomized-allocation Olden sensitivity to separate allocator-local
  stride behavior from pointer-provenance behavior.
- Added COPPER no-PEB vs PEB isolation on randomized Olden.
- Added a Bisort fingerprint validation build and full-system baseline/COPPER
  runs showing identical count/checksum/histogram hashes across phases.
- Added a medium randomized Olden subset (`treeadd 17`, `bisort 8192`,
  `health 5`) to test scale beyond the first small suite.
- Added gem5 built-in BOP, SPP, DCPT, AMPM, indirect-memory, and ISB baselines
  on randomized Olden small and medium subsets.
- Reran Vivado 2025.2 authority-chain XSIM, PEB XSIM, CLPD SRAM synthesis, and
  64K CLPD out-of-context place-and-route.
- Refreshed prior-art comparison against DMPs, pointer prefetchers,
  content-directed prefetch patents, and prefetch side-channel work.

## Strongest Current Claims

| Claim | Current evidence | Strength |
|---|---|---|
| COPPER is not just a confidence-filtered DMP | Prior-art table plus invariant: commit-created source proof, CLPD, CTLW, PEB, CS-SARI | Strong |
| COPPER suppresses unsafe/unproven content-derived issue | Heap fake-only, GAPBS, Olden, RTL/SVA authority chains, bounded checkers | Strong |
| COPPER keeps useful pointer-prefetch performance on targeted pointer workloads | Heap ROI multi-seed: CLPD-64K+PEB mean -2.905% vs none; structure/control workloads | Moderate to strong |
| COPPER is safe but not always faster than naive DMP | Medium Olden: COPPER -2.616%, naive -2.829%, but COPPER cuts CTLW misses by 61.8% | Strong and honest |
| COPPER is not a general-purpose prefetch replacement | Randomized Olden: DCPT -5.742% small / -7.025% medium; SPP -2.963% small / -5.870% medium; AMPM -2.465% small / -3.909% medium; COPPER -0.398% small / -2.616% medium | Strong and honest |
| 64K CLPD is hardware-plausible | Vivado A200T synthesis and route: 260 BRAM tiles, 636 LUTs, 170 FFs, +0.362 ns WNS at 10 ns | Moderate to strong |

## New Olden Results

| Workload | Policy | Mean tick delta vs none | PF issued | CTLW misses | Blocked no provenance | Faults |
|---|---|---:|---:|---:|---:|---:|
| Small randomized Olden | stride | +10.107% | 1,754,572 | 0 | 0 | 0 |
| Small randomized Olden | BOP | +0.271% | 2,992,528 | 0 | 0 | 0 |
| Small randomized Olden | SPP | -2.963% | 17,921,165 | 0 | 0 | 0 |
| Small randomized Olden | DCPT | -5.742% | 14,541,439 | 0 | 0 | 0 |
| Small randomized Olden | AMPM | -2.465% | 22,107,403 | 0 | 0 | 0 |
| Small randomized Olden | indirect-memory | -1.469% | 7,196,271 | 0 | 0 | 0 |
| Small randomized Olden | ISB | -0.045% | 403,654 | 0 | 0 | 0 |
| Small randomized Olden | naive | +0.039% | 349,965 | 188,223 | 0 | 0 |
| Small randomized Olden | COPPER CLPD-64K+PEB | -0.398% | 547,939 | 29,039 | 320,013 | 0 |
| Medium randomized Olden subset | stride | +11.565% | 3,416,573 | 0 | 0 | 0 |
| Medium randomized Olden subset | BOP | -4.036% | 5,283,506 | 0 | 0 | 0 |
| Medium randomized Olden subset | SPP | -5.870% | 29,679,379 | 0 | 0 | 0 |
| Medium randomized Olden subset | DCPT | -7.025% | 26,705,188 | 0 | 0 | 0 |
| Medium randomized Olden subset | AMPM | -3.909% | 40,142,406 | 0 | 0 | 0 |
| Medium randomized Olden subset | indirect-memory | -0.480% | 13,132,519 | 0 | 0 | 0 |
| Medium randomized Olden subset | ISB | -0.695% | 676,501 | 0 | 0 | 0 |
| Medium randomized Olden subset | naive | -2.829% | 192,298 | 123,516 | 0 | 0 |
| Medium randomized Olden subset | COPPER CLPD-64K+PEB | -2.616% | 639,330 | 47,145 | 185,023 | 0 |

Interpretation: Olden supports the safety-bounded DMP thesis. It does not
support claiming COPPER is an unconditional speed winner over unconstrained
naive DMP or over conventional address-correlation prefetchers.

## Current Scores

| Dimension | Score | Reason |
|---|---:|---|
| Novelty risk | 3/10 | Closest work covers DMP/content-directed/pointer prefetching, but not the full commit-provenance authority invariant. |
| Feasibility | 8/10 | gem5 full-system, RTL/SVA, Vivado synthesis, and routed CLPD evidence exist. |
| Measurability | 9/10 | The project now has timing, prefetch, witness-miss, blocked-candidate, fault, storage, and RTL coverage metrics. |
| Hardware cost | 7/10 | Logic is modest; 64K CLPD uses substantial BRAM but routes on A200T. ASIC SRAM modeling remains missing. |
| Paper strength | 7/10 | Strong mechanism and safety evidence; built-in baselines force careful positioning away from "best performance." |
| Publish-worthiness | 7/10 | Strong workshop or architecture-security venue candidate now; top-tier architecture still needs broader external pointer-heavy workloads and a cleaner safety/performance objective. |

## Reviewer Risks

- Reviewers may say the performance win is too workload-specific.
- Reviewers may prefer comparing against a documented production DDP, but public
  details are limited.
- Reviewers may say FPGA BRAM evidence is not an ASIC CPU cost model.
- Reviewers may object that full-system GAPBS is real but not pointer-heavy.
- Reviewers may see medium Olden naive DMP as slightly faster and ask why COPPER
  is worth the complexity.
- Reviewers may note that DCPT/SPP outperform COPPER on randomized Olden and
  require a clear explanation that those are conventional prefetchers, not safe
  content-derived DMP baselines.
- The indirect-memory baseline required a local gem5 guard so it checks
  `PrefetchInfo::hasData()` before reading request data in this full-system
  path. This is a simulator compatibility fix and should be disclosed if those
  indirect-memory numbers are used.

## Best Positioning

Do not sell COPPER as "the fastest prefetcher." Sell it as:

> a concrete, RTL-backed authority mechanism that recovers much of
> data-dependent pointer-prefetch benefit while making content-derived issue
> conditional on committed provenance, target witness authority, and scoped
> revocation.

## Honest Verdict

Current verdict: **Needs more evidence for a top PhD architecture conference;
strong workshop / architecture-security submission candidate.**

The project is meaningfully beyond a toy combination of blocks. The remaining
gap is not "make up a new mechanism"; the mechanism is now defensible. The gap
is broader external evaluation and sharper comparison against state-of-the-art
prefetchers under the same simulator and workloads.
