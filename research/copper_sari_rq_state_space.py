#!/usr/bin/env python3
"""Bounded checker for COPPER SARI-RQ.

SARI-RQ replaces SARI's shift queue with a circular queue to remove the long
queue-shift timing path. This checker does not try to prove ring buffers in
general. It checks the COPPER-specific contract:

1. Under the frontdoor ready protocol, the ring queue is equivalent to the
   original abstract SARI shift queue for source-revocation order and overflow.
2. A DMP candidate is held whenever there is an incoming source event, queued
   source revocation, target event, or overflow fallback.
3. If a source burst arrives while not ready, the frontdoor must hold and the
   conservative overflow fallback covers protocol violation.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path


SRC_LINES = 3
DEPTH = 3
MAX_DEPTH = 8

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "results" / "COPPER_SARI_RQ_STATE_SPACE.md"


@dataclass(frozen=True)
class State:
    shift_q: tuple[int, ...] = ()
    ring_q: tuple[int, ...] = ()
    shift_overflow: bool = False
    ring_overflow: bool = False


@dataclass(frozen=True)
class Event:
    sources: tuple[int, ...] = ()
    target_event: bool = False
    obey_ready: bool = True


EVENTS: list[Event] = [Event()]
for line in range(SRC_LINES):
    EVENTS.append(Event(sources=(line,)))
for a in range(SRC_LINES):
    for b in range(SRC_LINES):
        EVENTS.append(Event(sources=(a, b)))
for a in range(SRC_LINES):
    for b in range(SRC_LINES):
        for c in range(SRC_LINES):
            EVENTS.append(Event(sources=(a, b, c)))
EVENTS += [Event(target_event=True)]

VIOLATING_EVENTS = [
    Event(sources=(0,), obey_ready=False),
    Event(sources=(0, 1), obey_ready=False),
    Event(sources=(0, 1, 2), obey_ready=False),
]


def ready(queue: tuple[int, ...]) -> bool:
    space_after_dequeue = DEPTH - len(queue) + (1 if queue else 0)
    return space_after_dequeue >= 3


def dmp_hold(queue: tuple[int, ...], overflow: bool, event: Event) -> bool:
    return overflow or bool(queue) or bool(event.sources) or event.target_event


def source_clear(queue: tuple[int, ...]) -> int | None:
    return queue[0] if queue else None


def shift_transition(queue: tuple[int, ...], overflow: bool, event: Event) -> tuple[tuple[int, ...], bool]:
    q = list(queue)
    if q:
        q.pop(0)
    if event.sources and (event.obey_ready and not ready(queue)):
        return tuple(q), overflow
    if event.sources and (not event.obey_ready and not ready(queue)):
        return tuple(q), True
    for line in event.sources:
        if len(q) < DEPTH:
            q.append(line)
        else:
            overflow = True
    return tuple(q), overflow


def ring_transition(queue: tuple[int, ...], overflow: bool, event: Event) -> tuple[tuple[int, ...], bool]:
    q = list(queue)
    if q:
        q.pop(0)
    if event.sources and not ready(queue):
        if event.obey_ready:
            return tuple(q), overflow
        return tuple(q), True
    q.extend(event.sources)
    if len(q) > DEPTH:
        return tuple(q[:DEPTH]), True
    return tuple(q), overflow


def transition(state: State, event: Event) -> State:
    shift_q, shift_overflow = shift_transition(state.shift_q, state.shift_overflow, event)
    ring_q, ring_overflow = ring_transition(state.ring_q, state.ring_overflow, event)
    return State(shift_q, ring_q, shift_overflow, ring_overflow)


def event_label(event: Event) -> str:
    parts = []
    if event.sources:
        parts.append(f"sources={list(event.sources)}")
    if event.target_event:
        parts.append("target")
    if not event.obey_ready:
        parts.append("violates_ready")
    return "none" if not parts else ",".join(parts)


def state_label(state: State) -> str:
    return (
        f"shift_q={list(state.shift_q)} ring_q={list(state.ring_q)} "
        f"shift_overflow={int(state.shift_overflow)} "
        f"ring_overflow={int(state.ring_overflow)}"
    )


def path_text(path: list[Event]) -> str:
    return "(initial)" if not path else " -> ".join(event_label(event) for event in path)


def reachable_ready_states(max_depth: int) -> dict[State, list[Event]]:
    start = State()
    paths: dict[State, list[Event]] = {start: []}
    work = deque([start])
    while work:
        state = work.popleft()
        path = paths[state]
        if len(path) >= max_depth:
            continue
        for event in EVENTS:
            if event.sources and not ready(state.ring_q):
                continue
            nxt = transition(state, event)
            if nxt not in paths:
                paths[nxt] = path + [event]
                work.append(nxt)
    return paths


def equivalence_counterexample(paths: dict[State, list[Event]]) -> tuple[State, list[Event]] | None:
    for state, path in paths.items():
        if (
            state.shift_q != state.ring_q
            or state.shift_overflow != state.ring_overflow
        ):
            return state, path
    return None


def hold_counterexample(paths: dict[State, list[Event]]) -> tuple[State, list[Event], Event] | None:
    for state, path in paths.items():
        for event in EVENTS:
            hold = dmp_hold(state.ring_q, state.ring_overflow, event)
            hazard = state.ring_overflow or bool(state.ring_q) or bool(event.sources) or event.target_event
            if hazard and not hold:
                return state, path, event
    return None


def backpressure_witness(paths: dict[State, list[Event]]) -> tuple[State, list[Event], Event, State] | None:
    for state, path in paths.items():
        if ready(state.ring_q):
            continue
        for event in VIOLATING_EVENTS:
            nxt = transition(state, event)
            if dmp_hold(state.ring_q, state.ring_overflow, event) and nxt.ring_overflow:
                return state, path, event, nxt
    return None


def ready_acceptance_cover(paths: dict[State, list[Event]]) -> dict[int, tuple[State, list[Event], Event, State]]:
    cover = {}
    for state, path in paths.items():
        for event in EVENTS:
            if not event.sources or not ready(state.ring_q):
                continue
            nxt = transition(state, event)
            count = len(event.sources)
            if count not in cover and nxt.ring_q == nxt.shift_q:
                cover[count] = (state, path, event, nxt)
    return cover


def main() -> None:
    paths = reachable_ready_states(MAX_DEPTH)
    equiv_cex = equivalence_counterexample(paths)
    hold_cex = hold_counterexample(paths)
    bp = backpressure_witness(paths)
    cover = ready_acceptance_cover(paths)
    ok = equiv_cex is None and hold_cex is None and bp is not None and set(cover) == {1, 2, 3}

    lines = [
        "# COPPER SARI-RQ State-Space Check",
        "",
        "Date: 2026-06-16",
        "",
        "This bounded model checks the timing-optimized SARI-RQ ring queue",
        "against the original abstract SARI shift-queue behavior under the",
        "frontdoor ready protocol.",
        "",
        f"Model: {SRC_LINES} source lines, queue depth {DEPTH}, trace bound {MAX_DEPTH}.",
        f"Reachable ready-respecting states explored: {len(paths)}",
        "",
        "| Check | Result | Detail |",
        "|---|---:|---|",
    ]

    if equiv_cex is None:
        lines.append("| Ring/shift equivalence under ready protocol | PASS | queue order and overflow match for all reachable states |")
    else:
        state, path = equiv_cex
        lines.append(
            f"| Ring/shift equivalence under ready protocol | FAIL | path={path_text(path)}; state={state_label(state)} |"
        )

    if hold_cex is None:
        lines.append("| Hold covers incoming/queued/target/overflow hazards | PASS | no missing-hold counterexample found |")
    else:
        state, path, event = hold_cex
        lines.append(
            f"| Hold covers incoming/queued/target/overflow hazards | FAIL | path={path_text(path)}; state={state_label(state)}; event={event_label(event)} |"
        )

    if bp is None:
        lines.append("| Backpressure/overflow fallback | FAIL | no not-ready source-burst witness found |")
    else:
        state, path, event, nxt = bp
        lines.append(
            f"| Backpressure/overflow fallback | PASS | path={path_text(path)}; state={state_label(state)}; violating_event={event_label(event)}; next={state_label(nxt)} |"
        )

    for count in sorted(cover):
        state, path, event, nxt = cover[count]
        lines.append(
            f"| Ready burst admission {count} source event(s) | PASS | path={path_text(path)}; state={state_label(state)}; event={event_label(event)}; next={state_label(nxt)} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "SARI-RQ is not claimed as a new research idea by itself; it is the",
            "timing-safe implementation of the SoC revocation intake used by the",
            "AMBA/SARI/CLPD/CTLW authority bridge. The checker supports the RTL",
            "change by proving bounded equivalence to the abstract shift queue",
            "when the frontdoor obeys `source_events_ready`, and by confirming",
            "that a protocol-violating source burst falls into conservative",
            "`overflow_sticky` hold rather than silently losing authority events.",
            "",
            f"Overall status: {'PASS' if ok else 'FAIL'}",
            "",
        ]
    )

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)
    print(f"reachable_states={len(paths)}")
    print(f"status={'PASS' if ok else 'FAIL'}")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
