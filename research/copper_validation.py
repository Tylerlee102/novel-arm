#!/usr/bin/env python3
"""
Adversarial validation suite for COPPER.

This suite is deliberately sharper than the throughput model:
it checks security invariants, demonstrates why slot-only provenance is
insufficient, and searches for obvious failure modes such as token collisions,
domain mismatch, permission failure, and coherence invalidation.
"""

from __future__ import annotations

import argparse
import copy
import random
from statistics import mean

from copper_dmp_model import DMPPolicy, Obj, Workload, make_workload, simulate


def tiny_workload() -> Workload:
    objects = {
        0x1000: Obj(addr=0x1000, next_addr=0x1040, domain=0),
        0x1040: Obj(addr=0x1040, next_addr=0x1080, domain=0),
        0x1080: Obj(addr=0x1080, next_addr=None, domain=0),
        0x2000: Obj(addr=0x2000, next_addr=0x2040, domain=1),
        0x2040: Obj(addr=0x2040, next_addr=None, domain=1),
    }
    return Workload(
        objects=objects,
        traversals=[[0x1000, 0x1040, 0x1080]],
        secret_lines=[[0x1040, 0x2000]],
        mutation_sources=[0x1000],
        user_addrs=[0x1000, 0x1040, 0x1080],
    )


def prove_pointer(policy: DMPPolicy, wl: Workload, src: int, value: int, domain: int = 0) -> None:
    policy.load_line(value, requester_domain=domain, wl=wl, source_addr=src, source_slot=0)


def expect(condition: bool, name: str, failures: list[str]) -> None:
    if not condition:
        failures.append(name)


def test_data_at_rest_and_cross_domain(failures: list[str]) -> None:
    wl = tiny_workload()

    naive = DMPPolicy("naive", cache_lines=16, provenance_entries=16)
    naive.scan_secret_line(0, requester_domain=0, wl=wl)
    expect(naive.data_at_rest_prefetches == 2, "naive should prefetch from data-at-rest", failures)
    expect(naive.cross_domain_prefetches == 1, "naive should cross protection domain", failures)

    copper = DMPPolicy("copper_value", cache_lines=16, provenance_entries=16)
    copper.scan_secret_line(0, requester_domain=0, wl=wl)
    expect(copper.data_at_rest_prefetches == 0, "copper_value data-at-rest block", failures)
    expect(copper.cross_domain_prefetches == 0, "copper_value cross-domain block", failures)
    expect(copper.total_prefetches == 0, "copper_value should not prefetch without provenance", failures)


def test_committed_provenance_allows_safe_prefetch(failures: list[str]) -> None:
    wl = tiny_workload()
    copper = DMPPolicy("copper_value", cache_lines=16, provenance_entries=16)
    prove_pointer(copper, wl, src=0x1000, value=0x1040)
    copper._maybe_prefetch(0x1000, 0, 0x1040, 0, 0, wl)
    expect(copper.total_prefetches == 1, "committed exact pointer should be allowed", failures)


def test_slot_only_stale_provenance_failure(failures: list[str]) -> None:
    wl_slot = tiny_workload()
    slot = DMPPolicy("copper_slot", cache_lines=16, provenance_entries=16)
    prove_pointer(slot, wl_slot, src=0x1000, value=0x1040)
    wl_slot.objects[0x1000].next_addr = 0x1080
    wl_slot.objects[0x1000].secret_rewritten = True
    slot._maybe_prefetch(0x1000, 0, 0x1080, 0, 0, wl_slot)
    expect(slot.unproven_value_prefetches == 1, "slot-only should fail stale-provenance test", failures)

    wl_value = tiny_workload()
    value = DMPPolicy("copper_value", cache_lines=16, provenance_entries=16)
    prove_pointer(value, wl_value, src=0x1000, value=0x1040)
    wl_value.objects[0x1000].next_addr = 0x1080
    wl_value.objects[0x1000].secret_rewritten = True
    value._maybe_prefetch(0x1000, 0, 0x1080, 0, 0, wl_value)
    expect(value.unproven_value_prefetches == 0, "value-bound should block stale value", failures)
    expect(value.blocked_unproven_values == 1, "value-bound should count blocked stale value", failures)


def test_domain_permission_and_coherence(failures: list[str]) -> None:
    wl = tiny_workload()
    copper = DMPPolicy("copper_value", cache_lines=16, provenance_entries=16)
    prove_pointer(copper, wl, src=0x1000, value=0x1040, domain=0)

    copper._maybe_prefetch(0x1000, 0, 0x1040, 0, 1, wl)
    expect(copper.total_prefetches == 0, "domain mismatch should block", failures)

    copper._maybe_prefetch(0x1000, 0, 0x1040, 0, 0, wl, translation_ok=False)
    expect(copper.blocked_permission == 1, "translation failure should block", failures)

    copper._maybe_prefetch(0x1000, 0, 0x1040, 0, 0, wl, permission_ok=False)
    expect(copper.blocked_permission == 2, "permission failure should block", failures)

    copper.coherence_update(0x1000)
    copper._maybe_prefetch(0x1000, 0, 0x1040, 0, 0, wl)
    expect(copper.total_prefetches == 0, "coherence update should invalidate provenance", failures)


def test_token_collision_risk(failures: list[str]) -> None:
    wl = tiny_workload()
    copper = DMPPolicy(
        "copper_value",
        cache_lines=16,
        provenance_entries=16,
        value_token_bits=6,
    )
    prove_pointer(copper, wl, src=0x1000, value=0x1040)
    wl.objects[0x1000].next_addr = 0x1080
    wl.objects[0x1000].secret_rewritten = True
    copper._maybe_prefetch(0x1000, 0, 0x1080, 0, 0, wl)
    expect(
        copper.unproven_value_prefetches == 1,
        "short value tokens should expose collision risk",
        failures,
    )


