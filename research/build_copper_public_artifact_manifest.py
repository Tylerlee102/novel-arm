#!/usr/bin/env python3
"""Build a reviewer-facing public artifact manifest for COPPER.

The full local results tree is intentionally large. This script creates a
smaller manifest of paper-facing documents, source files, and explicitly cited
evidence artifacts with sizes and SHA-256 hashes. It is packaging evidence, not
an acceptance guarantee or a correctness proof.
"""

from __future__ import annotations

import csv
import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
RESULTS = RESEARCH / "results"
OUT_MD = RESULTS / "COPPER_PUBLIC_ARTIFACT_MANIFEST_20260620.md"
OUT_CSV = RESULTS / "copper_public_artifact_manifest_20260620.csv"
OUT_SHA256 = RESULTS / "copper_public_artifact_manifest_20260620.sha256"
OUT_PACKAGE_SUMMARY = RESULTS / "COPPER_PUBLIC_ARTIFACT_PACKAGE_BUILD_20260620.md"
SELF_OUTPUTS = {
    OUT_MD.resolve(),
    OUT_CSV.resolve(),
    OUT_SHA256.resolve(),
    OUT_PACKAGE_SUMMARY.resolve(),
}

SEED_DOCS = [
    RESEARCH / "COPPER_FULL_PAPER.md",
    RESEARCH / "COPPER_FINAL_OUTPUT.md",
    RESEARCH / "COPPER_ARTIFACT_REPRODUCTION_GUIDE.md",
    RESEARCH / "COPPER_ENVIRONMENT_ARTIFACT_MANIFEST_20260619.md",
    RESULTS / "COPPER_TOP_TIER_GAP_TRACKER_20260619.md",
    RESULTS / "COPPER_CLAIM_EVIDENCE_MATRIX_20260617.md",
    RESULTS / "COPPER_TOP_TIER_GATE_AUDIT_20260617.md",
    RESULTS / "COPPER_ARTIFACT_AUDIT_20260616.md",
]

