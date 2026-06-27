# Run COPPER CI Proof Now

This checkout is trigger-ready. Local Windows is editing-only. GitHub Actions, Codespaces, or Docker is the intended evidence environment for open-source RTL, Yosys synthesis, paper PDF, and artifact-package gates.

The proof threshold is a real run log plus downloaded artifacts. The existence of `.github/workflows/reproduce.yml`, `Dockerfile`, or `.devcontainer/devcontainer.json` is setup evidence only.

## Option A: GitHub Web UI, No GitHub CLI Needed

1. Push this branch to GitHub.
2. Open the repo on GitHub.
3. Click Actions.
4. Select `COPPER Reproduction` from `.github/workflows/reproduce.yml`.
5. Click Run workflow.
6. Choose branch `copper-ci-proof`.
7. Wait for the run to finish.
8. Download artifacts from the completed run.
9. Import the downloaded evidence:

```bash
python research/scripts/import_ci_artifacts.py --artifact-dir <downloaded-artifacts-folder>
```

If GitHub gives you a single zip instead of a folder, run:

```bash
python research/scripts/import_ci_artifacts.py --zip <github-actions-artifacts.zip>
```

## Option B: GitHub CLI

```bash
gh auth login
git checkout -b copper-ci-proof
git add .
git commit -m "Add COPPER CI proof workflow"
git push origin copper-ci-proof
gh workflow run reproduce.yml --ref copper-ci-proof
gh run list --workflow reproduce.yml --limit 5
gh run watch
gh run view --log
gh run download
python research/scripts/import_ci_artifacts.py --artifact-dir <downloaded-artifacts-folder>
```

If the workflow name differs in GitHub, use:

```bash
gh workflow list
gh workflow run "<actual workflow name>" --ref copper-ci-proof
```

## Optional Local Tool Installs

Windows GitHub CLI:

```powershell
winget install --id GitHub.cli
```

Windows Docker Desktop:

```powershell
winget install --id Docker.DockerDesktop
```

Do not mark CI, RTL, synthesis, paper, or artifact packaging PASS until the imported artifacts prove those gates.
