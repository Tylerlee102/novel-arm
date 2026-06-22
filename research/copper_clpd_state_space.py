#!/usr/bin/env python3
"""Bounded state-space checker for the COPPER CLPD representation.

CLPD compresses retained source proof by storing a per-source-line proof mask
and source-line epoch. This checker compares a small hardware-like directory
against a ground-truth committed-proof model and asks whether any DMP query can
be authorized without current committed source authority.

The model is intentionally tiny but exhaustive over the reachable state space:
three source lines, two direct-mapped entries, two words per line, two tokens,
and one-bit line epochs. It is not production formal signoff. Its purpose is to
make the CLPD invariant executable and to generate short counterexamples for
weakened CLPD variants.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path


LINES = 3
ENTRIES = 2
WORDS = 2
TOKENS = 2
MASK_ALL = (1 << WORDS) - 1


@dataclass(frozen=True)
class Entry:
    valid: bool = False
    tag: int = 0
    token: int = 0
    epoch: int = 0
    mask: int = 0


@dataclass(frozen=True)
class State:
    current_token: int = 0
    line_epoch: tuple[int, ...] = (0, 0, 0)
    truth_token: tuple[int, ...] = (0, 0, 0)
    truth_mask: tuple[int, ...] = (0, 0, 0)
    entries: tuple[Entry, ...] = (Entry(), Entry())


@dataclass(frozen=True)
class Variant:
    name: str
    check_tag: bool = True
    check_token: bool = True
    check_epoch: bool = True
    check_word_mask: bool = True
    clear_on_write: bool = True
    clear_on_fill: bool = True
    clear_on_invalidate: bool = True


VARIANTS = [
    Variant("COPPER_CLPD"),
    Variant("BUG_NO_TAG_CHECK", check_tag=False),
    Variant("BUG_NO_TOKEN_CHECK", check_token=False),
    Variant("BUG_NO_EPOCH_CHECK", check_epoch=False),
    Variant("BUG_LINE_PROOF_GRANTS_ALL_WORDS", check_word_mask=False),
    Variant("BUG_NO_WRITE_CLEAR", clear_on_write=False),
    Variant("BUG_NO_FILL_CLEAR", clear_on_fill=False),
    Variant("BUG_NO_INVALIDATE_CLEAR", clear_on_invalidate=False),
]


def idx(line: int) -> int:
    return line % ENTRIES


def replace_tuple(values: tuple[int, ...], index: int, value: int) -> tuple[int, ...]:
    out = list(values)
    out[index] = value
    return tuple(out)


def replace_entry(
    entries: tuple[Entry, ...],
    index: int,
    entry: Entry,
) -> tuple[Entry, ...]:
    out = list(entries)
    out[index] = entry
    return tuple(out)


def truth_authorized(state: State, line: int, word: int, token: int, epoch: int) -> bool:
    return (
        state.truth_token[line] == token
        and state.line_epoch[line] == epoch
        and bool(state.truth_mask[line] & (1 << word))
    )


def clpd_authorized(
    state: State,
    variant: Variant,
    line: int,
    word: int,
    src_token: int,
    target_token: int,
    epoch: int,
) -> bool:
    entry = state.entries[idx(line)]
    if not entry.valid:
        return False
    if variant.check_tag and entry.tag != line:
        return False
    if variant.check_epoch and entry.epoch != epoch:
        return False
    if variant.check_token and (entry.token != src_token or src_token != target_token):
        return False
    if variant.check_word_mask and not (entry.mask & (1 << word)):
        return False
    return True


def unsafe_query(state: State, variant: Variant) -> str | None:
    for line in range(LINES):
        for word in range(WORDS):
            for src_token in range(TOKENS):
                for target_token in range(TOKENS):
                    for epoch in range(2):
                        if not clpd_authorized(
                            state,
                            variant,
                            line,
                            word,
                            src_token,
                            target_token,
                            epoch,
                        ):
                            continue
                        if truth_authorized(state, line, word, src_token, epoch):
                            continue
                        reason = classify_unsafe(
                            state, line, word, src_token, target_token, epoch
                        )
                        return (
                            f"UNSAFE_CLPD_ISSUE reason={reason} "
                            f"query=(line={line}, word={word}, src_token={src_token}, "
                            f"target_token={target_token}, epoch={epoch}) state={state}"
                        )
    return None


def classify_unsafe(
    state: State,
    line: int,
    word: int,
    src_token: int,
    target_token: int,
    epoch: int,
) -> str:
    if src_token != target_token:
        return "source_target_token_mismatch"
    if state.line_epoch[line] != epoch:
        return "stale_source_line_epoch"
    if state.truth_token[line] != src_token:
        return "address_space_token_mismatch"
    if not (state.truth_mask[line] & (1 << word)):
        return "word_without_committed_source_proof"
    return "unknown_authority_mismatch"


def commit_word(state: State, line: int, word: int) -> State:
    line_i = idx(line)
    mask = state.truth_mask[line] | (1 << word)
    truth_mask = replace_tuple(state.truth_mask, line, mask)
    truth_token = replace_tuple(state.truth_token, line, state.current_token)

    entry = state.entries[line_i]
    if (
        entry.valid
        and entry.tag == line
        and entry.token == state.current_token
        and entry.epoch == state.line_epoch[line]
    ):
        new_entry = Entry(True, entry.tag, entry.token, entry.epoch, entry.mask | (1 << word))
    else:
        new_entry = Entry(True, line, state.current_token, state.line_epoch[line], 1 << word)
    entries = replace_entry(state.entries, line_i, new_entry)
    return State(
        current_token=state.current_token,
        line_epoch=state.line_epoch,
        truth_token=truth_token,
        truth_mask=truth_mask,
        entries=entries,
    )


def clear_directory_if_match(
    state: State,
    line: int,
    should_clear: bool,
) -> tuple[Entry, ...]:
    entries = state.entries
    if not should_clear:
        return entries
    line_i = idx(line)
    entry = entries[line_i]
    if entry.valid and entry.tag == line:
        entries = replace_entry(entries, line_i, Entry())
    return entries


def source_update(state: State, variant: Variant, line: int, kind: str) -> State:
    if kind == "write":
        should_clear = variant.clear_on_write
    elif kind == "fill":
        should_clear = variant.clear_on_fill
    elif kind == "invalidate":
        should_clear = variant.clear_on_invalidate
    else:
        raise ValueError(kind)

    line_epoch = replace_tuple(state.line_epoch, line, 1 - state.line_epoch[line])
    truth_mask = replace_tuple(state.truth_mask, line, 0)
    entries = clear_directory_if_match(state, line, should_clear)
    return State(
        current_token=state.current_token,
        line_epoch=line_epoch,
        truth_token=state.truth_token,
        truth_mask=truth_mask,
        entries=entries,
    )


def context_switch(state: State) -> State:
    return State(
        current_token=1 - state.current_token,
        line_epoch=state.line_epoch,
        truth_token=state.truth_token,
        truth_mask=state.truth_mask,
        entries=state.entries,
    )


def successors(state: State, variant: Variant) -> list[tuple[str, State]]:
    out: list[tuple[str, State]] = []

    for line in range(LINES):
        for word in range(WORDS):
            out.append((f"commit_word line={line} word={word}", commit_word(state, line, word)))

    for line in range(LINES):
        out.append((f"write_source_line line={line}", source_update(state, variant, line, "write")))
        out.append((f"fill_source_line line={line}", source_update(state, variant, line, "fill")))
        out.append((
            f"invalidate_source_line line={line}",
            source_update(state, variant, line, "invalidate"),
        ))

    out.append(("context_switch", context_switch(state)))
    return out


def check_variant(variant: Variant, max_depth: int) -> tuple[bool, int, list[str]]:
    initial = State()
    queue = deque([(initial, [])])
    seen = {initial}
    explored = 0

    while queue:
        state, trace = queue.popleft()
        explored += 1
        unsafe = unsafe_query(state, variant)
        if unsafe is not None:
            return False, explored, trace + [unsafe]
        if len(trace) >= max_depth:
            continue
        for label, nxt in successors(state, variant):
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, trace + [label]))

    return True, explored, []


def main() -> None:
    max_depth = 8
    rows = []
    for variant in VARIANTS:
        ok, explored, trace = check_variant(variant, max_depth)
        rows.append((variant.name, ok, explored, trace))

    out = Path("research/results/COPPER_CLPD_STATE_SPACE.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# COPPER CLPD State-Space Check",
        "",
        "Date: 2026-06-11",
        "",
        "This bounded exhaustive model checks the Compressed Line-Provenance",
        "Directory against a ground-truth committed-source-proof model. The",
        "state space uses three source lines, two direct-mapped directory",
        "entries, two words per line, two address-space tokens, and one-bit",
        "source-line epochs.",
        "",
        f"Search depth: {max_depth}",
        "",
        "| Variant | Result | States explored | Counterexample |",
        "|---|---:|---:|---|",
    ]

    for name, ok, explored, trace in rows:
        if ok:
            result = "PASS"
            cx = f"none within depth {max_depth}"
        else:
            result = "FAIL as expected" if name.startswith("BUG_") else "FAIL"
            cx = " -> ".join(trace)
        lines.append(f"| {name} | {result} | {explored:,} | {cx} |")

    lines.extend([
        "",
        "Interpretation: CLPD is safe in this bounded model when line tags,",
        "source-line epochs, source/target tokens, per-word proof masks, and",
        "write/fill/invalidate clearing are enforced. Weakened variants produce",
        "short counterexamples for aliasing without tag checks, token reuse,",
        "stale source-line epochs, whole-line proof overreach, and missed",
        "destructive source-line events.",
        "",
    ])

    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
