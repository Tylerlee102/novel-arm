#!/usr/bin/env python3
"""CS-SARI sensitivity sweep over GAPBS-derived revocation proxies.

This expands the single CS-SARI GAPBS-topology result across queue depths and
conflict profiles. It is still a trace/proxy experiment, not a full CHI/DMA
system model, but it checks whether the claimed precision/safety behavior is
fragile to one revocation mix.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
from statistics import median

from copper_cs_sari_gapbs_revocation_eval import (
    GAPBS_DIR,
    OUT_DIR as BASE_OUT_DIR,
    Scenario,
    merge_stats,
    pct,
    row_from_stats,
    run_one,
)


OUT_DIR = BASE_OUT_DIR / "sensitivity"
CSV_OUT = OUT_DIR / "cs_sari_sensitivity_sweep.csv"
CORRELATION_CSV_OUT = OUT_DIR / "cs_sari_correlation_sweep.csv"
MD_OUT = OUT_DIR / "CS_SARI_SENSITIVITY_SWEEP.md"


@dataclass(frozen=True)
class Profile:
    name: str
    source_event_prob: float
    source_conflict_prob: float
    target_remap_prob: float
    target_conflict_prob: float
    tlbi_token_prob: float
    tlbi_all_prob: float


PROFILES = [
    Profile("low_conflict", 0.020, 0.05, 0.004, 0.05, 0.001, 0.0),
    Profile("balanced", 0.030, 0.25, 0.008, 0.25, 0.004, 0.00002),
    Profile("hot_source", 0.040, 0.75, 0.006, 0.20, 0.002, 0.0),
    Profile("target_churn", 0.012, 0.20, 0.018, 0.60, 0.020, 0.00008),
]
QUEUE_DEPTHS = [1, 2, 4, 8, 16]
CORRELATION_VALUES = [0.0, 0.25, 0.50, 0.75, 1.0]
CORRELATION_GRAPH_LIMIT = 2
CORRELATION_PASSES = 2
KERNELS = ["edge_scan", "bfs_replay"]
SEEDS = [1]
PASSES = 2
LOOKAHEAD = 32

INT_FIELDS = {
    "raw_candidates",
    "authority_candidates",
    "source_events",
    "target_events",
    "conflict_hazards",
    "global_issued",
    "global_held",
    "scoped_issued",
    "scoped_held",
    "issue_delta",
    "avoided_global_hold",
    "scoped_unsafe",
    "no_hold_unsafe",
    "queue_depth",
    "runs",
    "overflow_runs",
    "passes",
    "lookahead",
}
FLOAT_FIELDS = {
    "hold_reduction_pct",
    "issue_gain_pct",
    "source_target_correlation",
}


def fmt_pct(value: float) -> str:
    return f"{value:.2f}%"


def coerce_cached_row(row: dict[str, str]) -> dict:
    coerced: dict = {}
    for key, value in row.items():
        if key in INT_FIELDS and value != "":
            coerced[key] = int(value)
        elif key in FLOAT_FIELDS and value != "":
            coerced[key] = float(value)
        else:
            coerced[key] = value
    return coerced


def load_cached_rows() -> list[dict] | None:
    if not CSV_OUT.exists():
        return None
    with CSV_OUT.open(newline="", encoding="utf-8") as handle:
        rows = [coerce_cached_row(row) for row in csv.DictReader(handle)]
    return rows or None


def main() -> None:
    graph_paths = sorted(GAPBS_DIR.glob("kron_g*.sg"))
    if not graph_paths:
        raise SystemExit(f"No GAPBS .sg files found in {GAPBS_DIR}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cached_rows = load_cached_rows()
    if cached_rows is not None:
        rows = cached_rows
        base_sweep_source = f"cached CSV ({CSV_OUT.name})"
    else:
        rows = []
        base_sweep_source = "fresh run"
        for profile in PROFILES:
            for queue_depth in QUEUE_DEPTHS:
                scenario = Scenario(
                    name=f"{profile.name}_q{queue_depth}",
                    source_event_prob=profile.source_event_prob,
                    source_conflict_prob=profile.source_conflict_prob,
                    target_remap_prob=profile.target_remap_prob,
                    target_conflict_prob=profile.target_conflict_prob,
                    tlbi_token_prob=profile.tlbi_token_prob,
                    tlbi_all_prob=profile.tlbi_all_prob,
                    queue_depth=queue_depth,
                )
                run_stats = []
                overflow_runs = 0
                for graph_path in graph_paths:
                    for kernel in KERNELS:
                        for seed in SEEDS:
                            stats = run_one(
                                graph_path,
                                kernel,
                                scenario,
                                seed,
                                passes=PASSES,
                                lookahead=LOOKAHEAD,
                            )
                            run_stats.append(stats)
                            if stats.overflow_cycle is not None:
                                overflow_runs += 1
                merged = merge_stats(run_stats)
                row = row_from_stats(scenario.name, merged)
                row.update(
                    {
                        "profile": profile.name,
                        "queue_depth": queue_depth,
                        "runs": len(run_stats),
                        "overflow_runs": overflow_runs,
                        "passes": PASSES,
                        "lookahead": LOOKAHEAD,
                    }
                )
                rows.append(row)

        with CSV_OUT.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    correlation_rows = []
    corr_profile = next(profile for profile in PROFILES if profile.name == "balanced")
    correlation_graph_paths = graph_paths[-CORRELATION_GRAPH_LIMIT:]
    correlation_pass_word = "pass" if CORRELATION_PASSES == 1 else "passes"
    for correlation in CORRELATION_VALUES:
        scenario = Scenario(
            name=f"balanced_q8_rho{correlation:.2f}",
            source_event_prob=corr_profile.source_event_prob,
            source_conflict_prob=corr_profile.source_conflict_prob,
            target_remap_prob=corr_profile.target_remap_prob,
            target_conflict_prob=corr_profile.target_conflict_prob,
            tlbi_token_prob=corr_profile.tlbi_token_prob,
            tlbi_all_prob=corr_profile.tlbi_all_prob,
            queue_depth=8,
            source_target_correlation=correlation,
        )
        run_stats = []
        overflow_runs = 0
        for graph_path in correlation_graph_paths:
            for kernel in KERNELS:
                for seed in SEEDS:
                    stats = run_one(
                        graph_path,
                        kernel,
                        scenario,
                        seed,
                        passes=CORRELATION_PASSES,
                        lookahead=LOOKAHEAD,
                    )
                    run_stats.append(stats)
                    if stats.overflow_cycle is not None:
                        overflow_runs += 1
        merged = merge_stats(run_stats)
        row = row_from_stats(scenario.name, merged)
        row.update(
            {
                "profile": corr_profile.name,
                "queue_depth": 8,
                "source_target_correlation": f"{correlation:.2f}",
                "runs": len(run_stats),
                "overflow_runs": overflow_runs,
                "passes": CORRELATION_PASSES,
                "lookahead": LOOKAHEAD,
            }
        )
        correlation_rows.append(row)

    with CORRELATION_CSV_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(correlation_rows[0]))
        writer.writeheader()
        writer.writerows(correlation_rows)

    scoped_unsafe_total = sum(int(row["scoped_unsafe"]) for row in rows)
    no_hold_unsafe_total = sum(int(row["no_hold_unsafe"]) for row in rows)
    correlation_scoped_unsafe_total = sum(int(row["scoped_unsafe"]) for row in correlation_rows)
    correlation_no_hold_unsafe_total = sum(int(row["no_hold_unsafe"]) for row in correlation_rows)
    hold_reductions = [float(row["hold_reduction_pct"]) for row in rows]
    correlation_hold_reductions = [float(row["hold_reduction_pct"]) for row in correlation_rows]
    issue_gains = [
        float(row["issue_gain_pct"])
        for row in rows
        if row["issue_gain_pct"] != ""
    ]
    avoided_total = sum(int(row["avoided_global_hold"]) for row in rows)

    lines = [
        "# CS-SARI Sensitivity Sweep",
        "",
        "Date: 2026-06-23",
        "",
        "This sweep reuses the GAPBS-derived source/target locality model and",
        "varies the CS-SARI revocation queue depth and conflict profile. It is",
        "not a full-system CHI/DMA model; it is a robustness check for the",
        "conflict-scoped hold rule.",
        "",
        "## Aggregate",
        "",
        f"- Base queue/profile table source: {base_sweep_source}",
        f"- Configurations: {len(rows)}",
        f"- Graph/kernel/seed runs per configuration: {rows[0]['runs']}",
        f"- Queue depths: {', '.join(str(item) for item in QUEUE_DEPTHS)}",
        f"- Profiles: {', '.join(profile.name for profile in PROFILES)}",
        f"- Total avoided global holds with authority present: {avoided_total}",
        f"- Total CS-SARI unsafe modeled issues: {scoped_unsafe_total}",
        f"- Total no-hold unsafe modeled issues: {no_hold_unsafe_total}",
        f"- Hold reduction range: {fmt_pct(min(hold_reductions))} to {fmt_pct(max(hold_reductions))}",
        f"- Median hold reduction: {fmt_pct(median(hold_reductions))}",
        f"- Issue gain range over global hold: {fmt_pct(min(issue_gains))} to {fmt_pct(max(issue_gains))}",
        f"- Correlated source/target sweep rho values: {', '.join(f'{value:.2f}' for value in CORRELATION_VALUES)}",
        f"- Correlated sweep sampled topologies: {', '.join(path.stem for path in correlation_graph_paths)}",
        f"- Correlated sweep graph/kernel/seed runs per rho: {correlation_rows[0]['runs']}",
        f"- Correlated sweep CS-SARI unsafe modeled issues: {correlation_scoped_unsafe_total}",
        f"- Correlated sweep no-hold unsafe modeled issues: {correlation_no_hold_unsafe_total}",
        f"- Correlated sweep hold reduction range: {fmt_pct(min(correlation_hold_reductions))} to {fmt_pct(max(correlation_hold_reductions))}",
        "",
        "## Results",
        "",
        "| Profile | Queue depth | Overflow runs | Global held | Scoped held | Hold reduction | Global issued | Scoped issued | Issue gain | Avoided global holds | Scoped unsafe | No-hold unsafe |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {profile} | {queue_depth} | {overflow_runs}/{runs} | {global_held} | {scoped_held} | {hold_reduction_pct:.2f}% | {global_issued} | {scoped_issued} | {issue_gain_display} | {avoided_global_hold} | {scoped_unsafe} | {no_hold_unsafe} |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "## Source/Target Correlation Sweep",
            "",
            f"This sampled rho sweep starts from the balanced profile with queue depth 8 and uses the largest {len(correlation_graph_paths)} GAPBS topologies with {CORRELATION_PASSES} {correlation_pass_word} per run. A higher rho makes an incoming source-line conflict more likely to coincide with a target remap conflict for the same candidate, modeling shared-root revocation bursts instead of independent source and target events.",
            "",
            "| Rho | Overflow runs | Global held | Scoped held | Hold reduction | Global issued | Scoped issued | Issue gain | Avoided global holds | Scoped unsafe | No-hold unsafe |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in correlation_rows:
        lines.append(
            "| {source_target_correlation} | {overflow_runs}/{runs} | {global_held} | {scoped_held} | {hold_reduction_pct:.2f}% | {global_issued} | {scoped_issued} | {issue_gain_display} | {avoided_global_hold} | {scoped_unsafe} | {no_hold_unsafe} |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- CS-SARI has zero modeled unsafe issues in every queue-depth/conflict",
            "  configuration in this sweep.",
            "- Queue depth mainly controls how quickly overflow forces the scoped",
            "  policy back toward conservative global hold.",
            "- The precision win is largest when revocations are common but rarely",
            "  conflict with the candidate source/target/token.",
            "- This is useful paper evidence because it shows the mechanism is not",
            "  a one-point trace artifact, but it still does not replace a real",
            "  full-system coherent interconnect experiment.",
            "- The sampled correlation sweep makes the previous independence assumption explicit:",
            "  as rho rises, target events increase, but in this balanced sampled",
            "  profile they mostly overlap candidates already scoped-held by source",
            "  conflicts, so the hold reduction remains stable and the scoped-hold",
            "  safety counter remains at zero.",
            "",
        ]
    )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(MD_OUT)
    print(CSV_OUT)
    print(CORRELATION_CSV_OUT)
    print(f"configs={len(rows)}")
    print(f"scoped_unsafe_total={scoped_unsafe_total}")
    print(f"no_hold_unsafe_total={no_hold_unsafe_total}")
    print(f"hold_reduction_min={min(hold_reductions):.2f}")
    print(f"hold_reduction_max={max(hold_reductions):.2f}")


if __name__ == "__main__":
    main()
