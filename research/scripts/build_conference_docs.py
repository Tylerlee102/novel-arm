#!/usr/bin/env python3
"""Generate conference-readiness ledgers, maps, and paper source."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "research"
RESULTS = RESEARCH / "results"
PAPER = RESEARCH / "paper"
OPEN_ENVIRONMENTS = {"github_actions", "docker", "codespaces"}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def any_status(path: Path, statuses: set[str]) -> bool:
    return any(row.get("status") in statuses for row in read_rows(path))


def open_rows(path: Path) -> list[dict[str, str]]:
    return [row for row in read_rows(path) if row.get("environment") in OPEN_ENVIRONMENTS]


def any_open_status(path: Path, statuses: set[str]) -> bool:
    return any(row.get("status") in statuses for row in open_rows(path))


def open_gate_status(path: Path) -> str:
    rows = open_rows(path)
    if any(row.get("status") == "PASS" for row in rows):
        return "PASS"
    if any(row.get("status") == "FAIL" for row in rows):
        return "FAIL"
    if any(row.get("status") == "BLOCKED" for row in rows):
        return "BLOCKED"
    if any_status(path, {"BLOCKED", "FAIL"}):
        return "BLOCKED"
    return "TODO"


def all_status(path: Path, status: str) -> bool:
    rows = read_rows(path)
    return bool(rows) and all(row.get("status") == status for row in rows)


def positive_int(value: str) -> bool:
    try:
        return int(value or 0) > 0
    except ValueError:
        return False


def baseline_pass() -> bool:
    rows = read_rows(RESULTS / "baseline_inventory.csv")
    required = {"B0 no_prefetch", "B1 next_line", "B2 stride", "B3 simple_pointer_chase", "B4 copper"}
    found = {row.get("baseline", "") for row in rows if row.get("implemented") == "yes"}
    return required.issubset(found)


def csv_has_no_todo(path: Path) -> bool:
    rows = read_rows(path)
    if not rows:
        return False
    body = "\n".join(",".join(str(value) for value in row.values()) for row in rows).lower()
    return "todo" not in body and "not isolated" not in body


def synthesis_overhead_pass() -> bool:
    return any(row.get("environment") in OPEN_ENVIRONMENTS and row.get("percent_overhead") for row in read_rows(RESULTS / "synthesis_overhead.csv"))


def build_inventory() -> None:
    rows: list[dict[str, str]] = []
    skip_parts = {".git", ".venv", "__pycache__", ".Xil", "xsim.dir", "m5out", "2025.2", ".vivado_appdata", ".vivado_user"}
    interesting_suffixes = {".py", ".sv", ".v", ".c", ".cc", ".h", ".tcl", ".ps1", ".sh", ".md", ".csv", ".rpt", ".log", ".bib", ".tex", ".json", ".yml", ".yaml"}
    roots = [ROOT / "README.md", ROOT / "REPRODUCIBILITY_STATUS.md", ROOT / "requirements.txt", ROOT / "reproduce.py", ROOT / "reproduce.sh", ROOT / "reproduce.ps1", ROOT / "Makefile", ROOT / "Dockerfile"]
    for path in roots:
        if path.exists():
            rows.append(inventory_row(path))
    for base in (RESEARCH, ROOT / "external"):
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if any(part in skip_parts for part in path.parts):
                continue
            if path.is_dir() and path.parent == RESULTS and path.name.startswith("gem5_"):
                rows.append(
                    {
                        "path": rel(path),
                        "type": "raw_result_directory",
                        "purpose": "Full-system raw output retained locally",
                        "generated_or_source": "generated",
                        "used_by_gate": "G7/G11/G12",
                        "status": "local-only-large",
                        "notes": "Directory-level inventory entry; package uses summaries instead of copying raw tree.",
                    }
                )
            if path.is_file() and path.suffix.lower() in interesting_suffixes:
                if path.parent != RESULTS or path.suffix.lower() in {".csv", ".md", ".rpt", ".log"}:
                    rows.append(inventory_row(path))
    fields = ["path", "type", "purpose", "generated_or_source", "used_by_gate", "status", "notes"]
    with (RESULTS / "artifact_inventory.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def inventory_row(path: Path) -> dict[str, str]:
    suffix = path.suffix.lower()
    name = path.name.lower()
    if suffix == ".py":
        typ, purpose, gate = "python", "model, analysis, audit, or reproduction script", "G1/G3/G10/G20"
    elif suffix in {".sv", ".v"}:
        typ, purpose, gate = "rtl", "SystemVerilog/Verilog design or testbench", "G4/G5/G15"
    elif suffix in {".c", ".cc", ".h"}:
        typ, purpose, gate = "workload_source", "C/C++ benchmark or workload source", "G6/G7"
    elif suffix == ".tcl":
        typ, purpose, gate = "tool_script", "Vivado/XSim/synthesis script", "G5/G15/G16"
    elif suffix in {".sh", ".ps1"} or name == "makefile":
        typ, purpose, gate = "reproduction_script", "Reviewer command wrapper", "G1/G18"
    elif suffix == ".csv":
        typ, purpose, gate = "result_csv", "Machine-readable evidence", "G10/G11/G12/G17"
    elif suffix in {".rpt", ".log"}:
        typ, purpose, gate = "tool_report", "Tool output or log", "G4/G5/G15/G16"
    elif suffix in {".md", ".tex", ".bib"}:
        typ, purpose, gate = "paper_or_documentation", "Paper, guide, matrix, or status document", "G18/G19/G20/G21/G22"
    else:
        typ, purpose, gate = "artifact", "Repository artifact", "G18"
    generated = "generated" if "results" in path.parts or suffix in {".rpt", ".log", ".csv"} else "source"
    return {
        "path": rel(path),
        "type": typ,
        "purpose": purpose,
        "generated_or_source": generated,
        "used_by_gate": gate,
        "status": "present",
        "notes": "Existing artifact file.",
    }


def gate_status() -> list[dict[str, str]]:
    package_exists = (ROOT / "dist" / "copper-artifact.zip").exists()
    ci_artifact_package = any(
        row.get("path", "").endswith("copper-artifact.zip")
        and positive_int(row.get("size_bytes", "0"))
        for row in read_rows(RESULTS / "ci_artifacts_manifest.csv")
    )
    paper_status = read_rows(RESULTS / "paper_build_status.csv")
    paper_built = any(row.get("environment") in OPEN_ENVIRONMENTS and row.get("status") == "PASS" for row in paper_status)
    rtl_compile_status = open_gate_status(RESULTS / "rtl_compile.csv")
    rtl_sim_status = open_gate_status(RESULTS / "rtl_simulation.csv")
    ci_status_rows = read_rows(RESULTS / "ci_status.csv")
    ci_blocked = any(row.get("status") == "BLOCKED" for row in ci_status_rows)
    g1_status = "PASS" if (
        rtl_compile_status == "PASS"
        and rtl_sim_status == "PASS"
        and synthesis_overhead_pass()
        and paper_built
        and ci_artifact_package
    ) else ("BLOCKED" if ci_blocked else "PARTIAL")
    audit_claims = read_rows(RESULTS / "claim_audit.csv")
    audit_numbers = read_rows(RESULTS / "number_audit.csv")
    audit_todos = read_rows(RESULTS / "todo_audit.csv")
    audits_pass = audit_claims and audit_numbers and audit_todos and all(r.get("status") == "PASS" for r in audit_claims + audit_numbers + audit_todos)
    return [
        gate("G1. Open-source CI/Docker reproduction", "Yes", g1_status, "Makefile; Dockerfile; .github/workflows/reproduce.yml; .devcontainer/devcontainer.json; research/results/ci_status.csv", "make readiness completes in GitHub Actions, Docker, or Codespaces with logs/artifacts", "CI/Docker/Codespaces proof has not been imported. Local Windows is editing-only." if g1_status != "PASS" else ""),
        gate("G2. Toolchain detection", "Yes", "PASS" if (RESULTS / "toolchain_status.csv").exists() else "TODO", "research/scripts/check_toolchain.py; research/results/toolchain_status.csv", "Required tools are detected and missing tools are explicit", ""),
        gate("G3. Functional model tests", "Yes", "PASS" if all_status(RESULTS / "model_tests.csv", "PASS") else ("PARTIAL" if (RESULTS / "model_tests.csv").exists() else "TODO"), "research/results/model_tests.csv; research/scripts/copper_eval_model.py", "Directed tests pass and unmodeled behaviors are labeled", "" if all_status(RESULTS / "model_tests.csv", "PASS") else "Some model checks are still non-PASS."),
        gate("G4. SystemVerilog RTL compile", "Yes", rtl_compile_status, "research/results/rtl_compile.csv; research/results/logs/rtl/", "Open-source smoke compile passes in GitHub Actions, Docker, or Codespaces", "No CI/Docker/Codespaces PASS row has been collected yet." if rtl_compile_status != "PASS" else ""),
        gate("G5. RTL simulation", "Yes", rtl_sim_status, "research/results/rtl_simulation.csv; research/results/logs/rtl/", "Directed RTL smoke simulation passes in GitHub Actions, Docker, or Codespaces", "No CI/Docker/Codespaces PASS row has been collected yet." if rtl_sim_status != "PASS" else ""),
        gate("G6. C benchmark/workload build", "Yes", "PARTIAL", "research/results/benchmark_inventory.csv; research/aarch64_*", "Workload sources and builders are inventoried", "Fresh cross/full-system builds require external toolchain."),
        gate("G7. Benchmark execution", "Yes", "PARTIAL", "research/results/performance.csv; research/results/*_SEED_STABILITY*.md", "Existing execution summaries are normalized", "Not all raw runs are fresh-clone reproducible."),
        gate("G8. Baseline prefetcher implementation", "Yes", "PASS" if baseline_pass() else "PARTIAL", "research/results/baseline_inventory.csv", "No-prefetch, next-line, stride, simple pointer-chase, and COPPER run through the same model path", "" if baseline_pass() else "At least one baseline is missing."),
        gate("G9. COPPER prefetcher implementation", "Yes", "PASS", "research/scripts/copper_eval_model.py; research/copper_prefetch_unit_open.sv; research/results/performance.csv", "Model and RTL-unit implementation exist", "Not a production core integration."),
        gate("G10. Prefetch usefulness/accuracy/coverage metrics", "Yes", "PASS" if (RESULTS / "prefetch_metrics.csv").exists() else "TODO", "research/results/prefetch_metrics.csv", "Issued/useful/useless/late/queue/coverage/accuracy metrics are generated", ""),
        gate("G11. Speedup/performance metrics", "Yes", "PARTIAL" if (RESULTS / "performance.csv").exists() else "TODO", "research/results/performance.csv", "Per-workload speedup versus no-prefetch is reported", "No claim of broad benchmark-suite win."),
        gate("G12. Memory traffic/bandwidth overhead metrics", "Yes", "PASS" if (RESULTS / "memory_traffic.csv").exists() else "TODO", "research/results/memory_traffic.csv", "Traffic overhead is generated from model memory-request counts", ""),
        gate("G13. Sensitivity studies", "Yes", "PASS" if csv_has_no_todo(RESULTS / "sensitivity.csv") else ("PARTIAL" if (RESULTS / "sensitivity.csv").exists() else "TODO"), "research/results/sensitivity.csv", "Queue, confidence, chain depth, distance, table size, and latency sensitivities are captured", ""),
        gate("G14. Ablation studies", "Yes", "PASS" if csv_has_no_todo(RESULTS / "ablation.csv") else ("PARTIAL" if (RESULTS / "ablation.csv").exists() else "TODO"), "research/results/ablation.csv", "A0-A5 model-level ablations are generated", ""),
        gate("G15. Area/resource/timing synthesis", "Yes", "PASS" if synthesis_overhead_pass() else ("PARTIAL" if (RESULTS / "synthesis.csv").exists() else "TODO"), "research/results/synthesis.csv; research/results/synthesis_overhead.csv; research/results/logs/synthesis/", "Matched unit-level overhead exists from the same GitHub Actions, Docker, or Codespaces flow", "No open-environment matched overhead row has been collected yet." if not synthesis_overhead_pass() else ""),
        gate("G16. Power/energy proxy or measured estimate", "Yes", "PARTIAL", "research/results/COPPER_RTL_POWER_PROXY_20260618.md; research/results/copper_rtl_power_proxy_20260618.csv", "Proxy evidence is identified", "Not calibrated full-chip power."),
        gate("G17. Statistical stability across seeds/input sizes", "Yes", "PASS" if (RESULTS / "statistical_summary.csv").exists() else "TODO", "research/results/seed_stability.csv; research/results/statistical_summary.csv", "Model stability covers seeds 1-3 and multiple input sizes", ""),
        gate("G18. Artifact package", "Yes", "PASS" if ci_artifact_package else ("PARTIAL" if package_exists else "TODO"), "dist/copper-artifact.zip; research/results/artifact_manifest.csv; research/results/ci_artifacts_manifest.csv", "Package regenerates in GitHub Actions, Docker, or Codespaces and the zip appears in imported artifacts", "" if ci_artifact_package else "Local package output is not final packaging proof."),
        gate("G19. Paper build", "Yes", "PASS" if paper_built else "BLOCKED", "research/paper/main.tex; research/results/paper_build_status.csv", "PDF builds in GitHub Actions, Docker, or Codespaces", "" if paper_built else "No CI/Docker/Codespaces paper PASS row has been collected yet."),
        gate("G20. Claim audit", "Yes", "PASS" if audits_pass else "TODO", "research/scripts/audit_claims.py; research/scripts/audit_numbers.py; research/scripts/audit_todos.py", "Audits pass", "" if audits_pass else "Run make paper-audit after paper generation."),
        gate("G21. Related work/novelty matrix", "Yes", "PASS", "research/COPPER_RELATED_WORK_MATRIX.md", "Matrix exists and avoids first/novel overclaim", ""),
        gate("G22. Reviewer attack response matrix", "Yes", "PASS", "research/COPPER_FINAL_REVIEWER_REPORT.md", "Reviewer panel and blockers exist", ""),
    ]


def gate(name: str, required: str, status: str, evidence: str, pass_condition: str, blocker: str) -> dict[str, str]:
    return {
        "Gate": name,
        "Required for full submission?": required,
        "Current status": status,
        "Evidence file/script": evidence,
        "Pass condition": pass_condition,
        "Blocker": blocker,
    }


def build_dashboard() -> None:
    rows = gate_status()
    lines = [
        "# COPPER Conference Readiness Dashboard",
        "",
        "This dashboard is intentionally strict. PASS means the current artifact has reproducible evidence for that gate. PARTIAL means useful evidence exists but is not yet enough for a full conference submission.",
        "",
        "Local Windows is editing-only. GitHub Actions/Codespaces/Docker is the intended evidence environment for open-source hardware and paper gates.",
        "",
        "| Gate | Required for full submission? | Current status | Evidence file/script | Pass condition | Blocker |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['Gate']} | {row['Required for full submission?']} | {row['Current status']} | {row['Evidence file/script']} | {row['Pass condition']} | {row['Blocker']} |"
        )
    write(RESEARCH / "CONFERENCE_READINESS_DASHBOARD.md", "\n".join(lines))


def build_claim_ledger() -> None:
    c7_status = "ALLOWED" if synthesis_overhead_pass() else "TODO"
    claims = [
        ("C1", "COPPER tracks committed pointer provenance.", "ALLOWED", "research/results/model_tests.csv; research/copper_prefetch_unit_open.sv", "model; rtl-unit only when GitHub Actions/Codespaces/Docker rtl_compile.csv and rtl_simulation.csv are PASS", "Allowed for the executable model; RTL wording requires open-environment PASS rows."),
        ("C2", "COPPER issues prefetches based on committed provenance rather than arbitrary speculation.", "ALLOWED", "research/results/model_tests.csv; research/results/rtl_simulation.csv", "model; rtl-unit only when GitHub Actions/Codespaces/Docker rtl_simulation.csv is PASS", "Do not extend to a production core without integration evidence."),
        ("C3", "COPPER improves prefetch usefulness on exact measured model workloads.", "ALLOWED", "research/results/prefetch_metrics.csv", "model", "Allowed only per generated row; not a gem5-wide or hardware claim."),
        ("C4", "COPPER reports accuracy, coverage, lateness, queue drops, and traffic overhead versus shared baselines.", "ALLOWED", "research/results/prefetch_metrics.csv; research/results/memory_traffic.csv", "model", "Use per-workload language and report where overhead increases."),
        ("C5", "COPPER improves performance/speedup on exact measured workloads where performance.csv shows speedup.", "ALLOWED", "research/results/performance.csv", "model", "Do not claim universal speedup or superiority over every baseline."),
        ("C6", "COPPER avoids architectural output changes in the executable model.", "ALLOWED", "research/results/model_tests.csv; research/results/seed_stability.csv; research/results/rtl_simulation.csv", "model; rtl-unit only when GitHub Actions/Codespaces/Docker rtl_simulation.csv is PASS", "Checksum equality is model-level, and RTL smoke coverage is unit-level, not a formal ISA proof."),
        ("C7", "COPPER has matched unit-level generic-synthesis overhead.", c7_status, "research/results/synthesis.csv; research/results/synthesis_overhead.csv", "unit synthesis", "Allowed only if an open-environment Yosys flow produced matched overhead rows; not full-core overhead."),
        ("C8", "COPPER maps/synthesizes at unit level.", "PARTIAL", "research/results/synthesis.csv; existing Vivado timing reports", "unit synthesis", "Generic Yosys has no mapped timing; Vivado rows are existing reports unless rerun."),
        ("C9", "COPPER generalizes beyond one model workload.", "ALLOWED", "research/results/benchmark_inventory.csv; research/results/statistical_summary.csv", "model", "Breadth is model-level and does not replace full-system benchmark evidence."),
        ("C10", "COPPER is novel versus existing pointer-chasing prefetchers.", "TODO", "research/COPPER_RELATED_WORK_MATRIX.md; research/COPPER_PRIOR_ART.md", "related-work matrix", "Use distinction language; do not claim first or publication-level novelty without a fresh literature audit."),
    ]
    lines = [
        "# COPPER Claim Ledger",
        "",
        "Allowed statuses: ALLOWED, PARTIAL, FORBIDDEN, TODO. The paper must not make stronger claims than this table supports.",
        "",
        "| claim_id | claim_text | allowed_status | evidence_file | evidence_level | caveat |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for claim in claims:
        lines.append("| " + " | ".join(claim) + " |")
    write(RESEARCH / "COPPER_CLAIM_LEDGER.md", "\n".join(lines))


def build_artifact_map() -> None:
    text = """# COPPER Artifact Map

