#!/usr/bin/env python3
"""Bounded TLB/coherence authority-contract checker for COPPER.

This is not a production Arm CHI/TLB proof. It is an executable contract model
for the COPPER boundary that reviewers keep asking about: source proof and
target witness metadata must not survive source revocation, target remap/TLBI,
permission downgrade, or pending invalidation windows.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SRC_LINES = 2
TGT_LINES = 2
TOKENS = 2
QUEUE_DEPTH = 2
MAX_DEPTH = 5

GLOBAL_ENTRY = 10_000
TOKEN_ENTRY_BASE = 1_000

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "results" / "COPPER_TLB_COHERENCE_CONTRACT.md"


BoolRows = tuple[tuple[bool, ...], ...]
IntRows = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class State:
    source_truth: tuple[bool, ...] = (False, False)
    source_meta: tuple[bool, ...] = (False, False)
    target_truth: BoolRows = ((False, False), (False, False))
    target_meta: BoolRows = ((False, False), (False, False))
    current_epoch: IntRows = ((0, 0), (0, 0))
    witness_epoch: IntRows = ((0, 0), (0, 0))
    permission: BoolRows = ((True, True), (True, True))
    source_queue: tuple[int, ...] = ()
    target_queue: tuple[int, ...] = ()
    overflow: bool = False


@dataclass(frozen=True)
class Event:
    kind: str
    src: int = 0
    tgt: int = 0
    token: int = 0


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
    check_token_tlbi_event: bool = True
    check_global_tlbi_event: bool = True
    check_queued_target: bool = True
    check_permission_event: bool = True
    check_overflow: bool = True
    clear_source_on_drain: bool = True
    clear_remap_on_drain: bool = True
    clear_token_tlbi_on_drain: bool = True
    clear_global_tlbi_on_drain: bool = True
    require_source_meta: bool = True
    require_exact_target_line: bool = True
    require_witness_epoch: bool = True
    require_permission: bool = True
    force_global_hold: bool = False
    expected: str = "safety_pass"


FULL = Variant("FULL_TLB_COHERENCE_CONTRACT")

VARIANTS = [
    FULL,
    Variant(
        "BUG_NO_INCOMING_SOURCE_HOLD",
        check_incoming_source=False,
        expected="safety_fail",
    ),
    Variant(
        "BUG_NO_QUEUED_SOURCE_HOLD",
        check_queued_source=False,
        clear_source_on_drain=False,
        expected="safety_fail",
    ),
    Variant(
        "BUG_NO_TARGET_REMAP_HOLD",
        check_remap_event=False,
        expected="safety_fail",
    ),
    Variant(
        "BUG_NO_TARGET_REMAP_CLEAR",
        clear_remap_on_drain=False,
        require_witness_epoch=False,
        expected="safety_fail",
    ),
    Variant(
        "BUG_NO_TOKEN_TLBI_HOLD",
        check_token_tlbi_event=False,
        expected="safety_fail",
    ),
    Variant(
        "BUG_NO_TOKEN_TLBI_CLEAR",
        clear_token_tlbi_on_drain=False,
        require_witness_epoch=False,
        expected="safety_fail",
    ),
    Variant(
        "BUG_NO_GLOBAL_TLBI_HOLD",
        check_global_tlbi_event=False,
        expected="safety_fail",
    ),
    Variant(
        "BUG_NO_GLOBAL_TLBI_CLEAR",
        clear_global_tlbi_on_drain=False,
        require_witness_epoch=False,
        expected="safety_fail",
    ),
    Variant(
        "BUG_NO_PERMISSION_DOWNGRADE_HOLD",
        check_permission_event=False,
        expected="safety_fail",
    ),
    Variant(
        "BUG_NO_PERMISSION_GATE",
        require_permission=False,
        expected="safety_fail",
    ),
    Variant(
        "BUG_NO_TARGET_QUEUE_HOLD",
        check_queued_target=False,
        expected="safety_fail",
    ),
    Variant(
        "BUG_PAGE_LEVEL_TARGET_WITNESS",
        require_exact_target_line=False,
        expected="safety_fail",
    ),
    Variant(
        "BUG_SOURCE_ONLY_AUTHORITY",
        require_exact_target_line=False,
        require_witness_epoch=False,
        expected="safety_fail",
    ),
    Variant("BUG_GLOBAL_HOLD", force_global_hold=True, expected="precision_fail"),
]


EVENTS = [Event("none")]
EVENTS += [Event("commit_source", src=src) for src in range(SRC_LINES)]
EVENTS += [
    Event("record_target", token=token, tgt=tgt)
    for token in range(TOKENS)
    for tgt in range(TGT_LINES)
]
EVENTS += [Event("dma_write", src=src) for src in range(SRC_LINES)]
EVENTS += [Event("chi_update", src=src) for src in range(SRC_LINES)]
EVENTS += [
    Event("target_remap", token=token, tgt=tgt)
    for token in range(TOKENS)
    for tgt in range(TGT_LINES)
]
EVENTS += [Event("tlbi_token", token=token) for token in range(TOKENS)]
EVENTS += [Event("tlbi_global")]
EVENTS += [
    Event("permission_downgrade", token=token, tgt=tgt)
    for token in range(TOKENS)
    for tgt in range(TGT_LINES)
]
EVENTS += [
    Event("permission_restore", token=token, tgt=tgt)
    for token in range(TOKENS)
    for tgt in range(TGT_LINES)
]

QUERIES = [Query(False, 0, 0, 0)]
QUERIES += [
    Query(True, src, tgt, token)
    for src in range(SRC_LINES)
    for token in range(TOKENS)
    for tgt in range(TGT_LINES)
]


def set_bool(values: tuple[bool, ...], idx: int, value: bool) -> tuple[bool, ...]:
    out = list(values)
    out[idx] = value
    return tuple(out)


def set_row_bool(values: BoolRows, token: int, tgt: int, value: bool) -> BoolRows:
    out = [list(row) for row in values]
    out[token][tgt] = value
    return tuple(tuple(row) for row in out)


def set_row_int(values: IntRows, token: int, tgt: int, value: int) -> IntRows:
    out = [list(row) for row in values]
    out[token][tgt] = value
    return tuple(tuple(row) for row in out)


def clear_token(values: BoolRows, token: int) -> BoolRows:
    out = [list(row) for row in values]
    out[token] = [False] * TGT_LINES
    return tuple(tuple(row) for row in out)


def bump_target_epoch(values: IntRows, token: int, tgt: int) -> IntRows:
    return set_row_int(values, token, tgt, values[token][tgt] ^ 1)


def bump_token_epoch(values: IntRows, token: int) -> IntRows:
    out = [list(row) for row in values]
    out[token] = [item ^ 1 for item in out[token]]
    return tuple(tuple(row) for row in out)


def bump_all_epoch(values: IntRows) -> IntRows:
    return tuple(tuple(item ^ 1 for item in row) for row in values)


def specific_entry(token: int, tgt: int) -> int:
    return token * TGT_LINES + tgt


def token_entry(token: int) -> int:
    return TOKEN_ENTRY_BASE + token


def target_entry_conflicts(entry: int, query: Query) -> bool:
    if entry == GLOBAL_ENTRY:
        return True
    if entry >= TOKEN_ENTRY_BASE:
        return entry - TOKEN_ENTRY_BASE == query.token
    return entry == specific_entry(query.token, query.tgt)


def enqueue(queue: tuple[int, ...], entry: int) -> tuple[tuple[int, ...], bool]:
    if entry in queue:
        return queue, False
    if len(queue) >= QUEUE_DEPTH:
        return queue, True
    return queue + (entry,), False


def source_event_line(event: Event) -> int | None:
    if event.kind in {"dma_write", "chi_update"}:
        return event.src
    return None


def target_event_entry(event: Event) -> int | None:
    if event.kind == "target_remap":
        return specific_entry(event.token, event.tgt)
    if event.kind == "tlbi_token":
        return token_entry(event.token)
    if event.kind == "tlbi_global":
        return GLOBAL_ENTRY
    return None


def event_conflicts_target(event: Event, query: Query) -> bool:
    entry = target_event_entry(event)
    if entry is None:
        return False
    return target_entry_conflicts(entry, query)


def event_conflicts_permission(event: Event, query: Query) -> bool:
    return (
        event.kind == "permission_downgrade"
        and event.token == query.token
        and event.tgt == query.tgt
    )


def metadata_authorized(state: State, query: Query, variant: Variant) -> bool:
    if not query.valid:
        return False

    source_ok = True
    if variant.require_source_meta:
        source_ok = state.source_meta[query.src]

    if variant.require_exact_target_line:
        target_ok = state.target_meta[query.token][query.tgt]
    else:
        # Page-level witness bug: any live target witness under the token opens
        # every target line under that token.
        target_ok = any(state.target_meta[query.token])

    epoch_ok = True
    if variant.require_witness_epoch:
        epoch_ok = (
            state.witness_epoch[query.token][query.tgt]
            == state.current_epoch[query.token][query.tgt]
        )

    perm_ok = True
    if variant.require_permission:
        perm_ok = state.permission[query.token][query.tgt]

    return source_ok and target_ok and epoch_ok and perm_ok


def ground_truth_authorized(state: State, query: Query) -> bool:
    return (
        query.valid
        and state.source_truth[query.src]
        and state.target_truth[query.token][query.tgt]
        and state.permission[query.token][query.tgt]
        and state.witness_epoch[query.token][query.tgt]
        == state.current_epoch[query.token][query.tgt]
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
        hold = hold or query.src in state.source_queue
    if variant.check_incoming_source:
        hold = hold or source_event_line(event) == query.src
    if variant.check_queued_target:
        hold = hold or any(target_entry_conflicts(entry, query) for entry in state.target_queue)
    if variant.check_remap_event and event.kind == "target_remap":
        hold = hold or event_conflicts_target(event, query)
    if variant.check_token_tlbi_event and event.kind == "tlbi_token":
        hold = hold or event_conflicts_target(event, query)
    if variant.check_global_tlbi_event and event.kind == "tlbi_global":
        hold = hold or event_conflicts_target(event, query)
    if variant.check_permission_event:
        hold = hold or event_conflicts_permission(event, query)
    return hold


def issue_allowed(state: State, event: Event, query: Query, variant: Variant) -> bool:
    return metadata_authorized(state, query, variant) and not variant_hold(
        state, event, query, variant
    )


def unsafe_reason(state: State, event: Event, query: Query) -> str | None:
    if not query.valid:
        return None
    source_line = source_event_line(event)
    if state.overflow:
        return "overflow_fallback"
    if query.src in state.source_queue:
        return "queued_source_revocation"
    if source_line == query.src:
        return "incoming_source_revocation"
    if any(target_entry_conflicts(entry, query) for entry in state.target_queue):
        return "queued_target_revocation"
    if event.kind == "target_remap" and event_conflicts_target(event, query):
        return "same_cycle_target_remap"
    if event.kind == "tlbi_token" and event_conflicts_target(event, query):
        return "same_cycle_token_tlbi"
    if event.kind == "tlbi_global":
        return "same_cycle_global_tlbi"
    if event_conflicts_permission(event, query):
        return "same_cycle_permission_downgrade"
    if not state.source_truth[query.src]:
        return "missing_or_stale_source_truth"
    if not state.target_truth[query.token][query.tgt]:
        return "missing_or_stale_target_witness"
    if (
        state.witness_epoch[query.token][query.tgt]
        != state.current_epoch[query.token][query.tgt]
    ):
        return "stale_target_epoch"
    if not state.permission[query.token][query.tgt]:
        return "permission_not_allowed"
    return None


def truth_hazard(state: State, event: Event, query: Query) -> bool:
    return unsafe_reason(state, event, query) in {
        "overflow_fallback",
        "queued_source_revocation",
        "incoming_source_revocation",
        "queued_target_revocation",
        "same_cycle_target_remap",
        "same_cycle_token_tlbi",
        "same_cycle_global_tlbi",
        "same_cycle_permission_downgrade",
    }


def global_hold(state: State, event: Event, query: Query) -> bool:
    return query.valid and (
        state.overflow
        or bool(state.source_queue)
        or bool(state.target_queue)
        or source_event_line(event) is not None
        or target_event_entry(event) is not None
        or event.kind == "permission_downgrade"
    )


def repair_target_entry(
    target_meta: BoolRows,
    current_epoch: IntRows,
    entry: int,
    variant: Variant,
) -> tuple[BoolRows, IntRows]:
    if entry == GLOBAL_ENTRY:
        if variant.clear_global_tlbi_on_drain:
            target_meta = tuple(tuple(False for _ in row) for row in target_meta)
        current_epoch = bump_all_epoch(current_epoch)
        return target_meta, current_epoch
    if entry >= TOKEN_ENTRY_BASE:
        token = entry - TOKEN_ENTRY_BASE
        if variant.clear_token_tlbi_on_drain:
            target_meta = clear_token(target_meta, token)
        current_epoch = bump_token_epoch(current_epoch, token)
        return target_meta, current_epoch
    token = entry // TGT_LINES
    tgt = entry % TGT_LINES
    if variant.clear_remap_on_drain:
        target_meta = set_row_bool(target_meta, token, tgt, False)
    current_epoch = bump_target_epoch(current_epoch, token, tgt)
    return target_meta, current_epoch


def step_state(state: State, event: Event, variant: Variant) -> State:
    source_truth = state.source_truth
    source_meta = state.source_meta
    target_truth = state.target_truth
    target_meta = state.target_meta
    current_epoch = state.current_epoch
    witness_epoch = state.witness_epoch
    permission = state.permission
    source_queue = list(state.source_queue)
    target_queue = list(state.target_queue)
    overflow = state.overflow

    if event.kind == "commit_source":
        source_truth = set_bool(source_truth, event.src, True)
        source_meta = set_bool(source_meta, event.src, True)
    elif event.kind == "record_target" and permission[event.token][event.tgt]:
        target_truth = set_row_bool(target_truth, event.token, event.tgt, True)
        target_meta = set_row_bool(target_meta, event.token, event.tgt, True)
        witness_epoch = set_row_int(
            witness_epoch,
            event.token,
            event.tgt,
            current_epoch[event.token][event.tgt],
        )
    elif event.kind in {"dma_write", "chi_update"}:
        source_truth = set_bool(source_truth, event.src, False)
        source_queue_tuple, spill = enqueue(tuple(source_queue), event.src)
        source_queue = list(source_queue_tuple)
        overflow = overflow or spill
    elif event.kind == "target_remap":
        target_truth = set_row_bool(target_truth, event.token, event.tgt, False)
        target_queue_tuple, spill = enqueue(
            tuple(target_queue), specific_entry(event.token, event.tgt)
        )
        target_queue = list(target_queue_tuple)
        overflow = overflow or spill
    elif event.kind == "tlbi_token":
        target_truth = clear_token(target_truth, event.token)
        target_queue_tuple, spill = enqueue(tuple(target_queue), token_entry(event.token))
        target_queue = list(target_queue_tuple)
        overflow = overflow or spill
    elif event.kind == "tlbi_global":
        target_truth = tuple(tuple(False for _ in row) for row in target_truth)
        target_queue_tuple, spill = enqueue(tuple(target_queue), GLOBAL_ENTRY)
        target_queue = list(target_queue_tuple)
        overflow = overflow or spill
    elif event.kind == "permission_downgrade":
        permission = set_row_bool(permission, event.token, event.tgt, False)
    elif event.kind == "permission_restore":
        permission = set_row_bool(permission, event.token, event.tgt, True)

    if state.source_queue:
        drained = source_queue.pop(0)
        if variant.clear_source_on_drain:
            source_meta = set_bool(source_meta, drained, False)

    if state.target_queue:
        drained = target_queue.pop(0)
        target_meta, current_epoch = repair_target_entry(
            target_meta, current_epoch, drained, variant
        )

    return State(
        source_truth=source_truth,
        source_meta=source_meta,
        target_truth=target_truth,
        target_meta=target_meta,
        current_epoch=current_epoch,
        witness_epoch=witness_epoch,
        permission=permission,
        source_queue=tuple(source_queue),
        target_queue=tuple(target_queue),
        overflow=overflow,
    )


def reachable_states(variant: Variant, depth: int) -> dict[State, list[Event]]:
    start = State()
    frontier: list[tuple[State, list[Event]]] = [(start, [])]
    paths: dict[State, list[Event]] = {start: []}
    while frontier:
        state, path = frontier.pop(0)
        if len(path) >= depth:
            continue
        for event in EVENTS:
            nxt = step_state(state, event, variant)
            if nxt not in paths:
                new_path = path + [event]
                paths[nxt] = new_path
                frontier.append((nxt, new_path))
    return paths


def event_label(event: Event) -> str:
    if event.kind in {"commit_source", "dma_write", "chi_update"}:
        return f"{event.kind}(src={event.src})"
    if event.kind in {"record_target", "target_remap", "permission_downgrade", "permission_restore"}:
        return f"{event.kind}(token={event.token}, tgt={event.tgt})"
    if event.kind == "tlbi_token":
        return f"tlbi_token(token={event.token})"
    return event.kind


def path_text(path: list[Event]) -> str:
    if not path:
        return "(initial)"
    return " -> ".join(event_label(event) for event in path)


def query_label(query: Query) -> str:
    return (
        f"valid={int(query.valid)} src={query.src} "
        f"token={query.token} tgt={query.tgt}"
    )


def state_label(state: State) -> str:
    return (
        f"source_truth={list(state.source_truth)} source_meta={list(state.source_meta)} "
        f"target_truth={[list(row) for row in state.target_truth]} "
        f"target_meta={[list(row) for row in state.target_meta]} "
        f"current_epoch={[list(row) for row in state.current_epoch]} "
        f"witness_epoch={[list(row) for row in state.witness_epoch]} "
        f"permission={[list(row) for row in state.permission]} "
        f"source_queue={list(state.source_queue)} target_queue={list(state.target_queue)} "
        f"overflow={int(state.overflow)}"
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
    for state, path in paths.items():
        for event in EVENTS:
            for query in QUERIES:
                if not ground_truth_authorized(state, query):
                    continue
                if truth_hazard(state, event, query):
                    continue
                if variant_hold(state, event, query, FULL):
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
        "queued_target_revocation",
        "same_cycle_target_remap",
        "same_cycle_token_tlbi",
        "same_cycle_global_tlbi",
        "same_cycle_permission_downgrade",
    }
    cover: dict[str, tuple[State, list[Event], Event, Query]] = {}
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
    results = {}
    all_ok = True

    full_paths = reachable_states(FULL, MAX_DEPTH)
    cover = hazard_cover(full_paths, FULL)

    lines = [
        "# COPPER TLB/Coherence Authority Contract",
        "",
        "Date: 2026-06-17",
        "",
        "This bounded checker targets the production memory-system objection:",
        "a COPPER DMP issue must require live source proof, an exact target-line",
        "witness under the current address-space token, fresh remap/TLBI epoch,",
        "permission success, and no conflicting pending invalidation.",
        "",
        "Modeled contract:",
        "",
        "- committed source proof is separate from hardware source metadata",
        "- exact target-line witness metadata is separate from target ground truth",
        "- target remap, token TLBI, and global TLBI invalidate target truth and bump a witness epoch",
        "- DMA/CHI updates invalidate source truth through a bounded queue",
        "- same-cycle and queued revocations must hold conflicting DMP candidates",
        "- permission downgrade blocks target issue until permission is restored and demand revalidates authority",
        "",
        f"Model: {SRC_LINES} source lines, {TGT_LINES} target lines, {TOKENS} tokens,",
        f"revocation queue depth {QUEUE_DEPTH}, trace bound {MAX_DEPTH}.",
        "",
        f"Full-contract reachable states explored: {len(full_paths)}",
        "",
        "| Variant | Reachable states | Safety result | Precision result | Notes |",
        "|---|---:|---|---|---|",
    ]

    for variant in VARIANTS:
        paths = reachable_states(variant, MAX_DEPTH)
        cex = safety_counterexample(paths, variant)
        precision = precision_witness(paths, variant)
        overhold = overhold_witness(paths, variant)
        results[variant.name] = {
            "states": len(paths),
            "cex": cex,
            "precision": precision,
            "overhold": overhold,
        }

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
                    "no stale authority found; has unrelated-revocation precision witness "
                    f"at event={event_label(event)}, query={query_label(query)}"
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
                    f"unexpected stale issue reason={reason}; path={path_text(path)}; "
                    f"event={event_label(event)}; query={query_label(query)}"
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
    for hazard in sorted(cover):
        state, path, event, query = cover[hazard]
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

    precision = results[FULL.name]["precision"]
    if precision:
        state, path, event, query = precision
        lines.extend(
            [
                "## Precision Witness",
                "",
                "The full contract permits a valid candidate while an unrelated",
                "revocation exists. A global revocation hold would unnecessarily",
                "block it, but the conflict-scoped rule keeps the safe issue open.",
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
            "The full TLB/coherence contract has no bounded stale-authority",
            "counterexample and retains a precision witness against global",
            "revocation hold. Removing source pending hold, target remap/TLBI",
            "hold or clearing, permission gating, exact target-line witnessing,",
            "or queued-target hold produces a short counterexample. This artifact",
            "does not prove a commercial ARM memory hierarchy, but it turns the",
            "production-integration boundary into an executable rule with explicit",
            "weakened-variant failures.",
            "",
            f"Full contract status: {'PASS' if all_ok else 'FAIL'}",
            f"status={'PASS' if all_ok else 'FAIL'}",
            "",
        ]
    )

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)
    print(f"full_reachable_states={len(full_paths)}")
    print(f"covered_hazards={len(cover)}")
    print(f"status={'PASS' if all_ok else 'FAIL'}")
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
