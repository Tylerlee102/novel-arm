# SQLite AArch64 Full-System Application Summary

This is a public SQLite-amalgamation application-style workload:
in-memory B-tree insertions, point lookups, range scans, secondary-index
probes, updates, and pointer-shaped payload-table reads. It runs as a
native AArch64 Linux binary under the same gem5 full-system path used by
the COPPER heap, GAPBS, and Olden experiments.

Input tag: `app_stress`.

| Policy | ROI ticks | Delta vs none | Insts | L1D misses | L1D miss delta | PF issued | PF useful | Pointer-like | Learned proofs | Allowed | Blocked | CTLW misses | Translation faults | Boundary drops | Checksum | rc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| none | 104853074301 | 0.000% | 124795314 | 1120412 | 0.000% | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xc91843372c7ddc37 | 0 |
| stride | 104478346071 | -0.357% | 124797373 | 1077000 | -3.875% | 87216 | 45848 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xc91843372c7ddc37 | 0 |
| naive | 104845717998 | -0.007% | 124795306 | 1119261 | -0.103% | 102184 | 25143 | 145412 | 4202 | 145412 | 0 | 43226 | 0 | 0 | 0xc91843372c7ddc37 | 0 |
| copper_clpd64k_peb | 104813948799 | -0.037% | 124795270 | 1118376 | -0.182% | 109163 | 24211 | 168158 | 2662 | 111706 | 56452 | 2543 | 0 | 19725 | 0xc91843372c7ddc37 | 0 |
| dcpt | 103727213289 | -1.074% | 124780298 | 1065048 | -4.941% | 1216940 | 114651 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xc91843372c7ddc37 | 0 |
| spp | 102140339751 | -2.587% | 124787097 | 865108 | -22.787% | 2317251 | 472866 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xc91843372c7ddc37 | 0 |
| ampm | 104746008141 | -0.102% | 124804649 | 1175904 | 4.953% | 3624320 | 432405 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0xc91843372c7ddc37 | 0 |
| spp_copper_slack | 102179909475 | -2.549% | 124791541 | 872534 | -22.124% | 2426579 | 483854 | 273251 | 1176 | 97413 | 175838 | 4224 | 0 | 10458 | 0xc91843372c7ddc37 | 0 |

Interpretation:

- Checksum agreement: yes (0xc91843372c7ddc37).
- Naive DMP CTLW misses: 43226; COPPER CLPD-64K+PEB CTLW misses: 2543; reduction: 94.1%.
- Naive DMP translation faults: 0; COPPER CLPD-64K+PEB translation faults: 0.
- This workload is stronger external-validity evidence than generated pointer kernels, but it is still one application-style point and should not be oversold as representative of all database/runtime software.