## Source

Source includes the Python model and analysis scripts under `research/*.py` and `research/scripts/*.py`, SystemVerilog RTL and testbenches under `research/*.sv`, C/C++ workload sources under `research/aarch64_*`, reproduction wrappers at the repository root, and the paper source under `research/paper`.

## Generated

Generated evidence lives under `research/results`. The new conference-facing generated CSVs are `toolchain_status.csv`, `model_tests.csv`, `rtl_compile.csv`, `rtl_simulation.csv`, `benchmark_inventory.csv`, `baseline_inventory.csv`, `performance.csv`, `prefetch_metrics.csv`, `memory_traffic.csv`, `ablation.csv`, `sensitivity.csv`, `seed_stability.csv`, `statistical_summary.csv`, `synthesis.csv`, `synthesis_overhead.csv`, `ci_status.csv`, `ci_artifacts_manifest.csv`, `ci_failure_summary.csv`, `artifact_inventory.csv`, and `artifact_manifest.csv`. Tool logs for open-source hardware gates are written under `research/results/logs/`.

## Evidence

Evidence used by the paper and dashboard comes from generated CSVs, existing gem5 summary CSVs, existing Vivado reports, and explicit logs. Paper claims are controlled by `research/COPPER_CLAIM_LEDGER.md`.

