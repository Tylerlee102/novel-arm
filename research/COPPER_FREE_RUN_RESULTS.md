# COPPER Free-Tool Run Results

Date: 2026-06-12 local machine time

Goal: run every no-license/free evaluation path currently available for COPPER and record what completed.

## Completed Locally

These runs completed on the local Windows/Vivado workstation.

### Python Trace Evaluation

Command:

```text
python research\copper_final_eval.py
```

Outputs:

- `research/results/copper_final_results.csv`
- `research/results/COPPER_RESULTS.md`

Main synthetic trace:

| Policy | Speedup | Prefetches | Data-at-rest | Cross-domain | Unproven value | Unproven line |
|---|---:|---:|---:|---:|---:|---:|
| disabled | 1.000x | 0 | 0 | 0 | 0 | 0 |
| naive | 3.628x | 4032 | 2048 | 1076 | 2616 | 2616 |
| copper_value | 2.414x | 1416 | 0 | 0 | 0 | 0 |
| copper_line | 2.414x | 1416 | 0 | 0 | 0 | 0 |
| copper_stream | 1.641x | 944 | 0 | 0 | 0 | 0 |

Adversarial trace:

| Policy | Speedup | Prefetches | Data-at-rest | Cross-domain | Unproven value | Unproven line |
|---|---:|---:|---:|---:|---:|---:|
| disabled | 1.000x | 0 | 0 | 0 | 0 | 0 |
| naive | 1.020x | 7 | 1 | 2 | 4 | 3 |
| copper_value | 1.000x | 1 | 0 | 0 | 0 | 0 |
| copper_line | 1.000x | 1 | 0 | 0 | 0 | 0 |
| copper_stream | 1.000x | 1 | 0 | 0 | 0 | 0 |

### Python Adversarial/Fuzz Validation

Command:

```text
python research\copper_validation.py
```

Result:

| Metric | Value |
|---|---:|
| Directed tests | 6 |
| Fuzz trials | 500 |
| Average speedup vs disabled | 1.671x |
| Average prefetches | 412.374 |
| Average blocked unproven values | 57.012 |
| Failures | 0 |

### Vivado RTL Simulation

Command:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_direct_xsim.ps1
```

Passing test messages:

```text
COPPER gate directed tests completed
COPPER stream gate directed tests completed
COPPER stream table gate directed tests completed
COPPER line provenance directed tests completed
COPPER line provenance random invariant tests completed: trials=2000 allowed=339 blocked=1152 errors=0
COPPER commit-epoch proof bridge directed tests completed
```

### Vivado Synthesis

Commands:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_line_synth.ps1
powershell -ExecutionPolicy Bypass -File research\run_copper_synth.ps1
```

Target:

- Vivado 2025.2
- FPGA part: `xc7a35tcpg236-1`
- Clock constraint: 10 ns

| RTL block | Slice LUTs | Slice registers | BRAM | DSP | WNS at 10 ns | Worst data path |
|---|---:|---:|---:|---:|---:|---:|
| `copper_line_provenance_gate` | 2063 / 20800, 9.92% | 1024 / 41600, 2.46% | 0 | 0 | +8.122 ns | 1.727 ns |
| `copper_commit_epoch_proof_bridge` | 5 / 20800, 0.02% | 0 / 41600, 0.00% | 0 | 0 | +3.682 ns | 6.318 ns |
| `copper_stream_table_gate` | 2528 / 20800, 12.15% | 2209 / 41600, 5.31% | 0 | 0 | +0.232 ns | 9.386 ns |

## Free Toolchain Installed

Installed locally under `tools/msys64` using the official MSYS2 installer.

| Toolchain component | Result |
|---|---|
| Git | 2.54.0 |
| GCC/G++ | 16.1.0 |
| GNU Make | 4.4.1 |
| CMake | 4.3.3 |
| Python | 3.14.5 |
| SCons | 4.10.1 |
| WSL | Still blocked; Windows feature enable requires elevated administrator rights |

## ChampSim Completed

ChampSim was cloned, dependency-bootstrapped, patched for local MSYS2/MinGW
portability, built, and run.

Local ChampSim build fixes:

- response-file include paths changed from MSYS absolute `/c/...` paths to
  relative paths so MinGW GCC can consume them from `@absolute.options`;
- one iterator-span helper made type-explicit to avoid a Windows `long` versus
  `ptrdiff_t` `std::min` ambiguity.

Built binaries:

