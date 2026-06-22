# COPPER Vivado Summary

Vivado version: AMD Vivado 2025.2  
Target FPGA: `xc7a35tcpg236-1`  
Timing constraint: 10 ns clock  
Latest simulation run: 2026-06-16 local machine time  
Latest synthesis/place-route reports: 2026-06-16 local machine time

The 2026-06-16 Vivado 2025.2 backend-path rerun added an LSQ-style source-tag
tracker and an LSQ -> CEPF -> line-gate integration harness. Both passed XSim,
and both synthesized cleanly at a 10 ns clock. The earlier 2026-06-15 rerun
passed the authority-chain XSIM regression
on 10 RTL/SVA harnesses, reran the PEB-specific XSIM test, refreshed CLPD SRAM
synthesis, and completed a 64K-entry CLPD out-of-context place-and-route on
`xc7a200tfbg676-2`. The route completed with 0 route errors, 0 unrouted nets,
0 partial nets, 0 critical warnings, 0 errors, and +0.362 ns setup slack at the
10 ns timing target. The run uses an explicit Vivado path plus a clean TclStore
environment (`XILINX_TCLAPP_REPO` and isolated `APPDATA`) to avoid the earlier
local Tcl app-registry failure documented in
`research/results/COPPER_VIVADO_2025_2_TCLSTORE_TRIAGE.md`.

## RTL Simulation

Main regression command:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_direct_xsim.ps1
```

Full-authority gate command:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_full_authority_xsim.ps1
```

Full-authority SVA harness command:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_full_authority_sva_xsim.ps1
```

CEPF-to-line end-to-end SVA command:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_cepf_line_e2e_xsim.ps1
```

LSQ source-tag tracker command:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_lsq_source_tag_tracker_xsim.ps1
```

LSQ-to-CEPF-to-line end-to-end command:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_lsq_cepf_line_e2e_xsim.ps1
```

Full LSQ-to-AMBA authority command:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_full_lsq_amba_authority_xsim.ps1
```

CTLW witness directory command:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_ctlw_witness_xsim.ps1
```

CTLW-to-full-authority E2E command:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_ctlw_full_authority_e2e_xsim.ps1
```

CLPD-CTLW authority E2E command:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_clpd_ctlw_authority_e2e_xsim.ps1
```

SARI revoker command:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_sari_revoker_xsim.ps1
```

SARI/CS-SARI authority regression command:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_authority_regression_xsim.ps1
```