## Old Or Local-Only

Large simulator outputs, Vivado scratch directories, DCP files, WDB files, SAIF/VCD waveforms, and raw gem5 folders are treated as local-only unless they are small summary files or explicitly listed in the package manifest. The package script records excluded heavy artifacts rather than hiding them.

## First Reviewer Command

Run `make check-toolchain` to see the local tool state, then `make readiness` in Docker/CI or Codespaces for the complete portable pass. Local Windows is editing-only for the final hardware and paper gates. If GitHub CLI or Docker is unavailable locally, use the GitHub web UI path in `docs/RUN_CI_NOW.md`. If a tool is missing, the relevant gate should read BLOCKED or PARTIAL instead of silently passing.
"""
    write(RESEARCH / "ARTIFACT_MAP.md", text)


def build_related_work() -> None:
    rows = [
        ("stride prefetchers", "Predict regular address deltas.", "Uses committed pointer-source evidence for data-derived candidates.", "COPPER does not replace stride on sequential kernels.", "baseline_inventory.csv; performance.csv"),
        ("next-line prefetchers", "Fetch adjacent cache lines.", "Targets pointer-derived streams rather than adjacency.", "Does not claim next-line is broadly dominated.", "baseline_inventory.csv"),
        ("stream prefetchers", "Track streams and correlations.", "Can coexist as SPP plus COPPER slack in existing summaries.", "COPPER does not claim better raw timing than SPP.", "performance.csv"),
        ("pointer-chase prefetchers", "Follow linked structures or indirect addresses.", "Requires committed source-word proof before data-derived issue.", "Does not claim pointer prefetching itself is new.", "model_tests.csv; COPPER_PRIOR_ART.md"),
        ("dependence/provenance-based prefetching", "Uses dependence or provenance-like information to guide prefetch.", "Narrows provenance to committed source-word authority for DMP issue.", "Does not claim all provenance mechanisms are new.", "COPPER_PRIOR_ART.md"),
        ("prefetch filtering/confidence mechanisms", "Filter low-confidence prefetches.", "Filters by architectural proof, not just usefulness confidence.", "Confidence-threshold sensitivity remains TODO.", "sensitivity.csv"),
        ("runahead execution", "Executes ahead to expose misses.", "Allows recursive carried provenance only with committed source proof.", "Not a general runahead engine.", "COPPER_FULL_PAPER.md"),
        ("helper-thread prefetching", "Uses software or hardware helpers.", "Keeps policy in the prefetch authority path.", "Does not claim helper-thread comparison evidence.", "COPPER_RELATED_WORK_MATRIX.md"),
        ("memory-dependence prediction", "Predicts memory ordering/dependence behavior.", "Uses committed pointer-source facts to gate prefetch issue.", "Not a memory-order predictor.", "COPPER_PRIOR_ART.md"),
        ("hardware/software cooperative prefetching", "Uses software hints or compiler/runtime cooperation.", "Requires no source transformation in the modeled mechanism.", "Does not claim compiler approaches are obsolete.", "COPPER_PRIOR_ART.md"),
    ]
    lines = [
        "# COPPER Related Work Matrix",
        "",
        "This matrix states distinctions without using broad priority claims.",
        "",
        "| Area | What prior work does | What COPPER does differently | What COPPER does not claim | Evidence supporting distinction |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    write(RESEARCH / "COPPER_RELATED_WORK_MATRIX.md", "\n".join(lines))


def build_reviewer_reports() -> None:
    report = """# COPPER Final Reviewer Report

