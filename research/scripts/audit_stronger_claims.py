#!/usr/bin/env python3
"""Fail on unsupported silicon/signoff/production-strength COPPER claims.

The regular claim audit catches broad promotional language in the paper. This
audit is narrower and evidence-aware: it allows blocker/limitation wording, but
an unqualified positive stronger claim must be backed by a matching evidence
manifest or generated power index row.
"""

from __future__ import annotations

import csv
import html
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "stronger_claim_audit.csv"
PY_CLAIM_SURFACES = {
    "build_conference_docs.py",
    "build_copper_claim_evidence_matrix.py",
    "build_copper_conference_docx.py",
    "build_copper_full_docx.py",
    "build_copper_scoop_conference_docx.py",
}

ALLOW_CONTEXT = re.compile(
    r"\b("
    r"absent|blocked|blocker|cannot|can't|disallow|does not|don't|do not|fail|forbid|forbidden|"
    r"guard|guards|limitation|missing|must not|needs?|no|not|only if|remain|requires?|required|"
    r"rather than|should not|unsupported|unless|without"
    r")\b",
    re.I,
)
NONE_SHOULD_BE_CALLED = re.compile(r"\bnone\s+should\s+be\s+called\b", re.I)


def rel(path: Path, root: Path = ROOT) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_rows(root: Path, relative: str) -> list[dict[str, str]]:
    path = root / relative
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def path_exists(root: Path, value: str) -> bool:
    value = (value or "").strip()
    return bool(value) and (root / value).exists()


def positive_float(value: str) -> bool:
    try:
        return float(value) > 0.0
    except (TypeError, ValueError):
        return False


def yes(value: str) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "pass"}


def row_has_existing_artifact(root: Path, row: dict[str, str]) -> bool:
    for field in ("report_path", "artifact_path", "power_report_path", "rtl_path", "gds_path"):
        if path_exists(root, row.get(field, "")):
            return True
    return False


def manifest_has_required_types(
    root: Path,
    relative: str,
    required: set[str],
    *,
    type_fields: tuple[str, ...] = ("evidence_type", "capability", "artifact_type"),
    extra_check: Callable[[dict[str, str]], bool] | None = None,
) -> tuple[bool, str]:
    rows = read_rows(root, relative)
    if not rows:
        return False, f"missing {relative}"
    found: set[str] = set()
    for row in rows:
        if row.get("status", "").strip().upper() != "PASS":
            continue
        if extra_check and not extra_check(row):
            continue
        if not row_has_existing_artifact(root, row):
            continue
        for field in type_fields:
            value = row.get(field, "").strip().lower()
            if value in required:
                found.add(value)
    missing = sorted(required - found)
    if missing:
        return False, f"{relative} missing PASS artifact type(s): {', '.join(missing)}"
    return True, f"{relative} has PASS artifacts for {', '.join(sorted(required))}"


def fabricated_silicon_evidence(root: Path) -> tuple[bool, str]:
    required = {"tapeout_gds", "foundry_shuttle", "fabrication_lot", "package_or_board", "bringup_log"}
    return manifest_has_required_types(root, "research/results/fabricated_silicon_manifest.csv", required)


def asic_signoff_evidence(root: Path) -> tuple[bool, str]:
    required = {"timing", "area", "power", "drc", "lvs"}
    return manifest_has_required_types(
        root,
        "research/results/asic_signoff_manifest.csv",
        required,
        extra_check=lambda row: yes(row.get("signoff_grade", "")),
    )


def measured_silicon_power_evidence(root: Path) -> tuple[bool, str]:
    rows = read_rows(root, "research/results/power_report_index.csv")
    if not rows:
        return False, "missing research/results/power_report_index.csv"
    for row in rows:
        if (
            row.get("status") == "PASS"
            and yes(row.get("available", ""))
            and row.get("measurement_type") == "measured_silicon"
            and yes(row.get("silicon_measured", ""))
            and positive_float(row.get("power_mw", ""))
            and path_exists(root, row.get("power_report_path") or row.get("report_path", ""))
        ):
            return True, f"measured_silicon PASS row {row.get('evidence_id', '')}".strip()
    return False, "no measured_silicon PASS row with silicon_measured=yes, positive power_mw, and existing report"


def production_arm_evidence(root: Path) -> tuple[bool, str]:
    required = {"ooo", "tlb", "caches", "coherence", "interrupts", "exceptions", "memory_system"}
    return manifest_has_required_types(
        root,
        "research/results/production_arm_integration.csv",
        required,
        type_fields=("capability", "evidence_type"),
    )


