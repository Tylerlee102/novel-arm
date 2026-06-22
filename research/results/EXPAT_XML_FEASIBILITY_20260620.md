# Expat XML Full-System Feasibility Note

Date: 2026-06-20

Attempted workload: deterministic native AArch64 binary calling the public
libexpat XML parser through the Ubuntu ARM64 guest library stack.

Local outcome:

- Build status: PASS (`research/results/expat_xml_workload_build/EXPAT_XML_WORKLOAD_BUILD.md`).
- Full-system timing run `expat_smoke` with 512 records did not complete within the local 10-minute foreground timeout.
- Reduced full-system timing run `expat_tiny` with 32 records and 4 attributes also remained in the native ROI after a further polling window; `stats.txt` was still empty and `board.terminal` had not printed `EXPAT_COPPER_RESULT`.
- Follow-up engineering attempt: the workload was changed to use gem5 self-ROI markers and to move XML generation outside the timed region. A `none` policy run with 8 records and 2 attributes still did not finish within the local 15-minute foreground timeout.
- Further narrowed attempt: the timed region was moved inside the workload around the `XML_Parse` loop after `XML_ParserCreate` and handler setup. A single-record, single-attribute `none` policy run still did not finish within the local 10-minute foreground timeout after reaching `m5_work_begin`.
- The partial runs were stopped and are not counted as benchmark evidence.

Interpretation:

This is a local tractability failure under the current full-system timing path,
not evidence for or against COPPER. The Expat driver may still be useful later
with a faster CPU model, syscall-emulation mode, static parser linkage, or a
separate parser-kernel model, but it should not appear in paper result tables
until it completes with matching checksums across policies.

status=NOT_COUNTED
