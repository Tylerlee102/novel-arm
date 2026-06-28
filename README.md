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
make paper
make paper-audit
make artifact
```

Local Windows is editing-only for final RTL, Yosys, paper, and artifact-package
proof. GitHub Actions, Codespaces, or Docker is the intended evidence
environment for those gates.

The Dockerfile and GitHub Actions workflow install the open-source tools needed
for the model, RTL smoke simulation, generic Yosys synthesis, LaTeX paper build,
and artifact packaging. The Codespaces devcontainer uses the same image.
The evaluation target also generates deterministic `cycle_model` evidence with
cache hit/miss latency, memory latency, prefetch lateness, queue drops, and
demand/prefetch traffic accounting. The top-tier pass adds a deterministic
`core_integrated` validation harness, explicit `gem5_*` BLOCKED rows when gem5
is not runnable, source-built C workload evidence via `make workloads`, a
near-core-stub synthesis flow, and `proxy_assumed` energy rows. These are
scoped evidence levels: `core_integrated` is not gem5, the near-core stub is not
a full CPU, and the energy proxy is not measured power. Vivado and full gem5
campaign reruns remain optional external-tool paths.

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
These are not fresh gem5 results.