- `external/ChampSim/bin/champsim_no.exe`
- `external/ChampSim/bin/champsim_next_line_l1d.exe`
- `external/ChampSim/bin/champsim_ip_stride_l1d.exe`

Generated traces:

- `research/traces/champsim/sequential_scan.champsimtrace`
- `research/traces/champsim/pointer_chase.champsimtrace`
- `research/traces/champsim/adversarial_shape.champsimtrace`

Summary files:

- `research/results/champsim/champsim_summary.csv`
- `research/results/champsim/CHAMPSIM_SUMMARY.md`

Key zero-warmup ChampSim results:

| Prefetcher | Trace | IPC | L1D miss rate | L1D misses | Prefetches issued | Useful prefetches |
|---|---|---:|---:|---:|---:|---:|
| no | sequential_scan | 0.86120 | 0.00673 | 135 | 0 | 0 |
| next_line | sequential_scan | 0.86083 | 0.00943 | 253 | 6769 | 0 |
| ip_stride | sequential_scan | 0.86120 | 0.00673 | 135 | 0 | 0 |
| no | pointer_chase | 0.81626 | 0.00967 | 194 | 0 | 0 |
| next_line | pointer_chase | 0.82566 | 0.01026 | 262 | 5506 | 7 |
| ip_stride | pointer_chase | 0.81626 | 0.00967 | 194 | 0 | 0 |
| no | adversarial_shape | 0.93533 | 0.00713 | 119 | 0 | 0 |
| next_line | adversarial_shape | 0.93625 | 0.00978 | 202 | 3960 | 0 |
| ip_stride | adversarial_shape | 0.93687 | 0.00775 | 130 | 117 | 0 |

Interpretation: stock prefetchers did not provide meaningful benefit on these
pointer-shaped synthetic traces. Next-line issued many low-usefulness prefetches.
This is useful supporting evidence, but stock ChampSim traces do not carry
committed pointer values or provenance domains, so COPPER-specific safety claims
still come from the Python trace model and RTL.

## GAPBS Completed

GAP Benchmark Suite was cloned, built with OpenMP, and run on generated
Kronecker graphs with verification enabled.

Summary files:

- `research/results/gapbs/gapbs_summary.csv`
- `research/results/gapbs/GAPBS_SUMMARY.md`

Largest local runs:

| Kernel | Scale | Trials | Nodes | Edges | Avg trial time | Verification |
|---|---:|---:|---:|---:|---:|---|
| BFS | 20 | 1 | 1048576 | 15699691 | 0.00750 s | PASS |
| CC | 20 | 1 | 1048576 | 15699691 | 0.01170 s | PASS |
| PageRank | 20 | 1 | 1048576 | 15699691 | 0.07741 s | PASS |
| SSSP | 20 | 1 | 1048576 | 15699691 | 0.07328 s | PASS |

One intentionally short PageRank smoke run at scale 12 with only 5 iterations
failed verification because it was below the convergence setting. The scale 16,
18, and 20 PageRank runs used the normal settings and passed.

## gem5 ARM Completed

gem5 was cloned and built locally under native MSYS2/Windows after several
portability fixes to gem5/SCons/Kconfig and a Windows PE link workaround.

Local build fixes:

- SCons compiler detection now inherits the process `PATH` and falls back to
  direct `gcc`/`g++` tool loading when `FindTool` returns `None`;
- Python version/config probing was hardened for the local MSYS2 shell;
- Kconfig generation was patched to write and consume the intended ARM config;
- ARM generated decoder objects compile with `-Wa,-mbig-obj` to avoid PE/COFF
  section-count failures;
- Cygwin/MSYS compatibility fixes were added for libelf, stdio macro collisions,
  syscall guards, `setjmp` fiber handling, `sync()`, `MAP_NORESERVE`, and socket
  type differences;
- Linux-style `-rdynamic` is skipped on Cygwin/MSYS so the linker does not try
  to export more than 100k internal gem5 symbols.

Build result:

| Target | Result | Size | Notes |
|---|---|---:|---|
| `build/ARM/gem5.opt` | Linked | 4.48 GB | Too large/oddly sectioned for local `strip`; MSYS reports exec-format failure |
| `build/ARM/gem5.fast` | PASS | 117.6 MB | Runs from MSYS |
| `build/ARM/gem5.fast.exe` | PASS | 117.6 MB | Runs from PowerShell when `tools/msys64/usr/bin` is on `PATH` |

Validation:

