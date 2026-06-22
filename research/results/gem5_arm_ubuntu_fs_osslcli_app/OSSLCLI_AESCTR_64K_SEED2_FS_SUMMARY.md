# Official OpenSSL CLI AES-CTR Fixed-Workload AArch64 Full-System Summary

This workload injects the official Ubuntu ARM64 `openssl` CLI binary, creates a deterministic pointer-shaped guest input file before ROI, then measures `openssl enc -aes-128-ctr` and an official `openssl dgst -sha256` fingerprint of the encrypted output under timing-mode full-system gem5. It is an official CLI fixed-workload datapoint, not the timer-driven `openssl speed` benchmark.

Input tag: `aesctr_64k_seed2`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | SHA256 | rc | after rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| none | 29466233604 | 0.000% | 34542233 | 432883 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 01accf653542e999c627a41a9286ad17da55a83c6cdd2b3b571ad2330357c999 | 0 | 0 |
| naive | 29454237612 | -0.041% | 34546237 | 430598 | -0.528% | 33546 | 6337 | 65760 | 2591 | 65760 | 0 | 32212 | 0 | 0 | 01accf653542e999c627a41a9286ad17da55a83c6cdd2b3b571ad2330357c999 | 0 | 0 |
| copper_clpd64k_peb | 29433503700 | -0.111% | 34545840 | 428327 | -1.052% | 31388 | 6585 | 87207 | 2588 | 32851 | 54356 | 1463 | 0 | 18995 | 01accf653542e999c627a41a9286ad17da55a83c6cdd2b3b571ad2330357c999 | 0 | 0 |
| spp | 24018226398 | -18.489% | 34500402 | 240963 | -44.335% | 1637751 | 235693 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 01accf653542e999c627a41a9286ad17da55a83c6cdd2b3b571ad2330357c999 | 0 | 0 |
| spp_copper_slack | 24104997207 | -18.195% | 34510255 | 244456 | -43.528% | 1625755 | 232411 | 143816 | 1987 | 31941 | 111875 | 1549 | 0 | 10246 | 01accf653542e999c627a41a9286ad17da55a83c6cdd2b3b571ad2330357c999 | 0 | 0 |

Interpretation:

- SHA256 agreement: yes (01accf653542e999c627a41a9286ad17da55a83c6cdd2b3b571ad2330357c999).
- Input checksum agreement: yes (0xd6ed7370bcfab27e).
- Native return-code agreement: yes (0).
- Native after-command return-code agreement: yes (0).
- Naive DMP CTLW misses: 32212; COPPER CLPD-64K+PEB CTLW misses: 1463; reduction: 95.5%.
- SPP+COPPER slack CTLW misses: 1549; reduction versus naive DMP: 95.2%.
- COPPER translation faults: 0; SPP+COPPER slack translation faults: 0.
- SPP+COPPER slack tick gap versus SPP: +0.294 percentage points.
- This is official-command AES-CTR plus output digest evidence, but still not the timer-driven `openssl speed` benchmark.

status=PASS
