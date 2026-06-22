# OpenSSL SHA256 AArch64 Full-System Summary

This workload is a deterministic native AArch64 Linux ROI that calls
OpenSSL libcrypto's exported `SHA256` routine while maintaining session
hash/LRU metadata and pointer-shaped ticket words loaded as data.

Input tag: `app_smoke`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 12114614259 | 0.000% | 14365240 | 144364 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x81965a75cf2e6850 | 0 |
| stride | 11065601988 | -8.659% | 14111101 | 122408 | -15.209% | 41553 | 20962 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x81965a75cf2e6850 | 0 |
| naive | 11887353081 | -1.876% | 14120991 | 141643 | -1.885% | 9040 | 1561 | 19633 | 1165 | 19633 | 0 | 10590 | 0 | 0 | 0x81965a75cf2e6850 | 0 |
| copper_clpd64k_peb | 11882528910 | -1.916% | 14120991 | 140916 | -2.388% | 6160 | 1360 | 22867 | 1115 | 6461 | 16406 | 301 | 0 | 17736 | 0x81965a75cf2e6850 | 0 |
| dcpt | 10514629845 | -13.207% | 14116400 | 102608 | -28.924% | 448414 | 44253 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x81965a75cf2e6850 | 0 |
| spp | 10103784435 | -16.598% | 14058352 | 83998 | -41.815% | 458539 | 72962 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x81965a75cf2e6850 | 0 |
| ampm | 10554247854 | -12.880% | 14469245 | 104099 | -27.891% | 566967 | 64550 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x81965a75cf2e6850 | 0 |
| spp_copper_slack | 10096355205 | -16.660% | 14058292 | 84210 | -41.668% | 459676 | 73089 | 34846 | 862 | 5369 | 29477 | 259 | 0 | 10240 | 0x81965a75cf2e6850 | 0 |

Interpretation:

- Checksum agreement: yes (0x81965a75cf2e6850).
- Naive DMP CTLW misses: 10590; COPPER CLPD-64K+PEB CTLW misses: 301; reduction: 97.2%.
- SPP+COPPER slack CTLW misses: 259; reduction versus naive DMP: 97.6%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is real libcrypto execution through the guest dynamic loader, but it is still a small synthetic driver around SHA256 rather than a full TLS stack or production crypto benchmark.

status=PASS