CLPD gate command:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_clpd_xsim.ps1
```

Passing test messages:

```text
COPPER gate directed tests completed
COPPER stream gate directed tests completed
COPPER stream table gate directed tests completed
COPPER line provenance directed tests completed
COPPER line provenance random invariant tests completed: trials=2000 allowed=339 blocked=1152 errors=0
COPPER commit-epoch proof bridge directed tests completed
COPPER full authority gate tests completed: directed=12 random=5000 allowed=956 blocked=3731 stale=624 token=123 target=240 terminal=58 perm=183 errors=0
COPPER full authority named coverage: no_source=2503 unsound=637 stale_value=389 stale_epoch=296 pasb_token=123 same_page_allow=386 cross_page_allow=570 missing_witness=72 wrong_line_witness=42 stale_witness=28 terminal=58 permission=183
COPPER full authority SVA completed: directed=12 random=10000 allowed=1919 blocked=7455 no_source=4994 unsound=1260 stale_value=794 stale_epoch=584 token=233 terminal=139 missing_witness=131 wrong_witness=79 stale_witness=54 perm=372 same_allow=769 cross_allow=1150
COPPER CEPF-line E2E SVA completed: directed=12 random=10000 valid_commit=2257 proof_to_allow=769 unproven_block=7658 stale_epoch_block=151 no_source_block=1247 fault_perm_block=1321 not_commit_block=1285 write_clear=1 fill_clear=1 invalidate_clear=1 domain_block=99 translation_block=196 permission_block=1 random_allow=769 random_block=7954 errors=0
COPPER LSQ source-tag tracker completed: directed=21 random=10000 clean_proof=1786 capture_no_proof=1326 no_tag=1082 stale=196 same_cycle_kill=87 epoch_mismatch=391 value_mismatch=413 fault_perm=1361 not_commit=1345 flush=12 clear=69 random_proof=1784 random_block=4470 errors=0
COPPER LSQ-CEPF-line E2E completed: directed=33 random=10000 bridge_proof=1730 materialized_allow=3572 same_cycle_dmp_block=558 no_tag=1076 stale=277 same_cycle_kill=83 epoch_mismatch=389 value_mismatch=425 fault_perm=1370 not_commit=1315 flush=12 clear=69 write_clear=1 fill_clear=1 invalidate_clear=1 domain_block=670 translation_block=275 permission_block=233 random_allow=3570 random_block=3324 errors=0
COPPER full LSQ-AMBA authority completed: directed=18 random=10000 baseline_allow=1 lsq_proof=2008 bridge_proof=2008 no_tag=1 stale_tag=1 epoch_value_mismatch=1 dma_hold=1 dma_post_block=1 chi_hold=1 chi_post_block=1 io_hold=1 io_post_block=1 remap_hold=1 remap_post_block=1 dvm_token_hold=1 dvm_token_post_block=1 dvm_all_hold=1 dvm_all_post_block=1 same_page_allow=1 terminal_block=1 perm_block=1 random_hold=4001 random_allow=1282 random_block=4733 errors=0
COPPER CTLW witness directory tests completed: directed=10 random=10000 exact_hit=1484 miss=6712 token_mismatch=124 line_mismatch=5162 remap_clear=1 tlbi_token_clear=112 tlbi_all_clear=49 collision=3354 stale_after_remap_block=1 stale_after_tlbi_block=1 errors=0
COPPER CTLW full-authority E2E tests completed: directed=12 random=10000 exact_cross_allow=3 no_witness_block=7102 token_mismatch_block=28 line_mismatch_block=6200 stale_after_remap_block=1 stale_after_tlbi_block=1 terminal_block=274 permission_block=85 stale_source_block=260 same_page_allow=379 random_allow=382 random_block=7721 collision=2659 errors=0
COPPER CLPD-CTLW authority E2E tests completed: directed=18 random=10000 joint_cross_allow=180 same_page_allow=65 no_source_block=8468 word_unproven_block=181 stale_epoch_block=374 source_token_block=100 target_no_witness_block=1239 target_line_alias_block=1183 remap_block=1 tlbi_block=1 write_clear_block=1 fill_clear_block=1 invalidate_clear_block=1 terminal_block=54 permission_block=12 clpd_collision=14 ctlw_collision=1376 random_allow=245 random_block=9773 errors=0
COPPER SARI revoker tests completed: directed=8 random=10000 dma=1 chi=1 io=1 triple_burst=1 hold=6321 remap=1 tlbi_token=1 tlbi_all=1 ready_low=4 overflow=4 final_queue=0 errors=0
COPPER SARI-CLPD-CTLW authority E2E tests completed: directed=12 random=10000 initial_allow=1 hold_block=1828 dma_hold=1 dma_post_block=1 chi_hold=1 chi_post_block=1 io_hold=1 io_post_block=1 triple_hold=1 triple_post_block=1 unrelated_survive=1 remap_hold=1 remap_post_block=1 tlbi_token_hold=1 tlbi_token_post_block=1 tlbi_all_hold=1 tlbi_all_post_block=1 same_page_after_target_event_allow=1 random_hold=1814 random_allow=1566 random_block=6630 overflow_hold=1 errors=0
COPPER CS-SARI authority E2E tests completed: directed=12 random=10000 initial_allow=1 conflict_hold=1245 matching_source_hold=1 matching_source_post_block=1 queued_source_hold=1 unrelated_source_allow=1 queued_unrelated_source_allow=1 matching_remap_hold=1 matching_remap_post_block=1 unrelated_remap_allow=1 wrong_token_remap_allow=1 matching_tlbi_hold=1 matching_tlbi_post_block=1 unrelated_tlbi_allow=1 tlbi_all_hold=1 tlbi_all_post_block=1 avoided_global_hold=1007 avoided_global_allow=1007 random_hold=1240 random_avoided=1002 random_allow=7238 random_block=1532 overflow_hold=1 errors=0
COPPER CLPD gate tests completed: directed=14 random=5000 allowed=4 blocked=5012 no_entry=4864 word_unproven=12 stale_epoch=132 token=2 fault_perm=2 write_clear=1 fill_clear=1 invalidate_clear=1 collision=1 errors=0
```

The line-provenance testbench covers:

- unproven source word block,
- committed clean word allow,
- source-domain mismatch block,
- target-domain mismatch block,
- translation failure block,
- permission failure block,
- write-clears-word behavior,
- sibling word remains proven after unrelated word write,
- line fill clears all word proofs,
- coherence invalidation clears all word proofs.

The randomized line-provenance testbench keeps an independent metadata
scoreboard and checks the DMP allow/block outputs across mixed commit, write,
fill, invalidation, translation, permission, and domain events. The latest run
exercised 2,000 cycles, 339 allowed DMP seeds, and 1,152 blocked DMP seeds with
0 mismatches.

The commit-epoch proof bridge testbench covers the backend proof-creation path:
clean committed dependent memory operations create proof, while non-memory
commits, squashes, missing source tags, exceptions, translation failures,
permission failures, and stale source epochs block proof creation. The stale
epoch case models an in-flight dependent memory operation whose source word is
overwritten before commit.

The full-authority gate testbench covers the combined CEPF/PASB/CTLW/terminal
predicate. Directed tests cover same-page allow, no proof, unsound proof, stale
source epoch/value, PASB token mismatch, terminal-source stop, cross-page
without witness, page-level/wrong-line witness, stale witness token,
cross-page exact witness allow, and permission failure. A 5,000-trial
randomized scoreboard then exercises allowed and blocked candidates across
named no-source, unsound-proof, stale-value, stale-epoch, PASB-token,
same-page-allow, cross-page-allow, missing-witness, wrong-line-witness,
stale-witness, terminal, and permission classes with 0 mismatches.

The full-authority SVA harness checks the same gate with assertions rather than
only a scoreboard. It asserts that any allowed seed requires exact committed
source proof, PASB token match, non-terminal source status, target authority,
and permission success, and it asserts that block-reason outputs match the
named unsafe classes. The 2026-06-12 XSIM regression run passed 12 directed plus 10,000
randomized assertion samples.

The CEPF-to-line end-to-end SVA harness connects the commit-epoch proof bridge
to the line-resident DMP gate. It checks proof creation, proof storage, and DMP
gate consumption across clock cycles against an independent shadow proof model.
The 2026-06-12 XSIM regression run passed 12 directed plus 10,000 randomized samples with
2,257 valid commits, 769 proof-to-allow cases, and 0 errors.

The LSQ source-tag tracker harness models the backend side before CEPF. It
checks that a dependent memory operation cannot create proof unless its captured
source tag is live, unstale, cleanly committed, and still matches the current
source epoch and value fingerprint. The LSQ-to-CEPF-to-line harness then checks
that this proof can materialize into cache-line metadata only after commit and
that same-cycle DMP seeds cannot consume the proof early. The 2026-06-16 XSIM
runs passed 21 and 33 directed cases, respectively, plus 10,000 randomized
samples each.

The full LSQ-to-AMBA authority harness composes LSQ source-tag capture, CEPF,
AMBA/SARI frontdoor decoding, SARI-RQ, CLPD source proof, CTLW target witnesses,
and the final DMP issue-authority predicate. A one-cycle revocation slice
retimes SoC clears into CLPD/CTLW only while the DMP authority gate remains
closed. The 2026-06-16 XSIM run passed 18 directed plus 10,000 randomized
samples with `errors=0`.

The CTLW witness directory testbench covers the exact target-line witness object
used by recursive cross-page issue. Directed and randomized checks cover exact
hit, absent witness miss, token mismatch, direct-mapped line alias mismatch,
remap clear, token-scoped TLBI clear, global TLBI clear, and collision eviction.
The 2026-06-12 XSIM regression run passed 10 directed plus 10,000 randomized samples with
0 errors.

The CTLW-to-full-authority E2E harness wires the witness directory into the
combined authority gate. It checks that exact live target-line witnesses open
cross-page DMP issue and that absent, token-stale, line-aliased, remap/TLBI
cleared, collision-evicted, terminal-source, permission-failure, and stale-source
cases block at the final issue predicate. The 2026-06-12 XSIM regression run passed 12
directed plus 10,000 randomized samples with 0 errors.

The CLPD-CTLW authority E2E harness connects the compressed source-line proof
directory, exact target-line witness directory, and final authority gate. It
checks that cross-page issue requires both live source proof and live target
witness authority, and that source write/fill/invalidate plus target remap/TLBI
events revoke that joint authority. The 2026-06-12 XSIM regression run passed 18 directed
plus 10,000 randomized samples with 0 errors.

The SARI revoker harness checks the boundary between external SoC/coherence
events and local COPPER metadata clearing. It queues DMA, CHI-style, and
coherent I/O source-line revocations, passes target remap/TLBI to CTLW, and
asserts immediate DMP hold while revocations are incoming, queued, or overflowing.
The 2026-06-12 XSIM run passed 8 directed plus 10,000 randomized cycles with 0
errors.

The SARI-CLPD-CTLW authority harness wires that boundary into the final
authority predicate. It checks same-cycle DMA/CHI/I/O/remap/TLBI hold behavior
and post-drain source/target blocking. The 2026-06-12 XSIM run passed 12
directed plus 10,000 randomized samples with 0 errors.

The CS-SARI authority harness checks conflict-scoped revocation hold. Matching
source, queued-source, remap, TLBI, TLBI-all, and overflow hazards hold, while
unrelated source/remap/token events avoid global stalls. The 2026-06-12 XSIM
run passed 12 directed plus 10,000 randomized samples with 0 errors and
`avoided_global_hold=1007`.

The CLPD gate testbench covers the compressed line-provenance directory used by
the GAPBS-backed topology trace. Directed tests cover reset block, proof
creation, per-word proof masks, token mismatch, source/target token mismatch,
stale line epoch, translation failure, permission failure, source-line write
clearing, line-fill clearing, invalidation clearing, and direct-mapped
collision eviction. A 5,000-trial randomized scoreboard then checks directory
state and query outputs with 0 mismatches.

## Synthesis Results

| RTL block | Slice LUTs | Slice registers | BRAM | DSP | WNS at 10 ns | Worst data path |
|---|---:|---:|---:|---:|---:|---:|
| `copper_line_provenance_gate` | 2063 / 20800, 9.92% | 1024 / 41600, 2.46% | 0 | 0 | +8.122 ns | 1.727 ns |
| `copper_commit_epoch_proof_bridge` | 5 / 20800, 0.02% | 0 / 41600, 0.00% | 0 | 0 | +3.682 ns | 6.318 ns |
| `copper_stream_table_gate` | 2528 / 20800, 12.15% | 2209 / 41600, 5.31% | 0 | 0 | +0.232 ns | 9.386 ns |
| `copper_lsq_source_tag_tracker` | 217 / 20800, 1.04% | 312 / 41600, 0.75% | 0 | 0 | +5.937 ns | 3.912 ns |
| `copper_lsq_cepf_line_e2e_top` | 1960 / 20800, 9.42% | 1336 / 41600, 3.21% | 0 | 0 | +2.176 ns | 7.442 ns |
| `copper_full_lsq_amba_authority_top` | 4692 / 20800, 22.56% | 3547 / 41600, 8.53% | 0 | 0 | +0.473 ns | 9.349 ns |

Fresh CLPD SRAM results from the 2026-06-15 Vivado rerun:

| CLPD storage block | Part | Entries | LUTs | FFs | BRAM tiles | BRAM % | Timing status |
|---|---|---:|---:|---:|---:|---:|---|
| Synthesized CLPD SRAM | `xc7a200tfbg676-2` | 65536 | 629 | 156 | 260 | 71.23% | +3.274 ns setup slack at 10 ns |
| Routed CLPD SRAM | `xc7a200tfbg676-2` | 65536 | 636 | 170 | 260 | 71.23% | +0.362 ns setup, +0.281 ns hold at 10 ns |

Status of latest rerun:

- `powershell -ExecutionPolicy Bypass -File research\run_copper_authority_regression_xsim.ps1`
  passed 10 RTL/SVA authority-chain simulations with 0 logged errors.
- `powershell -ExecutionPolicy Bypass -File research\run_copper_peb_xsim.ps1`
  passed the PEB directed testbench with 11 directed cases, 9 boundaries,
  stale-proof blocking, domain isolation, wrap blocking, and 0 errors.
- `powershell -ExecutionPolicy Bypass -File research\run_copper_clpd_sram_dir_synth_sweep.ps1`
  refreshed 1K/2K/4K CLPD SRAM synthesis on `xc7a35tcpg236-1`.
- `powershell -ExecutionPolicy Bypass -File research\run_copper_clpd_sram_dir_synth_a200t.ps1`
  refreshed 16K/64K CLPD SRAM synthesis on `xc7a200tfbg676-2`.
- `powershell -ExecutionPolicy Bypass -File research\run_copper_clpd_sram_dir_impl64k_a200t.ps1`
  completed 64K CLPD out-of-context place-and-route on `xc7a200tfbg676-2`
  with 0 route errors, 0 unrouted nets, 0 partial nets, and positive setup/hold
  slack at a 10 ns clock.
- `powershell -ExecutionPolicy Bypass -File research\run_copper_full_lsq_amba_authority_top_synth.ps1`
  synthesized the retimed full LSQ-to-AMBA authority top on `xc7a35tcpg236-1`
  with 0 errors, 0 critical warnings, 0 warnings, 4,692 LUTs, 3,547 FFs, 0
  BRAM/DSP, and +0.473 ns WNS at a 10 ns clock.
- The current paper should cite the 2026-06-16 LSQ/AMBA/SARI unified XSIM and
  synthesis runs as the freshest composed RTL evidence, and
  `research/results/COPPER_CLPD_SRAM_SYNTH_SUMMARY.md` as the freshest CLPD
  SRAM capacity hardware-cost evidence.

Interpretation:

- `copper_line_provenance_gate` is the paper's core mechanism. It is fast
  because it is an indexed cache-metadata check rather than a CAM-style
  provenance lookup.
- `copper_commit_epoch_proof_bridge` is the backend proof-path guard. It is
  intentionally tiny because it only qualifies commit metadata and checks a
  captured source epoch against the current source epoch.
- `copper_lsq_source_tag_tracker` is the LSQ-adjacent source-tag proof
  contract. It is the new backend evidence that source tags are not simply
  trusted metadata; they must remain live, unstale, and epoch/value-current at
  clean commit before line proof can be created.
- `copper_full_lsq_amba_authority_top` is the integrated public contract for
  backend proof creation, AMBA/SARI-style revocation, retained source/target
  authority, and final DMP issue gating. Its revocation slice is legal only
  because the DMP authority hold extends across the retimed clear cycle.
- `copper_stream_table_gate` is an optional aggressive extension. Its direct
  CAM-like RTL is much closer to the 10 ns limit and should be banked or
  pipelined before being presented as CPU-clock production RTL.
- Top-level FPGA I/O counts are not meaningful because internal cache/control
  signals are exposed as standalone module ports.

## Commands

Core COPPER-LINE synthesis:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_line_synth.ps1
```

