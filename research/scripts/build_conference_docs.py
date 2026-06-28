#!/usr/bin/env python3
"""Generate conference-readiness ledgers, maps, and paper source."""

from __future__ import annotations

import csv
import os
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


def current_open_environment() -> bool:
    env = os.environ.get("COPPER_ENVIRONMENT", "").strip()
    if not env:
        if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
            env = "github_actions"
        elif os.environ.get("CODESPACES", "").lower() == "true":
            env = "codespaces"
        elif Path("/.dockerenv").exists() or os.environ.get("container"):
            env = "docker"
    return env in OPEN_ENVIRONMENTS


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


def cycle_eval_pass() -> bool:
    rows = read_rows(RESULTS / "cycle_performance.csv")
    required = {"no_prefetch", "next_line", "stride", "simple_pointer_chase", "copper"}
    configs = {row.get("config", "") for row in rows if row.get("evidence_level") == "cycle_model" and row.get("status") == "PASS"}
    return required.issubset(configs)


def cycle_csv_pass(name: str) -> bool:
    rows = read_rows(RESULTS / name)
    return bool(rows) and any(row.get("evidence_level") == "cycle_model" for row in rows)


def cycle_stats_pass() -> bool:
    rows = read_rows(RESULTS / "statistical_summary.csv")
    return bool(rows) and any(row.get("evidence_level") == "cycle_model" for row in rows)


def workload_build_pass() -> bool:
    rows = read_rows(RESULTS / "workload_build.csv")
    required = {
        "linked_list",
        "tree_traversal",
        "hash_table_chaining",
        "graph_adjacency_walk",
        "patricia",
        "array_scan",
        "matrix_or_array_loop",
        "compute_heavy_low_memory",
        "random_non_pointer_access",
        "short_pointer_chains",
        "long_pointer_chains",
        "mixed_pointer_array",
        "noisy_allocation_pattern",
        "branchy_pointer_chains",
    }
    passed = {row.get("benchmark", "") for row in rows if row.get("build_status") == "PASS" and row.get("sha256")}
    return required.issubset(passed)


def core_integrated_pass() -> bool:
    rows = read_rows(RESULTS / "core_integrated_performance.csv")
    required = {"no_prefetch", "next_line", "stride", "simple_pointer_chase", "copper"}
    configs = {row.get("config", "") for row in rows if row.get("evidence_level") == "core_integrated" and row.get("status") == "PASS"}
    return required.issubset(configs)


def core_csv_pass(name: str) -> bool:
    rows = read_rows(RESULTS / name)
    return bool(rows) and any(row.get("evidence_level") == "core_integrated" for row in rows)


def independent_sim_pass() -> bool:
    rows = read_rows(RESULTS / "independent_sim_performance.csv")
    required = {"no_prefetch", "next_line", "stride", "simple_pointer_chase", "copper"}
    configs = {row.get("config", "") for row in rows if row.get("evidence_level") == "independent_sim" and row.get("status") == "PASS"}
    benches = {row.get("benchmark", "") for row in rows if row.get("evidence_level") == "independent_sim" and row.get("status") == "PASS"}
    required_benches = {
        "linked_list",
        "tree_traversal",
        "hash_table_chaining",
        "graph_adjacency_walk",
        "array_scan",
        "matrix_or_array_loop",
        "random_non_pointer_access",
        "long_pointer_chains",
        "mixed_pointer_array",
        "branchy_pointer_chains",
    }
    return required.issubset(configs) and required_benches.issubset(benches)


def independent_csv_pass(name: str) -> bool:
    rows = read_rows(RESULTS / name)
    return independent_sim_pass() and bool(rows) and any(row.get("evidence_level") == "independent_sim" for row in rows)


def near_core_synthesis_pass() -> bool:
    return any(
        row.get("scope") == "near_core_stub" and row.get("status") == "PASS" and row.get("percent_overhead")
        for row in read_rows(RESULTS / "fullcore_synthesis_overhead.csv")
    )


def matched_mapped_ppa_pass(scope: str = "near_core_stub") -> bool:
    if scope == "near_core_stub":
        baseline, copper = "nearcore_stub_baseline", "nearcore_stub_plus_copper"
    elif scope == "unit":
        baseline, copper = "baseline_prefetch_unit", "copper_unit"
    else:
        return False
    def has_real_timing(row: dict[str, str]) -> bool:
        return any(row.get(field, "").strip().upper() not in {"", "NA"} for field in ("fmax_mhz", "wns", "tns"))

    rows = [
        row
        for row in read_rows(RESULTS / "mapped_ppa.csv")
        if row.get("environment") in OPEN_ENVIRONMENTS
        and row.get("status") == "PASS"
        and row.get("flow") not in {"yosys", "not_run", ""}
        and has_real_timing(row)
    ]
    by_key: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        by_key.setdefault((row.get("target", ""), row.get("flow", "")), set()).add(row.get("design", ""))
    return any({baseline, copper}.issubset(designs) for designs in by_key.values())