| Check | Result |
|---|---|
| `gem5.fast --help` | PASS |
| PowerShell launch of `gem5.fast.exe --help` | PASS |
| Object probe | PASS: exposes `ArmTimingSimpleCPU`, `ArmMinorCPU`, `ArmO3CPU`, and major prefetchers |
| ARM SE smoke test | PASS: bundled ARM `hello` printed `Hello world!` |
| Stats generation | PASS: `stats.txt` produced |

Important artifacts:

- `external/gem5/build/ARM/gem5.fast.exe`
- `research/run_gem5_msys_fast_build.sh`
- `research/gem5_smoke_simple_arm.py`
- `research/results/gem5_fast_build_msys.log`
- `research/results/gem5_fast_help_powershell.txt`
- `research/results/gem5_objects_probe_cpu.log`
- `research/results/gem5_arm_smoke.log`
- `research/results/gem5_arm_smoke_m5out/stats.txt`

Smoke result:

```text
Beginning ARM smoke simulation
Hello world!
Exiting @ tick 368724000 because exiting with last active thread context
```

The smoke run is ARM syscall-emulation mode, not a full-system Linux boot. It is
enough to confirm a working ARM gem5 simulator, ARM CPU objects, cache/prefetcher
objects, and statistics output on this machine.

## Interpretation

Free local evaluations now completed:

1. Python trace model.
2. Python fuzz/adversarial validation.
3. Vivado RTL simulation.
4. Vivado synthesis.
5. ChampSim build and synthetic trace comparison against no/next-line/IP-stride.
6. GAPBS build and verified generated-graph runs through scale 20.
7. gem5 ARM fast build, object probe, ARM SE hello smoke test, and stats dump.
8. gem5 COPPER prefetcher integration and ARM/AArch64 SE pointer-workload campaign.
9. CEPF backend proof-bridge RTL simulation and synthesis.
10. Graph-style provenance trace with CSR-like edge slots, adversarial data, and rewritten edges.
11. gem5 ARM64 Ubuntu/Linux full-system boot/readfile probe with `no_systemd=true`.
12. gem5 ARM64 Ubuntu/Linux full-system native static AArch64 workload ROI with gem5 stats reset/dump.
13. gem5 ARM64 Ubuntu/Linux full-system timing ROI with none, stride, naive pointer-shaped DMP, pre-PASB COPPER, and PASB-COPPER attached at L1D.
14. gem5 ARM64 Ubuntu/Linux larger generated AArch64 page-permuted/random pointer ROIs with CTLW-terminal COPPER attached at L1D.
15. gem5 ARM64 Ubuntu/Linux generated AArch64 graph-gather ROI with none, stride, naive DMP, and CTLW-terminal COPPER attached at L1D.
16. LLVM/clang + LLD freestanding AArch64 C compilation path, validated in gem5 SE and ARM64 full-system Linux.
17. gem5 ARM64 Ubuntu/Linux compiled C kernel suite with graph gather, hash probing, tree lookup, and fake pointer-shaped data.
18. Bounded PASB/CTLW/terminal invariant checker with expected counterexamples for weakened variants.
19. gem5 ARM64 Ubuntu/Linux GAPBS-inspired compiled C mini-suite with BFS, SSSP-like relaxation, PageRank-style gather, connected-components-style propagation, and fake pointer-shaped data.
20. Richer bounded COPPER authority state-space checker with source value/epoch, CEPF, PASB, CTLW, witness invalidation, and terminal-fill state.
21. Vivado XSIM full-authority RTL gate regression for the combined CEPF/PASB/CTLW/terminal allow/block predicate.
22. Vivado XSIM CTLW-to-full-authority E2E regression connecting the witness directory to the final issue gate.
23. Vivado XSIM CLPD-CTLW authority E2E regression connecting compressed source proof, exact target witness, and the final issue gate.
24. Vivado XSIM SARI revoker regression for DMA/CHI/coherent-I/O source revocations, target remap/TLBI pass-through, and immediate DMP hold.
25. Vivado XSIM SARI-to-CLPD/CTLW/full-authority regression for same-cycle external revocation hold and post-drain blocking.
26. Vivado XSIM CS-SARI conflict-scoped revocation regression.
27. Generic and GAPBS-topology CS-SARI revocation trace proxies.

Still missing:

- positive gem5 full-system Arm/AArch64 COPPER speedup on larger real application runs beyond generated static pointer/graph binaries;
- SPEC CPU, because it is licensed and not free unless institutional access is
  available;
