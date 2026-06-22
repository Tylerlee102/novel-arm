# Cache-Service Poison vs No-Poison Control Audit

Date: 2026-06-18

Purpose: test whether the cache-service workload can be used as a clean
differential security oracle for pointer-shaped payload data. The answer is
no: even when payload words are constrained below the DMP candidate range,
the hash/LRU service still exposes real pointer fields and high-entropy
service data that produce pointer-like candidates. Therefore this workload
is valid as a service-style performance/authority stress point, but not as
the primary data-at-rest security oracle.

| Policy | Poison pointer-like | Clean pointer-like | Change | Poison allowed | Clean allowed | Poison CTLW | Clean CTLW | Faults poison/clean | Runtime poison | Runtime clean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| none | 0 | 0 | 0.0% | 0 | 0 | 0 | 0 | 0/0 | 0.000% | 0.000% |
| naive | 4895 | 4706 | -3.9% | 4895 | 4706 | 3637 | 3451 | 0/0 | -0.339% | -0.122% |
| copper_clpd64k_peb | 5264 | 5054 | -4.0% | 612 | 595 | 19 | 15 | 0/0 | -0.087% | -0.201% |
| spp_copper_slack | 7626 | 7338 | -3.8% | 410 | 396 | 19 | 23 | 0/0 | -13.406% | -13.054% |

Interpretation:

- Poisoned service run: COPPER reduces naive CTLW misses by 99.5% with zero translation faults.
- Clean no-poison run: COPPER reduces naive CTLW misses by 99.6% with zero translation faults.
- The no-poison run still has thousands of pointer-like candidates, so it does not isolate payload-shaped data. The residual candidates are consistent with the workload's real linked hash/LRU metadata and high-entropy service fields.
- Use the fake-only ROI, secret traffic oracle, observer oracle, and split scan/probe audit for differential security claims. Use the cache-service workload as an external-validity stress point showing that COPPER/SCOOP retain authority behavior on service-like pointer-rich code.
- Poison checksums agree: yes; clean checksums agree: yes.
- Guest return codes all zero: yes.

verdict=VALID_STRESS_POINT_NOT_CLEAN_SECURITY_ORACLE
status=PASS
