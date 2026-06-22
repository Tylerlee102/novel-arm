# COPPER Application Baseline Matrix

Date: 2026-06-17

This report adds the missing ordinary address-stream baselines to the 12 public AArch64 full-system application points: eight medium/stress single-engine public runs, two bounded JSON+SQLite service-composition runs, and two bounded cache-service hash/LRU scale points. It is intended to prevent an unfair comparison where COPPER/SCOOP is only compared against naive DMP and SPP.

| Workload | Best conventional | Best conv delta | Naive DMP delta | COPPER delta | SPP delta | SPP+COPPER slack delta | Slack gap to best conv | COPPER CTLW red. | Slack CTLW red. | Faults | Checksum/rc |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| SQLite medium | spp | -3.623% | -0.010% | -0.000% | -3.623% | -3.617% | 0.006 pp | 92.6% | 89.1% | 0/0 | yes/yes |
| SQLite stress | spp | -2.587% | -0.007% | -0.037% | -2.587% | -2.549% | 0.038 pp | 94.1% | 90.2% | 0/0 | yes/yes |
| Lua medium | spp | -29.532% | -1.929% | -2.153% | -29.532% | -29.240% | 0.292 pp | 91.3% | 96.9% | 0/0 | yes/yes |
| Lua stress | spp | -31.392% | -2.426% | -2.800% | -31.392% | -31.120% | 0.272 pp | 76.9% | 96.3% | 0/0 | yes/yes |
| Duktape medium | spp | -6.732% | -0.157% | -0.135% | -6.732% | -6.950% | -0.218 pp | 90.8% | 91.5% | 0/0 | yes/yes |
| Duktape stress | spp | -8.385% | -0.251% | -0.189% | -8.385% | -8.745% | -0.360 pp | 90.5% | 90.0% | 0/0 | yes/yes |
| yyjson medium | spp | -18.351% | -0.100% | -0.069% | -18.351% | -18.342% | 0.009 pp | 98.9% | 98.5% | 0/0 | yes/yes |
| yyjson stress | spp | -22.097% | -0.028% | -0.052% | -22.097% | -22.186% | -0.089 pp | 98.9% | 97.4% | 0/0 | yes/yes |
| JSON+SQLite medium | spp | -4.497% | -0.017% | -0.037% | -4.497% | -4.523% | -0.026 pp | 95.0% | 95.9% | 0/0 | yes/yes |
| JSON+SQLite stress | spp | -3.588% | -0.102% | -0.080% | -3.588% | -3.623% | -0.035 pp | 91.4% | 96.6% | 0/0 | yes/yes |
| Cache-service small | spp | -13.440% | -0.339% | -0.087% | -13.440% | -13.406% | 0.034 pp | 99.5% | 99.5% | 0/0 | yes/yes |
| Cache-service medium | spp | -13.115% | -0.378% | -0.271% | -13.115% | -13.086% | 0.029 pp | 99.4% | 99.4% | 0/0 | yes/yes |

Aggregate interpretation:

- Best conventional policy counts across the 12 workloads: spp: 12.
- Mean runtime delta vs no prefetching: naive DMP -0.479%, standalone COPPER -0.492%, SPP -13.112%, and SPP+COPPER slack -13.116%.
- SPP+COPPER slack has an average signed gap of -0.004 percentage points versus the best conventional policy; the worst absolute gap among these rows is 0.360 percentage points.
- Standalone COPPER reduces CTLW misses by 91.1% versus naive DMP across the 12 rows; SPP+COPPER slack reduces them by 94.0%.
- COPPER and SPP+COPPER slack both report 0 total translation faults across the 12 rows.
- Checksums all match: yes; guest return codes all zero: yes.

Reviewer-facing takeaway:

- COPPER should not be presented as a universal replacement for address-stream prefetchers. In this app matrix, SPP is the best ordinary performance baseline on all 12 points.
- The stronger claim is that the slack companion keeps SPP-class timing while adding the COPPER authority filter and eliminating the modeled unsafe DMP behavior measured by CTLW misses and translation-fault counters.
- Standalone COPPER is the low-traffic authority path; SPP+COPPER slack is the coexistence path for systems that already want an aggressive conventional prefetcher.
