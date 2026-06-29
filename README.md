# COPPER Research Artifact

This repository contains the public, reviewer-facing artifact package for
COPPER: Committed Pointer-Provenance Prefetching.

Start here:

- `reproduce.ps1` / `reproduce.sh` - create a local Python environment and rerun the clone-local artifact checks.
- `reproduce.py` - the Python reproduction runner used by both wrapper scripts.
- `research/COPPER_FULL_PAPER.md` - full paper draft.
- `research/COPPER_FINAL_OUTPUT.md` - compact final idea summary.
- `research/COPPER_ARTIFACT_REPRODUCTION_GUIDE.md` - how to reproduce the model and audit results.
- `REPRODUCIBILITY_STATUS.md` - what can and cannot be rerun from a fresh clone.
- `docs/RUN_CI_NOW.md` - GitHub web UI and CLI paths to trigger and collect the CI-proof run.
- `research/results/COPPER_PUBLIC_ARTIFACT_MANIFEST_20260620.md` - included artifact manifest.
- `research/results/COPPER_PUBLIC_ARTIFACT_PACKAGE_BUILD_20260620.md` - package build/audit summary.
- `research/results/MIBENCH_PATRICIA_12K_SEED_STABILITY_20260621.md` - two-seed public workload stability result.

The larger local workspace used to generate this package includes simulator
builds, Vivado scratch data, and temporary outputs. Those are intentionally not
part of this GitHub artifact package.

## Quick Reproduction

Open-source reviewer path (Linux/Docker/CI):

```bash
make check-toolchain
make test
make rtl
make sim
make eval
make synth
make fullcore-synth
make mapped-ppa
make power-evidence
make sync-hardware-evidence
make hardware-evidence
make paper
make paper-audit
make artifact
```

Local Windows is editing-only for final RTL, Yosys, paper, and artifact-package
proof. GitHub Actions, Codespaces, or Docker is the intended evidence
environment for those gates.

The Dockerfile and GitHub Actions workflow install the open-source tools needed
for the model, RTL smoke simulation, generic Yosys synthesis, mapped-PPA
attempts, LaTeX paper build, and artifact packaging. The `mapped-ppa` CI job
tries OSS CAD Suite or equivalent Yosys/nextpnr tools first, then records
OpenROAD/Vivado availability without requiring paid tools.
The evaluation target also generates deterministic `cycle_model` evidence with
cache hit/miss latency, memory latency, prefetch lateness, queue drops, and
demand/prefetch traffic accounting. The final evidence pass adds a deterministic
`core_integrated` validation harness, explicit `gem5_*` BLOCKED rows when gem5
is not runnable, source-built C workload evidence via `make workloads`, a
source-backed `independent_sim` trace/event simulator, imported gem5
ARM full-system summary rows when checksum/return-code validation passes,
`gem5_statistical_summary.csv` imported-summary confidence rows where repeated
validated samples exist,
near-core-stub, PicoRV32 accepted-core-wrapper, and PicoRV32 tiny-SoC full-core
synthesis flows, a strict
`mapped_ppa.csv` place-and-route ledger, `proxy_assumed_memory_energy` rows,
optional Nangate45 ASIC-Liberty tool-power rows when OpenSTA/OpenROAD is
available, Vivado `report_power` rows when Vivado is available, and a McPAT
activity-proxy index when the local McPAT sensitivity output is present. These
are scoped evidence levels: `independent_sim` is not gem5, `core_integrated` is
not gem5, imported gem5 summary rows are not a clone-local rerun of every raw
full-system simulation, gem5 statistical rows are imported-summary statistics
rather than fresh raw-run confidence intervals,
the near-core stub is not a full CPU, the PicoRV32 accepted wrapper is not the
tiny-SoC full-core target, the PicoRV32 tiny-SoC full-core target is not a
production ARM/OoO integration, generic Yosys is not mapped timing, and Vivado
`report_power` is tool-estimated FPGA power rather than silicon or ASIC signoff
power. ASIC-Liberty rows, when present, are standard-cell tool estimates rather
than post-route signoff or silicon measurements. `mapped_ppa.csv` may be cited for timing only when it has matched PASS
rows from nextpnr, Vivado, or OpenROAD and real timing fields are not `NA`.
Vivado, OpenSTA/OpenROAD, and broader gem5 campaign reruns remain optional
external-tool paths.
The strongest current hardware claim is PicoRV32 tiny-SoC full-core mapped FPGA
PPA plus scoped full-core FPGA tool-power when those rows are present; it is not
post-route ASIC signoff, silicon, production ARM/OoO, or top-tier
architecture-readiness evidence.
`research/results/hardware_evidence_summary.csv` and
`research/results/top_tier_gate_status.csv` synchronize those rows and keep
remaining silicon/signoff blockers machine-readable.

If `gh` or Docker is unavailable on the local machine, use
`docs/RUN_CI_NOW.md` to trigger the GitHub Actions run from the GitHub web UI,
download artifacts, and import them with
`research/scripts/import_ci_artifacts.py`.

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\reproduce.ps1
```

If Python is not on `PATH`, set `COPPER_PYTHON` to a Python 3 interpreter before
running the command.

Linux/macOS:

```bash
./reproduce.sh
```

Direct Python, after installing `requirements.txt`:

```bash
python reproduce.py --mode all-local
```

Expected local result: `Overall status: PASS` in
`research/results/reproduction/LOCAL_REPRODUCTION_REPORT.md`.

Current conference-readiness status is tracked in
`research/CONFERENCE_READINESS_DASHBOARD.md`. The open-source GitHub Actions
path has passing evidence for toolchain, model, RTL compile/simulation,
evaluation, synthesis, paper, paper audit, artifact packaging, and artifact
upload. The evaluation flow generates no-prefetch, next-line, stride, simple
pointer-chase, and COPPER baseline rows with accuracy, coverage, lateness,
queue-drop, traffic, ablation, sensitivity, and seed/input-stability CSVs at
model, deterministic cycle-model, and deterministic core-integrated levels.
The independent simulator rows add a separate source-backed trace/event path,
and gem5 rows add validated imported ARM full-system summary evidence. The
remaining blockers for a top-tier architecture claim are post-route/silicon
signoff-grade power, production-scale core/SoC integration, and a fresh raw-run
external-simulator matrix with confidence intervals; missing signoff rows must
stay BLOCKED rather than being replaced by generic resource counts.
