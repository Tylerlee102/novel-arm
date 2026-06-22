# COPPER TLB/Coherence Authority Filter RTL Summary

Date: 2026-06-17

This artifact is the RTL-facing counterpart of the bounded TLB/coherence
authority-contract checker. It is not a production Arm CHI/TLB decoder. It is a
small public integration block for the COPPER issue-side contract: DMP issue is
allowed only when source proof, exact target witness, target permission, and
conflict-scoped revocation state all agree.

## Mechanism

`copper_tlb_coherence_authority_filter.sv` accepts:

- candidate source line, target line, and address-space/protection token
- source proof, exact target-witness, and permission-valid inputs
- same-cycle source revocation, target remap, token TLBI, global TLBI, and permission downgrade
- bounded source and target invalidation queues with overflow fallback

It outputs `dmp_allow` only when all authority inputs are live and there is no
matching incoming or queued revocation. Unrelated source or target events do not
globally hold an otherwise authorized candidate.

## Vivado XSim

Command: `research/run_copper_tlb_coherence_authority_filter_xsim.ps1`

Result log: `research/results/copper_tlb_coherence_authority_filter_xsim_20260617.log`

Key line:

`COPPER TLB-coherence authority filter completed directed=27 random=10000 baseline_allow=1 no_source=1 no_target=2 permission=2 source_same=1 source_queued=1 target_remap=1 target_queued=1 tlbi_token=1 tlbi_all=1 unrelated_allow=2 overflow=1 random_allow=3633 random_block=4006 errors=0`

Covered directed cases:

- baseline allow
- missing source proof block
- non-exact/page-level target witness block
- source-only authority block
- permission failure and same-cycle permission downgrade block
- same-cycle and queued source revocation block
- same-cycle and queued target remap block
- token TLBI and global TLBI block
- unrelated source/target revocation precision allow
- overflow fallback block

## Synthesis

Command: `research/run_copper_tlb_coherence_authority_filter_synth.ps1`

Target: `xc7a35tcpg236-1`, 10 ns clock constraint.

| Metric | Result |
|---|---:|
| Slice LUTs | 332 |
| Slice registers | 167 |
| BRAM tiles | 0 |
| DSPs | 0 |
| WNS | +6.898 ns |
| TNS | 0.000 ns |
| Synthesis warnings | 0 |
| Synthesis critical warnings | 0 |
| Synthesis errors | 0 |

Relevant reports:

- `research/results/copper_tlb_coherence_authority_filter_utilization.rpt`
- `research/results/copper_tlb_coherence_authority_filter_timing.rpt`
- `research/results/copper_tlb_coherence_authority_filter_synth.log`

## Interpretation

The new RTL evidence closes part of the gap between the Python contract and the
existing CLPD/CTLW/SARI integration harnesses. It makes the TLB/coherence
authority rule tangible as a small issue-side filter with conflict-scoped
queued revocation, exact witness gating, permission gating, and overflow
fallback. This still is not a full production memory hierarchy proof; it is a
synthesizable contract block that a production integration would need to feed
from real TLB, coherence, DMA, and permission-change sources.

status=PASS
