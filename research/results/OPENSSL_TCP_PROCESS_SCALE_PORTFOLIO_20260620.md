# OpenSSL TCP Process-Server Scale Portfolio

Date: 2026-06-20

This artifact combines the two deterministic process-server seeds with scaled four-pair and eight-pair process-server points. Every point runs a forked TLS server process and parent TLS client process over AF_INET loopback inside a private user/network namespace under AArch64 full-system gem5. It is stronger than the original two one-pair seeds, but remains a bounded local server/client harness rather than a production TCP/TLS deployment.

## Source Summaries

- `research/results/gem5_arm_ubuntu_fs_ossltlstcp_app/ossltlstcp_tcp_netns_process_key1_summary.csv`
- `research/results/gem5_arm_ubuntu_fs_ossltlstcp_app/ossltlstcp_tcp_netns_process_seed1_summary.csv`
- `research/results/gem5_arm_ubuntu_fs_ossltlstcp_app/ossltlstcp_tcp_netns_process_scale2_summary.csv`
- `research/results/gem5_arm_ubuntu_fs_ossltlstcp_app/ossltlstcp_tcp_netns_process_scale3_summary.csv`

## Portfolio Table

| Point | Sessions | Handshakes | Records | Scan depth | Process pairs across policies | Checksum | Naive CTLW | COPPER CTLW | COPPER reduction | SPP+COPPER CTLW | SPP+COPPER reduction | SPP delta | Slack delta | Slack gap vs SPP | Child failures | COPPER/slack faults |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| seed0 | 16 | 1 | 1 | 4 | 5 | 0x57e171797b39f199 | 7185 | 111 | 98.5% | 131 | 98.2% | -9.784% | -9.884% | -0.100 pp | 0 | 0 |
| seed1 | 16 | 1 | 1 | 4 | 5 | 0x6afc80bc5e145a81 | 7175 | 111 | 98.5% | 136 | 98.1% | -9.984% | -10.114% | -0.130 pp | 0 | 0 |
| scale2 | 32 | 4 | 2 | 8 | 20 | 0x703cb54ece76864c | 23880 | 385 | 98.4% | 364 | 98.5% | -11.354% | -11.460% | -0.106 pp | 0 | 0 |
| scale3 | 64 | 8 | 2 | 16 | 40 | 0x46e083abee222484 | 39977 | 710 | 98.2% | 591 | 98.5% | -12.762% | -12.769% | -0.007 pp | 0 | 0 |

## Aggregate Interpretation

- Portfolio points: 4.
- Distinct checksums: 4.
- Total forked process TCP pairs across policies/points: 70.
- Child process failures across policies/points: 0.
- Minimum COPPER CTLW reduction versus naive DMP: 98.2%.
- Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 98.1%.
- Worst absolute SPP+COPPER slack tick gap versus SPP: 0.130 percentage points.
- COPPER/slack translation faults across portfolio: 0.

status=PASS
