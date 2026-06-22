# Official OpenSSL CLI Multi-Seed Stability

This summarizes official Ubuntu ARM64 `openssl` CLI fixed-workload runs over deterministic pointer-shaped input seeds. It covers SHA256 digest, AES-128-CTR plus output digest, and HMAC-SHA256. These are official-command fixed-workload datapoints, not timer-driven `openssl speed` results.

| Workload | Seeds | COPPER CTLW reduction min / mean | SPP+COPPER slack CTLW reduction min / mean | Worst abs slack-vs-SPP tick gap | Fault status | Correctness status |
|---|---:|---:|---:|---:|---|---|
| Official OpenSSL CLI SHA256 digest | 3 | 97.2% / 97.5% | 97.4% / 97.4% | 0.095 pp | zero faults | PASS |
| Official OpenSSL CLI AES-CTR + digest | 3 | 95.5% / 95.5% | 95.2% / 95.2% | 0.294 pp | zero faults | PASS |
| Official OpenSSL CLI HMAC-SHA256 | 3 | 96.9% / 96.9% | 97.4% / 97.5% | 0.053 pp | zero faults | PASS |

| Workload | Tag | Digest/MAC | Input checksum | Naive CTLW | COPPER CTLW | COPPER reduction | Slack CTLW | Slack reduction | SPP delta | Slack delta | Slack gap | COPPER/slack faults |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Official OpenSSL CLI SHA256 digest | fixed_64k | 77d85bbaaba62a96c40a96e4d9caf5d1265da704daade3a9f10d8e9dd8617cbe | 0xc59a1575a221a8e6 | 15940 | 387 | 97.6% | 415 | 97.4% | -17.786% | -17.691% | +0.095 pp | 0 |
| Official OpenSSL CLI SHA256 digest | fixed_64k_seed1 | 96175489d9b7d178b5966d5a9e4d65ff371dab5a1a19b421c0383341b7b42205 | 0xe4171b559e85fb67 | 16048 | 389 | 97.6% | 413 | 97.4% | -17.636% | -17.713% | -0.077 pp | 0 |
| Official OpenSSL CLI SHA256 digest | fixed_64k_seed2 | 4245ac7122381c1f56607336057673ee0efb3df92844986c412e94c2f8dae710 | 0xd6ed7370bcfab27e | 16044 | 442 | 97.2% | 413 | 97.4% | -17.677% | -17.700% | -0.023 pp | 0 |
| Official OpenSSL CLI AES-CTR + digest | aesctr_64k | 39839fb42f8d96fc3a570c163b6cd2edebb8467713d1de6671ede4f99382a076 | 0xc59a1575a221a8e6 | 32174 | 1463 | 95.5% | 1549 | 95.2% | -18.515% | -18.468% | +0.047 pp | 0 |
| Official OpenSSL CLI AES-CTR + digest | aesctr_64k_seed1 | 101627ce8b9b4e2d933a18d13cde9f416afdd81dd76bab934d0545048efa4d59 | 0xe4171b559e85fb67 | 32220 | 1463 | 95.5% | 1539 | 95.2% | -18.502% | -18.275% | +0.227 pp | 0 |
| Official OpenSSL CLI AES-CTR + digest | aesctr_64k_seed2 | 01accf653542e999c627a41a9286ad17da55a83c6cdd2b3b571ad2330357c999 | 0xd6ed7370bcfab27e | 32212 | 1463 | 95.5% | 1549 | 95.2% | -18.489% | -18.195% | +0.294 pp | 0 |
| Official OpenSSL CLI HMAC-SHA256 | hmac_64k | d3be5389af52965eb3084df01f75d9ed50f9af56e0cd391d05d760e034d7130a | 0xc59a1575a221a8e6 | 16903 | 524 | 96.9% | 435 | 97.4% | -17.323% | -17.335% | -0.012 pp | 0 |
| Official OpenSSL CLI HMAC-SHA256 | hmac_64k_seed1 | 02a3f90dc7f9202745ee10ec61a2c92dac401d9c9e2edde2e7db10834f19f618 | 0xe4171b559e85fb67 | 16905 | 525 | 96.9% | 421 | 97.5% | -17.309% | -17.256% | +0.053 pp | 0 |
| Official OpenSSL CLI HMAC-SHA256 | hmac_64k_seed2 | 534585d466138ec1a0f392e93573b3557587c9d9ec139f14f51b702c9c80ef81 | 0xd6ed7370bcfab27e | 16898 | 524 | 96.9% | 428 | 97.5% | -17.284% | -17.286% | -0.002 pp | 0 |

Interpretation:

- Across 9 official CLI seed/workload points, COPPER CTLW reduction is at least 95.5%.
- Across 9 official CLI seed/workload points, SPP+COPPER slack CTLW reduction is at least 95.2%.
- Worst absolute SPP+COPPER slack gap versus SPP is 0.294 percentage points.
- COPPER and SPP+COPPER slack translation faults remain zero.
- All official CLI commands preserve policy-independent digest/MAC fingerprints and return-code success.
- This strengthens standard-crypto evidence, but it remains fixed-workload CLI execution rather than timer-driven `openssl speed`.

status=PASS