- full GAP official input-set run, because the official graph set is large
  enough to require substantial disk/RAM/time.
- official GAPBS AArch64 full-system binary execution, because this Windows/MSYS
  setup has no AArch64 Linux C++ sysroot/libstdc++ path. A direct clang++
  probe against `external/gapbs/src/bfs.cc` failed at `<iostream>`.

## Current Research Strength After Free Local Runs

Local evidence is strong for:

- mechanism correctness under directed and fuzzed traces;
- RTL behavior under Vivado simulation;
- FPGA synthesis feasibility;
- clean headline security/performance tradeoff in generated COPPER traces;
- standard prefetcher weakness on pointer-shaped ChampSim traces;
- successful graph-workload benchmark build and verification;
- working local ARM gem5 execution in syscall-emulation mode with CPU,
  prefetcher, and statistics support.
- gem5 ARM/AArch64 SE evidence that CPTQ plus recursive carried provenance converts
  demand-visible MSHR misses into prefetch-origin misses on pointer loops.
- CEPF evidence that stale source epochs block backend proof creation after overwrite.
- graph-style trace evidence that source-only provenance is unsafe after edge rewrites,
  while COPPER epoch/value provenance blocks stale rewritten-edge prefetches.
- full-system ARM64 Ubuntu/Linux boot/readfile evidence: Linux 6.8.12 mounted
  `/dev/vda2`, loaded `gem5_bridge`, ran the host-provided probe, reported
  `aarch64`, and exited after 470.7M simulated instructions.
- full-system ARM64 native-workload evidence: Linux 6.8.12 ran a static AArch64
  ELF bracketed by ROI reset/dump markers, exited with `rc=0`, and generated
  2.71M simulated ROI instructions. The workload policy output shows naive DMP
  performs 128 data-at-rest prefetches, source-only provenance still permits 6
  stale/unproven rewritten-source prefetches, and COPPER epoch/value blocks both
  classes.
- integrated full-system ARM64 prefetcher evidence: with atomic boot and timing
  ROI, stride improves the tiny native workload by 5.279%, naive pointer-shaped
  DMP issues 40 prefetches with 0 useful and 30 translation faults, pre-PASB
  COPPER leaves 5 faulting recursive authorizations, and PASB-COPPER blocks all
  102 pointer-shaped unproven candidates with 0 translation faults.
- larger full-system ARM64 CTLW evidence: on generated 8192-node page-permuted
  and random native AArch64 ROIs, CTLW-terminal COPPER removes PASB-only
  recursive translation faults and gives small positive timing movement
  (-0.531% and -0.271% ticks versus no prefetch), while blocking about 15k
  unproven pointer-shaped candidates per COPPER run.
- full-system ARM64 graph-gather evidence: a generated static AArch64
  CSR-like edge-slot binary with random target nodes, repeated passes, a
  compute gap, and a fake pointer-shaped side array runs under the same
  Linux/timing ROI harness. COPPER-CTLW gives -0.367% ticks versus no
  prefetch, blocks 8,660 unproven candidates, and records zero translation
  faults; stride still wins this binary because the edge array itself is
  sequential.
- compiled C AArch64 evidence: LLVM/clang 22.1.7 plus LLD can now build
  freestanding AArch64 Linux ELFs locally. A compiled graph/hash/tree/fake
  pointer suite runs in SE and in ARM64 full-system Linux with matching
  checksum `0x5bf8bf1b`; COPPER-CTLW blocks 679 unproven candidates and
  records zero translation faults, but is 0.093% slower than no prefetch on
  the reduced full-system C suite.
- GAPBS-inspired graph-kernel evidence: a separate freestanding AArch64
  mini-suite with BFS, SSSP-like relaxation, PageRank-style gather, and
  connected-components-style propagation runs under the same ARM64
  full-system Linux/timing ROI harness with checksum `0xf1dd4e4d`.
  COPPER-CTLW blocks 952 unproven candidates, removes the 408 CTLW misses and
  408 unavailable recursive translations seen by naive DMP+CTLW, records
  7,729 terminal stops, and has the same ROI tick count as no prefetch. Stride
  remains faster because the reduced mini-suite scans sequential edge arrays.
- bounded invariant evidence: the PASB/CTLW/terminal state checker passes the
  correct mechanism and finds short counterexamples for no-PASB, no-CTLW, and
  no-terminal variants.
