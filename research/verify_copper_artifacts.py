#!/usr/bin/env python3
"""Audit the local COPPER paper artifacts for required evidence strings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "COPPER_ARTIFACT_AUDIT_20260616.md"


@dataclass
class Check:
    name: str
    status: bool
    detail: str


def text(path: Path) -> str:
    body = path.read_bytes()
    if b"\x00" in body[:200]:
        return body.decode("utf-16", errors="replace")
    return body.decode("utf-8", errors="replace")


def contains(path: Path, needles: list[str]) -> Check:
    if not path.exists():
        return Check(str(path.relative_to(ROOT)), False, "missing")
    body = text(path)
    missing = [needle for needle in needles if needle not in body]
    return Check(
        str(path.relative_to(ROOT)),
        not missing,
        "ok" if not missing else "missing: " + ", ".join(missing),
    )


def min_bytes(path: Path, minimum: int) -> Check:
    if not path.exists():
        return Check(str(path.relative_to(ROOT)), False, "missing")
    size = path.stat().st_size
    return Check(
        str(path.relative_to(ROOT)),
        size >= minimum,
        f"bytes={size}" if size >= minimum else f"too small: bytes={size}",
    )


def pdf_check(path: Path) -> Check:
    if not path.exists():
        return Check(str(path.relative_to(ROOT)), False, "missing")
    reader = PdfReader(str(path))
    body = "\n".join(page.extract_text() or "" for page in reader.pages)
    # The PDF/DOCX packaging pass is intentionally deferred while evidence is
    # still changing. Claim freshness is enforced against Markdown/CSV-derived
    # reports below; the PDF check remains a structural sanity check.
    needles = [
        "Olden AArch64 full-system",
        "AMPM reaches -2.465%",
        "-3.909% medium",
        "DCPT reaches -5.742%",
        "A 2026-06-16/17 public-application stress refresh",
        "SPP is the best ordinary address-stream baseline",
        "zero target-witness evictions",
        "90.706%",
        "15 engine-seed",
        "OoO-LSQ proof",
        "TLB/coherence",
        "+6.898",
        "Vivado RTL",
        "WNS 0.362 ns",
    ]
    missing = [needle for needle in needles if needle not in body]
    ok = len(reader.pages) >= 7 and not missing
    detail = f"pages={len(reader.pages)}, chars={len(body)}"
    if missing:
        detail += "; missing: " + ", ".join(missing)
    return Check(str(path.relative_to(ROOT)), ok, detail)


def main() -> None:
    checks = [
        pdf_check(RESULTS / "COPPER_CONFERENCE_DRAFT_REVIEW.pdf"),
        contains(
            ROOT / "research" / "COPPER_FULL_PAPER.md",
            [
                "COPPER is a safe authority mechanism",
                "AMPM reaches -2.465% small / -3.909% medium",
                "SPP is the best ordinary address-stream baseline on all 12 points",
                "not a replacement for the best address-stream prefetcher",
                "18.8% lower proxy pollution score",
                "Across the weight-sensitivity sweep",
            ],
        ),
        contains(
            ROOT / "research" / "COPPER_FINAL_OUTPUT.md",
            [
                "public Olden",
                "Publish-worthiness | 8/10 focused venue, 7/10 top-tier today",
                "Conventional prefetchers beat it.",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_olden_suite" / "OLDEN_BUILTIN_BASELINES.md",
            [
                "| medium randomized subset | ampm | -3.909%",
                "| medium randomized subset | indirect | -0.480%",
                "| medium randomized subset | isb | -0.695%",
                "| medium randomized subset | copper_clpd64k_peb | -2.616%",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_olden_suite" / "OLDEN_BISORT_FINGERPRINT_VALIDATION.md",
            [
                "Fingerprints match baseline vs COPPER: yes",
                "count",
                "histogram hash",
                "Translation faults",
            ],
        ),
        contains(
            RESULTS / "COPPER_CLPD_SRAM_SYNTH_SUMMARY.md",
            [
                "64K",
                "routed",
                "260",
                "0.362 ns",
            ],
        ),
        contains(
            ROOT / "research" / "COPPER_VIVADO_SUMMARY.md",
            [
                "2026-06-15",
                "errors=0",
                "64K-entry CLPD out-of-context place-and-route",
            ],
        ),
        contains(
            RESULTS / "COPPER_PRIOR_ART_UPDATE_20260615.md",
            [
                "to the best of public knowledge",
                "Dependence-Based Prefetching",
                "Augury",
                "GoFetch",
            ],
        ),
        contains(
            RESULTS / "COPPER_PRIOR_ART_UPDATE_20260616.md",
            [
                "SplittingSecrets",
                "CHERI-picking",
                "First public hardware DMP authority mechanism",
                "Novelty Risk",
            ],
        ),
        contains(
            RESULTS / "COPPER_PRIOR_ART_DELTA_20260617.md",
            [
                "ICP: Exploiting Instruction Correlation",
                "SPP wins raw speed on all eight public application points",
                "novelty_risk=3/10",
                "to the best of public knowledge",
            ],
        ),
        contains(
            RESULTS / "COPPER_PRIOR_ART_REFRESH_20260619.md",
            [
                "Improved Prefetching Techniques for Linked Data Structures",
                "Okapi",
                "US9886385B1",
                "Committed-source-word DMP authority invariant",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "COPPER_READINESS_AUDIT_20260615.md",
            [
                "Novelty risk | 3/10",
                "Publish-worthiness | 7/10",
                "AMPM | -3.909%",
            ],
        ),
        contains(
            RESULTS / "COPPER_READINESS_AUDIT_20260616.md",
            [
                "official GAPBS AArch64 full-system scaling",
                "Backend proof path",
                "Focused-conference plausible; top-tier not guaranteed",
                "medium/stress SQLite/Lua/Duktape seed portfolio",
                "yyjson medium/stress",
                "OoO-LSQ proof-contract checker",
                "TLB/coherence",
                "contract checker",
                "RTL filter",
            ],
        ),
        contains(
            RESULTS / "COPPER_CLAIM_EVIDENCE_MATRIX_20260617.md",
            [
                "C1 | COPPER/SCOOP is plausibly novel",
                "C10 | The current package is focused-conference plausible but not guaranteed top-tier",
                "TLB/coherence authority contract",
                "matching TLB/coherence RTL filter",
                "COPPER_ENERGY_POLLUTION_SCORECARD_20260617.md",
                "COPPER_DRAM_ENERGY_SCORECARD_20260618.md",
                "COPPER_MCPAT_SENSITIVITY_20260618.md",
                "COPPER_RTL_POWER_PROXY_20260618.md",
                "COPPER_CLPD_ACTIVITY_POWER_20260619.md",
                "COPPER_WORKLOAD_CLPD_ACTIVITY_POWER_20260619.md",
                "COPPER_TCP_PROCESS_CLPD_ACTIVITY_POWER_20260620.md",
                "COPPER_ROCCA_CLPD_COMMIT_ADAPTER_RTL_SUMMARY.md",
                "OPENSSL_TCP_PROCESS_METADATA_TOGGLE_BOUND_20260620.md",
                "OSSLSPEED_APP_SMOKE_FS_SUMMARY.md",
                "OSSLTLSSOCKET_SOCKET_SMOKE_FS_SUMMARY.md",
                "MIBENCH_PATRICIA_PATRICIA_SMALL8192_FS_SUMMARY.md",
                "MIBENCH_PATRICIA_PATRICIA_LARGE12288_FS_SUMMARY.md",
                "MIBENCH_PATRICIA_PATRICIA_LARGE12288_SEED1_FS_SUMMARY.md",
                "MIBENCH_PATRICIA_12K_SEED_STABILITY_20260621.md",
                "MIBENCH_PATRICIA_SCALE_PORTFOLIO_20260620.md",
                "PCRE2_PCRE2_SMOKE_FS_SUMMARY.md",
                "PCRE2_REGEX_SEED_STABILITY_20260620.md",
                "LIBXML2_XML_TINY_FULL_FS_SUMMARY.md",
                "LIBARCHIVE_TAR_TINY_FULL_FS_SUMMARY.md",
                "ZSTD_ZSTD_TINY_FS_SUMMARY.md",
                "ZLIB_ZLIB_TINY_FS_SUMMARY.md",
                "COMPRESSION_LIBRARY_SEED_STABILITY_20260620.md",
                "OPENSSL_TCP_LOOPBACK_FEASIBILITY_20260619.md",
                "ossltlstcp_TCP_NETNS_STRICT_FS_SUMMARY.md",
                "ossltlstcp_TCP_NETNS_PROCESS_KEY1_FS_SUMMARY.md",
                "OPENSSL_TCP_PROCESS_METADATA_TOGGLE_BOUND_20260620.md",
                "OPENSSL_TCP_PROCESS_SEED_STABILITY_20260620.md",
                "ossltlstcp_TCP_FALLBACK_PROBE_FS_SUMMARY.md",
                "COPPER_PUBLIC_ARTIFACT_MANIFEST_20260620.md",
                "COPPER_PUBLIC_ARTIFACT_PACKAGE_BUILD_20260620.md",
                "SQLITE_SPEEDTEST1_SPEEDTEST1_JSON_SMOKE_SIZE1_FS_SUMMARY.md",
                "SQLITE_SPEEDTEST1_SPEEDTEST1_STAR_SMOKE_SIZE1_FS_SUMMARY.md",
                "SQLITE_SPEEDTEST1_SPEEDTEST1_ORM_SMOKE_SIZE1_FS_SUMMARY.md",
                "SQLITE_SPEEDTEST1_COMPONENTS_20260619.md",
                "No row justifies saying the idea is guaranteed",
            ],
        ),
        contains(
            RESULTS / "COPPER_TOP_TIER_GATE_AUDIT_20260617.md",
            [
                "FOCUSED_CONFERENCE_READY__TOP_TIER_NEEDS_MORE_EVIDENCE",
                "NEAR_MISS_NOT_GUARANTEED",
                "SPEC-like application or production-service/production-TCP-TLS/standard-crypto-benchmark campaign",
            ],
        ),
        contains(
            ROOT / "research" / "COPPER_ARTIFACT_REPRODUCTION_GUIDE.md",
            [
                "COPPER Artifact Reproduction Guide",
                "Artifact audit line:",
                "artifact checks.",
                "research\\run_pcre2_regex_app_fs.sh",
                "research\\run_libxml2_xml_app_fs.sh",
                "research\\run_libarchive_tar_app_fs.sh",
                "research\\run_zstd_app_fs.sh",
                "research\\run_zlib_app_fs.sh",
                "research\\run_openssl_tls_socket_fs.sh",
                "research\\run_mibench_patricia_fs.sh",
                "ossltlstcp_TCP_NETNS_STRICT_FS_SUMMARY.md",
                "ossltlstcp_TCP_NETNS_PROCESS_KEY1_FS_SUMMARY.md",
                "COPPER_TCP_PROCESS_CLPD_ACTIVITY_POWER_20260620.md",
                "OPENSSL_TCP_PROCESS_METADATA_TOGGLE_BOUND_20260620.md",
                "OPENSSL_TCP_PROCESS_SEED_STABILITY_20260620.md",
                "ossltlstcp_TCP_FALLBACK_PROBE_FS_SUMMARY.md",
                "research\\run_openssl_cli_fixed_fs.ps1",
                "research\\run_copper_rocca_clpd_commit_adapter_xsim.ps1",
                "research\\run_copper_cavi_authority_issue_gate_xsim.ps1",
                "COPPER_CAVI_AUTHORITY_ISSUE_GATE_RTL_SUMMARY.md",
                "research\\run_sqlite_speedtest1_fs.sh",
                "SQLITE_SPEEDTEST1_COMPONENTS_20260619.md",
                "ZSTD_ZSTD_TINY_FS_SUMMARY.md",
                "ZLIB_ZLIB_TINY_FS_SUMMARY.md",
                "LIBXML2_XML_TINY_FULL_FS_SUMMARY.md",
                "LIBARCHIVE_TAR_TINY_FULL_FS_SUMMARY.md",
                "PCRE2_REGEX_SEED_STABILITY_20260620.md",
                "MIBENCH_PATRICIA_PATRICIA_SMALL8192_FS_SUMMARY.md",
                "MIBENCH_PATRICIA_PATRICIA_LARGE12288_FS_SUMMARY.md",
                "MIBENCH_PATRICIA_PATRICIA_LARGE12288_SEED1_FS_SUMMARY.md",
                "MIBENCH_PATRICIA_12K_SEED_STABILITY_20260621.md",
                "MIBENCH_PATRICIA_SCALE_PORTFOLIO_20260620.md",
                "COMPRESSION_LIBRARY_SEED_STABILITY_20260620.md",
                "COPPER_PUBLIC_ARTIFACT_MANIFEST_20260620.md",
                "COPPER_PUBLIC_ARTIFACT_PACKAGE_BUILD_20260620.md",
                "Worst SPP+COPPER slack gap versus SPP: 0.294 percentage points.",
                "status=PASS",
            ],
        ),
        contains(
            ROOT / "research" / "aarch64_pcre2_regex_workload.c",
            [
                "pcre2_compile_8",
                "pcre2_match_8",
                "PCRE2_COPPER_RESULT",
            ],
        ),
        contains(
            RESULTS / "pcre2_regex_workload_build" / "PCRE2_REGEX_WORKLOAD_BUILD.md",
            [
                "PCRE2 Regex Workload AArch64 Build",
                "PCRE2 8-bit regex compiler and matcher",
                "build_status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_pcre2_app" / "PCRE2_PCRE2_SMOKE_FS_SUMMARY.md",
            [
                "public PCRE2 8-bit regex compiler and matcher",
                "Naive DMP CTLW misses: 9406; COPPER CLPD-64K+PEB CTLW misses: 62; reduction: 99.3%",
                "SPP+COPPER slack CTLW misses: 79; reduction versus naive DMP: 99.2%",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_pcre2_app" / "PCRE2_PCRE2_SEED1_FS_SUMMARY.md",
            [
                "public PCRE2 8-bit regex compiler and matcher",
                "Input tag: `pcre2_seed1`.",
                "Naive DMP CTLW misses: 9394; COPPER CLPD-64K+PEB CTLW misses: 59; reduction: 99.4%",
                "SPP+COPPER slack CTLW misses: 107; reduction versus naive DMP: 98.9%",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "PCRE2_REGEX_SEED_STABILITY_20260620.md",
            [
                "PCRE2 Regex Seed Stability",
                "PCRE2 seed points: 2.",
                "Distinct per-seed checksums: 2.",
                "Minimum COPPER CTLW reduction versus naive DMP: 99.3%.",
                "Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 98.9%.",
                "COPPER/slack translation faults across both seed points: 0.",
                "status=PASS",
            ],
        ),
        contains(
            ROOT / "research" / "aarch64_mibench_patricia_workload.c",
            [
                "MIBENCH_PATRICIA_COPPER_RESULT",
                "pat_search",
                "pat_insert",
            ],
        ),
        contains(
            ROOT / "research" / "run_mibench_patricia_fs.sh",
            [
                "native-pre-command-file",
                "small.udp",
                "POLICY_LIST",
                "STAGE_COMPRESSED",
                "gzip -dc",
            ],
        ),
        contains(
            ROOT / "research" / "run_mibench_patricia_large16384_campaign.sh",
            [
                "patricia_large16384",
                "LIMIT=16384",
                "large.udp",
                "STAGE_COMPRESSED=1",
            ],
        ),
        contains(
            ROOT / "research" / "run_mibench_patricia_large12288_campaign.sh",
            [
                "patricia_large12288",
                "LIMIT=12288",
                "large.udp",
                "STAGE_COMPRESSED=1",
            ],
        ),
        contains(
            ROOT / "research" / "run_mibench_patricia_large12288_seed1_campaign.sh",
            [
                "patricia_large12288_seed1",
                "LIMIT=12288",
                "SEED=1",
                "STAGE_COMPRESSED=1",
            ],
        ),
        contains(
            ROOT / "research" / "run_mibench_patricia_large32768_campaign.sh",
            [
                "patricia_large32768",
                "LIMIT=32768",
                "large.udp",
                "STAGE_COMPRESSED=1",
            ],
        ),
        contains(
            ROOT / "research" / "run_mibench_patricia_large62721_campaign.sh",
            [
                "patricia_large62721",
                "LIMIT=62721",
                "large.udp",
                "STAGE_COMPRESSED=1",
            ],
        ),
        contains(
            ROOT / "research" / "run_mibench_patricia_large16384_non_naive_campaign.sh",
            [
                "patricia_large16384",
                "copper_clpd64k_peb spp spp_copper_slack",
                "large.udp",
                "STAGE_COMPRESSED=1",
            ],
        ),
        contains(
            ROOT / "research" / "summarize_mibench_patricia_fs.py",
            [
                "MIBENCH_PATRICIA_COPPER_RESULT",
                "MiBench Patricia",
            ],
        ),
        contains(
            ROOT / "research" / "summarize_mibench_patricia_scale_portfolio.py",
            [
                "MiBench Patricia Scale Portfolio",
                "patricia_small8192",
                "patricia_large12288",
            ],
        ),
        contains(
            ROOT / "research" / "summarize_mibench_patricia_seed_stability.py",
            [
                "MiBench Patricia 12K Seed Stability",
                "patricia_large12288_seed1",
                "Distinct per-seed checksums",
            ],
        ),
        contains(
            ROOT / "research" / "gem5_arm_ubuntu_fs_copper_workload.py",
            [
                "--native-pre-command-file",
                "native_pre_command_file.read_text",
            ],
        ),
        contains(
            RESULTS / "mibench_patricia_workload_build" / "MIBENCH_PATRICIA_WORKLOAD_BUILD.md",
            [
                "MiBench Patricia Workload AArch64 Build",
                "network/patricia",
                "build_status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_mibench_patricia_app" / "MIBENCH_PATRICIA_PATRICIA_PREPROBE_FS_SUMMARY.md",
            [
                "MiBench Patricia AArch64 Full-System Summary",
                "public MiBench network/patricia Patricia trie",
                "Public input records consumed: 128 of limit 128.",
                "Naive DMP CTLW misses: 11992; COPPER CLPD-64K+PEB CTLW misses: 85; reduction: 99.3%.",
                "SPP+COPPER slack CTLW misses: 102; reduction versus naive DMP: 99.1%.",
                "SPP+COPPER slack tick gap versus SPP: -0.026 percentage points.",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_mibench_patricia_app" / "MIBENCH_PATRICIA_PATRICIA_SMALL2048_FS_SUMMARY.md",
            [
                "MiBench Patricia AArch64 Full-System Summary",
                "Input tag: `patricia_small2048`.",
                "Public input records consumed: 2048 of limit 2048.",
                "Naive DMP CTLW misses: 14014; COPPER CLPD-64K+PEB CTLW misses: 181; reduction: 98.7%.",
                "SPP+COPPER slack CTLW misses: 422; reduction versus naive DMP: 97.0%.",
                "SPP+COPPER slack tick gap versus SPP: +0.030 percentage points.",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_mibench_patricia_app" / "MIBENCH_PATRICIA_PATRICIA_SMALL8192_FS_SUMMARY.md",
            [
                "MiBench Patricia AArch64 Full-System Summary",
                "Input tag: `patricia_small8192`.",
                "Public input records consumed: 8192 of limit 8192.",
                "Naive DMP CTLW misses: 16478; COPPER CLPD-64K+PEB CTLW misses: 245; reduction: 98.5%.",
                "SPP+COPPER slack CTLW misses: 379; reduction versus naive DMP: 97.7%.",
                "SPP+COPPER slack tick gap versus SPP: +0.050 percentage points.",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_mibench_patricia_app" / "MIBENCH_PATRICIA_PATRICIA_LARGE12288_FS_SUMMARY.md",
            [
                "MiBench Patricia AArch64 Full-System Summary",
                "Input tag: `patricia_large12288`.",
                "Public input records consumed: 12288 of limit 12288.",
                "Naive DMP CTLW misses: 18454; COPPER CLPD-64K+PEB CTLW misses: 381; reduction: 97.9%.",
                "SPP+COPPER slack CTLW misses: 635; reduction versus naive DMP: 96.6%.",
                "SPP+COPPER slack tick gap versus SPP: +0.035 percentage points.",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_mibench_patricia_app" / "MIBENCH_PATRICIA_PATRICIA_LARGE12288_SEED1_FS_SUMMARY.md",
            [
                "MiBench Patricia AArch64 Full-System Summary",
                "Input tag: `patricia_large12288_seed1`.",
                "Public input records consumed: 12288 of limit 12288.",
                "Naive DMP CTLW misses: 17909; COPPER CLPD-64K+PEB CTLW misses: 398; reduction: 97.8%.",
                "SPP+COPPER slack CTLW misses: 567; reduction versus naive DMP: 96.8%.",
                "SPP+COPPER slack tick gap versus SPP: -0.030 percentage points.",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "MIBENCH_PATRICIA_12K_SEED_STABILITY_20260621.md",
            [
                "MiBench Patricia 12K Seed Stability",
                "MiBench Patricia 12K seed points: 2.",
                "Distinct per-seed checksums: 2.",
                "Minimum COPPER CTLW reduction versus naive DMP: 97.8%.",
                "Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 96.6%.",
                "Worst absolute SPP+COPPER slack tick gap versus SPP: 0.035 percentage points.",
                "COPPER/slack translation faults across both 12K seeds: 0.",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "MIBENCH_PATRICIA_SCALE_PORTFOLIO_20260620.md",
            [
                "MiBench Patricia Scale Portfolio",
                "MiBench Patricia scale points: 4.",
                "Largest public input records consumed: 12288.",
                "Minimum COPPER CTLW reduction versus naive DMP: 97.9%.",
                "Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 96.6%.",
                "Worst absolute SPP+COPPER slack tick gap versus SPP: 0.050 percentage points.",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "MIBENCH_PATRICIA_LARGE16384_FEASIBILITY_20260620.md",
            [
                "MiBench Patricia 16K Feasibility Note",
                "Public input records consumed: 16,384 of limit 16,384.",
                "Final ROI simTicks: 106,061,839,659.",
                "COPPER entered the timed ROI",
                "status=PARTIAL_NEGATIVE_FEASIBILITY",
            ],
        ),
        contains(
            RESULTS / "MIBENCH_PATRICIA_LARGE32768_FEASIBILITY_20260620.md",
            [
                "MiBench Patricia 32K Feasibility Note",
                "Public input records consumed: 32,768 of limit 32,768.",
                "Final ROI simTicks: 222,447,259,404.",
                "status=PARTIAL_NEGATIVE_FEASIBILITY",
            ],
        ),
        contains(
            RESULTS / "MIBENCH_PATRICIA_LARGE62721_FEASIBILITY_20260620.md",
            [
                "MiBench Patricia Full-Large Feasibility Note",
                "Public input records consumed: 62,721 of limit 62,721.",
                "Final ROI simTicks: 417,102,890,922.",
                "status=PARTIAL_NEGATIVE_FEASIBILITY",
            ],
        ),
        contains(
            ROOT / "research" / "aarch64_libxml2_xml_workload.c",
            [
                "xmlReadMemory",
                "xmlDocDumpMemory",
                "LIBXML2_COPPER_RESULT",
            ],
        ),
        contains(
            RESULTS / "libxml2_xml_workload_build" / "LIBXML2_XML_WORKLOAD_BUILD.md",
            [
                "libxml2 XML Workload AArch64 Build",
                "libxml2 XML parser and serializer",
                "build_status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_libxml2_app" / "LIBXML2_XML_TINY_FULL_FS_SUMMARY.md",
            [
                "public libxml2 XML parser and serializer",
                "Input tag: `xml_tiny_full`.",
                "Naive DMP CTLW misses: 12758; COPPER CLPD-64K+PEB CTLW misses: 139; reduction: 98.9%",
                "SPP+COPPER slack CTLW misses: 136; reduction versus naive DMP: 98.9%",
                "slack gap: 0.035 percentage points",
                "status=PASS",
            ],
        ),
        contains(
            ROOT / "research" / "aarch64_libarchive_tar_workload.c",
            [
                "archive_read_open_memory",
                "archive_read_next_header",
                "LIBARCHIVE_COPPER_RESULT",
            ],
        ),
        contains(
            RESULTS / "libarchive_tar_workload_build" / "LIBARCHIVE_TAR_WORKLOAD_BUILD.md",
            [
                "libarchive TAR Workload AArch64 Build",
                "libarchive TAR parser",
                "build_status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_libarchive_app" / "LIBARCHIVE_TAR_TINY_FULL_FS_SUMMARY.md",
            [
                "public libarchive TAR parser",
                "Input tag: `tar_tiny_full`.",
                "Naive DMP CTLW misses: 17091; COPPER CLPD-64K+PEB CTLW misses: 341; reduction: 98.0%",
                "SPP+COPPER slack CTLW misses: 233; reduction versus naive DMP: 98.6%",
                "slack gap: -0.004 percentage points",
                "status=PASS",
            ],
        ),
        contains(
            ROOT / "research" / "aarch64_zstd_workload.c",
            [
                "ZSTD_compress",
                "ZSTD_decompress",
                "ZSTD_COPPER_RESULT",
            ],
        ),
        contains(
            RESULTS / "zstd_workload_build" / "ZSTD_WORKLOAD_BUILD.md",
            [
                "Zstd Workload AArch64 Build",
                "libzstd compression/decompression",
                "build_status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_zstd_app" / "ZSTD_ZSTD_TINY_FS_SUMMARY.md",
            [
                "public libzstd compression and decompression",
                "Naive DMP CTLW misses: 9239; COPPER CLPD-64K+PEB CTLW misses: 49; reduction: 99.5%",
                "SPP+COPPER slack CTLW misses: 51; reduction versus naive DMP: 99.4%",
                "status=PASS",
            ],
        ),
        contains(
            ROOT / "research" / "aarch64_zlib_workload.c",
            [
                "compress2",
                "uncompress",
                "ZLIB_COPPER_RESULT",
            ],
        ),
        contains(
            RESULTS / "zlib_workload_build" / "ZLIB_WORKLOAD_BUILD.md",
            [
                "zlib Workload AArch64 Build",
                "zlib compression/decompression",
                "build_status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_zlib_app" / "ZLIB_ZLIB_TINY_FS_SUMMARY.md",
            [
                "public zlib compression and decompression",
                "Naive DMP CTLW misses: 11336; COPPER CLPD-64K+PEB CTLW misses: 65; reduction: 99.4%",
                "SPP+COPPER slack CTLW misses: 58; reduction versus naive DMP: 99.5%",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "COMPRESSION_LIBRARY_SEED_STABILITY_20260620.md",
            [
                "Compression-Library Seed Stability",
                "Seed/library points: 4.",
                "Distinct library-checksum pairs: 4.",
                "Minimum COPPER CTLW reduction versus naive DMP: 99.4%.",
                "Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 99.4%.",
                "Worst absolute SPP+COPPER slack tick gap versus SPP: 0.183 percentage points.",
                "COPPER/slack translation faults across all seed points: 0.",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "EXPAT_XML_FEASIBILITY_20260620.md",
            [
                "Expat XML Full-System Feasibility Note",
                "not counted as benchmark evidence",
                "status=NOT_COUNTED",
            ],
        ),
        contains(
            ROOT / "research" / "COPPER_ENVIRONMENT_ARTIFACT_MANIFEST_20260619.md",
            [
                "COPPER Environment and Artifact Manifest",
                "Python 3.12.13",
                "vivado v2025.2",
                "external\\gem5\\build\\ARM\\gem5.fast.exe",
                "excluding materialized public package",
                "Materialized public package",
                "Git | Not available in the current PowerShell session",
                "manifest_status=PASS",
            ],
        ),
        contains(
            RESULTS / "COPPER_PUBLIC_ARTIFACT_MANIFEST_20260620.md",
            [
                "COPPER Public Artifact Manifest",
                "Manifest entries:",
                "Missing referenced files: 0",
                "Minimal-package bytes:",
                "External-store bytes: 13,479,413",
                "external-store-with-hash | 2",
                "include-in-minimal-package |",
                "research/results/copper_clpd_sram_tcp_process_activity.saif",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "COPPER_PUBLIC_ARTIFACT_PACKAGE_BUILD_20260620.md",
            [
                "COPPER Public Artifact Package Build",
                "Manifest rows read:",
                "Direct-package rows copied:",
                "Generated metadata files copied: 4",
                "Package files present:",
                "Heavy external-store rows not copied: 2",
                "Missing files: 0",
                "Hash mismatches: 0",
                "status=PASS",
            ],
        ),
        contains(
            ROOT / "research" / "aarch64_openssl_tls_socket_workload.c",
            [
                "socketpair(AF_UNIX, SOCK_STREAM, 0, sv)",
                "SSL_set_fd(client, sv[0])",
                "OPENSSL_TLS_SOCKET_COPPER_RESULT",
            ],
        ),
        contains(
            ROOT / "research" / "aarch64_openssl_tls_tcp_workload.c",
            [
                "socketpair(AF_UNIX, SOCK_STREAM, 0, sv)",
                "CLONE_NEWUSER",
                "CLONE_NEWNET",
                "tcp_loopback_netns",
                "--strict-tcp",
                "--no-netns-loopback",
                "--process-server",
                "fork()",
                "tcp_loopback_netns_process",
                "transport=%s",
                "OPENSSL_TLS_TCP_COPPER_RESULT",
            ],
        ),
        contains(
            ROOT / "research" / "run_openssl_tls_tcp_fs.sh",
            [
                "STRICT_TCP",
                "PROCESS_SERVER",
                "NO_NETNS_LOOPBACK",
                "EXTRA_TCP_ARGS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_ossltlstcp_app" / "ossltlstcp_TCP_NETNS_STRICT_FS_SUMMARY.md",
            [
                "OpenSSL libssl TLS TCP Loopback AArch64 Full-System Summary",
                "Transport modes observed: tcp_loopback_netns.",
                "Naive DMP CTLW misses: 9645; COPPER CLPD-64K+PEB CTLW misses: 221; reduction: 97.7%.",
                "SPP+COPPER slack CTLW misses: 269; reduction versus naive DMP: 97.2%.",
                "All policies used AF_INET TCP loopback inside a private user/network namespace",
                "status=TCP_NETNS_PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_ossltlstcp_app" / "ossltlstcp_TCP_NETNS_PROCESS_KEY1_FS_SUMMARY.md",
            [
                "OpenSSL libssl TLS TCP Loopback AArch64 Full-System Summary",
                "Transport modes observed: tcp_loopback_netns_process.",
                "Naive DMP CTLW misses: 7185; COPPER CLPD-64K+PEB CTLW misses: 111; reduction: 98.5%.",
                "SPP+COPPER slack CTLW misses: 131; reduction versus naive DMP: 98.2%.",
                "All policies used process-separated AF_INET TCP loopback inside a private user/network namespace with a forked TLS server process.",
                "Process-server flag values: 1; process TCP pairs: 5; child failures: 0.",
                "status=TCP_NETNS_PROCESS_PASS",
            ],
        ),
        contains(
            RESULTS / "OPENSSL_TCP_PROCESS_METADATA_TOGGLE_BOUND_20260620.md",
            [
                "OpenSSL TCP Process-Server Metadata Toggle Bound",
                "Selected policy rows: 8",
                "All selected rows use `tcp_loopback_netns_process`: yes.",
                "Translation faults across selected rows: 0.",
                "Matching gem5 DRAM rank-energy rows: found for every selected seed/policy row.",
                "| copper_clpd64k_peb | 4 | 14 | 170,564",
                "| spp_copper_slack | high | 20.0 | 40.0 | 5.0 | 6.818 uJ | 0.1510% | 0.005412% |",
                "maximum normalized metadata bound is 0.1510% of matching DRAM operation energy and 0.005412% of matching total DRAM energy",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "OPENSSL_TCP_PROCESS_SEED_STABILITY_20260620.md",
            [
                "OpenSSL TCP Process-Server Seed Stability",
                "Process-server seed points: 2.",
                "Distinct seed checksums: 2.",
                "Total forked process TCP pairs across policies/seeds: 10.",
                "Child process failures across policies/seeds: 0.",
                "Minimum COPPER CTLW reduction versus naive DMP: 98.5%.",
                "Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 98.1%.",
                "Worst absolute SPP+COPPER slack tick gap versus SPP: 0.130 percentage points.",
                "COPPER/slack translation faults across both seeds: 0.",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_ossltlstcp_app" / "ossltlstcp_TCP_NETNS_PROCESS_SCALE2_FS_SUMMARY.md",
            [
                "OpenSSL libssl TLS TCP Loopback AArch64 Full-System Summary",
                "Input tag: `tcp_netns_process_scale2`.",
                "Naive DMP CTLW misses: 23880; COPPER CLPD-64K+PEB CTLW misses: 385; reduction: 98.4%.",
                "SPP+COPPER slack CTLW misses: 364; reduction versus naive DMP: 98.5%.",
                "Process-server flag values: 1; process TCP pairs: 20; child failures: 0.",
                "status=TCP_NETNS_PROCESS_PASS",
            ],
        ),
        contains(
            RESULTS / "OPENSSL_TCP_PROCESS_SCALE_PORTFOLIO_20260620.md",
            [
                "OpenSSL TCP Process-Server Scale Portfolio",
                "Portfolio points: 4.",
                "Distinct checksums: 4.",
                "Total forked process TCP pairs across policies/points: 70.",
                "Minimum COPPER CTLW reduction versus naive DMP: 98.2%.",
                "Worst absolute SPP+COPPER slack tick gap versus SPP: 0.130 percentage points.",
                "COPPER/slack translation faults across portfolio: 0.",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_ossltlstcp_app" / "ossltlstcp_TCP_NETNS_PROCESS_SCALE3_FS_SUMMARY.md",
            [
                "OpenSSL libssl TLS TCP Loopback AArch64 Full-System Summary",
                "Input tag: `tcp_netns_process_scale3`.",
                "Naive DMP CTLW misses: 39977; COPPER CLPD-64K+PEB CTLW misses: 710; reduction: 98.2%.",
                "SPP+COPPER slack CTLW misses: 591; reduction versus naive DMP: 98.5%.",
                "Process-server flag values: 1; process TCP pairs: 40; child failures: 0.",
                "status=TCP_NETNS_PROCESS_PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_ossltlstcp_app" / "ossltlstcp_TCP_FALLBACK_PROBE_FS_SUMMARY.md",
            [
                "OpenSSL libssl TLS TCP Loopback AArch64 Full-System Summary",
                "Transport modes observed: af_unix_fallback.",
                "Naive DMP CTLW misses: 8839; COPPER CLPD-64K+PEB CTLW misses: 177; reduction: 98.0%.",
                "SPP+COPPER slack CTLW misses: 245; reduction versus naive DMP: 97.2%.",
                "The guest loopback interface was unavailable",
                "status=AF_UNIX_FALLBACK_PASS",
            ],
        ),
        contains(
            ROOT / "research" / "build_openssl_tls_socket_workload_aarch64.py",
            [
                "aarch64_openssl_tls_socket_workload.c",
                "openssl_tls_socket_workload_build",
                "build_status={'PASS' if proc.returncode == 0 else 'FAIL'}",
            ],
        ),
        contains(
            RESULTS / "openssl_tls_socket_workload_build" / "OPENSSL_TLS_SOCKET_WORKLOAD_BUILD.md",
            [
                "OpenSSL TLS Socket Workload AArch64 Build",
                "nonblocking Linux AF_UNIX socketpair",
                "build_status=PASS",
            ],
        ),
        contains(
            ROOT / "research" / "COPPER_AMBA_CHI_ACE_EVENT_MAP_20260619.md",
            [
                "COPPER SARI/CS-SARI AMBA CHI/ACE Event Map",
                "DVM/TLBI or translation-context invalidation",
                "Same-line write by CPU, DMA, coherent I/O, or accelerator",
                "not a complete CHI/ACE/AXI decoder",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "COPPER_TOP_TIER_GAP_TRACKER_20260619.md",
            [
                "COPPER Top-Tier Gap Tracker",
                "SPEC-like or production application campaign",
                "Production OoO/backend-fabric integration",
                "Current audit:",
                "ROPL-LSQ retire guard",
                "ROCCA-to-CLPD commit adapter",
                "CAVI final source-plus-target issue interlock",
                "AMBA-SARI frontdoor",
                "Zstd compression-library full-system evidence",
                "zlib compression-library full-system evidence",
                "libxml2 XML parser/serializer",
                "libarchive TAR parser",
                "COMPRESSION_LIBRARY_SEED_STABILITY_20260620.md",
                "ossltlstcp_TCP_NETNS_STRICT_FS_SUMMARY.md",
                "ossltlstcp_TCP_NETNS_PROCESS_KEY1_FS_SUMMARY.md",
                "COPPER_TCP_PROCESS_CLPD_ACTIVITY_POWER_20260620.md",
                "OPENSSL_TCP_PROCESS_METADATA_TOGGLE_BOUND_20260620.md",
                "OPENSSL_TCP_PROCESS_SEED_STABILITY_20260620.md",
                "ossltlstcp_TCP_FALLBACK_PROBE_FS_SUMMARY.md",
                "FOCUSED_CONFERENCE_READY__TOP_TIER_NEEDS_MORE_EVIDENCE",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "COPPER_AMBA_SARI_FRONTDOOR_RTL_SUMMARY.md",
            [
                "COPPER AMBA-SARI Frontdoor RTL Summary",
                "Directed cases | 10",
                "Randomized cycles | 10,000",
                "Slice LUTs | 8",
                "Worst setup slack | +7.525 ns",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "COPPER_ROCCA_CLPD_COMMIT_ADAPTER_RTL_SUMMARY.md",
            [
                "COPPER ROCCA-to-CLPD Commit Adapter RTL Summary",
                "Retirement-Ordered Clear-wins CLPD Adapter",
                "clear-wins proof commit",
                "Randomized cycles | 20,000",
                "Same-cycle clear-wins blocks | 1,598",
                "Slice LUTs | 4,302",
                "WNS at 10 ns | 1.149 ns",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "COPPER_CAVI_AUTHORITY_ISSUE_GATE_RTL_SUMMARY.md",
            [
                "COPPER CAVI Authority Issue Gate RTL Summary",
                "Commit-Authority Validity Interlock",
                "issue only if the ROCCA/CLPD source proof is valid",
                "Randomized trials | 20,000",
                "Random clear-wins proof suppressions | 2,021",
                "Random target revocation conflicts | 3,996",
                "Slice LUTs | 4,591",
                "WNS at 10 ns | 1.149 ns",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "copper_cavi_authority_issue_gate_xsim_20260620.log",
            [
                "COPPER CAVI authority issue gate completed",
                "directed=14",
                "random=20000",
                "clear_wins=2021",
                "target_revokes=3996",
                "errors=0",
            ],
        ),
        contains(
            RESULTS / "copper_cavi_authority_issue_gate_synth.log",
            [
                "Synthesis finished with 0 errors, 0 critical warnings and 0 warnings.",
                "synth_design completed successfully",
            ],
        ),
        contains(
            RESULTS / "copper_cavi_authority_issue_gate_timing.rpt",
            [
                "All user specified timing constraints are met",
                "1.149",
                "0.148",
            ],
        ),
        contains(
            ROOT / "research" / "copper_cavi_authority_issue_gate.sv",
            [
                "CAVI: Commit-Authority Validity Interlock",
                "dmp_issue_allow",
                "source_gate_allow",
                "target_gate_allow",
            ],
        ),
        contains(
            ROOT / "research" / "copper_cavi_authority_issue_gate_tb.sv",
            [
                "COPPER CAVI authority issue gate completed",
                "TRIALS = 20000",
                "direct queued target remap blocks until drained",
            ],
        ),
        contains(
            RESULTS / "copper_rocca_clpd_commit_adapter_xsim_20260620.log",
            [
                "COPPER ROCCA-CLPD adapter completed",
                "random=20000",
                "clear_wins=1598",
                "errors=0",
            ],
        ),
        contains(
            RESULTS / "copper_rocca_clpd_commit_adapter_synth.log",
            [
                "Synthesis finished with 0 errors, 0 critical warnings and 0 warnings.",
                "synth_design completed successfully",
            ],
        ),
        contains(
            ROOT / "research" / "copper_rocca_clpd_commit_adapter.sv",
            [
                "ROCCA: Retirement-Ordered Clear-wins CLPD Adapter",
                "clear-wins",
                "clpd_commit_ptr_valid",
                "blocked_clear_wins",
            ],
        ),
        contains(
            ROOT / "research" / "copper_rocca_clpd_commit_adapter_tb.sv",
            [
                "COPPER ROCCA-CLPD adapter completed",
                "TRIALS = 20000",
                "compare_clpd",
                "clear_win_seen",
            ],
        ),
        contains(
            RESULTS / "copper_amba_sari_frontdoor_xsim_20260620.log",
            [
                "COPPER AMBA-SARI frontdoor completed",
                "random=10000",
                "errors=0",
            ],
        ),
        contains(
            RESULTS / "COPPER_METADATA_TOGGLE_BOUND_20260619.md",
            [
                "COPPER Metadata Toggle Bound",
                "Learned-proof writes: 40,058",
                "CLPD source-proof reads: 1,407,655",
                "Total charged metadata reads: 1,427,701",
                "high | 20.0 | 40.0 | 5.0 | 37.495 uJ | 0.1801%",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "COPPER_OOO_REPLAY_EXCEPTION_ALIAS_CONTRACT.md",
            [
                "COPPER ROPL Replay/Exception/Alias Contract",
                "Full ROPL contract status: PASS",
                "FULL_ROPL_CONTRACT | 888 | 1 | 0",
                "BUG_NO_REPLAY_GENERATION",
                "BUG_NO_ALIAS_GENERATION",
                "BUG_NO_ORDER_VIOLATION_CLEAR",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "COPPER_ROPL_LSQ_RETIRE_GUARD_RTL_SUMMARY.md",
            [
                "COPPER ROPL-LSQ Retire Guard RTL Summary",
                "Directed hazard cases | 18",
                "Randomized cycles | 20,000",
                "Slice LUTs | 14",
                "Worst setup slack | +6.492 ns",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "copper_ropl_lsq_retire_guard_xsim_20260620.log",
            [
                "COPPER ROPL-LSQ retire guard completed",
                "random=20000",
                "errors=0",
            ],
        ),
        contains(
            RESULTS / "copper_ropl_lsq_retire_guard_top_timing.rpt",
            [
                "All user specified timing constraints are met",
                "6.492",
            ],
        ),
        contains(
            RESULTS / "copper_ropl_lsq_retire_guard_synth.log",
            [
                "Synthesis finished with 0 errors, 0 critical warnings and 0 warnings",
                "synth_design completed successfully",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_osslspeed_app" / "OSSLSPEED_APP_SMOKE_FS_SUMMARY.md",
            [
                "OpenSSL-Speed-Like AArch64 Full-System Summary",
                "fixed benchmark-style buffer sizes",
                "Naive DMP CTLW misses: 16353; COPPER CLPD-64K+PEB CTLW misses: 1257; reduction: 92.3%",
                "SPP+COPPER slack CTLW misses: 1093; reduction versus naive DMP: 93.3%",
                "SPP+COPPER slack tick gap versus SPP: +0.041 percentage points",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "OPENSSL_CLI_FEASIBILITY_20260619.md",
            [
                "OpenSSL CLI Full-System Feasibility Note",
                "OpenSSL 3.0.13 30 Jan 2024",
                "compatibility_status=PASS",
                "official_speed_status=NOT_LOCALLY_TRACTABLE_UNDER_TIMING_GEM5",
                "not counted as a benchmark result",
            ],
        ),
        contains(
            RESULTS / "OPENSSL_CLI_TLS_PAIR_FEASIBILITY_20260620.md",
            [
                "OpenSSL CLI TLS-Pair Feasibility Note",
                "`/usr/bin/openssl`",
                "COPPER_OPENSSL_GUEST_PROBE_DONE",
                "COPPER_OPENSSL_CLI_TLS_PAIR_SERVER_PID",
                "not counted as performance evidence",
                "status=NEGATIVE_FEASIBILITY_RESULT_NOT_BENCHMARK_EVIDENCE",
            ],
        ),
        contains(
            ROOT / "research" / "gem5_arm_ubuntu_fs_copper_workload.py",
            [
                "--native-shell-command-file",
                "native_shell_command_file.read_text",
                "mutually exclusive",
            ],
        ),
        contains(
            ROOT / "research" / "openssl_guest_probe.sh",
            [
                "COPPER_OPENSSL_GUEST_PROBE_START",
                "command -v openssl",
                "COPPER_OPENSSL_GUEST_PROBE_DONE",
            ],
        ),
        contains(
            ROOT / "research" / "openssl_cli_tls_pair_guest.sh",
            [
                "COPPER_OPENSSL_CLI_TLS_PAIR_START",
                "unshare -Urn /bin/sh /tmp/copper_tls_pair_ns.sh",
                "/usr/bin/openssl s_server",
                "/usr/bin/openssl s_client",
                "COPPER_OPENSSL_CLI_TLS_PAIR_RESULT",
            ],
        ),
        contains(
            RESULTS / "OPENSSL_SPEEDLIKE_SEED_STABILITY_20260619.md",
            [
                "OpenSSL-Speed-Like Two-Seed Stability",
                "COPPER CTLW reduction is stable at 92.3% minimum across the two seeds",
                "SPP+COPPER slack CTLW reduction is stable at 92.7% minimum across the two seeds",
                "Worst absolute SPP+COPPER slack gap versus SPP is 0.089 percentage points",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_osslcli_app" / "OSSLCLI_FIXED_64K_FS_SUMMARY.md",
            [
                "Official OpenSSL CLI Fixed-Workload AArch64 Full-System Summary",
                "official Ubuntu ARM64 `openssl` CLI binary",
                "SHA256 agreement: yes",
                "Naive DMP CTLW misses: 15940; COPPER CLPD-64K+PEB CTLW misses: 387; reduction: 97.6%",
                "SPP+COPPER slack CTLW misses: 415; reduction versus naive DMP: 97.4%",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_osslcli_app" / "OSSLCLI_AESCTR_64K_FS_SUMMARY.md",
            [
                "Official OpenSSL CLI AES-CTR Fixed-Workload AArch64 Full-System Summary",
                "official Ubuntu ARM64 `openssl` CLI binary",
                "SHA256 agreement: yes",
                "Native after-command return-code agreement: yes",
                "Naive DMP CTLW misses: 32174; COPPER CLPD-64K+PEB CTLW misses: 1463; reduction: 95.5%",
                "SPP+COPPER slack CTLW misses: 1549; reduction versus naive DMP: 95.2%",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_osslcli_app" / "OSSLCLI_HMAC_64K_FS_SUMMARY.md",
            [
                "Official OpenSSL CLI HMAC-SHA256 Fixed-Workload AArch64 Full-System Summary",
                "official Ubuntu ARM64 `openssl` CLI binary",
                "SHA256 agreement: yes",
                "Native return-code agreement: yes",
                "Naive DMP CTLW misses: 16903; COPPER CLPD-64K+PEB CTLW misses: 524; reduction: 96.9%",
                "SPP+COPPER slack CTLW misses: 435; reduction versus naive DMP: 97.4%",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "OPENSSL_CLI_SEED_STABILITY_20260619.md",
            [
                "Official OpenSSL CLI Multi-Seed Stability",
                "Official OpenSSL CLI SHA256 digest | 3 | 97.2% / 97.5%",
                "Official OpenSSL CLI AES-CTR + digest | 3 | 95.5% / 95.5%",
                "Official OpenSSL CLI HMAC-SHA256 | 3 | 96.9% / 96.9%",
                "Across 9 official CLI seed/workload points, COPPER CTLW reduction is at least 95.5%",
                "Across 9 official CLI seed/workload points, SPP+COPPER slack CTLW reduction is at least 95.2%",
                "Worst absolute SPP+COPPER slack gap versus SPP is 0.294 percentage points",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_osslcli_app" / "OSSLCLI_FIXED_64K_SEED2_FS_SUMMARY.md",
            [
                "Input tag: `fixed_64k_seed2`",
                "SHA256 agreement: yes",
                "Naive DMP CTLW misses: 16044; COPPER CLPD-64K+PEB CTLW misses: 442; reduction: 97.2%",
                "SPP+COPPER slack CTLW misses: 413; reduction versus naive DMP: 97.4%",
                "SPP+COPPER slack tick gap versus SPP: -0.023 percentage points",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_osslcli_app" / "OSSLCLI_AESCTR_64K_SEED2_FS_SUMMARY.md",
            [
                "Input tag: `aesctr_64k_seed2`",
                "Native after-command return-code agreement: yes (0)",
                "Naive DMP CTLW misses: 32212; COPPER CLPD-64K+PEB CTLW misses: 1463; reduction: 95.5%",
                "SPP+COPPER slack CTLW misses: 1549; reduction versus naive DMP: 95.2%",
                "SPP+COPPER slack tick gap versus SPP: +0.294 percentage points",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_osslcli_app" / "OSSLCLI_HMAC_64K_SEED2_FS_SUMMARY.md",
            [
                "Input tag: `hmac_64k_seed2`",
                "SHA256 agreement: yes",
                "Naive DMP CTLW misses: 16898; COPPER CLPD-64K+PEB CTLW misses: 524; reduction: 96.9%",
                "SPP+COPPER slack CTLW misses: 428; reduction versus naive DMP: 97.5%",
                "SPP+COPPER slack tick gap versus SPP: -0.002 percentage points",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "GEM5_POWERSHELL_RUNNER_FIX_20260619.md",
            [
                "gem5 PowerShell Runner Fix",
                "Direct gem5 launch from PowerShell | PASS",
                "COPPER_FS_HOST_SWITCH_TO_TIMING",
                "COPPER_FS_HOST_WORKEND",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_gapbs_official_suite" / "GAPBS_OFFICIAL_SUITE_FINAL_G14_FS_SUMMARY.md",
            [
                "copper_clpd64k_peb",
                "292168298574",
                "99.3%",
                "zero fill-origin translation faults",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_gapbs_official_suite" / "GAPBS_OFFICIAL_SUITE_CROSS_SCALE_SUMMARY.md",
            [
                "| 10 | copper |",
                "| 12 | copper |",
                "| 14 | copper |",
                "suppresses almost all naive cross-page CTLW misses",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_duktape_app" / "DUKTAPE_APP_MEDIUM_FS_SUMMARY.md",
            [
                "Input tag: `app_medium`",
                "Checksum agreement: yes",
                "reduction: 90.8%",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_sqlite_app" / "SQLITE_APP_STRESS_FS_SUMMARY.md",
            [
                "Input tag: `app_stress`",
                "0xc91843372c7ddc37",
                "reduction: 94.1%",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "LUA_APP_STRESS_FS_SUMMARY.md",
            [
                "Input tag: `app_stress`",
                "0x7c4170c4",
                "reduction: 76.9%",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "LUA_APP_MEDIUM_SEED_SWEEP_SUMMARY.md",
            [
                "COPPER CLPD-64K+PEB beats unsafe naive DMP on all three medium Lua layouts: yes",
                "COPPER cuts aggregate naive CTLW misses by 92.446%",
                "SPP+COPPER slack stays within 0.760 percentage points",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "COPPER_PUBLIC_APP_MEDIUM_SEED_SWEEP_20260617.md",
            [
                "SQLite, Lua, and Duktape",
                "Overall COPPER CTLW reduction versus naive DMP: 92.747%",
                "Overall SPP+COPPER slack CTLW reduction versus naive DMP: 93.011%",
                "Worst absolute SPP+COPPER slack gap versus SPP: 0.760 percentage points",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "COPPER_PUBLIC_APP_STRESS_SEED_SWEEP_20260617.md",
            [
                "extends repeated public-engine evaluation beyond the medium",
                "Overall COPPER CTLW reduction versus naive DMP: 88.925%",
                "Overall SPP+COPPER slack CTLW reduction versus naive DMP: 90.191%",
                "Worst absolute SPP+COPPER slack gap versus SPP: 0.651 percentage points",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "COPPER_PUBLIC_APP_REPEATED_SEED_PORTFOLIO_20260617.md",
            [
                "Engine-seed points: 15; policy rows: 75",
                "Overall COPPER CTLW reduction versus naive DMP: 90.706%",
                "Overall SPP+COPPER slack CTLW reduction versus naive DMP: 91.505%",
                "Worst absolute SPP+COPPER slack gap versus SPP: 0.760 percentage points",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "COPPER_ENERGY_POLLUTION_SCORECARD_20260617.md",
            [
                "0.879% versus 1.083%",
                "18.8% lower proxy pollution score",
                "Across the weight-sensitivity sweep",
                "SPP+COPPER slack adds 0.093 percentage points",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "COPPER_DRAM_ENERGY_SCORECARD_20260618.md",
            [
                "Scope: 26 AArch64 full-system points",
                "COPPER CLPD-64K+PEB has lower-or-equal total DRAM energy than naive DMP on 13/26 points",
                "SPP+COPPER slack total DRAM energy gap versus SPP averages 0.071%",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "COPPER_MCPAT_SENSITIVITY_20260618.md",
            [
                "Generated rows: 130; successful McPAT rows: 130.",
                "| copper_clpd64k_peb | 26 | -0.338% | -0.625%",
                "| naive | 26 | -0.322% | -0.608%",
                "McPAT total runtime energy: copper_clpd64k_peb <= naive on 12/26",
            ],
        ),
        contains(
            RESULTS / "COPPER_RTL_POWER_PROXY_20260618.md",
            [
                "Checkpoints attempted: 15",
                "Successful reports: 15",
                "Routed 64K-entry CLPD on xc7a200t: 0.479 W total, 0.344 W dynamic",
                "not calibrated ASIC power",
                "I/O-dominated in out-of-context Vivado reporting",
            ],
        ),
        contains(
            RESULTS / "COPPER_CLPD_ACTIVITY_POWER_20260619.md",
            [
                "directed=18 random=4000",
                "| SAIF | 37%   (126/342) | 0.076 | 0.007 | 0.069 | Medium | WNS 2.208 ns, constraints met |",
                "Vivado matched 126 of 342 design nets",
                "not a calibrated ASIC or workload-derived full-system power result",
            ],
        ),
        contains(
            RESULTS / "COPPER_WORKLOAD_CLPD_ACTIVITY_POWER_20260619.md",
            [
                "Raw driver events: 1,318,318",
                "| Workload-derived SAIF | 37%   (226/611) | 0.083 | 0.014 | 0.069 | Medium | WNS 1.807 ns |",
                "not an instruction-by-instruction full-system waveform",
                "stronger than a random testbench SAIF",
            ],
        ),
        contains(
            RESULTS / "COPPER_TCP_PROCESS_CLPD_ACTIVITY_POWER_20260620.md",
            [
                "COPPER TCP Process-Server CLPD Activity Power",
                "Raw driver events: 268,494",
                "Replay events: 268,494",
                "Seed points: 4",
                "Process TCP pairs in selected rows: 14",
                "Source policy: `spp_copper_slack`",
                "errors=0",
                "| TCP process-server SAIF | 37%   (226/611) | 0.083 | 0.014 | 0.069 | Medium | WNS 1.807 ns |",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "COPPER_OOO_LSQ_PROOF_CONTRACT.md",
            [
                "Full contract status: PASS",
                "Every weakened variant has a short counterexample",
                "BUG_EXECUTE_STAGE_PROOF",
                "BUG_NO_SOURCE_REVOCATION",
                "BUG_NO_TRANSLATION_PERMISSION_GATE",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "COPPER_TLB_COHERENCE_CONTRACT.md",
            [
                "Full-contract reachable states explored: 39098",
                "queued_target_revocation",
                "BUG_NO_TARGET_QUEUE_HOLD",
                "BUG_NO_PERMISSION_GATE",
                "BUG_PAGE_LEVEL_TARGET_WITNESS",
                "Full contract status: PASS",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "COPPER_TLB_COHERENCE_AUTHORITY_FILTER_RTL_SUMMARY.md",
            [
                "directed=27 random=10000",
                "same-cycle and queued target remap",
                "unrelated source/target revocation precision allow",
                "Slice LUTs | 332",
                "WNS | +6.898 ns",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "copper_tlb_coherence_authority_filter_xsim_20260617.log",
            [
                "COPPER TLB-coherence authority filter completed",
                "random=10000",
                "errors=0",
            ],
        ),
        contains(
            RESULTS / "copper_tlb_coherence_authority_filter_timing.rpt",
            [
                "All user specified timing constraints are met",
                "6.898",
            ],
        ),
        contains(
            RESULTS / "copper_tlb_coherence_authority_filter_synth.log",
            [
                "Synthesis finished with 0 errors, 0 critical warnings and 0 warnings",
                "synth_design completed successfully",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_duktape_app" / "DUKTAPE_APP_STRESS_FS_SUMMARY.md",
            [
                "Input tag: `app_stress`",
                "0x3928cced",
                "reduction: 90.5%",
            ],
        ),
        contains(
            RESULTS / "COPPER_PREFETCH_TRAFFIC_OVERHEAD_20260616.md",
            [
                "plus scaled process-separated OpenSSL libssl TCP-netns points",
                "reduces CTLW misses by 93.9%",
                "faster than naive DMP on 10/22",
                "zero target-witness evictions",
            ],
        ),
        contains(
            RESULTS / "COPPER_APP_BASELINE_MATRIX_20260617.md",
            [
                "Best conventional policy counts across the 12 workloads: spp: 12",
                "average signed gap of -0.004 percentage points",
                "worst absolute gap among these rows is 0.360 percentage points",
                "SPP is the best ordinary performance baseline on all 12 points",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_cachesvc_app" / "CACHESVC_NOPOISON_CONTROL_AUDIT.md",
            [
                "VALID_STRESS_POINT_NOT_CLEAN_SECURITY_ORACLE",
                "Use the fake-only ROI, secret traffic oracle, observer oracle, and split scan/probe audit for differential security claims",
                "Poisoned service run: COPPER reduces naive CTLW misses by 99.5%",
                "Clean no-poison run: COPPER reduces naive CTLW misses by 99.6%",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_cachesvc_app" / "CACHESVC_SEED_STABILITY_AUDIT.md",
            [
                "COPPER CTLW reduction versus naive DMP is stable across 2 seeds",
                "SPP+COPPER slack CTLW reduction versus naive DMP is stable across 2 seeds",
                "translation faults across the seed audit: 0",
                "seed_stability_status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_cachesvc_app" / "CACHESVC_SCALE_SENSITIVITY_AUDIT.md",
            [
                "COPPER CTLW reduction versus naive DMP across scales: 99.4% to 99.5%",
                "SPP+COPPER slack CTLW reduction versus naive DMP across scales: 99.4% to 99.5%",
                "translation faults across the scale audit: 0",
                "scale_sensitivity_status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_tlssvc_app" / "TLSSVC_APP_SMOKE_FS_SUMMARY.md",
            [
                "TLS/session-service style native AArch64 Linux ROI",
                "Naive DMP CTLW misses: 3680; COPPER CLPD-64K+PEB CTLW misses: 18; reduction: 99.5%",
                "SPP+COPPER slack CTLW misses: 19; reduction versus naive DMP: 99.5%",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_ossltlsbio_app" / "OSSLTLSBIO_APP_SMOKE_FS_SUMMARY.md",
            [
                "OpenSSL libssl's TLS 1.2 PSK handshake and TLS record read/write path",
                "Naive DMP CTLW misses: 2411; COPPER CLPD-64K+PEB CTLW misses: 29; reduction: 98.8%",
                "SPP+COPPER slack CTLW misses: 54; reduction versus naive DMP: 97.8%",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_ossltlsbio_app" / "OSSLTLSBIO_APP_MEDIUM_FS_SUMMARY.md",
            [
                "Input tag: `app_medium`",
                "Naive DMP CTLW misses: 58980; COPPER CLPD-64K+PEB CTLW misses: 725; reduction: 98.8%",
                "SPP+COPPER slack CTLW misses: 1664; reduction versus naive DMP: 97.2%",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_ossltlssocket_app" / "OSSLTLSSOCKET_SOCKET_SMOKE_FS_SUMMARY.md",
            [
                "OpenSSL libssl's TLS 1.2 PSK handshake and TLS record read/write path",
                "nonblocking Linux AF_UNIX socketpair",
                "Naive DMP CTLW misses: 16554; COPPER CLPD-64K+PEB CTLW misses: 144; reduction: 99.1%",
                "SPP+COPPER slack CTLW misses: 296; reduction versus naive DMP: 98.2%",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "OPENSSL_TCP_LOOPBACK_FEASIBILITY_20260619.md",
            [
                "OpenSSL TCP Loopback Feasibility Note",
                "errno=99",
                "errno=101",
                "tcp_diag_lo",
                "Operation not permitted",
                "`lo` down and no local route",
                "tcp_diag_systemd",
                "not counted as benchmark results",
                "host_namespace_tcp_loopback_status=NOT_LOCALLY_TRACTABLE_UNDER_CURRENT_GEM5_BOOT",
                "private_netns_tcp_loopback_status=PASS",
                "private_netns_process_tcp_loopback_status=PASS",
            ],
        ),
        contains(
            RESULTS / "OPENSSL_MEDIUM_SEED_STABILITY_20260619.md",
            [
                "OpenSSL libcrypto EVP/HMAC/SHA | 2 | 95.0% / 95.0%",
                "OpenSSL libssl TLS memory-BIO | 2 | 98.8% / 98.8%",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_osslsha_app" / "OSSLSHA_APP_SMOKE_FS_SUMMARY.md",
            [
                "OpenSSL libcrypto's exported `SHA256` routine",
                "Naive DMP CTLW misses: 10590; COPPER CLPD-64K+PEB CTLW misses: 301; reduction: 97.2%",
                "SPP+COPPER slack CTLW misses: 259; reduction versus naive DMP: 97.6%",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_osslcrypto_app" / "OSSLCRYPTO_APP_SMOKE_FS_SUMMARY.md",
            [
                "OpenSSL libcrypto EVP AES-128-CTR, HMAC-SHA256, SHA256, and",
                "Naive DMP CTLW misses: 16685; COPPER CLPD-64K+PEB CTLW misses: 954; reduction: 94.3%",
                "SPP+COPPER slack CTLW misses: 828; reduction versus naive DMP: 95.0%",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_osslcrypto_app" / "OSSLCRYPTO_APP_MEDIUM_FS_SUMMARY.md",
            [
                "Input tag: `app_medium`",
                "Naive DMP CTLW misses: 17857; COPPER CLPD-64K+PEB CTLW misses: 892; reduction: 95.0%",
                "SPP+COPPER slack CTLW misses: 716; reduction versus naive DMP: 96.0%",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "figures" / "COPPER_APP_FIGURE_INDEX_20260616.md",
            [
                "Runtime deltas",
                "Full baseline runtime matrix",
                "CTLW reduction",
                "Bus overhead",
            ],
        ),
        min_bytes(
            RESULTS / "figures" / "copper_app_runtime_delta.png",
            50000,
        ),
        min_bytes(
            RESULTS / "figures" / "copper_app_full_baseline_runtime.png",
            50000,
        ),
        min_bytes(
            RESULTS / "figures" / "copper_app_ctlw_reduction.png",
            50000,
        ),
        min_bytes(
            RESULTS / "figures" / "copper_app_bus_overhead.png",
            50000,
        ),
        contains(
            RESULTS / "COPPER_APPLICATION_WORKLOAD_PORTFOLIO_20260616.md",
            [
                "Duktape stress",
                "yyjson stress",
                "TLS session-service small",
                "OpenSSL libssl TLS memory-BIO small",
                "socket-backed OpenSSL libssl TLS execution",
                "strict private-netns TCP-loopback OpenSSL libssl TLS execution",
                "two-seed process-separated private-netns TCP-loopback OpenSSL libssl TLS execution",
                "two-seed PCRE2 regex matching",
                "public libxml2 XML parser/serializer execution",
                "public libarchive TAR parser execution",
                "Zstd and zlib compression/decompression",
                "PCRE2 seed-stability artifact",
                "COPPER keeps at least 99.3% CTLW reduction",
                "OpenSSL SHA service small",
                "OpenSSL EVP/HMAC service small",
                "SQLite speedtest1 JSON/star/ORM",
                "medium/stress scale points",
                "98.9% | 0",
                "99.5% | 0",
                "spp -6.732%",
                "portfolio_status=PASS",
            ],
        ),
        contains(
            RESULTS / "SQLITE_MEDIUM_STRESS_SEED_STABILITY_20260619.md",
            [
                "SQLite Medium/Stress Seed Stability",
                "Across all 5 SQLite medium/stress seed points, COPPER CTLW reduction is at least 90.3%",
                "Across all 5 SQLite medium/stress seed points, SPP+COPPER slack CTLW reduction is at least 86.4%",
                "Worst absolute SPP+COPPER slack tick gap versus SPP is 0.056 percentage points",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_sqlite_speedtest1" / "SQLITE_SPEEDTEST1_SPEEDTEST1_JSON_SMOKE_SIZE1_FS_SUMMARY.md",
            [
                "SQLite speedtest1 AArch64 Full-System Summary",
                "unmodified upstream SQLite speedtest1 workload built from SQLite 3.53.2",
                "Verification hash agreement: yes",
                "Verification byte-count agreement: 0",
                "Naive DMP CTLW misses: 12802; COPPER CLPD-64K+PEB CTLW misses: 983; reduction: 92.3%",
                "Translation faults: naive=0, COPPER=0, SPP=0, SPP+COPPER-slack=0",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_sqlite_speedtest1" / "SQLITE_SPEEDTEST1_SPEEDTEST1_STAR_SMOKE_SIZE1_FS_SUMMARY.md",
            [
                "SQLite speedtest1 AArch64 Full-System Summary",
                "--testset star",
                "Verification byte-count agreement: 0",
                "Naive DMP CTLW misses: 6844; COPPER CLPD-64K+PEB CTLW misses: 340; reduction: 95.0%",
                "Translation faults: naive=0, COPPER=0, SPP=0, SPP+COPPER-slack=0",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_sqlite_speedtest1" / "SQLITE_SPEEDTEST1_SPEEDTEST1_ORM_SMOKE_SIZE1_FS_SUMMARY.md",
            [
                "SQLite speedtest1 AArch64 Full-System Summary",
                "--testset orm",
                "Verification byte-count agreement: 408505",
                "Naive DMP CTLW misses: 38552; COPPER CLPD-64K+PEB CTLW misses: 1197; reduction: 96.9%",
                "Translation faults: naive=0, COPPER=0, SPP=0, SPP+COPPER-slack=0",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "SQLITE_SPEEDTEST1_COMPONENTS_20260619.md",
            [
                "SQLite speedtest1 Component Summary",
                "Components: 3.",
                "Minimum COPPER CTLW reduction versus naive DMP: 92.3%.",
                "Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 88.5%.",
                "Translation faults across key policies and components: 0.",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "LUA_DUKTAPE_MEDIUM_STRESS_SEED_STABILITY_20260619.md",
            [
                "Lua/Duktape Medium/Stress Seed Stability",
                "Across all 10 Lua/Duktape medium/stress seed points, COPPER CTLW reduction is at least 76.7%",
                "Across all 10 Lua/Duktape medium/stress seed points, SPP+COPPER slack CTLW reduction is at least 85.0%",
                "Worst absolute SPP+COPPER slack tick gap versus SPP is 0.760 percentage points",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "YYJSON_MEDIUM_STRESS_SEED_STABILITY_20260619.md",
            [
                "yyjson Medium/Stress Seed Stability",
                "Across all 4 yyjson medium/stress seed points, COPPER CTLW reduction is at least 98.9%",
                "Across all 4 yyjson medium/stress seed points, SPP+COPPER slack CTLW reduction is at least 97.4%",
                "Worst absolute SPP+COPPER slack tick gap versus SPP is 0.089 percentage points",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_jsonsqlite_app" / "JSONSQLITE_MEDIUM_SEED1_FS_SUMMARY.md",
            [
                "Input tag: `medium_seed1`",
                "Checksum agreement: yes (0x0ba31ab66d915ce3).",
                "Naive DMP CTLW misses: 14301; COPPER CLPD-64K+PEB CTLW misses: 523; reduction: 96.3%.",
                "SPP+COPPER slack CTLW misses: 564; reduction versus naive DMP: 96.1%.",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "JSONSQLITE_MEDIUM_SEED_STABILITY_20260619.md",
            [
                "JSON+SQLite Medium Two-Seed Stability",
                "COPPER CTLW reduction is at least 95.0%",
                "SPP+COPPER slack CTLW reduction is at least 95.9%",
                "Worst absolute SPP+COPPER slack tick gap versus SPP is 0.026 percentage points",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "gem5_arm_ubuntu_fs_jsonsqlite_app" / "JSONSQLITE_STRESS_SEED1_FS_SUMMARY.md",
            [
                "Input tag: `stress_seed1`",
                "Checksum agreement: yes (0x140fe495c0a04aef).",
                "Naive DMP CTLW misses: 41268; COPPER CLPD-64K+PEB CTLW misses: 2346; reduction: 94.3%.",
                "SPP+COPPER slack CTLW misses: 1168; reduction versus naive DMP: 97.2%.",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "JSONSQLITE_STRESS_SEED_STABILITY_20260619.md",
            [
                "JSON+SQLite Stress Two-Seed Stability",
                "COPPER CTLW reduction is at least 91.4%",
                "SPP+COPPER slack CTLW reduction is at least 96.6%",
                "Worst absolute SPP+COPPER slack tick gap versus SPP is 0.069 percentage points",
                "status=PASS",
            ],
        ),
        contains(
            RESULTS / "copper_lsq_source_tag_tracker_xsim_20260616.log",
            [
                "COPPER LSQ source-tag tracker completed",
                "random=10000",
                "errors=0",
            ],
        ),
        contains(
            RESULTS / "copper_lsq_cepf_line_e2e_xsim_20260616.log",
            [
                "COPPER LSQ-CEPF-line E2E completed",
                "random=10000",
                "errors=0",
            ],
        ),
        contains(
            RESULTS / "copper_lsq_cepf_line_e2e_top_timing.rpt",
            [
                "All user specified timing constraints are met",
                "2.176",
            ],
        ),
        contains(
            RESULTS / "copper_amba_sari_frontdoor_xsim_20260616.log",
            [
                "COPPER AMBA-SARI frontdoor completed",
                "random=10000",
                "errors=0",
            ],
        ),
        contains(
            RESULTS / "copper_amba_sari_frontdoor_regslice_timing.rpt",
            [
                "All user specified timing constraints are met",
                "7.525",
            ],
        ),
        contains(
            RESULTS / "copper_amba_sari_authority_bridge_xsim_20260616.log",
            [
                "COPPER AMBA-SARI authority bridge completed",
                "backpressure=1",
                "random=10000",
                "errors=0",
            ],
        ),
        contains(
            RESULTS / "copper_amba_sari_authority_bridge_top_timing.rpt",
            [
                "All user specified timing constraints are met",
                "1.082",
            ],
        ),
        contains(
            RESULTS / "copper_amba_sari_authority_bridge_top_synth.log",
            [
                "Synthesis finished with 0 errors, 0 critical warnings and 0 warnings",
                "synth_design completed successfully",
            ],
        ),
        contains(
            RESULTS / "copper_full_lsq_amba_authority_xsim_20260616.log",
            [
                "COPPER full LSQ-AMBA authority completed",
                "random=10000",
                "errors=0",
            ],
        ),
        contains(
            RESULTS / "copper_full_lsq_amba_authority_top_timing.rpt",
            [
                "All user specified timing constraints are met",
                "0.473",
            ],
        ),
        contains(
            RESULTS / "copper_full_lsq_amba_authority_top_synth.log",
            [
                "Synthesis finished with 0 errors, 0 critical warnings and 0 warnings",
                "synth_design completed successfully",
            ],
        ),
        contains(
            ROOT / "research" / "copper_sari_ring_revoker.sv",
            [
                "COPPER SARI-RQ",
                "ring-queued SoC Authority Revocation Interface",
                "overflow_sticky",
            ],
        ),
        contains(
            RESULTS / "COPPER_SARI_RQ_STATE_SPACE.md",
            [
                "Ring/shift equivalence under ready protocol | PASS",
                "Backpressure/overflow fallback | PASS",
                "Overall status: PASS",
            ],
        ),
    ]

    passed = sum(1 for check in checks if check.status)
    lines = [
        "# COPPER Artifact Audit",
        "",
            "Date: 2026-06-20",
        "",
        f"Passed {passed}/{len(checks)} artifact checks.",
        "",
        "| Artifact | Status | Detail |",
        "|---|---:|---|",
    ]
    for check in checks:
        lines.append(
            f"| `{check.name}` | {'PASS' if check.status else 'FAIL'} | {check.detail} |"
        )
    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            "- PASS means the local artifact contains the minimum evidence strings used by the current paper claim.",
            "- This is not a proof of correctness or novelty; it is a reproducibility sanity check to prevent stale paper artifacts from drifting away from measured results.",
            "- A top-tier submission still cannot be guaranteed, but the evidence now covers repeated medium/stress public-engine layout evidence, two-seed public PCRE2, public libxml2 XML parser/serializer and libarchive TAR parser points, plus two-seed Zstd/zlib library-driver points, bounded service-style and crypto-adjacent full-system stress points, real OpenSSL libssl TLS memory-BIO small/medium two-seed execution, socket-backed OpenSSL libssl TLS execution, a tagged TCP-harness AF_UNIX fallback libssl run, a strict private-netns TCP-loopback OpenSSL libssl run, a four-point process-separated private-netns TCP-loopback OpenSSL libssl portfolio including scaled four-pair and eight-pair points, real OpenSSL libcrypto SHA256 plus small/medium EVP/HMAC two-seed drivers, a two-seed OpenSSL-speed-like fixed-buffer libcrypto driver, official OpenSSL CLI compatibility plus multi-seed fixed-digest/AES/HMAC evidence, a PowerShell-native gem5 runner fix for the official CLI path, gem5-counter traffic/pollution, DRAM-energy, McPAT-sensitivity, Vivado vectorless/testbench-SAIF/workload-counter-replay/TCP-process-replay RTL power-proxy scorecards, app/service/parser/compression/TCP and TCP process-server metadata-toggle sensitivity bounds, OoO-LSQ and TLB/coherence contracts, a TLB/coherence RTL filter, LSQ proof capture, a timed AMBA-frontdoor/SARI/CLPD/CTLW authority path, and a generated public artifact manifest with hashes and pruning guidance.",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)
    if passed != len(checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
