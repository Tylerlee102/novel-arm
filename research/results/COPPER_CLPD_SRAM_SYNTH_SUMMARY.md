# COPPER CLPD SRAM Synthesis Summary

Generated from Vivado utilization, timing, and synthesis logs.

| Run | Entries | Part | KiB | LUTs | FFs | BRAM tiles | BRAM % | WNS ns | WHS ns | Errors | Critical warnings | Fits part |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| clpd1k_a35t | 1024 | xc7a35tcpg236-1 | 8.12 | 191 | 144 | 4 | 8.00 | 2.960 | 0.152 | 0 | 0 | True |
| clpd2k_a35t | 2048 | xc7a35tcpg236-1 | 16.25 | 198 | 146 | 8 | 16.00 | 2.960 | 0.155 | 0 | 0 | True |
| clpd4k_a35t | 4096 | xc7a35tcpg236-1 | 32.50 | 200 | 148 | 15 | 30.00 | 2.960 | 0.156 | 0 | 0 | True |
| clpd8k_a35t | 8192 | xc7a35tcpg236-1 | 65.00 | 229 | 150 | 33 | 66.00 | 2.960 | 0.161 | 0 | 0 | True |
| clpd16k_a35t | 16384 | xc7a35tcpg236-1 | 130.00 | 307 | 152 | 65 | 130.00 | 2.960 | 0.166 | 0 | 1 | False |
| clpd16k_a200t | 16384 | xc7a200tfbg676-2 | 130.00 | 283 | 152 | 65 | 17.81 | 4.094 | 0.148 | 0 | 0 | True |
| clpd64k_a200t | 65536 | xc7a200tfbg676-2 | 520.00 | 629 | 156 | 260 | 71.23 | 3.274 | 0.149 | 0 | 0 | True |

## Routed 64K A200T Implementation

| Entries | Part | LUTs | FFs | BRAM tiles | BRAM % | DSPs | WNS ns | WHS ns | Route errors | Unrouted nets | Partial nets | Errors | Critical warnings |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 65536 | xc7a200tfbg676-2 | 636 | 170 | 260 | 71.23 | 0 | 0.362 | 0.281 | 0 | 0 | 0 | 0 | 0 |

Key interpretation:

- All completed runs infer true-dual-port RAM for the CLPD storage array.
- On the small Artix-7 35T, 8K entries fit at 66% BRAM; 16K synthesizes but overuses BRAM at 130%, so it is not a fit for that part.
- On Artix-7 200T, the evaluated full 64K CLPD capacity synthesizes with no errors or critical warnings, using 260 BRAM tiles (71.23%).
- The 64K A200T out-of-context routed implementation completes routing with 0 route errors, 0 unrouted nets, 0 partial nets, and meets the 10 ns timing target with 0.362 ns setup slack.
- The routed run emits out-of-context port-location warnings; use the routed timing as feasibility evidence for the block, not as full-chip signoff.