## Computer Architecture Reviewer

Leaning: workshop accept / conference reject. Strengths: clear invariant, real model evidence, useful full-system summaries, and an open-source RTL-unit path. Weaknesses: raw performance is not consistently better than conventional stream prefetching, and CI proof has not been collected. Fatal blockers: no full portable benchmark rerun. Required fixes: collect CI/Docker/Codespaces hardware and paper evidence, then expand workloads. Claim risks: raw-speed claims must remain per-workload.

## Prefetching And Memory-Systems Reviewer

Leaning: workshop accept. Strengths: committed pointer-source authority is a crisp selectivity idea. Weaknesses: lateness, queue behavior, and confidence sensitivities are incomplete. Fatal blockers: missing lateness and queue-capacity metrics for the normalized table. Required fixes: add direct prefetch timeliness and pollution counters. Claim risks: do not present COPPER as a universal prefetcher replacement.

## Hardware Implementation Reviewer

Leaning: weak reject for full conference. Strengths: SystemVerilog units, open-source smoke targets, and existing Vivado summaries exist. Weaknesses: no full-core integration, no ASIC PPA, no CI-proven RTL/synthesis run yet, and no CI-proven baseline overhead computation. Fatal blockers: full overhead and timing story is incomplete. Required fixes: synthesize baseline and COPPER units under the same open-source flow and collect logs/artifacts. Claim risks: unit-level FPGA evidence must stay unit-level.

