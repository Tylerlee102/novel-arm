# COPPER: Committed Pointer-Provenance Prefetching

Status update, 2026-06-10: this note records the earlier value-bound version of
COPPER. The current strongest mechanism is **COPPER-LINE with Recursive
Carried-Provenance (RCP) and CPTQ**, summarized in
`research/COPPER_FULL_PAPER.md` and `research/results/GEM5_COPPER_SUMMARY.md`.
The value-table observations below remain useful history, but they are no
longer the recommended paper center.

## Thesis

Data-memory-dependent prefetchers (DMPs) should only dereference values that committed execution has already proven to be pointers in the same protection context. COPPER keeps the useful part of DMP behavior for pointer-heavy code while blocking DMP use of passive data that merely resembles an address.

The refined mechanism is **value-bound committed pointer provenance**:

```text
allow_dmp_seed(source_line, word_offset, candidate_value, domain)
    iff committed_demand_access_previously_used(
        source_line, word_offset, candidate_value, domain
    )
    and candidate_value translates with permission in domain
```

The value binding matters. A weaker slot-only rule, "this word offset was once used as a pointer," is insufficient because a later secret-looking value can occupy the same cache word.

## Threat Model

COPPER targets DMP-style data-at-rest leakage, as described by Augury and GoFetch, where the prefetcher reads memory contents and turns pointer-looking data into cache fills without the program architecturally dereferencing that data.

Out of scope:

- General Spectre/Meltdown leakage unrelated to DMP dereference behavior.
- Software prefetch instructions.
- Attacks where the victim architecturally uses the secret as an address; COPPER intentionally treats that as already address-observable.

## Prior Art Position

- Augury and GoFetch demonstrate the DMP leakage problem and show that DMPs can act on data-at-rest.
- SplittingSecrets prevents secrets from looking like addresses through compiler transformation.
- SafeSpec hides speculative side effects, but DMP data-at-rest leakage can be non-speculative memory-system behavior.
- ICP and other indirect prefetchers improve irregular prefetching, but do not define a data-at-rest safety invariant.

To the best of public knowledge from this search pass, the specific invariant "DMP seed eligibility requires exact committed value provenance under a matching domain" is not a public architectural mechanism.

## Prototype

The toy model is in `research/copper_dmp_model.py`.

It compares four policies:

- `disabled`: no DMP.
- `naive`: any pointer-looking data can seed a DMP prefetch.
- `copper_slot`: a cache slot may seed after that slot once supplied a committed demand address.
- `copper_value`: the slot and exact value must match a prior committed demand address.

Representative run:

```text
python research\copper_dmp_model.py --trials 1000 --seed 51 --lists 16 --length 32 \
  --secret-lines 128 --secret-slots 4 --cross-domain-secret-rate 0.5 \
  --repeats 4 --cache-lines 128 --rewrite-fraction 0.05 --provenance-entries 1024
```

Results:

| Policy | Speedup vs no DMP | Demand misses | Data-at-rest prefetches | Cross-domain prefetches | Unproven-value prefetches |
|---|---:|---:|---:|---:|---:|
| disabled | 1.000x | 2048.0 | 0.0 | 0.0 | 0.0 |
| naive | 4.072x | 130.7 | 2048.0 | 1023.2 | 72.0 |
| copper_slot | 2.562x | 628.8 | 0.0 | 0.0 | 72.0 |
| copper_value | 2.554x | 632.0 | 0.0 | 0.0 | 0.0 |

The slot-only policy fails the stale-provenance test. Value-bound COPPER blocks the 72 unproven-value prefetches with negligible extra performance loss in this toy model.

## Bounded Table Observation

With a naive global LRU provenance table:

| Provenance entries | COPPER value speedup | Notes |
|---:|---:|---|
| 64 | 1.000x | Provenance footprint thrashes. |
| 128 | 1.000x | Still thrashes. |
| 256 | 1.000x | Still below useful footprint. |
| 384 | 1.000x | Cascading eviction in this synthetic stream. |
| 512 | 2.554x | Recovers useful pointer-chain benefit. |
| 1024 | 2.554x | No further benefit in this workload. |

This makes replacement policy part of the paper, not a footnote. A realistic design should test PC-indexed, stream-local, or set-partitioned provenance tables instead of a single global LRU.

## RTL Structure

COPPER has two paths:

1. Commit path records a provenance token when a load uses a word previously loaded from memory as its effective address and the demand access commits.
2. DMP request path checks the token before allowing a memory-content-derived candidate address to issue.

Token fields:

- Source physical line tag.
- Source word offset.
- Exact candidate value token, physical target tag, or collision-checked equivalent. A short hash is not sufficient.
- ASID/VMID/security-state or equivalent domain.
- Optional MTE/PAC/tag-state class.
- Coherence/version epoch or invalidation hook.

The token must be invalidated or made non-matching when the source line is overwritten, evicted, or receives a coherence update.

## Most Important Next Experiments

1. Implement a DMP plus COPPER in ChampSim or gem5.
2. Evaluate pointer-heavy workloads: GAP, SPEC pointer-rich benchmarks, in-memory indexes, graph traversal.
3. Reproduce Augury/GoFetch-style data-at-rest trigger patterns in the simulator.
4. Sweep provenance table organization: global LRU, per-PC, per-stream, set-associative, and source-line versioned.
5. Build a small RTL prototype of the gate and estimate CAM/hash timing, area, and power.

## Additional Validation Finding

The expanded validation suite found that short value tokens can recreate the stale-value vulnerability through collisions. In the current synthetic workload, 0-12 bit value tokens behaved like slot-only provenance and allowed 72 unproven-value prefetches per trial; 16-bit and 64-bit tokens blocked them. This does not prove 16 bits is enough generally. The paper should specify exact physical-address-derived tokens or a collision-checked representation, not a small hash.

## COPPER-STREAM Extension

To address both short-token collisions and global-table pressure, the newer mechanism is **COPPER-STREAM**:

```text
allow_stream_dmp(source_word, domain)
    iff pointer-producing stream is trained
    and source_word is not marked dirty since its last committed proof
    and source domain equals target domain
    and translation and permission checks pass
```

COPPER-STREAM learns a repeated committed pointer-producing load stream, then gates future DMPs using a dirty-source table instead of a per-value provenance table. Source writes and coherence updates mark a source word dirty. A later committed demand use clears that dirty mark. Dirty-table overflow fails safe by blocking stream prefetches.

In the stress case where ordinary COPPER had no provenance entries and a zero-bit value token, COPPER-STREAM still achieved 2.554x speedup with zero modeled data-at-rest, cross-domain, and unproven-value prefetches. This is a stronger research direction than relying on short hashes.

## Current Verdict

COPPER is still at "needs more evidence," but the refined value-bound invariant is stronger than the first version. The paper should center on the stale-provenance counterexample because it makes the mechanism feel necessary rather than decorative.
