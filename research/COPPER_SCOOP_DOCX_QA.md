# COPPER/SCOOP Focused Conference Draft QA

Date: 2026-06-16

Artifact:

- `research/COPPER_SCOOP_CONFERENCE_DRAFT.docx`
- Builder: `research/build_copper_scoop_conference_docx.py`

Result:

- Word opened the DOCX with `OpenNoRepairDialog`.
- Word repagination completed.
- Page count: 8.
- Word count: 3,351.
- python-docx structural read completed.
- Paragraphs: 73.
- Tables: 10.
- Sections: 1.
- Empty tables: 0.
- Table dimensions: 1x1, 8x2, 1x1, 5x3, 6x4, 6x3, 7x6, 7x2, 6x3, 7x2.

Render status:

- The packaged LibreOffice renderer failed because `soffice` was not found.
- Word COM could open and count the document, but both `ExportAsFixedFormat`
  and `SaveAs2(..., PDF)` hung in this shell, so PDF/PNG visual QA could not
  be completed locally.
- No background Word process remained after cleanup.

Evidence integrated:

- SCOOP slack-only hybrid mechanism and strict-primary invariant.
- Direct traffic-only DMP oracle.
- Cold-cache observer oracle.
- Three-seed observer reproducibility sweep.
- Split scan/probe audit showing COPPER/SCOOP scan-phase allowed delta 0.
- Public SQLite, Lua, Duktape, Olden, GAPBS, heap, and fake-only workload data.
- Vivado XSim SCOOP arbiter result and bounded SCOOP checker result.

Status:

- Structural QA: PASS.
- Page-count target: PASS.
- Visual render QA: BLOCKED by local renderer/export tooling.
