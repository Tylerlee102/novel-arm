# Compression-Library Seed Stability

Date: 2026-06-20

This artifact aggregates two deterministic input seeds each for public
Zstd and zlib AArch64 Linux full-system workloads. The workloads call
the guest Ubuntu ARM64 library ABI over buffers containing
address-shaped words as data. They are library-driver evidence, not
production storage or network compression services.

| Library | Seed | Checksum | Naive CTLW | COPPER CTLW | COPPER reduction | SPP+COPPER CTLW | SPP+COPPER reduction | SPP delta | Slack delta | Slack gap vs SPP | Faults |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Zstd | 0 | 0x93d05761620949ad | 9239 | 49 | 99.470% | 51 | 99.448% | -15.931% | -15.748% | 0.183 | 0 |
| Zstd | 1 | 0x22c3e1e7b9a49990 | 9239 | 49 | 99.470% | 51 | 99.448% | -15.857% | -15.921% | -0.064 | 0 |
| zlib | 0 | 0xf5b59076d62b0a4a | 11336 | 65 | 99.427% | 58 | 99.488% | -13.773% | -13.809% | -0.036 | 0 |
| zlib | 1 | 0x258843db93c006e3 | 11450 | 65 | 99.432% | 57 | 99.502% | -13.626% | -13.652% | -0.026 | 0 |

Aggregate interpretation:

- Seed/library points: 4.
- Distinct library-checksum pairs: 4.
- Return-code agreement across all policies: yes.
- Minimum COPPER CTLW reduction versus naive DMP: 99.4%.
- Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 99.4%.
- Worst absolute SPP+COPPER slack tick gap versus SPP: 0.183 percentage points.
- COPPER/slack translation faults across all seed points: 0.
- The compression-library evidence strengthens public-library breadth, but does not replace SPEC-like, production server, or production compression-service evaluation.

status=PASS
