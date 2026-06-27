#!/usr/bin/env python3
"""Import downloaded GitHub Actions artifacts into COPPER evidence ledgers."""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import time
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "research" / "results"
IMPORT_ROOT = RESULTS / "imported_ci"
CI_STATUS = RESULTS / "ci_status.csv"
CI_ARTIFACTS = RESULTS / "ci_artifacts_manifest.csv"
CI_FAILURES = RESULTS / "ci_failure_summary.csv"
OPEN_ENVIRONMENTS = {"github_actions", "docker", "codespaces"}

EVIDENCE_CSVS = {
    "toolchain_status.csv",
    "model_tests.csv",
    "baseline_inventory.csv",
    "benchmark_inventory.csv",
    "performance.csv",
    "prefetch_metrics.csv",
    "memory_traffic.csv",
    "ablation.csv",
    "sensitivity.csv",
    "seed_stability.csv",
    "statistical_summary.csv",
    "rtl_compile.csv",
    "rtl_simulation.csv",
    "synthesis.csv",
    "synthesis_overhead.csv",
    "paper_build_status.csv",
    "claim_audit.csv",
    "number_audit.csv",
    "todo_audit.csv",
    "artifact_manifest.csv",
}

GATE_BY_FILE = {
    "toolchain_status.csv": "G1/G2",
    "model_tests.csv": "G3",
    "baseline_inventory.csv": "G8",
    "benchmark_inventory.csv": "G6/G7",
    "performance.csv": "G11",
    "prefetch_metrics.csv": "G10",
    "memory_traffic.csv": "G12",
    "ablation.csv": "G14",
    "sensitivity.csv": "G13",
    "seed_stability.csv": "G17",
    "statistical_summary.csv": "G17",
    "rtl_compile.csv": "G4",
    "rtl_simulation.csv": "G5",
    "synthesis.csv": "G15",
    "synthesis_overhead.csv": "G15",
    "paper_build_status.csv": "G19",
    "claim_audit.csv": "G20",
    "number_audit.csv": "G20",
    "todo_audit.csv": "G20",
    "artifact_manifest.csv": "G18",
    "main.pdf": "G19",
    "copper-artifact.zip": "G18",
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def sanitize(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return cleaned or "artifact"


def unique_dir(base: Path) -> Path:
    if not base.exists():
        return base
    stamp = time.strftime("%Y%m%d_%H%M%S")
    for idx in range(100):
        candidate = base.with_name(f"{base.name}_{stamp}_{idx:02d}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"could not allocate import directory below {base.parent}")


def safe_extract(zip_path: Path, target: Path) -> None:
    root = target.resolve()
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            out = (target / member.filename).resolve()
            if not out.is_relative_to(root):
                raise ValueError(f"unsafe zip member path: {member.filename}")
            if member.is_dir():
                out.mkdir(parents=True, exist_ok=True)
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, out.open("wb") as dst:
                shutil.copyfileobj(src, dst)


def copy_artifact_dir(source: Path, target: Path) -> None:
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        out = target / path.relative_to(source)
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, out)


def import_source(args: argparse.Namespace) -> Path:
    IMPORT_ROOT.mkdir(parents=True, exist_ok=True)
    if args.zip:
        source = Path(args.zip).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(source)
        target = unique_dir(IMPORT_ROOT / sanitize(source.stem))
        target.mkdir(parents=True, exist_ok=True)
        safe_extract(source, target)
        return target
    source = Path(args.artifact_dir).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    target = unique_dir(IMPORT_ROOT / sanitize(source.name))
    target.mkdir(parents=True, exist_ok=True)
    copy_artifact_dir(source, target)
    return target


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def csv_fields(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        return next(reader, [])


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def merge_evidence_csv(imported: Path) -> tuple[bool, str]:
    if imported.name not in EVIDENCE_CSVS:
        return False, "not a canonical evidence CSV"
    canonical = RESULTS / imported.name
    imported_fields = csv_fields(imported)
    if not imported_fields:
        return False, "empty CSV"
    if canonical.exists():
        canonical_fields = csv_fields(canonical)
        if canonical_fields and canonical_fields != imported_fields:
            return False, f"schema mismatch for {imported.name}"
    else:
        canonical_fields = imported_fields
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, ...]] = set()
    for source in (canonical, imported):
        if not source.exists():
            continue
        for row in read_csv(source):
            normalized = {field: row.get(field, "") for field in canonical_fields}
            key = tuple(normalized[field] for field in canonical_fields)
            if key in seen:
                continue
            seen.add(key)
            rows.append(normalized)
    write_csv(canonical, canonical_fields, rows)
    return True, "merged into canonical evidence CSV"


def produced_by_job(path: Path) -> str:
    name = path.name.lower()
    body = "/".join(part.lower() for part in path.parts)
    if "rtl" in body:
        return "rtl"
    if "synth" in body or "yosys" in body:
        return "synth"
    if "paper" in body or name == "main.pdf":
        return "paper"
    if "artifact" in body or name == "copper-artifact.zip":
        return "artifact"
    if "toolchain" in body:
        return "toolchain"
    if "eval" in body or name in {"performance.csv", "prefetch_metrics.csv", "memory_traffic.csv"}:
        return "eval"
    if "audit" in body:
        return "paper-audit"
    if "model" in body or name == "model_tests.csv":
        return "test"
    return "github_actions"


def used_by_gate(path: Path) -> str:
    return GATE_BY_FILE.get(path.name, "G1")


def first_path(imported_files: list[Path], name: str) -> str:
    for path in imported_files:
        if path.name == name:
            return rel(path)
    return ""


def imported_csv_rows(imported_files: list[Path], name: str) -> list[dict[str, str]]:
    for path in imported_files:
        if path.name == name:
            return read_csv(path)
    return []


def open_rows(name: str) -> list[dict[str, str]]:
    return [row for row in read_csv(RESULTS / name) if row.get("environment") in OPEN_ENVIRONMENTS]


def status_from_rows(name: str) -> tuple[str, str]:
    rows = open_rows(name)
    if any(row.get("status") == "PASS" for row in rows):
        return "PASS", f"open-environment PASS row found in {name}"
    if any(row.get("status") == "FAIL" for row in rows):
        return "FAIL", f"open-environment FAIL row found in {name}"
    if any(row.get("status") == "BLOCKED" for row in rows):
        return "BLOCKED", f"open-environment BLOCKED row found in {name}"
    return "MISSING", f"no open-environment rows found in {name}"


def imported_all_pass_status(imported_files: list[Path], name: str) -> tuple[str, str]:
    rows = imported_csv_rows(imported_files, name)
    if not rows:
        return "MISSING", f"{name} was not found in imported artifacts"
    if all(row.get("status") == "PASS" for row in rows):
        return "PASS", f"all imported {name} rows are PASS"
    if any(row.get("status") == "FAIL" for row in rows):
        return "FAIL", f"imported {name} contains FAIL rows"
    return "PARTIAL", f"imported {name} contains non-PASS rows"


def toolchain_status() -> tuple[str, str]:
    rows = open_rows("toolchain_status.csv")
    if not rows:
        return "MISSING", "no open-environment toolchain_status.csv rows found"
    required = {
        "python3",
        "pip",
        "make",
        "gcc",
        "g++",
        "iverilog",
        "vvp",
        "yosys",
        "latexmk",
        "pdflatex",
        "bibtex",
    }
    available = {row.get("tool") for row in rows if row.get("available") == "yes"}
    missing = sorted(required - available)
    if missing:
        return "BLOCKED", "missing required open-source tools: " + ", ".join(missing)
    return "PASS", "required open-source tools found in imported CI toolchain rows"


def synthesis_status() -> tuple[str, str]:
    overhead = [
        row
        for row in read_csv(RESULTS / "synthesis_overhead.csv")
        if row.get("environment") in OPEN_ENVIRONMENTS and row.get("percent_overhead")
    ]
    if overhead:
        return "PASS", "matched open-environment synthesis overhead rows found"
    synth_rows = open_rows("synthesis.csv")
    if any(row.get("status") == "FAIL" for row in synth_rows):
        return "FAIL", "open-environment synthesis FAIL row found"
    if any(row.get("status") == "BLOCKED" for row in synth_rows):
        return "BLOCKED", "open-environment synthesis BLOCKED row found"
    if any(row.get("status") == "PASS" for row in synth_rows):
        return "PARTIAL", "synthesis PASS rows found but matched overhead is missing"
    return "MISSING", "no open-environment synthesis rows found"


def paper_status(imported_files: list[Path]) -> tuple[str, str]:
    status, note = status_from_rows("paper_build_status.csv")
    has_pdf = any(path.name == "main.pdf" for path in imported_files)
    if status == "PASS" and has_pdf:
        return "PASS", "paper_build_status.csv PASS row and main.pdf found"
    if status == "PASS":
        return "PARTIAL", "paper build row passed but main.pdf was not found in imported artifacts"
    return status, note


def audits_status(imported_files: list[Path]) -> tuple[str, str]:
    names = ["claim_audit.csv", "number_audit.csv", "todo_audit.csv"]
    missing = [name for name in names if not imported_csv_rows(imported_files, name)]
    if missing:
        return "MISSING", "missing imported audit CSVs: " + ", ".join(missing)
    bad: list[str] = []
    for name in names:
        rows = imported_csv_rows(imported_files, name)
        if not rows or any(row.get("status") != "PASS" for row in rows):
            bad.append(name)
    if bad:
        return "FAIL", "non-PASS audit rows found in: " + ", ".join(bad)
    return "PASS", "claim, number, and TODO audits are PASS"


def artifact_status(imported_files: list[Path]) -> tuple[str, str]:
    if any(path.name == "copper-artifact.zip" for path in imported_files):
        return "PASS", "dist/copper-artifact.zip found in imported CI artifacts"
    return "MISSING", "dist/copper-artifact.zip not found in imported CI artifacts"


def log_for_step(step: str, imported_files: list[Path]) -> str:
    needles = {
        "make rtl": ("rtl", "iverilog"),
        "make sim": ("vvp", "simulation", "rtl"),
        "make synth": ("synth", "yosys"),
        "make paper": ("paper", "latex"),
        "make check-toolchain": ("toolchain",),
        "make artifact": ("artifact",),
    }.get(step, ())
    for path in imported_files:
        lower = "/".join(part.lower() for part in path.parts)
        if path.suffix.lower() in {".log", ".txt"} and any(needle in lower for needle in needles):
            return rel(path)
    return ""


def first_error(log_path: str, fallback: str) -> str:
    if not log_path:
        return fallback
    path = ROOT / log_path
    if not path.exists():
        return fallback
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        lower = line.lower()
        if any(word in lower for word in ("error", "failed", "missing", "not found", "fatal")):
            return line.strip()[:240]
    for line in text.splitlines():
        if line.strip():
            return line.strip()[:240]
    return fallback


def write_ci_ledgers(imported_dir: Path, imported_files: list[Path], merge_notes: dict[str, str]) -> None:
    artifact_rows = []
    for path in imported_files:
        if path == CI_STATUS or path == CI_ARTIFACTS or path == CI_FAILURES:
            continue
        artifact_rows.append(
            {
                "artifact_name": imported_dir.name,
                "path": rel(path),
                "size_bytes": str(path.stat().st_size),
                "produced_by_job": produced_by_job(path),
                "used_by_gate": used_by_gate(path),
                "notes": merge_notes.get(rel(path), "imported from downloaded GitHub Actions artifact"),
            }
        )
    if not artifact_rows:
        artifact_rows.append(
            {
                "artifact_name": imported_dir.name,
                "path": "",
                "size_bytes": "0",
                "produced_by_job": "github_actions",
                "used_by_gate": "G1",
                "notes": "missing: artifact directory or zip contained no files",
            }
        )
    write_csv(CI_ARTIFACTS, ["artifact_name", "path", "size_bytes", "produced_by_job", "used_by_gate", "notes"], artifact_rows)

    checks = [
        ("toolchain", "make check-toolchain", "G1/G2", toolchain_status()),
        ("test", "make test", "G3", imported_all_pass_status(imported_files, "model_tests.csv")),
        ("eval", "make eval", "G10/G11/G12/G13/G14/G17", ("PASS", "evaluation CSVs are imported") if first_path(imported_files, "performance.csv") else ("MISSING", "performance.csv is missing from imported artifacts")),
        ("rtl", "make rtl", "G4", status_from_rows("rtl_compile.csv")),
        ("sim", "make sim", "G5", status_from_rows("rtl_simulation.csv")),
        ("synth", "make synth", "G15", synthesis_status()),
        ("paper", "make paper", "G19", paper_status(imported_files)),
        ("paper-audit", "make paper-audit", "G20", audits_status(imported_files)),
        ("artifact", "make artifact", "G18", artifact_status(imported_files)),
    ]
    status_rows = []
    failure_rows = []
    for job, step, gate, (status, note) in checks:
        artifact_path = first_path(imported_files, {
            "make check-toolchain": "toolchain_status.csv",
            "make test": "model_tests.csv",
            "make eval": "performance.csv",
            "make rtl": "rtl_compile.csv",
            "make sim": "rtl_simulation.csv",
            "make synth": "synthesis.csv",
            "make paper": "paper_build_status.csv",
            "make paper-audit": "claim_audit.csv",
            "make artifact": "copper-artifact.zip",
        }[step])
        log_path = log_for_step(step, imported_files)
        status_rows.append(
            {
                "job": job,
                "step": step,
                "status": status,
                "duration_sec": "",
                "log_path": log_path,
                "artifact_path": artifact_path,
                "notes": note,
            }
        )
        if status not in {"PASS"}:
            failure_rows.append(
                {
                    "gate": gate,
                    "job": job,
                    "step": step,
                    "status": status,
                    "first_error": first_error(log_path, note),
                    "log_path": log_path,
                    "suggested_fix": "Inspect the imported log/artifact and rerun the GitHub Actions workflow after fixing the failing gate.",
                    "notes": "CI PASS is not claimed for this gate.",
                }
            )
    if not failure_rows:
        failure_rows.append(
            {
                "gate": "ALL",
                "job": "github_actions",
                "step": "imported artifacts",
                "status": "PASS",
                "first_error": "",
                "log_path": "",
                "suggested_fix": "",
                "notes": "All required imported CI evidence checks passed.",
            }
        )
    write_csv(CI_STATUS, ["job", "step", "status", "duration_sec", "log_path", "artifact_path", "notes"], status_rows)
    write_csv(CI_FAILURES, ["gate", "job", "step", "status", "first_error", "log_path", "suggested_fix", "notes"], failure_rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--artifact-dir", help="Downloaded GitHub Actions artifact directory")
    group.add_argument("--zip", help="Downloaded GitHub Actions artifact zip")
    args = parser.parse_args()

    RESULTS.mkdir(parents=True, exist_ok=True)
    imported_dir = import_source(args)
    imported_files = sorted(path for path in imported_dir.rglob("*") if path.is_file())
    merge_notes: dict[str, str] = {}
    for path in imported_files:
        if path.suffix.lower() != ".csv":
            continue
        merged, note = merge_evidence_csv(path)
        if merged:
            merge_notes[rel(path)] = note
    write_ci_ledgers(imported_dir, imported_files, merge_notes)
    print(f"imported {len(imported_files)} files into {rel(imported_dir)}")
    print(f"wrote {rel(CI_STATUS)}, {rel(CI_ARTIFACTS)}, and {rel(CI_FAILURES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
