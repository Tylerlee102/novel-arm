# COPPER Research Code Audit Report

Date: 2026-06-25

## Executive Summary

I audited the COPPER research-paper codebase with separate math, graph, code/reproducibility, and reviewer passes, then fixed the issues that were safe to correct locally. The local derived-artifact path now passes: `reproduce_results.py --mode quick` reports `Overall status: PASS`, the artifact verifier reports `Passed 177/177 artifact checks`, and the public package hash audit checks 575 direct-package files plus 2 external-by-hash SAIF files.

Strict fresh-clone/end-to-end reproducibility is still a fail: full raw gem5/Vivado reruns depend on local toolchains, large external artifacts, and environment setup that quick mode records but does not rebuild. The current state is much better for reviewer-facing local reproduction, but not yet a clean public artifact release.

## Final Status

| Area | Status | Basis |
|---|---:|---|
| Local derived-artifact reproduction | PASS | `research/results/reproduction/LOCAL_REPRODUCTION_REPORT.md`, overall PASS |
| Artifact evidence-string audit | PASS | `research/results/COPPER_ARTIFACT_AUDIT_20260616.md`, 177/177 checks |
| Public package manifest/build | PASS | 577 manifest entries, 575 direct files, 579 package files, 0 missing, 0 hash mismatches |
| Formula/math consistency for checked paper-facing derived results | PASS | Metadata-toggle bound, pressure score, DRAM ROI alignment, and claim strings refreshed |
| Graph correctness for checked app figures | PASS | Negative bus deltas now visible; twelve-point labels are consistent |
| Fresh-clone full reproduction | FAIL | External gem5/Vivado/toolchain/raw-run setup is not self-contained |

## Files And Scripts Inspected

Core paper/result files: `research/COPPER_FULL_PAPER.md`, `research/COPPER_FINAL_OUTPUT.md`, `research/COPPER_ARTIFACT_REPRODUCTION_GUIDE.md`, `research/results/COPPER_CLAIM_EVIDENCE_MATRIX_20260617.md`, `research/results/COPPER_TOP_TIER_GAP_TRACKER_20260619.md`, and generated evidence under `research/results`.

Main scripts audited or changed: `research/plot_copper_app_overhead_figures.py`, `research/analyze_copper_metadata_toggle_bound.py`, `research/analyze_copper_dram_energy_scorecard.py`, `research/build_copper_claim_evidence_matrix.py`, `research/verify_copper_artifacts.py`, `research/build_copper_public_artifact_manifest.py`, `research/build_copper_public_artifact_package.py`, `research/summarize_openssl_tls_tcp_fs.py`, the BIO/socket OpenSSL summarizers, `research/audit_sanity_checks.py`, and `reproduce_results.py`.

## Commands Run

- Python compile checks for the audited scripts.
- Regenerated metadata-toggle bound, app figures, claim matrix, artifact audit, public manifest, and public package build.
- Regenerated OpenSSL TCP/BIO/socket summary CSV/Markdown files where ROI-section provenance or wording changed.
- Ran `research/verify_copper_artifacts.py`.
- Ran `research/audit_sanity_checks.py`.
- Ran `reproduce_results.py --mode quick`.
- Ran stale-value sweeps for old metadata numbers, old ten/twelve figure text, stale package counts, and old process-server wording.

## Bugs And Fixes

| Severity | Area | Issue | Fix |
|---|---|---|---|
| High | Reproducibility | Fresh-clone reproduction is not self-contained; raw gem5/Vivado reruns still rely on local paths and external tools. | Added `reproduce_results.py` and `requirements.txt` for local derived checks; documented remaining full-rerun gap. |
| High | Public artifact | Manifest/package omitted explicit gem5 COPPER source evidence and package rebuild was fragile on Windows read-only files. | Added `external/gem5/.../copper.cc` and `.hh`; hardened package reset cleanup; rebuilt package. |
| Medium | Math/results | Metadata-toggle bound used stale 20-row values and mixed CLPD reads with CTLW target-witness lookups under a misleading label. | Recomputed 22-row bound and split CLPD source-proof reads from CTLW target-witness lookups. |
| Medium | Graphs | Bus-overhead plot clipped negative values by forcing the x-axis to start at zero. | Recentered x-axis around observed min/max and added a zero reference line. |
| Medium | Graphs/docs | App figure text said ten points while current figures use twelve public app points. | Updated plot subtitles and figure index wording. |
| Medium | OpenSSL summaries | ROI stats section selection was implicit. | Added explicit ROI-section selection, section count guard, and `stats_section_index` / `stats_sections_total` output fields. |
| Medium | Paper alignment | `COPPER_FINAL_OUTPUT.md` still described the TCP process-server evidence as the older two-seed/10-pair result. | Updated to the current four-point, four-checksum, 70-pair portfolio and regenerated summaries. |
| Medium | Packaging docs | Reproduction guide, gap tracker, full paper, and final output had stale public-package counts. | Updated to 577 manifest entries, 575 direct files, 6,194,294 direct bytes, and 579 package files. |
| Low | Verification | Artifact verifier is still mostly string-presence based. | Added focused sanity checks for counts, formulas, figure inputs, DRAM ROI alignment, and manifest/package hashes. |
| Low | Figures | Runtime figures still do not display confidence intervals even where repeated-seed evidence exists. | Left as a remaining improvement; current figures are deterministic summaries, not uncertainty plots. |

