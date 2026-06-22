# Official GAPBS AArch64 Full-System SUITE_FINAL g14 Summary

This summarizes the first local official GAPBS C++ AArch64 full-system suite
for COPPER. The public GAPBS C++ sources were cross-built with clang++/lld
against an extracted ARM64 Ubuntu 24.04 sysroot from the gem5 disk image,
copied into the guest through the gem5 readfile path, and executed under
Linux in full-system mode. Each kernel is bounded by guest `m5 resetstats`
and `m5 dumpstats` calls; the first 4 stats windows map to BFS, CC, PR, SSSP.

Workload suite: `bfs`, `cc`, `pr`, `sssp` from GAPBS, each at `-g 14 -k 8` with one trial
and kernel-specific official arguments.

## Per-kernel results

| Kernel | Policy | ROI ticks | Delta vs none | Insts | L1D demand misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Proof evictions | Allowed | Blocked no provenance | Translated PF | Translation faults | CTLW hits | CTLW misses | Boundary authority drops | Boundary PF drops | rc |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bfs | none | 68999502429 | 0.000% | 111487517 | 1083062 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| bfs | naive | 69020276634 | 0.030% | 111482913 | 1082673 | -0.036% | 7103 | 533 | 115778 | 2545 | 0 | 115778 | 0 | 6689 | 0 | 6689 | 108673 | 0 | 0 | 0 |
| bfs | copper | 69031906992 | 0.047% | 111482913 | 1082784 | -0.026% | 4574 | 242 | 116960 | 2612 | 0 | 4590 | 112370 | 4419 | 0 | 4419 | 16 | 0 | 0 | 0 |
| bfs | copper_clpd64k_peb | 69027185718 | 0.040% | 111479698 | 1082554 | -0.047% | 4896 | 290 | 116903 | 2510 | 0 | 5254 | 111649 | 4553 | 0 | 4553 | 358 | 18059 | 0 | 0 |
| cc | none | 66663769167 | 0.000% | 109872430 | 1089584 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| cc | naive | 66666638295 | 0.004% | 109872465 | 1090121 | 0.049% | 6895 | 540 | 116249 | 2495 | 0 | 116249 | 0 | 6480 | 0 | 6480 | 109352 | 0 | 0 | 0 |
| cc | copper | 66696484752 | 0.049% | 109875383 | 1089873 | 0.027% | 4419 | 307 | 117949 | 2594 | 0 | 4437 | 113512 | 4283 | 0 | 4283 | 18 | 0 | 0 | 0 |
| cc | copper_clpd64k_peb | 66688037208 | 0.036% | 109875415 | 1089859 | 0.025% | 4795 | 351 | 124552 | 2534 | 0 | 5595 | 118957 | 4403 | 0 | 4403 | 800 | 84812 | 0 | 0 |
| pr | none | 69843923496 | 0.000% | 110464497 | 1377030 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| pr | naive | 69830878221 | -0.019% | 110464493 | 1376846 | -0.013% | 5906 | 552 | 98290 | 2415 | 0 | 98290 | 0 | 5554 | 0 | 5554 | 92381 | 0 | 0 | 0 |
| pr | copper | 69835861899 | -0.012% | 110464468 | 1376854 | -0.013% | 3635 | 330 | 100349 | 2521 | 0 | 3647 | 96702 | 3540 | 0 | 3540 | 12 | 0 | 0 | 0 |
| pr | copper_clpd64k_peb | 69822269838 | -0.031% | 110464445 | 1376783 | -0.018% | 3885 | 360 | 110890 | 2531 | 0 | 4394 | 106496 | 3687 | 0 | 3687 | 509 | 88152 | 0 | 0 |
| sssp | none | 86613785847 | 0.000% | 131278078 | 1504196 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| sssp | naive | 86581931067 | -0.037% | 131280403 | 1504876 | 0.045% | 24213 | 1626 | 138770 | 3431 | 0 | 138770 | 0 | 23427 | 0 | 23427 | 114555 | 0 | 0 | 0 |
| sssp | copper | 86642219718 | 0.033% | 131288448 | 1505064 | 0.058% | 12954 | 727 | 144088 | 3614 | 0 | 13297 | 130791 | 12184 | 0 | 12184 | 343 | 0 | 0 | 0 |
| sssp | copper_clpd64k_peb | 86630805810 | 0.020% | 131280859 | 1506203 | 0.133% | 22204 | 1151 | 160158 | 3639 | 0 | 23383 | 136775 | 20657 | 0 | 20657 | 1179 | 84480 | 0 | 0 |

## Aggregate across 4 kernels

| Policy | Total ROI ticks | Delta vs none | L1D demand misses | L1D miss delta | PF issued | PF useful | Pointer-like | Proof evictions | Blocked no provenance | Translated PF | Translation faults | CTLW hits | CTLW misses | Boundary authority drops | Boundary PF drops |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| none | 292120980939 | 0.000% | 5053872 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| naive | 292099724217 | -0.007% | 5054516 | 0.013% | 44117 | 3251 | 469087 | 0 | 0 | 42150 | 0 | 42150 | 424961 | 0 | 0 |
| copper | 292206473361 | 0.029% | 5054575 | 0.014% | 25582 | 1606 | 479346 | 0 | 453375 | 24426 | 0 | 24426 | 389 | 0 | 0 |
| copper_clpd64k_peb | 292168298574 | 0.016% | 5055399 | 0.030% | 35780 | 2152 | 512503 | 0 | 473877 | 33300 | 0 | 33300 | 2846 | 275503 | 0 |

## Interpretation

- The official GAPBS blocker is now materially reduced: local tooling can build and run official C++ GAPBS kernels as AArch64 Linux binaries under gem5 full-system.
- COPPER blocked 453375 unproven pointer-shaped candidates across the 4 kernels while reporting zero fill-origin translation faults.
- Relative to the naive pointer-like policy, COPPER issued 42.0% fewer prefetches and reduced cross-page CTLW misses by 99.9%.
- Useful-prefetch rate was 6.3% for COPPER versus 7.4% for naive across this small suite.
- copper_clpd64k_peb issued 18.9% fewer prefetches than naive, reduced naive CTLW misses by 99.3%, recorded 0 proof evictions, and had a useful-prefetch rate of 6.0%.
- The suite is still scale-14 and therefore still modest for a full performance claim. Its strongest role is external-validity evidence: COPPER runs cleanly on official AArch64 C++ graph workloads and demonstrates its safety/control invariant under Linux.
- GAPBS stores graph edges primarily as integer vertex IDs, so these kernels stress provenance filtering less directly than heap pointer-chasing codes. That limitation should be stated clearly in the paper.
