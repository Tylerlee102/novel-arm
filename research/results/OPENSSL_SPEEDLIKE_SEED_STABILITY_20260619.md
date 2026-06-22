# OpenSSL-Speed-Like Two-Seed Stability

This summarizes two deterministic full-system AArch64 runs of the fixed-count OpenSSL-speed-like libcrypto driver. The driver calls real guest libcrypto EVP AES-128-CTR, SHA256, HMAC-SHA256, and `CRYPTO_memcmp` over fixed benchmark-style buffer sizes while retaining pointer-shaped metadata loaded as data. It remains a local speed-like driver, not the official OpenSSL CLI benchmark.

| Workload | Seeds | COPPER CTLW reduction min / mean | SPP+COPPER slack CTLW reduction min / mean | Worst abs slack-vs-SPP tick gap | Fault status | Checksum/rc status |
|---|---:|---:|---:|---:|---|---|
| OpenSSL speed-like fixed-buffer libcrypto | 2 | 92.3% / 92.3% | 92.7% / 93.0% | 0.089 pp | zero faults | PASS |

| Tag | Checksum | Naive CTLW | COPPER CTLW | COPPER reduction | Slack CTLW | Slack reduction | SPP delta | Slack delta | Slack gap | COPPER/slack faults |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| app_smoke | 0x8f37fdbf14f45f13 | 16353 | 1257 | 92.3% | 1093 | 93.3% | -13.213% | -13.172% | +0.041 pp | 0 |
| app_smoke_seed1 | 0x93b5e788058c0a2f | 16363 | 1256 | 92.3% | 1190 | 92.7% | -13.150% | -13.239% | -0.089 pp | 0 |

Interpretation:

- COPPER CTLW reduction is stable at 92.3% minimum across the two seeds.
- SPP+COPPER slack CTLW reduction is stable at 92.7% minimum across the two seeds.
- Worst absolute SPP+COPPER slack gap versus SPP is 0.089 percentage points.
- COPPER and SPP+COPPER slack translation faults remain zero.
- This strengthens the speed-like libcrypto evidence but does not convert it into an official OpenSSL CLI benchmark.

status=PASS