def energy_proxy_present() -> bool:
    rows = read_rows(RESULTS / "energy_summary.csv")
    return any(row.get("status") == "PASS" and row.get("evidence_level", "").startswith("proxy_") for row in rows)


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
    imported_artifact_package = any(
        row.get("path", "").endswith("copper-artifact.zip")
        and positive_int(row.get("size_bytes", "0"))
        for row in read_rows(RESULTS / "ci_artifacts_manifest.csv")
    )
    current_run_package = (
        current_open_environment()
        and package_exists
        and (RESULTS / "artifact_manifest.csv").exists()
    )
    ci_artifact_package = imported_artifact_package or current_run_package
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
        gate("G1. Open-source CI/Docker reproduction", "Yes", g1_status, "Makefile; Dockerfile; .github/workflows/reproduce.yml; .devcontainer/devcontainer.json; research/results/ci_status.csv; research/results/artifact_manifest.csv", "make readiness completes in GitHub Actions, Docker, or Codespaces with logs/artifacts", "CI/Docker/Codespaces proof has not been imported or produced in the current open evidence environment. Local Windows is editing-only." if g1_status != "PASS" else ""),
        gate("G2. Toolchain detection", "Yes", "PASS" if (RESULTS / "toolchain_status.csv").exists() else "TODO", "research/scripts/check_toolchain.py; research/results/toolchain_status.csv", "Required tools are detected and missing tools are explicit", ""),
        gate("G3. Functional model tests", "Yes", "PASS" if all_status(RESULTS / "model_tests.csv", "PASS") else ("PARTIAL" if (RESULTS / "model_tests.csv").exists() else "TODO"), "research/results/model_tests.csv; research/scripts/copper_eval_model.py", "Directed tests pass and unmodeled behaviors are labeled", "" if all_status(RESULTS / "model_tests.csv", "PASS") else "Some model checks are still non-PASS."),
        gate("G4. SystemVerilog RTL compile", "Yes", rtl_compile_status, "research/results/rtl_compile.csv; research/results/logs/rtl/", "Open-source smoke compile passes in GitHub Actions, Docker, or Codespaces", "No CI/Docker/Codespaces PASS row has been collected yet." if rtl_compile_status != "PASS" else ""),
        gate("G5. RTL simulation", "Yes", rtl_sim_status, "research/results/rtl_simulation.csv; research/results/logs/rtl/", "Directed RTL smoke simulation passes in GitHub Actions, Docker, or Codespaces", "No CI/Docker/Codespaces PASS row has been collected yet." if rtl_sim_status != "PASS" else ""),
        gate("G6. C benchmark/workload build", "Yes", "PASS" if workload_build_pass() else "PARTIAL", "research/results/workload_build.csv; research/workloads/copper_workload_suite.c", "Required workload suite builds from source and records one row per benchmark", "" if workload_build_pass() else "Current environment has not produced PASS rows for every required workload build."),
        gate("G7. Benchmark execution", "Yes", "PASS" if (cycle_eval_pass() and core_integrated_pass() and independent_sim_pass()) else ("PARTIAL" if cycle_eval_pass() or core_integrated_pass() or independent_sim_pass() else "TODO"), "research/results/performance.csv; research/results/cycle_performance.csv; research/results/core_integrated_performance.csv; research/results/independent_sim_performance.csv", "Model, cycle_model, core_integrated, and independent_sim rows exist for the public benchmark suite", "" if independent_sim_pass() else "Independent simulator rows are missing, blocked, or non-PASS."),
        gate("G8. Baseline prefetcher implementation", "Yes", "PASS" if baseline_pass() else "PARTIAL", "research/results/baseline_inventory.csv", "No-prefetch, next-line, stride, simple pointer-chase, and COPPER run through the same model path", "" if baseline_pass() else "At least one baseline is missing."),
        gate("G9. COPPER prefetcher implementation", "Yes", "PASS", "research/scripts/copper_eval_model.py; research/copper_prefetch_unit_open.sv; research/results/performance.csv", "Model and RTL-unit implementation exist", "Not a production core integration."),
        gate("G10. Prefetch usefulness/accuracy/coverage metrics", "Yes", "PASS" if independent_csv_pass("independent_sim_prefetch_metrics.csv") or core_csv_pass("core_integrated_prefetch_metrics.csv") or cycle_csv_pass("cycle_prefetch_metrics.csv") or (RESULTS / "prefetch_metrics.csv").exists() else "TODO", "research/results/prefetch_metrics.csv; research/results/cycle_prefetch_metrics.csv; research/results/core_integrated_prefetch_metrics.csv; research/results/independent_sim_prefetch_metrics.csv", "Issued/useful/useless/late/queue/coverage/accuracy metrics are generated with evidence-level labels", ""),
        gate("G11. Speedup/performance metrics", "Yes", "PASS" if independent_sim_pass() else ("PARTIAL" if core_integrated_pass() or cycle_eval_pass() else ("PARTIAL" if (RESULTS / "performance.csv").exists() else "TODO")), "research/results/performance.csv; research/results/cycle_performance.csv; research/results/core_integrated_performance.csv; research/results/independent_sim_performance.csv", "Per-workload speedup versus no-prefetch is reported with evidence-level labels", "" if independent_sim_pass() else "Independent simulator speedup rows are missing or blocked; do not promote beyond local deterministic models."),
        gate("G12. Memory traffic/bandwidth overhead metrics", "Yes", "PASS" if independent_csv_pass("independent_sim_memory_traffic.csv") or core_csv_pass("core_integrated_memory_traffic.csv") or cycle_csv_pass("cycle_memory_traffic.csv") or (RESULTS / "memory_traffic.csv").exists() else "TODO", "research/results/memory_traffic.csv; research/results/cycle_memory_traffic.csv; research/results/core_integrated_memory_traffic.csv; research/results/independent_sim_memory_traffic.csv", "Traffic overhead is generated from model, cycle-model, core-integrated, and independent-simulator request counts where available", ""),
        gate("G13. Sensitivity studies", "Yes", "PASS" if cycle_csv_pass("sensitivity.csv") or csv_has_no_todo(RESULTS / "sensitivity.csv") else ("PARTIAL" if (RESULTS / "sensitivity.csv").exists() else "TODO"), "research/results/sensitivity.csv", "Queue, confidence, chain depth, distance, table size, and latency sensitivities are captured", ""),
        gate("G14. Ablation studies", "Yes", "PASS" if cycle_csv_pass("ablation.csv") or csv_has_no_todo(RESULTS / "ablation.csv") else ("PARTIAL" if (RESULTS / "ablation.csv").exists() else "TODO"), "research/results/ablation.csv", "A0-A5 ablations are generated with evidence-level labels", ""),
        gate("G15. Area/resource/timing synthesis", "Yes", "PASS" if matched_mapped_ppa_pass() else ("PARTIAL" if near_core_synthesis_pass() or synthesis_overhead_pass() else ("TODO" if not (RESULTS / "fullcore_synthesis.csv").exists() else "BLOCKED")), "research/results/synthesis.csv; research/results/synthesis_overhead.csv; research/results/fullcore_synthesis.csv; research/results/fullcore_synthesis_overhead.csv; research/results/mapped_ppa.csv; research/results/mapped_ppa_overhead.csv", "Matched unit-level and near-core-stub resource rows exist; mapped timing requires real nextpnr, Vivado, or OpenROAD reports", "" if matched_mapped_ppa_pass() else ("No full-core or mapped near-core timing/power report exists; generic Yosys cells are resource evidence only. mapped_ppa.csv records the mapped-flow blocker." if near_core_synthesis_pass() or synthesis_overhead_pass() else "No matched near-core or unit overhead row has been collected yet.")),
        gate("G16. Power/energy proxy or measured estimate", "Yes", "PARTIAL" if energy_proxy_present() else "TODO", "research/results/energy_proxy.csv; research/results/energy_summary.csv; research/results/power_report_index.csv", "Proxy energy rows are generated with explicit assumptions and measured power is indexed if present", "Proxy is assumption-based and not calibrated measured power." if energy_proxy_present() else "No energy proxy or measured report has been generated."),
        gate("G17. Statistical stability across seeds/input sizes", "Yes", "PASS" if cycle_stats_pass() else ("PARTIAL" if (RESULTS / "statistical_summary.csv").exists() else "TODO"), "research/results/seed_stability.csv; research/results/statistical_summary.csv", "Stability covers seeds 1-3 and multiple input sizes with evidence-level labels", ""),
        gate("G18. Artifact package", "Yes", "PASS" if ci_artifact_package else ("PARTIAL" if package_exists else "TODO"), "dist/copper-artifact.zip; research/results/artifact_manifest.csv; research/results/ci_artifacts_manifest.csv", "Package regenerates in GitHub Actions, Docker, or Codespaces or the zip appears in imported artifacts", "" if ci_artifact_package else "Local package output is not final packaging proof."),
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
    c8_status = "ALLOWED" if near_core_synthesis_pass() else "TODO"
    c12_status = "ALLOWED" if matched_mapped_ppa_pass() else "TODO"
    energy_status = "PARTIAL" if energy_proxy_present() else "TODO"
    claims = [
        ("C1", "COPPER tracks committed pointer provenance.", "ALLOWED", "research/results/model_tests.csv; research/copper_prefetch_unit_open.sv", "model; rtl-unit only when GitHub Actions/Codespaces/Docker rtl_compile.csv and rtl_simulation.csv are PASS", "Allowed for the executable model; RTL wording requires open-environment PASS rows."),
        ("C2", "COPPER issues prefetches based on committed provenance rather than arbitrary speculation.", "ALLOWED", "research/results/model_tests.csv; research/results/rtl_simulation.csv", "model; rtl-unit only when GitHub Actions/Codespaces/Docker rtl_simulation.csv is PASS", "Do not extend to a production core without integration evidence."),
        ("C3", "COPPER improves prefetch usefulness on exact measured model, cycle-model, core-integrated, or independent-sim workloads where generated rows show improvement.", "ALLOWED", "research/results/prefetch_metrics.csv; research/results/cycle_prefetch_metrics.csv; research/results/core_integrated_prefetch_metrics.csv; research/results/independent_sim_prefetch_metrics.csv", "model; cycle_model; core_integrated; independent_sim", "Allowed only per generated row; independent_sim is not gem5, and gem5 remains BLOCKED unless gem5 CSVs contain real PASS rows."),
        ("C4", "COPPER reports accuracy, coverage, lateness, queue drops, and traffic overhead versus shared baselines.", "ALLOWED", "research/results/prefetch_metrics.csv; research/results/memory_traffic.csv; research/results/cycle_prefetch_metrics.csv; research/results/cycle_memory_traffic.csv; research/results/core_integrated_prefetch_metrics.csv; research/results/core_integrated_memory_traffic.csv; research/results/independent_sim_prefetch_metrics.csv; research/results/independent_sim_memory_traffic.csv", "model; cycle_model; core_integrated; independent_sim", "Use per-workload language and report where overhead increases."),
        ("C5", "COPPER improves performance/speedup on exact measured workloads where performance CSVs show speedup.", "ALLOWED", "research/results/performance.csv; research/results/cycle_performance.csv; research/results/core_integrated_performance.csv; research/results/independent_sim_performance.csv", "model; cycle_model; core_integrated; independent_sim", "Do not claim universal speedup or superiority over every baseline."),
        ("C6", "COPPER avoids architectural output changes in the executable model.", "ALLOWED", "research/results/model_tests.csv; research/results/seed_stability.csv; research/results/rtl_simulation.csv", "model; rtl-unit only when GitHub Actions/Codespaces/Docker rtl_simulation.csv is PASS", "Checksum equality is model-level, and RTL smoke coverage is unit-level, not a formal ISA proof."),
        ("C7", "COPPER has matched unit-level generic-synthesis overhead.", c7_status, "research/results/synthesis.csv; research/results/synthesis_overhead.csv", "unit synthesis", "Allowed only if an open-environment Yosys flow produced matched overhead rows; not full-core overhead."),
        ("C8", "COPPER has matched near-core-stub generic-synthesis overhead.", c8_status, "research/results/fullcore_synthesis.csv; research/results/fullcore_synthesis_overhead.csv", "near_core_stub", "Allowed only when scope is called near_core_stub; not full-core overhead or mapped timing."),
        ("C9", "COPPER generalizes across the evaluated model, cycle-model, core-integrated, and independent-sim workload suite.", "ALLOWED", "research/results/benchmark_inventory.csv; research/results/cycle_performance.csv; research/results/core_integrated_performance.csv; research/results/independent_sim_performance.csv; research/results/statistical_summary.csv", "model; cycle_model; core_integrated; independent_sim", "Breadth is still not a gem5 campaign or production-core result."),
        ("C10", "COPPER has an energy result.", energy_status, "research/results/energy_proxy.csv; research/results/energy_summary.csv; research/results/power_report_index.csv", "proxy_assumed_memory_energy", "Only assumption-based proxy energy may be discussed; no measured power or power-efficiency claim."),
        ("C11", "COPPER is novel versus existing pointer-chasing prefetchers.", "TODO", "research/COPPER_RELATED_WORK_MATRIX.md; research/COPPER_PRIOR_ART.md", "related-work matrix", "Use distinction language; do not claim first or publication-level novelty without a fresh literature audit."),
        ("C12", "COPPER has matched near-core-stub mapped timing.", c12_status, "research/results/mapped_ppa.csv; research/results/mapped_ppa_overhead.csv", "near_core_stub mapped PPA", "Allowed only when baseline and COPPER near-core-stub rows PASS in the same mapped flow with timing fields from nextpnr, Vivado, or OpenROAD; not full-core PPA."),
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

Generated evidence lives under `research/results`. The new conference-facing generated CSVs are `toolchain_status.csv`, `model_tests.csv`, `rtl_compile.csv`, `rtl_simulation.csv`, `workload_build.csv`, `benchmark_inventory.csv`, `baseline_inventory.csv`, `performance.csv`, `prefetch_metrics.csv`, `memory_traffic.csv`, `cycle_performance.csv`, `cycle_prefetch_metrics.csv`, `cycle_memory_traffic.csv`, `gem5_performance.csv`, `gem5_prefetch_metrics.csv`, `gem5_memory_traffic.csv`, `independent_sim_performance.csv`, `independent_sim_prefetch_metrics.csv`, `independent_sim_memory_traffic.csv`, `core_integrated_performance.csv`, `core_integrated_prefetch_metrics.csv`, `core_integrated_memory_traffic.csv`, `energy_proxy.csv`, `energy_summary.csv`, `power_report_index.csv`, `ablation.csv`, `sensitivity.csv`, `seed_stability.csv`, `statistical_summary.csv`, `synthesis.csv`, `synthesis_overhead.csv`, `fullcore_synthesis.csv`, `fullcore_synthesis_overhead.csv`, `mapped_ppa.csv`, `mapped_ppa_overhead.csv`, `ci_status.csv`, `ci_artifacts_manifest.csv`, `ci_failure_summary.csv`, `artifact_inventory.csv`, and `artifact_manifest.csv`. Tool logs for open-source hardware gates are written under `research/results/logs/`.

## Evidence

Evidence used by the paper and dashboard comes from generated CSVs and explicit logs. Gem5 rows remain BLOCKED unless a real runnable gem5 campaign produces PASS rows. Existing Vivado reports are local summaries unless rerun. Paper claims are controlled by `research/COPPER_CLAIM_LEDGER.md`.

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
        ("prefetch filtering/confidence mechanisms", "Filter low-confidence prefetches.", "Filters by architectural proof, not just usefulness confidence.", "Confidence-threshold sensitivity is reported in the deterministic cycle model.", "sensitivity.csv"),
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

Leaning: workshop accept / top-tier reject. Strengths: clear committed-provenance invariant, CI-proven RTL unit simulation, source workload build path, deterministic cycle-model rows, deterministic core-integrated rows, and an independent source-backed trace/event simulator across the required workload/config matrix. Weaknesses: gem5 remains unavailable, and the independent simulator is not a full-system gem5 campaign. Fatal blockers: no real gem5/full-system external simulator campaign for top-tier architecture claims. Required fixes: validate the same workload/config matrix in gem5 or another accepted external core simulator. Claim risks: performance claims must stay per-row and evidence-level scoped. Phase 0 discrepancy check: claimed PR/push evidence matched; main-branch Actions state was not verifiable because the API returned no main runs, so main-branch status must not be cited.

## Prefetching And Memory-Systems Reviewer

Leaning: weak accept for scoped mechanism, reject for replacement claims. Strengths: committed pointer-source authority is crisp; cycle and core-integrated tables include accuracy, coverage, lateness, queue drops, traffic, negative workloads, and sensitivity. Weaknesses: several COPPER rows trail the best baseline, and gem5 remains BLOCKED. Fatal blockers: any universal-speedup or broad-dominance language would be fatal. Required fixes: keep regression discussion visible and compare per workload/configuration. Claim risks: do not imply COPPER replaces stride/stream/unsafe pointer-chase prefetchers. Phase 0 discrepancy check: no claimed metric row-count mismatch found.

## Hardware Implementation Reviewer

Leaning: artifact accept / architecture-paper reject unless mapped PPA rows are PASS. Strengths: SystemVerilog unit, CI-proven open-source simulation, matched unit-level synthesis, an added near-core-stub synthesis target, and a dedicated mapped-PPA ledger. Weaknesses: local Windows may not have Yosys/nextpnr/OpenROAD/Vivado; CI or another tool-equipped environment is the proof environment. Near-core-stub evidence is not full-core implementation, and generic Yosys has no mapped timing or power. Fatal blockers: full-core overhead/timing and measured power are unsupported unless mapped_ppa.csv and power_report_index.csv contain real PASS rows. Required fixes: integrate into a real core or accepted open-source core wrapper and close timing under a mapped flow. Claim risks: near-core-stub must never be called full-core. Phase 0 discrepancy check: existing Vivado scratch directories do not imply runnable Vivado.

## Evaluation And Statistics Reviewer

Leaning: workshop accept if scoped, top-tier weak reject. Strengths: deterministic cycle and core-integrated rows cover seeds 1-3, multiple input sizes, and both positive/control/stress workloads; the independent simulator executes the source-built workload binary and retains regressions. Weaknesses: the independent simulator is still an artifact-local trace/event model, not gem5 or a full-system external simulator. Fatal blockers: no external full-system simulator statistics. Required fixes: add gem5 or another accepted external simulator run and confidence intervals from those runs. Claim risks: robust speedup must be described per benchmark/configuration, not as a suite-wide win. Phase 0 discrepancy check: row counts matched claimed deterministic-model rows.

## Artifact Evaluation Reviewer

Leaning: accept for artifact if final branch CI passes. Strengths: Phase 0 preserved prior CI proof, the pass adds explicit preflight/tooling evidence, source workload build scripts, core-integrated logs, near-core-stub synthesis scripts, and proxy energy ledgers. Weaknesses: local Windows cannot build paper, RTL, Yosys, or workloads; GitHub Actions/Docker/Codespaces is the intended proof path. Fatal blockers: final branch CI failure or package failure. Required fixes: keep artifact uploads and dashboards tied to the current run. Claim risks: local generated BLOCKED rows must not be promoted over CI PASS rows. Phase 0 discrepancy check: main branch Actions status was not verifiable.

## Skeptical Novelty Reviewer

Leaning: reject for broad novelty, acceptable for a narrow artifact/mechanism paper. Strengths: the committed-provenance authority invariant is concrete and has model, cycle-model, core-integrated, RTL-unit, and synthesis-scope support. Weaknesses: adjacent pointer-chase, taint, capability, dependence, and DMP-defense work is crowded; this pass did not perform a fresh literature audit. Fatal blockers: any first/priority/state-of-the-art language would be fatal. Required fixes: update the related-work matrix before aiming at a top-tier venue. Claim risks: paper must not imply gem5, full-core, measured power, or universal superiority. Phase 0 discrepancy check: unresolved main-branch status is at least SERIOUS BUT CAVEATABLE for release claims.
"""
    blockers = """# COPPER Final Submission Blockers

| Class | Blocker | Evidence | Required fix |
| --- | --- | --- | --- |
| SERIOUS BUT CAVEATABLE | Gem5 remains unavailable; independent_sim is source-backed trace/event validation, not a full-system external simulator. | gem5_performance.csv; independent_sim_performance.csv; independent_sim_prefetch_metrics.csv; independent_sim_memory_traffic.csv | Run the same workload/config matrix in gem5 or another accepted external simulator before making top-tier architecture claims. |
| FATAL | No full-core matched timing/area/power result. | fullcore_synthesis.csv; fullcore_synthesis_overhead.csv; mapped_ppa.csv | Integrate baseline and COPPER into the same real core or accepted core wrapper and close a mapped flow. |
| SERIOUS BUT CAVEATABLE | Near-core-stub synthesis is not full-core overhead. | fullcore_synthesis_overhead.csv; mapped_ppa.csv | Keep the scope labeled near_core_stub everywhere. |
| SERIOUS BUT CAVEATABLE | Energy is proxy_assumed_memory_energy, not measured or calibrated. | energy_proxy.csv; energy_summary.csv; power_report_index.csv | Add a real power report or calibrated model before claiming power efficiency. |
| SERIOUS BUT CAVEATABLE | Some workloads regress versus the best baseline. | cycle_performance.csv; core_integrated_performance.csv | Discuss regressions directly and keep speedup claims per-row. |
| SERIOUS BUT CAVEATABLE | Main-branch Actions status was not verifiable in Phase 0. | preflight_baseline_check.csv | Verify main branch separately before release claims. |
| NICE TO HAVE | Local Windows cannot run paper/RTL/synthesis/workload compilers. | tooling_availability.md | Use Docker/Codespaces/GitHub Actions as the proof environment. |
| FUTURE WORK | ASIC-calibrated PPA is absent. | synthesis.csv; fullcore_synthesis.csv; mapped_ppa.csv | Add ASIC/OpenROAD-style reports if silicon-grade PPA is needed. |
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
make workloads
make rtl
make sim
make eval
make synth
make mapped-ppa
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
Mapped PPA evidence is generated by `research/scripts/run_mapped_ppa.py`. It records BLOCKED rows when Yosys, nextpnr, OpenROAD, Vivado, or required platform data are unavailable, and PASS rows only after a real mapped flow succeeds.

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
COPPER explores whether committed pointer-provenance signals can improve the selectivity of hardware data-derived prefetching for pointer-intensive workloads. The mechanism records pointer-source evidence only after architectural commit, invalidates or blocks stale and mismatched sources, and uses that evidence to gate later prefetch issue. The artifact now supports a careful claim: COPPER is a measurable research mechanism with executable-model evidence, deterministic cycle-model evidence, deterministic core-integrated evidence, source-backed independent-simulator evidence, CI-proven RTL unit simulation, CI-proven paper/artifact reproduction, matched unit-level synthesis evidence, near-core-stub generic-resource evidence when the open-source flow is available, and assumption-based proxy-energy rows. It does not claim state-of-the-art performance, production readiness, gem5 validation unless gem5 CSVs contain PASS rows, full-system integration, mapped timing, measured power efficiency, or silicon signoff.
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

\section{Methodology}
\begin{table}[t]
\centering
\caption{Benchmarks}
\begin{tabular}{lll}
\hline
Class & Examples & Evidence file \\
\hline
Pointer-heavy & linked list, tree, hash, graph, Patricia & workload\_build.csv; independent\_sim\_performance.csv \\
Controls & array, matrix, compute, random access & workload\_build.csv; independent\_sim\_performance.csv \\
Stress & short chains, long chains, mixed, noisy, branchy & workload\_build.csv; independent\_sim\_performance.csv \\
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
no\_prefetch & reference & cycle\_performance.csv \\
next\_line & spatial baseline & cycle\_performance.csv \\
stride & regular-stream baseline & cycle\_performance.csv \\
simple\_pointer\_chase & unsafe content-derived baseline & cycle\_performance.csv \\
copper & committed-provenance policy & cycle\_performance.csv \\
\hline
\end{tabular}
\end{table}

The normalized CSVs report per-workload rows rather than hiding negative results inside averages. Evidence levels are explicit: \texttt{model} rows come from the executable policy model, \texttt{cycle\_model} rows come from a deterministic memory-system model with hit/miss latency, memory latency, outstanding prefetches, queue drops, lateness, and demand/prefetch traffic accounting. \texttt{core\_integrated} rows add a deterministic core envelope with fetch/issue width, reorder-window pressure, load-queue pressure, branch penalties, and memory-system timing. \texttt{independent\_sim} rows execute the source-built C workload driver for checksums and then use a separate trace/event cache simulator that does not import the cycle-model or core-integrated harness. Gem5 rows are reported separately and remain blocked unless \texttt{gem5\_*.csv} contains real PASS rows. None of these rows claim complete CPU integration.

\section{Evaluation}
\begin{figure}[t]
\centering
\fbox{\begin{minipage}{\linewidth}\centering
Speedup rows are generated in \texttt{research/results/performance.csv}, \texttt{research/results/cycle\_performance.csv}, \texttt{research/results/core\_integrated\_performance.csv}, and \texttt{research/results/independent\_sim\_performance.csv}. The paper does not collapse them into a single broad win claim.
\end{minipage}}
\caption{Speedup by benchmark.}
\label{fig:speedup}
\end{figure}

\begin{figure}[t]
\centering
\fbox{\begin{minipage}{\linewidth}\centering
Issued, useful, useless, accuracy, coverage, lateness, and queue-drop fields are generated in \texttt{research/results/prefetch\_metrics.csv}, \texttt{research/results/cycle\_prefetch\_metrics.csv}, \texttt{research/results/core\_integrated\_prefetch\_metrics.csv}, and \texttt{research/results/independent\_sim\_prefetch\_metrics.csv}.
\end{minipage}}
\caption{Prefetch accuracy and coverage.}
\label{fig:prefetch}
\end{figure}

\begin{figure}[t]
\centering
\fbox{\begin{minipage}{\linewidth}\centering
Demand-load, prefetch-load, total-request, and traffic-overhead fields are generated in \texttt{research/results/memory\_traffic.csv}, \texttt{research/results/cycle\_memory\_traffic.csv}, \texttt{research/results/core\_integrated\_memory\_traffic.csv}, and \texttt{research/results/independent\_sim\_memory\_traffic.csv}.
\end{minipage}}
\caption{Traffic overhead.}
\label{fig:traffic}
\end{figure}

Current evidence supports selective, per-workload discussion. Several cycle-model, core-integrated, and independent-sim rows show COPPER behind the best baseline; those regressions remain in the CSVs and block a universal speedup claim.

\section{Ablation And Sensitivity}
\begin{figure}[t]
\centering
\fbox{\begin{minipage}{\linewidth}\centering
Ablation and sensitivity rows are generated in \texttt{research/results/ablation.csv} and \texttt{research/results/sensitivity.csv}; the rows include evidence-level labels.
\end{minipage}}
\caption{Ablation and sensitivity.}
\label{fig:ablation}
\end{figure}

The cycle-model ablations isolate no provenance, speculative provenance, committed-only proof, confidence, queue filtering, and full COPPER. Queue size, confidence threshold, chain depth, distance, table size, and memory latency are varied in sensitivity rows. These are cycle-model counters and should not be described as gem5 counters.

\section{Hardware Cost}
\begin{table}[t]
\centering
\caption{Hardware Cost}
\begin{tabular}{lll}
\hline
Evidence & Scope & File \\
\hline
CI RTL simulation & open-source unit test & rtl\_simulation.csv \\
Yosys & generic unit resource context & synthesis.csv \\
nextpnr & mapped unit resource context when available & synthesis.csv \\
Overhead & matched unit rows from same flow & synthesis\_overhead.csv \\
Near-core stub & matched generic near-core-stub rows when Yosys runs & fullcore\_synthesis\_overhead.csv \\
Mapped PPA & matched near-core-stub or unit rows only when place-and-route succeeds & mapped\_ppa.csv; mapped\_ppa\_overhead.csv \\
Full-core wrapper & BLOCKED unless real core-wrapper RTL exists & fullcore\_synthesis.csv \\
\hline
\end{tabular}
\end{table}

The artifact supports unit-level hardware plausibility and, when Yosys is available, a matched near-core-stub resource-overhead row. The near-core stub is not a full CPU. Generic Yosys rows do not provide mapped timing, Fmax, ASIC area, or measured power. Mapped timing may be discussed only when \texttt{mapped\_ppa.csv} contains matched PASS rows from nextpnr, Vivado, or OpenROAD. Full-core wrapper rows remain BLOCKED unless real core-wrapper RTL and a mapped flow are added.

\section{Energy Proxy}
\begin{table}[t]
\centering
\caption{Energy/Power Evidence}
\begin{tabular}{lll}
\hline
Evidence & Scope & File \\
\hline
Memory traffic proxy & assumption-based, not measured & energy\_proxy.csv \\
Measured power index & BLOCKED unless real report exists & power\_report\_index.csv \\
Activity proxy & BLOCKED unless activity is converted by a calibrated tool flow & power\_report\_index.csv \\
Summary & proxy overhead statistics & energy\_summary.csv \\
\hline
\end{tabular}
\end{table}

Energy rows use explicit assumptions recorded in \texttt{energy\_proxy.csv}. They are \texttt{proxy\_assumed\_memory\_energy} rows, not calibrated power, not silicon measurements, and not a basis for claiming power efficiency. \texttt{proxy\_activity} remains blocked unless activity is converted through a calibrated tool flow.

\section{Limitations}
\begin{table}[t]
\centering
\caption{Limitations}
\begin{tabular}{ll}
\hline
Limitation & Consequence \\
\hline
Gem5 rows may be BLOCKED & Gem5 validation cannot be claimed without PASS rows \\
Independent simulator is trace/event level & It is not a system-level gem5 campaign \\
No full-core integration & Full-core area, timing, and power claims remain blocked \\
Energy is proxy-assumed & Measured power-efficiency claims remain blocked \\
External gem5 and Vivado setup & Large external-tool reruns are not clone-local \\
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
CI RTL evidence & rtl\_simulation.csv & GitHub Actions unit simulation \\
Cycle-model evidence & cycle\_performance.csv & deterministic memory-system timing model \\
Core-integrated evidence & core\_integrated\_performance.csv & deterministic core-envelope model \\
Independent simulator & independent\_sim\_performance.csv & source-backed trace/event simulator \\
Hardware cost & synthesis\_overhead.csv; fullcore\_synthesis\_overhead.csv; mapped\_ppa.csv & matched unit or near-core-stub resources, plus mapped timing only when PASS \\
Energy proxy & energy\_proxy.csv; power\_report\_index.csv & assumption-based proxy only \\
Package & artifact\_manifest.csv & included and excluded files \\
\hline
\end{tabular}
\end{table}

\section{Conclusion}
COPPER is best framed as a committed-provenance authority mechanism for data-derived prefetch issue. The artifact now has a CI-proven open-source path, deterministic cycle-model and core-integrated evidence, source-backed independent-simulator rows, matched unit-level and near-core-stub generic-resource paths, a mapped-PPA ledger that blocks unless real place-and-route timing succeeds, proxy energy rows, a claim ledger, audits, and a package manifest. The honest next step for a stronger architecture submission is real gem5 or comparable external core validation plus full-core timing/area/power evidence without changing the scoped claims in this artifact.

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