EXPLICIT_EVIDENCE = [
    RESULTS / "copper_clpd_sram_workload_activity_saif_power.rpt",
    RESULTS / "copper_clpd_sram_tcp_process_activity_saif_power.rpt",
    RESULTS / "COPPER_TCP_PROCESS_CLPD_ACTIVITY_POWER_20260620.md",
    RESULTS / "COPPER_CONFERENCE_DRAFT_REVIEW.pdf",
    RESULTS / "copper_prefetch_traffic_overhead_20260616.csv",
    RESULTS / "figures" / "COPPER_APP_FIGURE_INDEX_20260616.md",
    RESULTS / "figures" / "copper_app_runtime_delta.png",
    RESULTS / "figures" / "copper_app_runtime_delta.svg",
    RESULTS / "figures" / "copper_app_full_baseline_runtime.png",
    RESULTS / "figures" / "copper_app_full_baseline_runtime.svg",
    RESULTS / "figures" / "copper_app_ctlw_reduction.png",
    RESULTS / "figures" / "copper_app_ctlw_reduction.svg",
    RESULTS / "figures" / "copper_app_bus_overhead.png",
    RESULTS / "figures" / "copper_app_bus_overhead.svg",
    RESULTS / "OPENSSL_TCP_PROCESS_METADATA_TOGGLE_BOUND_20260620.md",
    RESULTS / "OPENSSL_TCP_PROCESS_SCALE_PORTFOLIO_20260620.md",
    RESULTS / "OPENSSL_CLI_TLS_PAIR_FEASIBILITY_20260620.md",
    RESULTS / "COPPER_ROCCA_CLPD_COMMIT_ADAPTER_RTL_SUMMARY.md",
    RESULTS / "COPPER_CAVI_AUTHORITY_ISSUE_GATE_RTL_SUMMARY.md",
    RESULTS / "copper_cavi_authority_issue_gate_xsim_20260620.log",
    RESULTS / "copper_cavi_authority_issue_gate_synth.log",
    RESULTS / "copper_cavi_authority_issue_gate_utilization.rpt",
    RESULTS / "copper_cavi_authority_issue_gate_timing.rpt",
    RESULTS / "gem5_arm_ubuntu_fs_ossltlstcp_app" / "ossltlstcp_TCP_NETNS_PROCESS_SCALE2_FS_SUMMARY.md",
    RESULTS / "gem5_arm_ubuntu_fs_ossltlstcp_app" / "ossltlstcp_tcp_netns_process_scale2_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_ossltlstcp_app" / "ossltlstcp_TCP_NETNS_PROCESS_SCALE3_FS_SUMMARY.md",
    RESULTS / "gem5_arm_ubuntu_fs_ossltlstcp_app" / "ossltlstcp_tcp_netns_process_scale3_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_mibench_patricia_app" / "MIBENCH_PATRICIA_PATRICIA_PREPROBE_FS_SUMMARY.md",
    RESULTS / "gem5_arm_ubuntu_fs_mibench_patricia_app" / "mibench_patricia_patricia_preprobe_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_mibench_patricia_app" / "MIBENCH_PATRICIA_PATRICIA_SMALL2048_FS_SUMMARY.md",
    RESULTS / "gem5_arm_ubuntu_fs_mibench_patricia_app" / "mibench_patricia_patricia_small2048_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_mibench_patricia_app" / "MIBENCH_PATRICIA_PATRICIA_SMALL8192_FS_SUMMARY.md",
    RESULTS / "gem5_arm_ubuntu_fs_mibench_patricia_app" / "mibench_patricia_patricia_small8192_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_mibench_patricia_app" / "MIBENCH_PATRICIA_PATRICIA_LARGE12288_FS_SUMMARY.md",
    RESULTS / "gem5_arm_ubuntu_fs_mibench_patricia_app" / "mibench_patricia_patricia_large12288_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_mibench_patricia_app" / "MIBENCH_PATRICIA_PATRICIA_LARGE12288_SEED1_FS_SUMMARY.md",
    RESULTS / "gem5_arm_ubuntu_fs_mibench_patricia_app" / "mibench_patricia_patricia_large12288_seed1_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_pcre2_app" / "pcre2_pcre2_smoke_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_pcre2_app" / "pcre2_pcre2_seed1_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_zstd_app" / "zstd_zstd_tiny_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_zstd_app" / "zstd_zstd_seed1_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_zlib_app" / "zlib_zlib_tiny_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_zlib_app" / "zlib_zlib_seed1_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_sqlite_app" / "sqlite_app_medium_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_sqlite_app" / "sqlite_app_stress_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_medium_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_stress_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_duktape_app" / "duktape_app_medium_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_duktape_app" / "duktape_app_stress_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_yyjson_app" / "yyjson_app_medium_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_yyjson_app" / "yyjson_app_stress_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_jsonsqlite_app" / "jsonsqlite_app_medium_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_jsonsqlite_app" / "jsonsqlite_app_stress_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_cachesvc_app" / "cachesvc_app_small_summary.csv",
    RESULTS / "gem5_arm_ubuntu_fs_cachesvc_app" / "cachesvc_app_medium_key_summary.csv",
    RESULTS / "MIBENCH_PATRICIA_SCALE_PORTFOLIO_20260620.md",
    RESULTS / "mibench_patricia_scale_portfolio_20260620.csv",
    RESULTS / "MIBENCH_PATRICIA_12K_SEED_STABILITY_20260621.md",
    RESULTS / "mibench_patricia_12k_seed_stability_20260621.csv",
    RESULTS / "MIBENCH_PATRICIA_LARGE16384_FEASIBILITY_20260620.md",
    RESULTS / "MIBENCH_PATRICIA_LARGE32768_FEASIBILITY_20260620.md",
    RESULTS / "MIBENCH_PATRICIA_LARGE62721_FEASIBILITY_20260620.md",
    RESULTS / "mibench_patricia_workload_build" / "MIBENCH_PATRICIA_WORKLOAD_BUILD.md",
    ROOT / "external" / "mibench_download" / "network.tar.gz",
    ROOT / "external" / "mibench_network" / "network" / "patricia" / "LICENSE",
    ROOT / "external" / "mibench_network" / "network" / "patricia" / "patricia.c",
    ROOT / "external" / "mibench_network" / "network" / "patricia" / "patricia.h",
    ROOT / "external" / "mibench_network" / "network" / "patricia" / "small.udp",
    ROOT / "external" / "mibench_network" / "network" / "patricia" / "large.udp",
]

STATIC_EXTERNAL_EVIDENCE = [
    (
        "research/results/copper_clpd_sram_tcp_process_activity.saif",
        "heavy_raw_evidence",
        6_798_821,
        "a405e60dfea7150965474680459e9f9c65d7640170aaa1f959bdb477aeae7534",
    ),
    (
        "research/results/copper_clpd_sram_workload_activity.saif",
        "heavy_raw_evidence",
        6_680_592,
        "02ccc7ab1095b5b2937039019607c1f68b69cc41e58ea12b90b6aff5212b9242",
    ),
]
STATIC_EXTERNAL_RELS = {item[0] for item in STATIC_EXTERNAL_EVIDENCE}

