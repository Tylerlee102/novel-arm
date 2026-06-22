# MiBench Patricia 16K Feasibility Note

Date: 2026-06-20

This note records the first 16,384-record public MiBench `large.udp`
prefix attempt. It is partial evidence, not the final 16K summary.

What passed:

- The compressed host-to-guest staging path completed and produced
  `/tmp/mibench_patricia_input.udp` with 1,514,237 bytes.
- The no-prefetch baseline completed under ARM64 full-system Linux.
- Public input records consumed: 16,384 of limit 16,384.
- Lookup operations: 32,768.
- Checksum: `0xaaa6fab2f1a60b59`.
- Return code: 0.
- Final ROI simTicks: 106,061,839,659.

What did not complete locally:

- The naive recursive DMP policy entered the timed ROI but did not reach
  the result or stats-dump markers before the local run was stopped at
  2026-06-20 22:11:36 -07:00.
- A follow-up non-naive campaign started COPPER CLPD-64K+PEB against the
  same completed baseline. COPPER entered the timed ROI but did not reach
  the result or stats-dump markers; the local background process was no
  longer running by 2026-06-20 22:27:24 -07:00 and did not emit the normal
  policy `DONE` marker.
- No panic, fatal, guest checksum mismatch, or translation-fault crash
  was observed before stopping.

Interpretation:

- The public 16K prefix input is valid and the baseline path is working.
- Naive recursive DMP remains the first local runtime bottleneck at this
  scale; the proposed COPPER path also exceeds the current interactive
  full-system budget before completing at 16K.
- The completed public-input scale frontier for five-policy comparison
  remains the 8,192-record point. The 16K, 32K, and 62,721-record attempts
  should be reported as scale-feasibility evidence, not as completed
  comparison data.

status=PARTIAL_NEGATIVE_FEASIBILITY
