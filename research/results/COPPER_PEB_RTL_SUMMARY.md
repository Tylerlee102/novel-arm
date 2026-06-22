# COPPER Provenance Epoch Boundary RTL Summary

Date: 2026-06-15

## Mechanism

`copper_provenance_epoch_boundary` implements an O(1) authority-boundary rule
for COPPER. Each requestor/security domain has a small epoch. Commit-time proof
tokens are salted with the current domain epoch, and DMP-time queries recompute
the same epoch-token. A boundary increments the domain epoch, so pre-boundary
proof entries immediately fail the epoch/token check without sweeping the CLPD
directory. If an epoch would wrap, the domain is blocked and `wrap_flush_required`
is asserted until external logic purges the affected proof entries and issues
`wrap_clear_valid`.

## RTL Validation

Command:

`powershell -ExecutionPolicy Bypass -File research\run_copper_peb_xsim.ps1 *> research\results\copper_peb_xsim.log`

Passing line:

`COPPER PEB tests completed: directed=11 boundaries=9 stale_blocks=1 domain_isolation_hits=4 wrap_blocks=1 errors=0`

Covered directed cases:

- Same-domain proof remains current before a boundary.
- Wrong token blocks.
- Boundary makes an old proof stale.
- New proof after the boundary becomes current.
- Boundary in one domain does not invalidate another domain.
- Epoch wrap requests a flush and blocks commits/queries until `wrap_clear_valid`.

## Vivado Synthesis

Command:

`powershell -ExecutionPolicy Bypass -File research\run_copper_peb_synth.ps1`

Target:

- Vivado 2025.2
- `xc7a35tcpg236-1`
- 10 ns clock constraint

Result:

| Block | LUTs | FFs | BRAM tiles | DSPs | Setup WNS | Hold WHS | Errors | Critical warnings |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `copper_provenance_epoch_boundary` | 346 | 147 | 0 | 0 | +3.782 ns | +0.294 ns | 0 | 0 |

Synthesis log line:

`Synthesis finished with 0 errors, 0 critical warnings and 0 warnings.`

## Paper Interpretation

PEB converts the full-system fake-only leakage fix into a hardware-realizable
mechanism rather than a simulator cleanup. In the gem5 AArch64 fake-only control,
CLPD-64K+PEB blocks 131,066 of 131,066 pointer-shaped fake observations, issues
zero prefetches, drops 76,560 stale authority entries at the boundary, and keeps
overhead to +0.033% versus no prefetching. In the three-seed real pointer ROI,
CLPD-64K+PEB improves all three seeds with mean -2.905% ROI ticks versus
no-prefetch, zero translation faults, and zero CTLW misses.

This does not prove full SoC signoff. It is RTL evidence that COPPER's boundary
invariant can be implemented as a small per-domain epoch/token structure with
explicit wrap handling.
