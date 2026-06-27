# COPPER DOCX QA

Date: 2026-06-12, updated 2026-06-15

## Fixed Errors

- The first DOCX export path failed because the document renderer could not find LibreOffice.
- The first hidden Word export hung because it was not run through a clean STA automation path.
- The first compact DOCX draft was only 3 pages, not the requested 8-page paper target.
- A references formatting issue caused Word auto-numbering to continue from an earlier numbered list.
- A temporary PDF rendering attempt using incomplete bundled Node native packages was removed.
- The rebuilt paper added AArch64 Minor/O3 sensitivity, randomized RTL-invariant evidence, CEPF backend proof filtering, graph-style provenance traces, an ARM64 full-system Linux boot/readfile probe, and a native AArch64 full-system workload ROI.
- Earlier Word automation checks could open/count the rebuilt DOCX, but the current Codex logon session cannot create a Word COM instance. The export pipeline therefore avoids Word's writer and uses the direct ReportLab PDF renderer plus structural DOCX/PDF checks.
- The latest rebuild adds PASB plus CTLW full-system timing evidence: naive pointer-shaped DMP has 30 translation-faulted recursive attempts in the tiny ROI; pre-PASB COPPER has 5; PASB-COPPER has 0 while blocking 102 pointer-shaped unproven candidates; larger CTLW-terminal ROIs have zero recursive translation faults with -0.531% and -0.271% ticks versus no prefetch.
- The current rebuild also adds a full-system AArch64 graph-gather control: COPPER-CTLW gives -0.367% ticks versus no prefetch, blocks 8,660 unproven candidates, and records zero translation faults; stride still wins that generated binary because the edge array is sequential.
- The latest rebuild adds LLVM/clang plus LLD validation, a freestanding C AArch64 graph/hash/tree/fake-pointer suite under full-system Linux, and a bounded PASB/CTLW/terminal invariant checker. The compiled C suite is intentionally reported as a safety/control result, not a speedup result: COPPER blocks 679 unproven candidates with zero translation faults but is 0.093% slower than no prefetch on that smaller suite.
- The latest rebuild adds a GAPBS-inspired freestanding AArch64 graph-kernel mini-suite with BFS, SSSP-like relaxation, PageRank-style gather, connected-components-style propagation, and fake pointer-shaped data. COPPER blocks 952 unproven candidates, removes 408 CTLW misses and 408 unavailable recursive translations seen by naive DMP+CTLW, records zero translation faults, and matches no-prefetch ROI ticks; stride still wins because edge arrays are sequential.
- An official GAPBS AArch64 feasibility probe was added. Direct clang++ compilation of `external/gapbs/src/bfs.cc` for `aarch64-linux-gnu` fails at `<iostream>`, confirming that official GAPBS full-system execution needs an AArch64 Linux C++ sysroot/toolchain rather than the freestanding C path used by the mini-suite.
- A richer bounded authority checker was added. `COPPER_FULL_AUTHORITY` passes 11,419 reachable states to depth 12, while weakened CEPF/source-invalidation/PASB/CTLW/witness/terminal variants fail with short counterexamples.
- A full-authority CEPF/PASB/CTLW SystemVerilog gate and randomized testbench were added. Vivado XSIM passes 12 directed cases plus 5,000 randomized scoreboard trials with `allowed=956 blocked=3731 stale=624 token=123 target=240 terminal=58 perm=183 errors=0`. The current testbench also requires nonzero named coverage for no-source, unsound, stale-value, stale-epoch, PASB-token, same-page allow, cross-page allow, missing-witness, wrong-line-witness, stale-witness, terminal, and permission classes. Fresh synthesis for this new gate was attempted but blocked before `synth_design` by the Vivado Tcl app initialization failure.
- A full-authority SVA harness was added. Vivado XSIM passes 12 directed cases plus 10,000 randomized assertion samples with `allowed=1919 blocked=7455 no_source=4994 unsound=1260 stale_value=794 stale_epoch=584 token=233 terminal=139 missing_witness=131 wrong_witness=79 stale_witness=54 perm=372 same_allow=769 cross_allow=1150`.
- A CEPF-line end-to-end SVA harness was added. Vivado XSIM passes 12 directed cases plus 10,000 randomized samples with `valid_commit=2257 proof_to_allow=769 unproven_block=7658 stale_epoch_block=151 no_source_block=1247 fault_perm_block=1321 not_commit_block=1285 write_clear=1 fill_clear=1 invalidate_clear=1 domain_block=99 translation_block=196 permission_block=1 random_allow=769 random_block=7954 errors=0`.
- A CTLW witness directory RTL block was added. Vivado XSIM passes 10 directed cases plus 10,000 randomized samples with `exact_hit=1484 miss=6712 token_mismatch=124 line_mismatch=5162 remap_clear=1 tlbi_token_clear=112 tlbi_all_clear=49 collision=3354 stale_after_remap_block=1 stale_after_tlbi_block=1 errors=0`.
- A CTLW-to-full-authority E2E harness was added. Vivado XSIM passes 12 directed cases plus 10,000 randomized samples with `exact_cross_allow=3 no_witness_block=7102 token_mismatch_block=28 line_mismatch_block=6200 stale_after_remap_block=1 stale_after_tlbi_block=1 terminal_block=274 permission_block=85 stale_source_block=260 same_page_allow=379 random_allow=382 random_block=7721 collision=2659 errors=0`.
- A CLPD-CTLW authority E2E harness was added. Vivado XSIM passes 18 directed cases plus 10,000 randomized samples with `joint_cross_allow=180 same_page_allow=65 no_source_block=8468 word_unproven_block=181 stale_epoch_block=374 source_token_block=100 target_no_witness_block=1239 target_line_alias_block=1183 remap_block=1 tlbi_block=1 write_clear_block=1 fill_clear_block=1 invalidate_clear_block=1 terminal_block=54 permission_block=12 clpd_collision=14 ctlw_collision=1376 random_allow=245 random_block=9773 errors=0`.
- A SARI revoker RTL block was added. Vivado XSIM passes 8 directed cases plus 10,000 randomized cycles with `dma=1 chi=1 io=1 triple_burst=1 hold=6321 remap=1 tlbi_token=1 tlbi_all=1 ready_low=4 overflow=4 final_queue=0 errors=0`.
- A wired SARI-to-CLPD/CTLW/full-authority harness was added. Vivado XSIM passes 12 directed cases plus 10,000 randomized samples with `hold_block=1828 dma_hold=1 chi_hold=1 io_hold=1 remap_hold=1 tlbi_token_hold=1 tlbi_all_hold=1 random_hold=1814 errors=0`.
- A conflict-scoped SARI refinement was added. Vivado XSIM passes 12 directed cases plus 10,000 randomized samples with `conflict_hold=1245 avoided_global_hold=1007 avoided_global_allow=1007 random_hold=1240 errors=0`; the five-graph GAPBS-topology revocation proxy reports `Aggregate hold reduction: 82.06%`, `Avoided global holds with authority present: 269879`, `CS-SARI unsafe modeled issues: 0`, and `No-hold unsafe modeled issues: 59013`.
- A CS-SARI/CLPD/CTLW composition checker was added and freshly rerun. Full composed authority passes 7,555 reachable states with `status=PASS`; weakened variants that omit incoming-source, queued-source, remap, token-TLBI, global-TLBI, overflow, source-proof, or target-witness authority fail as expected.
- A CS-SARI queue-depth/conflict sensitivity sweep was added and freshly rerun. Across 20 configurations, CS-SARI has 0 modeled unsafe issues, the no-hold control has 1,649,883 modeled unsafe issues, median hold reduction is 72.06%, and hold reduction ranges from 0.06% to 97.41%.
- A GAPBS-backed COPPER topology trace was added. It parses five public GAPBS serialized Kronecker graph files, replays edge-scan and BFS-replay streams, and adds CLPD as a compressed source-line proof representation. COPPER-epoch averages 1.770x and CLPD averages 1.896x with zero data-at-rest, unproven-edge, or stale-slot prefetches; on the g12 edge scan, CLPD recovers 2.115x with 8,192 line entries where the edge-exact ledger needs 131,072 entries for 2.369x.
- A CLPD SystemVerilog directory gate and randomized testbench were added. Vivado XSIM passes 14 directed cases plus 5,000 randomized scoreboard trials with `allowed=4 blocked=5012 no_entry=4864 word_unproven=12 stale_epoch=132 token=2 fault_perm=2 write_clear=1 fill_clear=1 invalidate_clear=1 collision=1 errors=0`. Fresh synthesis for CLPD was attempted but blocked before `synth_design` by the same Vivado Tcl app initialization failure as the full-authority gate.
- A CLPD bounded state-space checker was added. Full CLPD passes 24,354 reachable states to depth 8; weakened no-tag, no-token, no-epoch, whole-line-proof, no-write-clear, no-fill-clear, and no-invalidate-clear variants fail with short counterexamples.
- A CLPD storage model was added. Under explicit assumptions, CLPD full coverage is about 30.86-32.00x smaller than edge-exact retained proof across the GAPBS-backed graphs. On g12, the full-cover proxy is 1252.18 KiB edge-exact versus 39.87 KiB CLPD; at the measured points, CLPD uses 54.00 KiB for 2.115x while edge-exact uses 1696.00 KiB for 2.369x.
- A source-backed security coverage matrix was added. `research/copper_security_coverage_matrix.py` maps ten modeled unsafe classes to COPPER mechanisms and local evidence, verifies the cited evidence strings, and regenerates `research/results/COPPER_SECURITY_COVERAGE_MATRIX.md` with `coverage_status=PASS`.
- In the current Codex logon session, Word COM creation fails with `0x80070520`, and the official DOCX renderer cannot find a LibreOffice/soffice backend. The fallback QA path uses the regenerated ReportLab PDF plus structural DOCX/PDF checks.

