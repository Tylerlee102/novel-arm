# OpenSSL EVP/HMAC Crypto-Suite AArch64 Full-System Summary

This workload is a deterministic native AArch64 Linux ROI that calls
OpenSSL libcrypto EVP AES-128-CTR, HMAC-SHA256, SHA256, and
CRYPTO_memcmp while maintaining session hash/LRU metadata and
pointer-shaped ticket words loaded as data.

Input tag: `app_smoke`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 16254513549 | 0.000% | 20839418 | 257318 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x444a220a9b27e7d0 | 0 |
| stride | 15191413713 | -6.540% | 20167268 | 226397 | -12.017% | 47797 | 24677 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x444a220a9b27e7d0 | 0 |
| naive | 16387939323 | 0.821% | 20966473 | 253855 | -1.346% | 30132 | 6588 | 46820 | 1533 | 46820 | 0 | 16685 | 0 | 0 | 0x444a220a9b27e7d0 | 0 |
| copper_clpd64k_peb | 16373406537 | 0.731% | 20966330 | 253293 | -1.564% | 34014 | 6857 | 68239 | 1506 | 34968 | 33271 | 954 | 0 | 17737 | 0x444a220a9b27e7d0 | 0 |
| dcpt | 14738209371 | -9.329% | 20743891 | 210261 | -18.287% | 530680 | 53133 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x444a220a9b27e7d0 | 0 |
| spp | 13897421001 | -14.501% | 20154565 | 128908 | -49.903% | 1046928 | 147022 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x444a220a9b27e7d0 | 0 |
| ampm | 14319643689 | -11.904% | 20163363 | 189621 | -26.309% | 866025 | 94729 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x444a220a9b27e7d0 | 0 |
| spp_copper_slack | 13889147949 | -14.552% | 20154629 | 130699 | -49.207% | 1066647 | 145671 | 121667 | 1180 | 33840 | 87827 | 828 | 0 | 10234 | 0x444a220a9b27e7d0 | 0 |

Interpretation:

- Checksum agreement: yes (0x444a220a9b27e7d0).
- Naive DMP CTLW misses: 16685; COPPER CLPD-64K+PEB CTLW misses: 954; reduction: 94.3%.
- SPP+COPPER slack CTLW misses: 828; reduction versus naive DMP: 95.0%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is real libcrypto EVP/HMAC/SHA execution through the guest dynamic loader, but it remains a small service-style driver rather than a full TLS stack or production crypto benchmark.

status=PASS