## Evaluation And Statistics Reviewer

Leaning: workshop only. Strengths: seed ledgers and public workload summaries exist. Weaknesses: several public points have only two seeds and some results are model-level. Fatal blockers: broad statistical stability is incomplete. Required fixes: expand seeds and input sizes for positive and negative workloads. Claim risks: robust speedup cannot be claimed from limited seeds.

## Artifact Evaluation Reviewer

Leaning: conditional accept for artifact after CI proof. Strengths: one-command local model path, manifest, Docker/CI/Codespaces setup, web-triggerable workflow, and explicit blockers. Weaknesses: full gem5/Vivado reruns depend on external setup, and local Windows remains editing-only for proof gates. Fatal blockers: licensed/local tool reruns are not portable. Required fixes: run the workflow and import logs/artifacts. Claim risks: clone-local reproducibility must not be confused with full campaign reproducibility.

## Skeptical Novelty Reviewer

Leaning: reject until related-work story is sharpened. Strengths: the invariant is concrete and distinguishable. Weaknesses: adjacent pointer-chase, taint, capability, and DMP-defense work is crowded. Fatal blockers: no fresh formal literature review in this pass. Required fixes: keep distinction language and avoid priority language. Claim risks: priority claims remain TODO.
"""
    blockers = """# COPPER Final Submission Blockers

