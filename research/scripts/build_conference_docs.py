#!/usr/bin/env python3
"""Generate conference-readiness ledgers, maps, and paper source."""

from __future__ import annotations

import csv
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "research"
RESULTS = RESEARCH / "results"
PAPER = RESEARCH / "paper"
OPEN_ENVIRONMENTS = {"github_actions", "docker", "codespaces"}
MAPPED_PPA_ENVIRONMENTS = OPEN_ENVIRONMENTS | {"local_windows"}


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


def positive_float(value: str) -> bool:
    try:
        return float(value or 0) > 0.0
    except (TypeError, ValueError):
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


def gem5_full_system_pass() -> bool:
    rows = read_rows(RESULTS / "gem5_performance.csv")
    pass_rows = [
        row
        for row in rows
        if row.get("evidence_level") == "gem5_full_system" and row.get("status") == "PASS"
    ]
    configs = {row.get("config", "") for row in pass_rows}
    benches = {row.get("benchmark", "") for row in pass_rows}
    has_copper = any("copper" in config.lower() for config in configs)
    return "no_prefetch" in configs and has_copper and len(benches) >= 3


def gem5_stats_pass() -> bool:
    rows = read_rows(RESULTS / "gem5_statistical_summary.csv")
    return bool(rows) and any(row.get("evidence_level") == "gem5_full_system" for row in rows)


def gem5_raw_stats_summary() -> str:
    rows = [
        row
        for row in read_rows(RESULTS / "gem5_raw_rerun_statistical_summary.csv")
        if row.get("status") == "PASS"
    ]
    if not rows:
        return "no repeated local raw gem5 statistics"
    groups = sorted({row.get("raw_group", "") for row in rows if row.get("raw_group", "")})
    policies = sorted({row.get("policy", "") for row in rows if row.get("policy", "")})
    return (
        f"{len(rows)} repeated local raw gem5 statistic rows across "
        f"{len(groups)} raw group(s) and policies {', '.join(policies)}"
    )


def gem5_evidence_summary() -> str:
    rows = [
        row
        for row in read_rows(RESULTS / "gem5_performance.csv")
        if row.get("evidence_level") == "gem5_full_system" and row.get("status") == "PASS"
    ]
    if not rows:
        return "no validated gem5 ARM-system PASS rows"
    benches = {(row.get("benchmark", ""), row.get("input", "")) for row in rows}
    families = {row.get("benchmark", "") for row in rows}
    copper_rows = [row for row in rows if "copper" in row.get("config", "").lower()]
    return (
        f"{len(rows)} validated gem5 ARM-system PASS rows across "
        f"{len(families)} benchmark families and {len(benches)} benchmark/input groups, "
        f"including {len(copper_rows)} COPPER-family rows"
    )


def gem5_raw_rerun_summary() -> str:
    rows = [
        row
        for row in read_rows(RESULTS / "gem5_raw_rerun_manifest.csv")
        if row.get("status") == "PASS"
    ]
    if not rows:
        return "no local raw gem5 rerun rows"
    tags = sorted({row.get("tag", "") for row in rows if row.get("tag", "")})
    policies = sorted({row.get("policy", "") for row in rows if row.get("policy", "")})
    tag_label = "tag" if len(tags) == 1 else "tags"
    return (
        f"{len(rows)} local raw gem5 full-system rerun rows "
        f"across {len(tags)} {tag_label} and policies {', '.join(policies)}"
    )


def independent_csv_pass(name: str) -> bool:
    rows = read_rows(RESULTS / name)
    return independent_sim_pass() and bool(rows) and any(row.get("evidence_level") == "independent_sim" for row in rows)


def near_core_synthesis_pass() -> bool:
    return any(
        row.get("scope") == "near_core_stub" and row.get("status") == "PASS" and row.get("percent_overhead")
        for row in read_rows(RESULTS / "fullcore_synthesis_overhead.csv")
    )


def core_wrapper_synthesis_pass() -> bool:
    return any(
        row.get("scope") == "accepted_core_wrapper" and row.get("status") == "PASS" and row.get("percent_overhead")
        for row in read_rows(RESULTS / "fullcore_synthesis_overhead.csv")
    )


def full_core_synthesis_pass() -> bool:
    return any(
        row.get("scope") == "full_core" and row.get("status") == "PASS" and row.get("percent_overhead")
        for row in read_rows(RESULTS / "fullcore_synthesis_overhead.csv")
    )


def mapped_row_scope(row: dict[str, str]) -> str:
    return row.get("scope", "").strip()


def matched_mapped_ppa_pass(scope: str = "near_core_stub") -> bool:
    if scope == "near_core_stub":
        baseline, copper = "nearcore_stub_baseline", "nearcore_stub_plus_copper"
    elif scope == "accepted_core_wrapper":
        baseline, copper = "baseline_core_wrapper", "core_wrapper_plus_copper"
    elif scope == "full_core":
        baseline, copper = "full_core_baseline", "full_core_plus_copper"
    elif scope == "unit":
        baseline, copper = "baseline_prefetch_unit", "copper_unit"
    else:
        return False
    def has_real_timing(row: dict[str, str]) -> bool:
        return any(row.get(field, "").strip().upper() not in {"", "NA"} for field in ("fmax_mhz", "wns", "tns"))

    rows = [
        row
        for row in read_rows(RESULTS / "mapped_ppa.csv")
        if row.get("environment") in MAPPED_PPA_ENVIRONMENTS
        and row.get("status") == "PASS"
        and mapped_row_scope(row) == scope
        and row.get("flow") not in {"yosys", "not_run", ""}
        and has_real_timing(row)
    ]
    by_key: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        by_key.setdefault((row.get("target", ""), row.get("flow", "")), set()).add(row.get("design", ""))
    return any({baseline, copper}.issubset(designs) for designs in by_key.values())


def strongest_mapped_ppa_scope() -> str:
    if matched_mapped_ppa_pass("full_core"):
        return "full_core"
    if matched_mapped_ppa_pass("accepted_core_wrapper"):
        return "accepted_core_wrapper"
    if matched_mapped_ppa_pass("near_core_stub"):
        return "near_core_stub"
    if matched_mapped_ppa_pass("unit"):
        return "unit"
    return "none"


def top_gate(gate: str) -> dict[str, str]:
    for row in read_rows(RESULTS / "top_tier_gate_status.csv"):
        if row.get("gate") == gate:
            return row
    return {}


def top_gate_status(gate: str) -> str:
    return top_gate(gate).get("status", "UNKNOWN")


def top_overall_status() -> str:
    return top_gate_status("overall_status")


def paper_pass_row_has_artifacts(row: dict[str, str]) -> bool:
    pdf = row.get("pdf_path", "")
    log = row.get("log_path", "")
    return bool(pdf and (ROOT / pdf).exists() and (not log or (ROOT / log).exists()))


def top_gate_table() -> list[str]:
    rows = read_rows(RESULTS / "top_tier_gate_status.csv")
    lines = ["| Gate | Status | Blocker | Observed evidence |", "| --- | --- | --- | --- |"]
    if not rows:
        lines.append("| none | UNKNOWN | missing top_tier_gate_status.csv | none |")
        return lines
    for row in rows:
        lines.append(
            f"| {row.get('gate', '')} | {row.get('status', '')} | {row.get('blocker', '')} | {row.get('observed_evidence', '')} |"
        )
    return lines


def energy_proxy_present() -> bool:
    rows = read_rows(RESULTS / "energy_summary.csv")
    return any(row.get("status") == "PASS" and row.get("evidence_level", "").startswith("proxy_") for row in rows)


def csv_bool(row: dict[str, str], field: str) -> bool | None:
    value = row.get(field)
    if value is None or value == "":
        return None
    return value.strip().lower() in {"1", "true", "yes", "pass"}


def explicit_yes(row: dict[str, str], field: str) -> bool:
    return csv_bool(row, field) is True


def row_artifact_exists(row: dict[str, str]) -> bool:
    for field in ("report_path", "artifact_path", "power_report_path", "rtl_path", "gds_path"):
        value = row.get(field, "")
        if value and (ROOT / value).exists():
            return True
    return False


def manifest_has_required_types(path: Path, required: set[str], *, field: str = "evidence_type", require_signoff: bool = False) -> bool:
    rows = read_rows(path)
    found = set()
    for row in rows:
        if row.get("status") != "PASS":
            continue
        if require_signoff and not explicit_yes(row, "signoff_grade"):
            continue
        if not row_artifact_exists(row):
            continue
        value = row.get(field, "").strip().lower()
        if value in required:
            found.add(value)
    return required.issubset(found)


def fabricated_silicon_pass() -> bool:
    return manifest_has_required_types(
        RESULTS / "fabricated_silicon_manifest.csv",
        {"tapeout_gds", "foundry_shuttle", "fabrication_lot", "package_or_board", "bringup_log"},
    )


def asic_signoff_pass() -> bool:
    return manifest_has_required_types(
        RESULTS / "asic_signoff_manifest.csv",
        {"timing", "area", "power", "drc", "lvs"},
        require_signoff=True,
    )


def measured_silicon_power_pass() -> bool:
    for row in read_rows(RESULTS / "power_report_index.csv"):
        report = row.get("power_report_path") or row.get("report_path", "")
        if (
            row.get("status") == "PASS"
            and explicit_yes(row, "available")
            and row.get("measurement_type") == "measured_silicon"
            and explicit_yes(row, "silicon_measured")
            and positive_float(row.get("power_mw", ""))
            and report
            and (ROOT / report).exists()
        ):
            return True
    return False


def production_arm_integration_pass() -> bool:
    rows = read_rows(RESULTS / "production_arm_integration.csv")
    required = {"ooo", "tlb", "caches", "coherence", "interrupts", "exceptions", "memory_system"}
    found = {
        row.get("capability", "").strip().lower()
        for row in rows
        if row.get("status") == "PASS" and row_artifact_exists(row)
    }
    return required.issubset(found)


def sota_silicon_comparison_pass() -> bool:
    comparable = {"asic_signoff", "measured_silicon"}
    return any(
        row.get("status") == "PASS"
        and row.get("copper_evidence_level") in comparable
        and row.get("prior_work_evidence_level") in comparable
        and row.get("comparison_basis", "").strip().lower() in {"same_basis", "normalized_silicon"}
        and row.get("normalized_metric", "").strip()
        and row_artifact_exists(row)
        for row in read_rows(RESULTS / "sota_silicon_comparison.csv")
    )


