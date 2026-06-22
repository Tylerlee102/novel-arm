# COPPER SARI-RQ State-Space Check

Date: 2026-06-16

This bounded model checks the timing-optimized SARI-RQ ring queue
against the original abstract SARI shift-queue behavior under the
frontdoor ready protocol.

Model: 3 source lines, queue depth 3, trace bound 8.
Reachable ready-respecting states explored: 40

| Check | Result | Detail |
|---|---:|---|
| Ring/shift equivalence under ready protocol | PASS | queue order and overflow match for all reachable states |
| Hold covers incoming/queued/target/overflow hazards | PASS | no missing-hold counterexample found |
| Backpressure/overflow fallback | PASS | path=sources=[0, 0]; state=shift_q=[0, 0] ring_q=[0, 0] shift_overflow=0 ring_overflow=0; violating_event=sources=[0],violates_ready; next=shift_q=[0] ring_q=[0] shift_overflow=1 ring_overflow=1 |
| Ready burst admission 1 source event(s) | PASS | path=(initial); state=shift_q=[] ring_q=[] shift_overflow=0 ring_overflow=0; event=sources=[0]; next=shift_q=[0] ring_q=[0] shift_overflow=0 ring_overflow=0 |
| Ready burst admission 2 source event(s) | PASS | path=(initial); state=shift_q=[] ring_q=[] shift_overflow=0 ring_overflow=0; event=sources=[0, 0]; next=shift_q=[0, 0] ring_q=[0, 0] shift_overflow=0 ring_overflow=0 |
| Ready burst admission 3 source event(s) | PASS | path=(initial); state=shift_q=[] ring_q=[] shift_overflow=0 ring_overflow=0; event=sources=[0, 0, 0]; next=shift_q=[0, 0, 0] ring_q=[0, 0, 0] shift_overflow=0 ring_overflow=0 |

## Interpretation

SARI-RQ is not claimed as a new research idea by itself; it is the
timing-safe implementation of the SoC revocation intake used by the
AMBA/SARI/CLPD/CTLW authority bridge. The checker supports the RTL
change by proving bounded equivalence to the abstract shift queue
when the frontdoor obeys `source_events_ready`, and by confirming
that a protocol-violating source burst falls into conservative
`overflow_sticky` hold rather than silently losing authority events.

Overall status: PASS
