#!/usr/bin/env python3
"""Composition-level bounded checker for COPPER CS-SARI.

The standalone CS-SARI checker proves the scoped revocation hold predicate in
isolation. This model checks the composed issue contract:

    final_issue = CLPD(source) and CTLW(target) and not CS_SARI_hold(candidate)

against a small ground-truth machine. It intentionally includes weakened
variants that remove source clearing, target clearing, or one side of the final
authority gate so the report can distinguish a new safety mechanism from a
pile-up of familiar blocks.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path


SRC_LINES = 3
TGT_LINES = 3
TOKENS = 2
DEPTH = 2
MAX_DEPTH = 7

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "results" / "COPPER_CS_SARI_COMPOSITION_STATE_SPACE.md"


@dataclass(frozen=True)
class State:
    queue: tuple[int, ...] = ()
    overflow: bool = False
    truth_source: tuple[bool, ...] = (False, False, False)
    clpd_source: tuple[bool, ...] = (False, False, False)
    truth_target: tuple[tuple[bool, ...], ...] = (
        (False, False, False),
        (False, False, False),
    )
    ctlw_target: tuple[tuple[bool, ...], ...] = (
        (False, False, False),
        (False, False, False),
    )


@dataclass(frozen=True)
class Event:
    kind: str
    line: int = 0
    target: int = 0
    token: int = 0
    lines: tuple[int, ...] = ()


@dataclass(frozen=True)
class Query:
    valid: bool
    src: int
    tgt: int
    token: int


@dataclass(frozen=True)
class Variant:
    name: str
    check_incoming_source: bool = True
    check_queued_source: bool = True
    check_remap_event: bool = True
    check_tlbi_token: bool = True
    check_tlbi_all: bool = True
    check_overflow: bool = True
    clear_source_on_drain: bool = True
    clear_target_on_remap: bool = True
    clear_target_on_tlbi_token: bool = True
    clear_target_on_tlbi_all: bool = True
    require_source_metadata: bool = True
    require_target_metadata: bool = True
    force_global_hold: bool = False
    expected: str = "safety_pass"


VARIANTS = [
    Variant("COMPOSED_CS_SARI"),
    Variant("BUG_NO_INCOMING_SOURCE_HOLD", check_incoming_source=False, expected="safety_fail"),
    Variant("BUG_NO_QUEUED_SOURCE_HOLD", check_queued_source=False, expected="safety_fail"),
    Variant("BUG_NO_REMAP_HOLD", check_remap_event=False, expected="safety_fail"),
    Variant("BUG_NO_TLBI_TOKEN_HOLD", check_tlbi_token=False, expected="safety_fail"),
    Variant("BUG_NO_TLBI_ALL_HOLD", check_tlbi_all=False, expected="safety_fail"),
    Variant("BUG_NO_OVERFLOW_HOLD", check_overflow=False, expected="safety_fail"),
    Variant("BUG_CLPD_STALE_AFTER_REVOCATION", clear_source_on_drain=False, expected="safety_fail"),
    Variant("BUG_CTLW_STALE_AFTER_REMAP", clear_target_on_remap=False, expected="safety_fail"),
    Variant("BUG_CTLW_STALE_AFTER_TOKEN_TLBI", clear_target_on_tlbi_token=False, expected="safety_fail"),
    Variant("BUG_CTLW_STALE_AFTER_GLOBAL_TLBI", clear_target_on_tlbi_all=False, expected="safety_fail"),
    Variant("BUG_SOURCE_ONLY_AUTHORITY", require_target_metadata=False, expected="safety_fail"),
    Variant("BUG_TARGET_ONLY_AUTHORITY", require_source_metadata=False, expected="safety_fail"),
    Variant("BUG_GLOBAL_HOLD", force_global_hold=True, expected="precision_fail"),
]


EVENTS = [Event("none")]
EVENTS += [Event("commit_source", line=line) for line in range(SRC_LINES)]
EVENTS += [
    Event("record_target", target=target, token=token)
    for target in range(TGT_LINES)
    for token in range(TOKENS)
]
EVENTS += [Event("dma", line=line) for line in range(SRC_LINES)]
EVENTS += [Event("chi", line=line) for line in range(SRC_LINES)]
EVENTS += [Event("io", line=line) for line in range(SRC_LINES)]
EVENTS += [Event("burst", lines=(0, 1, 2))]
EVENTS += [
    Event("remap", target=target, token=token)
    for target in range(TGT_LINES)
    for token in range(TOKENS)
]
EVENTS += [Event("tlbi_token", token=token) for token in range(TOKENS)]
EVENTS += [Event("tlbi_all")]

QUERIES = [Query(False, 0, 0, 0)]
QUERIES += [
    Query(True, src, tgt, token)
    for src in range(SRC_LINES)
    for tgt in range(TGT_LINES)
    for token in range(TOKENS)
]


def source_event_lines(event: Event) -> tuple[int, ...]:
    if event.kind in {"dma", "chi", "io"}:
        return (event.line,)
    if event.kind == "burst":
        return event.lines
    return ()


def is_source_event(event: Event) -> bool:
    return bool(source_event_lines(event))


def metadata_authorized(state: State, query: Query, variant: Variant) -> bool:
    if not query.valid:
        return False
    source_ok = True
    target_ok = True
    if variant.require_source_metadata:
        source_ok = state.clpd_source[query.src]
    if variant.require_target_metadata:
        target_ok = state.ctlw_target[query.token][query.tgt]
    return source_ok and target_ok


def ground_truth_authorized(state: State, query: Query) -> bool:
    return (
        query.valid
        and state.truth_source[query.src]
        and state.truth_target[query.token][query.tgt]
    )


def truth_hazard(state: State, event: Event, query: Query) -> bool:
    if not query.valid:
        return False
    if state.overflow:
        return True
    if query.src in state.queue:
        return True
    if query.src in source_event_lines(event):
        return True
    if event.kind == "remap" and event.target == query.tgt and event.token == query.token:
        return True
    if event.kind == "tlbi_token" and event.token == query.token:
        return True
    if event.kind == "tlbi_all":
        return True
    return False


def global_hold(state: State, event: Event, query: Query) -> bool:
    return query.valid and (
        state.overflow
        or bool(state.queue)
        or is_source_event(event)
        or event.kind in {"remap", "tlbi_token", "tlbi_all"}
    )


def variant_hold(state: State, event: Event, query: Query, variant: Variant) -> bool:
    if not query.valid:
        return False
    if variant.force_global_hold:
        return global_hold(state, event, query)

    hold = False
    if variant.check_overflow:
        hold = hold or state.overflow
    if variant.check_queued_source:
        hold = hold or (query.src in state.queue)
    if variant.check_incoming_source:
        hold = hold or (query.src in source_event_lines(event))
    if event.kind == "remap" and variant.check_remap_event:
        hold = hold or (event.target == query.tgt and event.token == query.token)
    if event.kind == "tlbi_token" and variant.check_tlbi_token:
        hold = hold or (event.token == query.token)
    if event.kind == "tlbi_all" and variant.check_tlbi_all:
        hold = True
    return hold


def issue_allowed(state: State, event: Event, query: Query, variant: Variant) -> bool:
    return metadata_authorized(state, query, variant) and not variant_hold(
        state, event, query, variant
    )


def unsafe_reason(state: State, event: Event, query: Query) -> str | None:
    if not query.valid:
        return None
    if state.overflow:
        return "overflow_fallback"
    if query.src in state.queue:
        return "queued_source_revocation"
    if query.src in source_event_lines(event):
        return "incoming_source_revocation"
    if event.kind == "remap" and event.target == query.tgt and event.token == query.token:
        return "same_cycle_target_remap"
    if event.kind == "tlbi_token" and event.token == query.token:
        return "same_cycle_token_tlbi"
    if event.kind == "tlbi_all":
        return "same_cycle_global_tlbi"
    if not state.truth_source[query.src]:
        return "missing_or_stale_source_truth"
    if not state.truth_target[query.token][query.tgt]:
        return "missing_or_stale_target_truth"
    return None


def set_source(values: tuple[bool, ...], line: int, value: bool) -> tuple[bool, ...]:
    out = list(values)
    out[line] = value
    return tuple(out)


def set_target(
    values: tuple[tuple[bool, ...], ...], token: int, target: int, value: bool
) -> tuple[tuple[bool, ...], ...]:
    out = [list(row) for row in values]
    out[token][target] = value
    return tuple(tuple(row) for row in out)


def clear_token(
    values: tuple[tuple[bool, ...], ...], token: int
) -> tuple[tuple[bool, ...], ...]:
    out = [list(row) for row in values]
    out[token] = [False] * TGT_LINES
    return tuple(tuple(row) for row in out)


def clear_all_targets(values: tuple[tuple[bool, ...], ...]) -> tuple[tuple[bool, ...], ...]:
    return tuple(tuple(False for _ in range(TGT_LINES)) for _ in range(TOKENS))


def transition(state: State, event: Event, variant: Variant) -> State:
    queue = list(state.queue)
    truth_source = state.truth_source
    clpd_source = state.clpd_source
    truth_target = state.truth_target
    ctlw_target = state.ctlw_target
    overflow = state.overflow

    if queue:
        cleared = queue.pop(0)
        if variant.clear_source_on_drain:
            clpd_source = set_source(clpd_source, cleared, False)

    if event.kind == "commit_source":
        truth_source = set_source(truth_source, event.line, True)
        clpd_source = set_source(clpd_source, event.line, True)

    if event.kind == "record_target":
        truth_target = set_target(truth_target, event.token, event.target, True)
        ctlw_target = set_target(ctlw_target, event.token, event.target, True)

    for line in source_event_lines(event):
        truth_source = set_source(truth_source, line, False)
        if len(queue) < DEPTH:
            queue.append(line)
        else:
            overflow = True

    if event.kind == "remap":
        truth_target = set_target(truth_target, event.token, event.target, False)
        if variant.clear_target_on_remap:
            ctlw_target = set_target(ctlw_target, event.token, event.target, False)
    elif event.kind == "tlbi_token":
        truth_target = clear_token(truth_target, event.token)
        if variant.clear_target_on_tlbi_token:
            ctlw_target = clear_token(ctlw_target, event.token)
    elif event.kind == "tlbi_all":
        truth_target = clear_all_targets(truth_target)
        if variant.clear_target_on_tlbi_all:
            ctlw_target = clear_all_targets(ctlw_target)

    return State(
        queue=tuple(queue),
        overflow=overflow,
        truth_source=truth_source,
        clpd_source=clpd_source,
        truth_target=truth_target,
        ctlw_target=ctlw_target,
    )


def reachable_states(variant: Variant, max_depth: int) -> dict[State, list[Event]]:
    start = State()
    paths: dict[State, list[Event]] = {start: []}
    work = deque([start])
    while work:
        state = work.popleft()
        path = paths[state]
        if len(path) >= max_depth:
            continue
        for event in EVENTS:
            nxt = transition(state, event, variant)
            if nxt not in paths:
                paths[nxt] = path + [event]
                work.append(nxt)
    return paths


def event_label(event: Event) -> str:
    if event.kind in {"commit_source", "dma", "chi", "io"}:
        return f"{event.kind}(line={event.line})"
    if event.kind == "burst":
        return f"burst(lines={list(event.lines)})"
    if event.kind in {"record_target", "remap"}:
        return f"{event.kind}(target={event.target}, token={event.token})"
    if event.kind == "tlbi_token":
        return f"tlbi_token(token={event.token})"
    return event.kind


def path_text(path: list[Event]) -> str:
    if not path:
        return "(initial)"
    return " -> ".join(event_label(event) for event in path)


def state_label(state: State) -> str:
    return (
        f"queue={list(state.queue)} overflow={int(state.overflow)} "
        f"truth_source={list(state.truth_source)} clpd_source={list(state.clpd_source)} "
        f"truth_target={[list(row) for row in state.truth_target]} "
        f"ctlw_target={[list(row) for row in state.ctlw_target]}"
    )


def query_label(query: Query) -> str:
    return (
        f"valid={int(query.valid)} src={query.src} "
        f"tgt={query.tgt} token={query.token}"
    )


def safety_counterexample(
    paths: dict[State, list[Event]], variant: Variant
) -> tuple[State, list[Event], Event, Query, str] | None:
    for state, path in paths.items():
        for event in EVENTS:
            for query in QUERIES:
                if not issue_allowed(state, event, query, variant):
                    continue
                reason = unsafe_reason(state, event, query)
                if reason:
                    return state, path, event, query, reason
    return None


def precision_witness(
    paths: dict[State, list[Event]], variant: Variant
) -> tuple[State, list[Event], Event, Query] | None:
    for state, path in paths.items():
        for event in EVENTS:
            for query in QUERIES:
                if not ground_truth_authorized(state, query):
                    continue
                if truth_hazard(state, event, query):
                    continue
                if not global_hold(state, event, query):
                    continue
                if issue_allowed(state, event, query, variant):
                    return state, path, event, query
    return None


def overhold_witness(
    paths: dict[State, list[Event]], variant: Variant
) -> tuple[State, list[Event], Event, Query] | None:
    full = VARIANTS[0]
    for state, path in paths.items():
        for event in EVENTS:
            for query in QUERIES:
                if not ground_truth_authorized(state, query):
                    continue
                if truth_hazard(state, event, query):
                    continue
                if variant_hold(state, event, query, full):
                    continue
                if variant_hold(state, event, query, variant):
                    return state, path, event, query
    return None


def hazard_cover(
    paths: dict[State, list[Event]], variant: Variant
) -> dict[str, tuple[State, list[Event], Event, Query]]:
    wanted = {
        "incoming_source_revocation",
        "queued_source_revocation",
        "same_cycle_target_remap",
        "same_cycle_token_tlbi",
        "same_cycle_global_tlbi",
        "overflow_fallback",
    }
    cover = {}
    for state, path in paths.items():
        for event in EVENTS:
            for query in QUERIES:
                if not metadata_authorized(state, query, variant):
                    continue
                reason = unsafe_reason(state, event, query)
                if reason not in wanted or reason in cover:
                    continue
                if variant_hold(state, event, query, variant):
                    cover[reason] = (state, path, event, query)
                if cover.keys() == wanted:
                    return cover
    return cover


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    full_paths = reachable_states(VARIANTS[0], MAX_DEPTH)
    full_cover = hazard_cover(full_paths, VARIANTS[0])

    lines = [
        "# COPPER CS-SARI Composition State-Space Check",
        "",
        "Date: 2026-06-12",
        "",
        "This bounded checker explores a composed authority machine:",
        "`issue = CLPD(source proof) and CTLW(target witness) and not CS-SARI-hold(candidate)`. ",
        "It separates ground-truth source/target validity from hardware metadata,",
        "then searches for stale-authority issue under weakened variants.",
        "",
        f"Model: {SRC_LINES} source lines, {TGT_LINES} target lines, {TOKENS} tokens,",
        f"revocation queue depth {DEPTH}, trace bound {MAX_DEPTH}.",
        "",
        f"Full-design reachable states explored: {len(full_paths)}",
        "",
        "| Variant | Reachable states | Safety result | Precision result | Notes |",
        "|---|---:|---|---|---|",
    ]

    all_ok = True
    variant_state_counts = {}
    for variant in VARIANTS:
        paths = reachable_states(variant, MAX_DEPTH)
        variant_state_counts[variant.name] = len(paths)
        cex = safety_counterexample(paths, variant)
        precision = precision_witness(paths, variant)
        overhold = overhold_witness(paths, variant)

        if variant.expected == "safety_pass":
            safety_text = "PASS" if cex is None else "FAIL"
            precision_text = "PASS" if precision is not None else "FAIL"
            if cex:
                _, path, event, query, reason = cex
                notes = (
                    f"unexpected counterexample reason={reason}; path={path_text(path)}; "
                    f"event={event_label(event)}; query={query_label(query)}"
                )
            elif precision:
                _, path, event, query = precision
                notes = (
                    "no stale-authority issue found; has unrelated-revocation precision "
                    f"witness at event={event_label(event)}, query={query_label(query)}"
                )
            else:
                notes = "safe within bound but no precision witness found."
            all_ok = all_ok and cex is None and precision is not None
        elif variant.expected == "safety_fail":
            safety_text = "FAIL expected" if cex else "UNEXPECTED PASS"
            precision_text = "n/a"
            if cex:
                _, path, event, query, reason = cex
                notes = (
                    f"counterexample reason={reason}; path={path_text(path)}; "
                    f"event={event_label(event)}; query={query_label(query)}"
                )
            else:
                notes = "No counterexample found within bound."
            all_ok = all_ok and cex is not None
        elif variant.expected == "precision_fail":
            safety_text = "PASS" if cex is None else "UNEXPECTED SAFETY FAIL"
            precision_text = "FAIL expected" if overhold else "UNEXPECTED PASS"
            if overhold:
                _, path, event, query = overhold
                notes = (
                    f"unnecessary global hold; path={path_text(path)}; "
                    f"event={event_label(event)}; query={query_label(query)}"
                )
            elif cex:
                _, path, event, query, reason = cex
                notes = (
                    f"unexpected stale-authority issue reason={reason}; "
                    f"path={path_text(path)}; event={event_label(event)}; "
                    f"query={query_label(query)}"
                )
            else:
                notes = "No over-hold witness found within bound."
            all_ok = all_ok and cex is None and overhold is not None
        else:
            raise ValueError(variant.expected)

        lines.append(
            f"| {variant.name} | {len(paths)} | {safety_text} | {precision_text} | {notes} |"
        )

    lines.extend(["", "## Hazard Coverage", ""])
    for hazard in sorted(full_cover):
        state, path, event, query = full_cover[hazard]
        lines.extend(
            [
                f"### {hazard}",
                "",
                f"- Path: `{path_text(path)}`",
                f"- State: `{state_label(state)}`",
                f"- Event: `{event_label(event)}`",
                f"- Query: `{query_label(query)}`",
                "",
            ]
        )

    precision = precision_witness(full_paths, VARIANTS[0])
    if precision:
        state, path, event, query = precision
        lines.extend(
            [
                "## Precision Witness",
                "",
                "The query has valid CLPD and CTLW metadata and valid ground truth.",
                "A global revocation hold would stop it, but CS-SARI does not hold",
                "because the event is unrelated to the candidate source, target,",
                "and token.",
                "",
                f"- Path: `{path_text(path)}`",
                f"- State: `{state_label(state)}`",
                f"- Event: `{event_label(event)}`",
                f"- Query: `{query_label(query)}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Interpretation",
            "",
            "The composed checker is stricter than the standalone CS-SARI model: it",
            "requires source proof, target witness, scoped revocation hold, and",
            "post-revocation metadata clearing to agree. The full variant has no",
            "bounded stale-authority counterexample and retains a precision witness",
            "against global revocation hold. Removing either one side of the final",
            "authority gate, either metadata clear path, or any required CS-SARI",
            "hazard term produces a short counterexample.",
            "",
            f"Overall status: {'PASS' if all_ok else 'FAIL'}",
            "",
        ]
    )

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)
    print(f"full_reachable_states={len(full_paths)}")
    for name, count in sorted(variant_state_counts.items()):
        print(f"{name}_states={count}")
    print(f"status={'PASS' if all_ok else 'FAIL'}")
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
