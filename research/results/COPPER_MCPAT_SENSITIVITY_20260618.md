# COPPER McPAT Sensitivity Scorecard

Scope: relative McPAT sensitivity from measured gem5 AArch64 ROI stats. The XML uses one fixed AArch64-style proxy core/cache model and changes only measured activity counters: cycles, committed instructions, cache/TLB accesses, and cache misses. This is not calibrated silicon power and does not include detailed COPPER metadata-table switching power.

Generated rows: 130; successful McPAT rows: 130.
Invalid/nonphysical McPAT rows excluded from means: 0.

## Mean Delta vs None

| Policy | Workloads | Runtime delta | McPAT total-energy delta | McPAT dynamic-energy delta | McPAT runtime-power delta | L1D miss delta | L2 read-miss delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| naive | 26 | -0.322% | -0.608% | -1.050% | -0.728% | -0.939% | 0.720% |
| copper_clpd64k_peb | 26 | -0.338% | -0.625% | -1.068% | -0.730% | -1.177% | 0.574% |
| spp | 26 | -12.061% | -9.892% | -5.296% | 7.544% | -37.955% | 36.941% |
| spp_copper_slack | 26 | -12.062% | -11.521% | -10.334% | 2.031% | -38.025% | 37.031% |

## Pairwise Checks

- McPAT total runtime energy: copper_clpd64k_peb <= naive on 12/26; mean delta -0.017%.
- McPAT runtime dynamic energy: copper_clpd64k_peb <= naive on 12/26; mean delta -0.019%.
- McPAT total runtime energy: spp_copper_slack <= spp on 14/26; mean delta -1.206%.
- McPAT runtime dynamic energy: spp_copper_slack <= spp on 13/26; mean delta -2.241%.

## Per-Workload McPAT Total-Energy Delta

| Workload | Naive | COPPER | SPP | SPP+COPPER slack |
|---|---:|---:|---:|---:|
| cachesvc_medium | -0.362% | -0.262% | -12.426% | -12.397% |
| cachesvc_small | -0.326% | -0.083% | -12.760% | -12.727% |
| duktape_medium | -0.142% | -0.122% | -6.147% | -6.346% |
| duktape_stress | -0.229% | -0.172% | -7.681% | -8.009% |
| jsonsqlite_medium | -0.014% | -0.034% | -4.076% | -4.103% |
| jsonsqlite_stress | -0.091% | -0.072% | -3.193% | -3.231% |
| libarchive_tiny | -0.157% | -0.105% | -14.688% | -14.688% |
| libxml2_tiny | 0.075% | 0.082% | -11.237% | -11.176% |
| lua_medium | -1.805% | -2.015% | -27.637% | -27.359% |
| lua_stress | -2.269% | -2.619% | -29.383% | -29.119% |
| osslcrypto_small | 0.812% | 0.728% | -13.681% | -13.725% |
| osslsha_small | -1.865% | -1.904% | -15.660% | -15.717% |
| ossltlsbio_small | -0.484% | -0.442% | -2.397% | -2.388% |
| ossltlstcp_process_scale2 | -0.216% | -0.383% | -10.609% | -10.715% |
| ossltlstcp_process_scale3 | -0.367% | -0.534% | -12.006% | -12.020% |
| pcre2_seed1 | 0.003% | -0.013% | -5.232% | -5.235% |
| pcre2_smoke | 0.001% | 0.037% | -5.284% | -5.243% |
| sqlite_medium | -0.006% | 0.003% | -3.337% | -3.328% |
| sqlite_stress | -0.002% | -0.031% | -2.364% | -2.325% |
| tlssvc_small | -0.116% | -0.076% | -12.985% | -13.009% |
| yyjson_medium | -0.091% | -0.063% | -16.936% | -16.930% |
| yyjson_stress | -7.943% | -7.963% | -26.669% | -26.748% |
| zlib_seed1 | -0.010% | 0.031% | 34.365% | -7.997% |
| zlib_tiny | -0.025% | -0.053% | -8.040% | -8.038% |
| zstd_seed1 | -0.020% | -0.080% | -13.511% | -13.554% |
| zstd_tiny | -0.169% | -0.109% | -13.629% | -13.429% |

## Caveats

- The McPAT XML is a fixed proxy and is used for relative sensitivity only.
- The gem5 CPU model is TimingSimple-style; the McPAT core model is therefore an architectural proxy rather than a matched implementation.
- COPPER metadata table, proof-table, and comparator switching are not separately modeled here; those remain RTL/Vivado or CACTI/RTL-power work.
- Rows where McPAT emits nonphysical sentinel-scale energy/power values are marked invalid and excluded from aggregate means.
- This scorecard is useful as a reviewer-facing sanity check that measured COPPER traffic does not obviously erase the energy story.
