# Official OpenSSL CLI AES-CTR Fixed-Workload AArch64 Full-System Summary

This workload injects the official Ubuntu ARM64 `openssl` CLI binary, creates a deterministic pointer-shaped guest input file before ROI, then measures `openssl enc -aes-128-ctr` and an official `openssl dgst -sha256` fingerprint of the encrypted output under timing-mode full-system gem5. It is an official CLI fixed-workload datapoint, not the timer-driven `openssl speed` benchmark.

Input tag: `aesctr_64k`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | SHA256 | rc | after rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| none | 29475667161 | 0.000% | 34545910 | 433084 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 39839fb42f8d96fc3a570c163b6cd2edebb8467713d1de6671ede4f99382a076 | 0 | 0 |
| naive | 29453992524 | -0.074% | 34546234 | 430582 | -0.578% | 33486 | 6333 | 65662 | 2581 | 65662 | 0 | 32174 | 0 | 0 | 39839fb42f8d96fc3a570c163b6cd2edebb8467713d1de6671ede4f99382a076 | 0 | 0 |
| copper_clpd64k_peb | 29435091777 | -0.138% | 34545855 | 428329 | -1.098% | 31390 | 6583 | 87203 | 2588 | 32853 | 54350 | 1463 | 0 | 18995 | 39839fb42f8d96fc3a570c163b6cd2edebb8467713d1de6671ede4f99382a076 | 0 | 0 |
| spp | 24018350274 | -18.515% | 34498691 | 240839 | -44.390% | 1634973 | 235599 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 39839fb42f8d96fc3a570c163b6cd2edebb8467713d1de6671ede4f99382a076 | 0 | 0 |
| spp_copper_slack | 24032175768 | -18.468% | 34510479 | 242057 | -44.109% | 1657108 | 235049 | 144175 | 1999 | 32114 | 112061 | 1549 | 0 | 10246 | 39839fb42f8d96fc3a570c163b6cd2edebb8467713d1de6671ede4f99382a076 | 0 | 0 |

Interpretation:

- SHA256 agreement: yes (39839fb42f8d96fc3a570c163b6cd2edebb8467713d1de6671ede4f99382a076).
- Input checksum agreement: yes (0xc59a1575a221a8e6).
- Native return-code agreement: yes (0).
- Native after-command return-code agreement: yes (0).
- Naive DMP CTLW misses: 32174; COPPER CLPD-64K+PEB CTLW misses: 1463; reduction: 95.5%.
- SPP+COPPER slack CTLW misses: 1549; reduction versus naive DMP: 95.2%.
- COPPER translation faults: 0; SPP+COPPER slack translation faults: 0.
- SPP+COPPER slack tick gap versus SPP: +0.047 percentage points.
- This is official-command AES-CTR plus output digest evidence, but still not the timer-driven `openssl speed` benchmark.

status=PASS
