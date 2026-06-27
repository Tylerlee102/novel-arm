#!/usr/bin/env python3
"""One-command local reproduction runner for paper-facing COPPER artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESEARCH = ROOT / "research"
RESULTS = RESEARCH / "results"
OUT_DIR = RESULTS / "reproduction"
REPORT = OUT_DIR / "LOCAL_REPRODUCTION_REPORT.md"
SUMMARY_JSON = OUT_DIR / "local_reproduction_summary.json"


@dataclass
class Step:
    name: str
    command: list[str]
    required: bool = True


@dataclass
class StepResult:
    name: str
    status: str
    seconds: float
    detail: str


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def have_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def run_step(step: Step) -> StepResult:
    if not step.required:
        return StepResult(step.name, "SKIP", 0.0, "optional dependency missing")

    start = time.perf_counter()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(RESEARCH) + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        step.command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    elapsed = time.perf_counter() - start
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log_name = step.name.lower().replace(" ", "_").replace("/", "_") + ".log"
    log_path = OUT_DIR / log_name
    log_path.write_text(proc.stdout, encoding="utf-8")
    if proc.returncode == 0:
        return StepResult(step.name, "PASS", elapsed, f"log={rel(log_path)}")
    tail = "\n".join(proc.stdout.splitlines()[-8:])
    return StepResult(step.name, "FAIL", elapsed, f"log={rel(log_path)}; tail={tail}")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def audit_manifest_rows() -> StepResult:
    start = time.perf_counter()
    manifest = RESULTS / "copper_public_artifact_manifest_20260620.csv"
    if not manifest.exists():
        return StepResult("Manifest hash audit", "FAIL", 0.0, f"missing {rel(manifest)}")
    missing: list[str] = []
    mismatched: list[str] = []
    checked = 0
    external = 0
    with manifest.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            path = ROOT / row["path"]
            if row["package_recommendation"] == "external-store-with-hash":
                external += 1
                continue
            checked += 1
            if not path.exists():
                missing.append(row["path"])
                continue
            if file_sha256(path) != row["sha256"]:
                mismatched.append(row["path"])
    elapsed = time.perf_counter() - start
    if missing or mismatched:
        detail = f"checked={checked}, external={external}, missing={missing[:8]}, mismatched={mismatched[:8]}"
        return StepResult("Manifest hash audit", "FAIL", elapsed, detail)
    return StepResult("Manifest hash audit", "PASS", elapsed, f"checked={checked}, external_by_hash={external}")


def external_tool_status() -> dict[str, str]:
    tools = {
        "python": sys.executable,
        "git": shutil.which("git") or "",
        "bash": shutil.which("bash") or "",
        "vivado": shutil.which("vivado") or shutil.which("vivado.bat") or "",
        "gem5_fast_expected": str(ROOT / "external" / "gem5" / "build" / "ARM" / "gem5.fast.exe"),
    }
    return {name: (value if value and Path(value).exists() else "not found") for name, value in tools.items()}


def extract_key_results() -> dict[str, str]:
    results: dict[str, str] = {}
    candidates = {
        "artifact_audit": RESULTS / "COPPER_ARTIFACT_AUDIT_20260616.md",
        "claim_matrix": RESULTS / "COPPER_CLAIM_EVIDENCE_MATRIX_20260617.md",
        "public_manifest": RESULTS / "COPPER_PUBLIC_ARTIFACT_MANIFEST_20260620.md",
        "figure_index": RESULTS / "figures" / "COPPER_APP_FIGURE_INDEX_20260616.md",
    }
    for key, path in candidates.items():
        if not path.exists():
            continue
        body = path.read_text(encoding="utf-8", errors="replace")
        for line in body.splitlines():
            if "Passed " in line and "artifact checks" in line:
                results[key] = line.strip()
                break
            if "status=PASS" in line or "manifest_status=PASS" in line:
                results.setdefault(key, line.strip())
    return results


def local_steps(mode: str) -> list[Step]:
    py = sys.executable
    steps = [
        Step(
            "Python compile check",
            [
                py,
                "-m",
                "py_compile",
                "research/verify_copper_artifacts.py",
                "research/build_copper_claim_evidence_matrix.py",
                "research/analyze_copper_energy_pollution_scorecard.py",
                "research/analyze_copper_dram_energy_scorecard.py",
                "research/plot_copper_app_overhead_figures.py",
                "research/plot_copper_app_full_baseline_runtime.py",
                "research/audit_sanity_checks.py",
            ],
        ),
        Step("Energy/pollution scorecard", [py, "research/analyze_copper_energy_pollution_scorecard.py"]),
        Step("DRAM energy scorecard", [py, "research/analyze_copper_dram_energy_scorecard.py"]),
        Step("Application overhead figures", [py, "research/plot_copper_app_overhead_figures.py"], required=have_module("matplotlib")),
        Step("Application full-baseline figure", [py, "research/plot_copper_app_full_baseline_runtime.py"], required=have_module("matplotlib")),
        Step("Claim evidence matrix", [py, "research/build_copper_claim_evidence_matrix.py"]),
        Step("Artifact audit", [py, "research/verify_copper_artifacts.py"], required=have_module("pypdf")),
        Step("Audit sanity checks", [py, "research/audit_sanity_checks.py"]),
        Step("Public artifact manifest", [py, "research/build_copper_public_artifact_manifest.py"]),
    ]
    if mode == "quick":
        return [
            step
            for step in steps
            if step.name
            not in {
                "Application overhead figures",
                "Application full-baseline figure",
                "Public artifact manifest",
            }
        ]
    return steps


def write_report(step_results: list[StepResult], manifest_result: StepResult) -> None:
    key_results = extract_key_results()
    tools = external_tool_status()
    all_results = step_results + [manifest_result]
    status = "PASS" if all(result.status in {"PASS", "SKIP"} for result in all_results) else "FAIL"
    ran_steps = {result.name for result in step_results}
    if {"Application overhead figures", "Application full-baseline figure", "Public artifact manifest"} <= ran_steps:
        scope_line = (
            "This runner reproduces clone-local derived scorecards, application figures, "
            "evidence-string checks, sanity checks, public-manifest generation, and manifest hashes."
        )
    else:
        scope_line = (
            "Quick mode reproduces clone-local derived scorecards, evidence-string checks, "
            "sanity checks, and manifest hashes; use --mode all-local to regenerate "
            "application figures and public-manifest metadata as well."
        )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# COPPER Local Reproduction Report",
        "",
        f"Overall status: {status}",
        "",
        "## Environment",
        "",
        f"- Python: `{sys.version.split()[0]}`",
        f"- Platform: `{platform.platform()}`",
        f"- Root: `{ROOT}`",
        "",
        "## Dependency Status",
        "",
        f"- pypdf: {'present' if have_module('pypdf') else 'missing'}",
        f"- matplotlib: {'present' if have_module('matplotlib') else 'missing'}",
        f"- reportlab: {'present' if have_module('reportlab') else 'missing'}",
        f"- python-docx: {'present' if have_module('docx') else 'missing'}",
        "",
        "## External Tool Status",
        "",
    ]
    for name, value in tools.items():
        lines.append(f"- {name}: `{value}`")
    lines.extend(["", "## Step Results", "", "| Step | Status | Seconds | Detail |", "|---|---:|---:|---|"])
    for result in all_results:
        detail = result.detail.replace("\n", "<br>")
        lines.append(f"| {result.name} | {result.status} | {result.seconds:.2f} | {detail} |")
    lines.extend(["", "## Key Reproduced Results", ""])
    for key, value in key_results.items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Scope",
            "",
            scope_line,
            "Raw full-system gem5 and Vivado reruns require the external tools listed above; this runner records their availability but does not install licensed tools or rebuild the full simulator stack.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    SUMMARY_JSON.write_text(
        json.dumps(
            {
                "status": status,
                "report": rel(REPORT),
                "steps": [result.__dict__ for result in all_results],
                "key_results": key_results,
                "external_tools": tools,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["quick", "all-local"], default="quick")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    step_results = [run_step(step) for step in local_steps(args.mode)]
    manifest_result = audit_manifest_rows()
    write_report(step_results, manifest_result)
    print(REPORT)
    return 0 if all(result.status in {"PASS", "SKIP"} for result in step_results + [manifest_result]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