SOURCE_EXTS = {
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".py",
    ".ps1",
    ".sh",
    ".sv",
    ".v",
    ".tcl",
    ".xdc",
    ".md",
}
RESULT_EXTS = {".md", ".csv", ".txt", ".log", ".rpt", ".saif", ".svh", ".json", ".png", ".svg", ".pdf"}
HEAVY_EXTS = {".saif", ".dcp", ".vcd"}
SKIP_PARTS = {"__pycache__", "bin", "downloads", "_vendor"}


@dataclass(frozen=True)
class Entry:
    path: Path
    rel: str
    artifact_class: str
    size: int
    sha256: str
    package_recommendation: str


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def normalize_candidate(token: str) -> Path | None:
    token = token.strip().strip(".,;:")
    if not token:
        return None
    if "\n" in token or "\r" in token or "*" in token:
        return None
    if any(ch.isspace() for ch in token):
        return None
    if token.startswith("C:") or token.startswith("http:") or token.startswith("https:"):
        return None
    if "copper_public_artifact_package_20260620" in token:
        return None
    if token.startswith("research/") or token.startswith("research\\"):
        return (ROOT / token).resolve()
    if token.startswith("external/") or token.startswith("external\\"):
        return None
    return None


def referenced_paths() -> set[Path]:
    refs: set[Path] = set()
    docs = [doc for doc in SEED_DOCS if doc.exists()]
    for doc in docs:
        body = doc.read_text(encoding="utf-8", errors="replace")
        for token in re.findall(r"`([^`]+)`", body):
            path = normalize_candidate(token)
            if path is not None:
                refs.add(path)
    return refs


def source_paths() -> set[Path]:
    paths: set[Path] = set()
    for path in RESEARCH.iterdir():
        if path.is_file() and path.suffix.lower() in SOURCE_EXTS:
            paths.add(path.resolve())
    return paths


def classify(path: Path, seed_docs: set[Path]) -> str:
    suffix = path.suffix.lower()
    if path.resolve() in seed_docs:
        return "paper_or_reproduction_doc"
    if is_under(path, RESULTS):
        if suffix in HEAVY_EXTS:
            return "heavy_raw_evidence"
        if suffix in {".rpt", ".log"}:
            return "tool_report_or_log"
        if suffix in {".csv", ".json", ".svh"}:
            return "derived_table_or_config"
        return "measured_summary"
    if suffix in {".sv", ".v", ".xdc", ".tcl"}:
        return "rtl_or_tool_flow_source"
    if suffix in {".c", ".cc", ".cpp", ".h", ".hpp"}:
        return "workload_source"
    if suffix in {".py", ".ps1", ".sh"}:
        return "reproduction_script"
    return "source_or_note"


def recommendation(path: Path, artifact_class: str) -> str:
    suffix = path.suffix.lower()
    if suffix in HEAVY_EXTS:
        return "external-store-with-hash"
    if artifact_class == "tool_report_or_log" and path.stat().st_size > 1_000_000:
        return "external-store-with-hash"
    return "include-in-minimal-package"


def collect_entries() -> tuple[list[Entry], list[str], list[str]]:
    seed_doc_set = {doc.resolve() for doc in SEED_DOCS if doc.exists()}
    missing = [rel(doc) for doc in SEED_DOCS if not doc.exists()]
    candidates = set(seed_doc_set)
    candidates |= source_paths()
    for path in EXPLICIT_EVIDENCE:
        if path.exists():
            candidates.add(path.resolve())
        else:
            missing.append(rel(path))

    for path in referenced_paths():
        rel_path = rel(path) if is_under(path, ROOT) else str(path)
        if rel_path in STATIC_EXTERNAL_RELS:
            continue
        if not path.exists():
            missing.append(rel_path)
            continue
        if path.is_file() and (path.suffix.lower() in RESULT_EXTS or not is_under(path, RESULTS)):
            candidates.add(path.resolve())

    filtered: set[Path] = set()
    skipped_dirs: list[str] = []
    for path in candidates:
        if path.resolve() in SELF_OUTPUTS:
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.is_dir():
            skipped_dirs.append(rel(path))
            continue
        if not path.exists():
            missing.append(rel(path) if is_under(path, ROOT) else str(path))
            continue
        filtered.add(path)

    entries: list[Entry] = []
    for path in sorted(filtered, key=rel):
        artifact_class = classify(path, seed_doc_set)
        entries.append(
            Entry(
                path=path,
                rel=rel(path),
                artifact_class=artifact_class,
                size=path.stat().st_size,
                sha256=sha256(path),
                package_recommendation=recommendation(path, artifact_class),
            )
        )
    present = {entry.rel for entry in entries}
    for rel_path, artifact_class, size, digest in STATIC_EXTERNAL_EVIDENCE:
        if rel_path not in present:
            entries.append(
                Entry(
                    path=(ROOT / rel_path),
                    rel=rel_path,
                    artifact_class=artifact_class,
                    size=size,
                    sha256=digest,
                    package_recommendation="external-store-with-hash",
                )
            )
    entries.sort(key=lambda entry: entry.rel)
    return entries, sorted(set(missing)), sorted(set(skipped_dirs))


