#!/usr/bin/env python3
"""Materialize the reviewer-facing COPPER public artifact package.

The generated public manifest separates small direct-package artifacts from
large raw evidence. This script copies only the direct-package rows, then adds
the generated manifest metadata files and a package-build summary. Heavy SAIF
artifacts remain external-store-by-hash evidence.
"""

from __future__ import annotations

import csv
import hashlib
import os
import shutil
import stat
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
MANIFEST_CSV = RESULTS / "copper_public_artifact_manifest_20260620.csv"
MANIFEST_MD = RESULTS / "COPPER_PUBLIC_ARTIFACT_MANIFEST_20260620.md"
MANIFEST_SHA256 = RESULTS / "copper_public_artifact_manifest_20260620.sha256"
SUMMARY = RESULTS / "COPPER_PUBLIC_ARTIFACT_PACKAGE_BUILD_20260620.md"
OUT_DIR = RESULTS / "copper_public_artifact_package_20260620"


@dataclass(frozen=True)
class ManifestRow:
    rel: str
    artifact_class: str
    size: int
    sha256: str
    recommendation: str


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def write_text_lf(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def read_manifest() -> list[ManifestRow]:
    rows: list[ManifestRow] = []
    with MANIFEST_CSV.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(
                ManifestRow(
                    rel=row["path"],
                    artifact_class=row["class"],
                    size=int(row["bytes"]),
                    sha256=row["sha256"],
                    recommendation=row["package_recommendation"],
                )
            )
    return rows


def reset_output_dir() -> None:
    out = OUT_DIR.resolve()
    expected_parent = RESULTS.resolve()
    if out.parent != expected_parent or out.name != "copper_public_artifact_package_20260620":
        raise RuntimeError(f"Refusing to reset unexpected package path: {out}")
    if out.exists():
        def clear_readonly(func, path, _exc_info):
            os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
            func(path)

        shutil.rmtree(out, onerror=clear_readonly)
    out.mkdir(parents=True)


def copy_rel(src: Path) -> Path:
    dst = OUT_DIR / src.relative_to(ROOT)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def main() -> None:
    rows = read_manifest()
    include_rows = [r for r in rows if r.recommendation == "include-in-minimal-package"]
    external_rows = [r for r in rows if r.recommendation == "external-store-with-hash"]

    missing: list[str] = []
    mismatches: list[str] = []

    reset_output_dir()

    copied_row_bytes = 0
    for row in include_rows:
        src = (ROOT / row.rel).resolve()
        if not src.exists():
            missing.append(row.rel)
            continue
        dst = copy_rel(src)
        copied_row_bytes += src.stat().st_size
        if sha256(dst) != row.sha256:
            mismatches.append(row.rel)

    metadata_files = [MANIFEST_MD, MANIFEST_CSV, MANIFEST_SHA256]
    copied_metadata: list[str] = []
    for src in metadata_files:
        if not src.exists():
            missing.append(rel(src))
            continue
        dst = copy_rel(src)
        copied_metadata.append(rel(src))
        if sha256(dst) != sha256(src):
            mismatches.append(rel(src))

    expected_files = len(include_rows) + len(copied_metadata) + 1
    actual_files_before_summary = len([p for p in OUT_DIR.rglob("*") if p.is_file()])
    status = (
        "PASS"
        if not missing
        and not mismatches
        and actual_files_before_summary + 1 == expected_files
        else "FAIL"
    )

    lines = [
        "# COPPER Public Artifact Package Build",
        "",
        "Date: 2026-06-20",
        "",
        "Purpose: materialize the generated COPPER public artifact manifest into a compact local reviewer-facing package tree. This is an artifact-portability check, not a claim of top-tier acceptance and not the exact contents of `dist/copper-artifact.zip`.",
        "",
        "## Package Build Summary",
        "",
        f"- Manifest rows read: {len(rows):,}",
        f"- Direct-package rows copied: {len(include_rows):,}",
        f"- Direct-package row bytes copied: {copied_row_bytes:,}",
        f"- Generated metadata files copied: {len(copied_metadata) + 1:,}",
        f"- Package files present: {expected_files:,}",
        f"- Heavy external-store rows not copied: {len(external_rows):,}",
        f"- Missing files: {len(missing):,}",
        f"- Hash mismatches: {len(mismatches):,}",
        f"- Output directory: `{rel(OUT_DIR)}`",
        f"- Final zip bundle: `dist/copper-artifact.zip` is built separately by `research/scripts/package_artifact.py` and does not embed this output directory as a nested tree.",
        "",
        "## Generated Metadata Included",
        "",
        "| Path |",
        "|---|",
    ]
    for item in copied_metadata + [rel(SUMMARY)]:
        lines.append(f"| `{item}` |")

    lines.extend(
        [
            "",
            "## External Heavy Evidence",
            "",
            "| Path | Bytes | SHA-256 prefix |",
            "|---|---:|---|",
        ]
    )
    for row in external_rows:
        lines.append(f"| `{row.rel}` | {row.size:,} | `{row.sha256[:16]}` |")

    if missing:
        lines.extend(["", "## Missing Files", "", "| Path |", "|---|"])
        for item in missing:
            lines.append(f"| `{item}` |")

    if mismatches:
        lines.extend(["", "## Hash Mismatches", "", "| Path |", "|---|"])
        for item in mismatches:
            lines.append(f"| `{item}` |")

    lines.extend(["", f"status={status}", ""])
    write_text_lf(SUMMARY, "\n".join(lines))

    summary_copy = copy_rel(SUMMARY)
    if sha256(summary_copy) != sha256(SUMMARY):
        raise RuntimeError("Package summary copy hash mismatch")

    actual_files = len([p for p in OUT_DIR.rglob("*") if p.is_file()])
    if status != "PASS" or actual_files != expected_files:
        raise SystemExit(1)
    print(SUMMARY)


if __name__ == "__main__":
    main()
