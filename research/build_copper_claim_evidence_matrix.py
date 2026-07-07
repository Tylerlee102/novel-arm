#!/usr/bin/env python3
"""Build a claim-to-evidence matrix for the COPPER/SCOOP submission package."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT_MATRIX = RESULTS / "COPPER_CLAIM_EVIDENCE_MATRIX_20260617.md"
OUT_GATE = RESULTS / "COPPER_TOP_TIER_GATE_AUDIT_20260617.md"


@dataclass(frozen=True)
class Evidence:
    path: Path
    needles: tuple[str, ...]


@dataclass(frozen=True)
class Claim:
    claim_id: str
    wording: str
    allowed_wording: str
    evidence: tuple[Evidence, ...]
    reviewer_risk: str
    remaining_gap: str


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_text(path: Path) -> str:
    body = path.read_bytes()
    if b"\x00" in body[:200]:
        return body.decode("utf-16", errors="replace")
    return body.decode("utf-8", errors="replace")


def evidence_status(evidence: Evidence) -> tuple[bool, str]:
    if not evidence.path.exists():
        return False, "missing"
    body = read_text(evidence.path)
    missing = [needle for needle in evidence.needles if needle not in body]
    if missing:
        return False, "missing: " + "; ".join(missing)
    return True, "ok"


CLAIMS = (
    Claim(
        "C1",
        "COPPER/SCOOP is positioned as a distinct public DMP authority mechanism.",
        "The current related-work record did not identify a public DMP mechanism that uses committed pointer provenance, address-space binding, and committed target-line witnesses as the authority for recursive content-derived prefetching while coexisting with conventional address-correlation prefetchers.",
        (
            Evidence(
                RESULTS / "COPPER_PRIOR_ART_DELTA_20260617.md",
                (
                    "to the best of public knowledge",
                    "ICP: Exploiting Instruction Correlation",
                    "novelty_risk=3/10",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_PRIOR_ART_UPDATE_20260616.md",
                (
                    "SplittingSecrets",
                    "Novelty Risk",
                    "Closest Public Prior Art",
                ),
            ),
        ),
        "A reviewer may collapse the idea into generic taint/provenance metadata or cite unpublished commercial DMP restrictions.",
        "Keep the novelty claim public-knowledge scoped and centered on DMP issue authority, not metadata itself.",
    ),
    Claim(
        "C2",
        "The core contribution is not a renamed combination of known blocks.",
        "The named mechanism is the authority invariant: content-derived DMP issue requires committed source-word proof, clean-since-proof lifecycle, PASB token match, and exact CTLW target witnesses for recursive cross-page issue.",
        (
            Evidence(
                ROOT / "research" / "COPPER_FULL_PAPER.md",
                (
                    "The contribution is the authority rule for a DMP and its recursive consequence",
                    "A DMP may dereference a memory word only if committed execution has already",
                    "Committed Target-Line Witnessing",
                ),
            ),
            Evidence(
                ROOT / "research" / "COPPER_FINAL_OUTPUT.md",
                (
                    "Why It Is Not Merely a Combination",
                    "DMP dereference authority comes from committed architectural pointer use",
                    "RCP extends this invariant recursively",
                ),
            ),
        ),
        "The paper is easy to misread as metadata plus a prefetcher plus epochs.",
        "Use short mechanism diagrams and lead with the invariant before listing implementation blocks.",
    ),
    Claim(
        "C3",
        "The security oracle shows unsafe DMP traffic is secret-dependent and COPPER/SCOOP block the unauthorized scan-phase issue.",
        "In the tested AArch64 full-system DMP oracles, unsafe DMP produces secret-dependent prefetch/allowed deltas, while COPPER and SCOOP have zero unauthorized scan-phase allowed-candidate delta.",
        (
            Evidence(
                RESULTS / "COPPER_SECURITY_EVIDENCE_PORTFOLIO_20260616.md",
                (
                    "PF delta 32760",
                    "scan allowed delta 0",
                    "companion allowed delta 0",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_dmp_oracle" / "DMP_ORACLE_I512_P4_PROBE1_EVICT512_SPLIT_SUMMARY.md",
                (
                    "Scan-phase deltas",
                    "The unsafe prefetcher leaks during the scan phase",
                    "COPPER and SCOOP block the scan-phase secret-dependent candidates",
                ),
            ),
        ),
        "A reviewer may argue the observer phase includes legitimate architectural probes.",
        "Use the split scan/probe result as the primary security claim; treat non-split observer deltas as supporting evidence.",
    ),
    Claim(
        "C4",
        "The public application baseline matrix is fair about conventional prefetchers.",
        "On the 12-point SQLite/Lua/Duktape/yyjson plus JSON+SQLite and cache-service AArch64 full-system app matrix, SPP is the best conventional baseline on all 12 points; SPP+COPPER slack has an average signed gap of -0.004 percentage points versus SPP and a 0.360-point worst absolute gap.",
        (
            Evidence(
                RESULTS / "COPPER_APP_BASELINE_MATRIX_20260617.md",
                (
                    "Best conventional policy counts across the 12 workloads: spp: 12",
                    "average signed gap of -0.004 percentage points",
                    "worst absolute gap among these rows is 0.360 percentage points",
                ),
            ),
            Evidence(
                RESULTS / "figures" / "COPPER_APP_FIGURE_INDEX_20260616.md",
                ("Full baseline runtime matrix",),
            ),
        ),
        "Conventional prefetchers still win raw performance on many workloads.",
        "Frame SCOOP as coexistence with a conventional primary, not a universal replacement.",
    ),
    Claim(
        "C5",
        "Standalone COPPER is a low-overhead authority path, not a universal speed path.",
        "Across the expanded public app/service/parser/compression/TCP side-effect suite, standalone COPPER averages -0.321% ticks, +0.441% memory-bus bytes, 93.9% CTLW reduction versus naive DMP, zero translation faults, a base-weighted 18.8% lower mean gem5-counter pressure score than naive DMP with 18.1%-20.6% lower results across transparent weight scenarios, lower mean modeled DRAM total/op energy than naive DMP, a fixed-architecture McPAT sensitivity pass with -0.321% mean total-energy proxy versus no prefetch while naive DMP is -0.304%, a metadata-toggle sensitivity bound whose high scenario is 0.1801% of matching COPPER DRAM operation energy, and TCP process-server side-effect checks whose high pJ/access scenario stays below 6.818 uJ and whose conservative slack candidate stream replays through Vivado SAIF at 0.083 W total / 0.014 W dynamic.",
        (
            Evidence(
                RESULTS / "COPPER_PREFETCH_TRAFFIC_OVERHEAD_20260616.md",
                (
                    "COPPER CLPD-64K+PEB has a mean tick delta of -0.321%",
                    "COPPER CLPD-64K+PEB changes mean bus bytes by 0.441%",
                    "reduces CTLW misses by 93.9%",
                    "with zero observed translation faults",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_ENERGY_POLLUTION_SCORECARD_20260617.md",
                (
                    "0.879% versus 1.083%",
                    "18.8% lower proxy pollution score",
                    "Across the weight-sensitivity sweep",
                    "SPP+COPPER slack adds 0.093 percentage points",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_DRAM_ENERGY_SCORECARD_20260618.md",
                (
                    "Scope: 26 AArch64 full-system points",
                    "COPPER CLPD-64K+PEB has lower-or-equal total DRAM energy than naive DMP on 13/26 points",
                    "SPP+COPPER slack total DRAM energy gap versus SPP averages 0.071%",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_MCPAT_SENSITIVITY_20260618.md",
                (
                    "Generated rows: 130; successful McPAT rows: 130.",
                    "| copper_clpd64k_peb | 26 | -0.338% | -0.321%",
                    "| naive | 26 | -0.322% | -0.304%",
                    "McPAT total runtime energy: copper_clpd64k_peb <= naive on 12/26",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_METADATA_TOGGLE_BOUND_20260619.md",
                (
                    "Learned-proof writes: 40,058",
                    "CLPD source-proof reads: 1,407,655",
                    "Total charged metadata reads: 1,427,701",
                    "high | 20.0 | 40.0 | 5.0 | 37.495 uJ | 0.1801%",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "OPENSSL_TCP_PROCESS_METADATA_TOGGLE_BOUND_20260620.md",
                (
                    "OpenSSL TCP Process-Server Metadata Toggle Bound",
                    "Selected policy rows: 8",
                    "| copper_clpd64k_peb | 4 | 14 | 170,564",
                    "| spp_copper_slack | high | 20.0 | 40.0 | 5.0 | 6.818 uJ | 0.1510% | 0.005412% |",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_TCP_PROCESS_CLPD_ACTIVITY_POWER_20260620.md",
                (
                    "COPPER TCP Process-Server CLPD Activity Power",
                    "Raw driver events: 268,494",
                    "Replay events: 268,494",
                    "| TCP process-server SAIF | 37%   (226/611) | 0.083 | 0.014 | 0.069 | Medium | WNS 1.807 ns |",
                    "status=PASS",
                ),
            ),
        ),
        "The McPAT result is still a fixed proxy, and the metadata-toggle bound is pJ/access sensitivity rather than calibrated full-chip power.",
        "Call it gem5 DRAM energy plus McPAT and metadata-toggle sensitivity, not silicon CPU/SoC power.",
    ),
    Claim(
        "C6",
        "The evaluation includes real AArch64/Linux full-system execution, not only traces.",
        "Validated gem5 ARM-system summaries and retained raw-run manifests show native AArch64/Linux full-system ROIs for the listed benchmark families where the generated validation rows PASS. Feasibility rows, larger scale attempts, and imported summaries are labeled separately and must not be promoted to a complete fresh raw-run campaign.",
        (
            Evidence(
                RESULTS / "COPPER_APPLICATION_WORKLOAD_PORTFOLIO_20260616.md",
                (
                    "The application evidence is materially stronger than the earlier generated-only story",
                    "two-seed PCRE2 regex matching",
                    "public libxml2 XML parser/serializer execution",
                    "public libarchive TAR parser execution",
                    "socket-backed OpenSSL libssl TLS execution",
                    "two-seed process-separated private-netns TCP-loopback OpenSSL libssl TLS execution",
                    "real OpenSSL libcrypto SHA256 plus EVP/HMAC drivers",
                    "medium/stress scale points",
                    "portfolio_status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_ossltlsbio_app" / "OSSLTLSBIO_APP_SMOKE_FS_SUMMARY.md",
                (
                    "OpenSSL libssl's TLS 1.2 PSK handshake and TLS record read/write path",
                    "Naive DMP CTLW misses: 2411; COPPER CLPD-64K+PEB CTLW misses: 29; reduction: 98.8%",
                    "SPP+COPPER slack CTLW misses: 54; reduction versus naive DMP: 97.8%",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_ossltlsbio_app" / "OSSLTLSBIO_APP_MEDIUM_FS_SUMMARY.md",
                (
                    "Input tag: `app_medium`",
                    "Naive DMP CTLW misses: 58980; COPPER CLPD-64K+PEB CTLW misses: 725; reduction: 98.8%",
                    "SPP+COPPER slack CTLW misses: 1664; reduction versus naive DMP: 97.2%",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_ossltlssocket_app" / "OSSLTLSSOCKET_SOCKET_SMOKE_FS_SUMMARY.md",
                (
                    "OpenSSL libssl's TLS 1.2 PSK handshake and TLS record read/write path",
                    "nonblocking Linux AF_UNIX socketpair",
                    "Naive DMP CTLW misses: 16554; COPPER CLPD-64K+PEB CTLW misses: 144; reduction: 99.1%",
                    "SPP+COPPER slack CTLW misses: 296; reduction versus naive DMP: 98.2%",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_pcre2_app" / "PCRE2_PCRE2_SMOKE_FS_SUMMARY.md",
                (
                    "public PCRE2 8-bit regex compiler and matcher",
                    "Naive DMP CTLW misses: 9406; COPPER CLPD-64K+PEB CTLW misses: 62; reduction: 99.3%",
                    "SPP+COPPER slack CTLW misses: 79; reduction versus naive DMP: 99.2%",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "PCRE2_REGEX_SEED_STABILITY_20260620.md",
                (
                    "PCRE2 Regex Seed Stability",
                    "PCRE2 seed points: 2.",
                    "Distinct per-seed checksums: 2.",
                    "Minimum COPPER CTLW reduction versus naive DMP: 99.3%.",
                    "Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 98.9%.",
                    "COPPER/slack translation faults across both seed points: 0.",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_mibench_patricia_app" / "MIBENCH_PATRICIA_PATRICIA_PREPROBE_FS_SUMMARY.md",
                (
                    "MiBench Patricia AArch64 Full-System Summary",
                    "public MiBench network/patricia Patricia trie",
                    "Public input records consumed: 128 of limit 128.",
                    "Naive DMP CTLW misses: 11992; COPPER CLPD-64K+PEB CTLW misses: 85; reduction: 99.3%.",
                    "SPP+COPPER slack CTLW misses: 102; reduction versus naive DMP: 99.1%.",
                    "SPP+COPPER slack tick gap versus SPP: -0.026 percentage points.",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_mibench_patricia_app" / "MIBENCH_PATRICIA_PATRICIA_SMALL2048_FS_SUMMARY.md",
                (
                    "MiBench Patricia AArch64 Full-System Summary",
                    "Input tag: `patricia_small2048`.",
                    "Public input records consumed: 2048 of limit 2048.",
                    "Naive DMP CTLW misses: 14014; COPPER CLPD-64K+PEB CTLW misses: 181; reduction: 98.7%.",
                    "SPP+COPPER slack CTLW misses: 422; reduction versus naive DMP: 97.0%.",
                    "SPP+COPPER slack tick gap versus SPP: +0.030 percentage points.",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_mibench_patricia_app" / "MIBENCH_PATRICIA_PATRICIA_SMALL8192_FS_SUMMARY.md",
                (
                    "MiBench Patricia AArch64 Full-System Summary",
                    "Input tag: `patricia_small8192`.",
                    "Public input records consumed: 8192 of limit 8192.",
                    "Naive DMP CTLW misses: 16478; COPPER CLPD-64K+PEB CTLW misses: 245; reduction: 98.5%.",
                    "SPP+COPPER slack CTLW misses: 379; reduction versus naive DMP: 97.7%.",
                    "SPP+COPPER slack tick gap versus SPP: +0.050 percentage points.",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_mibench_patricia_app" / "MIBENCH_PATRICIA_PATRICIA_LARGE12288_FS_SUMMARY.md",
                (
                    "MiBench Patricia AArch64 Full-System Summary",
                    "Input tag: `patricia_large12288`.",
                    "Public input records consumed: 12288 of limit 12288.",
                    "Naive DMP CTLW misses: 18454; COPPER CLPD-64K+PEB CTLW misses: 381; reduction: 97.9%.",
                    "SPP+COPPER slack CTLW misses: 635; reduction versus naive DMP: 96.6%.",
                    "SPP+COPPER slack tick gap versus SPP: +0.035 percentage points.",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_mibench_patricia_app" / "MIBENCH_PATRICIA_PATRICIA_LARGE12288_SEED1_FS_SUMMARY.md",
                (
                    "MiBench Patricia AArch64 Full-System Summary",
                    "Input tag: `patricia_large12288_seed1`.",
                    "Public input records consumed: 12288 of limit 12288.",
                    "Naive DMP CTLW misses: 17909; COPPER CLPD-64K+PEB CTLW misses: 398; reduction: 97.8%.",
                    "SPP+COPPER slack CTLW misses: 567; reduction versus naive DMP: 96.8%.",
                    "SPP+COPPER slack tick gap versus SPP: -0.030 percentage points.",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "MIBENCH_PATRICIA_12K_SEED_STABILITY_20260621.md",
                (
                    "MiBench Patricia 12K Seed Stability",
                    "MiBench Patricia 12K seed points: 2.",
                    "Distinct per-seed checksums: 2.",
                    "Minimum COPPER CTLW reduction versus naive DMP: 97.8%.",
                    "Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 96.6%.",
                    "Worst absolute SPP+COPPER slack tick gap versus SPP: 0.035 percentage points.",
                    "COPPER/slack translation faults across both 12K seeds: 0.",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "MIBENCH_PATRICIA_SCALE_PORTFOLIO_20260620.md",
                (
                    "MiBench Patricia Scale Portfolio",
                    "MiBench Patricia scale points: 4.",
                    "Largest public input records consumed: 12288.",
                    "Minimum COPPER CTLW reduction versus naive DMP: 97.9%.",
                    "Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 96.6%.",
                    "Worst absolute SPP+COPPER slack tick gap versus SPP: 0.050 percentage points.",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "MIBENCH_PATRICIA_LARGE16384_FEASIBILITY_20260620.md",
                (
                    "MiBench Patricia 16K Feasibility Note",
                    "Public input records consumed: 16,384 of limit 16,384.",
                    "Final ROI simTicks: 106,061,839,659.",
                    "COPPER entered the timed ROI",
                    "status=PARTIAL_NEGATIVE_FEASIBILITY",
                ),
            ),
            Evidence(
                RESULTS / "MIBENCH_PATRICIA_LARGE32768_FEASIBILITY_20260620.md",
                (
                    "MiBench Patricia 32K Feasibility Note",
                    "Public input records consumed: 32,768 of limit 32,768.",
                    "Final ROI simTicks: 222,447,259,404.",
                    "status=PARTIAL_NEGATIVE_FEASIBILITY",
                ),
            ),
            Evidence(
                RESULTS / "MIBENCH_PATRICIA_LARGE62721_FEASIBILITY_20260620.md",
                (
                    "MiBench Patricia Full-Large Feasibility Note",
                    "Public input records consumed: 62,721 of limit 62,721.",
                    "Final ROI simTicks: 417,102,890,922.",
                    "status=PARTIAL_NEGATIVE_FEASIBILITY",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_libxml2_app" / "LIBXML2_XML_TINY_FULL_FS_SUMMARY.md",
                (
                    "public libxml2 XML parser and serializer",
                    "Input tag: `xml_tiny_full`.",
                    "Naive DMP CTLW misses: 12758; COPPER CLPD-64K+PEB CTLW misses: 139; reduction: 98.9%",
                    "SPP+COPPER slack CTLW misses: 136; reduction versus naive DMP: 98.9%",
                    "slack gap: 0.035 percentage points",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_libarchive_app" / "LIBARCHIVE_TAR_TINY_FULL_FS_SUMMARY.md",
                (
                    "public libarchive TAR parser",
                    "Input tag: `tar_tiny_full`.",
                    "Naive DMP CTLW misses: 17091; COPPER CLPD-64K+PEB CTLW misses: 341; reduction: 98.0%",
                    "SPP+COPPER slack CTLW misses: 233; reduction versus naive DMP: 98.6%",
                    "slack gap: -0.004 percentage points",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_zstd_app" / "ZSTD_ZSTD_TINY_FS_SUMMARY.md",
                (
                    "public libzstd compression and decompression",
                    "Naive DMP CTLW misses: 9239; COPPER CLPD-64K+PEB CTLW misses: 49; reduction: 99.5%",
                    "SPP+COPPER slack CTLW misses: 51; reduction versus naive DMP: 99.4%",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_zlib_app" / "ZLIB_ZLIB_TINY_FS_SUMMARY.md",
                (
                    "public zlib compression and decompression",
                    "Naive DMP CTLW misses: 11336; COPPER CLPD-64K+PEB CTLW misses: 65; reduction: 99.4%",
                    "SPP+COPPER slack CTLW misses: 58; reduction versus naive DMP: 99.5%",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "COMPRESSION_LIBRARY_SEED_STABILITY_20260620.md",
                (
                    "Compression-Library Seed Stability",
                    "Seed/library points: 4.",
                    "Minimum COPPER CTLW reduction versus naive DMP: 99.4%.",
                    "Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 99.4%.",
                    "COPPER/slack translation faults across all seed points: 0.",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "OPENSSL_TCP_LOOPBACK_FEASIBILITY_20260619.md",
                (
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
                ),
            ),
            Evidence(
                RESULTS / "OPENSSL_CLI_TLS_PAIR_FEASIBILITY_20260620.md",
                (
                    "OpenSSL CLI TLS-Pair Feasibility Note",
                    "`/usr/bin/openssl`",
                    "COPPER_OPENSSL_GUEST_PROBE_DONE",
                    "not counted as performance evidence",
                    "status=NEGATIVE_FEASIBILITY_RESULT_NOT_BENCHMARK_EVIDENCE",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_ossltlstcp_app" / "ossltlstcp_TCP_NETNS_STRICT_FS_SUMMARY.md",
                (
                    "OpenSSL libssl TLS TCP Loopback AArch64 Full-System Summary",
                    "Transport modes observed: tcp_loopback_netns.",
                    "Naive DMP CTLW misses: 9645; COPPER CLPD-64K+PEB CTLW misses: 221; reduction: 97.7%.",
                    "SPP+COPPER slack CTLW misses: 269; reduction versus naive DMP: 97.2%.",
                    "status=TCP_NETNS_PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_ossltlstcp_app" / "ossltlstcp_TCP_NETNS_PROCESS_KEY1_FS_SUMMARY.md",
                (
                    "OpenSSL libssl TLS TCP Loopback AArch64 Full-System Summary",
                    "Transport modes observed: tcp_loopback_netns_process.",
                    "Naive DMP CTLW misses: 7185; COPPER CLPD-64K+PEB CTLW misses: 111; reduction: 98.5%.",
                    "SPP+COPPER slack CTLW misses: 131; reduction versus naive DMP: 98.2%.",
                    "All policies used process-separated AF_INET TCP loopback inside a private user/network namespace with a forked TLS server process.",
                    "status=TCP_NETNS_PROCESS_PASS",
                ),
            ),
            Evidence(
                RESULTS / "OPENSSL_TCP_PROCESS_SEED_STABILITY_20260620.md",
                (
                    "OpenSSL TCP Process-Server Seed Stability",
                    "Process-server seed points: 2.",
                    "Distinct seed checksums: 2.",
                    "Total forked process TCP pairs across policies/seeds: 10.",
                    "Child process failures across policies/seeds: 0.",
                    "Minimum COPPER CTLW reduction versus naive DMP: 98.5%.",
                    "Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 98.1%.",
                    "COPPER/slack translation faults across both seeds: 0.",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "OPENSSL_TCP_PROCESS_SCALE_PORTFOLIO_20260620.md",
                (
                    "OpenSSL TCP Process-Server Scale Portfolio",
                    "Portfolio points: 4.",
                    "Distinct checksums: 4.",
                    "Total forked process TCP pairs across policies/points: 70.",
                    "Minimum COPPER CTLW reduction versus naive DMP: 98.2%.",
                    "Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 98.1%.",
                    "COPPER/slack translation faults across portfolio: 0.",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_ossltlstcp_app" / "ossltlstcp_TCP_FALLBACK_PROBE_FS_SUMMARY.md",
                (
                    "OpenSSL libssl TLS TCP Loopback AArch64 Full-System Summary",
                    "Transport modes observed: af_unix_fallback.",
                    "Naive DMP CTLW misses: 8839; COPPER CLPD-64K+PEB CTLW misses: 177; reduction: 98.0%.",
                    "SPP+COPPER slack CTLW misses: 245; reduction versus naive DMP: 97.2%.",
                    "status=AF_UNIX_FALLBACK_PASS",
                ),
            ),
            Evidence(
                RESULTS / "OPENSSL_MEDIUM_SEED_STABILITY_20260619.md",
                (
                    "OpenSSL libcrypto EVP/HMAC/SHA | 2 | 95.0% / 95.0%",
                    "OpenSSL libssl TLS memory-BIO | 2 | 98.8% / 98.8%",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "SQLITE_MEDIUM_STRESS_SEED_STABILITY_20260619.md",
                (
                    "SQLite Medium/Stress Seed Stability",
                    "Across all 5 SQLite medium/stress seed points, COPPER CTLW reduction is at least 90.3%",
                    "Across all 5 SQLite medium/stress seed points, SPP+COPPER slack CTLW reduction is at least 86.4%",
                    "Worst absolute SPP+COPPER slack tick gap versus SPP is 0.056 percentage points",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_sqlite_speedtest1" / "SQLITE_SPEEDTEST1_SPEEDTEST1_JSON_SMOKE_SIZE1_FS_SUMMARY.md",
                (
                    "SQLite speedtest1 AArch64 Full-System Summary",
                    "unmodified upstream SQLite speedtest1 workload built from SQLite 3.53.2",
                    "Verification hash agreement: yes",
                    "Verification byte-count agreement: 0",
                    "Naive DMP CTLW misses: 12802; COPPER CLPD-64K+PEB CTLW misses: 983; reduction: 92.3%",
                    "Translation faults: naive=0, COPPER=0, SPP=0, SPP+COPPER-slack=0",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_sqlite_speedtest1" / "SQLITE_SPEEDTEST1_SPEEDTEST1_STAR_SMOKE_SIZE1_FS_SUMMARY.md",
                (
                    "SQLite speedtest1 AArch64 Full-System Summary",
                    "--testset star",
                    "Verification byte-count agreement: 0",
                    "Naive DMP CTLW misses: 6844; COPPER CLPD-64K+PEB CTLW misses: 340; reduction: 95.0%",
                    "Translation faults: naive=0, COPPER=0, SPP=0, SPP+COPPER-slack=0",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_sqlite_speedtest1" / "SQLITE_SPEEDTEST1_SPEEDTEST1_ORM_SMOKE_SIZE1_FS_SUMMARY.md",
                (
                    "SQLite speedtest1 AArch64 Full-System Summary",
                    "--testset orm",
                    "Verification byte-count agreement: 408505",
                    "Naive DMP CTLW misses: 38552; COPPER CLPD-64K+PEB CTLW misses: 1197; reduction: 96.9%",
                    "Translation faults: naive=0, COPPER=0, SPP=0, SPP+COPPER-slack=0",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "SQLITE_SPEEDTEST1_COMPONENTS_20260619.md",
                (
                    "SQLite speedtest1 Component Summary",
                    "Components: 3.",
                    "Minimum COPPER CTLW reduction versus naive DMP: 92.3%.",
                    "Minimum SPP+COPPER slack CTLW reduction versus naive DMP: 88.5%.",
                    "Translation faults across key policies and components: 0.",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "LUA_DUKTAPE_MEDIUM_STRESS_SEED_STABILITY_20260619.md",
                (
                    "Lua/Duktape Medium/Stress Seed Stability",
                    "Across all 10 Lua/Duktape medium/stress seed points, COPPER CTLW reduction is at least 76.7%",
                    "Across all 10 Lua/Duktape medium/stress seed points, SPP+COPPER slack CTLW reduction is at least 85.0%",
                    "Worst absolute SPP+COPPER slack tick gap versus SPP is 0.760 percentage points",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "YYJSON_MEDIUM_STRESS_SEED_STABILITY_20260619.md",
                (
                    "yyjson Medium/Stress Seed Stability",
                    "Across all 4 yyjson medium/stress seed points, COPPER CTLW reduction is at least 98.9%",
                    "Across all 4 yyjson medium/stress seed points, SPP+COPPER slack CTLW reduction is at least 97.4%",
                    "Worst absolute SPP+COPPER slack tick gap versus SPP is 0.089 percentage points",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "JSONSQLITE_MEDIUM_SEED_STABILITY_20260619.md",
                (
                    "JSON+SQLite Medium Two-Seed Stability",
                    "COPPER CTLW reduction is at least 95.0%",
                    "SPP+COPPER slack CTLW reduction is at least 95.9%",
                    "Worst absolute SPP+COPPER slack tick gap versus SPP is 0.026 percentage points",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "JSONSQLITE_STRESS_SEED_STABILITY_20260619.md",
                (
                    "JSON+SQLite Stress Two-Seed Stability",
                    "COPPER CTLW reduction is at least 91.4%",
                    "SPP+COPPER slack CTLW reduction is at least 96.6%",
                    "Worst absolute SPP+COPPER slack tick gap versus SPP is 0.069 percentage points",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_osslsha_app" / "OSSLSHA_APP_SMOKE_FS_SUMMARY.md",
                (
                    "OpenSSL libcrypto's exported `SHA256` routine",
                    "Naive DMP CTLW misses: 10590; COPPER CLPD-64K+PEB CTLW misses: 301; reduction: 97.2%",
                    "SPP+COPPER slack CTLW misses: 259; reduction versus naive DMP: 97.6%",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_osslcrypto_app" / "OSSLCRYPTO_APP_SMOKE_FS_SUMMARY.md",
                (
                    "OpenSSL libcrypto EVP AES-128-CTR, HMAC-SHA256, SHA256, and",
                    "Naive DMP CTLW misses: 16685; COPPER CLPD-64K+PEB CTLW misses: 954; reduction: 94.3%",
                    "SPP+COPPER slack CTLW misses: 828; reduction versus naive DMP: 95.0%",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_osslcrypto_app" / "OSSLCRYPTO_APP_MEDIUM_FS_SUMMARY.md",
                (
                    "Input tag: `app_medium`",
                    "Naive DMP CTLW misses: 17857; COPPER CLPD-64K+PEB CTLW misses: 892; reduction: 95.0%",
                    "SPP+COPPER slack CTLW misses: 716; reduction versus naive DMP: 96.0%",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_osslspeed_app" / "OSSLSPEED_APP_SMOKE_FS_SUMMARY.md",
                (
                    "fixed benchmark-style buffer sizes",
                    "Naive DMP CTLW misses: 16353; COPPER CLPD-64K+PEB CTLW misses: 1257; reduction: 92.3%",
                    "SPP+COPPER slack CTLW misses: 1093; reduction versus naive DMP: 93.3%",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "OPENSSL_SPEEDLIKE_SEED_STABILITY_20260619.md",
                (
                    "COPPER CTLW reduction is stable at 92.3% minimum across the two seeds",
                    "SPP+COPPER slack CTLW reduction is stable at 92.7% minimum across the two seeds",
                    "Worst absolute SPP+COPPER slack gap versus SPP is 0.089 percentage points",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "OPENSSL_CLI_FEASIBILITY_20260619.md",
                (
                    "compatibility_status=PASS",
                    "official_speed_status=NOT_LOCALLY_TRACTABLE_UNDER_TIMING_GEM5",
                    "not counted as a benchmark result",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_osslcli_app" / "OSSLCLI_FIXED_64K_FS_SUMMARY.md",
                (
                    "official Ubuntu ARM64 `openssl` CLI binary",
                    "Naive DMP CTLW misses: 15940; COPPER CLPD-64K+PEB CTLW misses: 387; reduction: 97.6%",
                    "SPP+COPPER slack CTLW misses: 415; reduction versus naive DMP: 97.4%",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_osslcli_app" / "OSSLCLI_AESCTR_64K_FS_SUMMARY.md",
                (
                    "Official OpenSSL CLI AES-CTR Fixed-Workload",
                    "Naive DMP CTLW misses: 32174; COPPER CLPD-64K+PEB CTLW misses: 1463; reduction: 95.5%",
                    "SPP+COPPER slack CTLW misses: 1549; reduction versus naive DMP: 95.2%",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_osslcli_app" / "OSSLCLI_HMAC_64K_FS_SUMMARY.md",
                (
                    "Official OpenSSL CLI HMAC-SHA256 Fixed-Workload",
                    "Naive DMP CTLW misses: 16903; COPPER CLPD-64K+PEB CTLW misses: 524; reduction: 96.9%",
                    "SPP+COPPER slack CTLW misses: 435; reduction versus naive DMP: 97.4%",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "OPENSSL_CLI_SEED_STABILITY_20260619.md",
                (
                    "Official OpenSSL CLI Multi-Seed Stability",
                    "Official OpenSSL CLI AES-CTR + digest | 3 | 95.5% / 95.5%",
                    "Across 9 official CLI seed/workload points, COPPER CTLW reduction is at least 95.5%",
                    "Across 9 official CLI seed/workload points, SPP+COPPER slack CTLW reduction is at least 95.2%",
                    "Worst absolute SPP+COPPER slack gap versus SPP is 0.294 percentage points",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_tlssvc_app" / "TLSSVC_APP_SMOKE_FS_SUMMARY.md",
                (
                    "TLS/session-service style native AArch64 Linux ROI",
                    "Naive DMP CTLW misses: 3680; COPPER CLPD-64K+PEB CTLW misses: 18; reduction: 99.5%",
                    "SPP+COPPER slack CTLW misses: 19; reduction versus naive DMP: 99.5%",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_cachesvc_app" / "CACHESVC_NOPOISON_CONTROL_AUDIT.md",
                (
                    "VALID_STRESS_POINT_NOT_CLEAN_SECURITY_ORACLE",
                    "Use the fake-only ROI, secret traffic oracle, observer oracle, and split scan/probe audit for differential security claims",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_cachesvc_app" / "CACHESVC_SEED_STABILITY_AUDIT.md",
                (
                    "COPPER CTLW reduction versus naive DMP is stable across 2 seeds",
                    "SPP+COPPER slack CTLW reduction versus naive DMP is stable across 2 seeds",
                    "seed_stability_status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_cachesvc_app" / "CACHESVC_SCALE_SENSITIVITY_AUDIT.md",
                (
                    "COPPER CTLW reduction versus naive DMP across scales",
                    "SPP+COPPER slack CTLW reduction versus naive DMP across scales",
                    "scale_sensitivity_status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_yyjson_app" / "YYJSON_APP_STRESS_FS_SUMMARY.md",
                (
                    "public yyjson JSON-parser workload",
                    "Input tag: `app_stress`",
                    "reduction: 98.9%",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_gapbs_official_suite" / "GAPBS_OFFICIAL_SUITE_FINAL_G14_FS_SUMMARY.md",
                (
                    "copper_clpd64k_peb",
                    "zero fill-origin translation faults",
                    "The official GAPBS blocker is now materially reduced",
                ),
            ),
            Evidence(
                RESULTS / "gem5_arm_ubuntu_fs_olden_suite" / "OLDEN_BUILTIN_BASELINES.md",
                (
                    "medium randomized subset",
                    "copper_clpd64k_peb",
                    "AMPM",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_PUBLIC_APP_REPEATED_SEED_PORTFOLIO_20260617.md",
                (
                    "Engine-seed points: 15; policy rows: 75",
                    "Overall COPPER CTLW reduction versus naive DMP: 90.706%",
                    "Worst absolute SPP+COPPER slack gap versus SPP: 0.760 percentage points",
                    "status=PASS",
                ),
            ),
        ),
        "Still not SPEC, production server software, a production TCP/TLS server, or completed timer-driven official OpenSSL speed results under full-system Linux.",
        "The top-tier path is broader application campaigns and larger-scale runtime/database/full-crypto workloads; the standalone SQLite, upstream SQLite speedtest1 components, Lua/Duktape, yyjson seed-stability runs, two-seed PCRE2 regex point, public MiBench Patricia trie point, two-seed 12K completed Patricia comparison plus 16K/32K/full-large Patricia feasibility attempts, public libxml2 XML parser/serializer point, public libarchive TAR parser point, two-seed Zstd/zlib compression points, medium/stress two-seed JSON+SQLite service-composition runs, two-seed medium OpenSSL libssl/libcrypto runs, the socket-backed libssl run, tagged TCP-harness AF_UNIX fallback diagnostic, strict private-netns TCP-loopback libssl run, four-point process-separated private-netns TCP-loopback libssl portfolio, speed-like driver, official CLI compatibility run, and multi-seed official CLI fixed digest/AES/HMAC runs reduce but do not eliminate this gap.",
    ),
    Claim(
        "C7",
        "The RTL evidence covers a composed backend-to-SoC authority path.",
        "The local Vivado evidence includes LSQ source-tag capture, CEPF proof filtering, a ROPL-LSQ retire guard, a ROCCA-to-CLPD clear-wins proof-write adapter, CAVI final source-plus-target authority issue interlock, AMBA/SARI frontdoor revocation, CLPD, and CTLW with XSim randomized testing and synthesis timing.",
        (
            Evidence(
                RESULTS / "COPPER_AMBA_SARI_FRONTDOOR_RTL_SUMMARY.md",
                (
                    "COPPER AMBA-SARI Frontdoor RTL Summary",
                    "Directed cases | 10",
                    "Randomized cycles | 10,000",
                    "Slice LUTs | 8",
                    "Worst setup slack | +7.525 ns",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_ROPL_LSQ_RETIRE_GUARD_RTL_SUMMARY.md",
                (
                    "COPPER ROPL-LSQ Retire Guard RTL Summary",
                    "Directed hazard cases | 18",
                    "Randomized cycles | 20,000",
                    "Slice LUTs | 14",
                    "Worst setup slack | +6.492 ns",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_ROCCA_CLPD_COMMIT_ADAPTER_RTL_SUMMARY.md",
                (
                    "COPPER ROCCA-to-CLPD Commit Adapter RTL Summary",
                    "Slice LUTs | 4,302",
                    "Slice registers | 2,624",
                    "WNS at 10 ns | 1.149 ns",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_CAVI_AUTHORITY_ISSUE_GATE_RTL_SUMMARY.md",
                (
                    "COPPER CAVI Authority Issue Gate RTL Summary",
                    "Commit-Authority Validity Interlock",
                    "Randomized trials | 20,000",
                    "Random target revocation conflicts | 3,996",
                    "Slice LUTs | 4,591",
                    "WNS at 10 ns | 1.149 ns",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "copper_full_lsq_amba_authority_xsim_20260616.log",
                ("COPPER full LSQ-AMBA authority completed", "random=10000", "errors=0"),
            ),
            Evidence(
                RESULTS / "COPPER_TLB_COHERENCE_AUTHORITY_FILTER_RTL_SUMMARY.md",
                (
                    "directed=27 random=10000",
                    "Slice LUTs | 332",
                    "WNS | +6.898 ns",
                    "status=PASS",
                ),
            ),
            Evidence(
                ROOT / "research" / "COPPER_AMBA_CHI_ACE_EVENT_MAP_20260619.md",
                (
                    "COPPER SARI/CS-SARI AMBA CHI/ACE Event Map",
                    "DVM/TLBI or translation-context invalidation",
                    "Same-line write by CPU, DMA, coherent I/O, or accelerator",
                    "not a complete CHI/ACE/AXI decoder",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "copper_full_lsq_amba_authority_top_timing.rpt",
                ("All user specified timing constraints are met",),
            ),
            Evidence(
                RESULTS / "copper_full_lsq_amba_authority_top_synth.log",
                ("synth_design completed successfully",),
            ),
        ),
        "This is not a production ARM out-of-order LSQ or full CHI/ACE implementation.",
        "Keep the claim at RTL-representative integration evidence, not production signoff.",
    ),
    Claim(
        "C8",
        "The storage structures have plausible FPGA synthesis/route and power-proxy evidence.",
        "The scalable 64K CLPD SRAM directory and PEB boundary block have local Vivado synthesis/route evidence with positive timing slack; power evidence now includes a 15-checkpoint vectorless pass, a routed CLPD testbench-SAIF activity pass, a measured workload-counter-derived CLPD SAIF replay, a TCP process-server CLPD SAIF replay, a 22-row metadata-toggle sensitivity bound, and a TCP process-server metadata-toggle bound.",
        (
            Evidence(
                RESULTS / "COPPER_CLPD_SRAM_SYNTH_SUMMARY.md",
                ("64K", "0.362 ns", "260"),
            ),
            Evidence(
                RESULTS / "COPPER_PEB_RTL_SUMMARY.md",
                ("+3.782 ns", "errors=0", "CLPD-64K+PEB blocks 131,066 of 131,066"),
            ),
            Evidence(
                RESULTS / "COPPER_RTL_POWER_PROXY_20260618.md",
                (
                    "Checkpoints attempted: 15",
                    "Successful reports: 15",
                    "Routed 64K-entry CLPD on xc7a200t: 0.479 W total, 0.344 W dynamic",
                    "not calibrated ASIC power",
                    "I/O-dominated in out-of-context Vivado reporting",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_CLPD_ACTIVITY_POWER_20260619.md",
                (
                    "directed=18 random=4000",
                    "| SAIF | 37%   (126/342) | 0.076 | 0.007 | 0.069 | Medium | WNS 2.208 ns, constraints met |",
                    "Vivado matched 126 of 342 design nets",
                    "not a calibrated ASIC or workload-derived full-system power result",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_WORKLOAD_CLPD_ACTIVITY_POWER_20260619.md",
                (
                    "Raw driver events: 1,318,318",
                    "| Workload-derived SAIF | 37%   (226/611) | 0.083 | 0.014 | 0.069 | Medium | WNS 1.807 ns |",
                    "not an instruction-by-instruction full-system waveform",
                    "stronger than a random testbench SAIF",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_METADATA_TOGGLE_BOUND_20260619.md",
                (
                    "Total metadata events: 1,467,759",
                    "Even the deliberately high scenario is 0.1801%",
                    "not calibrated silicon power",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "OPENSSL_TCP_PROCESS_METADATA_TOGGLE_BOUND_20260620.md",
                (
                    "Metadata reads | Metadata writes | Metadata events",
                    "| copper_clpd64k_peb | 4 | 14 | 170,564",
                    "| spp_copper_slack | 4 | 14 | 261,979",
                    "This does not prove full-chip power",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_TCP_PROCESS_CLPD_ACTIVITY_POWER_20260620.md",
                (
                    "Source policy: `spp_copper_slack`",
                    "XSim result: `COPPER CLPD workload activity replay completed: source_label=tcp_process_spp_copper_slack",
                    "| TCP process-server SAIF | 37%   (226/611) | 0.083 | 0.014 | 0.069 | Medium | WNS 1.807 ns |",
                    "status=PASS",
                ),
            ),
        ),
        "FPGA resource reports, vectorless power estimates, testbench SAIF, transaction-level workload-counter replay, and pJ/access accounting are not ASIC area/power signoff or instruction-by-instruction full-system switching power.",
        "Use as hardware plausibility and metadata-power-proxy evidence; add instruction-level full-system switching or ASIC PPA later if available.",
    ),
    Claim(
        "C9",
        "Bounded checkers and SVA harnesses tie the named rules to executable invariants.",
        "The artifact includes bounded state-space checks and SVA-style RTL harnesses for CEPF/PASB/CTLW, CLPD, SARI/CS-SARI, an OoO-LSQ proof contract, a ROPL replay/exception/alias contract, a ROPL-LSQ retire guard RTL check, the ROCCA-to-CLPD clear-wins proof-write adapter, the CAVI final source-plus-target authority issue interlock, a TLB/coherence authority contract, a matching TLB/coherence RTL filter, and weakened variants.",
        (
            Evidence(
                RESULTS / "COPPER_SARI_RQ_STATE_SPACE.md",
                ("PASS", "ready-respecting states", "overflow"),
            ),
            Evidence(
                RESULTS / "copper_lsq_cepf_line_e2e_xsim_20260616.log",
                ("COPPER LSQ-CEPF-line E2E completed", "random=10000", "errors=0"),
            ),
            Evidence(
                RESULTS / "COPPER_SECURITY_COVERAGE_MATRIX.md",
                ("PASS", "unsafe", "Residual risk"),
            ),
            Evidence(
                RESULTS / "COPPER_OOO_LSQ_PROOF_CONTRACT.md",
                (
                    "Full contract status: PASS",
                    "Every weakened variant has a short counterexample",
                    "BUG_EXECUTE_STAGE_PROOF",
                    "BUG_NO_TRANSLATION_PERMISSION_GATE",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_OOO_REPLAY_EXCEPTION_ALIAS_CONTRACT.md",
                (
                    "Full ROPL contract status: PASS",
                    "FULL_ROPL_CONTRACT | 888 | 1 | 0",
                    "BUG_NO_REPLAY_GENERATION",
                    "BUG_NO_ALIAS_GENERATION",
                    "BUG_NO_ORDER_VIOLATION_CLEAR",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "copper_ropl_lsq_retire_guard_xsim_20260620.log",
                (
                    "COPPER ROPL-LSQ retire guard completed",
                    "random=20000",
                    "errors=0",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_ROCCA_CLPD_COMMIT_ADAPTER_RTL_SUMMARY.md",
                (
                    "COPPER ROCCA-to-CLPD Commit Adapter RTL Summary",
                    "Retirement-Ordered Clear-wins CLPD Adapter",
                    "Randomized cycles | 20,000",
                    "Same-cycle clear-wins blocks | 1,598",
                    "WNS at 10 ns | 1.149 ns",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_CAVI_AUTHORITY_ISSUE_GATE_RTL_SUMMARY.md",
                (
                    "COPPER CAVI Authority Issue Gate RTL Summary",
                    "issue only if the ROCCA/CLPD source proof is valid",
                    "Randomized trials | 20,000",
                    "Random clear-wins proof suppressions | 2,021",
                    "Random target revocation conflicts | 3,996",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_TLB_COHERENCE_CONTRACT.md",
                (
                    "Full-contract reachable states explored: 39098",
                    "BUG_NO_TARGET_QUEUE_HOLD",
                    "BUG_NO_PERMISSION_GATE",
                    "BUG_PAGE_LEVEL_TARGET_WITNESS",
                    "Full contract status: PASS",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_TLB_COHERENCE_AUTHORITY_FILTER_RTL_SUMMARY.md",
                (
                    "same-cycle and queued source revocation",
                    "same-cycle and queued target remap",
                    "unrelated source/target revocation precision allow",
                    "status=PASS",
                ),
            ),
        ),
        "Bounded model checks are not a full formal proof of the production memory hierarchy.",
        "Use the checkers to show rule coverage and counterexamples, not absolute correctness.",
    ),
    Claim(
        "C10",
        "The current package is an evidence-bounded regular conference or artifact-track candidate, not an acceptance guarantee.",
        "Current evidence is strong enough for a serious evidence-bounded architecture/security submission, but acceptance and stronger production/silicon claims remain unproven because broader raw-run workloads and production-grade integration are still open.",
        (
            Evidence(
                RESULTS / "COPPER_READINESS_AUDIT_20260616.md",
                (
                    "Evidence-bounded regular-conference or artifact-track candidate",
                    "SPEC-like",
                    "OoO/coherence integration",
                    "TLB/coherence",
                    "contract checker",
                    "RTL filter",
                    "energy/pollution",
                    "scorecard",
                ),
            ),
            Evidence(
                ROOT / "research" / "COPPER_FINAL_OUTPUT.md",
                (
                    "8/10 focused venue, 7/10 top-tier today",
                    "top-tier still needs broader application evidence",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_PUBLIC_ARTIFACT_MANIFEST_20260620.md",
                (
                    "COPPER Public Artifact Manifest",
                    "Manifest entries:",
                    "Missing referenced files: 0",
                    "include-in-minimal-package |",
                    "external-store-with-hash | 2",
                    "status=PASS",
                ),
            ),
            Evidence(
                RESULTS / "COPPER_PUBLIC_ARTIFACT_PACKAGE_BUILD_20260620.md",
                (
                    "COPPER Public Artifact Package Build",
                    "Direct-package rows copied:",
                    "Package files present:",
                    "Missing files: 0",
                    "Hash mismatches: 0",
                    "status=PASS",
                ),
            ),
        ),
        "The user objective asks for a guarantee, but no honest research process can guarantee acceptance.",
        "Continue closing concrete reviewer risks while preserving honest verdict language.",
    ),
)


GATES = (
    (
        "Novelty and positioning",
        ("C1", "C2"),
        "PASS_WITH_PUBLIC_KNOWLEDGE_CAVEAT",
        "The exact authority invariant remains defensible, but the paper must not claim metadata or pointer prefetching as new.",
    ),
    (
        "Security evidence",
        ("C3", "C9"),
        "STRONG_FOR_MODELED_THREAT",
        "Split oracle and checkers are strong for modeled DMP data-at-rest activation; full production hierarchy proof remains future work.",
    ),
    (
        "Performance and baselines",
        ("C4", "C5", "C6"),
        "FAIR_BUT_NOT_UNIVERSAL_SPEEDUP",
        "Conventional SPP wins speed; SCOOP coexistence is the stronger claim, with quantified traffic side effects.",
    ),
    (
        "Hardware feasibility",
        ("C7", "C8", "C9"),
        "PLAUSIBLE_RTL_EVIDENCE",
        "Vivado/XSim plus vectorless and SAIF-driven RTL power reporting, the OoO-LSQ/ROCCA proof-write checks, CAVI source-plus-target issue interlock, and TLB/coherence contract/filter evidence are meaningful but not ASIC signoff or production ARM integration.",
    ),
    (
        "Reproducibility package",
        ("C3", "C4", "C6", "C7"),
        "GOOD_LOCAL_ARTIFACT",
        "Environment documentation, a generated public manifest, and a materialized local package now exist; external hosting and third-party rerun remain future artifact work.",
    ),
    (
        "Top-tier readiness",
        ("C1", "C3", "C4", "C6", "C7", "C10"),
        "NEAR_MISS_NOT_GUARANTEED",
        "The strongest remaining gaps are SPEC-like applications, production-service or production TCP/TLS/standard crypto benchmark workloads, instruction-level full-system switching or ASIC-calibrated metadata power beyond the local FPGA/McPAT/transaction-replay proxies, and production-grade OoO/SoC integration beyond bounded contracts.",
    ),
)


def build_matrix() -> tuple[dict[str, bool], list[str]]:
    claim_pass: dict[str, bool] = {}
    lines = [
        "# COPPER/SCOOP Claim-to-Evidence Matrix",
        "",
        "Date: 2026-06-20",
        "",
        "Purpose: make every major paper claim auditable against local artifacts. This file is evidence packaging, not a new proof. Claims keep the required public-knowledge and non-guarantee caveats.",
        "",
        "| ID | Claim | Allowed wording | Evidence status | Evidence artifacts | Reviewer risk | Remaining gap |",
        "|---|---|---|---|---|---|---|",
    ]
    for claim in CLAIMS:
        evidence_bits: list[str] = []
        ok_all = True
        for evidence in claim.evidence:
            ok, detail = evidence_status(evidence)
            ok_all = ok_all and ok
            evidence_bits.append(f"`{rel(evidence.path)}` ({detail})")
        claim_pass[claim.claim_id] = ok_all
        lines.append(
            f"| {claim.claim_id} | {claim.wording} | {claim.allowed_wording} | "
            f"{'PASS' if ok_all else 'FAIL'} | {'<br>'.join(evidence_bits)} | "
            f"{claim.reviewer_risk} | {claim.remaining_gap} |"
        )
    lines.extend(
        [
            "",
            "## Use In The Paper",
            "",
            "- Claims marked PASS have local artifact support for the exact allowed wording, not for stronger wording.",
            "- No row justifies saying the idea is guaranteed to pass a top-tier conference.",
            "- If the paper makes a stronger claim than the allowed wording above, that claim should be treated as unsupported until new evidence is added.",
            "",
        ]
    )
    OUT_MATRIX.write_text("\n".join(lines), encoding="utf-8")
    return claim_pass, lines


def build_gate(claim_pass: dict[str, bool]) -> None:
    lines = [
        "# COPPER/SCOOP Top-Tier Gate Audit",
        "",
        "Date: 2026-06-20",
        "",
        "This audit asks whether the current package is ready for a top-tier architecture/security PhD-conference submission. It intentionally cannot and does not guarantee acceptance.",
        "",
        "| Gate | Dependent claims | Local evidence result | Gate verdict | Remaining issue |",
        "|---|---|---:|---|---|",
    ]
    all_gate_claims_pass = True
    for gate, claim_ids, verdict, issue in GATES:
        gate_ok = all(claim_pass.get(claim_id, False) for claim_id in claim_ids)
        all_gate_claims_pass = all_gate_claims_pass and gate_ok
        lines.append(
            f"| {gate} | {', '.join(claim_ids)} | {'PASS' if gate_ok else 'FAIL'} | {verdict} | {issue} |"
        )

    final = "EVIDENCE_BOUNDED_SUBMISSION_READY__ACCEPTANCE_NOT_GUARANTEED"
    if not all_gate_claims_pass:
        final = "EVIDENCE_GATES_FAIL__DO_NOT_SUBMIT"

    lines.extend(
        [
            "",
            "## Final Gate Result",
            "",
            f"`{final}`",
            "",
            "The current package is an evidence-bounded regular-conference or artifact-track candidate: it has public prior-art deltas, AArch64 full-system runs, adversarial DMP oracles, fair conventional baselines, repeated medium/stress public-engine layout evidence including two-seed PCRE2 regex matching, public MiBench Patricia two-seed 12K trie execution with larger Patricia feasibility probes, public libxml2 XML parser/serializer execution, public libarchive TAR parser execution, and two-seed Zstd/zlib compression/decompression, bounded service-style and crypto-adjacent full-system stress points, real OpenSSL libssl TLS memory-BIO small/medium two-seed execution, socket-backed OpenSSL libssl TLS execution, strict private-netns TCP-loopback OpenSSL libssl TLS execution, a four-point process-separated private-netns TCP-loopback OpenSSL libssl TLS portfolio, real OpenSSL libcrypto SHA256 plus small/medium EVP/HMAC two-seed drivers, fixed-buffer and multi-seed official OpenSSL CLI crypto evidence, gem5-counter energy/pollution, gem5 DRAM-energy, McPAT-sensitivity, Vivado vectorless/testbench-SAIF/workload-counter-replay/TCP-process-replay RTL power-proxy scorecards, app/service/parser/compression/TCP and TCP process-server metadata-toggle sensitivity bounds, Vivado RTL checks, synthesis/timing reports, an AMBA-SARI frontdoor RTL check, OoO-LSQ and TLB/coherence contract checkers, ROPL-LSQ retire guard plus ROCCA-to-CLPD clear-wins proof-write RTL checks, CAVI source-plus-target final issue interlock RTL evidence, a matching TLB/coherence RTL filter, and a passing artifact audit. It is still not honest to call acceptance guaranteed. The next evidence that would move the needle most for stronger claims is a SPEC-like application or production-service/production-TCP-TLS/standard-crypto-benchmark campaign, instruction-level full-system switching or ASIC-calibrated metadata power beyond the local FPGA/McPAT/transaction-replay proxies, plus production-style OoO/TLB/coherence integration beyond bounded contracts.",
            "",
        ]
    )
    OUT_GATE.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    claim_pass, _ = build_matrix()
    build_gate(claim_pass)
    print(OUT_MATRIX)
    print(OUT_GATE)


if __name__ == "__main__":
    main()
