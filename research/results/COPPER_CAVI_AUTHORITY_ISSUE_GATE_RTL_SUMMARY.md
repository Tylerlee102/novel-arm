# COPPER CAVI Authority Issue Gate RTL Summary

CAVI means Commit-Authority Validity Interlock. It is the final DMP issue-side
contract that couples the retained source-proof path to the target-line
translation/coherence witness path. The invariant is:

> issue only if the ROCCA/CLPD source proof is valid and the target authority
> filter still has a current exact target witness; same-cycle source clears,
> target remaps, TLBI, permission downgrades, and queued target revocations
> take priority over proof reuse.

This is not a production ARM LSQ, MMU, or CHI/ACE/AXI fabric. It is a
synthesizable composition boundary for checking whether the previously separate
ROCCA, CLPD, and TLB/coherence authority blocks agree at the last issue gate.

## XSim Result

| Check | Result |
|---|---:|
| Directed cases | 14 |
| Randomized trials | 20,000 |
| Random legal allows | 7,561 |
| Random blocks | 12,439 |
| Random source-side blocks | 7,937 |
| Random target-side blocks after source proof | 4,502 |
| Random clear-wins proof suppressions | 2,021 |
| Random target revocation conflicts | 3,996 |
| Errors | 0 |

The directed suite covers legal issue, unproven source words, same-cycle
clear-wins proof suppression, source-write proof clearing, target remap,
unrelated target remap, token TLBI, permission downgrade, missing target
witness, source/target token mismatch, source translation fault, global
proof-boundary clear, queued target remap hold, and drain/re-allow behavior.

Log: `research/results/copper_cavi_authority_issue_gate_xsim_20260620.log`

## Vivado Synthesis Result

Target: Artix-7 `xc7a35tcpg236-1`, 10 ns clock.

| Metric | Result |
|---|---:|
| Slice LUTs | 4,591 |
| Slice registers | 2,791 |
| Block RAM tiles | 0 |
| DSPs | 0 |
| WNS at 10 ns | 1.149 ns |
| WHS at 10 ns | 0.148 ns |
| Synthesis errors | 0 |
| Critical warnings | 0 |
| Synthesis warnings | 0 |

Reports:

- `research/results/copper_cavi_authority_issue_gate_utilization.rpt`
- `research/results/copper_cavi_authority_issue_gate_timing.rpt`
- `research/results/copper_cavi_authority_issue_gate_synth.log`

## Paper Interpretation

CAVI strengthens the "not merely a pile of blocks" argument by making the
cross-block issue invariant executable. A candidate DMP issue must pass source
provenance, source translation/permission, target witness freshness, target
permission, and pending revocation checks in the same cycle. The testbench also
checks that a queued target remap can hold issue until drained and that the
candidate re-allows only after the target witness is considered refreshed.

status=PASS