## Formula And Math Audit

The metadata-toggle calculation is now aligned with the current 22-row app/service/parser/compression/TCP side-effect mix: 40,058 learned-proof writes, 1,407,655 CLPD source-proof reads, 20,046 CTLW target-witness lookups charged as metadata reads, 1,427,701 total charged metadata reads, and 37.495 uJ in the high scenario. The report now says this is 0.1801% of matching COPPER DRAM operation energy and 0.002190% of total DRAM energy.

The added sanity checks verify the pressure-score formula, weight-scenario sums, 12-point/22-point claim counts, and DRAM `sim_ticks` versus summary `roi_ticks` for representative SQLite and OpenSSL TCP rows. I did not claim proof of every formula in the paper; the pass applies to the checked paper-facing derived results.

## Graph Audit

The bus-overhead chart now shows both negative and positive memory-bus byte deltas instead of clipping negative bars. The app figure index and subtitles now consistently describe twelve public app points. The remaining graph weakness is presentation rather than arithmetic: uncertainty intervals are not visualized in the main runtime figures despite repeated-seed evidence elsewhere.

## Reproducibility Audit

Local quick reproduction passes and records the environment, Python dependencies, external-tool availability, step logs, and manifest hash audit. The public package now builds with 579 files and zero hash mismatches.

Strict public reproducibility still fails because a fresh clone cannot rebuild every raw full-system result without local gem5, Vivado, simulator configuration, large artifacts, and exact workload/toolchain setup. The local `.git` status command also fails because this workspace is not a normal Git repository, so provenance should be captured through release hashes/manifests rather than Git state alone.

## Claim Evidence Alignment

| Claim surface | Alignment after fixes |
|---|---|
| 12-point app matrix | PASS: figure labels, plot data, and figure index now agree on twelve points. |
| 22-row side-effect/energy scorecards | PASS: metadata-toggle bound and claim matrix use current 22-row values. |
| OpenSSL TCP process-server evidence | PASS: final output now cites the four-point portfolio with 4 checksums, 70 pairs, 98.2% min COPPER CTLW reduction, 98.1% min slack reduction, and 0 faults. |
| Public artifact packaging | PASS: manifest, reproduction guide, gap tracker, full paper, final output, and package build now agree on 577 entries, 575 direct files, and 579 package files. |
| Full raw gem5/Vivado evidence | FAIL for fresh reproduction: evidence exists locally, but rerun automation is not public-clean or toolchain-complete. |

## Verification Results

- `reproduce_results.py --mode quick`: PASS.
- `research/verify_copper_artifacts.py`: PASS, 177/177 checks.
- `research/audit_sanity_checks.py`: PASS.
- Public package build: PASS, 0 missing files and 0 hash mismatches.
- Manifest hash audit: PASS, 575 checked direct files and 2 external-by-hash files.

## Remaining Concerns

Fresh-clone reproduction needs the most work: remove hard-coded local assumptions, publish a machine-readable environment manifest, and provide scripts that either fetch or clearly stub large raw artifacts. Full raw simulation/tool reruns were not performed in this audit.

The verification suite still mixes strong checks with brittle string checks. It now catches more drift, but it should eventually compare structured CSV/JSON values to paper claims instead of searching prose.

The paper should keep the power/energy claim narrow. McPAT and Vivado evidence are proxy evidence, and metadata-toggle bounds are pJ/access sensitivity checks, not ASIC signoff.

## Top Five Next Fixes

1. Build a clean public reproduction bundle that works from a fresh clone with one documented Python environment and explicit external-artifact downloads.
2. Convert paper-claim checks from prose string matching into structured claim tables with numeric tolerances.
3. Add uncertainty/error bars or companion repeated-seed panels for the main runtime graphs.
4. Add explicit random seeds and seed logs to randomized RTL/testbench flows.
5. Containerize or script the gem5/Vivado prerequisites enough that reviewers can distinguish "not installed" from "result failed."

