#!/usr/bin/env python3
"""Parameter sweeps for COPPER validation."""

from __future__ import annotations

import argparse
import copy
import random
from statistics import mean

from copper_dmp_model import DMPPolicy, make_workload, simulate


POLICIES = ("disabled", "naive", "copper_slot", "copper_value", "copper_stream")


def run_condition(
    *,
    trials: int,
    seed: int,
    lists: int,
    length: int,
    secret_lines: int,
    secret_slots: int,
    cross_domain_secret_rate: float,
    repeats: int,
    cache_lines: int,
    rewrite_fraction: float,
    provenance_entries: int,
    value_token_bits: int,
    stream_threshold: int,
) -> dict[str, list[DMPPolicy]]:
    rng = random.Random(seed)
    results: dict[str, list[DMPPolicy]] = {policy: [] for policy in POLICIES}
    for _ in range(trials):
        wl = make_workload(
            rng,
            lists,
            length,
            secret_lines,
            secret_slots,
            cross_domain_secret_rate,
            rewrite_fraction,
        )
        for policy in POLICIES:
            results[policy].append(
                simulate(
                    policy,
                    copy.deepcopy(wl),
                    repeats,
                    cache_lines,
                    provenance_entries,
                    value_token_bits,
                    stream_threshold,
                )
            )
    return results


def summarize(results: dict[str, list[DMPPolicy]]) -> list[dict[str, float | str]]:
    disabled_cycles = mean(policy.cycles for policy in results["disabled"])
    rows: list[dict[str, float | str]] = []
    for name, policies in results.items():
        cycles = mean(policy.cycles for policy in policies)
        rows.append(
            {
                "policy": name,
                "speedup": disabled_cycles / cycles if cycles else 0.0,
                "demand_misses": mean(policy.demand_misses for policy in policies),
                "prefetches": mean(policy.total_prefetches for policy in policies),
                "data_at_rest": mean(policy.data_at_rest_prefetches for policy in policies),
                "cross_domain": mean(policy.cross_domain_prefetches for policy in policies),
                "unproven_value": mean(policy.unproven_value_prefetches for policy in policies),
                "blocked_unproven": mean(policy.blocked_unproven_values for policy in policies),
                "blocked_permission": mean(policy.blocked_permission for policy in policies),
            }
        )
    return rows


def emit_rows(sweep: str, param: str, value: float | int, rows: list[dict[str, float | str]]) -> None:
    for row in rows:
        print(
            f"{sweep},{param},{value},{row['policy']},"
            f"{row['speedup']:.4f},{row['demand_misses']:.3f},{row['prefetches']:.3f},"
            f"{row['data_at_rest']:.3f},{row['cross_domain']:.3f},"
            f"{row['unproven_value']:.3f},{row['blocked_unproven']:.3f},"
            f"{row['blocked_permission']:.3f}"
        )


def run_and_emit(args: argparse.Namespace, sweep: str, param: str, value: float | int, **overrides: float | int) -> None:
    seed_mix = sum(ord(ch) for ch in f"{sweep}:{param}:{value}")
    config = {
        "trials": args.trials,
        "seed": args.seed + seed_mix,
        "lists": args.lists,
        "length": args.length,
        "secret_lines": args.secret_lines,
        "secret_slots": args.secret_slots,
        "cross_domain_secret_rate": args.cross_domain_secret_rate,
        "repeats": args.repeats,
        "cache_lines": args.cache_lines,
        "rewrite_fraction": args.rewrite_fraction,
        "provenance_entries": args.provenance_entries,
        "value_token_bits": args.value_token_bits,
        "stream_threshold": args.stream_threshold,
    }
    config.update(overrides)
    emit_rows(sweep, param, value, summarize(run_condition(**config)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=100)
    parser.add_argument("--seed", type=int, default=202)
    parser.add_argument("--lists", type=int, default=16)
    parser.add_argument("--length", type=int, default=32)
    parser.add_argument("--secret-lines", type=int, default=128)
    parser.add_argument("--secret-slots", type=int, default=4)
    parser.add_argument("--cross-domain-secret-rate", type=float, default=0.5)
    parser.add_argument("--repeats", type=int, default=4)
    parser.add_argument("--cache-lines", type=int, default=128)
    parser.add_argument("--rewrite-fraction", type=float, default=0.05)
    parser.add_argument("--provenance-entries", type=int, default=1024)
    parser.add_argument("--value-token-bits", type=int, default=64)
    parser.add_argument("--stream-threshold", type=int, default=32)
    args = parser.parse_args()

    print(
        "sweep,param,value,policy,speedup,demand_misses,prefetches,"
        "data_at_rest,cross_domain,unproven_value,blocked_unproven,blocked_permission"
    )

    for entries in (0, 64, 128, 256, 384, 512, 768, 1024, 2048):
        run_and_emit(args, "table", "provenance_entries", entries, provenance_entries=entries)

    for rewrite in (0.0, 0.01, 0.05, 0.10, 0.25, 0.50):
        run_and_emit(args, "rewrite", "rewrite_fraction", rewrite, rewrite_fraction=rewrite)

    for domain_rate in (0.0, 0.25, 0.50, 0.75, 1.0):
        run_and_emit(
            args,
            "domain_mix",
            "cross_domain_secret_rate",
            domain_rate,
            cross_domain_secret_rate=domain_rate,
        )

    for bits in (0, 4, 6, 8, 10, 12, 16, 64):
        run_and_emit(args, "token", "value_token_bits", bits, value_token_bits=bits)

    for threshold in (1, 4, 8, 16, 32, 64, 128):
        run_and_emit(args, "stream", "stream_threshold", threshold, stream_threshold=threshold)


if __name__ == "__main__":
    main()
