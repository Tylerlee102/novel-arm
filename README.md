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
- `research/results/COPPER_PUBLIC_ARTIFACT_MANIFEST_20260620.md` - included artifact manifest.
- `research/results/COPPER_PUBLIC_ARTIFACT_PACKAGE_BUILD_20260620.md` - package build/audit summary.
- `research/results/MIBENCH_PATRICIA_12K_SEED_STABILITY_20260621.md` - two-seed public workload stability result.

The larger local workspace used to generate this package includes simulator
builds, Vivado scratch data, and temporary outputs. Those are intentionally not
part of this GitHub artifact package.

## Quick Reproduction

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
