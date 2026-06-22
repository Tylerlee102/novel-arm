# Cache-Service Scale Sensitivity Audit

Date: 2026-06-18

Purpose: test whether the cache-service authority result survives a larger
service state. The medium point doubles item count, request count, and
hot-list scan depth relative to the small point, while keeping the key
authority policies fixed: none, naive DMP, COPPER CLPD-64K+PEB, and
SPP+COPPER slack.

| Scale | Items | Requests | Scan depth | Policy | Runtime delta | Pointer-like | Allowed | Blocked | CTLW misses | Faults | Checksum | rc |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---|---:|
| small | 256 | 512 | 32 | none | 0.000% | 0 | 0 | 0 | 0 | 0 | 0xd8e12b7b2c5a2f4b | 0 |
| small | 256 | 512 | 32 | naive | -0.339% | 4895 | 4895 | 0 | 3637 | 0 | 0xd8e12b7b2c5a2f4b | 0 |
| small | 256 | 512 | 32 | copper_clpd64k_peb | -0.087% | 5264 | 612 | 4652 | 19 | 0 | 0xd8e12b7b2c5a2f4b | 0 |
| small | 256 | 512 | 32 | spp_copper_slack | -13.406% | 7626 | 410 | 7216 | 19 | 0 | 0xd8e12b7b2c5a2f4b | 0 |
| medium | 512 | 1024 | 64 | none | 0.000% | 0 | 0 | 0 | 0 | 0 | 0x3d38f00f0464cb72 | 0 |
| medium | 512 | 1024 | 64 | naive | -0.378% | 6312 | 6312 | 0 | 4119 | 0 | 0x3d38f00f0464cb72 | 0 |
| medium | 512 | 1024 | 64 | copper_clpd64k_peb | -0.271% | 6950 | 1361 | 5589 | 24 | 0 | 0x3d38f00f0464cb72 | 0 |
| medium | 512 | 1024 | 64 | spp_copper_slack | -13.086% | 11155 | 1188 | 9967 | 26 | 0 | 0x3d38f00f0464cb72 | 0 |

Interpretation:

- COPPER CTLW reduction versus naive DMP across scales: 99.4% to 99.5%.
- SPP+COPPER slack CTLW reduction versus naive DMP across scales: 99.4% to 99.5%.
- COPPER and SPP+COPPER slack translation faults across the scale audit: 0.
- Checksums agree within each scale: yes; guest return codes all zero: yes.
- This is still a bounded micro-service scale audit, not a production cache-server campaign. It does reduce the risk that COPPER's cache-service authority behavior only appears at the smallest service state.

scale_sensitivity_status=PASS
