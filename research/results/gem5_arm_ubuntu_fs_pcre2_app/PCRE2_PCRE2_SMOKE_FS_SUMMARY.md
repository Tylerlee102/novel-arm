# PCRE2 Regex AArch64 Full-System Summary

This workload is a deterministic native AArch64 Linux ROI that calls
the public PCRE2 8-bit regex compiler and matcher through the Ubuntu
guest library stack while scanning log-like records containing
address-shaped ticket words loaded as data.

Input tag: `pcre2_smoke`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 21268901142 | 0.000% | 133647034 | 174440 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x70905e0adac9ac17 | 0 |
| naive | 21267571473 | -0.006% | 133647734 | 174263 | -0.101% | 6575 | 1151 | 15987 | 885 | 15987 | 0 | 9406 | 0 | 0 | 0x70905e0adac9ac17 | 0 |
| copper_clpd64k_peb | 21292385634 | 0.110% | 133657814 | 174379 | -0.035% | 5296 | 841 | 18846 | 828 | 5358 | 13488 | 62 | 0 | 17746 | 0x70905e0adac9ac17 | 0 |
| spp | 19546196238 | -8.100% | 133426894 | 74542 | -57.268% | 772809 | 111515 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x70905e0adac9ac17 | 0 |
| spp_copper_slack | 19555851573 | -8.054% | 133426894 | 74241 | -57.440% | 767484 | 111794 | 33354 | 634 | 3134 | 30220 | 79 | 0 | 10202 | 0x70905e0adac9ac17 | 0 |

Interpretation:

- Checksum agreement: yes (0x70905e0adac9ac17).
- Return-code agreement: yes (0).
- Naive DMP CTLW misses: 9406; COPPER CLPD-64K+PEB CTLW misses: 62; reduction: 99.3%.
- SPP+COPPER slack CTLW misses: 79; reduction versus naive DMP: 99.2%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is a public parser/matcher library point, not a production server workload.

status=PASS
