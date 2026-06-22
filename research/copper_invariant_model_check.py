#!/usr/bin/env python3
"""Bounded invariant checker for COPPER PASB/CTLW authority rules."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class State:
    clean: bool = False
    proof: bool = False
    token_match: bool = True
    same_page: bool = True
    line_witness: bool = False
    terminal_source: bool = False
    issued_once: bool = False


@dataclass(frozen=True)
class Variant:
    name: str
    require_pasb: bool = True
    require_line_witness: bool = True
    enforce_terminal_stop: bool = True


CORRECT = Variant("COPPER_PASB_CTLW_TERMINAL")
NO_PASB = Variant("BUG_NO_PASB", require_pasb=False)
NO_CTLW = Variant("BUG_NO_CTLW", require_line_witness=False)
NO_TERMINAL = Variant("BUG_NO_TERMINAL", enforce_terminal_stop=False)


def can_issue(state: State, variant: Variant) -> bool:
    if not state.clean or not state.proof:
        return False
    if variant.require_pasb and not state.token_match:
        return False
    if variant.enforce_terminal_stop and state.terminal_source:
        return False
    if not state.same_page and variant.require_line_witness and not state.line_witness:
        return False
    return True


def unsafe_reason(state: State) -> str | None:
    if not state.clean:
        return "dirty_or_uninitialized_source"
    if not state.proof:
        return "no_committed_source_proof"
    if not state.token_match:
        return "address_space_token_mismatch"
    if state.terminal_source:
        return "witness_derived_terminal_source_chased"
    if not state.same_page and not state.line_witness:
        return "cross_page_target_without_exact_line_witness"
    return None


def successors(state: State, variant: Variant) -> list[tuple[str, State]]:
    out: list[tuple[str, State]] = []

    out.append(("demand_load_source_clean", State(
        clean=True,
        proof=state.proof,
        token_match=state.token_match,
        same_page=state.same_page,
        line_witness=state.line_witness,
        terminal_source=state.terminal_source,
        issued_once=state.issued_once,
    )))

    if state.clean and state.token_match:
        out.append(("commit_dependent_pointer_use", State(
            clean=True,
            proof=True,
            token_match=state.token_match,
            same_page=state.same_page,
            line_witness=state.line_witness,
            terminal_source=state.terminal_source,
            issued_once=state.issued_once,
        )))

    out.append(("write_or_fill_source", State(
        clean=False,
        proof=False,
        token_match=state.token_match,
        same_page=state.same_page,
        line_witness=state.line_witness,
        terminal_source=False,
        issued_once=state.issued_once,
    )))

    out.append(("context_switch_or_ttbr_change", State(
        clean=state.clean,
        proof=state.proof,
        token_match=False,
        same_page=state.same_page,
        line_witness=False,
        terminal_source=state.terminal_source,
        issued_once=state.issued_once,
    )))

    out.append(("context_restored_matching_token", State(
        clean=state.clean,
        proof=state.proof,
        token_match=True,
        same_page=state.same_page,
        line_witness=state.line_witness,
        terminal_source=state.terminal_source,
        issued_once=state.issued_once,
    )))

    out.append(("target_same_page", State(
        clean=state.clean,
        proof=state.proof,
        token_match=state.token_match,
        same_page=True,
        line_witness=state.line_witness,
        terminal_source=state.terminal_source,
        issued_once=state.issued_once,
    )))

    out.append(("target_cross_page", State(
        clean=state.clean,
        proof=state.proof,
        token_match=state.token_match,
        same_page=False,
        line_witness=state.line_witness,
        terminal_source=state.terminal_source,
        issued_once=state.issued_once,
    )))

    if state.token_match:
        out.append(("committed_target_line_witness", State(
            clean=state.clean,
            proof=state.proof,
            token_match=state.token_match,
            same_page=state.same_page,
            line_witness=True,
            terminal_source=state.terminal_source,
            issued_once=state.issued_once,
        )))

    out.append(("witness_evicted_or_invalidated", State(
        clean=state.clean,
        proof=state.proof,
        token_match=state.token_match,
        same_page=state.same_page,
        line_witness=False,
        terminal_source=state.terminal_source,
        issued_once=state.issued_once,
    )))

    if can_issue(state, variant):
        terminal = (not state.same_page) and state.line_witness
        out.append(("issue_dmp_prefetch", State(
            clean=True,
            proof=state.proof,
            token_match=state.token_match,
            same_page=state.same_page,
            line_witness=state.line_witness,
            terminal_source=terminal,
            issued_once=True,
        )))

    return out


def check_variant(variant: Variant, max_depth: int) -> tuple[bool, int, list[str]]:
    initial = State()
    queue = deque([(initial, [])])
    seen = {initial}
    explored = 0
    while queue:
        state, trace = queue.popleft()
        explored += 1
        if can_issue(state, variant):
            reason = unsafe_reason(state)
            if reason is not None:
                return False, explored, trace + [
                    f"UNSAFE_ISSUE reason={reason} state={state}"
                ]
        if len(trace) >= max_depth:
            continue
        for label, nxt in successors(state, variant):
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, trace + [label]))
    return True, explored, []


def main() -> None:
    rows = []
    for variant in (CORRECT, NO_PASB, NO_CTLW, NO_TERMINAL):
        ok, explored, trace = check_variant(variant, max_depth=10)
        rows.append((variant.name, ok, explored, trace))

    out = Path("research/results/COPPER_INVARIANT_MODEL_CHECK.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# COPPER PASB/CTLW Bounded Invariant Check",
        "",
        "Finite-state bounded search over source cleanliness, committed proof,",
        "address-space token match, same-page/cross-page target, exact target-line",
        "witness, and CTLW terminal-source state.",
        "",
        "| Variant | Result | States explored | Counterexample |",
        "|---|---:|---:|---|",
    ]
    for name, ok, explored, trace in rows:
        if ok:
            cx = "none within depth 10"
            result = "PASS"
        else:
            cx = " -> ".join(trace)
            result = "FAIL as expected" if name.startswith("BUG_") else "FAIL"
        lines.append(f"| {name} | {result} | {explored} | {cx} |")
    lines.extend([
        "",
        "Interpretation: the bounded model is not industrial formal signoff, but",
        "it checks that the proposed PASB/CTLW/terminal rules exclude the three",
        "known bad classes exposed during full-system testing: stale address-space",
        "proof reuse, cross-page recursion without an exact committed target-line",
        "witness, and recursive amplification from witness-derived terminal fills.",
        "",
    ])
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