## Current Deliverables

| Artifact | Status |
|---|---|
| `research/COPPER_CONFERENCE_DRAFT.docx` | Older compact Word draft; DOCX ZIP/package integrity passes, but the current source of truth is the markdown/PDF path |
| `research/results/COPPER_CONFERENCE_DRAFT_REVIEW.pdf` | Regenerated from the direct ReportLab PDF renderer; current primary 8-page paper artifact |
| `research/results/copper_full_docx_render_word/COPPER_CONFERENCE_DRAFT.pdf` | Synced mirror of the verified 8-page review PDF for the older deliverable path |
| `research/results/copper_review_pdf_render_latest/pages/page_01.png` through `page_08.png` | Fresh PyMuPDF render from the current 8-page review PDF |
| `research/results/copper_review_pdf_render_latest/contact_sheet.png` | Fresh contact sheet; visual inspection found no blank pages, clipping, or obvious overflow |

## QA Results

| Check | Result |
|---|---|
| Word page count | Not available in current logon session: Word COM creation fails with `0x80070520` |
| Word word count | Not available in current logon session |
| Fixed PDF pipeline | PASS: expected PDF artifact generated without Word save/export |
| Native Word PDF export | DISABLED: Word COM save/export hangs globally, confirmed by an all-temp smoke test |
| Generated PDF build | PASS, 8 pages |
| Generated PDF text extraction | PASS: all 8 pages contain extracted text; 88,630 extracted characters in the current PDF |
| Generated PDF key strings | PASS: `GAPBS-backed`, `CLPD`, `8,192`, `131,072`, `2.115x`, `1.896x`, `14 directed`, `5,000 randomized`, `10,000 randomized`, `CEPF-to-line`, `proof_to_allow`, `CTLW witness`, `exact_hit`, `CTLW-to-full-authority`, `exact_cross_allow`, `CLPD-CTLW`, `joint_cross_allow`, `SARI`, `CS-SARI`, `conflict-scoped`, `avoided_global_hold`, `269,879`, `82.06%`, `composition checker`, `7,555`, `20-configuration`, `1,649,883`, `72.06%`, `SoC Authority Revocation`, `dma=1`, `chi=1`, `io=1`, `hold=6321`, `ready_low=4`, `overflow=4`, `no_source_block`, `word_unproven_block`, `target_no_witness_block`, `write_clear_block`, `tlbi_block`, `clpd_collision`, `ctlw_collision`, `no_witness_block`, `line_mismatch_block`, `stale_after_remap_block`, `stale_after_tlbi_block`, `permission_block`, `DMP issue gate`, `TLBI`, `5012`, `collision`, `24,354`, `54.00 KiB`, `1696.00 KiB`, `11,419`, `full-authority`, `SVA`, `coverage matrix`, `ten modeled`, `evidence string`, `terminal-fill`, and CLPD/security coverage result text are present |
| Generated PDF page render | PASS: current 8-page PDF rendered to PNG with the local PyMuPDF renderer |
| Contact-sheet inspection | PASS: fresh contact sheet has no blank pages, clipping, or obvious overflow; the paper is intentionally dense |
| References numbering | PASS: starts at 1 |
| DOCX ZIP/package integrity | PASS |
| Table geometry | PASS structurally: 6 Word tables; direct PDF text extraction confirms CTLW/PASB, graph-gather, compiled C, GAPBS-inspired mini-suite, richer bounded-checker, full-authority RTL/SVA, CTLW-to-full-authority E2E, CLPD-CTLW E2E, SARI, GAPBS-backed trace, CLPD trace, CLPD RTL, CLPD bounded-checker, CLPD storage, and security coverage result text is present |

## Notes

LibreOffice is still not installed, so the official DOCX render helper cannot
be used on this machine. In this logon session, Microsoft Word COM creation
also fails before page/word counting with `0x80070520`. Native Word COM
save/export was already disabled because it previously hung even on a tiny
all-temp smoke test. The fallback pipeline therefore uses the ReportLab renderer
to generate the primary 8-page PDF paper artifact, checks the generated PDF with
`pypdf` text extraction, mirrors the verified PDF to the older deliverable path,
and renders the current PDF to PNG/contact-sheet images for visual QA.