def sota_efficiency_evidence(root: Path) -> tuple[bool, str]:
    rows = read_rows(root, "research/results/sota_silicon_comparison.csv")
    if not rows:
        return False, "missing research/results/sota_silicon_comparison.csv"
    comparable = {"asic_signoff", "measured_silicon"}
    for row in rows:
        if (
            row.get("status") == "PASS"
            and row.get("copper_evidence_level") in comparable
            and row.get("prior_work_evidence_level") in comparable
            and row.get("comparison_basis", "").strip().lower() in {"same_basis", "normalized_silicon"}
            and row.get("normalized_metric", "").strip()
            and row_has_existing_artifact(root, row)
        ):
            return True, f"comparable silicon/signoff SOTA row {row.get('comparison_id', '')}".strip()
    return False, "no comparable asic_signoff/measured_silicon PASS row with a normalized metric and artifact"


def fresh_literature_audit_evidence(root: Path) -> tuple[bool, str]:
    rows = read_rows(root, "research/results/literature_priority_audit.csv")
    if not rows:
        return False, "missing research/results/literature_priority_audit.csv"
    for row in rows:
        if row.get("status") == "PASS" and row.get("claim_scope", "").strip().lower() == "priority":
            return True, "literature_priority_audit.csv has PASS priority scope"
    return False, "no PASS priority-scope row in literature_priority_audit.csv"


@dataclass(frozen=True)
class ClaimPolicy:
    term: str
    pattern: re.Pattern[str]
    evidence_required: str
    checker: Callable[[Path], tuple[bool, str]]


POLICIES = [
    ClaimPolicy(
        "fabricated chip",
        re.compile(r"\bfabricated[- ]chip\b|\bfabricated\s+COPPER\s+chip\b|\bchip\s+fabricat(?:ed|ion)\b", re.I),
        "fabricated_silicon_manifest.csv PASS tapeout/fab/package/bring-up artifacts",
        fabricated_silicon_evidence,
    ),
    ClaimPolicy(
        "tapeout",
        re.compile(r"\btape[- ]?out\b|\btaped[- ]?out\b", re.I),
        "fabricated_silicon_manifest.csv PASS tapeout/fab/package/bring-up artifacts",
        fabricated_silicon_evidence,
    ),
    ClaimPolicy(
        "post-silicon",
        re.compile(r"\bpost[- ]silicon\b", re.I),
        "fabricated_silicon_manifest.csv PASS tapeout/fab/package/bring-up artifacts",
        fabricated_silicon_evidence,
    ),
    ClaimPolicy(
        "measured silicon",
        re.compile(r"\bmeasured[- ]silicon\b(?![- ]power)|\bsilicon[- ]measured\b(?![- ]power)", re.I),
        "fabricated_silicon_manifest.csv PASS tapeout/fab/package/bring-up artifacts",
        fabricated_silicon_evidence,
    ),
    ClaimPolicy(
        "silicon-proven",
        re.compile(r"\bsilicon[- ]proven\b", re.I),
        "fabricated_silicon_manifest.csv PASS tapeout/fab/package/bring-up artifacts",
        fabricated_silicon_evidence,
    ),
    ClaimPolicy(
        "ASIC signoff",
        re.compile(r"\b(?:ASIC|foundry)[- /]?signoff\b|\bASIC\s+signoff\b|\bfoundry\s+signoff\b", re.I),
        "asic_signoff_manifest.csv PASS timing/area/power/DRC/LVS signoff-grade artifacts",
        asic_signoff_evidence,
    ),
    ClaimPolicy(
        "production ARM",
        re.compile(r"\bproduction[- ]ARM(?:/OoO)?\b|\bproduction\s+ARM\b", re.I),
        "production_arm_integration.csv PASS OoO/TLB/cache/coherence/interrupt/exception/memory-system artifacts",
        production_arm_evidence,
    ),
    ClaimPolicy(
        "SOTA efficiency",
        re.compile(r"\bSOTA[- ]efficiency\b|\bstate[- ]of[- ]the[- ]art\s+(?:power\s+)?efficiency\b", re.I),
        "sota_silicon_comparison.csv comparable ASIC/signoff or silicon-measured normalized rows",
        sota_efficiency_evidence,
    ),
    ClaimPolicy(
        "measured power",
        re.compile(r"\bmeasured[- ](?:silicon[- ])?power\b|\bmeasured\s+silicon\s+power\b|\bsilicon[- ]measured[- ]power\b", re.I),
        "power_report_index.csv measured_silicon PASS row with positive power_mw and existing report",
        measured_silicon_power_evidence,
    ),
    ClaimPolicy(
        "priority novelty",
        re.compile(r"\bfirst\s+public\b|\bfirst\s+public\s+DMP\s+defen[cs]e\b|\bpublication[- ]level\s+novelty\b", re.I),
        "fresh literature-priority audit with claim_scope=priority",
        fresh_literature_audit_evidence,
    ),
]


