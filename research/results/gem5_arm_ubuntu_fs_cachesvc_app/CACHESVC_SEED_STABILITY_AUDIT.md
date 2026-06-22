# Cache-Service Seed Stability Audit

Date: 2026-06-18

Purpose: check whether the cache-service result is a one-layout accident.
This audit uses the same native AArch64 hash/LRU service workload at the
same small scale, but with two independent layout/data seeds and the key
authority policies: none, naive DMP, COPPER CLPD-64K+PEB, and
SPP+COPPER slack.

| Seed | Policy | Runtime delta | Pointer-like | Allowed | Blocked | CTLW misses | Faults | Checksum | rc |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|
| seed2 | none | 0.000% | 0 | 0 | 0 | 0 | 0 | 0xd8e12b7b2c5a2f4b | 0 |
| seed2 | naive | -0.339% | 4895 | 4895 | 0 | 3637 | 0 | 0xd8e12b7b2c5a2f4b | 0 |
| seed2 | copper_clpd64k_peb | -0.087% | 5264 | 612 | 4652 | 19 | 0 | 0xd8e12b7b2c5a2f4b | 0 |
| seed2 | spp_copper_slack | -13.406% | 7626 | 410 | 7216 | 19 | 0 | 0xd8e12b7b2c5a2f4b | 0 |
| seed3 | none | 0.000% | 0 | 0 | 0 | 0 | 0 | 0xe7084bb32bf4d77d | 0 |
| seed3 | naive | -0.238% | 4944 | 4944 | 0 | 3664 | 0 | 0xe7084bb32bf4d77d | 0 |
| seed3 | copper_clpd64k_peb | -0.111% | 5298 | 613 | 4685 | 19 | 0 | 0xe7084bb32bf4d77d | 0 |
| seed3 | spp_copper_slack | -13.347% | 7671 | 437 | 7234 | 20 | 0 | 0xe7084bb32bf4d77d | 0 |

Interpretation:

- COPPER CTLW reduction versus naive DMP is stable across 2 seeds: 99.5% to 99.5%.
- SPP+COPPER slack CTLW reduction versus naive DMP is stable across 2 seeds: 99.5% to 99.5%.
- COPPER and SPP+COPPER slack translation faults across the seed audit: 0.
- Checksums agree within each seed: yes; guest return codes all zero: yes.
- This is still a two-seed bounded service-style audit, not a production cache-server campaign, but it reduces the risk that the cache-service result is a single layout accident.

seed_stability_status=PASS