def test_stream_surpasses_token_and_table_limits(failures: list[str]) -> None:
    rng = random.Random(909)
    wl = make_workload(
        rng,
        lists=16,
        length=32,
        secret_lines=128,
        secret_slots=4,
        cross_domain_secret_rate=0.5,
        rewrite_fraction=0.05,
    )
    disabled = simulate(
        "disabled",
        copy.deepcopy(wl),
        repeats=4,
        cache_lines=128,
        provenance_entries=0,
        value_token_bits=0,
        stream_threshold=32,
    )
    stream = simulate(
        "copper_stream",
        copy.deepcopy(wl),
        repeats=4,
        cache_lines=128,
        provenance_entries=0,
        value_token_bits=0,
        stream_threshold=32,
    )
    expect(stream.data_at_rest_prefetches == 0, "stream data-at-rest block", failures)
    expect(stream.cross_domain_prefetches == 0, "stream cross-domain block", failures)
    expect(stream.unproven_value_prefetches == 0, "stream stale-value block", failures)
    expect(disabled.cycles / stream.cycles > 2.0, "stream should retain useful speedup", failures)


def run_random_invariant_fuzz(args: argparse.Namespace, failures: list[str]) -> dict[str, float]:
    rng = random.Random(args.seed)
    speeds = []
    prefetches = []
    blocked = []
    for i in range(args.fuzz_trials):
        wl = make_workload(
            rng,
            lists=rng.randint(2, args.max_lists),
            length=rng.randint(4, args.max_length),
            secret_lines=rng.randint(1, args.max_secret_lines),
            secret_slots=rng.randint(1, args.max_secret_slots),
            cross_domain_secret_rate=rng.random(),
            rewrite_fraction=rng.random() * args.max_rewrite_fraction,
        )
        disabled = simulate(
            "disabled",
            copy.deepcopy(wl),
            repeats=args.repeats,
            cache_lines=args.cache_lines,
            provenance_entries=args.provenance_entries,
            value_token_bits=64,
            stream_threshold=args.stream_threshold,
        )
        copper = simulate(
            "copper_value",
            copy.deepcopy(wl),
            repeats=args.repeats,
            cache_lines=args.cache_lines,
            provenance_entries=args.provenance_entries,
            value_token_bits=64,
            stream_threshold=args.stream_threshold,
        )
        stream = simulate(
            "copper_stream",
            copy.deepcopy(wl),
            repeats=args.repeats,
            cache_lines=args.cache_lines,
            provenance_entries=0,
            value_token_bits=0,
            stream_threshold=args.stream_threshold,
        )
        if copper.data_at_rest_prefetches != 0:
            failures.append(f"fuzz {i}: data-at-rest leak")
        if copper.cross_domain_prefetches != 0:
            failures.append(f"fuzz {i}: cross-domain leak")
        if copper.unproven_value_prefetches != 0:
            failures.append(f"fuzz {i}: unproven-value leak")
        if stream.data_at_rest_prefetches != 0:
            failures.append(f"fuzz {i}: stream data-at-rest leak")
        if stream.cross_domain_prefetches != 0:
            failures.append(f"fuzz {i}: stream cross-domain leak")
        if stream.unproven_value_prefetches != 0:
            failures.append(f"fuzz {i}: stream unproven-value leak")
        speeds.append(disabled.cycles / copper.cycles if copper.cycles else 0.0)
        prefetches.append(copper.total_prefetches)
        blocked.append(copper.blocked_unproven_values)

    return {
        "avg_speedup": mean(speeds) if speeds else 0.0,
        "avg_prefetches": mean(prefetches) if prefetches else 0.0,
        "avg_blocked_unproven": mean(blocked) if blocked else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--fuzz-trials", type=int, default=500)
    parser.add_argument("--max-lists", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=32)
    parser.add_argument("--max-secret-lines", type=int, default=64)
    parser.add_argument("--max-secret-slots", type=int, default=8)
    parser.add_argument("--max-rewrite-fraction", type=float, default=0.25)
    parser.add_argument("--repeats", type=int, default=4)
    parser.add_argument("--cache-lines", type=int, default=128)
    parser.add_argument("--provenance-entries", type=int, default=1024)
    parser.add_argument("--stream-threshold", type=int, default=32)
    args = parser.parse_args()

    failures: list[str] = []
    test_data_at_rest_and_cross_domain(failures)
    test_committed_provenance_allows_safe_prefetch(failures)
    test_slot_only_stale_provenance_failure(failures)
    test_domain_permission_and_coherence(failures)
    test_token_collision_risk(failures)
    test_stream_surpasses_token_and_table_limits(failures)
    fuzz_summary = run_random_invariant_fuzz(args, failures)

    print("COPPER adversarial validation")
    print(f"directed_tests: 6")
    print(f"fuzz_trials: {args.fuzz_trials}")
    print(f"fuzz_avg_speedup_vs_disabled: {fuzz_summary['avg_speedup']:.3f}")
    print(f"fuzz_avg_prefetches: {fuzz_summary['avg_prefetches']:.3f}")
    print(f"fuzz_avg_blocked_unproven_values: {fuzz_summary['avg_blocked_unproven']:.3f}")
    print(f"failures: {len(failures)}")
    for failure in failures[:20]:
        print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
