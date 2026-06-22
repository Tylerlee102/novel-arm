# Olden Bisort Fingerprint Validation

This validation build keeps the public Bisort algorithm but adds compact
guest-side fingerprints over all tree values plus the spring value.
The fingerprint is order-independent: equal count, checksum, and
histogram hash across phases shows that the full value multiset is
preserved; equal fingerprints across policies show that COPPER did not
change architectural results for this checked run.

| Policy | Phase | Count | Expected | Checksum | Histogram hash | Min | Max | Spring | rc |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| none | initial | 4096 | 4096 | 202954 | 274282176826957977 | 0 | 99 | 8 | 0 |
| none | forward | 4096 | 4096 | 202954 | 274282176826957977 | 0 | 99 | 99 | 0 |
| none | backward | 4096 | 4096 | 202954 | 274282176826957977 | 0 | 99 | 0 | 0 |
| copper_clpd64k_peb | initial | 4096 | 4096 | 202954 | 274282176826957977 | 0 | 99 | 8 | 0 |
| copper_clpd64k_peb | forward | 4096 | 4096 | 202954 | 274282176826957977 | 0 | 99 | 99 | 0 |
| copper_clpd64k_peb | backward | 4096 | 4096 | 202954 | 274282176826957977 | 0 | 99 | 0 | 0 |

## COPPER Counters

| Policy | PF issued | Blocked no provenance | CTLW misses | Translation faults |
|---|---:|---:|---:|---:|
| none | 0 | 0 | 0 | 0 |
| copper_clpd64k_peb | 22970 | 7667 | 234 | 0 |

## Verdict

- Fingerprints match baseline vs COPPER: yes.
- Initial, forward, and backward phases preserve the same count, checksum, and histogram hash.
- COPPER issued 22970 prefetches, blocked 7667 candidates without provenance, and reported 0 translation faults.
