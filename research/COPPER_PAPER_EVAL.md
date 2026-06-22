# COPPER Paper-Grade Evaluation Pass

## Executive Conclusion

The strongest current mechanism is no longer the original value-token COPPER or stream-only COPPER. The strongest publishable version is:

**COPPER-LINE: line-resident clean pointer provenance for data-memory-dependent prefetchers.**

Core invariant:

```text
allow_dmp(source_line, word, domain)
    iff source_line.word has been used as a committed demand address
    and source_line.word has not been written or invalidated since that proof
    and source domain equals target domain
    and translation/permission checks pass
```

This avoids both limitations found earlier:

- no short value hash, so no token-collision false positives;
- no global value-provenance CAM, so no global table thrashing.

The line metadata acts like a clean proof bit. Writes and coherence invalidations clear it. Eviction drops it. Failure mode is safe: fewer prefetches, not unsafe prefetches.

COPPER-STREAM remains useful as an aggressive extension, but the trace-driven model shows it is more sensitive to untrained streams and dirty-table capacity. For the paper, COPPER-LINE should be the core mechanism and COPPER-STREAM should be a scaling/performance variant.

## New Artifacts

- `research/copper_trace_gen.py`: generates synthetic and adversarial CSV traces.
- `research/copper_trace_sim.py`: trace-driven simulator for disabled, naive, value-bound, line-clean, and stream policies.
- `research/copper_trace_sweep.py`: trace-driven sensitivity sweeps.
- `research/copper_stream_table_gate.sv`: multi-stream RTL gate with stream table and dirty-source CAM.
- `research/copper_stream_table_gate_tb.sv`: directed RTL testbench.
- `research/run_copper_direct_xsim.ps1`: one-command xsim runner for all RTL tests.
- `research/run_copper_synth.ps1`: Vivado synthesis runner with Tcl Store workaround.
- `research/copper_stream_table_constraints.xdc`: 100 MHz synthesis constraint.

## Trace Format

Trace rows are CSV events:

```text
cycle,event,stream,domain,addr,src_line,src_word,candidate,src_domain,target_domain,committed,translation_ok,permission_ok,tag
```

Supported event types:

- `DEMAND`: committed or non-committed demand load.
- `DMP`: data-memory-dependent prefetch candidate.
- `WRITE`: source word rewrite.
- `COH`: coherence invalidation/update.
- `EPOCH`: training boundary for stream policies.

## Trace-Driven Headline Result

Command:

```text
python research\copper_trace_gen.py --scenario synthetic --out research\traces\synthetic.csv --seed 2027 --lists 16 --length 32 --secret-lines 128 --secret-slots 4 --cross-domain-secret-rate 0.5 --rewrite-fraction 0.05 --repeats 4
python research\copper_trace_sim.py research\traces\synthetic.csv --cache-lines 128 --value-entries 1024 --stream-threshold 32 --dirty-entries 512
```

| Policy | Speedup | Prefetches | Data-at-rest | Cross-domain | Unproven value | Unproven line |
|---|---:|---:|---:|---:|---:|---:|
| disabled | 1.000x | 0 | 0 | 0 | 0 | 0 |
| naive DMP | 3.628x | 4032 | 2048 | 1076 | 2616 | 2616 |
| COPPER-value | 2.414x | 1416 | 0 | 0 | 0 | 0 |
| COPPER-LINE | 2.414x | 1416 | 0 | 0 | 0 | 0 |
| COPPER-STREAM | 1.641x | 944 | 0 | 0 | 0 | 0 |

Interpretation:

- Naive DMP is faster but leaks heavily in the modeled trace.
- COPPER-value and COPPER-LINE preserve the same useful subset of prefetches.
- COPPER-LINE does this without a value CAM.
- COPPER-STREAM is safe in this trace but more conservative because many candidates occur before stream training or after dirty marks.

## Zero Value-Table Stress

Command:

```text
python research\copper_trace_sim.py research\traces\synthetic.csv --cache-lines 128 --value-entries 0 --stream-threshold 32 --dirty-entries 512
```

| Policy | Speedup | Prefetches | Data-at-rest | Cross-domain | Unproven value |
|---|---:|---:|---:|---:|---:|
| COPPER-value | 1.000x | 0 | 0 | 0 | 0 |
| COPPER-LINE | 2.414x | 1416 | 0 | 0 | 0 |
| COPPER-STREAM | 1.641x | 944 | 0 | 0 | 0 |

This is the key result for the new mechanism: **line-resident clean provenance surpasses the global value-table limitation**.

## Adversarial Trace

Command:

```text
python research\copper_trace_gen.py --scenario adversarial --out research\traces\adversarial.csv --train-threshold 32
python research\copper_trace_sim.py research\traces\adversarial.csv --cache-lines 128 --value-entries 1024 --stream-threshold 32 --dirty-entries 512
```

| Policy | Data-at-rest | Cross-domain | Unproven value | Blocked permission |
|---|---:|---:|---:|---:|
| naive DMP | 1 | 2 | 4 | 0 |
| COPPER-value | 0 | 0 | 0 | 2 |
| COPPER-LINE | 0 | 0 | 0 | 2 |
| COPPER-STREAM | 0 | 0 | 0 | 2 |

