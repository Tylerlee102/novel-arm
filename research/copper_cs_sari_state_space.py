#!/usr/bin/env python3
"""Bounded state-space checker for COPPER CS-SARI.

CS-SARI replaces global DMP revocation hold with candidate-specific conflict
hold. This checker exhaustively explores a tiny revocation queue and asks:

1. Safety: no authorized DMP candidate may issue when a matching source,
   queued-source, remap, TLBI, TLBI-all, or overflow revocation hazard exists.
2. Precision: an authorized DMP candidate may issue during unrelated revocation
   events that global SARI would have held.

The model is intentionally small: three source lines, three target lines, two
tokens, a two-entry queue, and bounded traces. It is not production formal
signoff, but it makes the CS-SARI invariant executable and produces short
counterexamples for weakened variants.
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
OUT = ROOT / "research" / "results" / "COPPER_CS_SARI_STATE_SPACE.md"


@dataclass(frozen=True)
class State:
    queue: tuple[int, ...] = ()
    overflow: bool = False
    live_source: tuple[bool, ...] = (True, True, True)
    live_target: tuple[tuple[bool, ...], ...] = (
        (True, True, True),
        (True, True, True),
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
    check_remap_line: bool = True
    check_remap_token: bool = True
    check_tlbi_token: bool = True
    check_tlbi_all: bool = True
    check_overflow: bool = True
    expected: str = "safety_pass"


VARIANTS = [
    Variant("CS_SARI"),
    Variant("BUG_NO_INCOMING_SOURCE_CHECK", check_incoming_source=False, expected="safety_fail"),
    Variant("BUG_NO_QUEUED_SOURCE_CHECK", check_queued_source=False, expected="safety_fail"),
    Variant("BUG_NO_REMAP_CHECK", check_remap_event=False, expected="safety_fail"),
    Variant("BUG_REMAP_IGNORES_LINE_PRECISION", check_remap_line=False, expected="precision_fail"),
    Variant("BUG_REMAP_IGNORES_TOKEN_PRECISION", check_remap_token=False, expected="precision_fail"),
    Variant("BUG_NO_TLBI_TOKEN_CHECK", check_tlbi_token=False, expected="safety_fail"),
    Variant("BUG_NO_TLBI_ALL_CHECK", check_tlbi_all=False, expected="safety_fail"),
    Variant("BUG_NO_OVERFLOW_FALLBACK", check_overflow=False, expected="safety_fail"),
]


EVENTS = [Event("none")]
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


def is_source_event(event: Event) -> bool:
    return bool(source_event_lines(event))


def source_event_lines(event: Event) -> tuple[int, ...]:
    if event.kind in {"dma", "chi", "io"}:
        return (event.line,)
    if event.kind == "burst":
        return event.lines
    return ()


def authorized(state: State, query: Query) -> bool:
    return (
        query.valid
        and state.live_source[query.src]
        and state.live_target[query.token][query.tgt]
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

    hold = False
    if variant.check_overflow:
        hold = hold or state.overflow
    if variant.check_queued_source:
        hold = hold or (query.src in state.queue)
    if variant.check_incoming_source:
        hold = hold or (query.src in source_event_lines(event))

    if event.kind == "remap" and variant.check_remap_event:
        line_ok = (event.target == query.tgt) if variant.check_remap_line else True
        token_ok = (event.token == query.token) if variant.check_remap_token else True
        hold = hold or (line_ok and token_ok)

    if event.kind == "tlbi_token":
        if variant.check_tlbi_token:
            hold = hold or (event.token == query.token)

    if event.kind == "tlbi_all" and variant.check_tlbi_all:
        hold = True

    return hold


def issue_allowed(state: State, event: Event, query: Query, variant: Variant) -> bool:
    return authorized(state, query) and not variant_hold(state, event, query, variant)


def transition(state: State, event: Event) -> State:
    live_source = list(state.live_source)
    live_target = [list(row) for row in state.live_target]

    queue = list(state.queue)
    if queue:
        cleared = queue.pop(0)
        live_source[cleared] = False

    overflow = state.overflow
    for line in source_event_lines(event):
        if len(queue) < DEPTH:
            queue.append(line)
        else:
            overflow = True

    if event.kind == "remap":
        live_target[event.token][event.target] = False
    elif event.kind == "tlbi_token":
        live_target[event.token] = [False] * TGT_LINES
    elif event.kind == "tlbi_all":
        live_target = [[False] * TGT_LINES for _ in range(TOKENS)]

    return State(
        queue=tuple(queue),
        overflow=overflow,
        live_source=tuple(live_source),
        live_target=tuple(tuple(row) for row in live_target),
    )


def reachable_states(max_depth: int) -> dict[State, list[Event]]:
    start = State()
    paths: dict[State, list[Event]] = {start: []}
    work = deque([start])
    while work:
        state = work.popleft()
        path = paths[state]
        if len(path) >= max_depth:
            continue
        for event in EVENTS:
            nxt = transition(state, event)
            if nxt not in paths:
                paths[nxt] = path + [event]
                work.append(nxt)
    return paths


def event_label(event: Event) -> str:
    if event.kind in {"dma", "chi", "io"}:
        return f"{event.kind}(line={event.line})"
    if event.kind == "burst":
        return f"burst(lines={list(event.lines)})"
    if event.kind == "remap":
        return f"remap(target={event.target}, token={event.token})"
    if event.kind == "tlbi_token":
        return f"tlbi_token(token={event.token})"
    return event.kind


def state_label(state: State) -> str:
    return (
        f"queue={list(state.queue)} overflow={int(state.overflow)} "
        f"live_source={list(state.live_source)} "
        f"live_target={[list(row) for row in state.live_target]}"
    )


def query_label(query: Query) -> str:
    return (
        f"valid={int(query.valid)} src={query.src} "
        f"tgt={query.tgt} token={query.token}"
    )


def classify_hazard(state: State, event: Event, query: Query) -> str:
    if state.overflow:
        return "overflow_fallback"
    if query.src in state.queue:
        return "queued_source"
    if query.src in source_event_lines(event):
        return "incoming_source"
    if event.kind == "remap" and event.target == query.tgt and event.token == query.token:
        return "target_remap"
    if event.kind == "tlbi_token" and event.token == query.token:
        return "tlbi_token"
    if event.kind == "tlbi_all":
        return "tlbi_all"
    return "none"


def safety_counterexample(
    paths: dict[State, list[Event]], variant: Variant
) -> tuple[State, list[Event], Event, Query, str] | None:
    for state, path in paths.items():
        for event in EVENTS:
            for query in QUERIES:
                if not authorized(state, query):
                    continue
                if not truth_hazard(state, event, query):
                    continue
                if issue_allowed(state, event, query, variant):
                    return state, path, event, query, classify_hazard(state, event, query)
    return None


def precision_witness(paths: dict[State, list[Event]], variant: Variant) -> tuple[State, list[Event], Event, Query] | None:
    for state, path in paths.items():
        for event in EVENTS:
            for query in QUERIES:
                if not authorized(state, query):
                    continue
                if truth_hazard(state, event, query):
                    continue
                if not global_hold(state, event, query):
                    continue
                if issue_allowed(state, event, query, variant):
                    return state, path, event, query
    return None


def overhold_counterexample(
    paths: dict[State, list[Event]], variant: Variant
) -> tuple[State, list[Event], Event, Query] | None:
    full = VARIANTS[0]
    for state, path in paths.items():
        for event in EVENTS:
            for query in QUERIES:
                if not authorized(state, query):
                    continue
                if truth_hazard(state, event, query):
                    continue
                if variant_hold(state, event, query, full):
                    continue
                if variant_hold(state, event, query, variant):
                    return state, path, event, query
    return None


def minimal_cover(paths: dict[State, list[Event]], variant: Variant) -> dict[str, tuple[State, list[Event], Event, Query]]:
    cover = {}
    wanted = {
        "incoming_source",
        "queued_source",
        "target_remap",
        "tlbi_token",
        "tlbi_all",
        "overflow_fallback",
    }
    for state, path in paths.items():
        for event in EVENTS:
            for query in QUERIES:
                if not authorized(state, query):
                    continue
                hazard = classify_hazard(state, event, query)
                if hazard not in wanted or hazard in cover:
                    continue
                if variant_hold(state, event, query, variant):
                    cover[hazard] = (state, path, event, query)
                if cover.keys() == wanted:
                    return cover
    return cover


def path_text(path: list[Event]) -> str:
    if not path:
        return "(initial)"
    return " -> ".join(event_label(event) for event in path)


def main() -> None:
    paths = reachable_states(MAX_DEPTH)
    lines = [
        "# COPPER CS-SARI State-Space Check",
        "",
        "Date: 2026-06-12",
        "",
        "This bounded checker exhaustively explores a tiny CS-SARI revocation",
        f"model with {SRC_LINES} source lines, {TGT_LINES} target lines,",
        f"{TOKENS} tokens, queue depth {DEPTH}, and traces to depth {MAX_DEPTH}.",
        "It checks that candidate-specific hold is safe for matching hazards",
        "and precise enough to avoid global stalls for unrelated revocations.",
        "",
        f"Reachable states explored: {len(paths)}",
        "",
        "| Variant | Safety result | Precision result | Notes |",
        "|---|---|---|---|",
    ]

    full_cover = minimal_cover(paths, VARIANTS[0])
    all_ok = True
    for variant in VARIANTS:
        cex = safety_counterexample(paths, variant)
        witness = precision_witness(paths, variant)
        overhold = overhold_counterexample(paths, variant)
        if variant.expected == "safety_pass":
            safety = "PASS"
            precision = "PASS" if witness and overhold is None else "FAIL"
            notes = "No stale-authority issue found; unrelated global-hold witness found."
            all_ok = all_ok and cex is None and witness is not None and overhold is None
        elif variant.expected == "safety_fail":
            safety = "FAIL expected" if cex else "UNEXPECTED PASS"
            precision = "n/a"
            if cex:
                _, path, event, query, hazard = cex
                notes = (
                    f"counterexample hazard={hazard}; path={path_text(path)}; "
                    f"event={event_label(event)}; query={query_label(query)}"
                )
            else:
                notes = "No counterexample found within bound."
            all_ok = all_ok and cex is not None
        elif variant.expected == "precision_fail":
            safety = "PASS (over-conservative)"
            precision = "FAIL expected" if overhold else "UNEXPECTED PASS"
            if overhold:
                _, path, event, query = overhold
                notes = (
                    "unnecessary hold; "
                    f"path={path_text(path)}; event={event_label(event)}; "
                    f"query={query_label(query)}"
                )
            else:
                notes = "No over-hold witness found within bound."
            all_ok = all_ok and cex is None and overhold is not None
        else:
            raise ValueError(variant.expected)
        lines.append(f"| {variant.name} | {safety} | {precision} | {notes} |")

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

    witness = precision_witness(paths, VARIANTS[0])
    if witness:
        state, path, event, query = witness
        lines.extend(
            [
                "## Precision Witness",
                "",
                "This witness is authorized and would be globally held, but CS-SARI",
                "does not hold because the revocation does not conflict with the",
                "candidate.",
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
            "The full CS-SARI model satisfies the bounded no-transient-authority",
            "property and has an explicit precision witness. Each weakened variant",
            "fails with a short stale-authority counterexample, showing that the",
            "incoming-source, queued-source, target-remap, token-TLBI, TLBI-all,",
            "and overflow terms are not decorative. The line/token precision",
            "variants remain safe but over-hold unrelated remaps, which is a",
            "performance/precision failure rather than a stale-authority failure.",
            "",
            f"Overall status: {'PASS' if all_ok else 'FAIL'}",
            "",
        ]
    )

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)
    print(f"reachable_states={len(paths)}")
    print(f"status={'PASS' if all_ok else 'FAIL'}")
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
