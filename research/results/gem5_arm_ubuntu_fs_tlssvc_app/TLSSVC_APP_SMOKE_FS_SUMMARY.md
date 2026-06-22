# TLS Session-Service AArch64 Full-System Summary

This workload is a deterministic TLS/session-service style native AArch64 Linux ROI:
hash-table session lookup, LRU session state, linked record chains, and
constant-time-ish record-authentication arithmetic. Ticket/mask fields contain pointer-shaped 64-bit words that are loaded by the authentication loop but never used as architectural addresses.

Input tag: `app_smoke`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 4076632620 | 0.000% | 3545848 | 51588 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x92f3bb62393cd786 | 0 |
| stride | 3811711806 | -6.499% | 3545442 | 42655 | -17.316% | 20066 | 10444 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x92f3bb62393cd786 | 0 |
| naive | 4071854736 | -0.117% | 3542633 | 51398 | -0.368% | 1131 | 195 | 4813 | 360 | 4813 | 0 | 3680 | 0 | 0 | 0x92f3bb62393cd786 | 0 |
| copper_clpd64k_peb | 4073610978 | -0.074% | 3542404 | 51385 | -0.394% | 548 | 91 | 5240 | 379 | 566 | 4674 | 18 | 0 | 17708 | 0x92f3bb62393cd786 | 0 |
| dcpt | 3603073986 | -11.616% | 3543301 | 35152 | -31.860% | 200375 | 19470 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x92f3bb62393cd786 | 0 |
| spp | 3518692119 | -13.686% | 3546748 | 32327 | -37.336% | 161329 | 25702 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x92f3bb62393cd786 | 0 |
| ampm | 3641108580 | -10.683% | 3547161 | 36036 | -30.147% | 236095 | 25500 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x92f3bb62393cd786 | 0 |
| spp_copper_slack | 3517643835 | -13.712% | 3546748 | 32304 | -37.381% | 161547 | 25747 | 7675 | 259 | 372 | 7303 | 19 | 0 | 10216 | 0x92f3bb62393cd786 | 0 |

Interpretation:

- Checksum agreement: yes (0x92f3bb62393cd786).
- Naive DMP CTLW misses: 3680; COPPER CLPD-64K+PEB CTLW misses: 18; reduction: 99.5%.
- SPP+COPPER slack CTLW misses: 19; reduction versus naive DMP: 99.5%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is not a production TLS stack. It is a crypto-adjacent service-style stress point for pointer-like ticket data, session hash/LRU metadata, and linked record traversal under the same full-system AArch64 path as the public app matrix.

status=PASS