The adversarial trace covers data-at-rest, untrained first use, stale rewrite, cross-domain, translation failure, and permission failure.

## Sensitivity Findings

### Value table size

COPPER-value needs at least 512 entries in this trace. COPPER-LINE is unaffected because the proof state is line-resident.

| Value entries | COPPER-value speedup | COPPER-LINE speedup |
|---:|---:|---:|
| 0 | 1.000x | 2.414x |
| 64 | 1.000x | 2.414x |
| 128 | 1.000x | 2.414x |
| 256 | 1.000x | 2.414x |
| 512 | 2.414x | 2.414x |
| 1024 | 2.414x | 2.414x |

### Rewrite rate

As more pointer fields are rewritten into unproven values, all safe policies lose prefetches by design.

| Rewrite fraction | Naive speedup | COPPER-LINE speedup | COPPER-STREAM speedup |
|---:|---:|---:|---:|
| 0.00 | 4.046x | 2.601x | 1.696x |
| 0.01 | 3.966x | 2.568x | 1.687x |
| 0.05 | 3.608x | 2.414x | 1.641x |
| 0.10 | 3.294x | 2.246x | 1.587x |
| 0.25 | 2.715x | 1.858x | 1.445x |
| 0.50 | 2.364x | 1.445x | 1.258x |

### Dirty table size for COPPER-STREAM

COPPER-STREAM needs dirty-table capacity; below 32 entries in this trace it fails safe and stops prefetching.

| Dirty entries | COPPER-STREAM speedup |
|---:|---:|
| 0 | 1.000x |
| 8 | 1.000x |
| 16 | 1.000x |
| 32 | 1.641x |
| 64 | 1.641x |
| 128 | 1.641x |
| 512 | 1.641x |

## RTL Simulation

Command:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_direct_xsim.ps1
```

Passing messages observed:

```text
COPPER gate directed tests completed
COPPER stream gate directed tests completed
COPPER stream table gate directed tests completed
```

The RTL tests cover:

- unproven candidate blocks,
- exact committed candidate allows,
- stale candidate blocks,
- untrained stream blocks,
- trained stream allows,
- dirty source blocks,
- committed proof clears dirty,
- domain mismatch blocks,
- translation/permission failure blocks,
- dirty-table overflow fails safe.

## Vivado Synthesis

Project-mode Vivado initially failed because the local Tcl Store search path was broken. The workaround in `research/run_copper_synth.ps1` sets `TCLLIBPATH` to the installed Vivado Tcl Store support/app directories.

Command:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_synth.ps1
```

Target:

- Part: `xc7a35tcpg236-1`
- RTL: `copper_stream_table_gate.sv`
- Configuration: default parameters, 8 stream entries, 32 dirty entries
- Constraint: 10 ns clock

Result:

| Metric | Result |
|---|---:|
| Slice LUTs | 2528 / 20800, 12.15% |
| Slice registers | 2209 / 41600, 5.31% |
| BRAM | 0 |
| DSP | 0 |
| WNS at 10 ns | +0.232 ns |
| Worst data path delay | 9.386 ns |

The same naive CAM-style RTL failed a 2 ns constraint with WNS -7.752 ns. This is not surprising: the current RTL is intentionally direct and unpipelined. A CPU-clock implementation needs banking, pipelining, or cache-metadata integration.

Important caveat: the FPGA I/O count is not meaningful because this is a standalone block with internal SoC signals exposed as top-level pins.

## Mechanism Recommendation

Paper framing should shift to:

**COPPER-LINE: Clean-Provenance Metadata for Safe Data-Dependent Prefetching**

with COPPER-STREAM as an optional extension:

**COPPER-STREAM: Stream-Certified DMP with Dirty-Source Gating**

The cleanest contribution is the line-resident invariant:

> A DMP may dereference a memory-derived value only if the source word has a clean committed-pointer proof in the current protection domain.

Why this is stronger than the earlier variants:

- Slot-only provenance is unsafe after rewrites.
- Short value tokens collide.
- Global value tables thrash.
- Line-resident clean proof state naturally invalidates on write/coherence and scales with cache capacity.

## Reviewer Risks

1. **Metadata cost in real cache arrays.**  
   Need an area estimate for per-word proof bits and domain tags in L1/L2 metadata.

2. **First-pass performance loss.**  
   COPPER-LINE cannot prefetch first-time pointer fields until after proof. The paper must quantify warmup loss.

3. **Coherence semantics.**  
   The clean bit must clear on all local writes, remote invalidations, DMA writes, and line fills that replace the data.

4. **Type confusion / stream abuse.**  
   COPPER-STREAM is riskier than COPPER-LINE; reviewers may prefer it as an optional mode.

5. **Real workload evidence.**  
   Synthetic traces are not enough for a full architecture venue. The next step is gem5/ChampSim with GAP/SPEC-like pointer workloads and GoFetch/Augury-style attack traces.

## Current Verdict

**Needs more evidence, but now substantially stronger.**

The research idea is no longer just "value-bound provenance." The stronger, cleaner paper idea is:

> Store clean committed-pointer provenance with the source cache word, and let DMPs act only on source words whose current contents are still covered by that proof.

That is a crisp mechanism, a measurable behavior, and a direct answer to the limitations found during testing.
