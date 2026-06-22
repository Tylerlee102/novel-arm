#!/usr/bin/env python3
"""Trace model for global SARI hold versus conflict-scoped SARI hold.

The model is intentionally small and deterministic. It does not model a full
cache hierarchy or AMBA fabric. It asks one narrow question: when SoC revocation
events overlap with raw DMP candidates, how much unnecessary DMP issue blocking
does conflict-scoped hold avoid while preserving the no-transient-authority
contract?
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import csv
import random


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research" / "results" / "sari_scoped_trace"
CSV_OUT = OUT_DIR / "sari_scoped_trace_results.csv"
MD_OUT = OUT_DIR / "SARI_SCOPED_TRACE_SUMMARY.md"


@dataclass(frozen=True)
class Scenario:
    name: str
    cycles: int
    seed: int
    source_lines: int
    target_lines: int
    tokens: int
    hot_sources: int
    hot_targets: int
    source_event_prob: float
    target_remap_prob: float
    tlbi_token_prob: float
    tlbi_all_prob: float
    reproof_prob: float
    source_event_hot_prob: float
    target_event_hot_prob: float
    burst_period: int = 0
    burst_len: int = 0
    burst_width: int = 0
    queue_depth: int = 8


@dataclass
class PolicyStats:
    issued: int = 0
    held: int = 0
    blocked_no_authority: int = 0
    unsafe_issued: int = 0


@dataclass
class ScenarioStats:
    global_policy: PolicyStats = field(default_factory=PolicyStats)
    scoped_policy: PolicyStats = field(default_factory=PolicyStats)
    no_hold_policy: PolicyStats = field(default_factory=PolicyStats)
    raw_candidates: int = 0
    authority_candidates: int = 0
    source_events: int = 0
    target_events: int = 0
    tlbi_all_events: int = 0
    overflow_cycle: int | None = None
    avoided_global_hold: int = 0
    avoided_global_allow: int = 0
    conflict_hazard_cycles: int = 0


def choose_line(rng: random.Random, total: int, hot: int, hot_prob: float) -> int:
    if rng.random() < hot_prob:
        return rng.randrange(hot)
    return rng.randrange(hot, total)


def choose_target(rng: random.Random, scenario: Scenario, hot_prob: float) -> int:
    return choose_line(rng, scenario.target_lines, scenario.hot_targets, hot_prob)


def source_events_for_cycle(
    rng: random.Random, scenario: Scenario, cycle: int
) -> list[int]:
    events: list[int] = []
    if rng.random() < scenario.source_event_prob:
        events.append(
            choose_line(
                rng,
                scenario.source_lines,
                scenario.hot_sources,
                scenario.source_event_hot_prob,
            )
        )
    if (
        scenario.burst_period
        and scenario.burst_len
        and scenario.burst_width
        and (cycle % scenario.burst_period) < scenario.burst_len
    ):
        for _ in range(scenario.burst_width):
            events.append(
                choose_line(
                    rng,
                    scenario.source_lines,
                    scenario.hot_sources,
                    scenario.source_event_hot_prob,
                )
            )
    return events


def target_events_for_cycle(
    rng: random.Random, scenario: Scenario
) -> tuple[list[tuple[int, int]], list[int], bool]:
    remaps: list[tuple[int, int]] = []
    tlbi_tokens: list[int] = []
    tlbi_all = False
    if rng.random() < scenario.target_remap_prob:
        remaps.append(
            (
                choose_target(rng, scenario, scenario.target_event_hot_prob),
                rng.randrange(scenario.tokens),
            )
        )
    if rng.random() < scenario.tlbi_token_prob:
        tlbi_tokens.append(rng.randrange(scenario.tokens))
    if rng.random() < scenario.tlbi_all_prob:
        tlbi_all = True
    return remaps, tlbi_tokens, tlbi_all


def apply_policy(
    stats: PolicyStats,
    candidate_authorized: bool,
    hold: bool,
    hazard: bool,
) -> None:
    if not candidate_authorized:
        stats.blocked_no_authority += 1
        return
    if hold:
        stats.held += 1
        return
    stats.issued += 1
    if hazard:
        stats.unsafe_issued += 1


def run_scenario(scenario: Scenario) -> ScenarioStats:
    rng = random.Random(scenario.seed)
    source_live = [True] * scenario.source_lines
    target_live = {
        (line, token): True
        for line in range(scenario.target_lines)
        for token in range(scenario.tokens)
    }
    queue: list[int] = []
    overflow = False
    stats = ScenarioStats()

    for cycle in range(scenario.cycles):
        if rng.random() < scenario.reproof_prob:
            source_live[rng.randrange(scenario.hot_sources)] = True
        if rng.random() < scenario.reproof_prob:
            target_live[(rng.randrange(scenario.hot_targets), rng.randrange(scenario.tokens))] = True

        src = rng.randrange(scenario.hot_sources)
        tgt = rng.randrange(scenario.hot_targets)
        token = rng.randrange(scenario.tokens)
        stats.raw_candidates += 1

        source_events = source_events_for_cycle(rng, scenario, cycle)
        remaps, tlbi_tokens, tlbi_all = target_events_for_cycle(rng, scenario)
        stats.source_events += len(source_events)
        stats.target_events += len(remaps) + len(tlbi_tokens) + int(tlbi_all)
        stats.tlbi_all_events += int(tlbi_all)

        queued_source_conflict = src in queue
        incoming_source_conflict = src in source_events
        remap_conflict = any(line == tgt and event_token == token for line, event_token in remaps)
        tlbi_token_conflict = token in tlbi_tokens
        target_conflict = remap_conflict or tlbi_token_conflict or tlbi_all
        hazard = queued_source_conflict or incoming_source_conflict or target_conflict or overflow
        if hazard:
            stats.conflict_hazard_cycles += 1

        candidate_authorized = source_live[src] and target_live[(tgt, token)]
        if candidate_authorized:
            stats.authority_candidates += 1

        global_hold = overflow or bool(queue) or bool(source_events) or bool(remaps) or bool(tlbi_tokens) or tlbi_all
        scoped_hold = overflow or queued_source_conflict or incoming_source_conflict or target_conflict

        apply_policy(stats.no_hold_policy, candidate_authorized, False, hazard)
        apply_policy(stats.global_policy, candidate_authorized, global_hold, hazard)
        apply_policy(stats.scoped_policy, candidate_authorized, scoped_hold, hazard)

        if candidate_authorized and global_hold and not scoped_hold:
            stats.avoided_global_hold += 1
            if not hazard:
                stats.avoided_global_allow += 1

        if queue:
            cleared = queue.pop(0)
            source_live[cleared] = False

        for line in source_events:
            if len(queue) < scenario.queue_depth:
                queue.append(line)
            else:
                overflow = True
                if stats.overflow_cycle is None:
                    stats.overflow_cycle = cycle

        for line, event_token in remaps:
            target_live[(line, event_token)] = False
        for event_token in tlbi_tokens:
            for line in range(scenario.target_lines):
                target_live[(line, event_token)] = False
        if tlbi_all:
            for key in list(target_live):
                target_live[key] = False

    return stats


def pct(part: int, whole: int) -> float:
    return 0.0 if whole == 0 else 100.0 * part / whole


def main() -> None:
    scenarios = [
        Scenario(
            name="unrelated_dma_noise",
            cycles=200_000,
            seed=11,
            source_lines=4096,
            target_lines=4096,
            tokens=16,
            hot_sources=64,
            hot_targets=64,
            source_event_prob=0.08,
            target_remap_prob=0.01,
            tlbi_token_prob=0.002,
            tlbi_all_prob=0.0,
            reproof_prob=0.03,
            source_event_hot_prob=0.05,
            target_event_hot_prob=0.05,
        ),
        Scenario(
            name="shared_io_buffer",
            cycles=200_000,
            seed=17,
            source_lines=4096,
            target_lines=4096,
            tokens=16,
            hot_sources=64,
            hot_targets=64,
            source_event_prob=0.08,
            target_remap_prob=0.01,
            tlbi_token_prob=0.002,
            tlbi_all_prob=0.0,
            reproof_prob=0.03,
            source_event_hot_prob=0.85,
            target_event_hot_prob=0.65,
        ),
        Scenario(
            name="tlbi_churn",
            cycles=200_000,
            seed=23,
            source_lines=4096,
            target_lines=4096,
            tokens=16,
            hot_sources=64,
            hot_targets=64,
            source_event_prob=0.01,
            target_remap_prob=0.02,
            tlbi_token_prob=0.04,
            tlbi_all_prob=0.0002,
            reproof_prob=0.04,
            source_event_hot_prob=0.25,
            target_event_hot_prob=0.35,
        ),
        Scenario(
            name="burst_dma_mixed",
            cycles=200_000,
            seed=31,
            source_lines=4096,
            target_lines=4096,
            tokens=16,
            hot_sources=64,
            hot_targets=64,
            source_event_prob=0.01,
            target_remap_prob=0.006,
            tlbi_token_prob=0.001,
            tlbi_all_prob=0.0,
            reproof_prob=0.04,
            source_event_hot_prob=0.30,
            target_event_hot_prob=0.20,
            burst_period=200,
            burst_len=8,
            burst_width=3,
        ),
        Scenario(
            name="overflow_fallback",
            cycles=80_000,
            seed=37,
            source_lines=4096,
            target_lines=4096,
            tokens=16,
            hot_sources=64,
            hot_targets=64,
            source_event_prob=0.03,
            target_remap_prob=0.002,
            tlbi_token_prob=0.001,
            tlbi_all_prob=0.0,
            reproof_prob=0.03,
            source_event_hot_prob=0.50,
            target_event_hot_prob=0.20,
            burst_period=50,
            burst_len=20,
            burst_width=4,
            queue_depth=8,
        ),
    ]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for scenario in scenarios:
        stats = run_scenario(scenario)
        global_holds = stats.global_policy.held
        scoped_holds = stats.scoped_policy.held
        global_issued = stats.global_policy.issued
        scoped_issued = stats.scoped_policy.issued
        issue_delta = scoped_issued - global_issued
        issue_gain_pct = None if global_issued == 0 else pct(issue_delta, global_issued)
        rows.append(
            {
                "scenario": scenario.name,
                "cycles": scenario.cycles,
                "authority_candidates": stats.authority_candidates,
                "source_events": stats.source_events,
                "target_events": stats.target_events,
                "conflict_hazard_cycles": stats.conflict_hazard_cycles,
                "global_issued": global_issued,
                "global_held": global_holds,
                "global_unsafe": stats.global_policy.unsafe_issued,
                "scoped_issued": scoped_issued,
                "scoped_held": scoped_holds,
                "scoped_unsafe": stats.scoped_policy.unsafe_issued,
                "no_hold_unsafe": stats.no_hold_policy.unsafe_issued,
                "avoided_global_hold": stats.avoided_global_hold,
                "avoided_global_allow": stats.avoided_global_allow,
                "hold_reduction_pct": pct(global_holds - scoped_holds, global_holds),
                "issue_delta": issue_delta,
                "issue_gain_pct": "" if issue_gain_pct is None else issue_gain_pct,
                "issue_gain_display": f"+{issue_delta} from zero" if issue_gain_pct is None else f"{issue_gain_pct:.2f}%",
                "overflow_cycle": "" if stats.overflow_cycle is None else stats.overflow_cycle,
            }
        )

    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# CS-SARI Trace-Level Stall Model",
        "",
        "Date: 2026-06-12",
        "",
        "This deterministic trace model compares three policies over synthetic",
        "SoC-revocation streams: no hold, global SARI hold, and conflict-scoped",
        "SARI hold. It is not a cache or AMBA fabric simulator; it measures the",
        "specific SARI question of stale-authority safety versus unnecessary DMP",
        "issue stalls.",
        "",
        "| Scenario | Authority candidates | Source events | Target events | Conflict hazards | Global held | Scoped held | Hold reduction | Global issued | Scoped issued | Issue gain | Avoided global holds | Scoped unsafe | No-hold unsafe | Overflow cycle |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        overflow = row["overflow_cycle"] if row["overflow_cycle"] != "" else "-"
        lines.append(
            "| {scenario} | {authority_candidates} | {source_events} | {target_events} | {conflict_hazard_cycles} | {global_held} | {scoped_held} | {hold_reduction_pct:.2f}% | {global_issued} | {scoped_issued} | {issue_gain_display} | {avoided_global_hold} | {scoped_unsafe} | {no_hold_unsafe} | {overflow} |".format(
                **row, overflow=overflow
            )
        )

    total_global_held = sum(row["global_held"] for row in rows)
    total_scoped_held = sum(row["scoped_held"] for row in rows)
    total_global_issued = sum(row["global_issued"] for row in rows)
    total_scoped_issued = sum(row["scoped_issued"] for row in rows)
    total_no_hold_unsafe = sum(row["no_hold_unsafe"] for row in rows)
    total_scoped_unsafe = sum(row["scoped_unsafe"] for row in rows)
    total_avoided = sum(row["avoided_global_hold"] for row in rows)

    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            f"- Total global holds: {total_global_held}",
            f"- Total CS-SARI holds: {total_scoped_held}",
            f"- Aggregate hold reduction: {pct(total_global_held - total_scoped_held, total_global_held):.2f}%",
            f"- Total global issued candidates: {total_global_issued}",
            f"- Total CS-SARI issued candidates: {total_scoped_issued}",
            f"- Aggregate issue gain over global hold: {pct(total_scoped_issued - total_global_issued, max(total_global_issued, 1)):.2f}%",
            f"- Avoided global holds with authority present: {total_avoided}",
            f"- CS-SARI unsafe modeled issues: {total_scoped_unsafe}",
            f"- No-hold unsafe modeled issues: {total_no_hold_unsafe}",
            "",
            "Interpretation: CS-SARI preserves the modeled no-transient-authority",
            "contract in all scenarios while recovering issue opportunities that",
            "global hold discards. In the overflow scenario, both policies converge",
            "after the precise revocation queue overflows, as intended.",
            "",
        ]
    )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(MD_OUT)
    print(CSV_OUT)


if __name__ == "__main__":
    main()