- richer bounded authority evidence: `COPPER_FULL_AUTHORITY` passes 11,419
  reachable states to depth 12, while weakened mechanism classes fail with
  short counterexamples for stale backend proof without CEPF, missed source
  invalidation, address-space token reuse, cross-page issue without CTLW,
  page-level or stale target witnesses, and recursive terminal-fill chasing.
- full-authority RTL evidence: `research/copper_full_authority_gate.sv` and
  `research/copper_full_authority_gate_tb.sv` simulate in Vivado XSIM with 12
  directed cases plus 5,000 randomized scoreboard trials. The saved log reports
  `allowed=956 blocked=3731 stale=624 token=123 target=240 terminal=58
  perm=183 errors=0`, plus nonzero named coverage for no-source, unsound,
  stale-value, stale-epoch, PASB-token, same-page allow, cross-page allow,
  missing-witness, wrong-line-witness, stale-witness, terminal, and permission
  classes.
- full-authority SVA evidence: `research/copper_full_authority_sva_tb.sv`
  simulates in Vivado XSIM with 12 directed cases plus 10,000 randomized
  assertion samples. The saved log reports `allowed=1919 blocked=7455
  no_source=4994 unsound=1260 stale_value=794 stale_epoch=584 token=233
  terminal=139 missing_witness=131 wrong_witness=79 stale_witness=54 perm=372
  same_allow=769 cross_allow=1150`. The harness asserts the allow predicate
  implies exact source proof, PASB token match, non-terminal source status,
  target authority, and permission success.
- CEPF-line end-to-end SVA evidence: `research/copper_cepf_line_e2e_sva_tb.sv`
  connects the CEPF bridge to the line-provenance DMP gate and simulates in
  Vivado XSIM with 12 directed cases plus 10,000 randomized samples. The saved
  log reports `valid_commit=2257 proof_to_allow=769 unproven_block=7658
  stale_epoch_block=151 no_source_block=1247 fault_perm_block=1321
  not_commit_block=1285 write_clear=1 fill_clear=1 invalidate_clear=1
  domain_block=99 translation_block=196 permission_block=1 random_allow=769
  random_block=7954 errors=0`.
- CTLW witness directory RTL evidence: `research/copper_ctlw_witness_dir.sv`
  and `research/copper_ctlw_witness_dir_tb.sv` simulate in Vivado XSIM with 10
  directed cases plus 10,000 randomized samples. The saved log reports
  `exact_hit=1484 miss=6712 token_mismatch=124 line_mismatch=5162
  remap_clear=1 tlbi_token_clear=112 tlbi_all_clear=49 collision=3354
  stale_after_remap_block=1 stale_after_tlbi_block=1 errors=0`.
- CTLW-to-full-authority E2E RTL evidence:
  `research/copper_ctlw_full_authority_e2e_tb.sv` connects the CTLW witness
  directory to the combined authority gate and simulates in Vivado XSIM with 12
  directed cases plus 10,000 randomized samples. The saved log reports
  `exact_cross_allow=3 no_witness_block=7102 token_mismatch_block=28
  line_mismatch_block=6200 stale_after_remap_block=1
  stale_after_tlbi_block=1 terminal_block=274 permission_block=85
  stale_source_block=260 same_page_allow=379 random_allow=382
  random_block=7721 collision=2659 errors=0`.
- CLPD-CTLW authority E2E RTL evidence:
  `research/copper_clpd_ctlw_authority_e2e_tb.sv` connects the compressed
  source-line proof directory, CTLW witness directory, and full-authority gate.
  The saved Vivado XSIM log reports 18 directed plus 10,000 randomized samples:
  `joint_cross_allow=180 same_page_allow=65 no_source_block=8468
  word_unproven_block=181 stale_epoch_block=374 source_token_block=100
  target_no_witness_block=1239 target_line_alias_block=1183 remap_block=1
  tlbi_block=1 write_clear_block=1 fill_clear_block=1
  invalidate_clear_block=1 terminal_block=54 permission_block=12
  clpd_collision=14 ctlw_collision=1376 random_allow=245 random_block=9773
  errors=0`.
- SARI revoker RTL evidence: `research/copper_sari_revoker.sv` queues
  DMA/CHI/coherent-I/O source-line revocations, passes target remap/TLBI events
  to CTLW, and asserts immediate DMP hold while revocation is incoming or
  queued. The saved Vivado XSIM log reports `directed=8 random=10000 dma=1
  chi=1 io=1 triple_burst=1 hold=6321 remap=1 tlbi_token=1 tlbi_all=1
  ready_low=4 overflow=4 final_queue=0 errors=0`.
