# OpenSSL EVP/HMAC Crypto-Suite AArch64 Full-System Summary

This workload is a deterministic native AArch64 Linux ROI that calls
OpenSSL libcrypto EVP AES-128-CTR, HMAC-SHA256, SHA256, and
CRYPTO_memcmp while maintaining session hash/LRU metadata and
pointer-shaped ticket words loaded as data.

Input tag: `app_medium`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 20223897858 | 0.000% | 27288916 | 271773 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xf642ebd3ac6f45be | 0 |
| naive | 20204232876 | -0.097% | 27293922 | 268047 | -1.371% | 31577 | 6649 | 49437 | 1575 | 49437 | 0 | 17857 | 0 | 0 | 0xf642ebd3ac6f45be | 0 |
| copper_clpd64k_peb | 20195801649 | -0.139% | 27293179 | 267351 | -1.627% | 34893 | 6893 | 71003 | 1538 | 35785 | 35218 | 892 | 0 | 17737 | 0xf642ebd3ac6f45be | 0 |
| spp | 17750032533 | -12.232% | 26456000 | 141910 | -47.784% | 1110772 | 151729 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xf642ebd3ac6f45be | 0 |
| spp_copper_slack | 17745858378 | -12.253% | 26455980 | 141962 | -47.764% | 1120964 | 151447 | 124534 | 1211 | 36047 | 88487 | 716 | 0 | 10234 | 0xf642ebd3ac6f45be | 0 |

Interpretation:

- Checksum agreement: yes (0xf642ebd3ac6f45be).
- Naive DMP CTLW misses: 17857; COPPER CLPD-64K+PEB CTLW misses: 892; reduction: 95.0%.
- SPP+COPPER slack CTLW misses: 716; reduction versus naive DMP: 96.0%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is real libcrypto EVP/HMAC/SHA execution through the guest dynamic loader, but it remains a small service-style driver rather than a full TLS stack or production crypto benchmark.

status=PASS
