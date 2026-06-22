#!/usr/bin/env python3
"""Generate an evidence-backed COPPER security coverage matrix.

Each row maps an unsafe DMP behavior class to the COPPER mechanism that should
block it and to local evidence files. The script checks for expected strings in
those files before marking the row covered, so the matrix is tied to artifacts
rather than hand-written claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "results" / "COPPER_SECURITY_COVERAGE_MATRIX.md"


@dataclass(frozen=True)
class Evidence:
    path: str
    must_contain: tuple[str, ...]
    note: str


@dataclass(frozen=True)
class CoverageRow:
    unsafe_class: str
    mechanism: str
    security_contract: str
    evidence: tuple[Evidence, ...]
    residual_risk: str


ROWS = [
    CoverageRow(
        unsafe_class="Pointer-shaped data at rest",
        mechanism="COPPER-LINE committed source proof",
        security_contract="A memory word that merely looks like an address must not authorize DMP dereference.",
        evidence=(
            Evidence(
                "research/results/COPPER_RESULTS.md",
                ("| naive | 3.628x | 4032 | 2048", "| copper_line | 2.414x | 1416 | 0 | 0 | 0 | 0 |"),
                "Synthetic trace: naive prefetches data-at-rest; COPPER-LINE does not.",
            ),
            Evidence(
                "research/results/gapbs_copper_trace/GAPBS_COPPER_TRACE_SUMMARY.md",
                ("| naive | 4.096x", "| copper_line_epoch | 1.896x", "| copper_line_epoch | 1.896x | 56,266.9 | 287,642.3 | 118,547.4 | 0.0 | 0.0 | 0.0 |"),
                "GAPBS-backed topology trace: CLPD has zero data-at-rest, unproven-edge, and stale-slot prefetches.",
            ),
            Evidence(
                "research/results/gapbs_copper_kernel_sensitivity/GAPBS_COPPER_KERNEL_SENSITIVITY.md",
                ("Policy runs: 4,320", "COPPER unsafe modeled prefetches: 0", "Naive unsafe modeled prefetches: 81,605,320", "| copper_line_epoch | 864 | 1.649x"),
                "Expanded GAPBS-style kernel sensitivity keeps COPPER unsafe modeled prefetches at zero while naive remains unsafe.",
            ),
        ),
        residual_risk="Trace-level evidence; needs known-attack binary reproduction on real hardware or richer full-system traces.",
    ),
    CoverageRow(
        unsafe_class="Unproven first-use source word",
        mechanism="Per-word proof bit/ledger entry",
        security_contract="First observation of a pointer-looking word cannot be used until committed demand execution proves it.",
        evidence=(
            Evidence(
                "research/results/COPPER_RESULTS.md",
                ("Naive unproven line", "| 0.00 | 4.080x", "| 0.50 | 2.380x"),
                "Rewrite sensitivity keeps COPPER unproven-line count at zero while naive remains unsafe.",
            ),
            Evidence(
                "research/results/copper_clpd_xsim.log",
                ("no_entry=4864", "word_unproven=12", "errors=0"),
                "CLPD RTL simulation exercises no-entry and word-unproven block classes.",
            ),
            Evidence(
                "research/results/COPPER_FULL_AUTHORITY_SVA_SUMMARY.md",
                ("no_source=4994", "unsound=1260", "allowed=1919"),
                "Full-authority SVA harness asserts allow requires a sound committed source proof.",
            ),
            Evidence(
                "research/results/COPPER_CEPF_LINE_E2E_SVA_SUMMARY.md",
                ("unproven_block=7658", "proof_to_allow=769", "errors=0"),
                "CEPF-to-line end-to-end SVA harness checks unproven sources block and valid CEPF proof can authorize the line gate.",
            ),
            Evidence(
                "research/results/COPPER_CLPD_CTLW_AUTHORITY_E2E_SUMMARY.md",
                ("no_source_block=8468", "word_unproven_block=181", "joint_cross_allow=180", "errors=0"),
                "CLPD-CTLW authority harness checks compressed source proof must exist before the final gate can issue.",
            ),
        ),
        residual_risk="Backend source-word identification still needs production LSQ/dependency integration.",
    ),
    CoverageRow(
        unsafe_class="Cross-domain or source/target token mismatch",
        mechanism="Domain check and PASB/CLPD token binding",
        security_contract="Committed proof cannot cross protection or address-space authority.",
        evidence=(
            Evidence(
                "research/results/COPPER_RESULTS.md",
                ("| naive | 3.628x | 4032 | 2048 | 1076", "| copper_line | 2.414x | 1416 | 0 | 0 | 0 | 0 |"),
                "Synthetic trace: naive cross-domain prefetches disappear under COPPER-LINE.",
            ),
            Evidence(
                "research/results/COPPER_AUTHORITY_STATE_SPACE.md",
                ("BUG_NO_PASB", "address_space_token_mismatch"),
                "Authority checker gives a PASB counterexample when token binding is removed.",
            ),
            Evidence(
                "research/results/COPPER_CLPD_STATE_SPACE.md",
                ("BUG_NO_TOKEN_CHECK", "source_target_token_mismatch"),
                "CLPD checker gives a token-mismatch counterexample when token checking is removed.",
            ),
            Evidence(
                "research/results/COPPER_FULL_AUTHORITY_SVA_SUMMARY.md",
                ("token=233", "a_allow_requires_pasb_token", "allowed=1919"),
                "Full-authority SVA harness asserts allowed seeds require PASB token match.",
            ),
        ),
        residual_risk="Real systems must map the token to ASID/VMID/security-state semantics precisely.",
    ),
    CoverageRow(
        unsafe_class="Stale source after write, fill, invalidation, or backend race",
        mechanism="CEPF plus proof clearing/source epochs",
        security_contract="A source word changed after proof cannot retain or recreate DMP authority.",
        evidence=(
            Evidence(
                "research/results/COPPER_AUTHORITY_STATE_SPACE.md",
                ("BUG_NO_CEPF", "proof_created_from_stale_backend_tag", "BUG_LINE_PROOF_MISSED_SOURCE_INVALIDATE"),
                "Authority checker finds stale backend and missed source-invalidation counterexamples.",
            ),
            Evidence(
                "research/results/gapbs_copper_trace/GAPBS_COPPER_TRACE_SUMMARY.md",
                ("| source_only | 1.808x", "| copper_epoch | 1.770x", "| copper_epoch | 1.770x | 140,166.9 | 126,931.3 | 34,659.1 | 0.0 | 0.0 | 0.0 | 851.3 |"),
                "GAPBS-backed trace: source-only allows stale slots; COPPER epoch/value blocks them.",
            ),
            Evidence(
                "research/results/gapbs_copper_kernel_sensitivity/GAPBS_COPPER_KERNEL_SENSITIVITY.md",
                ("Source-only unsafe modeled prefetches: 284,488", "COPPER unsafe modeled prefetches: 0", "| source_only | 864 | 1.309x", "| copper_epoch | 864 | 1.295x"),
                "Expanded GAPBS-style kernel sweep shows source-only provenance remains unsafe while epoch/value-bound COPPER stays at zero unsafe modeled prefetches.",
            ),
            Evidence(
                "research/results/COPPER_CLPD_STATE_SPACE.md",
                ("BUG_NO_WRITE_CLEAR", "BUG_NO_FILL_CLEAR", "BUG_NO_INVALIDATE_CLEAR"),
                "CLPD checker finds counterexamples for missed destructive line events.",
            ),
            Evidence(
                "research/results/COPPER_FULL_AUTHORITY_SVA_SUMMARY.md",
                ("stale_value=794", "stale_epoch=584", "a_allow_requires_exact_committed_source"),
                "Full-authority SVA harness asserts allowed seeds require exact source value and epoch.",
            ),
            Evidence(
                "research/results/COPPER_CEPF_LINE_E2E_SVA_SUMMARY.md",
                ("stale_epoch_block=151", "write_clear=1", "fill_clear=1", "invalidate_clear=1"),
                "CEPF-to-line end-to-end SVA harness checks stale epochs and destructive line events block or clear proof.",
            ),
            Evidence(
                "research/results/COPPER_CLPD_CTLW_AUTHORITY_E2E_SUMMARY.md",
                ("stale_epoch_block=374", "write_clear_block=1", "fill_clear_block=1", "invalidate_clear_block=1", "errors=0"),
                "CLPD-CTLW authority harness checks stale source-line epochs and source write/fill/invalidate events block at the combined issue predicate.",
            ),
            Evidence(
                "research/results/COPPER_SARI_REVOKER_RTL_SUMMARY.md",
                ("dma=1", "chi=1", "io=1", "hold=6321", "errors=0"),
                "SARI RTL maps DMA, CHI-style, and coherent I/O writes into source-line revocations and immediate DMP hold.",
            ),
            Evidence(
                "research/results/COPPER_SARI_CLPD_CTLW_AUTHORITY_E2E_SUMMARY.md",
                ("dma_post_block=1", "chi_post_block=1", "io_post_block=1", "triple_post_block=1", "errors=0"),
                "SARI-to-CLPD/CTLW authority harness checks external source revocations clear compressed proof and block the final issue predicate.",
            ),
            Evidence(
                "research/results/COPPER_CS_SARI_STATE_SPACE.md",
                ("Reachable states explored: 4509", "BUG_NO_INCOMING_SOURCE_CHECK", "BUG_NO_QUEUED_SOURCE_CHECK", "Overall status: PASS"),
                "CS-SARI state-space checker proves incoming and queued source revocation terms are required for stale-source safety.",
            ),
            Evidence(
                "research/results/COPPER_CS_SARI_COMPOSITION_STATE_SPACE.md",
                ("COMPOSED_CS_SARI | 7555 | PASS | PASS", "BUG_CLPD_STALE_AFTER_REVOCATION", "BUG_TARGET_ONLY_AUTHORITY", "Overall status: PASS"),
                "Composition checker proves stale-source clearing and the source side of the final authority gate are required with CS-SARI.",
            ),
        ),
        residual_risk="Needs full cache-coherence/DMA integration proof in a production memory hierarchy.",
    ),
    CoverageRow(
        unsafe_class="External DMA/coherence update races local metadata clear",
        mechanism="SARI queued revocation plus immediate DMP hold",
        security_contract="A SoC/coherence authority-changing event cannot leave a one-cycle window where stale COPPER metadata still issues DMP.",
        evidence=(
            Evidence(
                "research/results/COPPER_SARI_REVOKER_RTL_SUMMARY.md",
                ("dma=1", "chi=1", "io=1", "triple_burst=1", "hold=6321", "ready_low=4", "overflow=4", "errors=0"),
                "SARI RTL checks DMA/CHI/I/O revocation bursts, queue backpressure/overflow visibility, and immediate DMP hold.",
            ),
            Evidence(
                "research/results/COPPER_SARI_CLPD_CTLW_AUTHORITY_E2E_SUMMARY.md",
                ("hold_block=1828", "dma_hold=1", "chi_hold=1", "io_hold=1", "triple_hold=1", "random_hold=1814", "overflow_hold=1", "errors=0"),
                "The wired SARI-CLPD-CTLW authority harness checks same-cycle external revocation hold and post-drain blocking at the final issue predicate.",
            ),
            Evidence(
                "research/results/COPPER_CS_SARI_AUTHORITY_E2E_SUMMARY.md",
                ("conflict_hold=1245", "matching_source_hold=1", "queued_source_hold=1", "matching_remap_hold=1", "matching_tlbi_hold=1", "avoided_global_hold=1007", "errors=0"),
                "CS-SARI checks the same no-transient-authority contract with candidate-specific conflict hold while avoiding unrelated global stalls.",
            ),
            Evidence(
                "research/results/sari_scoped_trace/SARI_SCOPED_TRACE_SUMMARY.md",
                ("Aggregate hold reduction: 13.01%", "Avoided global holds with authority present: 8186", "CS-SARI unsafe modeled issues: 0", "No-hold unsafe modeled issues: 54724"),
                "Trace-level CS-SARI model measures avoided global holds while preserving zero modeled unsafe stale-authority issues.",
            ),
            Evidence(
                "research/results/cs_sari_gapbs_revocation/CS_SARI_GAPBS_REVOCATION_SUMMARY.md",
                ("Aggregate hold reduction: 82.06%", "Avoided global holds with authority present: 269879", "CS-SARI unsafe modeled issues: 0", "No-hold unsafe modeled issues: 59013"),
                "GAPBS-topology revocation proxy ties CS-SARI safety/stall behavior to graph-derived source and target locality.",
            ),
            Evidence(
                "research/results/COPPER_CS_SARI_STATE_SPACE.md",
                ("CS_SARI | PASS | PASS", "BUG_NO_OVERFLOW_FALLBACK", "Precision Witness", "Overall status: PASS"),
                "Bounded CS-SARI checker proves the scoped hold has no stale-authority counterexample within the model and keeps a precision witness against global hold.",
            ),
            Evidence(
                "research/results/COPPER_CS_SARI_COMPOSITION_STATE_SPACE.md",
                ("BUG_NO_INCOMING_SOURCE_HOLD", "BUG_NO_QUEUED_SOURCE_HOLD", "BUG_NO_OVERFLOW_HOLD", "BUG_GLOBAL_HOLD", "Overall status: PASS"),
                "Composition checker shows source-race and overflow terms are safety-critical while a global hold is a measurable precision failure.",
            ),
            Evidence(
                "research/results/COPPER_TLB_COHERENCE_CONTRACT.md",
                ("incoming_source_revocation", "queued_source_revocation", "BUG_NO_INCOMING_SOURCE_HOLD", "BUG_NO_QUEUED_SOURCE_HOLD", "Full contract status: PASS"),
                "TLB/coherence contract checker separately covers same-cycle and queued source revocation hazards.",
            ),
            Evidence(
                "research/results/COPPER_TLB_COHERENCE_AUTHORITY_FILTER_RTL_SUMMARY.md",
                ("same-cycle and queued source revocation", "unrelated source/target revocation precision allow", "errors=0", "status=PASS"),
                "Synthesizable TLB/coherence filter checks source revocation hold and unrelated-event precision at RTL.",
            ),
            Evidence(
                "research/results/cs_sari_gapbs_revocation/sensitivity/CS_SARI_SENSITIVITY_SWEEP.md",
                ("Configurations: 20", "Total CS-SARI unsafe modeled issues: 0", "Total no-hold unsafe modeled issues: 1649883", "Median hold reduction: 72.06%"),
                "Queue-depth/conflict sensitivity sweep shows CS-SARI safety is not a single-point trace artifact and exposes overflow-driven precision loss.",
            ),
        ),
        residual_risk="SARI is a boundary contract and queue, not a complete AMBA CHI/ACE decoder or full SoC coherence proof.",
    ),
    CoverageRow(
        unsafe_class="Direct-mapped CLPD alias or whole-line overreach",
        mechanism="CLPD line tag and per-word proof mask",
        security_contract="A compressed line entry must not authorize another aliased line or an unproven word in the same line.",
        evidence=(
            Evidence(
                "research/results/COPPER_CLPD_STATE_SPACE.md",
                ("BUG_NO_TAG_CHECK", "BUG_LINE_PROOF_GRANTS_ALL_WORDS"),
                "CLPD checker gives short alias and whole-line-overreach counterexamples.",
            ),
            Evidence(
                "research/results/copper_clpd_xsim.log",
                ("collision=1", "word_unproven=12", "errors=0"),
                "CLPD RTL simulation covers collision eviction and word-unproven blocking.",
            ),
            Evidence(
                "research/results/COPPER_CLPD_CTLW_AUTHORITY_E2E_SUMMARY.md",
                ("clpd_collision=14", "word_unproven_block=181", "errors=0"),
                "CLPD-CTLW authority harness checks CLPD collision eviction and unproven word blocking when CTLW target authority is also present.",
            ),
        ),
        residual_risk="Physical implementation still needs banking/replacement policy evaluation.",
    ),
    CoverageRow(
        unsafe_class="Cross-page recursive target without exact translation authority",
        mechanism="CTLW exact committed target-line witness",
        security_contract="Recursive cross-page targets require exact demand-observed line translation, not page-level or fresh speculative translation.",
        evidence=(
            Evidence(
                "research/results/COPPER_AUTHORITY_STATE_SPACE.md",
                ("BUG_NO_CTLW", "BUG_PAGE_LEVEL_WITNESS", "cross_page_target_without_exact_live_line_witness"),
                "Authority checker gives no-CTLW and page-level-witness counterexamples.",
            ),
            Evidence(
                "research/results/gem5_arm_ubuntu_fs_large_ctlw/FS_LARGE_CTLW_SUMMARY.md",
                ("CTLW-terminal", "zero recursive translation faults", "Terminal stops"),
                "Full-system larger CTLW-terminal runs record zero recursive translation faults.",
            ),
            Evidence(
                "research/results/COPPER_FULL_AUTHORITY_SVA_SUMMARY.md",
                ("missing_witness=131", "wrong_witness=79", "a_allow_requires_target_authority"),
                "Full-authority SVA harness asserts cross-page allow requires exact target-line witness authority.",
            ),
            Evidence(
                "research/results/COPPER_CTLW_WITNESS_RTL_SUMMARY.md",
                ("exact_hit=1484", "miss=6712", "line_mismatch=5162", "errors=0"),
                "CTLW witness directory RTL requires exact target-line match and reports misses for absent or aliased witnesses.",
            ),
            Evidence(
                "research/results/COPPER_CTLW_FULL_AUTHORITY_E2E_SUMMARY.md",
                ("exact_cross_allow=3", "no_witness_block=7102", "line_mismatch_block=6200", "errors=0"),
                "CTLW-to-full-authority integration harness checks exact witnesses open cross-page issue and absent or aliased witnesses block it.",
            ),
            Evidence(
                "research/results/COPPER_CLPD_CTLW_AUTHORITY_E2E_SUMMARY.md",
                ("joint_cross_allow=180", "target_no_witness_block=1239", "target_line_alias_block=1183", "errors=0"),
                "CLPD-CTLW authority harness checks exact target witnesses are required even when compressed source proof is live.",
            ),
            Evidence(
                "research/results/COPPER_CS_SARI_COMPOSITION_STATE_SPACE.md",
                ("BUG_SOURCE_ONLY_AUTHORITY", "BUG_TARGET_ONLY_AUTHORITY", "missing_or_stale_target_truth", "Overall status: PASS"),
                "Composition checker finds counterexamples when the final issue gate omits either source proof or target witness authority.",
            ),
            Evidence(
                "research/results/COPPER_TLB_COHERENCE_CONTRACT.md",
                ("BUG_PAGE_LEVEL_TARGET_WITNESS", "BUG_SOURCE_ONLY_AUTHORITY", "missing_or_stale_target_witness", "Full contract status: PASS"),
                "TLB/coherence contract checker finds page-level target-witness and source-only authority counterexamples.",
            ),
            Evidence(
                "research/results/COPPER_TLB_COHERENCE_AUTHORITY_FILTER_RTL_SUMMARY.md",
                ("non-exact/page-level target witness block", "source-only authority block", "errors=0", "status=PASS"),
                "RTL filter directed tests block page-level/non-exact target witness and source-only authority.",
            ),
        ),
        residual_risk="Needs wider OS/TLBI/remap stress beyond generated workloads.",
    ),
    CoverageRow(
        unsafe_class="Stale target witness after remap/TLBI",
        mechanism="Exact witness invalidation/remap handling",
        security_contract="A target witness cannot survive a remap and authorize the wrong physical line.",
        evidence=(
            Evidence(
                "research/results/COPPER_AUTHORITY_STATE_SPACE.md",
                ("BUG_STALE_PAGE_WITNESS_AFTER_REMAP", "stale page-witness reuse after"),
                "Authority checker includes stale witness/remap counterexample class.",
            ),
            Evidence(
                "research/results/COPPER_FULL_AUTHORITY_SVA_SUMMARY.md",
                ("stale_witness=54", "a_allow_requires_target_authority"),
                "Full-authority SVA harness asserts witness token freshness for target authority.",
            ),
            Evidence(
                "research/results/COPPER_CTLW_WITNESS_RTL_SUMMARY.md",
                ("remap_clear=1", "tlbi_token_clear=112", "tlbi_all_clear=49", "stale_after_remap_block=1", "stale_after_tlbi_block=1"),
                "CTLW witness directory RTL clears exact remap and TLBI-invalidated witnesses before reuse.",
            ),
            Evidence(
                "research/results/COPPER_CTLW_FULL_AUTHORITY_E2E_SUMMARY.md",
                ("stale_after_remap_block=1", "stale_after_tlbi_block=1", "token_mismatch_block=28", "errors=0"),
                "CTLW-to-full-authority integration harness shows remap/TLBI-cleared and token-stale witnesses block at the final DMP issue predicate.",
            ),
            Evidence(
                "research/results/COPPER_CLPD_CTLW_AUTHORITY_E2E_SUMMARY.md",
                ("remap_block=1", "tlbi_block=1", "source_token_block=100", "errors=0"),
                "CLPD-CTLW authority harness checks target remap/TLBI revocation under live compressed source proof.",
            ),
            Evidence(
                "research/results/COPPER_SARI_REVOKER_RTL_SUMMARY.md",
                ("remap=1", "tlbi_token=1", "tlbi_all=1", "hold=6321", "errors=0"),
                "SARI RTL passes target remap/TLBI events to CTLW and holds DMP issue while target authority is being revoked.",
            ),
            Evidence(
                "research/results/COPPER_SARI_CLPD_CTLW_AUTHORITY_E2E_SUMMARY.md",
                ("remap_hold=1", "remap_post_block=1", "tlbi_token_hold=1", "tlbi_token_post_block=1", "tlbi_all_hold=1", "tlbi_all_post_block=1", "errors=0"),
                "SARI-to-CLPD/CTLW authority harness checks same-cycle target revocation hold and post-clear final-gate blocking.",
            ),
            Evidence(
                "research/results/COPPER_CS_SARI_AUTHORITY_E2E_SUMMARY.md",
                ("matching_remap_post_block=1", "matching_tlbi_post_block=1", "tlbi_all_post_block=1", "wrong_token_remap_allow=1", "unrelated_tlbi_allow=1", "errors=0"),
                "CS-SARI confirms target revocation conflicts block while unrelated remaps or token-mismatched invalidations do not unnecessarily hold issue.",
            ),
            Evidence(
                "research/results/COPPER_CS_SARI_STATE_SPACE.md",
                ("BUG_NO_REMAP_CHECK", "BUG_NO_TLBI_TOKEN_CHECK", "BUG_NO_TLBI_ALL_CHECK", "BUG_REMAP_IGNORES_TOKEN_PRECISION", "Overall status: PASS"),
                "CS-SARI state-space checker shows target remap/TLBI terms are safety-critical and token/line precision avoids unrelated over-hold.",
            ),
            Evidence(
                "research/results/COPPER_CS_SARI_COMPOSITION_STATE_SPACE.md",
                ("BUG_CTLW_STALE_AFTER_REMAP", "BUG_CTLW_STALE_AFTER_TOKEN_TLBI", "BUG_CTLW_STALE_AFTER_GLOBAL_TLBI", "missing_or_stale_target_truth", "Overall status: PASS"),
                "Composition checker proves CTLW target clears after remap, token TLBI, and global TLBI are necessary under the final authority gate.",
            ),
            Evidence(
                "research/results/COPPER_TLB_COHERENCE_CONTRACT.md",
                ("BUG_NO_TARGET_REMAP_HOLD", "BUG_NO_TOKEN_TLBI_HOLD", "BUG_NO_GLOBAL_TLBI_HOLD", "BUG_NO_TARGET_QUEUE_HOLD", "Full contract status: PASS"),
                "TLB/coherence contract checker covers remap, token TLBI, global TLBI, queued target revocation, and exact-witness stale-target counterexamples.",
            ),
            Evidence(
                "research/results/COPPER_TLB_COHERENCE_AUTHORITY_FILTER_RTL_SUMMARY.md",
                ("same-cycle and queued target remap", "token TLBI and global TLBI block", "WNS | +6.898 ns", "status=PASS"),
                "RTL filter checks same-cycle/queued target remap plus token/global TLBI and has positive timing slack.",
            ),
        ),
        residual_risk="RTL witness clearing evidence exists; production design still needs integration with the real TLB/cache invalidation fabric.",
    ),
    CoverageRow(
        unsafe_class="Recursive amplification from witness-derived fills",
        mechanism="CTLW terminal-fill rule",
        security_contract="A witness-derived fill may fetch data but cannot recursively seed another DMP request until demand-validating proof exists.",
        evidence=(
            Evidence(
                "research/results/COPPER_AUTHORITY_STATE_SPACE.md",
                ("BUG_NO_TERMINAL", "witness_derived_terminal_source_chased"),
                "Authority checker finds terminal-fill recursion if the terminal rule is removed.",
            ),
            Evidence(
                "research/results/gem5_arm_ubuntu_fs_gapbs_mini/GAPBS_MINI_SUMMARY.md",
                ("7,729 terminal stops", "zero recursive", "translation faults"),
                "Full-system GAPBS-inspired mini-suite records terminal stops and zero translation faults.",
            ),
            Evidence(
                "research/results/COPPER_FULL_AUTHORITY_SVA_SUMMARY.md",
                ("terminal=139", "a_allow_requires_nonterminal_source"),
                "Full-authority SVA harness asserts allowed seeds cannot come from terminal witness-derived sources.",
            ),
            Evidence(
                "research/results/COPPER_CTLW_FULL_AUTHORITY_E2E_SUMMARY.md",
                ("terminal_block=274", "exact_cross_allow=3", "errors=0"),
                "CTLW-to-full-authority integration harness confirms terminal sources block even when an exact target witness is present.",
            ),
            Evidence(
                "research/results/COPPER_CLPD_CTLW_AUTHORITY_E2E_SUMMARY.md",
                ("terminal_block=54", "joint_cross_allow=180", "errors=0"),
                "CLPD-CTLW authority harness confirms terminal sources block even when source and target authorities are both live.",
            ),
        ),
        residual_risk="Needs workload sweep over different RCP depths and prefetch-queue sizes.",
    ),
    CoverageRow(
        unsafe_class="Permission or translation failure on candidate target",
        mechanism="Translation and permission gate",
        security_contract="DMP authority is still subordinate to translation and permission success.",
        evidence=(
            Evidence(
                "research/results/copper_full_authority_xsim.log",
                ("permission=183", "errors=0"),
                "Full-authority RTL simulation covers permission-failure blocking.",
            ),
            Evidence(
                "research/results/gem5_arm_ubuntu_fs_native_pasb_timing/FS_PASB_TIMING_SUMMARY.md",
                ("30 translation-faulted recursive attempts", "zero translation faults"),
                "Full-system PASB timing shows unsafe/pre-PASB faulting attempts reduced to zero under PASB-COPPER.",
            ),
            Evidence(
                "research/results/COPPER_FULL_AUTHORITY_SVA_SUMMARY.md",
                ("perm=372", "a_allow_requires_permission"),
                "Full-authority SVA harness asserts allowed seeds require target permission.",
            ),
            Evidence(
                "research/results/COPPER_CEPF_LINE_E2E_SVA_SUMMARY.md",
                ("fault_perm_block=1321", "translation_block=196", "permission_block=1"),
                "CEPF-to-line end-to-end SVA harness checks fault/permission failures before proof creation and at DMP use.",
            ),
            Evidence(
                "research/results/COPPER_CTLW_FULL_AUTHORITY_E2E_SUMMARY.md",
                ("permission_block=85", "exact_cross_allow=3", "errors=0"),
                "CTLW-to-full-authority integration harness confirms target permission still blocks exact-witness cross-page issue.",
            ),
            Evidence(
                "research/results/COPPER_CLPD_CTLW_AUTHORITY_E2E_SUMMARY.md",
                ("permission_block=12", "joint_cross_allow=180", "errors=0"),
                "CLPD-CTLW authority harness confirms permission failures block even with live compressed source proof and exact target witness.",
            ),
            Evidence(
                "research/results/COPPER_TLB_COHERENCE_CONTRACT.md",
                ("BUG_NO_PERMISSION_DOWNGRADE_HOLD", "BUG_NO_PERMISSION_GATE", "permission_not_allowed", "Full contract status: PASS"),
                "TLB/coherence contract checker shows same-cycle permission downgrade and missed permission gate are unsafe.",
            ),
            Evidence(
                "research/results/COPPER_TLB_COHERENCE_AUTHORITY_FILTER_RTL_SUMMARY.md",
                ("permission failure and same-cycle permission downgrade block", "target permission", "errors=0", "status=PASS"),
                "RTL filter checks target permission and same-cycle permission downgrade blocking.",
            ),
        ),
        residual_risk="Needs real OS/application stress with page faults, unmapped regions, and permission changes.",
    ),
]


def evidence_status(evidence: Evidence) -> tuple[bool, str]:
    path = ROOT / evidence.path
    if not path.exists():
        return False, f"missing file: `{evidence.path}`"
    text = path.read_text(encoding="utf-8", errors="replace").replace("\x00", "")
    missing = [needle for needle in evidence.must_contain if needle not in text]
    if missing:
        return False, "missing strings: " + "; ".join(f"`{item}`" for item in missing)
    return True, "ok"


def write_matrix() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# COPPER Security Coverage Matrix",
        "",
        "Date: 2026-06-17",
        "",
        "This matrix maps modeled unsafe data-memory-dependent prefetch behavior to",
        "the COPPER mechanism that blocks it and to local artifacts that contain",
        "the claimed evidence. The generator checks the evidence strings before",
        "marking a row covered.",
        "",
        "| Unsafe class | Mechanism | Contract | Evidence status | Residual risk |",
        "|---|---|---|---|---|",
    ]

    all_ok = True
    for row in ROWS:
        statuses = []
        row_ok = True
        for evidence in row.evidence:
            ok, status = evidence_status(evidence)
            row_ok = row_ok and ok
            statuses.append(
                f"{'PASS' if ok else 'FAIL'} `{evidence.path}`: {evidence.note} ({status})"
            )
        all_ok = all_ok and row_ok
        lines.append(
            "| {unsafe} | {mechanism} | {contract} | {status} | {risk} |".format(
                unsafe=row.unsafe_class,
                mechanism=row.mechanism,
                contract=row.security_contract,
                status="<br>".join(statuses),
                risk=row.residual_risk,
            )
        )

    lines.extend(
        [
            "",
            f"Overall coverage status: {'PASS' if all_ok else 'FAIL'}",
            "",
            "Interpretation: this is not a proof of complete security. It is a",
            "source-backed audit that the paper's named unsafe classes have local",
            "evidence and that the remaining risks are explicit.",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)
    print(f"coverage_status={'PASS' if all_ok else 'FAIL'}")
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    write_matrix()