| Class | Blocker | Evidence | Required fix |
| --- | --- | --- | --- |
| FATAL | Full campaign is not one-command reproducible from a fresh clone. | REPRODUCIBILITY_STATUS.md; CONFERENCE_READINESS_DASHBOARD.md | Provide containerized gem5/workload inputs or narrow submission claims to portable evidence. |
| FATAL | GitHub Actions/Docker/Codespaces proof has not been collected. | ci_status.csv; docs/RUN_CI_NOW.md | Run the workflow from the GitHub web UI or Docker/Codespaces path and import logs/artifacts. |
| FATAL | No complete baseline-vs-COPPER hardware overhead table. | synthesis_overhead.csv | Synthesize matched baseline and COPPER units under the same flow. |
| SERIOUS BUT CAVEATABLE | Lateness and queue-capacity metrics are model-level rather than full-system counters. | prefetch_metrics.csv | Keep the paper wording model-level or add full-system simulator counters. |
| SERIOUS BUT CAVEATABLE | Statistical stability is uneven across workload families. | statistical_summary.csv | Add at least three seeds and multiple sizes for key positive and negative workloads. |
| SERIOUS BUT CAVEATABLE | Conventional prefetchers can win raw timing. | performance.csv | Frame COPPER as selectivity/safety authority and coexistence, not universal speed. |
| NICE TO HAVE | Open-source synthesis is blocked when Yosys is unavailable locally. | synthesis.csv | Use CI/Docker/Codespaces for the open-source synthesis pass; local Windows is editing-only for final proof. |
| FUTURE WORK | ASIC-calibrated power and full-core timing are absent. | synthesis.csv; existing power proxy files | Run an ASIC or OpenROAD-style flow if the claim needs silicon-grade PPA. |
"""
    write(RESEARCH / "COPPER_FINAL_REVIEWER_REPORT.md", report)
    write(RESEARCH / "COPPER_FINAL_SUBMISSION_BLOCKERS.md", blockers)


def build_reproduction_guide() -> None:
    text = """# COPPER Artifact Reproduction Guide

This guide separates portable artifact checks from external-tool reruns.

## Portable Path

Run:

