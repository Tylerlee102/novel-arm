# Official OpenSSL CLI HMAC-SHA256 Fixed-Workload AArch64 Full-System Summary

This workload injects the official Ubuntu ARM64 `openssl` CLI binary, creates a deterministic pointer-shaped guest input file before ROI, then measures `openssl dgst -sha256 -hmac` under timing-mode full-system gem5. It is an official CLI fixed-workload MAC datapoint, not the timer-driven `openssl speed` benchmark.

Input tag: `hmac_64k`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | SHA256 | rc | after rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| none | 16650192807 | 0.000% | 19047870 | 210034 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | d3be5389af52965eb3084df01f75d9ed50f9af56e0cd391d05d760e034d7130a | 0 |  |
| naive | 16650696303 | 0.003% | 19047800 | 209833 | -0.096% | 11054 | 1774 | 27959 | 1328 | 27959 | 0 | 16903 | 0 | 0 | d3be5389af52965eb3084df01f75d9ed50f9af56e0cd391d05d760e034d7130a | 0 |  |
| copper_clpd64k_peb | 16634032317 | -0.097% | 19047371 | 208874 | -0.552% | 8905 | 1749 | 32869 | 1312 | 9429 | 23440 | 524 | 0 | 18991 | d3be5389af52965eb3084df01f75d9ed50f9af56e0cd391d05d760e034d7130a | 0 |  |
| spp | 13765853367 | -17.323% | 19062866 | 127232 | -39.423% | 690926 | 106006 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | d3be5389af52965eb3084df01f75d9ed50f9af56e0cd391d05d760e034d7130a | 0 |  |
| spp_copper_slack | 13763941947 | -17.335% | 19060172 | 127243 | -39.418% | 695589 | 106176 | 50680 | 1001 | 8380 | 42300 | 435 | 0 | 10235 | d3be5389af52965eb3084df01f75d9ed50f9af56e0cd391d05d760e034d7130a | 0 |  |

Interpretation:

- SHA256 agreement: yes (d3be5389af52965eb3084df01f75d9ed50f9af56e0cd391d05d760e034d7130a).
- Input checksum agreement: yes (0xc59a1575a221a8e6).
- Native return-code agreement: yes (0).
- Native after-command return-code agreement: not used.
- Naive DMP CTLW misses: 16903; COPPER CLPD-64K+PEB CTLW misses: 524; reduction: 96.9%.
- SPP+COPPER slack CTLW misses: 435; reduction versus naive DMP: 97.4%.
- COPPER translation faults: 0; SPP+COPPER slack translation faults: 0.
- SPP+COPPER slack tick gap versus SPP: -0.012 percentage points.
- This is official-command HMAC-SHA256 evidence, but still not the timer-driven `openssl speed` benchmark.

status=PASS
