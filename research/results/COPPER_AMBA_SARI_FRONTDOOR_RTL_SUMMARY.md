# COPPER AMBA-SARI Frontdoor RTL Summary

Date: 2026-06-20

Purpose: connect the public AMBA CHI/ACE event-class map to a concrete RTL
front door for COPPER's SoC Authority Revocation Interface (SARI). This is a
simplified public decoder, not a complete Arm CHI/ACE/AXI implementation.

## Mechanism

`copper_amba_sari_frontdoor` maps public event classes into abstract COPPER
revocation signals:

- DMA write, I/O write, and CHI source-changing events become source-line
  revocations.
- CHI read-shared/no-change events do not revoke source authority.
- target remap events pass to target-witness revocation.
- DVM/TLBI token and DVM/TLBI-all events pass to PASB/target authority
  revocation.
- source-side backpressure holds DMP issue until SARI can accept the event.

`copper_amba_sari_frontdoor_regslice` is a registered timing slice around the
decoder so Vivado reports a real 10 ns register-to-register path.

## XSim Result

Command: `research/run_copper_amba_sari_frontdoor_xsim.ps1`

Log: `research/results/copper_amba_sari_frontdoor_xsim_20260620.log`

| Check | Result |
|---|---:|
| Directed cases | 10 |
| Randomized cycles | 10,000 |
| CHI read-only no-revoke observations | 367 |
| CHI read-unique revoke observations | 723 |
| CHI clean-invalidate observations | 707 |
| CHI make-invalid observations | 665 |
| CHI dirty-writeback observations | 729 |
| DMA accepted events | 2,289 |
| I/O accepted events | 2,319 |
| Triple source-lane accept observations | 165 |
| Target remap observations | 590 |
| DVM token TLBI observations | 189 |
| DVM all TLBI observations | 163 |
| Backpressure observations | 525 |
| Hold observations | 6,383 |
| Errors | 0 |

## Vivado Registered-Slice Result

Target: `xc7a35tcpg236-1`, 10 ns clock, synthesized design state.

| Metric | Result |
|---|---:|
| Slice LUTs | 8 |
| Slice registers | 160 |
| BRAM | 0 |
| DSP | 0 |
| Worst setup slack | +7.525 ns |
| Worst hold slack | +0.142 ns |
| Worst path data delay | 2.324 ns |
| Worst path logic levels | 2 |
| Synthesis warnings / critical warnings / errors | 0 / 0 / 0 |

Timing report: `research/results/copper_amba_sari_frontdoor_regslice_timing.rpt`

## Interpretation

This strengthens the AMBA/SoC integration story by showing that the public
event-class map is not only prose: it has a small front-door decoder and a
timed register-slice boundary. It still does not prove a complete CHI/ACE/AXI
fabric, ordering model, or production coherency implementation.

status=PASS
