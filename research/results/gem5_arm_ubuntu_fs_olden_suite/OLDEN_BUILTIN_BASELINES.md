# Olden Built-In Prefetcher Baselines

This compares COPPER against gem5 built-in prefetchers on public
randomized-allocation Olden workloads. BOP, SPP, DCPT, AMPM,
indirect-memory, and ISB are conventional address-stream/correlation
prefetchers; they are not content-derived DMP mechanisms and therefore
do not exercise COPPER's source-proof/target-witness safety counters.
The `spp_copper` and `spp_copper_slack` rows are different: they
keep SPP while adding COPPER as a safe content-derived companion lane.

| Workload | Policy | Mean tick delta vs none | Total PF issued | PF per 1K insts | CTLW misses | Translation faults |
|---|---|---:|---:|---:|---:|---:|
| small randomized suite | none | 0.000% | 0 | 0.000 | 0 | 0 |
| small randomized suite | stride | 10.107% | 1754572 | 10.248 | 0 | 0 |
| small randomized suite | bop | 0.271% | 2992528 | 17.433 | 0 | 0 |
| small randomized suite | spp | -2.962% | 17921165 | 104.430 | 0 | 0 |
| small randomized suite | spp_copper | -3.245% | 18915088 | 110.243 | 23532 | 0 |
| small randomized suite | spp_copper_slack | -3.192% | 19132372 | 111.473 | 23589 | 0 |
| small randomized suite | dcpt | -5.742% | 14541439 | 84.728 | 0 | 0 |
| small randomized suite | ampm | -2.465% | 22107403 | 128.898 | 0 | 0 |
| small randomized suite | indirect | -1.469% | 7196271 | 41.931 | 0 | 0 |
| small randomized suite | isb | -0.045% | 403654 | 2.338 | 0 | 0 |
| small randomized suite | naive | 0.039% | 349965 | 2.027 | 188223 | 0 |
| small randomized suite | copper_clpd64k_peb | -0.398% | 547939 | 3.176 | 29039 | 0 |
| medium randomized subset | none | 0.000% | 0 | 0.000 | 0 | 0 |
| medium randomized subset | stride | 11.565% | 3416573 | 12.516 | 0 | 0 |
| medium randomized subset | bop | -4.036% | 5283506 | 19.287 | 0 | 0 |
| medium randomized subset | spp | -5.870% | 29679379 | 109.179 | 0 | 0 |
| medium randomized subset | dcpt | -7.025% | 26705188 | 97.514 | 0 | 0 |
| medium randomized subset | ampm | -3.909% | 40142406 | 146.278 | 0 | 0 |
| medium randomized subset | indirect | -0.480% | 13132519 | 47.871 | 0 | 0 |
| medium randomized subset | isb | -0.695% | 676501 | 2.470 | 0 | 0 |
| medium randomized subset | naive | -2.829% | 192298 | 0.702 | 123516 | 0 |
| medium randomized subset | copper_clpd64k_peb | -2.616% | 639330 | 2.330 | 47145 | 0 |

Interpretation:

- DCPT and SPP are the best measured pure conventional baselines on both Olden points: DCPT is -5.742% small / -7.025% medium, and SPP is -2.963% small / -5.870% medium.
- On the small randomized suite, hybrid SPP+COPPER reaches -3.245% with stock Multi arbitration and -3.192% with the slack-only companion arbiter, slightly better than SPP alone while exercising COPPER's authority path with zero translation faults.
- COPPER CLPD-64K+PEB is not the fastest policy on Olden (-0.398% small / -2.616% medium), but it is the only policy in this table that evaluates content-derived pointer candidates under committed provenance and target-witness authority.
- Naive DMP produces 188,223 small-suite and 123,516 medium-subset CTLW misses; COPPER cuts those to 29,039 and 47,145 while preserving zero translation faults.
- BOP/SPP/DCPT/AMPM/indirect/ISB should be presented as conventional-performance baselines, not as safety baselines for data-dependent pointer chasing.