def main() -> None:
    entries, missing, skipped_dirs = collect_entries()

    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "path",
                "class",
                "bytes",
                "sha256",
                "package_recommendation",
            ],
        )
        writer.writeheader()
        for entry in entries:
            writer.writerow(
                {
                    "path": entry.rel,
                    "class": entry.artifact_class,
                    "bytes": entry.size,
                    "sha256": entry.sha256,
                    "package_recommendation": entry.package_recommendation,
                }
            )

    OUT_SHA256.write_text(
        "".join(f"{entry.sha256}  {entry.rel}\n" for entry in entries),
        encoding="utf-8",
    )

    by_class: dict[str, list[Entry]] = defaultdict(list)
    by_recommendation: dict[str, list[Entry]] = defaultdict(list)
    for entry in entries:
        by_class[entry.artifact_class].append(entry)
        by_recommendation[entry.package_recommendation].append(entry)

    include_bytes = sum(e.size for e in by_recommendation["include-in-minimal-package"])
    external_bytes = sum(e.size for e in by_recommendation["external-store-with-hash"])
    largest = sorted(entries, key=lambda e: e.size, reverse=True)[:12]

    status = "PASS" if not missing else "MISSING"
    lines = [
        "# COPPER Public Artifact Manifest",
        "",
        "Date: 2026-06-20",
        "",
        "Purpose: define a practical reviewer-facing artifact package for the current COPPER paper state. This generated manifest lists paper-facing documents, source/reproduction files, and explicitly cited evidence artifacts with sizes and SHA-256 hashes. It does not claim top-tier acceptance or replace the full local results tree.",
        "",
        "## Package Summary",
        "",
        f"- Manifest entries: {len(entries):,}",
        f"- Missing referenced files: {len(missing):,}",
        f"- Minimal-package bytes: {include_bytes:,}",
        f"- External-store bytes: {external_bytes:,}",
        f"- CSV manifest: `{rel(OUT_CSV)}`",
        f"- SHA-256 manifest: `{rel(OUT_SHA256)}`",
        "",
        "## Class Summary",
        "",
        "| Class | Files | Bytes |",
        "|---|---:|---:|",
    ]
    for klass in sorted(by_class):
        rows = by_class[klass]
        lines.append(f"| {klass} | {len(rows):,} | {sum(e.size for e in rows):,} |")

    lines.extend(
        [
            "",
            "## Packaging Recommendation",
            "",
            "| Recommendation | Files | Bytes | Meaning |",
            "|---|---:|---:|---|",
        ]
    )
    meaning = {
        "include-in-minimal-package": "Small or central artifacts that should be copied directly into a public package.",
        "external-store-with-hash": "Large raw artifacts that should be hosted separately or made optional, with this manifest providing hashes.",
    }
    for rec in sorted(by_recommendation):
        rows = by_recommendation[rec]
        lines.append(f"| {rec} | {len(rows):,} | {sum(e.size for e in rows):,} | {meaning[rec]} |")

    lines.extend(
        [
            "",
            "## Largest Entries",
            "",
            "| Path | Class | Bytes | Recommendation | SHA-256 prefix |",
            "|---|---|---:|---|---|",
        ]
    )
    for entry in largest:
        lines.append(
            f"| `{entry.rel}` | {entry.artifact_class} | {entry.size:,} | "
            f"{entry.package_recommendation} | `{entry.sha256[:16]}` |"
        )

    if missing:
        lines.extend(["", "## Missing References", "", "| Path |", "|---|"])
        for item in missing:
            lines.append(f"| `{item}` |")

    if skipped_dirs:
        lines.extend(
            [
                "",
                "## Directory References Not Expanded",
                "",
                "The following referenced directories are intentionally not expanded into the minimal package manifest; representative summaries and hashes are preferred over raw full-run dumps.",
                "",
                "| Directory |",
                "|---|",
            ]
        )
        for item in skipped_dirs:
            lines.append(f"| `{item}` |")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The manifest is generated from the current claim matrix, reproduction guide, final output, full paper, and top-level research source files.",
            "- It intentionally separates direct-package files from optional heavy raw evidence.",
            "- Generated public-manifest and package-build output files are excluded from the hashed entry table to avoid self-referential checksums.",
            "- A public artifact release should copy the direct-package files, preserve relative paths, and either host or omit heavy raw evidence according to reviewer artifact-size limits.",
            "- The full local `research/results` tree is still the authoritative internal evidence store; this file is a packaging map.",
            "",
            f"status={status}",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(OUT_MD)
    if missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
