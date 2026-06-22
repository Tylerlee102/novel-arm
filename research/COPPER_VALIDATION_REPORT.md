# COPPER Validation Report

## Status

This validation pass strengthens COPPER but does not prove it secure. The current evidence supports the refined claim:

> A DMP seed should be allowed only when the exact candidate value from the exact source word previously produced a committed demand access in the same protection context.

The strongest refinement from testing is that COPPER must be **value-bound**, not merely **slot-bound**.

## Artifacts

- `research/copper_dmp_model.py`: finite-cache DMP model with disabled, naive, slot-only COPPER, and value-bound COPPER policies.
- `research/copper_validation.py`: directed adversarial tests plus randomized invariant fuzzing.
- `research/copper_sweep.py`: parameter sweeps for provenance table size, rewrite rate, domain mix, and value-token width.
- `research/copper_prefetch_gate.sv`: SystemVerilog RTL sketch of the COPPER gate.
- `research/copper_prefetch_gate_tb.sv`: directed SystemVerilog testbench.
- `research/copper_stream_gate.sv`: SystemVerilog sketch of the COPPER-STREAM gate.
- `research/copper_stream_gate_tb.sv`: directed SystemVerilog testbench for stream-certified gating.
- `research/run_copper_xsim.tcl`: Vivado/xsim batch launcher.
- `research/run_copper_direct_xsim.ps1`: direct xvlog/xelab/xsim runner that avoids Vivado project Tcl Store issues.

Vivado was found at `C:\AMDDesignTools\2025.2\Vivado\bin\vivado.bat`. Vivado project mode failed because the local Tcl Store initializer is broken, but direct `xvlog`, `xelab`, and `xsim` work. Both HDL directed testbenches passed through `research/run_copper_direct_xsim.ps1`.

## Directed Security Tests

The Python validation suite checks:

1. Naive DMP leaks data-at-rest values.
2. Naive DMP can cross protection domains.
3. Value-bound COPPER blocks DMP use without committed provenance.
4. Committed exact provenance allows a safe same-domain prefetch.
5. Slot-only COPPER fails after a source word is rewritten.
6. Value-bound COPPER blocks the rewritten unproven value.
7. Domain mismatch blocks.
8. Translation failure blocks.
9. Permission failure blocks.
10. Coherence update invalidates provenance.
11. Short value tokens produce collision false positives.

Command:

```text
python research\copper_validation.py --fuzz-trials 1000 --seed 777 --provenance-entries 1024 --cache-lines 128
```

Result:

```text
directed_tests: 6
fuzz_trials: 1000
fuzz_avg_speedup_vs_disabled: 1.627
fuzz_avg_prefetches: 395.982
fuzz_avg_blocked_unproven_values: 52.521
failures: 0
```

Interpretation: no invariant failures were found for full-token value-bound COPPER across directed tests and 1000 randomized workloads. This is evidence for the mechanism, not a proof.

## Headline Workload Result

Command:

```text
python research\copper_dmp_model.py --trials 200 --seed 999 --lists 16 --length 32 --secret-lines 128 --secret-slots 4 --cross-domain-secret-rate 0.5 --repeats 4 --cache-lines 128 --rewrite-fraction 0.05 --provenance-entries 1024 --value-token-bits 64
```

| Policy | Speedup | Demand misses | Prefetches | Data-at-rest | Cross-domain | Unproven-value | Blocked unproven |
|---|---:|---:|---:|---:|---:|---:|---:|
| disabled | 1.000x | 2048.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| naive | 4.075x | 130.2 | 4032.0 | 2048.0 | 1029.3 | 72.0 | 0.0 |
| copper_slot | 2.562x | 628.8 | 1488.0 | 0.0 | 0.0 | 72.0 | 0.0 |
| copper_value | 2.554x | 632.0 | 1416.0 | 0.0 | 0.0 | 0.0 | 72.0 |

Key finding: slot-only COPPER removes raw data-at-rest and cross-domain prefetches but still lets rewritten unproven values through. Value-bound COPPER blocks those with almost no additional speed loss in this workload.

## Provenance Table Sweep

The finite table is a real design constraint.

| Entries | COPPER value speedup | COPPER value prefetches | Security failures |
|---:|---:|---:|---:|
| 0 | 1.000x | 0 | 0 |
| 64 | 1.000x | 0 | 0 |
| 128 | 1.000x | 0 | 0 |
| 256 | 1.000x | 0 | 0 |
| 384 | 1.000x | 0 | 0 |
| 512 | 2.554x | 1416 | 0 |
| 768 | 2.554x | 1416 | 0 |
| 1024 | 2.554x | 1416 | 0 |
| 2048 | 2.554x | 1416 | 0 |

Interpretation: with the current synthetic access order and global LRU provenance table, the benefit has a sharp knee around 512 entries. Smaller tables fail safe by losing performance, not by leaking. For a paper, replacement policy must be treated as a first-class design problem.

## Rewrite Sensitivity

As more source words are rewritten after provenance is learned, value-bound COPPER blocks more stale values and speedup declines.

