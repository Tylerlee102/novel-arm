# COPPER ROCCA-to-CLPD Commit Adapter RTL Summary

Date: 2026-06-20

## Mechanism

ROCCA means Retirement-Ordered Clear-wins CLPD Adapter. It is the explicit backend-to-CLPD proof-write boundary for COPPER. A retirement-side proof may write retained CLPD source authority only when:

- the ROPL/retire proof is valid,
- the source word is still clean,
- the source epoch still matches,
- translation and permission checks have passed, and
- no same-cycle source-line write, line fill, invalidate, or global proof-boundary clear conflicts with that proof.

The named invariant is clear-wins proof commit: a destructive source-line event in the same cycle suppresses the retained CLPD proof write, so CLPD cannot recreate stale proof immediately after a clear.

## XSim Result

Script: `research\run_copper_rocca_clpd_commit_adapter_xsim.ps1`

Log: `research\results\copper_rocca_clpd_commit_adapter_xsim_20260620.log`

Result line:

`COPPER ROCCA-CLPD adapter completed: directed=11 random=20000 commits=7651 clear_wins=1598 allows=3306 token_blocks=877 epoch_blocks=974 fault_blocks=602 source_not_clean=2014 errors=0`

Coverage summary:

| Check | Count |
|---|---:|
| Directed scenarios | 11 |
| Randomized cycles | 20,000 |
| Legal CLPD proof commits | 7,651 |
| Same-cycle clear-wins blocks | 1,598 |
| Authorized CLPD allows | 3,306 |
| Token-mismatch query blocks | 877 |
| Stale-epoch query blocks | 974 |
| Fault/permission query blocks | 602 |
| Source-not-clean proof blocks | 2,014 |
| Errors | 0 |

## Vivado Synthesis Result

Script: `research\run_copper_rocca_clpd_commit_adapter_synth.ps1`

Top: `copper_rocca_clpd_commit_adapter_top`

Device: `xc7a35tcpg236-1`

The synthesized top includes ROCCA plus the existing 64-entry LUT/FF CLPD gate, not just the small adapter.

| Metric | Result |
|---|---:|
| Slice LUTs | 4,302 |
| Slice registers | 2,624 |
| BRAM tiles | 0 |
| DSPs | 0 |
| WNS at 10 ns | 1.149 ns |
| WHS | 0.288 ns |
| Synthesis errors | 0 |
| Critical warnings | 0 |

Vivado reports: `All user specified timing constraints are met.`

## Interpretation

This narrows the backend-integration objection by making the final proof-write race executable: even if an upstream retire guard produces a proof, ROCCA prevents that proof from entering CLPD in a cycle where the source line is simultaneously being cleared. This is still a public contract and prototype, not a production ARM LSQ integration, but it is stronger than prose because the invariant is checked against an independent reference model and synthesized with the CLPD boundary attached.

status=PASS