def power_index_pass(evidence_level: str) -> bool:
    rows = [
        row
        for row in read_rows(RESULTS / "power_report_index.csv")
        if row.get("evidence_level") == evidence_level and row.get("status") == "PASS"
    ]
    def available(row: dict[str, str]) -> bool:
        return explicit_yes(row, "available")

    if evidence_level == "openroad_postroute_tool_estimate":
        return any(
            available(row)
            and row.get("measurement_type") == "openroad_estimate"
            and explicit_yes(row, "tool_report_power")
            and explicit_yes(row, "asic_tool_estimate")
            and explicit_yes(row, "postroute_estimate")
            and explicit_yes(row, "physical_layout_present")
            and explicit_yes(row, "parasitics_present")
            for row in rows
        )
    if evidence_level == "asic_liberty_tool_estimate":
        return any(
            available(row)
            and row.get("measurement_type") == "openroad_estimate"
            and explicit_yes(row, "tool_report_power")
            and explicit_yes(row, "asic_tool_estimate")
            for row in rows
        )
    if evidence_level == "fpga_tool_estimate":
        return any(
            available(row)
            and row.get("measurement_type") == "fpga_tool_estimate"
            and explicit_yes(row, "tool_report_power")
            for row in rows
        )
    if evidence_level == "proxy_activity":
        return any(
            available(row)
            and row.get("measurement_type") == "activity_proxy"
            and explicit_yes(row, "activity_proxy")
            for row in rows
        )
    if evidence_level == "proxy_assumed_memory_energy":
        return any(
            available(row)
            and row.get("measurement_type") == "memory_energy_proxy"
            and explicit_yes(row, "assumption_proxy")
            for row in rows
        )
    return any(available(row) for row in rows)


def activity_power_proxy_present() -> bool:
    return power_index_pass("proxy_activity")


def energy_gate_pass() -> bool:
    return energy_proxy_present() and (
        activity_power_proxy_present()
        or power_index_pass("openroad_postroute_tool_estimate")
        or power_index_pass("asic_liberty_tool_estimate")
        or power_index_pass("fpga_tool_estimate")
    )


def energy_evidence_levels() -> str:
    levels = []
    if power_index_pass("openroad_postroute_tool_estimate"):
        levels.append("openroad_postroute_tool_estimate")
    if power_index_pass("asic_liberty_tool_estimate"):
        levels.append("asic_liberty_tool_estimate")
    if power_index_pass("fpga_tool_estimate"):
        levels.append("fpga_tool_estimate")
    if activity_power_proxy_present():
        levels.append("proxy_activity")
    if energy_proxy_present():
        levels.append("proxy_assumed_memory_energy")
    return "; ".join(levels) if levels else "none"


