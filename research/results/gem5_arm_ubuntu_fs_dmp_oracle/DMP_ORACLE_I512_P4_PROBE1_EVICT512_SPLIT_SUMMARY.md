# Split-Phase DMP Oracle Scan/Probe Audit

This run separates the secret data scan from the later target-probe
phase with `m5_dump_stats` and `m5_reset_stats`. The scan phase is
where a DMP-like prefetcher can leak values that have not been
architecturally dereferenced as pointers; the probe phase may contain
legitimate target dereferences by construction.

| Secret | Policy | Phase | Ticks | L1D misses | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | Translated PF | Faults | CTLW hits | CTLW misses | Boundary drops | rc |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | naive | scan | 31153149 | 73 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 0 | naive | probe | 44704917 | 709 | 3 | 0 | 11 | 1 | 11 | 0 | 2 | 0 | 2 | 8 | 0 | 0 |
| 0 | copper_clpd64k_peb | scan | 31194774 | 74 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 8336 | 0 |
| 0 | copper_clpd64k_peb | probe | 44704917 | 709 | 0 | 0 | 15 | 1 | 0 | 15 | 0 | 0 | 0 | 0 | 76 | 0 |
| 0 | spp_copper_slack | scan | 29642328 | 62 | 146 | 33 | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 285 | 0 |
| 0 | spp_copper_slack | probe | 30624345 | 562 | 1040 | 194 | 20 | 1 | 0 | 20 | 0 | 0 | 0 | 0 | 68 | 0 |
| 1 | naive | scan | 31540428 | 110 | 64 | 1 | 66 | 1 | 66 | 0 | 62 | 0 | 62 | 2 | 0 | 0 |
| 1 | naive | probe | 42023601 | 706 | 3 | 3 | 11 | 64 | 11 | 0 | 2 | 0 | 2 | 8 | 0 | 0 |
| 1 | copper_clpd64k_peb | scan | 31297671 | 74 | 0 | 0 | 64 | 0 | 0 | 64 | 0 | 0 | 0 | 0 | 8336 | 0 |
| 1 | copper_clpd64k_peb | probe | 44704917 | 709 | 0 | 0 | 16 | 1 | 0 | 16 | 0 | 0 | 0 | 0 | 140 | 0 |
| 1 | spp_copper_slack | scan | 29394576 | 62 | 146 | 33 | 67 | 0 | 0 | 67 | 0 | 0 | 0 | 0 | 285 | 0 |
| 1 | spp_copper_slack | probe | 30606696 | 562 | 1040 | 194 | 24 | 1 | 0 | 24 | 0 | 0 | 0 | 0 | 132 | 0 |

Scan-phase deltas (`secret=1 minus secret=0`):

| Policy | PF issued delta | Allowed delta | Blocked delta | L1D miss delta |
|---|---:|---:|---:|---:|
| naive | 64 | 66 | 0 | 37 |
| copper_clpd64k_peb | 0 | 0 | 64 | 0 |
| spp_copper_slack | 0 | 0 | 64 | 0 |

Interpretation:

- The unsafe prefetcher leaks during the scan phase: its secret-dependent issued/allowed deltas appear before any target probe.
- COPPER and SCOOP block the scan-phase secret-dependent candidates rather than relying on the later observer phase.
- Any remaining allowed candidates in the probe phase are easier to defend because the probe phase intentionally dereferences target lines architecturally.
