# MiBench Patricia Scale Portfolio

This generated summary aggregates public MiBench network/patricia
full-system AArch64 runs over public `small.udp` and `large.udp`
packet-field inputs.
It is public trie benchmark-family evidence, not SPEC and not
production network routing software.

| Tag | Records | Lookups | Checksum | Naive CTLW | COPPER CTLW | COPPER reduction | Slack CTLW | Slack reduction | Slack gap vs SPP | COPPER/slack faults |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| patricia_preprobe | 128 | 256 | `0xe9324f49c2b21a34` | 11992 | 85 | 99.3% | 102 | 99.1% | -0.026 pp | 0 |
| patricia_small2048 | 2048 | 4096 | `0x11f999a2549d757f` | 14014 | 181 | 98.7% | 422 | 97.0% | +0.030 pp | 0 |
| patricia_small8192 | 8192 | 16384 | `0xd4f96d52a9711657` | 16478 | 245 | 98.5% | 379 | 97.7% | +0.050 pp | 0 |
| patricia_large12288 | 12288 | 24576 | `0x60874357358c1fc4` | 18454 | 381 | 97.9% | 635 | 96.6% | +0.035 pp | 0 |

Interpretation:

- MiBench Patricia scale points: 4.
- Largest public input records consumed: 12288.
- Minimum COPPER CTLW reduction versus naive DMP: 97.9%.
- Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 96.6%.
- Worst absolute SPP+COPPER slack tick gap versus SPP: 0.050 percentage points.
- COPPER/slack translation faults across scale points: 0.
- Checksum agreement holds within every scale point.

status=PASS
