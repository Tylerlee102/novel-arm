# OpenSSL Medium Seed Stability

Generated: 2026-06-19

## Scope

This report checks two independent data/layout seeds for the medium-scale OpenSSL libcrypto EVP/HMAC/SHA and OpenSSL libssl TLS memory-BIO full-system AArch64 workloads. It is a stability audit over real OpenSSL library execution, not a production networked TLS server or a broad standard crypto benchmark suite.

## Aggregate

| Workload | Seeds | COPPER CTLW reduction min/mean | SPP+COPPER CTLW reduction min/mean | COPPER faults | Slack faults | Worst abs slack-vs-SPP tick gap | Checksums/rc |
|---|---:|---:|---:|---:|---:|---:|---|
| OpenSSL libcrypto EVP/HMAC/SHA | 2 | 95.0% / 95.0% | 95.6% / 95.8% | 0 | 0 | 0.021 pp | PASS |
| OpenSSL libssl TLS memory-BIO | 2 | 98.8% / 98.8% | 97.2% / 97.2% | 0 | 0 | 0.333 pp | PASS |

## Per-Seed Detail

| Workload | Tag | None ticks | Naive CTLW | COPPER CTLW | COPPER reduction | Slack CTLW | Slack reduction | COPPER faults | Slack faults | SPP delta | Slack delta | Slack-SPP gap | Checksums | rc |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| OpenSSL libcrypto EVP/HMAC/SHA | app_medium | 20223897858 | 17857 | 892 | 95.0% | 716 | 96.0% | 0 | 0 | -12.232% | -12.253% | -0.021 pp | yes | yes |
| OpenSSL libcrypto EVP/HMAC/SHA | app_medium_seed2 | 20235874869 | 17815 | 881 | 95.1% | 782 | 95.6% | 0 | 0 | -12.285% | -12.267% | +0.018 pp | yes | yes |
| OpenSSL libssl TLS memory-BIO | app_medium | 37934604090 | 58980 | 725 | 98.8% | 1664 | 97.2% | 0 | 0 | -0.003% | -0.236% | -0.233 pp | yes | yes |
| OpenSSL libssl TLS memory-BIO | app_medium_seed2 | 37926346689 | 58951 | 725 | 98.8% | 1585 | 97.3% | 0 | 0 | 0.117% | -0.216% | -0.333 pp | yes | yes |

## Interpretation

Across the two medium seeds, both real OpenSSL workloads preserve checksum agreement and `rc=0` for every key policy. COPPER keeps translation faults at zero and cuts naive DMP CTLW misses by at least 95.0% on libcrypto and 98.8% on libssl TLS memory-BIO. The SPP+COPPER slack path remains close to SPP timing while preserving the authority filter. This reduces the reviewer risk that the crypto-library result is a one-seed accident, but it still does not replace a production networked TLS server, SPEC-like suite, or broad standard crypto benchmark campaign.

status=PASS
