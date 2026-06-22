# Official OpenSSL CLI HMAC-SHA256 Fixed-Workload AArch64 Full-System Summary

This workload injects the official Ubuntu ARM64 `openssl` CLI binary, creates a deterministic pointer-shaped guest input file before ROI, then measures `openssl dgst -sha256 -hmac` under timing-mode full-system gem5. It is an official CLI fixed-workload MAC datapoint, not the timer-driven `openssl speed` benchmark.

Input tag: `hmac_64k_seed2`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | SHA256 | rc | after rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| none | 16652170494 | 0.000% | 19050852 | 210198 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 534585d466138ec1a0f392e93573b3557587c9d9ec139f14f51b702c9c80ef81 | 0 |  |
| naive | 16639883793 | -0.074% | 19037958 | 209765 | -0.206% | 11053 | 1773 | 27953 | 1327 | 27953 | 0 | 16898 | 0 | 0 | 534585d466138ec1a0f392e93573b3557587c9d9ec139f14f51b702c9c80ef81 | 0 |  |
| copper_clpd64k_peb | 16633962720 | -0.109% | 19047514 | 208863 | -0.635% | 8905 | 1749 | 32870 | 1312 | 9429 | 23441 | 524 | 0 | 18991 | 534585d466138ec1a0f392e93573b3557587c9d9ec139f14f51b702c9c80ef81 | 0 |  |
| spp | 13773936942 | -17.284% | 19066582 | 127038 | -39.563% | 695696 | 106478 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 534585d466138ec1a0f392e93573b3557587c9d9ec139f14f51b702c9c80ef81 | 0 |  |
| spp_copper_slack | 13773623589 | -17.286% | 19065249 | 127133 | -39.518% | 693430 | 106388 | 50431 | 996 | 8338 | 42093 | 428 | 0 | 10234 | 534585d466138ec1a0f392e93573b3557587c9d9ec139f14f51b702c9c80ef81 | 0 |  |

Interpretation:

- SHA256 agreement: yes (534585d466138ec1a0f392e93573b3557587c9d9ec139f14f51b702c9c80ef81).
- Input checksum agreement: yes (0xd6ed7370bcfab27e).
- Native return-code agreement: yes (0).
- Native after-command return-code agreement: not used.
- Naive DMP CTLW misses: 16898; COPPER CLPD-64K+PEB CTLW misses: 524; reduction: 96.9%.
- SPP+COPPER slack CTLW misses: 428; reduction versus naive DMP: 97.5%.
- COPPER translation faults: 0; SPP+COPPER slack translation faults: 0.
- SPP+COPPER slack tick gap versus SPP: -0.002 percentage points.
- This is official-command HMAC-SHA256 evidence, but still not the timer-driven `openssl speed` benchmark.

status=PASS
