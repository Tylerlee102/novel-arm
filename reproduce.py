#!/usr/bin/env python3
"""One-command local reproduction runner for the COPPER public artifact."""

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
    log_name = step.name.lower().replace(" ", "_").replace("/", "_") + ".log"
    log_path = OUT_DIR / log_name
    log_path.write_text(proc.stdout, encoding="utf-8")
    if proc.returncode == 0:
        return StepResult(step.name, "PASS", elapsed, f"log={rel(log_path)}")
    status = "FAIL" if step.required else "SKIP"
    tail = "\n".join(proc.stdout.splitlines()[-8:])
    return StepResult(step.name, status, elapsed, f"log={rel(log_path)}; tail={tail}")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def audit_manifest_rows() -> StepResult:
    start = time.perf_counter()
    manifest = RESULTS / "copper_public_artifact_manifest_20260620.csv"
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
        "mibench_12k": RESULTS / "MIBENCH_PATRICIA_12K_SEED_STABILITY_20260621.md",
        "public_manifest": RESULTS / "COPPER_PUBLIC_ARTIFACT_MANIFEST_20260620.md",
        "claim_matrix": RESULTS / "COPPER_CLAIM_EVIDENCE_MATRIX_20260617.md",
    }
    for key, path in candidates.items():
        body = path.read_text(encoding="utf-8", errors="replace")
        for line in body.splitlines():
            if "Passed " in line and "artifact checks" in line:
                results[key] = line.strip()
                break
            if "status=PASS" in line or "manifest_status=PASS" in line:
                results.setdefault(key, line.strip())
            if "Minimum COPPER" in line or "Distinct per-seed checksums" in line:
                results.setdefault(key, line.strip())
    return results


def local_steps(mode: str) -> list[Step]:
    py = sys.executable
    steps = [
        Step("Python compile check", [py, "-m", "py_compile",
            "research/verify_copper_artifacts.py",
            "research/build_copper_claim_evidence_matrix.py",
            "research/build_copper_public_artifact_manifest.py",
            "research/summarize_mibench_patricia_seed_stability.py",
            "research/summarize_pcre2_seed_stability.py",
            "research/summarize_compression_seed_stability.py",
        ]),
        Step("MiBench Patricia 12K seed summary", [py, "research/summarize_mibench_patricia_seed_stability.py"]),
        Step("PCRE2 seed summary", [py, "research/summarize_pcre2_seed_stability.py"]),
        Step("Compression seed summary", [py, "research/summarize_compression_seed_stability.py"]),
        Step("Application overhead figures", [py, "research/plot_copper_app_overhead_figures.py"], required=have_module("matplotlib")),
        Step("Application full-baseline figure", [py, "research/plot_copper_app_full_baseline_runtime.py"], required=have_module("matplotlib")),
        Step("Public artifact manifest precheck", [py, "research/build_copper_public_artifact_manifest.py"]),
        Step("Claim evidence matrix", [py, "research/build_copper_claim_evidence_matrix.py"]),
        Step("Artifact audit", [py, "research/verify_copper_artifacts.py"], required=have_module("pypdf")),
        Step("Public artifact manifest final", [py, "research/build_copper_public_artifact_manifest.py"]),
    ]
    if mode == "quick":
        return [step for step in steps if step.name not in {"Application overhead figures", "Application full-baseline figure"}]
    return steps


def write_report(step_results: list[StepResult], manifest_result: StepResult) -> None:
    key_results = extract_key_results()
    tools = external_tool_status()
    all_results = step_results + [manifest_result]
    status = "PASS" if all(r.status in {"PASS", "SKIP"} for r in all_results) else "FAIL"
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
            "This run reproduces the clone-local evidence checks, derived summaries, figures, and manifest hashes.",
            "Raw full-system gem5 and Vivado reruns require the external tools listed above; this runner records their availability but does not install licensed tools or rebuild the full simulator stack by default.",
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
    parser.add_argument("--mode", choices=["quick", "all-local"], default="all-local")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    step_results = [run_step(step) for step in local_steps(args.mode)]
    manifest_result = audit_manifest_rows()
    write_report(step_results, manifest_result)
    print(REPORT)
    return 0 if all(r.status in {"PASS", "SKIP"} for r in step_results + [manifest_result]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
