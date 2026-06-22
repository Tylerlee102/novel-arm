# COPPER ROPL-LSQ Retire Guard RTL Summary

Date: 2026-06-20

Purpose: add RTL evidence for the ROPL backend hazard rule. ROPL means
Retirement-Only Provenance Latching: COPPER may create a source proof only when
the dependent memory operation reaches retirement with an older clean source
tag and no replay, squash, exception, alias, memory-order, translation, or
permission hazard still pending.

## Mechanism

`copper_ropl_lsq_retire_guard` is a synthesizable combinational guard between a
backend LSQ/dependency tracker and the COPPER proof table. It emits
`proof_valid` only when all of the following are true:

- the dependent operation is retiring and is a memory operation
- the carried source tag is valid, live, and not stale
- the source load executed, retired, is older than the dependent operation, and
  did not take an exception
- dependent exception and squash bits are clear
- replay generation, squash epoch, and same-line alias generation match
- no memory-order violation is pending
- target translation and permission checks pass

`copper_ropl_lsq_retire_guard_top` is a registered timing wrapper around the
same guard. It exists only to give Vivado a reproducible 10 ns register-to-
register timing boundary.

## XSim Result

| Check | Result |
|---|---:|
| Directed hazard cases | 18 |
| Randomized cycles | 20,000 |
| Legal proof observations | 9,251 |
| Execute-stage blocks | 184 |
| Not-retire blocks | 227 |
| Non-memory retire blocks | 230 |
| Missing/dead/stale tag blocks | 1,561 |
| Source-not-clean blocks | 2,064 |
| Exception/squash blocks | 622 |
| Replay/squash-epoch blocks | 3,371 |
| Alias/order blocks | 2,534 |
| Translation/permission blocks | 140 |
| Errors | 0 |

Log: `research/results/copper_ropl_lsq_retire_guard_xsim_20260620.log`

## Vivado Synthesis Result

Target: `xc7a35tcpg236-1`, 10 ns clock, synthesized design state.

| Metric | Result |
|---|---:|
| Slice LUTs | 14 |
| Slice registers | 49 |
| BRAM | 0 |
| DSP | 0 |
| Worst setup slack | +6.492 ns |
| Worst hold slack | +0.146 ns |
| Worst path data delay | 3.357 ns |
| Worst path logic levels | 3 |
| Synthesis warnings / critical warnings / errors | 0 / 0 / 0 |

Timing report: `research/results/copper_ropl_lsq_retire_guard_top_timing.rpt`

## Interpretation

This moves ROPL from only a bounded Python contract into a small tested RTL
interface. It is still not a complete production ARM load-store queue, but it
does make the paper's backend requirement more concrete: a backend can expose a
retire-stage proof gate with explicit replay, squash, alias, ordering,
exception, translation, and permission inputs, and the measured local cost is
small in this FPGA wrapper.

status=PASS