- SARI authority-path evidence:
  `research/copper_sari_clpd_ctlw_authority_e2e_tb.sv` wires SARI into CLPD,
  CTLW, and the final authority gate. The saved Vivado XSIM log reports
  `directed=12 random=10000 hold_block=1828 dma_hold=1 chi_hold=1 io_hold=1
  remap_hold=1 tlbi_token_hold=1 tlbi_all_hold=1 random_hold=1814 errors=0`.
- CS-SARI evidence: `research/copper_sari_scoped_revoker.sv` replaces global
  SARI hold with a candidate-specific source-line/target-line/token conflict
  predicate. The saved Vivado XSIM log reports `directed=12 random=10000
  conflict_hold=1245 avoided_global_hold=1007 avoided_global_allow=1007
  random_hold=1240 errors=0`. The five-graph GAPBS-topology proxy reports 82.06%
  aggregate hold reduction versus global SARI, 269,879 authorized candidates
  recovered, zero CS-SARI modeled unsafe issues, and 59,013 no-hold unsafe
  issues.
- CLPD RTL evidence: `research/copper_clpd_gate.sv` and
  `research/copper_clpd_gate_tb.sv` simulate in Vivado XSIM with 14 directed
  cases plus 5,000 randomized scoreboard trials. The saved log reports
  `allowed=4 blocked=5012 no_entry=4864 word_unproven=12 stale_epoch=132
  token=2 fault_perm=2 write_clear=1 fill_clear=1 invalidate_clear=1
  collision=1 errors=0`. A CLPD synthesis attempt was made, but the local Vivado
  Tcl app initialization failed before `synth_design`.
- CLPD bounded-checker evidence: `research/copper_clpd_state_space.py`
  compares the compressed directory against a ground-truth committed-proof
  model. Full CLPD passes 24,354 reachable states to depth 8. Weakened variants
  without tag, token, epoch, per-word mask, write-clear, fill-clear, or
  invalidate-clear requirements fail with short counterexamples.
- CLPD storage evidence: `research/copper_clpd_storage_model.py` compares
  edge-exact retained proof against CLPD under explicit assumptions. Across the
  GAPBS-backed graphs, CLPD full coverage is about 30.86-32.00x smaller. On g12, the
  full-cover proxy is 1252.18 KiB for edge-exact versus 39.87 KiB for CLPD. At
  the measured capacity points, 8,192 CLPD entries cost 54.00 KiB and recover
  2.115x, while 131,072 edge-exact entries cost 1696.00 KiB and recover 2.369x.
- security coverage evidence: `research/copper_security_coverage_matrix.py`
  maps ten modeled unsafe classes to COPPER mechanisms and local evidence
  artifacts. The generated matrix passes its evidence string audit and lists
  residual risks for each unsafe class; this is a source-backed coverage audit,
  not a complete proof.

Local evidence is still weak for:

- positive full-system Arm/AArch64 COPPER speedup on larger real applications;
- gem5 IPC on real AArch64 workloads rather than generated/freestanding pointer, graph, and C binaries;
- real binary traces carrying enough semantic information to evaluate committed
  pointer provenance directly.

The remaining main-conference evidence gap is therefore not another Vivado smoke
test or a basic full-system attachment test. It is COPPER timing on richer
AArch64/Linux applications, or an equally rigorous provenance-aware trace
campaign over those workloads. The graph-gather, compiled C, and GAPBS-inspired
mini-suite binaries narrow the gap, but they do not replace official
GAPBS/SPEC/crypto-style application evidence.

## Graph-Style Provenance Trace Completed

The new graph trace is not full GAPBS, but it is closer to graph workloads than
the linked-list microbenchmarks. It models CSR-like edge slots, repeated graph
passes, adversarial pointer-shaped data-at-rest, and a 5% edge rewrite after
warmup.

Summary artifacts:

- `research/copper_graph_workload_eval.py`
- `research/results/graph_copper/graph_copper_summary.csv`
- `research/results/graph_copper/graph_copper_capacity.csv`
- `research/results/graph_copper/GRAPH_COPPER_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_gapbs_mini/GAPBS_OFFICIAL_AARCH64_FEASIBILITY.md`
- `research/gapbs_copper_trace_eval.py`
- `research/results/gapbs_copper_trace/GAPBS_COPPER_TRACE_SUMMARY.md`
- `research/results/gapbs_copper_trace/gapbs_copper_trace_summary.csv`
- `research/results/gapbs_copper_trace/gapbs_copper_trace_capacity.csv`

