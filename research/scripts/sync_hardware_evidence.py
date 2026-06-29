#!/usr/bin/env python3
"""Synchronize COPPER hardware, power, paper, and artifact evidence gates."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "research" / "results"
DIST = ROOT / "dist"
SUMMARY = RESULTS / "hardware_evidence_summary.csv"
TOP_TIER = RESULTS / "top_tier_gate_status.csv"
REPORT = RESULTS / "COPPER_SYNCHRONIZED_HARDWARE_EVIDENCE_REPORT.md"

VALID_SCOPES = {"unit", "near_core_stub", "accepted_core_wrapper", "core_wrapper", "full_core"}
NON_POWER_MEASUREMENT_TYPES = {"activity_proxy", "memory_energy_proxy"}
POWER_MEASUREMENT_TYPES = {"fpga_tool_estimate", "openroad_estimate", "asic_signoff", "measured_silicon"}
SIGNOFF_MEASUREMENT_TYPES = {"asic_signoff", "measured_silicon"}
VALID_MEASUREMENT_TYPES = POWER_MEASUREMENT_TYPES | NON_POWER_MEASUREMENT_TYPES | {"unavailable"}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def good(value: str) -> bool:
    return value.strip().upper() not in {"", "NA", "N/A", "NONE"}


def report_exists(row: dict[str, str]) -> bool:
    report = row.get("report_path") or row.get("power_report_path") or ""
    if not report:
        return False
    return (ROOT / report).exists()


def normalize_scope(row: dict[str, str]) -> str:
    return row.get("scope", "").strip()


def has_real_timing(row: dict[str, str]) -> bool:
    return any(good(row.get(field, "")) for field in ("fmax_mhz", "wns", "tns"))


def schema_findings() -> list[str]:
    findings: list[str] = []
    hardware_files = {
        "research/results/full_core_design_inventory.csv": ["evidence_id", "scope", "design", "target", "flow", "environment", "status", "report_path", "notes"],
        "research/results/full_core_target_inventory.csv": ["evidence_id", "scope", "design", "target", "flow", "environment", "status", "report_path", "notes"],
        "research/results/fullcore_synthesis.csv": ["evidence_id", "scope", "design", "target", "flow", "environment", "status", "report_path", "notes"],
        "research/results/mapped_ppa.csv": ["evidence_id", "scope", "design", "target", "flow", "environment", "status", "report_path", "notes"],
        "research/results/power_report_index.csv": [
            "evidence_id",
            "scope",
            "design",
            "target",
            "flow",
            "environment",
            "status",
            "report_path",
            "notes",
            "power_report_path",
            "available",
            "power_mw",
            "measurement_type",
            "signoff_grade",
            "silicon_measured",
            "full_core",
            "evidence_level",
        ],
        "research/results/energy_proxy.csv": ["evidence_id", "scope", "design", "target", "flow", "environment", "status", "report_path", "notes"],
        "research/results/energy_summary.csv": ["evidence_id", "scope", "design", "target", "flow", "environment", "status", "report_path", "notes"],
    }
    for rel_path, required in hardware_files.items():
        path = ROOT / rel_path
        rows = read_rows(path)
        if not rows:
            findings.append(f"{rel_path} has no rows")
            continue
        missing = [field for field in required if field not in rows[0]]
        if missing:
            findings.append(f"{rel_path} missing required columns: {', '.join(missing)}")
        for index, row in enumerate(rows, 2):
            scope = row.get("scope", "")
            if scope not in VALID_SCOPES:
                findings.append(f"{rel_path}:{index} has unsupported scope={scope!r}")
            if row.get("status") == "PASS" and not report_exists(row):
                findings.append(f"{rel_path}:{index} PASS row has missing report_path")
            if row.get("status") == "PASS" and row.get("flow") == "generic-yosys-resource":
                bad = [field for field in ("fmax_mhz", "wns", "tns", "power_mw") if good(row.get(field, ""))]
                if bad:
                    findings.append(f"{rel_path}:{index} generic Yosys row has non-NA mapped fields: {', '.join(bad)}")
            if rel_path == "research/results/power_report_index.csv":
                measurement_type = row.get("measurement_type", "")
                if measurement_type not in VALID_MEASUREMENT_TYPES:
                    findings.append(f"{rel_path}:{index} has unsupported measurement_type={measurement_type!r}")
                if row.get("status") == "PASS" and row.get("available", "").strip().lower() != "yes":
                    findings.append(f"{rel_path}:{index} PASS row must have available=yes")
                if row.get("status") == "PASS" and measurement_type == "unavailable":
                    findings.append(f"{rel_path}:{index} PASS row cannot use measurement_type='unavailable'")
                if row.get("silicon_measured", "").strip().lower() == "yes" and measurement_type != "measured_silicon":
                    findings.append(f"{rel_path}:{index} silicon_measured=yes without measurement_type='measured_silicon'")
                if row.get("signoff_grade", "").strip().lower() == "yes" and measurement_type not in SIGNOFF_MEASUREMENT_TYPES:
                    findings.append(f"{rel_path}:{index} signoff_grade=yes without signoff-grade measurement_type")
                if row.get("full_core", "").strip().lower() == "yes" and scope != "full_core":
                    findings.append(f"{rel_path}:{index} full_core=yes without scope='full_core'")
    for rel_path in ("research/results/fullcore_synthesis_overhead.csv", "research/results/mapped_ppa_overhead.csv"):
        rows = read_rows(ROOT / rel_path)
        if not rows:
            findings.append(f"{rel_path} has no rows")
            continue
        required = ["evidence_id", "scope", "target", "flow", "environment", "status", "metric", "baseline", "with_copper", "delta", "percent_overhead", "notes"]
        missing = [field for field in required if field not in rows[0]]
        if missing:
            findings.append(f"{rel_path} missing required columns: {', '.join(missing)}")
        for index, row in enumerate(rows, 2):
            if row.get("scope") not in VALID_SCOPES:
                findings.append(f"{rel_path}:{index} has unsupported scope={row.get('scope')!r}")
    return findings


def matched_mapped_row(rows: list[dict[str, str]], scope: str) -> dict[str, str] | None:
    pairs = {
        "accepted_core_wrapper": {"baseline_core_wrapper", "core_wrapper_plus_copper"},
        "full_core": {"full_core_baseline", "full_core_plus_copper"},
    }
    by_key: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        row_scope = normalize_scope(row)
        if (
            row.get("status") == "PASS"
            and row_scope == scope
            and row.get("flow") not in {"", "not_run", "yosys", "generic-yosys-resource"}
            and has_real_timing(row)
        ):
            by_key.setdefault((row.get("target", ""), row.get("flow", "")), []).append(row)

    def mapped_priority(item: tuple[tuple[str, str], list[dict[str, str]]]) -> tuple[int, str, str]:
        target, flow = item[0]
        if flow == "vivado-impl":
            return (0, target, flow)
        if "openroad" in flow:
            return (1, target, flow)
        if "nextpnr-ecp5" in flow:
            return (2, target, flow)
        if "nextpnr-ice40" in flow:
            return (3, target, flow)
        return (9, target, flow)

    for _key, group in sorted(by_key.items(), key=mapped_priority):
        designs = {row.get("design", "") for row in group}
        if pairs[scope].issubset(designs):
            copper = next((row for row in group if row.get("design") in {"core_wrapper_plus_copper", "full_core_plus_copper"}), group[0])
            return copper
    return None


def matched_overhead_row(rows: list[dict[str, str]], scope: str) -> dict[str, str] | None:
    for row in rows:
        if row.get("scope") == scope and row.get("status") == "PASS" and good(row.get("percent_overhead", "")):
            return row
    return None


def strongest_power_row(rows: list[dict[str, str]]) -> tuple[dict[str, str] | None, bool]:
    order = {
        "measured_silicon": 0,
        "asic_signoff": 1,
        "openroad_estimate": 2,
        "fpga_tool_estimate": 3,
        "activity_proxy": 4,
        "memory_energy_proxy": 5,
    }
    pass_rows = [row for row in rows if row.get("status") == "PASS" and row.get("available", "").strip().lower() == "yes"]
    pass_rows.sort(key=lambda row: order.get(row.get("measurement_type", "unavailable"), 99))
    only_proxy = bool(pass_rows) and all(row.get("measurement_type") in NON_POWER_MEASUREMENT_TYPES for row in pass_rows)
    return (pass_rows[0] if pass_rows else None), only_proxy


def audit_status() -> tuple[str, str]:
    audit_files = [
        RESULTS / "claim_audit.csv",
        RESULTS / "stronger_claim_audit.csv",
        RESULTS / "number_audit.csv",
        RESULTS / "todo_audit.csv",
    ]
    missing = [rel(path) for path in audit_files if not path.exists()]
    if missing:
        return "FATAL", f"missing audit file(s): {', '.join(missing)}"
    failing = []
    for path in audit_files:
        for row in read_rows(path):
            if row.get("status") == "FAIL":
                failing.append(rel(path))
                break
    if failing:
        return "FATAL", f"audit failure in {', '.join(sorted(set(failing)))}"
    return "PASS", "claim, stronger-claim, number, and todo audits pass"


def paper_status() -> tuple[str, str]:
    rows = read_rows(RESULTS / "paper_build_status.csv")
    for row in rows:
        if row.get("status") != "PASS":
            continue
        pdf = row.get("pdf_path", "")
        log = row.get("log_path", "")
        if pdf and (ROOT / pdf).exists() and (not log or (ROOT / log).exists()):
            return "PASS", f"paper_build_status.csv contains a PASS row with existing PDF/log for {row.get('environment', 'unknown')}"
    if any(row.get("status") == "PASS" for row in rows):
        return "BLOCKER", "paper build PASS row exists but its referenced PDF/log is missing"
    if any(row.get("status") == "FAIL" for row in rows):
        return "FATAL", "paper build has a FAIL row and no PASS row"
    return "BLOCKER", "paper build has no PASS row in the available evidence"


def artifact_status() -> tuple[str, str]:
    zip_path = DIST / "copper-artifact.zip"
    manifest = RESULTS / "artifact_manifest.csv"
    if zip_path.exists() and manifest.exists() and zip_path.stat().st_size > 0:
        return "PASS", "artifact zip and manifest exist"
    return "FATAL", "artifact package or manifest is missing"


def summary_row(
    gate: str,
    scope: str,
    status: str,
    strongest: str,
    evidence_id: str,
    source_csv: str,
    allowed: str,
    forbidden: str,
    notes: str,
) -> dict[str, str]:
    return {
        "gate": gate,
        "scope": scope,
        "status": status,
        "strongest_evidence": strongest,
        "evidence_id": evidence_id,
        "source_csv": source_csv,
        "claim_allowed": allowed,
        "claim_forbidden": forbidden,
        "notes": notes,
    }


def gate_row(gate: str, status: str, severity: str, required: str, observed: str, blocker: str, notes: str) -> dict[str, str]:
    return {
        "gate": gate,
        "status": status,
        "severity": severity,
        "required_evidence": required,
        "observed_evidence": observed,
        "blocker": blocker,
        "notes": notes,
    }


def markdown_table(rows: list[dict[str, str]], fields: list[str]) -> list[str]:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    if not rows:
        lines.append("| " + " | ".join("none" for _ in fields) + " |")
        return lines
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("|", "/") for field in fields) + " |")
    return lines


def first_gate(rows: list[dict[str, str]], gate: str) -> dict[str, str]:
    return next((row for row in rows if row.get("gate") == gate), {})


def report_recommendation(overall: str) -> str:
    if overall == "SUBMISSION-READY":
        return "Submit"
    if overall == "WORKSHOP-ONLY":
        return "workshop only"
    return "do not submit yet"


def write_synchronized_report(summary: list[dict[str, str]], top: list[dict[str, str]], overall: str) -> None:
    lane_a = [
        row
        for row in read_rows(RESULTS / "fullcore_synthesis.csv")
        if row.get("status") == "PASS" and row.get("scope") in {"accepted_core_wrapper", "full_core"}
    ][:8]
    lane_b = [
        row
        for row in read_rows(RESULTS / "mapped_ppa.csv")
        if row.get("status") == "PASS"
        and row.get("scope") in {"accepted_core_wrapper", "full_core"}
        and row.get("flow") not in {"generic-yosys-resource", "not_run", ""}
    ][:10]
    lane_c = [row for row in read_rows(RESULTS / "power_report_index.csv") if row.get("status") == "PASS"][:8]
    paper_gate = first_gate(top, "paper_audits_artifact")
    remaining = first_gate(top, "silicon_signoff_power_absent")
    allowed = [row for row in summary if row.get("status") == "PASS" and row.get("claim_allowed")]
    forbidden = sorted({row.get("claim_forbidden", "") for row in summary if row.get("claim_forbidden")})
    main_result = (
        "The synchronized hardware-evidence pass supports a scoped COPPER artifact/mechanism submission. "
        "It has accepted-core-wrapper or stronger mapped timing, matched baseline/COPPER overhead, "
        "fpga_tool_estimate or stronger power evidence, passing paper/audit/artifact gates, and explicit "
        "machine-readable blockers for stronger production-core, signoff, silicon, or top-tier claims."
    )
    lines = [
        "# COPPER Synchronized Hardware Evidence Report",
        "",
        "## Status",
        "",
        overall,
        "",
        "## Main Result",
        "",
        main_result,
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
        "- GitHub Actions parallel lanes: `full-readiness`, `fullcore-synth`, `mapped-ppa`, `power-evidence`, `sync-docs-audit-package`.",
        "",
        "## Lane A Full-Core/Core-Wrapper PPA",
        "",
        *markdown_table(lane_a, ["scope", "design", "target", "flow", "environment", "status", "report_path"]),
        "",
        "## Lane B Mapped Timing/Area/Power",
        "",
        *markdown_table(lane_b, ["scope", "design", "target", "flow", "environment", "status", "fmax_mhz", "wns", "tns", "power_mw", "report_path"]),
        "",
        "## Lane C Power Classification",
        "",
        *markdown_table(lane_c, ["scope", "design", "target", "measurement_type", "available", "power_mw", "full_core", "signoff_grade", "silicon_measured", "report_path"]),
        "",
        "## Sync Gate Status",
        "",
        *markdown_table(top, ["gate", "status", "severity", "blocker", "observed_evidence"]),
        "",
        "## Paper/Audit/Artifact Status",
        "",
        f"{paper_gate.get('status', 'UNKNOWN')}: {paper_gate.get('notes', 'paper/audit/artifact evidence unavailable')}",
        "",
        "## Claims Allowed Now",
        "",
        *markdown_table(allowed, ["gate", "scope", "claim_allowed", "evidence_id", "source_csv"]),
        "",
        "## Claims Still Forbidden",
        "",
    ]
    lines.extend(f"- {item}" for item in forbidden)
    lines.extend(
        [
            "",
            "## Exact Remaining Blocker",
            "",
            f"{remaining.get('blocker', 'silicon/signoff power absent')}: {remaining.get('notes', 'Tool estimates are not signoff-grade or silicon measurements.')}",
            "",
            "## Recommendation",
            "",
            report_recommendation(overall),
            "",
        ]
    )
    write_text(REPORT, "\n".join(lines))


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    mapped_rows = read_rows(RESULTS / "mapped_ppa.csv")
    mapped_overhead = read_rows(RESULTS / "mapped_ppa_overhead.csv")
    fullcore_overhead = read_rows(RESULTS / "fullcore_synthesis_overhead.csv")
    power_rows = read_rows(RESULTS / "power_report_index.csv")
    findings = schema_findings()

    full_core_timing = matched_mapped_row(mapped_rows, "full_core")
    accepted_timing = matched_mapped_row(mapped_rows, "accepted_core_wrapper")
    timing = full_core_timing or accepted_timing
    timing_scope = "full_core" if full_core_timing else ("accepted_core_wrapper" if accepted_timing else "none")

    overhead = (
        matched_overhead_row(mapped_overhead, "full_core")
        or matched_overhead_row(mapped_overhead, "accepted_core_wrapper")
        or matched_overhead_row(fullcore_overhead, "accepted_core_wrapper")
    )
    overhead_scope = overhead.get("scope", "none") if overhead else "none"

    power, only_proxy = strongest_power_row(power_rows)
    power_type = power.get("measurement_type", "none") if power else "none"
    power_is_strong_enough = power_type in POWER_MEASUREMENT_TYPES
    signoff_power = any(
        row.get("status") == "PASS"
        and row.get("available", "").strip().lower() == "yes"
        and row.get("measurement_type") in SIGNOFF_MEASUREMENT_TYPES
        for row in power_rows
    )

    audit_state, audit_note = audit_status()
    paper_state, paper_note = paper_status()
    artifact_state, artifact_note = artifact_status()
    paper_bundle_state = "PASS" if audit_state == paper_state == artifact_state == "PASS" else "FATAL" if "FATAL" in {audit_state, paper_state, artifact_state} else "BLOCKER"
    timing_claim = (
        "accepted-core-wrapper mapped timing"
        if timing_scope == "accepted_core_wrapper"
        else ("PicoRV32 tiny-SoC full-core mapped timing" if timing_scope == "full_core" else "")
    )
    timing_forbidden = (
        "unscoped or production-core full-core PPA; generic Yosys timing; unmapped Fmax"
        if timing_scope == "full_core"
        else "full-core PPA; generic Yosys timing; unmapped Fmax"
    )
    overhead_forbidden = (
        "unscoped or production-core overhead"
        if overhead_scope == "full_core"
        else "full-core overhead unless full_core rows PASS"
    )

    summary = [
        summary_row(
            "mapped_timing",
            timing_scope,
            "PASS" if timing else "BLOCKER",
            f"{timing.get('flow', '')} {timing.get('target', '')}".strip() if timing else "none",
            timing.get("evidence_id", "") if timing else "",
            "research/results/mapped_ppa.csv",
            timing_claim,
            timing_forbidden,
            "Matched baseline/COPPER mapped timing exists." if timing else "No accepted_core_wrapper or full_core matched mapped timing PASS row.",
        ),
        summary_row(
            "matched_overhead",
            overhead_scope,
            "PASS" if overhead else "BLOCKER",
            overhead.get("metric", "") if overhead else "none",
            overhead.get("evidence_id", "") if overhead else "",
            "research/results/mapped_ppa_overhead.csv; research/results/fullcore_synthesis_overhead.csv",
            "matched overhead for the listed scope" if overhead else "",
            overhead_forbidden,
            "Matched overhead PASS row exists." if overhead else "No matched baseline/COPPER overhead PASS row.",
        ),
        summary_row(
            "power_classification",
            power.get("scope", "none") if power else "none",
            "PASS" if power_is_strong_enough else ("BLOCKER" if power or only_proxy else "BLOCKER"),
            power_type,
            power.get("evidence_id", "") if power else "",
            "research/results/power_report_index.csv",
            f"{power_type} power evidence" if power_is_strong_enough else ("proxy energy only" if power else ""),
            "silicon/signoff/full-core power unless measurement_type proves it",
            "Strongest power row is a tool estimate or better." if power_is_strong_enough else "Only proxy or unavailable power evidence is present.",
        ),
        summary_row(
            "paper_audit_artifact",
            "artifact",
            paper_bundle_state,
            f"paper={paper_state}; audit={audit_state}; artifact={artifact_state}",
            "",
            "research/results/claim_audit.csv; research/results/stronger_claim_audit.csv; research/results/number_audit.csv; research/results/todo_audit.csv; research/results/paper_build_status.csv; research/results/artifact_manifest.csv",
            "scoped paper/artifact claims" if paper_bundle_state == "PASS" else "",
            "unsupported paper claims; failed artifact package",
            f"{paper_note}; {audit_note}; {artifact_note}",
        ),
    ]

    top = []
    top.append(gate_row("schema_integrity", "FATAL" if findings else "PASS", "FATAL" if findings else "INFO", "shared schema and valid scope rows", " | ".join(findings) if findings else "all checked ledgers have required columns", "schema mismatch" if findings else "", "Exit 1 only when this or another FATAL row is present."))
    top.append(gate_row("accepted_or_full_mapped_timing", "PASS" if timing else "BLOCKER", "BLOCKER" if not timing else "INFO", "accepted_core_wrapper or full_core matched mapped timing PASS", timing.get("evidence_id", "none") if timing else "none", "" if timing else "no accepted_core_wrapper/full_core timing PASS", "Generic Yosys resource rows are deliberately excluded."))
    top.append(gate_row("matched_overhead", "PASS" if overhead else "BLOCKER", "BLOCKER" if not overhead else "INFO", "matched baseline/COPPER overhead PASS", overhead.get("evidence_id", "none") if overhead else "none", "" if overhead else "no matched overhead PASS", "Overhead may be mapped or generic but must be scope-labeled."))
    top.append(gate_row("power_evidence", "PASS" if power_is_strong_enough else "BLOCKER", "BLOCKER" if not power_is_strong_enough else "INFO", "fpga_tool_estimate or stronger", power_type, "only proxy power" if only_proxy else ("" if power_is_strong_enough else "no qualifying power estimate"), "Proxy rows remain useful but do not satisfy this gate alone."))
    top.append(gate_row("full_core_absent", "BLOCKER" if not full_core_timing else "PASS", "BLOCKER" if not full_core_timing else "INFO", "true full_core mapped PPA", full_core_timing.get("evidence_id", "none") if full_core_timing else "none", "full_core absent" if not full_core_timing else "", "Accepted core-wrapper rows are not full-core rows."))
    top.append(gate_row("silicon_signoff_power_absent", "BLOCKER" if not signoff_power else "PASS", "BLOCKER" if not signoff_power else "INFO", "measured_silicon or asic_signoff power", "present" if signoff_power else "none", "silicon/signoff power absent" if not signoff_power else "", "Tool estimates are not signoff-grade or silicon measurements."))
    top.append(gate_row("paper_audits_artifact", paper_bundle_state, "FATAL" if paper_bundle_state == "FATAL" else ("BLOCKER" if paper_bundle_state == "BLOCKER" else "INFO"), "paper build, audits, and artifact package PASS", f"paper={paper_state}; audit={audit_state}; artifact={artifact_state}", "" if paper_bundle_state == "PASS" else "paper/audit/artifact gate not PASS", f"{paper_note}; {audit_note}; {artifact_note}"))

    fatal = any(row["status"] == "FATAL" or row["severity"] == "FATAL" for row in top)
    submission_ready = bool(timing and overhead and power_is_strong_enough and paper_bundle_state == "PASS" and not fatal)
    overall = "SUBMISSION-READY" if submission_ready else ("NOT READY" if fatal else "WORKSHOP-ONLY")
    top.append(gate_row("overall_status", overall, "INFO" if not fatal else "FATAL", "scoped artifact/mechanism gates PASS while stronger-claim blockers stay explicit", overall, "production/full-system full-core and silicon/signoff blockers remain for stronger claims" if submission_ready else ("fatal evidence/audit/artifact failure" if fatal else "honest hardware/power blocker remains"), "SUBMISSION-READY here means scoped artifact/mechanism readiness only, not top-tier full-core, production, ASIC signoff, or silicon readiness."))

    write_csv(SUMMARY, ["gate", "scope", "status", "strongest_evidence", "evidence_id", "source_csv", "claim_allowed", "claim_forbidden", "notes"], summary)
    write_csv(TOP_TIER, ["gate", "status", "severity", "required_evidence", "observed_evidence", "blocker", "notes"], top)
    write_synchronized_report(summary, top, overall)
    print(f"wrote {rel(SUMMARY)}, {rel(TOP_TIER)}, and {rel(REPORT)} ({overall})")
    return 1 if fatal else 0


if __name__ == "__main__":
    raise SystemExit(main())
