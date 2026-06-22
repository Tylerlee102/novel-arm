# COPPER/SCOOP Security Evidence Portfolio

This portfolio consolidates adversarial AArch64 full-system runs and
the SCOOP arbitration checks. The security claim supported here is
differential: content-derived prefetch behavior should not change as a
function of secret pointer-shaped data unless committed provenance
authorizes the candidate.

| Evidence point | Unsafe signal | COPPER result | SCOOP result | Why it matters |
|---|---:|---:|---:|---|
| Fake-pointer-only ROI | naive issues 28685 content-derived prefetches from 131094 fake observations | PEB allows 0 and blocks 131066 | companion allows 0 and blocks 191674 while SPP keeps 766837 total PF | Rejects pointer-shaped data that is never dereferenced |
| Secret traffic oracle | naive PF delta 32760, allowed delta 32760 | allowed delta 0, blocked delta 32760 | companion allowed delta 0, blocked delta 64143 | Shows raw loaded secret values create DMP traffic, but not COPPER/SCOOP companion traffic |
| Cold-cache observer oracle | naive L1D-miss delta -14 and timing-delta shift -4.906 pp | L1D-miss delta 0, allowed delta 1 | L1D-miss delta 1, companion allowed delta 0 | Tests whether secret-shaped data warms an observable cache footprint |
| Observer seed sweep | naive allowed deltas 63..65, L1D-miss deltas -14..-9 | standalone COPPER L1D-miss delta 0 in all seeds | companion allowed delta set 0 | Checks the observer oracle across three address permutations |
| Split scan/probe audit | scan PF delta 64, allowed delta 66 | scan allowed delta 0, blocked delta 64 | scan companion allowed delta 0, blocked delta 64 | Separates the unauthorized secret scan from the later legitimate target probe |
| SCOOP bounded arbitration checker | companion-first and round-robin fail | n/a | PASS to depth 10 | Verifies the slack-only invariant at the algorithm level |
| SCOOP RTL arbiter simulation | randomized stall/ready stress | n/a | PASS under Vivado XSim | Checks the synthesizable arbitration structure, not just the model |

Key readout:

- The strongest unsafe signal is the traffic oracle: 32760 extra DMP-like prefetches when the secret data words are valid heap addresses.
- The strongest observable side-channel signal is the cold-cache oracle: unsafe DMP reduces target-probe L1D demand misses by 14 and shifts relative timing by -4.906 percentage points.
- Across three observer seeds, unsafe DMP always has positive allowed deltas (63..65) and fewer L1D misses for `secret=1` (-14..-9).
- The split scan/probe audit localizes the leak: unsafe DMP's scan phase has allowed delta 66, while COPPER and SCOOP scan-phase allowed deltas are both 0.
- SCOOP preserves the conventional SPP lane but keeps the companion lane differentially silent in both oracle tests: allowed-candidate delta 0 in the traffic oracle and 0 in the observer oracle.
- The earlier non-split observer edge is now bounded by phase evidence: during the unauthorized scan phase, standalone COPPER and SCOOP both have zero allowed-candidate delta.
- All full-system rows used here completed with `rc=0` and zero fill-origin translation faults.

Status: stronger than the prior artifact, but still not a guaranteed top-tier acceptance. The remaining high-value evidence gap is broader production-style workloads and a clean paper writeup that states the differential security claim precisely.