Ten-seed headline:

| Policy | Speedup vs disabled | Data-at-rest PF | Stale/unproven PF | Interpretation |
|---|---:|---:|---:|---|
| naive | 7.991x | 10240.0 | 0.0 | fastest but unsafe on adversarial data-at-rest |
| source-only provenance | 3.361x | 0.0 | 1638.0 | shows why source-only proof is insufficient after rewrites |
| COPPER epoch/value | 3.276x | 0.0 | 0.0 | blocks both adversarial and stale rewritten-edge cases |

The capacity sweep also exposed a design constraint: with 32,768 graph edge
slots, the proof ledger needs at least 32,768 entries in this scan-order trace
to retain reusable proofs. Smaller ledgers correctly block unsafe issue but lose
the graph-pass speedup.

## GAPBS-Backed COPPER Topology Trace Completed

The next trace step parses public GAPBS serialized `.sg` graph files and replays
edge-scan plus BFS-replay streams over actual generated Kronecker topology. This
is still not official full-system GAPBS execution, but it removes the invented
graph generator from the provenance trace and tests COPPER on GAPBS graph
structure.

Parsed graphs:

| Graph | Nodes | Directed edge slots |
|---|---:|---:|
| kron_g10 | 1,024 | 20,992 |
| kron_g11 | 2,048 | 45,418 |
| kron_g12 | 4,096 | 96,772 |
| kron_g13 | 8,191 | 204,248 |
| kron_g14 | 16,381 | 425,860 |

Five-seed/two-kernel headline:

| Policy | Speedup | Data-at-rest PF | Unproven edge PF | Stale slot PF | Interpretation |
|---|---:|---:|---:|---:|---|
| naive | 3.444x | 16,384.0 | 148,063.5 | 900.8 | fastest but unsafe on data-at-rest and unproven edge values |
| source-only provenance | 1.783x | 0.0 | 900.8 | 900.8 | blocks data-at-rest but fails stale rewritten slots |
| COPPER epoch/value | 1.770x | 0.0 | 0.0 | 0.0 | exact edge proof blocks unsafe prefetches |
| COPPER-CLPD | 1.896x | 0.0 | 0.0 | 0.0 | compressed source-line proof also blocks unsafe prefetches |

The GAPBS-backed capacity sweep exposed and fixed a sharper design limitation.
On the g12 edge-scan replay, the edge-exact ledger shows a cliff: 65,536 entries
still gives 1.000x, while 131,072 entries gives 2.369x. The new CLPD
representation stores one source-line proof mask and epoch per cache line, so it
recovers 2.115x with 8,192 line entries while keeping data-at-rest, unproven-edge,
and stale-slot prefetch counts at zero. Its cost is conservative invalidation:
a write to one slot invalidates the whole source-line proof until demand
recreates it.

## gem5 COPPER Integration Completed

The ARM gem5 tree now includes a runnable `CopperPrefetcher` model:

- `external/gem5/src/mem/cache/prefetch/copper.hh`
- `external/gem5/src/mem/cache/prefetch/copper.cc`
- `research/gem5_copper_arm32_config.py`
- `research/make_arm32_pointer_bench.py`

The mechanism implemented is a committed provenance ledger:

1. demand fills expose candidate pointer values;
2. a later demand access to the candidate line learns a source/value proof;
3. future fills from that source may issue a prefetch only if the proof exists
   and the current value matches;
4. proofs survive clean L1 replacement but are revoked on modeled writes or
   explicit invalidation policy;
5. fill-origin prefetches use a small physical issue queue;
6. CPTQ (Committed Page-Translation Queue) extends that queue across pages only
   when the target has both a committed pointer proof and a valid process
   page-table translation;
7. RCP (Recursive Carried-Provenance) lets prefetched pointer lines seed deeper
   DMP requests only when the prefetched source word/value already has committed
   provenance in the ledger.
8. PASB (Provenance Address-Space Binding) keys proofs and carried-provenance
   records by a translation-context token so proof cannot move across Linux
   address spaces sharing the same hardware context.

Summary artifacts:

- `research/results/gem5_copper_summary.csv`
- `research/results/GEM5_COPPER_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_nosystemd_probe/FS_PROBE_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_native_workload_roi/FS_NATIVE_WORKLOAD_SUMMARY.md`
- `research/results/gem5_arm_ubuntu_fs_native_pasb_timing/FS_PASB_TIMING_SUMMARY.md`

