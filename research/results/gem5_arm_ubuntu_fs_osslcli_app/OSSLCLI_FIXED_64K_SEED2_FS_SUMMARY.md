# Official OpenSSL CLI Fixed-Workload AArch64 Full-System Summary

This workload injects the official Ubuntu ARM64 `openssl` CLI binary, creates a deterministic pointer-shaped guest input file before ROI, then measures `openssl dgst -sha256 /tmp/openssl_cli_input.bin` under timing-mode full-system gem5. It is an official CLI fixed-workload datapoint, not the timer-driven `openssl speed` benchmark.

Input tag: `fixed_64k_seed2`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | SHA256 | rc | after rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| none | 15907604139 | 0.000% | 18181205 | 202421 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4245ac7122381c1f56607336057673ee0efb3df92844986c412e94c2f8dae710 | 0 |  |
| naive | 15902959455 | -0.029% | 18180628 | 202300 | -0.060% | 10262 | 1611 | 26309 | 1195 | 26309 | 0 | 16044 | 0 | 0 | 4245ac7122381c1f56607336057673ee0efb3df92844986c412e94c2f8dae710 | 0 |  |
| copper_clpd64k_peb | 15904716363 | -0.018% | 18180716 | 201623 | -0.394% | 8069 | 1512 | 30764 | 1189 | 8511 | 22253 | 442 | 0 | 19060 | 4245ac7122381c1f56607336057673ee0efb3df92844986c412e94c2f8dae710 | 0 |  |
| spp | 13095567990 | -17.677% | 18094769 | 122058 | -39.701% | 672012 | 102103 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4245ac7122381c1f56607336057673ee0efb3df92844986c412e94c2f8dae710 | 0 |  |
| spp_copper_slack | 13092016212 | -17.700% | 18096149 | 122186 | -39.638% | 672547 | 102297 | 47149 | 931 | 7671 | 39478 | 413 | 0 | 10193 | 4245ac7122381c1f56607336057673ee0efb3df92844986c412e94c2f8dae710 | 0 |  |

Interpretation:

- SHA256 agreement: yes (4245ac7122381c1f56607336057673ee0efb3df92844986c412e94c2f8dae710).
- Input checksum agreement: yes (0xd6ed7370bcfab27e).
- Native return-code agreement: yes (0).
- Native after-command return-code agreement: not used.
- Naive DMP CTLW misses: 16044; COPPER CLPD-64K+PEB CTLW misses: 442; reduction: 97.2%.
- SPP+COPPER slack CTLW misses: 413; reduction versus naive DMP: 97.4%.
- COPPER translation faults: 0; SPP+COPPER slack translation faults: 0.
- SPP+COPPER slack tick gap versus SPP: -0.023 percentage points.
- This is stronger official-command evidence than a local libcrypto driver, but it is still a fixed-workload CLI digest rather than the official timer-driven `openssl speed` benchmark.

status=PASS
