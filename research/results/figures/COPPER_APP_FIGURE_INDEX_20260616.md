# COPPER Application Figure Index

Source data: `research/results/copper_prefetch_traffic_overhead_20260616.csv`.

| Figure | PNG | SVG | Purpose |
|---|---|---|---|
| Full baseline runtime matrix | `research/results/figures/copper_app_full_baseline_runtime.png` | `research/results/figures/copper_app_full_baseline_runtime.svg` | Shows naive DMP, standalone COPPER, stride, DCPT, AMPM, SPP, and SPP+COPPER slack on the ten public app points. |
| Runtime deltas | `research/results/figures/copper_app_runtime_delta.png` | `research/results/figures/copper_app_runtime_delta.svg` | Compares raw timing behavior across no-prefetch-normalized app runs. |
| CTLW reduction | `research/results/figures/copper_app_ctlw_reduction.png` | `research/results/figures/copper_app_ctlw_reduction.svg` | Shows authority-risk reduction versus naive DMP. |
| Bus overhead | `research/results/figures/copper_app_bus_overhead.png` | `research/results/figures/copper_app_bus_overhead.svg` | Shows standalone COPPER memory-traffic cost versus no prefetching. |

Notes:

- Static charts were rendered with Matplotlib because Seaborn is not installed in the local bundled Python runtime.
- The figures intentionally keep SPP framed as the raw-performance baseline and standalone COPPER as the authority/low-overhead path.