Stream-table extension synthesis:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_synth.ps1
```

Commit-epoch proof bridge synthesis:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_commit_epoch_synth.ps1
```

LSQ source-tag tracker synthesis:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_lsq_source_tag_tracker_synth.ps1
```

LSQ-to-CEPF-to-line wrapper synthesis:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_lsq_cepf_line_e2e_top_synth.ps1
```

Full-authority gate simulation:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_full_authority_xsim.ps1
```

Full-authority SVA simulation:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_full_authority_sva_xsim.ps1
```

CEPF-to-line end-to-end SVA simulation:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_cepf_line_e2e_xsim.ps1
```

LSQ source-tag tracker simulation:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_lsq_source_tag_tracker_xsim.ps1
```

LSQ-to-CEPF-to-line end-to-end simulation:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_lsq_cepf_line_e2e_xsim.ps1
```

Full LSQ-to-AMBA authority simulation:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_full_lsq_amba_authority_xsim.ps1
```

Full LSQ-to-AMBA authority synthesis:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_full_lsq_amba_authority_top_synth.ps1
```

CTLW witness directory simulation:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_ctlw_witness_xsim.ps1
```

CTLW-to-full-authority E2E simulation:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_ctlw_full_authority_e2e_xsim.ps1
```

CLPD-CTLW authority E2E simulation:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_clpd_ctlw_authority_e2e_xsim.ps1
```

SARI revoker simulation:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_sari_revoker_xsim.ps1
```

Full-authority gate synthesis attempt:

```text
vivado.bat -mode batch -source research\run_copper_full_authority_synth.tcl
```

CLPD gate simulation:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_clpd_xsim.ps1
```

CLPD gate synthesis attempt:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_clpd_synth.ps1
```
