#!/usr/bin/env python3
"""Final COPPER evaluation harness for paper tables."""

from __future__ import annotations

from argparse import Namespace
import csv
from pathlib import Path
from statistics import mean, pstdev

from copper_trace_gen import make_adversarial, make_synthetic, write_trace
from copper_trace_sim import Event, POLICIES, run_policy


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
TRACE_DIR = ROOT / "traces"


def synthetic_args(
    *,
    seed: int = 2027,
    lists: int = 16,
    length: int = 32,
    secret_lines: int = 128,
    secret_slots: int = 4,
    cross_domain_secret_rate: float = 0.5,
    rewrite_fraction: float = 0.05,
    repeats: int = 4,
) -> Namespace:
    return Namespace(
        seed=seed,
        lists=lists,
        length=length,
        secret_lines=secret_lines,
        secret_slots=secret_slots,
        cross_domain_secret_rate=cross_domain_secret_rate,
        rewrite_fraction=rewrite_fraction,
        repeats=repeats,
    )


def adversarial_args(*, train_threshold: int = 32) -> Namespace:
    return Namespace(train_threshold=train_threshold)


def rows_to_events(rows: list[dict[str, int | str]]) -> list[Event]:
    events: list[Event] = []
    for raw in rows:
        events.append(
            Event(
                cycle=int(raw["cycle"]),
                event=str(raw["event"]),
                stream=int(raw["stream"]),
                domain=int(raw["domain"]),
                addr=int(raw["addr"]),
                src_line=int(raw["src_line"]),
                src_word=int(raw["src_word"]),
                candidate=int(raw["candidate"]),
                src_domain=int(raw["src_domain"]),
                target_domain=int(raw["target_domain"]),
                committed=bool(int(raw["committed"])),
                translation_ok=bool(int(raw["translation_ok"])),
                permission_ok=bool(int(raw["permission_ok"])),
                tag=str(raw["tag"]),
            )
        )
    return events


def run_trace(
    events: list[Event],
    *,
    cache_lines: int = 128,
    value_entries: int = 1024,
    stream_threshold: int = 32,
    dirty_entries: int = 512,
) -> dict[str, dict[str, float]]:
    states = {
        policy: run_policy(events, policy, cache_lines, value_entries, stream_threshold, dirty_entries)
        for policy in POLICIES
    }
    disabled_cycles = states["disabled"].cycles
    out: dict[str, dict[str, float]] = {}
    for policy, state in states.items():
        out[policy] = {
            "speedup": disabled_cycles / state.cycles if state.cycles else 0.0,
            "cycles": float(state.cycles),
            "demand_misses": float(state.demand_misses),
            "prefetches": float(state.prefetches),
            "data_at_rest": float(state.data_at_rest_prefetches),
            "cross_domain": float(state.cross_domain_prefetches),
            "unproven_value": float(state.unproven_value_prefetches),
            "unproven_line": float(state.unproven_line_prefetches),
            "blocked_dirty": float(state.blocked_dirty),
            "blocked_untrained": float(state.blocked_untrained),
            "blocked_unproven": float(state.blocked_unproven),
            "blocked_permission": float(state.blocked_permission),
        }
    return out


def add_rows(
    rows: list[dict[str, str | float]],
    experiment: str,
    variant: str,
    results: dict[str, dict[str, float]],
) -> None:
    for policy, metrics in results.items():
        row: dict[str, str | float] = {
            "experiment": experiment,
            "variant": variant,
            "policy": policy,
        }
        row.update(metrics)
        rows.append(row)


def aggregate(
    rows: list[dict[str, str | float]],
    experiment: str,
    policy: str,
    metric: str,
) -> tuple[float, float, float, float]:
    values = [
        float(row[metric])
        for row in rows
        if row["experiment"] == experiment and row["policy"] == policy
    ]
    if not values:
        return (0.0, 0.0, 0.0, 0.0)
    return (mean(values), pstdev(values) if len(values) > 1 else 0.0, min(values), max(values))


