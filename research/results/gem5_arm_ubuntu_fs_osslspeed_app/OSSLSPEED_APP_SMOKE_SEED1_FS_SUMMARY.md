# OpenSSL-Speed-Like AArch64 Full-System Summary

This workload is a deterministic native AArch64 Linux ROI that calls OpenSSL libcrypto EVP AES-128-CTR, SHA256, HMAC-SHA256, and CRYPTO_memcmp over fixed benchmark-style buffer sizes while maintaining pointer-shaped metadata records loaded as data. It is closer to `openssl speed` than the service-style OpenSSL driver, but it is not the official OpenSSL CLI benchmark.

Input tag: `app_smoke_seed1`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 16118345520 | 0.000% | 20287118 | 250036 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x93b5e788058c0a2f | 0 |
| naive | 16103193354 | -0.094% | 20287028 | 247528 | -1.003% | 29151 | 5269 | 45516 | 1464 | 45516 | 0 | 16363 | 0 | 0 | 0x93b5e788058c0a2f | 0 |
| copper_clpd64k_peb | 16087603626 | -0.191% | 20283903 | 246268 | -1.507% | 27617 | 5119 | 59558 | 1460 | 28873 | 30685 | 1256 | 0 | 17735 | 0x93b5e788058c0a2f | 0 |
| spp | 13998780207 | -13.150% | 20326216 | 130489 | -47.812% | 1089963 | 147424 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x93b5e788058c0a2f | 0 |
| spp_copper_slack | 13984501167 | -13.239% | 20326276 | 130748 | -47.708% | 1103389 | 147958 | 116531 | 1089 | 27259 | 89272 | 1190 | 0 | 10181 | 0x93b5e788058c0a2f | 0 |

Interpretation:

- Checksum agreement: yes (0x93b5e788058c0a2f).
- Naive DMP CTLW misses: 16363; COPPER CLPD-64K+PEB CTLW misses: 1256; reduction: 92.3%.
- SPP+COPPER slack CTLW misses: 1190; reduction versus naive DMP: 92.7%.
- COPPER translation faults: 0; SPP+COPPER slack translation faults: 0.
- SPP+COPPER slack tick gap versus SPP: -0.089 percentage points.
- This is real libcrypto execution through the guest dynamic loader over benchmark-style buffer sizes; it remains a local speed-like driver rather than the official OpenSSL CLI.

status=PASS
