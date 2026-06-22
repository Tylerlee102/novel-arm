# OpenSSL-Speed-Like AArch64 Full-System Summary

This workload is a deterministic native AArch64 Linux ROI that calls OpenSSL libcrypto EVP AES-128-CTR, SHA256, HMAC-SHA256, and CRYPTO_memcmp over fixed benchmark-style buffer sizes while maintaining pointer-shaped metadata records loaded as data. It is closer to `openssl speed` than the service-style OpenSSL driver, but it is not the official OpenSSL CLI benchmark.

Input tag: `app_smoke`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 16112771100 | 0.000% | 20287121 | 249763 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x8f37fdbf14f45f13 | 0 |
| naive | 16097612940 | -0.094% | 20287121 | 247229 | -1.015% | 29153 | 5273 | 45508 | 1461 | 45508 | 0 | 16353 | 0 | 0 | 0x8f37fdbf14f45f13 | 0 |
| copper_clpd64k_peb | 16087479084 | -0.157% | 20283906 | 246002 | -1.506% | 27614 | 5121 | 59511 | 1458 | 28871 | 30640 | 1257 | 0 | 17735 | 0x8f37fdbf14f45f13 | 0 |
| spp | 13983831504 | -13.213% | 20326249 | 130153 | -47.889% | 1093082 | 147592 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x8f37fdbf14f45f13 | 0 |
| spp_copper_slack | 13990328001 | -13.172% | 20326279 | 130323 | -47.821% | 1105274 | 147933 | 116229 | 1088 | 27159 | 89070 | 1093 | 0 | 10181 | 0x8f37fdbf14f45f13 | 0 |

Interpretation:

- Checksum agreement: yes (0x8f37fdbf14f45f13).
- Naive DMP CTLW misses: 16353; COPPER CLPD-64K+PEB CTLW misses: 1257; reduction: 92.3%.
- SPP+COPPER slack CTLW misses: 1093; reduction versus naive DMP: 93.3%.
- COPPER translation faults: 0; SPP+COPPER slack translation faults: 0.
- SPP+COPPER slack tick gap versus SPP: +0.041 percentage points.
- This is real libcrypto execution through the guest dynamic loader over benchmark-style buffer sizes; it remains a local speed-like driver rather than the official OpenSSL CLI.

status=PASS