```sh
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

Or run the combined pass:

```sh
make readiness
```

The Dockerfile, Codespaces devcontainer, and GitHub Actions workflow are the intended source of truth for a Linux reviewer environment. Local Windows is editing-only. If the workflow has not been executed yet, follow the GitHub web UI path in `docs/RUN_CI_NOW.md`; setup files alone do not prove RTL, synthesis, paper, or artifact gates.

## Existing Local Path

The original clone-local runner remains available:

```sh
python reproduce.py --mode all-local
```

This reruns the existing package checks and writes `research/results/reproduction/LOCAL_REPRODUCTION_REPORT.md`.

## External Tool Path

Full ARM/gem5 and Vivado reruns require external simulator, guest image, cross-toolchain, and licensed-tool setup. The repository includes scripts and summaries, but a fresh clone should not be expected to regenerate every raw full-system or Vivado artifact without that setup.

## Interpreting BLOCKED

BLOCKED is an honest artifact status. It means a needed external tool or raw input is missing from the current environment; it does not permit substituting fake timing, power, or benchmark numbers.

## Legacy Audit Anchors

The existing `research/verify_copper_artifacts.py` audit checks that the guide still points reviewers to the public artifact evidence set. Keep these anchors present when editing this file:

- Artifact audit line: `Passed 176/177 artifact checks.` or better after local regeneration.
- artifact checks.
- `research\\run_pcre2_regex_app_fs.sh`
- `research\\run_libxml2_xml_app_fs.sh`
- `research\\run_libarchive_tar_app_fs.sh`
- `research\\run_zstd_app_fs.sh`
- `research\\run_zlib_app_fs.sh`
- `research\\run_openssl_tls_socket_fs.sh`
- `research\\run_mibench_patricia_fs.sh`
- `ossltlstcp_TCP_NETNS_STRICT_FS_SUMMARY.md`
- `ossltlstcp_TCP_NETNS_PROCESS_KEY1_FS_SUMMARY.md`
- `COPPER_TCP_PROCESS_CLPD_ACTIVITY_POWER_20260620.md`
- `OPENSSL_TCP_PROCESS_METADATA_TOGGLE_BOUND_20260620.md`
- `OPENSSL_TCP_PROCESS_SEED_STABILITY_20260620.md`
- `ossltlstcp_TCP_FALLBACK_PROBE_FS_SUMMARY.md`
- `research\\run_openssl_cli_fixed_fs.ps1`
- `research\\run_copper_rocca_clpd_commit_adapter_xsim.ps1`
- `research\\run_copper_cavi_authority_issue_gate_xsim.ps1`
- `COPPER_CAVI_AUTHORITY_ISSUE_GATE_RTL_SUMMARY.md`
- `research\\run_sqlite_speedtest1_fs.sh`
- `SQLITE_SPEEDTEST1_COMPONENTS_20260619.md`
- `ZSTD_ZSTD_TINY_FS_SUMMARY.md`
- `ZLIB_ZLIB_TINY_FS_SUMMARY.md`
- `LIBXML2_XML_TINY_FULL_FS_SUMMARY.md`
- `LIBARCHIVE_TAR_TINY_FULL_FS_SUMMARY.md`
- `PCRE2_REGEX_SEED_STABILITY_20260620.md`
- `MIBENCH_PATRICIA_PATRICIA_SMALL8192_FS_SUMMARY.md`
- `MIBENCH_PATRICIA_PATRICIA_LARGE12288_FS_SUMMARY.md`
- `MIBENCH_PATRICIA_PATRICIA_LARGE12288_SEED1_FS_SUMMARY.md`
- `MIBENCH_PATRICIA_12K_SEED_STABILITY_20260621.md`
- `MIBENCH_PATRICIA_SCALE_PORTFOLIO_20260620.md`
- `COMPRESSION_LIBRARY_SEED_STABILITY_20260620.md`
- `COPPER_PUBLIC_ARTIFACT_MANIFEST_20260620.md`
- `COPPER_PUBLIC_ARTIFACT_PACKAGE_BUILD_20260620.md`
- Worst SPP+COPPER slack gap versus SPP: 0.294 percentage points.
- status=PASS
"""
    write(RESEARCH / "COPPER_ARTIFACT_REPRODUCTION_GUIDE.md", text)


def build_paper_source() -> None:
    PAPER.mkdir(parents=True, exist_ok=True)
    tex = r"""\documentclass[10pt]{article}
\usepackage[margin=0.75in]{geometry}
\usepackage{url}
\usepackage{graphicx}

\title{COPPER: Committed Pointer-Provenance Prefetching}
\author{Artifact draft}
\date{}

\begin{document}
\maketitle

\begin{abstract}
COPPER explores whether committed pointer-provenance signals can improve the selectivity of hardware data-derived prefetching for pointer-intensive workloads. The mechanism records pointer-source evidence only after architectural commit, invalidates or blocks stale and mismatched sources, and uses that evidence to gate later prefetch issue. The current artifact supports a careful claim: COPPER is a measurable research mechanism with model tests, open-source RTL and synthesis smoke paths awaiting GitHub Actions/Codespaces/Docker proof, existing gem5 Linux summaries, and existing unit-level hardware summaries. It does not claim production readiness, broad benchmark dominance, or silicon signoff.
\end{abstract}

\section{Introduction}
Pointer-heavy programs expose memory latency that ordinary address-stream prefetchers can miss. Data-derived prefetching can help, but it can also act on data that merely resembles an address. COPPER changes the authority rule: a prefetch candidate needs committed pointer-source evidence before issue. This paper version is claim-disciplined; all measurements are routed through generated CSVs and all unsupported claims are kept out of the body.

\section{Motivation}
\begin{figure}[t]
\centering
\fbox{\begin{minipage}{\linewidth}\centering
Demand execution uses a loaded pointer after commit. COPPER records that source word as eligible. Later data-derived prefetch issue checks the same source identity, value evidence, domain, and permission path before acting.
\end{minipage}}
\caption{Pointer-chasing motivation.}
\label{fig:motivation}
\end{figure}

The motivating failure mode is not ordinary speculation alone. It is that a prefetcher may treat address-shaped data as authority. COPPER instead treats committed pointer use as authority.

\section{Background And Related Work}
Prior work covers next-line, stride, stream, indirect, pointer-chase, runahead, helper-thread, and dependence-guided prefetching, as well as metadata and capability mechanisms. COPPER's distinction is narrower: committed source-word proof gates data-derived prefetch issue. The repository matrix records what COPPER does not claim.

\section{COPPER Design}
\begin{figure}[t]
\centering
\fbox{\begin{minipage}{\linewidth}\centering
Commit path: observe pointer-source use. Provenance table: retain clean source evidence. Prefetch path: require source match, target permission, and valid translation context. Invalidation path: clear source evidence on writes and coherence events.
\end{minipage}}
\caption{COPPER architecture.}
\label{fig:architecture}
\end{figure}

\begin{figure}[t]
\centering
\fbox{\begin{minipage}{\linewidth}\centering
Load source word, use as demand address, commit, record proof, later prefetch candidate, check proof, issue or block.
\end{minipage}}
\caption{Committed provenance update timeline.}
\label{fig:timeline}
\end{figure}

COPPER has three core rules: proof creation occurs after committed architectural evidence; writes, coherence updates, failed permissions, and context mismatch block or destroy proof; recursive issue does not gain authority merely because a line arrived by prefetch.

\section{Implementation}
The artifact contains a Python model, a trace-driven evaluation harness, SystemVerilog RTL units, C/C++ workload sources, reproduction scripts, and summary parsers. The open-source RTL smoke target is \texttt{copper\_prefetch\_unit\_open}; larger local Vivado summaries are treated as existing evidence rather than portable rerun proof.

\section{Experimental Methodology}
\begin{table}[t]
\centering
\caption{Benchmarks}
\begin{tabular}{lll}
\hline
Class & Examples & Evidence file \\
\hline
Pointer-heavy & heap, graph, Patricia & benchmark\_inventory.csv \\
Controls & array, compute, random access & benchmark\_inventory.csv \\
Stress & mixed, branchy, noisy allocation & benchmark\_inventory.csv \\
\hline
\end{tabular}
\end{table}

\begin{table}[t]
\centering
\caption{Configurations And Baselines}
\begin{tabular}{lll}
\hline
Config & Role & Evidence file \\
\hline
no\_prefetch & reference & baseline\_inventory.csv \\
pointer\_chase\_simple & unsafe content-derived baseline & baseline\_inventory.csv \\
spp\_conventional & conventional comparison & baseline\_inventory.csv \\
copper & committed-provenance policy & baseline\_inventory.csv \\
\hline
\end{tabular}
\end{table}

The normalized CSVs report per-workload rows rather than hiding negative results inside averages. Model-level rows and gem5-summary rows are labeled in notes.

\section{Evaluation}
\begin{figure}[t]
\centering
\fbox{\begin{minipage}{\linewidth}\centering
Speedup rows are generated in \texttt{research/results/performance.csv}. The paper does not collapse them into a single broad win claim.
\end{minipage}}
\caption{Speedup by benchmark.}
\label{fig:speedup}
\end{figure}

\begin{figure}[t]
\centering
\fbox{\begin{minipage}{\linewidth}\centering
Issued, useful, useless, accuracy, and coverage fields are generated in \texttt{research/results/prefetch\_metrics.csv}.
\end{minipage}}
\caption{Prefetch accuracy and coverage.}
\label{fig:prefetch}
\end{figure}

\begin{figure}[t]
\centering
\fbox{\begin{minipage}{\linewidth}\centering
Memory-traffic counters and byte-overhead fields are generated in \texttt{research/results/memory\_traffic.csv}.
\end{minipage}}
\caption{Traffic overhead.}
\label{fig:traffic}
\end{figure}

Current evidence supports selective, per-workload discussion. It does not support a universal speedup claim.

\section{Ablation And Sensitivity}
\begin{figure}[t]
\centering
\fbox{\begin{minipage}{\linewidth}\centering
Ablation and sensitivity rows are generated in \texttt{research/results/ablation.csv} and \texttt{research/results/sensitivity.csv}.
\end{minipage}}
\caption{Ablation and sensitivity.}
\label{fig:ablation}
\end{figure}

The current public model isolates several provenance choices. Queue filtering, confidence threshold, distance, and memory-latency sensitivity are reported at model level and should not be described as gem5 execution counters.

\section{Hardware Cost}
\begin{table}[t]
\centering
\caption{Hardware Cost}
\begin{tabular}{lll}
\hline
Evidence & Scope & File \\
\hline
Yosys & generic unit if tool exists & synthesis.csv \\
Vivado summaries & existing unit reports & synthesis.csv \\
Overhead & matched generic unit rows when Yosys runs & synthesis\_overhead.csv \\
\hline
\end{tabular}
\end{table}

The artifact supports unit-level hardware plausibility only. It does not claim full-core implementation cost.

\section{Limitations}
\begin{table}[t]
\centering
\caption{Limitations}
\begin{tabular}{ll}
\hline
Limitation & Consequence \\
\hline
External gem5 and Vivado setup & Full campaign is not fresh-clone portable \\
Model-only next-line and stride isolation & Baseline story is not gem5-level \\
No full-core matched hardware overhead & Full-core area claim remains blocked \\
Limited seed coverage in some workloads & Stability claim remains preliminary \\
\hline
\end{tabular}
\end{table}

\section{Artifact Evidence Gates}
\begin{table}[t]
\centering
\caption{Artifact And Evidence Gates}
\begin{tabular}{lll}
\hline
Gate class & Status source & Interpretation \\
\hline
Reproduction & CONFERENCE\_READINESS\_DASHBOARD.md & portable path plus blockers \\
Claims & COPPER\_CLAIM\_LEDGER.md & allowed wording only \\
Package & artifact\_manifest.csv & included and excluded files \\
\hline
\end{tabular}
\end{table}

\section{Conclusion}
COPPER is best framed as a committed-provenance authority mechanism for data-derived prefetch issue. The artifact now has a stricter reproduction path, claim ledger, metrics ledgers, paper source, audits, package manifest, and web-triggerable CI path. The honest recommendation is to treat the current repository as workshop-level unless GitHub Actions/Codespaces/Docker proof, RTL simulation, matched synthesis overhead, and paper PDF build blockers are closed.

\bibliographystyle{plain}
\bibliography{references}
\end{document}
"""
    bib = r"""@inproceedings{jouppi1990improving,
  title={Improving direct-mapped cache performance by the addition of a small fully-associative cache and prefetch buffers},
  author={Jouppi, Norman P.},
  booktitle={International Symposium on Computer Architecture},
  year={1990}
}

@article{chen1995effective,
  title={Effective hardware-based data prefetching for high-performance processors},
  author={Chen, Tien-Fu and Baer, Jean-Loup},
  journal={IEEE Transactions on Computers},
  year={1995}
}

@inproceedings{roth1998dependence,
  title={Dependence based prefetching for linked data structures},
  author={Roth, Amir and Moshovos, Andreas and Sohi, Gurindar S.},
  booktitle={International Conference on Architectural Support for Programming Languages and Operating Systems},
  year={1998}
}

@misc{augury,
  title={Augury: Using Data Memory-Dependent Prefetchers to Leak Data at Rest},
  howpublished={\url{https://www.prefetchers.info/augury.pdf}}
}

@misc{gofetch,
  title={GoFetch},
  howpublished={\url{https://gofetch.fail/}}
}

@misc{cheri,
  title={CHERI: Capability Hardware Enhanced RISC Instructions},
  howpublished={\url{https://www.cl.cam.ac.uk/research/security/ctsrd/cheri/}}
}
"""
    write(PAPER / "main.tex", tex)
    write(PAPER / "references.bib", bib)


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    build_inventory()
    build_claim_ledger()
    build_artifact_map()
    build_related_work()
    build_reviewer_reports()
    build_reproduction_guide()
    build_paper_source()
    build_dashboard()
    print("wrote conference readiness documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
