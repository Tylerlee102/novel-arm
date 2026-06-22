# PCRE2 Regex AArch64 Full-System Summary

This workload is a deterministic native AArch64 Linux ROI that calls
the public PCRE2 8-bit regex compiler and matcher through the Ubuntu
guest library stack while scanning log-like records containing
address-shaped ticket words loaded as data.

Input tag: `pcre2_seed1`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 21289588101 | 0.000% | 133726006 | 172719 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xfc469fc668f4c38c | 0 |
| naive | 21296069946 | 0.030% | 133726098 | 172465 | -0.147% | 5976 | 1211 | 15376 | 873 | 15376 | 0 | 9394 | 0 | 0 | 0xfc469fc668f4c38c | 0 |
| copper_clpd64k_peb | 21291670683 | 0.010% | 133725958 | 172394 | -0.188% | 4364 | 907 | 18002 | 824 | 4423 | 13579 | 59 | 0 | 17746 | 0xfc469fc668f4c38c | 0 |
| spp | 19564844904 | -8.101% | 133495086 | 74597 | -56.810% | 725600 | 109328 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xfc469fc668f4c38c | 0 |
| spp_copper_slack | 19565147934 | -8.100% | 133495086 | 74482 | -56.877% | 709731 | 109380 | 30629 | 637 | 2921 | 27708 | 107 | 0 | 10202 | 0xfc469fc668f4c38c | 0 |

Interpretation:

- Checksum agreement: yes (0xfc469fc668f4c38c).
- Return-code agreement: yes (0).
- Naive DMP CTLW misses: 9394; COPPER CLPD-64K+PEB CTLW misses: 59; reduction: 99.4%.
- SPP+COPPER slack CTLW misses: 107; reduction versus naive DMP: 98.9%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This is a public parser/matcher library point, not a production server workload.

status=PASS