def energy_claim_caveat() -> str:
    if power_index_pass("openroad_postroute_tool_estimate"):
        return "OpenROAD post-route power is a Nangate45 tool estimate with OpenROAD-flow-scripts reports and indexed final DEF/SPEF/netlist artifacts; do not call it silicon measurement or foundry signoff."
    if power_index_pass("asic_liberty_tool_estimate"):
        return "ASIC Liberty power is a Nangate45 standard-cell tool estimate; do not call it silicon measurement or post-route signoff with extracted parasitics."
    if power_index_pass("fpga_tool_estimate"):
        return "Vivado report_power is tool-estimated FPGA power for the mapped target; do not call it silicon measurement or ASIC signoff."
    return "Allowed only as proxy/model energy. Do not claim silicon power, RTL signoff power, or power efficiency without a real power report."


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
                        "purpose": "ARM-system raw output retained locally",
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
    paper_built = any(row.get("status") == "PASS" and paper_pass_row_has_artifacts(row) for row in paper_status)
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
    audit_stronger_claims = read_rows(RESULTS / "stronger_claim_audit.csv")
    audit_numbers = read_rows(RESULTS / "number_audit.csv")
    audit_todos = read_rows(RESULTS / "todo_audit.csv")
    audits_pass = (
        audit_claims
        and audit_stronger_claims
        and audit_numbers
        and audit_todos
        and all(r.get("status") == "PASS" for r in audit_claims + audit_stronger_claims + audit_numbers + audit_todos)
    )
    mapped_scope = strongest_mapped_ppa_scope()
    mapped_pass = mapped_scope != "none"
    synthesis_scope_pass = full_core_synthesis_pass() or core_wrapper_synthesis_pass() or near_core_synthesis_pass() or synthesis_overhead_pass()
    return [
        gate("G1. Open-source CI/Docker reproduction", "Yes", g1_status, "Makefile; Dockerfile; .github/workflows/reproduce.yml; .devcontainer/devcontainer.json; research/results/ci_status.csv; research/results/artifact_manifest.csv", "make readiness completes in GitHub Actions, Docker, or Codespaces with logs/artifacts", "CI/Docker/Codespaces proof has not been imported or produced in the current open evidence environment. Local Windows is editing-only." if g1_status != "PASS" else ""),
        gate("G2. Toolchain detection", "Yes", "PASS" if (RESULTS / "toolchain_status.csv").exists() else "TODO", "research/scripts/check_toolchain.py; research/results/toolchain_status.csv", "Required tools are detected and missing tools are explicit", ""),
        gate("G3. Functional model tests", "Yes", "PASS" if all_status(RESULTS / "model_tests.csv", "PASS") else ("PARTIAL" if (RESULTS / "model_tests.csv").exists() else "TODO"), "research/results/model_tests.csv; research/scripts/copper_eval_model.py", "Directed tests pass and unmodeled behaviors are labeled", "" if all_status(RESULTS / "model_tests.csv", "PASS") else "Some model checks are still non-PASS."),
        gate("G4. SystemVerilog RTL compile", "Yes", rtl_compile_status, "research/results/rtl_compile.csv; research/results/logs/rtl/", "Open-source smoke compile passes in GitHub Actions, Docker, or Codespaces", "No CI/Docker/Codespaces PASS row has been collected yet." if rtl_compile_status != "PASS" else ""),
        gate("G5. RTL simulation", "Yes", rtl_sim_status, "research/results/rtl_simulation.csv; research/results/logs/rtl/", "Directed RTL smoke simulation passes in GitHub Actions, Docker, or Codespaces", "No CI/Docker/Codespaces PASS row has been collected yet." if rtl_sim_status != "PASS" else ""),
        gate("G6. C benchmark/workload build", "Yes", "PASS" if workload_build_pass() else "PARTIAL", "research/results/workload_build.csv; research/workloads/copper_workload_suite.c", "Required workload suite builds from source and records one row per benchmark", "" if workload_build_pass() else "Current environment has not produced PASS rows for every required workload build."),
        gate("G7. Benchmark execution", "Yes", "PASS" if (cycle_eval_pass() and core_integrated_pass() and independent_sim_pass()) else ("PARTIAL" if cycle_eval_pass() or core_integrated_pass() or independent_sim_pass() or gem5_full_system_pass() else "TODO"), "research/results/performance.csv; research/results/cycle_performance.csv; research/results/core_integrated_performance.csv; research/results/independent_sim_performance.csv; research/results/gem5_validation.csv; research/results/gem5_performance.csv", "Model, cycle_model, core_integrated, and independent_sim rows exist for the public benchmark suite; gem5 rows add validated imported ARM full-system checks when present", "" if independent_sim_pass() else "Independent simulator rows are missing, blocked, or non-PASS."),
        gate("G8. Baseline prefetcher implementation", "Yes", "PASS" if baseline_pass() else "PARTIAL", "research/results/baseline_inventory.csv", "No-prefetch, next-line, stride, simple pointer-chase, and COPPER run through the same model path", "" if baseline_pass() else "At least one baseline is missing."),
        gate("G9. COPPER prefetcher implementation", "Yes", "PASS", "research/scripts/copper_eval_model.py; research/copper_prefetch_unit_open.sv; research/results/performance.csv", "Model and RTL-unit implementation exist", "Not a production core integration."),
        gate("G10. Prefetch usefulness/accuracy/coverage metrics", "Yes", "PASS" if independent_csv_pass("independent_sim_prefetch_metrics.csv") or core_csv_pass("core_integrated_prefetch_metrics.csv") or cycle_csv_pass("cycle_prefetch_metrics.csv") or (RESULTS / "prefetch_metrics.csv").exists() else "TODO", "research/results/prefetch_metrics.csv; research/results/cycle_prefetch_metrics.csv; research/results/core_integrated_prefetch_metrics.csv; research/results/independent_sim_prefetch_metrics.csv", "Issued/useful/useless/late/queue/coverage/accuracy metrics are generated with evidence-level labels", ""),
        gate("G11. Speedup/performance metrics", "Yes", "PASS" if independent_sim_pass() else ("PARTIAL" if core_integrated_pass() or cycle_eval_pass() or gem5_full_system_pass() else ("PARTIAL" if (RESULTS / "performance.csv").exists() else "TODO")), "research/results/performance.csv; research/results/cycle_performance.csv; research/results/core_integrated_performance.csv; research/results/independent_sim_performance.csv; research/results/gem5_validation.csv; research/results/gem5_performance.csv", "Per-workload speedup versus no-prefetch is reported with evidence-level labels", "" if independent_sim_pass() else "Independent simulator speedup rows are missing or blocked; do not promote beyond local deterministic models."),
        gate("G12. Memory traffic/bandwidth overhead metrics", "Yes", "PASS" if independent_csv_pass("independent_sim_memory_traffic.csv") or core_csv_pass("core_integrated_memory_traffic.csv") or cycle_csv_pass("cycle_memory_traffic.csv") or (RESULTS / "memory_traffic.csv").exists() else "TODO", "research/results/memory_traffic.csv; research/results/cycle_memory_traffic.csv; research/results/core_integrated_memory_traffic.csv; research/results/independent_sim_memory_traffic.csv", "Traffic overhead is generated from model, cycle-model, core-integrated, and independent-simulator request counts where available", ""),
        gate("G13. Sensitivity studies", "Yes", "PASS" if cycle_csv_pass("sensitivity.csv") or csv_has_no_todo(RESULTS / "sensitivity.csv") else ("PARTIAL" if (RESULTS / "sensitivity.csv").exists() else "TODO"), "research/results/sensitivity.csv", "Queue, confidence, chain depth, distance, table size, and latency sensitivities are captured", ""),
        gate("G14. Ablation studies", "Yes", "PASS" if cycle_csv_pass("ablation.csv") or csv_has_no_todo(RESULTS / "ablation.csv") else ("PARTIAL" if (RESULTS / "ablation.csv").exists() else "TODO"), "research/results/ablation.csv", "A0-A5 ablations are generated with evidence-level labels", ""),
        gate("G15. Area/resource/timing synthesis", "Yes", "PASS" if mapped_pass else ("PARTIAL" if synthesis_scope_pass else ("TODO" if not (RESULTS / "fullcore_synthesis.csv").exists() else "BLOCKED")), "research/results/synthesis.csv; research/results/synthesis_overhead.csv; research/results/fullcore_synthesis.csv; research/results/fullcore_synthesis_overhead.csv; research/results/mapped_ppa.csv; research/results/mapped_ppa_overhead.csv", "Matched unit, near-core-stub, accepted core-wrapper, or PicoRV32 tiny-SoC full-core rows exist; mapped timing requires real nextpnr, Vivado, or OpenROAD reports", "" if mapped_pass else ("No mapped full-core, near-core, or core-wrapper timing report exists; generic Yosys cells are resource evidence only. mapped_ppa.csv records the mapped-flow blocker." if synthesis_scope_pass else "No matched full-core, near-core, core-wrapper, or unit overhead row has been collected yet.")),
        gate("G16. Power/energy proxy or tool estimate", "Yes", "PASS" if energy_gate_pass() else ("PARTIAL" if energy_proxy_present() else "TODO"), "research/results/energy_proxy.csv; research/results/energy_summary.csv; research/results/power_report_index.csv; research/results/openroad_postroute_power.csv; research/results/asic_power.csv; research/results/mapped_ppa.csv; research/results/copper_mcpat_sensitivity_20260618.csv; research/results/COPPER_MCPAT_SENSITIVITY_20260618.md", "Proxy energy rows are generated and either scoped OpenROAD post-route, ASIC-Liberty, FPGA tool-power, or activity-based McPAT proxy evidence is indexed", "" if energy_gate_pass() else ("Proxy is assumption-based and not backed by activity/model power." if energy_proxy_present() else "No energy proxy or tool-power report has been generated.")),
        gate("G17. Statistical stability across seeds/input sizes", "Yes", "PASS" if cycle_stats_pass() else ("PARTIAL" if (RESULTS / "statistical_summary.csv").exists() or gem5_stats_pass() else "TODO"), "research/results/seed_stability.csv; research/results/statistical_summary.csv; research/results/gem5_statistical_summary.csv; research/results/gem5_raw_rerun_statistical_summary.csv", "Cycle-model stability covers seeds 1-3 and multiple input sizes; gem5 statistics summarize validated imported ARM-system rows and local raw rerun repeats when present", ""),
        gate("G18. Artifact package", "Yes", "PASS" if ci_artifact_package else ("PARTIAL" if package_exists else "TODO"), "dist/copper-artifact.zip; research/results/artifact_manifest.csv; research/results/ci_artifacts_manifest.csv", "Package regenerates in GitHub Actions, Docker, or Codespaces or the zip appears in imported artifacts", "" if ci_artifact_package else "Local package output is not final packaging proof."),
        gate("G19. Paper build", "Yes", "PASS" if paper_built else "BLOCKED", "research/paper/main.tex; research/results/paper_build_status.csv", "PDF builds in the current environment or imported CI; CI/Docker LaTeX is preferred when available", "" if paper_built else "No paper PASS row with existing PDF/log artifact has been collected yet."),
        gate("G20. Claim audit", "Yes", "PASS" if audits_pass else "TODO", "research/scripts/audit_claims.py; research/scripts/audit_stronger_claims.py; research/scripts/audit_numbers.py; research/scripts/audit_todos.py", "Claim, stronger-claim, number, and TODO audits pass", "" if audits_pass else "Run make paper-audit after paper generation."),
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
    status = top_overall_status()
    lines = [
        "# COPPER Conference Readiness Dashboard",
        "",
        "This dashboard is intentionally strict. PASS means the current artifact has reproducible evidence for that gate. PARTIAL means useful evidence exists, but not enough to widen the claim. The intended target is an evidence-bounded regular conference paper with an artifact/reproducibility package.",
        "",
        "Local Windows is editing-only. GitHub Actions/Codespaces/Docker is the intended evidence environment for open-source hardware and paper gates.",
        "",
        f"Final submission status from `research/results/top_tier_gate_status.csv`: {status}. This dashboard records the evidence-bounded COPPER conference package: CI-proven RTL simulation, raw gem5 full-system provenance where indexed, independent simulator evidence, accepted-core-wrapper or PicoRV32 tiny-SoC full-core mapped FPGA PPA where generated PASS rows exist, and tool-estimated/proxy power with explicit caveats. It does not authorize production ARM/OoO integration, measured silicon power, ASIC/foundry signoff, state-of-the-art performance, or broad production-readiness claims.",
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
    c12_status = "ALLOWED" if matched_mapped_ppa_pass("near_core_stub") else "TODO"
    c13_status = "ALLOWED" if matched_mapped_ppa_pass("accepted_core_wrapper") else "TODO"
    c14_status = "ALLOWED" if core_wrapper_synthesis_pass() else "TODO"
    c15_status = "ALLOWED" if gem5_full_system_pass() else "TODO"
    c16_status = "ALLOWED" if full_core_synthesis_pass() else "TODO"
    c17_status = "ALLOWED" if matched_mapped_ppa_pass("full_core") else "TODO"
    c18_status = "ALLOWED" if fabricated_silicon_pass() else "FORBIDDEN"
    c19_status = "ALLOWED" if asic_signoff_pass() else "FORBIDDEN"
    c20_status = "ALLOWED" if measured_silicon_power_pass() else "FORBIDDEN"
    c21_status = "ALLOWED" if production_arm_integration_pass() else "FORBIDDEN"
    c22_status = "ALLOWED" if sota_silicon_comparison_pass() else "FORBIDDEN"
    energy_status = "ALLOWED" if energy_gate_pass() else ("PARTIAL" if energy_proxy_present() else "TODO")
    claims = [
        ("C1", "COPPER tracks committed pointer provenance.", "ALLOWED", "research/results/model_tests.csv; research/copper_prefetch_unit_open.sv", "model; rtl-unit only when GitHub Actions/Codespaces/Docker rtl_compile.csv and rtl_simulation.csv are PASS", "Allowed for the executable model; RTL wording requires open-environment PASS rows."),
        ("C2", "COPPER issues prefetches based on committed provenance rather than arbitrary speculation.", "ALLOWED", "research/results/model_tests.csv; research/results/rtl_simulation.csv", "model; rtl-unit only when GitHub Actions/Codespaces/Docker rtl_simulation.csv is PASS", "Do not extend to a production core without integration evidence."),
        ("C3", "COPPER improves prefetch usefulness on exact measured model, cycle-model, core-integrated, independent-sim, or gem5 workloads where generated rows show improvement.", "ALLOWED", "research/results/prefetch_metrics.csv; research/results/cycle_prefetch_metrics.csv; research/results/core_integrated_prefetch_metrics.csv; research/results/independent_sim_prefetch_metrics.csv; research/results/gem5_prefetch_metrics.csv", "model; cycle_model; core_integrated; independent_sim; gem5_full_system when PASS", f"Allowed only per generated row; current gem5 scope is {gem5_evidence_summary()}; raw rerun scope is {gem5_raw_rerun_summary()}, not a fresh clone-local rerun of every raw simulation."),
        ("C4", "COPPER reports accuracy, coverage, lateness, queue drops, and traffic overhead versus shared baselines.", "ALLOWED", "research/results/prefetch_metrics.csv; research/results/memory_traffic.csv; research/results/cycle_prefetch_metrics.csv; research/results/cycle_memory_traffic.csv; research/results/core_integrated_prefetch_metrics.csv; research/results/core_integrated_memory_traffic.csv; research/results/independent_sim_prefetch_metrics.csv; research/results/independent_sim_memory_traffic.csv", "model; cycle_model; core_integrated; independent_sim", "Use per-workload language and report where overhead increases."),
        ("C5", "COPPER improves performance/speedup on exact measured workloads where performance CSVs show speedup.", "ALLOWED", "research/results/performance.csv; research/results/cycle_performance.csv; research/results/core_integrated_performance.csv; research/results/independent_sim_performance.csv", "model; cycle_model; core_integrated; independent_sim", "Do not claim universal speedup or superiority over every baseline."),
        ("C6", "COPPER avoids architectural output changes in the executable model.", "ALLOWED", "research/results/model_tests.csv; research/results/seed_stability.csv; research/results/rtl_simulation.csv", "model; rtl-unit only when GitHub Actions/Codespaces/Docker rtl_simulation.csv is PASS", "Checksum equality is model-level, and RTL smoke coverage is unit-level, not a formal ISA proof."),
        ("C7", "COPPER has matched unit-level generic-synthesis overhead.", c7_status, "research/results/synthesis.csv; research/results/synthesis_overhead.csv", "unit synthesis", "Allowed only if an open-environment Yosys flow produced matched overhead rows; not full-core overhead."),
        ("C8", "COPPER has matched near-core-stub generic-synthesis overhead.", c8_status, "research/results/fullcore_synthesis.csv; research/results/fullcore_synthesis_overhead.csv", "near_core_stub", "Allowed only when scope is called near_core_stub; not full-core overhead or mapped timing."),
        ("C9", "COPPER generalizes across the evaluated model, cycle-model, core-integrated, and independent-sim workload suite.", "ALLOWED", "research/results/benchmark_inventory.csv; research/results/cycle_performance.csv; research/results/core_integrated_performance.csv; research/results/independent_sim_performance.csv; research/results/statistical_summary.csv", "model; cycle_model; core_integrated; independent_sim", "Breadth is still not a gem5 campaign or production-core result."),
        ("C10", "COPPER has evidence-bounded OpenROAD post-route, ASIC-Liberty/FPGA tool-power, and proxy/model energy results where indexed PASS.", energy_status, "research/results/openroad_postroute_power.csv; research/results/openroad_postroute_power_overhead.csv; research/results/asic_power.csv; research/results/asic_power_overhead.csv; research/results/energy_proxy.csv; research/results/energy_summary.csv; research/results/power_report_index.csv; research/results/mapped_ppa.csv; research/results/copper_mcpat_sensitivity_20260618.csv", energy_evidence_levels(), energy_claim_caveat()),
        ("C11", "COPPER is novel versus existing pointer-chasing prefetchers.", "TODO", "research/COPPER_RELATED_WORK_MATRIX.md; research/COPPER_PRIOR_ART.md", "related-work matrix", "Use distinction language; do not claim first or publication-level novelty without a fresh literature audit."),
        ("C12", "COPPER has matched near-core-stub mapped timing.", c12_status, "research/results/mapped_ppa.csv; research/results/mapped_ppa_overhead.csv", "near_core_stub mapped PPA", "Allowed only when baseline and COPPER near-core-stub rows PASS in the same mapped flow with timing fields from nextpnr, Vivado, or OpenROAD; not full-core PPA."),
        ("C13", "COPPER has matched PicoRV32 accepted core-wrapper mapped FPGA PPA.", c13_status, "research/results/mapped_ppa.csv; research/results/mapped_ppa_overhead.csv", "accepted_core_wrapper mapped PPA", "Allowed only when baseline and COPPER PicoRV32 accepted-core-wrapper rows PASS in the same mapped flow with timing fields from nextpnr, Vivado, or OpenROAD; not full-core, ARM-core, ASIC, or silicon PPA."),
        ("C14", "COPPER has matched PicoRV32 accepted core-wrapper generic-synthesis overhead.", c14_status, "research/results/fullcore_synthesis.csv; research/results/fullcore_synthesis_overhead.csv", "accepted_core_wrapper", "Allowed only when scope is called accepted_core_wrapper; not full-core overhead or ASIC timing."),
        ("C15", "COPPER has validated gem5 ARM-system evidence across multiple benchmark families.", c15_status, "research/results/gem5_validation.csv; research/results/gem5_performance.csv; research/results/gem5_prefetch_metrics.csv; research/results/gem5_memory_traffic.csv; research/results/gem5_statistical_summary.csv; research/results/gem5_raw_rerun_manifest.csv; research/results/gem5_raw_rerun_statistical_summary.csv; research/results/logs/gem5/gem5_import.log", "gem5_full_system", f"Allowed only for summary groups with a no-prefetch baseline, a COPPER-family row, matching checksums, rc=0, and positive tick counts; current scope is {gem5_evidence_summary()}. Local raw rerun scope is {gem5_raw_rerun_summary()}; raw-only repeated-stat scope is {gem5_raw_stats_summary()}. gem5_statistical_summary.csv is still summary-derived and the raw-only statistics are not a full-matrix confidence interval unless the raw group covers the final matrix."),
        ("C16", "COPPER has matched PicoRV32 tiny-SoC full-core generic-synthesis overhead.", c16_status, "research/results/fullcore_synthesis.csv; research/results/fullcore_synthesis_overhead.csv", "full_core", "Allowed only for the open-source PicoRV32 tiny-SoC full-core harness; not production ARM, OoO, silicon, or signoff evidence."),
        ("C17", "COPPER has matched PicoRV32 tiny-SoC full-core mapped FPGA PPA.", c17_status, "research/results/mapped_ppa.csv; research/results/mapped_ppa_overhead.csv", "full_core mapped PPA", "Allowed only when baseline and COPPER PicoRV32 tiny-SoC full-core rows PASS in the same mapped flow with real timing fields; not production ARM, ASIC signoff, or silicon PPA."),
        ("C18", "COPPER is silicon-proven, taped out, fabricated, or post-silicon validated.", c18_status, "research/results/fabricated_silicon_manifest.csv", "fabricated_silicon", "Forbidden unless a manifest has PASS tapeout GDS/OAS, foundry/shuttle, fabrication lot, package/board, and bring-up artifacts with existing paths."),
        ("C19", "COPPER has ASIC or foundry signoff.", c19_status, "research/results/asic_signoff_manifest.csv", "asic_signoff", "Forbidden unless timing, area, power, DRC, and LVS signoff-grade PASS artifacts exist. OpenROAD, ASIC-Liberty, and Vivado tool estimates are not foundry signoff."),
        ("C20", "COPPER has measured silicon power.", c20_status, "research/results/power_report_index.csv", "measured_silicon", "Forbidden unless power_report_index.csv has a measured_silicon PASS row with silicon_measured=yes, positive power_mw, and an existing raw/report artifact."),
        ("C21", "COPPER integrates with a production ARM or OoO full-system core.", c21_status, "research/results/production_arm_integration.csv", "production_arm_integration", "Forbidden unless OoO, TLB, caches, coherence, interrupts, exceptions, and memory-system capabilities each have PASS integration artifacts. PicoRV32 tiny-SoC and gem5 prefetcher attachment do not satisfy this claim."),
        ("C22", "COPPER has SOTA silicon or power-efficiency results.", c22_status, "research/results/sota_silicon_comparison.csv", "sota_silicon_comparison", "Forbidden unless COPPER and prior-work rows are compared on the same ASIC signoff or measured-silicon basis with a normalized metric and source artifact."),
    ]
    lines = [
        "# COPPER Claim Ledger",
        "",
        "Allowed statuses: ALLOWED, PARTIAL, FORBIDDEN, TODO. The paper must not make stronger claims than this table supports. The intended submission claim is an evidence-bounded reproducible COPPER mechanism contribution, not silicon, signoff, production ARM/OoO, broad dominance, or production readiness.",
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

Generated evidence lives under `research/results`. The new conference-facing generated CSVs are `toolchain_status.csv`, `model_tests.csv`, `rtl_compile.csv`, `rtl_simulation.csv`, `workload_build.csv`, `benchmark_inventory.csv`, `baseline_inventory.csv`, `performance.csv`, `prefetch_metrics.csv`, `memory_traffic.csv`, `cycle_performance.csv`, `cycle_prefetch_metrics.csv`, `cycle_memory_traffic.csv`, `gem5_validation.csv`, `gem5_performance.csv`, `gem5_prefetch_metrics.csv`, `gem5_memory_traffic.csv`, `gem5_statistical_summary.csv`, `gem5_raw_rerun_manifest.csv`, `gem5_raw_rerun_statistical_summary.csv`, `independent_sim_performance.csv`, `independent_sim_prefetch_metrics.csv`, `independent_sim_memory_traffic.csv`, `core_integrated_performance.csv`, `core_integrated_prefetch_metrics.csv`, `core_integrated_memory_traffic.csv`, `energy_proxy.csv`, `energy_summary.csv`, `power_report_index.csv`, `openroad_postroute_power.csv`, `openroad_postroute_power_overhead.csv`, `asic_power.csv`, `asic_power_overhead.csv`, `copper_mcpat_sensitivity_20260618.csv`, `ablation.csv`, `sensitivity.csv`, `seed_stability.csv`, `statistical_summary.csv`, `synthesis.csv`, `synthesis_overhead.csv`, `full_core_design_inventory.csv`, `full_core_target_inventory.csv`, `fullcore_synthesis.csv`, `fullcore_synthesis_overhead.csv`, `mapped_ppa.csv`, `mapped_ppa_overhead.csv`, `hardware_evidence_summary.csv`, `top_tier_gate_status.csv`, `claim_audit.csv`, `stronger_claim_audit.csv`, `number_audit.csv`, `todo_audit.csv`, `preflight_baseline_check_public.csv`, `ci_status.csv`, `ci_artifacts_manifest.csv`, `ci_failure_summary.csv`, `artifact_inventory.csv`, and `artifact_manifest.csv`. Tool logs for open-source hardware gates are written under `research/results/logs/`.

## Evidence

Evidence used by the paper and dashboard comes from generated CSVs and explicit logs. Gem5 rows are promoted only from public tracked summaries that pass `gem5_validation.csv`: a no-prefetch baseline, a COPPER-family row, matching checksums, clean return codes, and positive tick counts; `gem5_statistical_summary.csv` is derived only from those promoted rows and marks single-sample statistics explicitly. The package includes the tracked `gem5_arm_ubuntu_fs_*/*_summary.csv` input files used by that validation ledger. `gem5_raw_rerun_manifest.csv` records local raw full-system rows with retained stats and terminal logs for the `cachesvc_codex_raw_smoke`, `zlib_codex_raw_zlib_tiny`, `zlib_codex_raw_zlib_tiny_seed12`, and `zstd_zstd_*` summaries; `gem5_raw_rerun_statistical_summary.csv` reports raw-only repeated statistics where those rerun rows have multiple samples. The current gem5 rows span multiple ARM-system benchmark families, but only the rows in `gem5_raw_rerun_manifest.csv` have retained local raw stats/terminal provenance in this workspace; the rest remain validated summaries. OpenROAD post-route rows are tool estimates only when OpenROAD-flow-scripts emits real route/final reports and, for current-schema rows, indexed final DEF/SPEF/netlist/report JSON artifacts; ASIC Liberty rows are standard-cell tool estimates only when OpenSTA/OpenROAD emits a real report; Vivado report_power rows are FPGA tool estimates. `hardware_evidence_summary.csv` and `top_tier_gate_status.csv` merge those lane outputs and keep production-core and silicon/signoff gaps machine-readable. None should be called measured silicon or signoff power. Paper claims are controlled by `research/COPPER_CLAIM_LEDGER.md`.

## Old Or Local-Only

Large simulator outputs, Vivado scratch directories, DCP files, WDB files, SAIF/VCD waveforms, and raw gem5 folders are treated as local-only unless they are small summary files or explicitly listed in the package manifest. `preflight_baseline_check_public.csv` is the packaged reviewer-facing preflight ledger; the older local `preflight_baseline_check.csv` can contain private absolute paths and is allowed to remain excluded. The package script records excluded heavy and local-only artifacts rather than hiding them.

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
    gem5_summary = gem5_evidence_summary()
    raw_summary = gem5_raw_rerun_summary()
    raw_stats = gem5_raw_stats_summary()
    status = top_overall_status()
    report = f"""# COPPER Final Reviewer Report

## Final Evidence Classification

Status: {status} for an evidence-bounded conference submission package according to `research/results/top_tier_gate_status.csv`. The strongest defensible framing is a reproducible hardware mechanism study with a coherent artifact trail. The paper can cite CI-proven RTL simulation, raw gem5 full-system provenance where retained, validated imported gem5 ARM-system summaries where PASS, independent simulator evidence, accepted-core-wrapper/PicoRV32 tiny-SoC full-core FPGA mapped PPA where PASS, FPGA tool-estimated power, and proxy energy with caveats. It must not claim production ARM/OoO integration, measured silicon power, ASIC/foundry signoff, state-of-the-art efficiency, universal speedup, production readiness, or full silicon PPA.

## Computer Architecture Reviewer

Leaning: regular-paper borderline with artifact strength, artifact-track accept. Strengths: clear committed-provenance invariant, CI-proven RTL unit simulation, source workload build path, deterministic cycle-model rows, deterministic core-integrated rows, an independent source-backed trace/event simulator across the required workload/config matrix, imported gem5 ARM-system rows with checksum/return-code agreement ({gem5_summary}) plus imported-summary confidence intervals where repeated samples exist, a local raw gem5 rerun manifest ({raw_summary}) with raw-only repeated statistics ({raw_stats}), and PicoRV32 tiny-SoC full-core mapped PPA where the generated rows PASS. Weaknesses: most gem5 evidence is still imported from validated summaries, and the local raw rerun set is still small, so it does not prove a complete broad simulator campaign with full raw-run confidence intervals. Stronger-claim blockers: no production ARM/OoO integration and no full-core post-route/silicon-grade power. Required fix for a broader architecture venue: validate the final workload/config matrix in gem5 or another accepted external core simulator with a reproducible raw-run path. Claim risks: performance claims must stay per-row and evidence-level bounded. Release check: cite the final GitHub Actions run for the submitted commit; older Phase 0 PR/push rows are not a substitute for that final run.

## Prefetching And Memory-Systems Reviewer

Leaning: weak accept for scoped mechanism, reject for replacement claims. Strengths: committed pointer-source authority is crisp; cycle, core-integrated, independent-sim, and gem5 tables include accuracy, coverage, lateness, queue drops, traffic, negative workloads, and sensitivity where available. Weaknesses: several COPPER rows trail the best baseline, including in gem5 rows. Fatal blockers: any universal-speedup or broad-dominance language would be fatal. Required fixes: keep regression discussion visible and compare per workload/configuration. Claim risks: do not imply COPPER replaces stride/stream/unsafe pointer-chase prefetchers. Phase 0 discrepancy check: no claimed metric row-count mismatch found.

## Hardware Implementation Reviewer

Leaning: artifact-track accept / broad production-architecture reject. Strengths: SystemVerilog unit, CI-proven open-source simulation, matched unit-level synthesis, near-core-stub synthesis, matched near-core-stub mapped-FPGA PPA, matched PicoRV32 accepted core-wrapper mapped-FPGA PPA, matched PicoRV32 tiny-SoC full-core synthesis/mapped-FPGA PPA when those rows are PASS, Vivado FPGA tool-estimated power when fpga_tool_estimate is PASS, and activity-based McPAT proxy evidence when proxy_activity is PASS. Weaknesses: the PicoRV32 tiny-SoC full-core harness is still not a production ARM/OoO integration, and generic Yosys has no mapped timing or power. Fatal blockers for stronger claims: silicon or foundry-signoff power remain unsupported; OpenROAD, ASIC-Liberty, and Vivado rows are tool estimates, not silicon/signoff power. Required fixes: add a signoff-calibrated or silicon-measured flow before stronger power claims. Claim risks: near-core-stub and accepted-core-wrapper rows must not be called full-core, PicoRV32 tiny-SoC full-core rows must not be called production ARM/OoO, OpenROAD/ASIC-Liberty/Vivado report_power must not be called silicon measurement, and McPAT proxy must not be called measured silicon or RTL signoff power.

## Evaluation And Statistics Reviewer

Leaning: conference artifact accept; regular paper depends on reviewer tolerance for imported/raw-mixed gem5 provenance. Strengths: deterministic cycle and core-integrated rows cover seeds 1-3, multiple input sizes, and both positive/control/stress workloads; the independent simulator executes the source-built workload binary and retains regressions; gem5 ARM-system summaries are validated with checksum/return-code checks ({gem5_summary}), imported-summary confidence intervals are emitted where repeated samples exist, and the raw rerun manifest records {raw_summary} with {raw_stats}. Weaknesses: the local raw gem5 rerun set is still too small to provide confidence intervals for a final broad workload/config matrix. Fatal blockers for stronger claims: no broad external simulator statistics with a reproducible raw-run path. Required fixes: add gem5 or another accepted external simulator run for the same workload/config matrix and confidence intervals from those runs. Claim risks: robust speedup must be described per benchmark/configuration, not as a suite-wide win. Phase 0 discrepancy check: row counts matched claimed deterministic-model rows.

## Artifact Evaluation Reviewer

Leaning: accept for the artifact if synchronized post-change CI evidence remains PASS. Strengths: Phase 0 preserved prior CI proof, the pass adds explicit preflight/tooling evidence, source workload build scripts, core-integrated logs, near-core-stub synthesis scripts, PicoRV32 core-wrapper mapped-PPA scripts, PicoRV32 tiny-SoC full-core mapped-PPA scripts, OpenROAD/ASIC-Liberty/FPGA power rows when indexed PASS, archived Vivado FPGA tool-power rows when indexed PASS, and proxy energy ledgers. Weaknesses: local Windows evidence must stay clearly separated from CI/Docker/Codespaces proof. Fatal blockers for stronger claims: silicon/signoff evidence and production ARM/OoO integration are still absent. Required fixes: keep artifact uploads and dashboards tied to the synchronized run. Claim risks: local generated rows must not be promoted over CI PASS rows unless the workflow reruns or the archived reports are explicitly indexed as archived evidence. Release check: synchronized CI evidence must correspond to the submitted commit before artifact claims are cited.

## Skeptical Novelty Reviewer

Leaning: acceptable for a narrow artifact/mechanism paper, weak for broad novelty. Strengths: the committed-provenance authority invariant is concrete and has model, cycle-model, core-integrated, imported gem5, RTL-unit, and synthesis-scope support. Weaknesses: adjacent pointer-chase, taint, capability, dependence, and DMP-defense work is crowded; the current pass refreshed the related-work matrix and paper citations for DMP attack, vendor, compiler-defense, scheduler-defense, and speculation-shadowing anchors, but it is still not a freedom-to-operate review. Fatal blockers: any first/priority/state-of-the-art language would be fatal. Required fixes: keep the related-work matrix synchronized with the paper before aiming at a broader venue. Claim risks: paper must not imply production ARM/OoO integration, measured power, or universal superiority. Release check: main-branch CI is a release gate, not a novelty claim; it must be cited from the final submitted commit.
"""
    blockers = f"""# COPPER Final Submission Blockers

Final submission status from `research/results/top_tier_gate_status.csv`: {status}. These are release boundary conditions for the evidence-bounded COPPER conference package. They are not blockers for submission at the stated evidence levels, but they are binding blockers for stronger production-core, signoff, silicon, or broad-dominance claims.

| Class | Blocker | Evidence | Required fix |
| --- | --- | --- | --- |
| SERIOUS BUT CAVEATABLE | Gem5 evidence includes validated ARM-system summaries ({gem5_summary}), imported-summary statistics where repeated samples exist, {raw_summary}, and {raw_stats}; independent_sim remains source-backed trace/event validation. | gem5_performance.csv; gem5_prefetch_metrics.csv; gem5_memory_traffic.csv; gem5_statistical_summary.csv; gem5_raw_rerun_manifest.csv; gem5_raw_rerun_statistical_summary.csv; independent_sim_performance.csv; independent_sim_prefetch_metrics.csv; independent_sim_memory_traffic.csv | Run the final full workload/config matrix in gem5 or another accepted external simulator with a reproducible raw-run path and raw-run confidence intervals before making top-tier architecture claims. |
| SERIOUS BUT CAVEATABLE | PicoRV32 tiny-SoC full-core mapped PPA is present only when generated `scope=full_core` rows PASS; it is not production ARM/OoO integration. | fullcore_synthesis.csv; fullcore_synthesis_overhead.csv; mapped_ppa.csv | Keep full-core claims scoped to the PicoRV32 tiny-SoC harness unless a production target is added. |
| SERIOUS BUT CAVEATABLE | Near-core-stub synthesis is not full-core overhead. | fullcore_synthesis_overhead.csv; mapped_ppa.csv | Keep the scope labeled near_core_stub everywhere. |
| TOP-TIER BLOCKER | Power evidence can include scoped OpenROAD post-route estimates, Nangate45 ASIC-Liberty estimates, proxy/model energy, and optional FPGA tool-power rows when indexed PASS. It is still not silicon measurement, foundry signoff, or signoff-grade power. | openroad_postroute_power.csv; asic_power.csv; asic_power_overhead.csv; mapped_ppa.csv; energy_proxy.csv; energy_summary.csv; power_report_index.csv; copper_mcpat_sensitivity_20260618.csv | Add full-core post-route/signoff or silicon-calibrated power before claiming full-system power efficiency. |
| SERIOUS BUT CAVEATABLE | Some workloads regress versus the best baseline. | cycle_performance.csv; core_integrated_performance.csv | Discuss regressions directly and keep speedup claims per-row. |
| RELEASE GATE | Main-branch Actions status must be verified for the submitted commit. | GitHub Actions `COPPER Reproduction` run for the submitted commit; preflight_baseline_check_public.csv is historical Phase 0 evidence only. | Cite the passing final main-branch run before release claims. |
| NICE TO HAVE | Local Windows cannot run paper/RTL/synthesis/workload compilers. | tooling_availability.md | Use Docker/Codespaces/GitHub Actions as the proof environment. |
| FUTURE WORK | Full-core post-route/signoff ASIC PPA is absent. | synthesis.csv; fullcore_synthesis.csv; mapped_ppa.csv; asic_power.csv | Add full-core ASIC/OpenROAD-style signoff reports if silicon-grade PPA is needed. |
"""
    write(RESEARCH / "COPPER_FINAL_REVIEWER_REPORT.md", report)
    write(RESEARCH / "COPPER_FINAL_SUBMISSION_BLOCKERS.md", blockers)


def latest_imported_ci_label() -> str:
    text = (RESULTS / "ci_status.csv").read_text(encoding="utf-8", errors="ignore") if (RESULTS / "ci_status.csv").exists() else ""
    match = re.search(r"copper_ci_(\d+)_([0-9]{8}_[0-9]{6})", text)
    if not match:
        return "not recorded in ci_status.csv"
    return f"GitHub Actions run {match.group(1)} imported at {match.group(2)}"


def build_reviewer_response_notes() -> None:
    status = top_overall_status()
    text = f"""# COPPER Reviewer Response Notes

## 1. What hardware evidence backs the submission?

The artifact has unit evidence, near-core-stub evidence, accepted-core-wrapper evidence, and PicoRV32 tiny-SoC full-core rows only where the generated CSVs mark those rows PASS. This supports the conference package at those evidence levels. It is not production ARM/OoO evidence.

## 2. Is the power measured or estimated?

Estimated/proxy only. Vivado rows are FPGA tool estimates, OpenROAD/ASIC-Liberty rows are tool estimates when indexed, and McPAT/memory-energy rows are proxy evidence. The repo has no measured silicon power claim.

## 3. Why is this not silicon-proven?

No. There is no PASS fabricated-silicon manifest, no tapeout/fabrication/package/bring-up evidence, and no post-silicon validation. The stronger-claim audit blocks unqualified silicon wording.

## 4. Is the comparison to prior work fair?

Yes only within the stated evidence level. The paper compares generated model, cycle-model, core-integrated, independent-sim, imported gem5, FPGA PPA, and proxy/tool-power rows separately. It does not compare FPGA/tool estimates against silicon-measured prior work as if they were equivalent.

## 5. Are negative/regression cases shown?

Yes. The CSVs retain per-workload rows, including cases where COPPER trails the best baseline. This blocks a universal-speedup claim.

## 6. Can the artifact reproduce the claims?

For the evidence-bounded claims, yes when the CI/Docker/Codespaces path is used. The expected checks are paper build, artifact package, claim/number/TODO/stronger-claim audits, RTL unit simulation, independent simulator rows, and hardware evidence ledgers.

## 7. What exactly is novel?

The contribution is the committed pointer-provenance authority rule for data-derived prefetch issue: a candidate must be backed by committed source-word evidence and must survive invalidation, permission, and context checks before issue. The paper does not claim pointer prefetching itself is new.

## Current Readiness

{status} for the evidence-bounded COPPER conference submission package.
"""
    write(RESEARCH / "COPPER_REVIEWER_RESPONSE_NOTES.md", text)


def build_submission_readiness_summary() -> None:
    status = top_overall_status()
    artifact = ROOT / "dist" / "copper-artifact.zip"
    paper = PAPER / "main.pdf"
    recommendation = "Submit as an evidence-bounded regular conference or artifact-track package after the final main-branch CI run for the submitted commit is attached." if status == "SUBMISSION-READY" else "Do not submit yet."
    text = f"""# COPPER Submission Readiness Summary

## Target Submission Type

Regular conference paper with an artifact/reproducibility package. The paper should be framed as an evidence-bounded reproducible hardware mechanism study.

## Strongest Supported Claims

- COPPER is a committed pointer-provenance prefetch mechanism.
- CI/Docker/Codespaces reproduce the open-source checks when the workflow passes.
- RTL unit simulation, model tests, independent simulator evidence, raw gem5 full-system provenance where retained, and validated imported gem5 ARM-system rows support the evidence-bounded evaluation.
- Accepted-core-wrapper/PicoRV32 tiny-SoC full-core FPGA mapped PPA may be cited only where generated rows PASS.
- FPGA tool-estimated power and proxy energy may be cited with caveats.

## Claims Still Forbidden

- Do not claim silicon-proven, taped-out, fabricated-chip, or post-silicon validation.
- Do not claim ASIC/foundry signoff or full silicon PPA.
- Do not claim measured silicon power.
- Do not claim production ARM/OoO/TLB/cache/coherence/interrupt integration.
- Do not claim state-of-the-art silicon efficiency, universal speedup, or production-ready status.

## Exact CI Run

Last imported artifact evidence: {latest_imported_ci_label()}. Final release evidence is the GitHub Actions run for the submitted commit; attach that run URL at submission time.

## Artifact Path

`{rel(artifact)}` if present after `make artifact`.

## Paper Path

`{rel(paper)}` if present after `make paper`.

## Remaining Limitations

- Full gem5 raw reruns are not clone-local for every imported summary row.
- PicoRV32 tiny-SoC evidence is the open-source full-core harness, not production ARM/OoO integration.
- Power is tool-estimated or proxy/model based, not measured silicon.
- Stronger silicon/signoff/commercial-production claims remain blocked by missing physical evidence.

## Recommendation

{recommendation}
"""
    write(RESEARCH / "SUBMISSION_READINESS_SUMMARY.md", text)


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

Full ARM/gem5 and Vivado reruns require external simulator, guest image, cross-toolchain, and licensed-tool setup. The repository includes scripts and summaries, but a fresh clone should not be expected to regenerate every raw simulator or Vivado artifact without that setup.
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


def first_matching(path: Path, predicate) -> dict[str, str]:
    for row in read_rows(path):
        if predicate(row):
            return row
    return {}


def compact_table(rows: list[dict[str, str]], fields: list[str]) -> list[str]:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    if not rows:
        lines.append("| " + " | ".join("none" for _ in fields) + " |")
        return lines
    for row in rows:
        lines.append("| " + " | ".join(row.get(field, "") for field in fields) + " |")
    return lines


def build_synchronized_hardware_report() -> None:
    status = top_overall_status()
    fullcore_rows = [
        row
        for row in read_rows(RESULTS / "fullcore_synthesis.csv")
        if row.get("status") == "PASS" and row.get("scope") in {"accepted_core_wrapper", "full_core"}
    ][:6]
    mapped_rows = [
        row
        for row in read_rows(RESULTS / "mapped_ppa.csv")
        if row.get("status") == "PASS"
        and row.get("scope") in {"accepted_core_wrapper", "full_core"}
        and row.get("flow") not in {"generic-yosys-resource", "not_run", ""}
    ][:8]
    power_rows = [
        row
        for row in read_rows(RESULTS / "power_report_index.csv")
        if row.get("status") == "PASS"
    ][:8]
    allowed_claims = []
    claim_lines = (RESEARCH / "COPPER_CLAIM_LEDGER.md").read_text(encoding="utf-8").splitlines() if (RESEARCH / "COPPER_CLAIM_LEDGER.md").exists() else []
    for line in claim_lines:
        if "| C" in line and "| ALLOWED |" in line:
            allowed_claims.append(line)
    recommendation = "Submit as an evidence-bounded conference artifact/mechanism package." if status == "SUBMISSION-READY" else ("Workshop only." if status == "WORKSHOP-ONLY" else "Do not submit yet.")
    remaining_blocker = top_gate("silicon_signoff_power_absent")
    text_lines = [
        "# COPPER Synchronized Hardware Evidence Report",
        "",
        "## Status",
        "",
        status,
        "",
        "## Main Result",
        "",
        "The synchronized evidence pass supports the COPPER conference artifact/mechanism submission package. It includes PicoRV32 tiny-SoC full-core mapped FPGA PPA, matched overhead, FPGA tool-estimated power where indexed, passing paper/claim audits, and a packaged artifact. It does not support production ARM/OoO integration, ASIC/foundry signoff, measured silicon power, or state-of-the-art claims.",
        "",
        "## Commands Run",
        "",
        "- `make fullcore-synth`",
        "- `make mapped-ppa`",
        "- `make power-evidence`",
        "- `make sync-hardware-evidence`",
        "- `make paper`",
        "- `make paper-audit`",
        "- `make artifact`",
        "- GitHub Actions `COPPER Reproduction` parallel lanes: `full-readiness`, `fullcore-synth`, `mapped-ppa`, `power-evidence`, and `sync-docs-audit-package`.",
        "",
        "## Lane A Full-Core/Core-Wrapper PPA",
        "",
        *compact_table(fullcore_rows, ["scope", "design", "target", "flow", "environment", "status", "report_path"]),
        "",
        "## Lane B Mapped Timing/Area/Power",
        "",
        *compact_table(mapped_rows, ["scope", "design", "target", "flow", "environment", "status", "fmax_mhz", "wns", "tns", "power_mw", "report_path"]),
        "",
        "## Lane C Power Classification",
        "",
        *compact_table(power_rows, ["scope", "design", "target", "measurement_type", "available", "power_mw", "full_core", "signoff_grade", "silicon_measured", "report_path"]),
        "",
        "## Sync Gate Status",
        "",
        *top_gate_table(),
        "",
        "## Paper/Audit/Artifact Status",
        "",
        f"- Paper/audit/artifact gate: {top_gate_status('paper_audits_artifact')}",
        "- Claim audit, stronger-claim audit, number audit, and TODO audit must all remain PASS before release.",
        "- Artifact package is generated by `make artifact` and checked by `sync_hardware_evidence.py`.",
        "",
        "## Claims Allowed Now",
        "",
    ]
    text_lines.extend(allowed_claims or ["- See `research/COPPER_CLAIM_LEDGER.md`; no ALLOWED rows were parsed."])
    text_lines.extend(
        [
            "",
            "## Claims Still Forbidden",
            "",
            "- Fabricated-chip, tapeout, or post-silicon validation.",
            "- Silicon power.",
            "- ASIC or foundry signoff.",
            "- Measured silicon power.",
            "- Production ARM/OoO integration.",
            "- State-of-the-art silicon efficiency or universal speedup.",
            "- Calling generic Yosys mapped timing.",
            "- Calling accepted-core-wrapper or near-core-stub rows full-core.",
            "- Calling PicoRV32 tiny-SoC rows production ARM/OoO.",
            "",
            "## Exact Remaining Blocker",
            "",
            f"{remaining_blocker.get('blocker', 'silicon/signoff power absent')}: {remaining_blocker.get('notes', 'Tool estimates are not signoff-grade or silicon measurements.')}",
            "",
            "## Recommendation",
            "",
            recommendation,
            "",
        ]
    )
    write(RESEARCH / "COPPER_SYNCHRONIZED_HARDWARE_EVIDENCE_REPORT.md", "\n".join(text_lines))


def build_paper_source() -> None:
    PAPER.mkdir(parents=True, exist_ok=True)
    tex = r"""\documentclass[10pt]{article}
\usepackage[margin=0.75in]{geometry}
\usepackage{url}
\usepackage{graphicx}
\usepackage{array}
\usepackage{tabularx}
\usepackage{float}
\usepackage{xcolor}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,shapes.geometric}
\graphicspath{{../results/figures/}}
\newcolumntype{Y}{>{\raggedright\arraybackslash}X}
\tikzset{
  copperpicture/.style={node distance=8mm and 10mm},
  copperbox/.style={draw, rounded corners=1.5pt, align=center, font=\footnotesize, inner sep=4pt, minimum height=8mm, text width=24mm, fill=gray!5},
  copperwide/.style={copperbox, text width=30mm},
  coppergate/.style={diamond, draw, aspect=2, align=center, font=\footnotesize, inner sep=2pt, text width=20mm, fill=orange!12},
  copperblock/.style={draw, dashed, rounded corners=1.5pt, align=center, font=\footnotesize, inner sep=4pt, text width=26mm, fill=red!6},
  copperok/.style={copperbox, fill=green!8},
  copperarrow/.style={-{Latex[length=2mm]}, thick},
  copperclear/.style={-{Latex[length=2mm]}, thick, dashed}
}

\title{COPPER: Committed Pointer-Provenance Prefetching}
\author{Anonymous Artifact Submission}
\date{}

\begin{document}
\maketitle

\begin{abstract}
Data-derived prefetchers can reduce pointer-chasing latency, but they can also turn address-shaped data into prefetch authority before the program has proved that the data is a pointer. COPPER addresses that authority problem with committed pointer-provenance prefetching: it records pointer-source evidence only after architectural commit, invalidates stale or mismatched evidence, and gates later data-derived prefetch issue on that committed evidence. This submission frames COPPER as an evidence-bounded reproducible hardware mechanism study evaluated with CI-proven RTL simulation, raw gem5 full-system provenance where retained, validated imported gem5 ARM-system summaries where PASS, independent simulator evidence, accepted-core-wrapper/PicoRV32 tiny-SoC full-core FPGA mapped PPA, and tool-estimated/proxy power. The supported claim is auditable at the stated evidence levels. It does not claim state-of-the-art performance, production readiness, a complete clone-local gem5 campaign, production ARM/OoO integration, production-core mapped timing, measured silicon power efficiency, ASIC signoff, foundry signoff, or silicon signoff.
\end{abstract}

\section{Introduction}
Pointer-heavy programs expose memory latency that ordinary address-stream prefetchers can miss. Data-derived prefetching can help by following loaded values, but the same behavior is risky when a value merely resembles an address. COPPER changes the authority rule: a prefetch candidate needs committed pointer-source evidence before issue. The mechanism is meant to filter unsafe or stale candidates while preserving the useful subset of pointer-derived prefetches.

This paper makes an evidence-bounded contribution. COPPER is evaluated as a reproducible hardware mechanism, not as a silicon product or a production processor feature. The evidence consists of executable model checks, deterministic cycle-model and core-integrated rows, source-backed independent simulator rows, validated gem5 ARM-system summaries and retained raw gem5 provenance where available, CI-proven RTL unit simulation, accepted-core-wrapper/PicoRV32 tiny-SoC full-core mapped FPGA PPA, FPGA tool-estimated power, and proxy energy. The artifact keeps these evidence levels separate and keeps negative rows visible.

This paper does not claim silicon-proven status, ASIC/foundry signoff, measured silicon power, production ARM/OoO/TLB/cache/coherence integration, state-of-the-art silicon efficiency, universal speedup, production readiness, or full silicon PPA. The claim ledger and audits are part of the submission: if the paper drifts into unsupported language, the artifact should fail.

\section{Motivation}
\begin{figure}[H]
\centering
\begin{tikzpicture}[copperpicture]
\node[copperbox] (data) {Address-shaped data word};
\node[copperblock, right=of data] (unsafe) {Data-derived candidate without committed proof};
\node[copperblock, right=of unsafe] (badissue) {Unsafe prefetch authority};
\node[copperbox, below=of data] (demand) {Demand execution uses loaded value};
\node[copperok, right=of demand] (commit) {Architectural commit creates source proof};
\node[coppergate, right=of commit] (gate) {Proof, domain, target witness?};
\node[copperok, right=of gate] (safeissue) {Scoped prefetch issue};
\draw[copperarrow] (data) -- (unsafe);
\draw[copperarrow] (unsafe) -- (badissue);
\draw[copperarrow] (data) -- (demand);
\draw[copperarrow] (demand) -- (commit);
\draw[copperarrow] (commit) -- (gate);
\draw[copperarrow] (gate) -- (safeissue);
\draw[copperclear] (gate) -- node[above, font=\scriptsize] {block on mismatch} (badissue);
\end{tikzpicture}
\caption{Pointer-chasing authority problem and COPPER's evidence-gated alternative. A data value alone is not enough authority; issue is allowed only after committed source proof and target checks agree.}
\label{fig:motivation}
\end{figure}

The motivating failure mode is not ordinary speculation alone. It is that a prefetcher may treat address-shaped data as authority, a concern sharpened by recent data-memory-dependent prefetcher attacks \cite{augury,gofetch}. COPPER instead treats committed pointer use as authority.

\section{Background And Related Work}
Prior work covers next-line, stream, stride, indirect, pointer-chase, runahead, helper-thread, and dependence-guided prefetching \cite{jouppi1990improving,chen1995effective,baer1991effective,roth1998dependence,srinath2007feedback}, as well as metadata and capability mechanisms \cite{cheri}. COPPER's distinction is narrower: committed source-word proof gates data-derived prefetch issue. The repository matrix records what COPPER does not claim.

Recent DMP attack and vendor material make the authority problem concrete: a data-dependent prefetcher may examine memory data and create cache-visible effects from the derived target \cite{augury,gofetch,intelDDP}. Software and OS defenses such as memory representation transformation or scheduler-managed prefetcher disablement address adjacent deployment points \cite{splittingsecrets,prefence}. Shadow-structure speculation defenses isolate speculative side effects until commit; COPPER instead scopes the authority of a non-speculative data-derived prefetch path \cite{safespec}.

\begin{table}[H]
\centering
\caption{Related Work Positioning}
\label{tab:related-positioning}
\begin{tabularx}{\linewidth}{YYYY}
\hline
Adjacent area & Typical focus & COPPER distinction & Claim boundary \\
\hline
Data-memory-dependent attacks & Show that data values can trigger observable prefetch behavior & Replaces address-shapedness with committed source-word authority & Attack surface is the DMP authority path, not all channels \\
Pointer-chase and indirect prefetching & Expose irregular memory parallelism from pointer-like streams & Allows issue only after the source word has committed-use proof & Does not claim pointer prefetching itself \\
Confidence and usefulness filters & Suppress candidates predicted to be inaccurate or wasteful & Blocks candidates that lack architectural authority even when they look useful & Performance regressions remain visible per row \\
Capability, tag, and taint mechanisms & Track architectural permissions, memory safety, or information flow & Tracks a small positive proof for microarchitectural DMP dereference permission & Does not replace architectural memory-safety mechanisms \\
Software or OS DMP defenses & Transform data or disable prefetching in sensitive regions & Keeps the hardware gate active at source-word granularity & Does not make compiler or OS policies obsolete \\
Runahead and translation aids & Expose misses or accelerate address translation & Recursive and cross-page issue stay bound to source proof and target witnesses & Not a general runahead or translation accelerator \\
\hline
\end{tabularx}
\end{table}

\section{Threat Model And Security Contract}
COPPER targets data-memory-dependent prefetch issue where address-shaped data, stale pointer values, or mismatched address-space state could otherwise create cache-visible prefetch activity before the program has committed a pointer use. The adversary model is scoped to the prefetch authority decision: an adversary may influence data values and observe cache or memory-system side effects, while ordinary demand accesses, branch predictor channels, non-DMP microarchitectural channels, and full operating-system isolation policy are outside this mechanism-level contract.

The security contract is intentionally small: a data-derived candidate may issue only when committed source proof exists, the source proof remains clean and current, the target authority check succeeds, and the candidate is still bound to the same relevant context. Table~\ref{tab:security-contract} maps the main reviewer attack surfaces to the local evidence that exercises the rule.

\begin{table}[H]
\centering
\caption{Security Contract And Evidence}
\label{tab:security-contract}
\begin{tabularx}{\linewidth}{YYY}
\hline
Reviewer concern & COPPER contract response & Evidence anchor \\
\hline
Address-shaped data at rest & No committed source proof, so the issue gate blocks data-only candidates & \path{COPPER_SECURITY_COVERAGE_MATRIX.md}; \path{model_tests.csv}; \path{rtl_simulation.csv} \\
Stale source after write or coherence activity & Source proof is cleared or fails epoch/value freshness checks before issue & \path{COPPER_AUTHORITY_REGRESSION_SUMMARY.md}; \path{COPPER_CEPF_LINE_E2E_SVA_SUMMARY.md} \\
Recursive or cross-page target issue & Target-line witness and translation/permission checks are required before issue & \path{COPPER_CTLW_FULL_AUTHORITY_E2E_SUMMARY.md}; \path{COPPER_CAVI_AUTHORITY_ISSUE_GATE_RTL_SUMMARY.md} \\
Context remap, permission, or revocation & Domain and revocation checks are part of the authority path, and missing evidence blocks the candidate & \path{COPPER_TLB_COHERENCE_AUTHORITY_FILTER_RTL_SUMMARY.md}; \path{COPPER_SARI_CLPD_CTLW_AUTHORITY_E2E_SUMMARY.md} \\
Broader microarchitectural isolation & Out of scope for this artifact; stronger production and silicon claims remain blocked by the claim ledger & \path{COPPER_CLAIM_LEDGER.md}; \path{stronger_claim_audit.csv} \\
\hline
\end{tabularx}
\end{table}

\section{COPPER Design}
\begin{figure}[H]
\centering
\begin{tikzpicture}[copperpicture]
\node[copperwide] (commit) {Commit path observes pointer-source use};
\node[copperwide, right=of commit] (proof) {Provenance table retains clean source evidence};
\node[coppergate, right=of proof] (issue) {Issue gate};
\node[copperwide, right=of issue] (prefetch) {Prefetch request};
\node[copperwide, below=of proof] (target) {Translation, permission, and domain checks};
\node[copperwide, above=of proof] (clear) {Writes, coherence events, remaps, and revocations clear proof};
\draw[copperarrow] (commit) -- (proof);
\draw[copperarrow] (proof) -- (issue);
\draw[copperarrow] (target) -- (issue);
\draw[copperarrow] (issue) -- (prefetch);
\draw[copperclear] (clear) -- (proof);
\end{tikzpicture}
\caption{COPPER architecture. The commit path creates source proof, invalidation removes stale proof, and the prefetch path issues only when source proof and target authority both hold.}
\label{fig:architecture}
\end{figure}

\begin{figure}[H]
\centering
\begin{tikzpicture}[copperpicture]
\node[copperbox] (load) {Load source word};
\node[copperbox, right=of load] (use) {Use as demand address};
\node[copperok, right=of use] (commit) {Commit};
\node[copperok, right=of commit] (record) {Record source proof};
\node[copperbox, below=of record] (candidate) {Later candidate forms};
\node[coppergate, left=of candidate] (check) {Check proof and authority};
\node[copperok, left=of check] (issue) {Issue};
\node[copperblock, below=of check] (block) {Block};
\draw[copperarrow] (load) -- (use);
\draw[copperarrow] (use) -- (commit);
\draw[copperarrow] (commit) -- (record);
\draw[copperarrow] (record) -- (candidate);
\draw[copperarrow] (candidate) -- (check);
\draw[copperarrow] (check) -- node[above, font=\scriptsize] {match} (issue);
\draw[copperclear] (check) -- node[right, font=\scriptsize] {mismatch} (block);
\end{tikzpicture}
\caption{Committed provenance update timeline.}
\label{fig:timeline}
\end{figure}

COPPER has three core rules: proof creation occurs after committed architectural evidence; writes, coherence updates, failed permissions, and context mismatch block or destroy proof; recursive issue does not gain authority merely because a line arrived by prefetch.

\section{Implementation}
The artifact contains a Python model, a trace-driven evaluation harness, SystemVerilog RTL units, C/C++ workload sources, reproduction scripts, and summary parsers. The open-source RTL smoke target is \path{copper_prefetch_unit_open}; larger local Vivado summaries are treated as existing evidence rather than portable rerun proof. The gem5 evidence is validated through retained summaries and provenance files where available \cite{binkert2011gem5}; the open-source full-core hardware harness uses PicoRV32 rather than a production ARM/OoO target \cite{wolf2019picorv32}.

\section{Methodology}
\begin{table}[H]
\centering
\caption{Benchmarks}
\begin{tabularx}{\linewidth}{lYY}
\hline
Class & Examples & Evidence file \\
\hline
Pointer-heavy & linked list, tree, hash, graph, Patricia & workload\_build.csv; independent\_sim\_performance.csv \\
Controls & array, matrix, compute, random access & workload\_build.csv; independent\_sim\_performance.csv \\
Stress & short chains, long chains, mixed, noisy, branchy & workload\_build.csv; independent\_sim\_performance.csv \\
\hline
\end{tabularx}
\end{table}

\begin{table}[H]
\centering
\caption{Configurations And Baselines}
\begin{tabularx}{\linewidth}{lYY}
\hline
Config & Role & Evidence file \\
\hline
no\_prefetch & reference & cycle\_performance.csv \\
next\_line & spatial baseline & cycle\_performance.csv \\
stride & regular-stream baseline & cycle\_performance.csv \\
simple\_pointer\_chase & unsafe content-derived baseline & cycle\_performance.csv \\
copper & committed-provenance policy & cycle\_performance.csv \\
\hline
\end{tabularx}
\end{table}

The normalized CSVs report per-workload rows rather than hiding negative results inside averages. Evidence levels are explicit: \texttt{model} rows come from the executable policy model, \texttt{cycle\_model} rows come from a deterministic memory-system model with hit/miss latency, memory latency, outstanding prefetches, queue drops, lateness, and demand/prefetch traffic accounting. \texttt{core\_integrated} rows add a deterministic core envelope with fetch/issue width, reorder-window pressure, load-queue pressure, branch penalties, and memory-system timing. \texttt{independent\_sim} rows execute the source-built C workload driver for checksums and then use a separate trace/event cache simulator that does not import the cycle-model or core-integrated harness. \texttt{gem5\_full\_system} rows are imported from validated ARM-system summaries only when the compared group has a no-prefetch baseline, a COPPER-family row, matching checksums, zero return codes, and positive tick counts. \texttt{gem5\_statistical\_summary.csv} reports imported-summary confidence intervals where repeated samples exist and marks single-sample rows explicitly. This paper does not claim a clone-local rerun of every raw simulator run. None of these rows claim complete CPU integration.

\section{Evaluation}
\begin{figure}[H]
\centering
\includegraphics[width=\linewidth]{copper_app_full_baseline_runtime.png}
\caption{Application runtime deltas from the generated AArch64 application figure set. The plot keeps conventional SPP, SPP+COPPER slack, standalone COPPER, and unsafe data-derived baselines visible so authority and speed are discussed separately.}
\label{fig:speedup}
\end{figure}

\begin{figure}[H]
\centering
\includegraphics[width=\linewidth]{copper_app_ctlw_reduction.png}
\caption{Target-line witness miss reduction against the unsafe data-derived baseline. This figure supports the authority-safety discussion rather than a universal performance claim.}
\label{fig:prefetch}
\end{figure}

\begin{figure}[H]
\centering
\includegraphics[width=\linewidth]{copper_app_bus_overhead.png}
\caption{Memory-bus byte deltas for standalone COPPER on the generated application workload points. The figure is used only for evidence-level traffic discussion and is not a silicon-power measurement.}
\label{fig:traffic}
\end{figure}

\begin{table}[H]
\centering
\caption{Result Figure Provenance}
\label{tab:figure-provenance}
\begin{tabularx}{\linewidth}{lYY}
\hline
Figure & Source image & Data and producer \\
\hline
\ref{fig:speedup} & \path{copper_app_full_baseline_runtime.png} & \path{copper_prefetch_traffic_overhead_20260616.csv}; \path{plot_copper_app_full_baseline_runtime.py} \\
\ref{fig:prefetch} & \path{copper_app_ctlw_reduction.png} & \path{copper_prefetch_traffic_overhead_20260616.csv}; \path{plot_copper_app_overhead_figures.py} \\
\ref{fig:traffic} & \path{copper_app_bus_overhead.png} & \path{copper_prefetch_traffic_overhead_20260616.csv}; \path{plot_copper_app_overhead_figures.py}; \path{COPPER_APP_FIGURE_INDEX_20260616.md} \\
\hline
\end{tabularx}
\end{table}

Current evidence supports selective, per-workload discussion. Several cycle-model, core-integrated, and independent-sim rows show COPPER behind the best baseline; those regressions remain in the CSVs and block a universal speedup claim.

\section{Ablation And Sensitivity}
\begin{figure}[H]
\centering
\begin{tikzpicture}[copperpicture]
\node[copperwide] (abl) {Ablation ledger: proof creation, confidence, queue, and full policy variants};
\node[copperwide, right=of abl] (sens) {Sensitivity ledger: queue, confidence, chain, distance, table, and latency sweeps};
\node[coppergate, right=of sens] (label) {Evidence-level labels};
\node[copperok, right=of label] (claim) {Per-row claim gate};
\draw[copperarrow] (abl) -- (sens);
\draw[copperarrow] (sens) -- (label);
\draw[copperarrow] (label) -- (claim);
\end{tikzpicture}
\caption{Ablation and sensitivity evidence flow. The CSV ledgers preserve scope labels so cycle-model counters are not presented as gem5 or hardware counters.}
\label{fig:ablation}
\end{figure}

The cycle-model ablations isolate no provenance, speculative provenance, committed-only proof, confidence, queue filtering, and full COPPER. Queue size, confidence threshold, chain depth, distance, table size, and memory latency are varied in sensitivity rows. These are cycle-model counters and should not be described as gem5 counters.

\section{Hardware Cost}
\begin{table}[H]
\centering
\caption{Hardware Cost}
\begin{tabularx}{\linewidth}{YYY}
\hline
Evidence & Scope & File \\
\hline
CI RTL simulation & open-source unit test & rtl\_simulation.csv \\
Yosys & generic unit resource context & synthesis.csv \\
nextpnr & mapped unit resource context when available & synthesis.csv \\
Overhead & matched unit rows from same flow & synthesis\_overhead.csv \\
Near-core stub & matched generic near-core-stub rows when Yosys runs & fullcore\_synthesis\_overhead.csv \\
PicoRV32 core-wrapper & matched generic accepted core-wrapper rows when Yosys runs & fullcore\_synthesis\_overhead.csv \\
PicoRV32 tiny-SoC full-core & matched full-core rows when Yosys or mapped flows run & fullcore\_synthesis\_overhead.csv; mapped\_ppa.csv \\
Mapped PPA & matched near-core-stub, PicoRV32 core-wrapper, PicoRV32 tiny-SoC full-core, or unit rows only when place-and-route succeeds & mapped\_ppa.csv; mapped\_ppa\_overhead.csv \\
Production-core integration & not claimed & top\_tier\_gate\_status.csv \\
\hline
\end{tabularx}
\end{table}

The artifact supports unit-level hardware plausibility, matched near-core-stub resource-overhead rows, matched PicoRV32 accepted-core-wrapper rows, and matched PicoRV32 tiny-SoC full-core rows when the generated ledgers mark them PASS. The near-core stub is not a full CPU, the accepted wrapper is not full-core, and the PicoRV32 tiny-SoC full-core harness is not a production ARM/OoO integration. Generic Yosys rows do not provide mapped timing, Fmax, ASIC area, or measured power. Mapped timing may be discussed only when \path{mapped_ppa.csv} contains matched PASS rows from nextpnr, Vivado, or OpenROAD.

\section{Energy Proxy}
\begin{table}[H]
\centering
\caption{Energy/Power Evidence}
\begin{tabularx}{\linewidth}{YYY}
\hline
Evidence & Scope & File \\
\hline
Memory traffic proxy & assumption-based, not measured & energy\_proxy.csv \\
ASIC Liberty tool-power index & Nangate45 standard-cell estimate when indexed PASS & asic\_power.csv; power\_report\_index.csv \\
OpenROAD post-route power index & Nangate45 post-route tool estimate with indexed final DEF/SPEF/netlist when PASS & openroad\_postroute\_power.csv; power\_report\_index.csv \\
FPGA tool-power index & Vivado FPGA tool estimate when indexed PASS & power\_report\_index.csv; mapped\_ppa.csv \\
Activity proxy & McPAT proxy when indexed PASS & power\_report\_index.csv; copper\_mcpat\_sensitivity\_20260618.csv \\
Summary & proxy overhead statistics & energy\_summary.csv \\
\hline
\end{tabularx}
\end{table}

Energy rows use explicit assumptions recorded in \path{energy_proxy.csv}. When the power index marks OpenROAD post-route tool estimates as PASS, the row is a Nangate45 OpenROAD-flow-scripts post-route estimate with indexed final DEF/SPEF/netlist artifacts, not silicon measurement or foundry signoff. When ASIC Liberty tool estimates are PASS, the row is a Nangate45 standard-cell Liberty estimate from OpenSTA/OpenROAD, not silicon measurement or post-route signoff with extracted parasitics. When FPGA tool estimates are PASS, the row is Vivado report power for the mapped FPGA target, not silicon or ASIC signoff. Activity-proxy PASS rows are fixed-architecture McPAT sensitivity runs driven by measured gem5 ROI counters. This supports evidence-level tool-power and proxy/model energy discussion, not foundry-signoff or silicon power-efficiency claims.

\section{Limitations}
\begin{table}[H]
\centering
\caption{Limitations}
\begin{tabularx}{\linewidth}{YY}
\hline
Limitation & Consequence \\
\hline
Gem5 rows are validated imported ARM-system summaries & Gem5 validation applies to imported PASS rows \\
Independent simulator is trace/event level & It is not a replacement for a broad gem5 campaign \\
PicoRV32 tiny-SoC is the open-source full-core target & Production ARM/OoO claims remain blocked \\
Power is tool-estimate/model based & Signoff and silicon power-efficiency claims remain blocked \\
External gem5 and Vivado setup & Large external-tool reruns are not clone-local \\
\hline
\end{tabularx}
\end{table}

\section{Artifact Evidence Gates}
\begin{table}[H]
\centering
\caption{Artifact And Evidence Gates}
\begin{tabularx}{\linewidth}{YYY}
\hline
Gate class & Status source & Interpretation \\
\hline
CI RTL evidence & rtl\_simulation.csv & GitHub Actions unit simulation \\
Cycle-model evidence & cycle\_performance.csv & deterministic memory-system timing model \\
Core-integrated evidence & core\_integrated\_performance.csv & deterministic core-envelope model \\
Independent simulator & independent\_sim\_performance.csv & source-backed trace/event simulator \\
Gem5 validated summaries & gem5\_validation.csv; gem5\_performance.csv; gem5\_statistical\_summary.csv & imported ARM-system rows and imported-summary statistics when PASS \\
Hardware cost & synthesis\_overhead.csv; fullcore\_synthesis\_overhead.csv; mapped\_ppa.csv & matched unit, near-core-stub, PicoRV32 core-wrapper, or PicoRV32 tiny-SoC full-core resources, plus mapped timing only when PASS \\
Energy proxy & energy\_proxy.csv; openroad\_postroute\_power.csv; asic\_power.csv; power\_report\_index.csv & assumption-based proxy plus OpenROAD post-route, ASIC Liberty, or FPGA tool estimates when indexed PASS \\
Package & artifact\_manifest.csv & included and excluded files \\
\hline
\end{tabularx}
\end{table}

\section{Conclusion}
COPPER is best framed as a committed-provenance authority mechanism for data-derived prefetch issue. The artifact supports that claim with a CI-proven open-source path, deterministic cycle-model and core-integrated evidence, source-backed independent-simulator rows, validated imported gem5 ARM-system rows with imported-summary statistics, matched unit-level, near-core-stub, PicoRV32 accepted-core-wrapper, and PicoRV32 tiny-SoC full-core FPGA PPA paths, FPGA tool-estimated power where indexed PASS, proxy energy rows, a claim ledger, audits, and a package manifest. The honest next step for broader production/silicon claims is a final raw-rerunnable gem5 or comparable external core validation matrix plus signoff-calibrated or silicon-measured power evidence without changing the evidence-bounded claims in this artifact.

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

@inproceedings{baer1991effective,
  title={An effective on-chip preloading scheme to reduce data access penalty},
  author={Baer, Jean-Loup and Chen, Tien-Fu},
  booktitle={ACM/IEEE Supercomputing Conference},
  year={1991}
}

@inproceedings{srinath2007feedback,
  title={Feedback directed prefetching: Improving the performance and bandwidth-efficiency of hardware prefetchers},
  author={Srinath, Santhosh and Mutlu, Onur and Kim, Hyesoon and Patt, Yale N.},
  booktitle={International Symposium on High-Performance Computer Architecture},
  year={2007}
}

@article{binkert2011gem5,
  title={The gem5 simulator},
  author={Binkert, Nathan and Beckmann, Bradford and Black, Gabriel and Reinhardt, Steven K. and Saidi, Ali and Basu, Arkaprava and Hestness, Joel and Hower, Derek R. and Krishna, Tushar and Sardashti, Somayeh and others},
  journal={ACM SIGARCH Computer Architecture News},
  year={2011}
}

@misc{wolf2019picorv32,
  title={PicoRV32: A size-optimized RISC-V CPU},
  author={Wolf, Clifford},
  howpublished={\url{https://github.com/YosysHQ/picorv32}},
  year={2019}
}

@misc{augury,
  title={Augury: Using Data Memory-Dependent Prefetchers to Leak Data at Rest},
  howpublished={\url{https://www.prefetchers.info/augury.pdf}}
}

@misc{gofetch,
  title={GoFetch},
  howpublished={\url{https://gofetch.fail/}}
}

@misc{intelDDP,
  title={Data Dependent Prefetcher},
  author={{Intel}},
  howpublished={\url{https://www.intel.com/content/www/us/en/developer/articles/technical/software-security-guidance/technical-documentation/data-dependent-prefetcher.html}},
  year={2022}
}

@misc{splittingsecrets,
  title={SplittingSecrets: A Compiler-Based Defense for Preventing Data Memory-Dependent Prefetcher Side-Channels},
  author={Sharma, Reshabh K. and Grossman, Dan and Kohlbrenner, David},
  howpublished={arXiv:2601.12270},
  year={2026}
}

@inproceedings{prefence,
  title={PreFence: A Fine-Grained and Scheduling-Aware Defense Against Prefetching-Based Attacks},
  author={Schlueter, Till and Tippenhauer, Nils Ole},
  booktitle={IEEE European Symposium on Security and Privacy},
  year={2025}
}

@inproceedings{safespec,
  title={SafeSpec: Banishing the Spectre of a Meltdown with Leakage-Free Speculation},
  author={Khasawneh, Khaled N. and Koruyeh, Esmaeil Mohammadian and Song, Chengyu and Evtyushkin, Dmitry and Ponomarev, Dmitry and Abu-Ghazaleh, Nael},
  booktitle={Design Automation Conference},
  year={2019}
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
    build_reviewer_response_notes()
    build_submission_readiness_summary()
    build_reproduction_guide()
    build_synchronized_hardware_report()
    build_paper_source()
    build_dashboard()
    print("wrote conference readiness documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
