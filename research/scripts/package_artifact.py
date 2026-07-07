#!/usr/bin/env python3
"""Package the COPPER conference-readiness artifact without local scratch."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "research"
RESULTS = RESEARCH / "results"
DIST = ROOT / "dist"
ZIP_PATH = DIST / "copper-artifact.zip"
MANIFEST = RESULTS / "artifact_manifest.csv"
PREFLIGHT_PRIVATE = RESULTS / "preflight_baseline_check.csv"
PREFLIGHT_PUBLIC = RESULTS / "preflight_baseline_check_public.csv"


INCLUDE_SUFFIXES = {
    ".py",
    ".sv",
    ".v",
    ".c",
    ".cc",
    ".h",
    ".tcl",
    ".ps1",
    ".sh",
    ".md",
    ".csv",
    ".tex",
    ".bib",
    ".json",
    ".xml",
    ".yml",
    ".yaml",
    ".txt",
    ".rpt",
    ".log",
    ".png",
    ".pdf",
    ".udp",
    ".sha256",
}
EXCLUDE_SUFFIXES = {".dcp", ".wdb", ".vcd", ".saif", ".jou", ".pb", ".zip", ".gz", ".tar"}
EXCLUDE_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".Xil",
    "xsim.dir",
    "m5out",
    "2025.2",
    ".vivado_appdata",
    ".vivado_user",
    "dist",
    "imported_ci",
    "pass_top_tier_before",
    "ppa_ci_before",
    "copper_public_artifact_package_20260620",
    "_vendor",
}
PRIVATE_PATH_PATTERNS = {
    "C:" + "\\Users\\tyboy",
    "C:" + "\\\\Users\\\\tyboy",
    "C:/Users/" + "tyboy",
    "/c/Users/" + "tyboy",
    "home/" + "tyboy",
}
GEM5_SUMMARY_PREFIX = "gem5_arm_ubuntu_fs_"
OPENROAD_FINAL_PHYSICAL = {
    "6_final.def",
    "6_final.spef",
}
ROOT_FILES = {
    "README.md",
    "REPRODUCIBILITY_STATUS.md",
    "requirements.txt",
    "reproduce.py",
    "reproduce.sh",
    "reproduce.ps1",
    "Makefile",
    "Dockerfile",
    "AUDIT.md",
    "AUDIT_REPORT.md",
}

_TRACKED_PATHS: set[str] | None = None


LOCAL_USER = "ty" + "boy"
WIN_USER_RE = rf"C:[\\/]+Users[\\/]+{LOCAL_USER}"
MSYS_USER_RE = rf"/c/Users/{LOCAL_USER}"
HOME_USER_RE = rf"home/{LOCAL_USER}"

PRIVATE_PATH_REPLACEMENTS = [
    (re.compile(WIN_USER_RE + r"[\\/]+AppData[\\/]+Local[\\/]+Temp[\\/]+copper-ci-final-[^,;\s\"]+"), "<local-ci-artifact-extract>"),
    (re.compile(WIN_USER_RE + r"[\\/]+\.cache[\\/]+codex-runtimes[\\/]+codex-primary-runtime[\\/]+dependencies[\\/]+python[\\/]+python\.exe"), "python"),
    (re.compile(WIN_USER_RE), "<local-user-dir>"),
    (re.compile(MSYS_USER_RE), "<local-user-dir>"),
    (re.compile(HOME_USER_RE), "<local-user-dir>"),
]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def tracked_paths() -> set[str]:
    global _TRACKED_PATHS
    if _TRACKED_PATHS is not None:
        return _TRACKED_PATHS
    try:
        proc = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=20,
        )
    except Exception:
        _TRACKED_PATHS = set()
        return _TRACKED_PATHS
    if proc.returncode != 0:
        _TRACKED_PATHS = set()
        return _TRACKED_PATHS
    _TRACKED_PATHS = {line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()}
    return _TRACKED_PATHS


def is_tracked(path: Path) -> bool:
    tracked = tracked_paths()
    return bool(tracked) and rel(path) in tracked


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def contains_private_path(path: Path) -> bool:
    if path.suffix.lower() not in INCLUDE_SUFFIXES and path.name not in {"Makefile", "Dockerfile", "README.md", "requirements.txt", "LICENSE"}:
        return False
    try:
        body = path.read_bytes()
    except OSError:
        return False
    text_candidates: list[str] = []
    for encoding in ("utf-8", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            text_candidates.append(body.decode(encoding, errors="ignore"))
        except (LookupError, UnicodeError):
            continue
    text_candidates.extend(text.replace("\x00", "") for text in list(text_candidates))
    return any(pattern in text for text in text_candidates for pattern in PRIVATE_PATH_PATTERNS)


def text_has_private_path(text: str) -> bool:
    return any(pattern in text for pattern in PRIVATE_PATH_PATTERNS)


def public_text_from_file(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return public_cell(text)


def public_cell(text: str) -> str:
    out = text
    for pattern, replacement in PRIVATE_PATH_REPLACEMENTS:
        out = pattern.sub(replacement, out)
    return out


def write_public_preflight() -> None:
    if not PREFLIGHT_PRIVATE.exists():
        return
    with PREFLIGHT_PRIVATE.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames or []
        rows = [{field: public_cell(row.get(field, "")) for field in fieldnames} for row in reader]
    if not fieldnames:
        return
    with PREFLIGHT_PUBLIC.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def should_include(path: Path) -> tuple[bool, str]:
    rel_parts = set(path.relative_to(ROOT).parts)
    if rel_parts & EXCLUDE_PARTS:
        return False, "excluded scratch/private/build directory"
    if path.suffix.lower() in EXCLUDE_SUFFIXES:
        return False, "excluded heavy or archive artifact"
    if contains_private_path(path):
        return False, "excluded local-only file containing a private absolute path"
    if path.parent == ROOT and path.name not in ROOT_FILES:
        return False, "excluded root-local log or scratch file"
    if path.parts and "external" in path.parts:
        try:
            ext_rel = path.relative_to(ROOT / "external")
        except ValueError:
            ext_rel = None
        ext_text = str(ext_rel).replace("\\", "/") if ext_rel else ""
        if not ext_text.startswith(("mibench_network/", "picorv32/")):
            return False, "excluded external dependency not needed for public package"
        if ext_text.startswith("picorv32/") and ext_text not in {"picorv32/picorv32.v", "picorv32/README.md", "picorv32/COPYING"}:
            return False, "excluded unused PicoRV32 support file"
        if ext_text.startswith("picorv32/"):
            return True, "included minimal PicoRV32 source/license file"
        if path.suffix.lower() not in INCLUDE_SUFFIXES and path.name not in {"LICENSE", "COPYING"}:
            return False, "excluded external file suffix"
    if path.is_relative_to(RESULTS):
        result_parts = path.relative_to(RESULTS).parts
        if any(part.startswith("gem5_") for part in result_parts):
            if len(result_parts) == 1 and path.suffix.lower() == ".csv":
                return True, "included generated gem5 summary/evidence csv"
            if (
                len(result_parts) >= 2
                and result_parts[0].startswith(GEM5_SUMMARY_PREFIX)
                and (path.name.endswith("_summary.csv") or path.name.endswith("_SUMMARY.md"))
                and is_tracked(path)
            ):
                return True, "included public tracked gem5 summary input/report"
            return False, "excluded raw gem5 output tree; summaries are included"
        if (
            len(result_parts) >= 5
            and result_parts[0] == "logs"
            and result_parts[1] == "openroad_postroute"
            and result_parts[3] == "results"
            and result_parts[4] in OPENROAD_FINAL_PHYSICAL
        ):
            return True, "included OpenROAD final physical artifact referenced by post-route evidence"
        return path.suffix.lower() in INCLUDE_SUFFIXES, "included summary/evidence file"
    if path == ZIP_PATH:
        return False, "output zip excluded"
    if path.suffix.lower() in INCLUDE_SUFFIXES or path.name in {"Makefile", "Dockerfile", "README.md", "requirements.txt", "LICENSE"}:
        return True, "included source or reviewer file"
    return False, "suffix not included"


def is_excluded_tree(path: Path) -> bool:
    try:
        rel_parts = set(path.relative_to(ROOT).parts)
    except ValueError:
        return False
    return bool(rel_parts & EXCLUDE_PARTS)


def main() -> int:
    DIST.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_public_preflight()
    entries: list[dict[str, str]] = []
    include_paths: list[Path] = []
    candidates: list[Path] = []
    for name in sorted(ROOT_FILES):
        path = ROOT / name
        if path.exists():
            candidates.append(path)
    for base in (ROOT / ".devcontainer", ROOT / ".github", ROOT / "docs", RESEARCH, ROOT / "tests", ROOT / "external" / "mibench_network", ROOT / "external" / "picorv32"):
        if base.exists():
            candidates.extend(path for path in base.rglob("*") if path.is_file() and not is_excluded_tree(path))
    for path in sorted(set(candidates)):
        if path == MANIFEST:
            continue
        include, note = should_include(path)
        row = {
            "path": rel(path),
            "size_bytes": str(path.stat().st_size),
            "sha256": sha256(path) if include else "",
            "included": "yes" if include else "no",
            "package_path": rel(path) if include else "",
            "notes": note,
        }
        entries.append(row)
        if include:
            include_paths.append(path)
    with MANIFEST.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["path", "size_bytes", "sha256", "included", "package_path", "notes"])
        writer.writeheader()
        writer.writerows(entries)
    if MANIFEST not in include_paths:
        include_paths.append(MANIFEST)
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(set(include_paths)):
            zf.write(path, rel(path))
    print(f"wrote {rel(ZIP_PATH)} with {len(set(include_paths))} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