Headline ARM SE timing results:

| Workload | Best COPPER result | Stride comparison | Key interpretation |
|---|---:|---:|---|
| Sequential 8192-node list | +6.76% with recursive COPPER | +98.93% | stride wins because layout is trivially sequential |
| Page-permuted 8192-node list | +6.76% to +6.78% across seeds 1-5 | +0.69% | recursive COPPER survives when stride loses the pattern |
| Fully random 8192-node list | +5.59% to +5.66% across ARM32 seeds 1-3 | +0.59% | CPTQ plus recursive carried provenance rescues the random case |
| AArch64 page-permuted 8192-node list | +6.77% with recursive COPPER | +0.67% | direct AArch64 ELF confirms the ARM32 SE shape |
| AArch64 random 8192-node list | +5.61% with recursive COPPER | +0.57% | direct AArch64 ELF confirms the random cross-page result |
| AArch64 Minor page-permuted/random | +2.79% / +2.64% with recursive COPPER | +0.59% / +0.50% | benefit survives a more detailed in-order core model |
| AArch64 O3 page-permuted/random | +2.77% / +2.68% with recursive COPPER | +0.13% / +0.11% | benefit survives an out-of-order core model with only +0.48-0.50% DRAM-read traffic |
| Medium 256-node page-permuted list | +15.06% with recursive COPPER | +0.17% | smaller test confirms proof/issue path works when stride has little pattern |

Important nuance: COPPER does not yet reduce raw D-cache miss count in these
gem5 runs. Instead, it converts demand-visible MSHR misses into prefetch-origin
MSHR misses. For the full ARM32 random seed-1 list, demand MSHR misses fall from
33,026 to 8,451 while recursive COPPER issues 25,166 committed-proof
prefetches.

The AArch64 full-list runs show the same demand-path shift: demand MSHR misses
fall from about 33,024 to 8,449 while recursive COPPER issues about 25k
prefetch-origin MSHR misses.

Full-system ARM64 timing ROI results:

| Prefetcher | ROI ticks | vs none | L1D misses | PF issued | PF useful | Pointer-like candidates | Learned proofs | Allowed | Blocked | Translation faults |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| none | 3,571,493,265 | 0.000% | 38,899 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| stride | 3,382,963,983 | -5.279% | 32,022 | 15,443 | 7,125 | 0 | 0 | 0 | 0 | 0 |
| naive pointer-shaped DMP | 3,572,333,757 | +0.024% | 38,900 | 40 | 0 | 70 | 32 | 70 | 0 | 30 |
| COPPER before PASB | 3,571,493,265 | 0.000% | 38,899 | 0 | 0 | 102 | 69 | 5 | 97 | 5 |
| PASB-COPPER | 3,571,493,265 | 0.000% | 38,899 | 0 | 0 | 102 | 63 | 0 | 102 | 0 |

This is evidence that the mechanism is real and measurable, but it is not yet a
main-conference-strength application result. CPTQ fixed the first obvious
limitation: same-page-only issue. RCP fixed the next limitation by allowing safe
recursive runahead. The ARM64 full-system timing ROI fixed the next limitation:
proofs must be address-space-bound, not merely hardware-context-bound. The
larger generated full-system runs fixed the next limitation: recursive
cross-page targets need exact committed target-line translation witnesses and
terminal witness-derived fills. The generated graph-gather run then fixed the
"pointer-chain only" concern enough to show COPPER-CTLW on stable CSR-like edge
slots, the LLVM/clang C suite fixed the "hand-generated ELF only" concern, and
the GAPBS-inspired mini-suite adds a BFS/SSSP/PageRank/CC-shaped graph-kernel
  control. The C and mini-suite runs are not COPPER speedup wins, but they show
  the source-authority block, terminal witness behavior, and zero translation
  faults on compiler-authored AArch64 code. The richer authority checker then
  ties CEPF, PASB, CTLW, exact source state, witness invalidation, and terminal
  fills to executable counterexamples. The full-authority RTL gate then checks
  the combined allow/block predicate in XSIM. PASB and CTLW are therefore part of
  the mechanism now. The remaining evidence gap is not whether the prefetcher can
be attached under full-system Linux; it is whether COPPER-CTLW shows useful
speedup on larger official AArch64/Linux workloads while preserving the safety
behavior seen here.

