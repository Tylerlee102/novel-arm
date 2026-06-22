# Lua AArch64 Full-System Medium Seed Sweep

Date: 2026-06-17

This sweep repeats the public Lua 5.4.8 table/runtime workload across
three medium-size layout seeds. Seed 0 is the prior `app_medium` run;
seeds 1 and 2 use the workload `--seed` argument. Each run uses 2,048
rows, 6,000 lookups, 2,048 updates, and 6,000 linked traversals under
ARM64/Linux gem5 full-system timing.

| Seed | Policy | Delta vs none | ROI ticks | L1D misses | PF issued | PF useful | Pointer-like | Allowed | Blocked | CTLW misses | Translation faults | Checksum | rc |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| 0 | none | 0.000% | 38222677395 | 396700 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x1087e661 | 0 |
| 0 | naive | -1.929% | 37485191286 | 385791 | 74914 | 12522 | 106125 | 106125 | 0 | 31209 | 0 | 0x1087e661 | 0 |
| 0 | copper_clpd64k_peb | -2.153% | 37399695201 | 381455 | 73613 | 16745 | 147770 | 76319 | 71451 | 2706 | 0 | 0x1087e661 | 0 |
| 0 | spp | -29.532% | 26934731640 | 150510 | 1911196 | 264160 | 0 | 0 | 0 | 0 | 0 | 0x1087e661 | 0 |
| 0 | spp_copper_slack | -29.240% | 27046477116 | 152897 | 1858545 | 261573 | 272364 | 25216 | 247148 | 966 | 0 | 0x1087e661 | 0 |
| 1 | none | 0.000% | 38162873925 | 393726 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xb0f65a6 | 0 |
| 1 | naive | -1.920% | 37429964568 | 378625 | 84132 | 17052 | 97148 | 97148 | 0 | 13014 | 0 | 0xb0f65a6 | 0 |
| 1 | copper_clpd64k_peb | -2.537% | 37194868899 | 368926 | 96362 | 26399 | 137912 | 97146 | 40766 | 784 | 0 | 0xb0f65a6 | 0 |
| 1 | spp | -27.928% | 27504914220 | 156527 | 1943237 | 256618 | 0 | 0 | 0 | 0 | 0 | 0xb0f65a6 | 0 |
| 1 | spp_copper_slack | -28.688% | 27214588503 | 150543 | 1971855 | 263038 | 255314 | 23297 | 232017 | 364 | 0 | 0xb0f65a6 | 0 |
| 2 | none | 0.000% | 38170423701 | 393792 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0x40166f35 | 0 |
| 2 | naive | -2.005% | 37405089135 | 378496 | 84283 | 17083 | 97551 | 97551 | 0 | 13266 | 0 | 0x40166f35 | 0 |
| 2 | copper_clpd64k_peb | -2.601% | 37177757361 | 368923 | 96715 | 26413 | 138549 | 97568 | 40981 | 853 | 0 | 0x40166f35 | 0 |
| 2 | spp | -27.757% | 27575606457 | 157093 | 1918292 | 256291 | 0 | 0 | 0 | 0 | 0 | 0x40166f35 | 0 |
| 2 | spp_copper_slack | -28.355% | 27347018274 | 153046 | 1977186 | 260359 | 253697 | 22566 | 231131 | 397 | 0 | 0x40166f35 | 0 |

Aggregate:

| Policy | Seeds | Mean delta vs none | Min delta | Max delta | Total CTLW misses | Translation faults |
|---|---:|---:|---:|---:|---:|---:|
| none | 3 | 0.000% | 0.000% | 0.000% | 0 | 0 |
| naive | 3 | -1.951% | -2.005% | -1.920% | 57489 | 0 |
| copper_clpd64k_peb | 3 | -2.430% | -2.601% | -2.153% | 4343 | 0 |
| spp | 3 | -28.406% | -29.532% | -27.757% | 0 | 0 |
| spp_copper_slack | 3 | -28.761% | -29.240% | -28.355% | 1727 | 0 |

Interpretation:

- Checksum and `rc=0` agree within each seed across all policies: yes.
- COPPER CLPD-64K+PEB beats unsafe naive DMP on all three medium Lua layouts: yes.
- COPPER cuts aggregate naive CTLW misses by 92.446%.
- SPP+COPPER slack stays within 0.760 percentage points of SPP across the medium seeds and cuts aggregate naive CTLW misses by 96.996%.
- Total fill-origin translation faults across the sweep: 0.
- This improves application-layout stability evidence, but it remains a bounded language-runtime study rather than a SPEC-scale statistical campaign.

status=PASS