def write_csv(path: Path, rows: list[dict[str, str | float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "experiment",
        "variant",
        "policy",
        "speedup",
        "cycles",
        "demand_misses",
        "prefetches",
        "data_at_rest",
        "cross_domain",
        "unproven_value",
        "unproven_line",
        "blocked_dirty",
        "blocked_untrained",
        "blocked_unproven",
        "blocked_permission",
    ]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fmt(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def policy_table(results: dict[str, dict[str, float]]) -> str:
    lines = [
        "| Policy | Speedup | Prefetches | Data-at-rest | Cross-domain | Unproven value | Unproven line |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for policy in POLICIES:
        metrics = results[policy]
        lines.append(
            "| "
            + " | ".join(
                [
                    policy,
                    fmt(metrics["speedup"], 3) + "x",
                    str(int(metrics["prefetches"])),
                    str(int(metrics["data_at_rest"])),
                    str(int(metrics["cross_domain"])),
                    str(int(metrics["unproven_value"])),
                    str(int(metrics["unproven_line"])),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def write_markdown(
    path: Path,
    primary: dict[str, dict[str, float]],
    adversarial: dict[str, dict[str, float]],
    rows: list[dict[str, str | float]],
) -> None:
    metadata_lines = [
        "| Domain bits per line | Metadata bits per 64B line | Data-array overhead |",
        "|---:|---:|---:|",
    ]
    for domain_bits in (0, 4, 8, 16):
        bits = 8 + domain_bits
        metadata_lines.append(f"| {domain_bits} | {bits} | {100.0 * bits / 512.0:.2f}% |")

    mc_lines = [
        "| Policy | Mean speedup | Std. dev. | Min | Max | Mean data-at-rest | Mean cross-domain | Mean unproven line |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for policy in POLICIES:
        speed = aggregate(rows, "monte_carlo_seed", policy, "speedup")
        data_at_rest = aggregate(rows, "monte_carlo_seed", policy, "data_at_rest")[0]
        cross_domain = aggregate(rows, "monte_carlo_seed", policy, "cross_domain")[0]
        unproven_line = aggregate(rows, "monte_carlo_seed", policy, "unproven_line")[0]
        mc_lines.append(
            f"| {policy} | {speed[0]:.3f}x | {speed[1]:.3f} | "
            f"{speed[2]:.3f}x | {speed[3]:.3f}x | "
            f"{data_at_rest:.1f} | {cross_domain:.1f} | {unproven_line:.1f} |"
        )

    rewrite_lines = [
        "| Rewrite fraction | Naive speedup | COPPER-value speedup | COPPER-LINE speedup | Naive unproven line | COPPER-LINE unproven line |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for rewrite in (0.0, 0.01, 0.05, 0.10, 0.25, 0.50):
        variant = f"rewrite={rewrite:.2f}"
        subset = [row for row in rows if row["experiment"] == "rewrite_sweep" and row["variant"] == variant]
        def m(policy: str, metric: str) -> float:
            values = [float(row[metric]) for row in subset if row["policy"] == policy]
            return mean(values) if values else 0.0

        rewrite_lines.append(
            f"| {rewrite:.2f} | {m('naive', 'speedup'):.3f}x | "
            f"{m('copper_value', 'speedup'):.3f}x | {m('copper_line', 'speedup'):.3f}x | "
            f"{m('naive', 'unproven_line'):.1f} | {m('copper_line', 'unproven_line'):.1f} |"
        )

    value_lines = [
        "| Value table entries | COPPER-value speedup | COPPER-LINE speedup | COPPER-value prefetches | COPPER-LINE prefetches |",
        "|---:|---:|---:|---:|---:|",
    ]
    for entries in (0, 64, 128, 256, 512, 1024):
        variant = f"value_entries={entries}"
        subset = [row for row in rows if row["experiment"] == "value_capacity" and row["variant"] == variant]
        def m(policy: str, metric: str) -> float:
            values = [float(row[metric]) for row in subset if row["policy"] == policy]
            return mean(values) if values else 0.0

        value_lines.append(
            f"| {entries} | {m('copper_value', 'speedup'):.3f}x | "
            f"{m('copper_line', 'speedup'):.3f}x | "
            f"{m('copper_value', 'prefetches'):.1f} | {m('copper_line', 'prefetches'):.1f} |"
        )

    cache_lines = [
        "| Cache lines | Naive speedup | COPPER-LINE speedup | COPPER-LINE demand misses |",
        "|---:|---:|---:|---:|",
    ]
    for cache in (32, 64, 128, 256):
        variant = f"cache_lines={cache}"
        subset = [row for row in rows if row["experiment"] == "cache_sweep" and row["variant"] == variant]
        def m(policy: str, metric: str) -> float:
            values = [float(row[metric]) for row in subset if row["policy"] == policy]
            return mean(values) if values else 0.0

        cache_lines.append(
            f"| {cache} | {m('naive', 'speedup'):.3f}x | "
            f"{m('copper_line', 'speedup'):.3f}x | {m('copper_line', 'demand_misses'):.1f} |"
        )

    text = f"""# COPPER Final Experimental Results

Generated by `research/copper_final_eval.py`.

## Main Synthetic Trace

{policy_table(primary)}

## Adversarial Trace

{policy_table(adversarial)}

## Monte Carlo, 30 Seeds

{chr(10).join(mc_lines)}

## Rewrite Sensitivity

{chr(10).join(rewrite_lines)}

## Value-Table Capacity Stress

{chr(10).join(value_lines)}

## Cache Capacity Sweep

{chr(10).join(cache_lines)}

## COPPER-LINE Metadata Estimate

Assuming 64-byte cache lines and eight 64-bit source words per line:

{chr(10).join(metadata_lines)}

The minimal mechanism needs eight proof bits per 64-byte line. A small domain
color can be stored per line rather than per word when the cache line is already
owned by one security/translation context.
"""
    path.write_text(text)


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    TRACE_DIR.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict[str, str | float]] = []

    primary_rows = make_synthetic(synthetic_args())
    write_trace(TRACE_DIR / "paper_primary.csv", primary_rows)
    primary = run_trace(rows_to_events(primary_rows))
    add_rows(all_rows, "primary", "seed=2027", primary)

    adversarial_rows = make_adversarial(adversarial_args())
    write_trace(TRACE_DIR / "paper_adversarial.csv", adversarial_rows)
    adversarial = run_trace(rows_to_events(adversarial_rows))
    add_rows(all_rows, "adversarial", "train_threshold=32", adversarial)

    for seed in range(2000, 2030):
        rows = make_synthetic(synthetic_args(seed=seed))
        results = run_trace(rows_to_events(rows))
        add_rows(all_rows, "monte_carlo_seed", f"seed={seed}", results)

    for rewrite in (0.0, 0.01, 0.05, 0.10, 0.25, 0.50):
        for seed in range(2100, 2110):
            rows = make_synthetic(synthetic_args(seed=seed, rewrite_fraction=rewrite))
            results = run_trace(rows_to_events(rows))
            add_rows(all_rows, "rewrite_sweep", f"rewrite={rewrite:.2f}", results)

    fixed_events = rows_to_events(primary_rows)
    for entries in (0, 64, 128, 256, 512, 1024):
        results = run_trace(fixed_events, value_entries=entries)
        add_rows(all_rows, "value_capacity", f"value_entries={entries}", results)

    for cache in (32, 64, 128, 256):
        for seed in range(2200, 2210):
            rows = make_synthetic(synthetic_args(seed=seed))
            results = run_trace(rows_to_events(rows), cache_lines=cache)
            add_rows(all_rows, "cache_sweep", f"cache_lines={cache}", results)

    write_csv(RESULTS / "copper_final_results.csv", all_rows)
    write_markdown(RESULTS / "COPPER_RESULTS.md", primary, adversarial, all_rows)

    print(f"wrote {RESULTS / 'copper_final_results.csv'}")
    print(f"wrote {RESULTS / 'COPPER_RESULTS.md'}")


if __name__ == "__main__":
    main()
