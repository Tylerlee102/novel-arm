# Official GAPBS Full-System Cross-Scale Summary

This file compares the official GAPBS AArch64 full-system suite at the three
scales currently run locally. The numbers aggregate BFS, CC, PR, and SSSP
within each policy.

| Scale | Policy | Total ROI ticks | Delta vs none | L1D demand misses | L1D miss delta | PF issued | PF useful rate | Pointer-like | Blocked no provenance | Translated PF | Translation faults | CTLW misses | CTLW miss reduction vs naive |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | none | 37955407266 | 0.000% | 448538 | 0.000% | 0 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0.000% |
| 10 | naive | 37953769572 | -0.004% | 448096 | -0.099% | 8922 | 15.893% | 40087 | 0 | 7447 | 0 | 31156 | 0.000% |
| 10 | copper | 37931115915 | -0.064% | 447722 | -0.182% | 3793 | 19.009% | 43925 | 40128 | 3321 | 0 | 4 | 99.987% |
| 12 | none | 83222845182 | 0.000% | 1088355 | 0.000% | 0 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0.000% |
| 12 | naive | 83217355677 | -0.007% | 1090531 | 0.200% | 16621 | 11.877% | 91383 | 0 | 14914 | 0 | 74753 | 0.000% |
| 12 | copper | 83185651080 | -0.045% | 1089921 | 0.144% | 9690 | 11.176% | 98419 | 88445 | 9045 | 0 | 284 | 99.620% |
| 14 | none | 292120980939 | 0.000% | 5053872 | 0.000% | 0 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0.000% |
| 14 | naive | 292099724217 | -0.007% | 5054516 | 0.013% | 44117 | 7.369% | 469087 | 0 | 42150 | 0 | 424961 | 0.000% |
| 14 | copper | 292206473361 | 0.029% | 5054575 | 0.014% | 25582 | 6.278% | 479346 | 453375 | 24426 | 0 | 389 | 99.908% |

Key readout:

- The official suite now scales from 1024-node to 16384-node generated GAPBS graphs under full-system AArch64 Linux.
- COPPER's performance movement remains near zero on these integer-edge graph kernels, so the paper should not sell GAPBS as the speedup centerpiece.
- COPPER's safety/control behavior scales: it blocks unproven pointer-shaped candidates, keeps fill-origin translation faults at zero, and suppresses almost all naive cross-page CTLW misses.
- The strongest conference-facing use of official GAPBS is external validity and negative-control evidence; pointer-heavy microbenchmarks and targeted security traces remain the right place to show the main mechanism's benefit.