def read_claim_surface(path: Path) -> str:
    if path.suffix.lower() != ".docx":
        return path.read_text(encoding="utf-8", errors="ignore")
    try:
        with zipfile.ZipFile(path) as zf:
            xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
    except (KeyError, OSError, zipfile.BadZipFile):
        return ""
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<[^>]+>", " ", xml)
    return html.unescape(xml)


def default_documents(root: Path) -> list[Path]:
    candidates = [
        root / "README.md",
        root / "REPRODUCIBILITY_STATUS.md",
        root / "AUDIT.md",
        root / "AUDIT_REPORT.md",
        root / "research" / "paper" / "main.tex",
    ]
    for base in (root / "docs", root / "research"):
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or "results" in path.parts:
                continue
            suffix = path.suffix.lower()
            if suffix in {".md", ".tex", ".docx"} or (suffix == ".py" and path.name in PY_CLAIM_SURFACES):
                candidates.append(path)
    return sorted(set(path for path in candidates if path.exists()))


def local_claim_context(line: str, start: int, end: int) -> str:
    """Return the local clause around a matched phrase.

    A whole-line exemption is too loose: "does not claim ASIC signoff; COPPER is
    silicon-proven" should allow the first phrase but still fail the second.
    """
    left_candidates = [line.rfind(delim, 0, start) for delim in (";", ".", "!", "?")]
    left = max(left_candidates)
    right_candidates = [line.find(delim, end) for delim in (";", ".", "!", "?")]
    right_existing = [idx for idx in right_candidates if idx != -1]
    right = min(right_existing) if right_existing else len(line)
    return line[left + 1 : right].strip()


def is_qualified_context(line: str, start: int, end: int) -> bool:
    context = local_claim_context(line, start, end)
    return bool(ALLOW_CONTEXT.search(context) or NONE_SHOULD_BE_CALLED.search(context))


def audit(root: Path = ROOT, documents: list[Path] | None = None) -> tuple[list[dict[str, str]], bool]:
    documents = default_documents(root) if documents is None else documents
    rows: list[dict[str, str]] = []
    term_seen: set[str] = set()
    has_failure = False
    evidence_cache = {policy.term: policy.checker(root) for policy in POLICIES}

    for path in documents:
        text = read_claim_surface(path)
        previous_line = ""
        in_forbidden_section = False
        for lineno, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            heading_probe = stripped.strip('",')
            if re.match(r"#+\s+claims\s+still\s+forbidden\b", heading_probe, re.I):
                in_forbidden_section = True
            elif heading_probe.startswith("#") and "claims still forbidden" not in heading_probe.lower():
                in_forbidden_section = False
            row_is_forbidden = "| forbidden |" in line.lower() or "forbidden unless" in line.lower()
            for policy in POLICIES:
                for match in policy.pattern.finditer(line):
                    term_seen.add(policy.term)
                    evidence_ok, evidence_found = evidence_cache[policy.term]
                    combined_line = f"{previous_line} {line}" if previous_line else line
                    offset = len(previous_line) + 1 if previous_line else 0
                    qualified = in_forbidden_section or row_is_forbidden or is_qualified_context(
                        combined_line,
                        offset + match.start(),
                        offset + match.end(),
                    )
                    status = "PASS" if qualified or evidence_ok else "FAIL"
                    if status == "FAIL":
                        has_failure = True
                    disposition = (
                        "qualified blocker/limitation wording"
                        if qualified
                        else ("positive use backed by matching evidence" if evidence_ok else "unqualified positive use without matching evidence")
                    )
                    rows.append(
                        {
                            "status": status,
                            "term": policy.term,
                            "file": rel(path, root),
                            "line": str(lineno),
                            "context": line.strip(),
                            "evidence_required": policy.evidence_required,
                            "evidence_found": evidence_found,
                            "disposition": disposition,
                        }
                    )
            if stripped:
                previous_line = line

    for policy in POLICIES:
        if policy.term in term_seen:
            continue
        _evidence_ok, evidence_found = evidence_cache[policy.term]
        rows.append(
            {
                "status": "PASS",
                "term": policy.term,
                "file": "",
                "line": "",
                "context": "No unqualified positive use found.",
                "evidence_required": policy.evidence_required,
                "evidence_found": evidence_found,
                "disposition": "term absent from audited claim surfaces",
            }
        )

    return rows, has_failure


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fields = [
        "status",
        "term",
        "file",
        "line",
        "context",
        "evidence_required",
        "evidence_found",
        "disposition",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def main() -> int:
    rows, has_failure = audit(ROOT)
    write_csv(OUT, rows)
    print(f"wrote {rel(OUT)}")
    return 1 if has_failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