| Rewrite fraction | Naive speedup | Slot-only speedup | Value-bound speedup | Slot-only unproven prefetches | Value-bound unproven prefetches |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 4.636x | 2.773x | 2.773x | 0 | 0 |
| 0.01 | 4.520x | 2.734x | 2.734x | 12 | 0 |
| 0.05 | 4.072x | 2.562x | 2.554x | 72 | 0 |
| 0.10 | 3.656x | 2.391x | 2.360x | 147 | 0 |
| 0.25 | 2.940x | 2.073x | 1.921x | 372 | 0 |
| 0.50 | 2.527x | 1.893x | 1.470x | 744 | 0 |

Interpretation: COPPER is best for stable pointer structures. It intentionally loses prefetch benefit when pointer-like data mutates into unproven values.

## Domain-Mix Sensitivity

Naive DMP cross-domain prefetches scale with the fraction of cross-domain pointer-looking secret values. Value-bound COPPER stays at zero.

| Cross-domain secret rate | Naive cross-domain prefetches | Value-bound cross-domain prefetches |
|---:|---:|---:|
| 0.00 | 0.0 | 0.0 |
| 0.25 | 512.1 | 0.0 |
| 0.50 | 1021.5 | 0.0 |
| 0.75 | 1542.3 | 0.0 |
| 1.00 | 2048.0 | 0.0 |

## Value-Token Width Sensitivity

Short tokens are unsafe in this model. Because the synthetic addresses are line-aligned, low-bit tokens collide heavily.

| Token bits | Value-bound speedup | Value-bound unproven prefetches |
|---:|---:|---:|
| 0 | 2.562x | 72 |
| 4 | 2.562x | 72 |
| 6 | 2.562x | 72 |
| 8 | 2.563x | 72 |
| 10 | 2.563x | 72 |
| 12 | 2.561x | 72 |
| 16 | 2.554x | 0 |
| 64 | 2.554x | 0 |

Interpretation: the paper should not propose a small hash as the primary token. The safer design is an exact physical-address-derived token, or a collision-checked target tag plus enough entropy to make false matches negligible.

## COPPER-STREAM: Surpassing Both Limits

COPPER-STREAM was added after the first validation pass exposed two limits:

- short value tokens can collide,
- small global provenance tables can fail to retain useful proofs.

The new mechanism replaces per-value proof lookup with stream certification plus dirty-source gating. Once a pointer-producing stream has enough committed uses, DMP candidates from that stream are allowed only if the source word has not been written or invalidated since its last committed proof. Writes/coherence updates mark source words dirty; committed demand use clears the dirty bit. Dirty-table overflow fails safe by blocking stream prefetches.

Stress command:

```text
python research\copper_dmp_model.py --trials 200 --seed 1201 --lists 16 --length 32 --secret-lines 128 --secret-slots 4 --cross-domain-secret-rate 0.5 --repeats 4 --cache-lines 128 --rewrite-fraction 0.05 --provenance-entries 0 --value-token-bits 0 --stream-threshold 32
```

| Policy | Speedup | Provenance entries | Token bits | Data-at-rest | Cross-domain | Unproven-value |
|---|---:|---:|---:|---:|---:|---:|
| copper_value | 1.000x | 0 | 0 | 0.0 | 0.0 | 0.0 |
| copper_stream | 2.554x | 0 | 0 | 0.0 | 0.0 | 0.0 |

Interpretation: COPPER-STREAM recovers the useful prefetch behavior without relying on a global value table or a value hash. This is now the stronger publishable mechanism.

## RTL Validation

The generated SystemVerilog testbench checks:

- unproven seed blocks,
- exact committed value allows,
- stale different value blocks,
- domain mismatch blocks,
- translation failure blocks,
- permission failure blocks,
- coherence invalidation blocks.

Vivado project mode hit a Tcl Store error, so direct xsim is preferred:

```text
powershell -ExecutionPolicy Bypass -File research\run_copper_direct_xsim.ps1
```

Observed passing messages:

```text
COPPER gate directed tests completed
COPPER stream gate directed tests completed
```

The older project-mode launcher remains available but is not the recommended path on this machine:

```text
vivado -mode batch -source research\run_copper_xsim.tcl
```

## Paper Implications

What got stronger:

- The core invariant is now crisp and testable.
- Slot-only provenance is shown to be insufficient by counterexample.
- Full-token value-bound COPPER passed the current adversarial and randomized tests.
- The mechanism fails safe under small provenance tables by dropping prefetches.
- COPPER-STREAM removes the need for a value token and restores benefit with zero provenance entries in the stress case.

What got weaker:

- A short value hash is not acceptable without collision handling.
- A naive global LRU provenance table has an ugly threshold around 512 entries in this workload.
- Performance falls as pointer fields are frequently rewritten.
- COPPER-STREAM now needs its own evaluation: stream misclassification, dirty-table pressure, and multi-PC aliasing are the next likely reviewer targets.

## Current Verdict

COPPER remains worth pursuing. The stronger paper should now be framed around two mechanisms:

1. Value-bound committed pointer provenance as the conservative baseline.
2. COPPER-STREAM as the scalable extension: stream-certified DMP plus fail-safe dirty-source gating.

The next strongest evidence would be a gem5 or ChampSim implementation with real pointer-heavy workloads and a synthesized provenance table design.
