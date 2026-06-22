# MiBench Patricia Full-Large Feasibility Note

Date: 2026-06-20

This note records a public MiBench `large.udp` scale attempt. It is
negative feasibility evidence for the full five-policy campaign, not a
completed benchmark comparison.

What passed:

- The compressed host-to-guest staging path completed and produced
  `/tmp/mibench_patricia_input.udp` with 1,514,237 bytes.
- The no-prefetch baseline completed under ARM64 full-system Linux.
- Public input records consumed: 62,721 of limit 62,721.
- Lookup operations: 125,442.
- Checksum: `0xfbd3bc01d9160d87`.
- Return code: 0.
- Final ROI simTicks: 417,102,890,922.

What did not complete locally:

- The naive recursive DMP policy entered the timed ROI but did not reach
  the result or stats-dump markers before the local run was stopped at
  2026-06-20 21:16:09 -07:00.
- No panic, fatal, guest checksum mismatch, or translation-fault crash
  was observed before stopping.

Interpretation:

- The public full-large input is valid and the baseline path is working.
- Full-large naive DMP appears too slow for the current local interactive
  campaign budget.
- The next complete comparison should use a larger-than-8,192 but
  tractable prefix of the public `large.udp` input, preserving the same
  five-policy comparison.

status=PARTIAL_NEGATIVE_FEASIBILITY

