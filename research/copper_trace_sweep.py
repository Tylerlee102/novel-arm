#!/usr/bin/env python3
"""Trace-driven sweeps for COPPER policies."""

from __future__ import annotations

import argparse
from pathlib import Path
import tempfile

from copper_trace_gen import make_synthetic, write_trace
from copper_trace_sim import POLICIES, read_trace, run_policy


def run_case(args: argparse.Namespace, *, rewrite: float, value_entries: int, dirty_entries: int) -> list[dict[str, str | float | int]]:
    tmp = Path(tempfile.gettempdir()) / "copper_trace_sweep.csv"
    gen_args = argparse.Namespace(
        seed=args.seed,
        lists=args.lists,
        length=args.length,
        secret_lines=args.secret_lines,
        secret_slots=args.secret_slots,
        cross_domain_secret_rate=args.cross_domain_secret_rate,
        rewrite_fraction=rewrite,
        repeats=args.repeats,
    )
    write_trace(tmp, make_synthetic(gen_args))
    events = read_trace(tmp)
    disabled = run_policy(
        events,
        "disabled",
        args.cache_lines,
        value_entries,
        args.stream_threshold,
        dirty_entries,
    )
    rows = []
    for policy in POLICIES:
        state = run_policy(
            events,
            policy,
            args.cache_lines,
            value_entries,
            args.stream_threshold,
            dirty_entries,
        )
        rows.append(
            {
                "policy": policy,
                "speedup": disabled.cycles / state.cycles if state.cycles else 0.0,
                "prefetches": state.prefetches,
                "data_at_rest": state.data_at_rest_prefetches,
                "cross_domain": state.cross_domain_prefetches,
                "unproven_value": state.unproven_value_prefetches,
                "unproven_line": state.unproven_line_prefetches,
                "blocked_dirty": state.blocked_dirty,
                "blocked_untrained": state.blocked_untrained,
                "blocked_unproven": state.blocked_unproven,
            }
        )
    return rows


def emit(sweep: str, param: str, value: float | int, rows: list[dict[str, str | float | int]]) -> None:
    for row in rows:
        print(
            f"{sweep},{param},{value},{row['policy']},{row['speedup']:.4f},"
            f"{row['prefetches']},{row['data_at_rest']},{row['cross_domain']},"
            f"{row['unproven_value']},{row['unproven_line']},{row['blocked_dirty']},"
            f"{row['blocked_untrained']},{row['blocked_unproven']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=404)
    parser.add_argument("--lists", type=int, default=16)
    parser.add_argument("--length", type=int, default=32)
    parser.add_argument("--secret-lines", type=int, default=128)
    parser.add_argument("--secret-slots", type=int, default=4)
    parser.add_argument("--cross-domain-secret-rate", type=float, default=0.5)
    parser.add_argument("--repeats", type=int, default=4)
    parser.add_argument("--cache-lines", type=int, default=128)
    parser.add_argument("--stream-threshold", type=int, default=32)
    args = parser.parse_args()

    print(
        "sweep,param,value,policy,speedup,prefetches,data_at_rest,cross_domain,"
        "unproven_value,unproven_line,blocked_dirty,blocked_untrained,blocked_unproven"
    )
    for entries in (0, 64, 128, 256, 512, 1024):
        emit(
            "value_table",
            "value_entries",
            entries,
            run_case(args, rewrite=0.05, value_entries=entries, dirty_entries=512),
        )

    for rewrite in (0.0, 0.01, 0.05, 0.10, 0.25, 0.50):
        emit(
            "rewrite",
            "rewrite_fraction",
            rewrite,
            run_case(args, rewrite=rewrite, value_entries=1024, dirty_entries=512),
        )

    for dirty in (0, 8, 16, 32, 64, 128, 512):
        emit(
            "dirty_table",
            "dirty_entries",
            dirty,
            run_case(args, rewrite=0.05, value_entries=0, dirty_entries=dirty),
        )


if __name__ == "__main__":
    main()
