# Official OpenSSL CLI Fixed-Workload AArch64 Full-System Summary

This workload injects the official Ubuntu ARM64 `openssl` CLI binary, creates a deterministic pointer-shaped guest input file before ROI, then measures `openssl dgst -sha256 /tmp/openssl_cli_input.bin` under timing-mode full-system gem5. It is an official CLI fixed-workload datapoint, not the timer-driven `openssl speed` benchmark.

Input tag: `fixed_64k`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | SHA256 | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 15832750734 | 0.000% | 18077768 | 201405 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 77d85bbaaba62a96c40a96e4d9caf5d1265da704daade3a9f10d8e9dd8617cbe | 0 |
| naive | 15836366448 | 0.023% | 18072440 | 201353 | -0.026% | 10126 | 1561 | 26069 | 1165 | 26069 | 0 | 15940 | 0 | 0 | 77d85bbaaba62a96c40a96e4d9caf5d1265da704daade3a9f10d8e9dd8617cbe | 0 |
| copper_clpd64k_peb | 15829681806 | -0.019% | 18072458 | 200556 | -0.422% | 7980 | 1498 | 30522 | 1172 | 8367 | 22155 | 387 | 0 | 18984 | 77d85bbaaba62a96c40a96e4d9caf5d1265da704daade3a9f10d8e9dd8617cbe | 0 |
| spp | 13016774196 | -17.786% | 17988044 | 120999 | -39.923% | 669899 | 101839 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 77d85bbaaba62a96c40a96e4d9caf5d1265da704daade3a9f10d8e9dd8617cbe | 0 |
| spp_copper_slack | 13031848107 | -17.691% | 17989810 | 121523 | -39.662% | 669052 | 101671 | 46696 | 913 | 7599 | 39097 | 415 | 0 | 10206 | 77d85bbaaba62a96c40a96e4d9caf5d1265da704daade3a9f10d8e9dd8617cbe | 0 |

Interpretation:

- SHA256 agreement: yes (77d85bbaaba62a96c40a96e4d9caf5d1265da704daade3a9f10d8e9dd8617cbe).
- Input checksum agreement: yes (0xc59a1575a221a8e6).
- Native return-code agreement: yes (0).
- Naive DMP CTLW misses: 15940; COPPER CLPD-64K+PEB CTLW misses: 387; reduction: 97.6%.
- SPP+COPPER slack CTLW misses: 415; reduction versus naive DMP: 97.4%.
- COPPER translation faults: 0; SPP+COPPER slack translation faults: 0.
- SPP+COPPER slack tick gap versus SPP: +0.095 percentage points.
- This is stronger official-command evidence than a local libcrypto driver, but it is still a fixed-workload CLI digest rather than the official timer-driven `openssl speed` benchmark.

status=PASS
