# OpenSSL TCP Process-Server Seed Stability

Date: 2026-06-20

This artifact aggregates two deterministic seeds for the OpenSSL libssl
process-separated TCP-netns workload. Each point runs a forked TLS server
process and parent TLS client process over AF_INET loopback inside a
private user/network namespace under AArch64 full-system gem5.
It is stronger than in-process loopback evidence, but remains a bounded
local server/client harness rather than a production TCP/TLS deployment.

| Seed | Checksum | Naive CTLW | COPPER CTLW | COPPER reduction | SPP+COPPER CTLW | SPP+COPPER reduction | COPPER delta | SPP delta | Slack delta | Slack gap vs SPP | Process pairs | Child failures | Faults |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0x57e171797b39f199 | 7185 | 111 | 98.5% | 131 | 98.2% | 0.036% | -9.784% | -9.884% | -0.100 pp | 5 | 0 | 0 |
| 1 | 0x6afc80bc5e145a81 | 7175 | 111 | 98.5% | 136 | 98.1% | -0.043% | -9.984% | -10.114% | -0.130 pp | 5 | 0 | 0 |

Aggregate interpretation:

- Process-server seed points: 2.
- Distinct seed checksums: 2.
- All rows used `tcp_loopback_netns_process`: yes.
- Total forked process TCP pairs across policies/seeds: 10.
- Child process failures across policies/seeds: 0.
- Minimum COPPER CTLW reduction versus naive DMP: 98.5%.
- Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 98.1%.
- Worst absolute SPP+COPPER slack tick gap versus SPP: 0.130 percentage points.
- COPPER/slack translation faults across both seeds: 0.

status=PASS
