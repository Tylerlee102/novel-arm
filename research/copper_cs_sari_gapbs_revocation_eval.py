#!/usr/bin/env python3
"""GAPBS-topology CS-SARI revocation evaluation.

This is a workload-derived revocation proxy, not a full-system CHI/DMA model.
It reuses the GAPBS serialized graph topologies already generated in the repo.
Graph edge slots act as COPPER source words and neighbor node-property lines act
as CTLW target witnesses. The evaluator injects source-line and target-witness
revocations with controlled conflict rates and compares global SARI hold with
conflict-scoped SARI hold.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import csv
import random

from gapbs_copper_trace_eval import (
    BASE,
    NODE_STRIDE,
    SOURCE_SLOTS_PER_LINE,
    bfs_replay_trace,
    edge_scan_trace,
    make_workload,
    read_gapbs_sg,
)


ROOT = Path(__file__).resolve().parents[1]
GAPBS_DIR = ROOT / "research" / "results" / "gapbs_copper_trace"
OUT_DIR = ROOT / "research" / "results" / "cs_sari_gapbs_revocation"
CSV_OUT = OUT_DIR / "cs_sari_gapbs_revocation_results.csv"
MD_OUT = OUT_DIR / "CS_SARI_GAPBS_REVOCATION_SUMMARY.md"


@dataclass(frozen=True)
class Scenario:
    name: str
    source_event_prob: float
    source_conflict_prob: float
    target_remap_prob: float
    target_conflict_prob: float
    tlbi_token_prob: float
    tlbi_all_prob: float
    queue_depth: int = 8
    source_target_correlation: float = 0.0


@dataclass
class PolicyStats:
    issued: int = 0
    held: int = 0
    blocked_no_authority: int = 0
    unsafe_issued: int = 0


@dataclass
class RunStats:
    no_hold: PolicyStats = field(default_factory=PolicyStats)
    global_hold: PolicyStats = field(default_factory=PolicyStats)
    scoped_hold: PolicyStats = field(default_factory=PolicyStats)
    raw_candidates: int = 0
    authority_candidates: int = 0
    source_events: int = 0
    target_events: int = 0
    conflict_hazards: int = 0
    avoided_global_hold: int = 0
    avoided_global_allow: int = 0
    overflow_cycle: int | None = None


def pct(part: int, whole: int) -> float:
    return 0.0 if whole == 0 else 100.0 * part / whole


def source_line(edge_index: int) -> int:
    return edge_index // SOURCE_SLOTS_PER_LINE


def source_bit(edge_index: int) -> int:
    return edge_index % SOURCE_SLOTS_PER_LINE


def target_line(addr: int) -> int:
    return (addr - BASE) // NODE_STRIDE


def line_has_proof(line_masks: dict[int, int], edge_index: int) -> bool:
    return bool(line_masks.get(source_line(edge_index), 0) & (1 << source_bit(edge_index)))


def remember_proof(line_masks: dict[int, int], edge_index: int) -> None:
    line = source_line(edge_index)
    line_masks[line] = line_masks.get(line, 0) | (1 << source_bit(edge_index))


def choose_source_event(
    rng: random.Random,
    scenario: Scenario,
    pf_edge: int,
    edge_count: int,
) -> list[int]:
    events: list[int] = []
    if rng.random() < scenario.source_event_prob:
        if rng.random() < scenario.source_conflict_prob:
            events.append(source_line(pf_edge))
        else:
            events.append(source_line(rng.randrange(edge_count)))
    return events


def choose_target_events(
    rng: random.Random,
    scenario: Scenario,
    pf_target: int,
    node_count: int,
    token: int,
    force_conflict: bool = False,
) -> tuple[list[tuple[int, int]], list[int], bool]:
    remaps: list[tuple[int, int]] = []
    tlbi_tokens: list[int] = []
    tlbi_all = False
    if force_conflict or rng.random() < scenario.target_remap_prob:
        if force_conflict or rng.random() < scenario.target_conflict_prob:
            remaps.append((pf_target, token))
        else:
            remaps.append((rng.randrange(node_count), rng.randrange(16)))
    if rng.random() < scenario.tlbi_token_prob:
        if rng.random() < scenario.target_conflict_prob:
            tlbi_tokens.append(token)
        else:
            tlbi_tokens.append((token + rng.randrange(1, 16)) & 0xF)
    if rng.random() < scenario.tlbi_all_prob:
        tlbi_all = True
    return remaps, tlbi_tokens, tlbi_all


def apply_policy(stats: PolicyStats, authorized: bool, hold: bool, hazard: bool) -> None:
    if not authorized:
        stats.blocked_no_authority += 1
    elif hold:
        stats.held += 1
    else:
        stats.issued += 1
        if hazard:
            stats.unsafe_issued += 1


def run_one(
    graph_path: Path,
    kernel: str,
    scenario: Scenario,
    seed: int,
    passes: int = 3,
    lookahead: int = 32,
) -> RunStats:
    graph = read_gapbs_sg(graph_path)
    workload = make_workload(graph, seed)
    trace = edge_scan_trace(graph) if kernel == "edge_scan" else bfs_replay_trace(graph)
    rng = random.Random(200_000 + seed * 97 + graph.edges + len(kernel) * 17)
    token = seed & 0xF

    line_masks: dict[int, int] = {}
    target_witnesses: set[tuple[int, int]] = set()
    queue: list[int] = []
    overflow = False
    stats = RunStats()
    cycle = 0

    for pass_index in range(passes):
        for pos, edge_index in enumerate(trace):
            pf_pos = pos + lookahead
            if pf_pos >= len(trace):
                remember_proof(line_masks, edge_index)
                target_witnesses.add((target_line(workload.targets[edge_index]), token))
                cycle += 1
                continue

            pf_edge = trace[pf_pos]
            pf_source_line = source_line(pf_edge)
            pf_target_line = target_line(workload.targets[pf_edge])
            stats.raw_candidates += 1

            source_events = choose_source_event(rng, scenario, pf_edge, graph.edges)
            incoming_source_conflict = pf_source_line in source_events
            remaps, tlbi_tokens, tlbi_all = choose_target_events(
                rng,
                scenario,
                pf_target_line,
                graph.nodes,
                token,
                force_conflict=(
                    incoming_source_conflict
                    and rng.random() < scenario.source_target_correlation
                ),
            )

            if pass_index == 1 and edge_index in workload.mutate_slots:
                source_events.append(source_line(edge_index))

            stats.source_events += len(source_events)
            stats.target_events += len(remaps) + len(tlbi_tokens) + int(tlbi_all)

            queued_source_conflict = pf_source_line in queue
            remap_conflict = any(line == pf_target_line and event_token == token for line, event_token in remaps)
            tlbi_token_conflict = token in tlbi_tokens
            target_conflict = remap_conflict or tlbi_token_conflict or tlbi_all
            hazard = overflow or queued_source_conflict or incoming_source_conflict or target_conflict
            if hazard:
                stats.conflict_hazards += 1

            authorized = line_has_proof(line_masks, pf_edge) and ((pf_target_line, token) in target_witnesses)
            if authorized:
                stats.authority_candidates += 1

            global_hold = overflow or bool(queue) or bool(source_events) or bool(remaps) or bool(tlbi_tokens) or tlbi_all
            scoped_hold = overflow or queued_source_conflict or incoming_source_conflict or target_conflict

            apply_policy(stats.no_hold, authorized, False, hazard)
            apply_policy(stats.global_hold, authorized, global_hold, hazard)
            apply_policy(stats.scoped_hold, authorized, scoped_hold, hazard)

            if authorized and global_hold and not scoped_hold:
                stats.avoided_global_hold += 1
                if not hazard:
                    stats.avoided_global_allow += 1

            if queue:
                line_masks.pop(queue.pop(0), None)

            for line in source_events:
                if len(queue) < scenario.queue_depth:
                    queue.append(line)
                else:
                    overflow = True
                    if stats.overflow_cycle is None:
                        stats.overflow_cycle = cycle

            for line, event_token in remaps:
                target_witnesses.discard((line, event_token))
            for event_token in tlbi_tokens:
                target_witnesses = {
                    item for item in target_witnesses if item[1] != event_token
                }
            if tlbi_all:
                target_witnesses.clear()

            remember_proof(line_masks, edge_index)
            target_witnesses.add((target_line(workload.targets[edge_index]), token))
            cycle += 1

    return stats


def merge_stats(items: list[RunStats]) -> RunStats:
    out = RunStats()
    for stats in items:
        for name in ("no_hold", "global_hold", "scoped_hold"):
            dst = getattr(out, name)
            src = getattr(stats, name)
            dst.issued += src.issued
            dst.held += src.held
            dst.blocked_no_authority += src.blocked_no_authority
            dst.unsafe_issued += src.unsafe_issued
        out.raw_candidates += stats.raw_candidates
        out.authority_candidates += stats.authority_candidates
        out.source_events += stats.source_events
        out.target_events += stats.target_events
        out.conflict_hazards += stats.conflict_hazards
        out.avoided_global_hold += stats.avoided_global_hold
        out.avoided_global_allow += stats.avoided_global_allow
        if stats.overflow_cycle is not None:
            out.overflow_cycle = stats.overflow_cycle if out.overflow_cycle is None else min(out.overflow_cycle, stats.overflow_cycle)
    return out


def row_from_stats(scenario: str, stats: RunStats) -> dict[str, str | int | float]:
    global_issued = stats.global_hold.issued
    scoped_issued = stats.scoped_hold.issued
    issue_delta = scoped_issued - global_issued
    issue_gain = "" if global_issued == 0 else pct(issue_delta, global_issued)
    return {
        "scenario": scenario,
        "raw_candidates": stats.raw_candidates,
        "authority_candidates": stats.authority_candidates,
        "source_events": stats.source_events,
        "target_events": stats.target_events,
        "conflict_hazards": stats.conflict_hazards,
        "global_issued": global_issued,
        "global_held": stats.global_hold.held,
        "scoped_issued": scoped_issued,
        "scoped_held": stats.scoped_hold.held,
        "hold_reduction_pct": pct(stats.global_hold.held - stats.scoped_hold.held, stats.global_hold.held),
        "issue_delta": issue_delta,
        "issue_gain_pct": issue_gain,
        "issue_gain_display": f"+{issue_delta} from zero" if issue_gain == "" else f"{issue_gain:.2f}%",
        "avoided_global_hold": stats.avoided_global_hold,
        "scoped_unsafe": stats.scoped_hold.unsafe_issued,
        "no_hold_unsafe": stats.no_hold.unsafe_issued,
        "overflow_cycle": "" if stats.overflow_cycle is None else stats.overflow_cycle,
    }


def main() -> None:
    scenarios = [
        Scenario("gapbs_low_conflict", 0.025, 0.05, 0.006, 0.05, 0.001, 0.0),
        Scenario("gapbs_hot_revocation", 0.035, 0.55, 0.008, 0.45, 0.002, 0.0),
        Scenario("gapbs_tlbi_churn", 0.008, 0.20, 0.012, 0.25, 0.018, 0.00005),
    ]
    graph_paths = sorted(GAPBS_DIR.glob("kron_g*.sg"))
    if not graph_paths:
        raise SystemExit(f"No GAPBS .sg files found in {GAPBS_DIR}")
    kernels = ["edge_scan", "bfs_replay"]
    seeds = [1, 3]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    detail_rows = []
    for scenario in scenarios:
        scenario_stats = []
        for graph_path in graph_paths:
            for kernel in kernels:
                for seed in seeds:
                    stats = run_one(graph_path, kernel, scenario, seed)
                    scenario_stats.append(stats)
                    detail = row_from_stats(f"{scenario.name}:{graph_path.stem}:{kernel}:s{seed}", stats)
                    detail_rows.append(detail)
        merged = merge_stats(scenario_stats)
        rows.append(row_from_stats(scenario.name, merged))

    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    detail_csv = OUT_DIR / "cs_sari_gapbs_revocation_detail.csv"
    with detail_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(detail_rows[0]))
        writer.writeheader()
        writer.writerows(detail_rows)

    lines = [
        "# CS-SARI GAPBS-Topology Revocation Evaluation",
        "",
        "Date: 2026-06-12",
        "",
        "This is a workload-derived revocation proxy over the repository's GAPBS",
        "serialized graph topologies. It is not a full-system AMBA CHI/DMA run.",
        "Edge slots provide source-proof locality and graph neighbor lines provide",
        "target-witness locality; DMA/remap/TLBI-like revocations are injected with",
        "controlled conflict rates.",
        "",
        "| Scenario | Raw candidates | Authority candidates | Source events | Target events | Conflict hazards | Global held | Scoped held | Hold reduction | Global issued | Scoped issued | Issue gain | Avoided global holds | Scoped unsafe | No-hold unsafe |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {scenario} | {raw_candidates} | {authority_candidates} | {source_events} | {target_events} | {conflict_hazards} | {global_held} | {scoped_held} | {hold_reduction_pct:.2f}% | {global_issued} | {scoped_issued} | {issue_gain_display} | {avoided_global_hold} | {scoped_unsafe} | {no_hold_unsafe} |".format(
                **row
            )
        )

    total_global_held = sum(int(row["global_held"]) for row in rows)
    total_scoped_held = sum(int(row["scoped_held"]) for row in rows)
    total_global_issued = sum(int(row["global_issued"]) for row in rows)
    total_scoped_issued = sum(int(row["scoped_issued"]) for row in rows)
    total_scoped_unsafe = sum(int(row["scoped_unsafe"]) for row in rows)
    total_no_hold_unsafe = sum(int(row["no_hold_unsafe"]) for row in rows)
    total_avoided = sum(int(row["avoided_global_hold"]) for row in rows)
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
            "Interpretation: the GAPBS-topology proxy keeps the same safety pattern",
            "as the generic SARI trace: CS-SARI has zero modeled unsafe issues while",
            "recovering DMP issue opportunities lost to global hold. The remaining",
            "research gap is full-system coherent DMA/TLBI event capture.",
            "",
        ]
    )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(MD_OUT)
    print(CSV_OUT)
    print(detail_csv)


if __name__ == "__main__":
    main()
