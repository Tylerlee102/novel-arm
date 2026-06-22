# MiBench Patricia 32K Feasibility Note

Date: 2026-06-20

This note records a public MiBench `large.udp` prefix scale attempt. It is
negative feasibility evidence for the 32,768-record five-policy campaign,
not a completed benchmark comparison.

What passed:

- The compressed host-to-guest staging path completed and produced
  `/tmp/mibench_patricia_input.udp` with 1,514,237 bytes.
- The no-prefetch baseline completed under ARM64 full-system Linux.
- Public input records consumed: 32,768 of limit 32,768.
- Lookup operations: 65,536.
- Checksum: `0x3d8faaf97d9a4eb2`.
- Return code: 0.
- Final ROI simTicks: 222,447,259,404.

What did not complete locally:

- The naive recursive DMP policy entered the timed ROI but did not reach
  the result or stats-dump markers before the local run was stopped at
  2026-06-20 21:47:52 -07:00.
- No panic, fatal, guest checksum mismatch, or translation-fault crash
  was observed before stopping.

Interpretation:

- The public 32K prefix input is valid and the baseline path is working.
- Naive recursive DMP appears too slow for the current local interactive
  campaign budget at this scale.
- The next complete comparison should use a 16,384-record prefix of the
  same public `large.udp` input, preserving the five-policy comparison.

status=PARTIAL_NEGATIVE_FEASIBILITY

