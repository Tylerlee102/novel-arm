#!/usr/bin/env python3
"""Richer bounded state-space checker for COPPER authority.

This model is deliberately small enough to exhaustively search, but richer than
the first PASB/CTLW checker. It tracks:

- source word value and epoch;
- whether proof was created from a sound committed dependency;
- address-space token binding;
- exact target-line witness matching;
- witness invalidation after a target remap;
- CTLW terminal-source behavior; and
- a backend in-flight source tag for CEPF.

The checker is not industrial formal signoff. Its purpose is to make the paper's
authority invariant precise and to show short counterexamples for weakened
variants.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class State:
    src_clean: bool = False
    src_value: int = 0
    src_epoch: int = 0
    current_token: int = 0

    proof_valid: bool = False
    proof_value: int = 0
    proof_epoch: int = 0
    proof_token: int = 0
    proof_sound: bool = False

    inflight_valid: bool = False
    inflight_value: int = 0
    inflight_epoch: int = 0
    inflight_token: int = 0

    target_same_page: bool = True
    candidate_target: int = 0
    witness_valid: bool = False
    witness_target: int = 0
    witness_token: int = 0
    terminal_source: bool = False
    issued_once: bool = False


@dataclass(frozen=True)
class Variant:
    name: str
    require_cepf: bool = True
    clear_proof_on_source_update: bool = True
    require_exact_source: bool = True
    require_pasb: bool = True
    require_ctlw: bool = True
    require_exact_witness: bool = True
    invalidate_witness_on_remap: bool = True
    enforce_terminal_stop: bool = True


VARIANTS = [
    Variant("COPPER_FULL_AUTHORITY"),
    Variant("BUG_NO_CEPF", require_cepf=False),
    Variant(
        "BUG_LINE_PROOF_MISSED_SOURCE_INVALIDATE",
        clear_proof_on_source_update=False,
        require_exact_source=False,
    ),
    Variant("BUG_NO_PASB", require_pasb=False),
    Variant("BUG_NO_CTLW", require_ctlw=False),
    Variant("BUG_PAGE_LEVEL_WITNESS", require_exact_witness=False),
    Variant(
        "BUG_STALE_PAGE_WITNESS_AFTER_REMAP",
        require_exact_witness=False,
        invalidate_witness_on_remap=False,
    ),
    Variant("BUG_NO_TERMINAL", enforce_terminal_stop=False),
]


def source_exact(state: State) -> bool:
    return (
        state.proof_value == state.src_value
        and state.proof_epoch == state.src_epoch
    )


def witness_exact(state: State) -> bool:
    return (
        state.witness_valid
        and state.witness_target == state.candidate_target
        and state.witness_token == state.current_token
    )


def can_issue(state: State, variant: Variant) -> bool:
    if not state.src_clean or not state.proof_valid:
        return False
    if variant.require_exact_source and not source_exact(state):
        return False
    if variant.require_pasb and state.proof_token != state.current_token:
        return False
    if variant.enforce_terminal_stop and state.terminal_source:
        return False
    if not state.target_same_page and variant.require_ctlw:
        if variant.require_exact_witness:
            if not witness_exact(state):
                return False
        elif not state.witness_valid:
            return False
    return True


def unsafe_reason(state: State) -> str | None:
    if not state.src_clean:
        return "dirty_or_uninitialized_source"
    if not state.proof_valid:
        return "no_committed_source_proof"
    if not state.proof_sound:
        return "proof_created_from_stale_backend_tag"
    if not source_exact(state):
        return "source_value_or_epoch_mismatch"
    if state.proof_token != state.current_token:
        return "address_space_token_mismatch"
    if state.terminal_source:
        return "witness_derived_terminal_source_chased"
    if not state.target_same_page and not witness_exact(state):
        return "cross_page_target_without_exact_live_line_witness"
    return None


def replace(
    state: State,
    **kwargs: object,
) -> State:
    values = state.__dict__.copy()
    values.update(kwargs)
    return State(**values)


def source_update(state: State, variant: Variant, label: str) -> tuple[str, State]:
    next_value = 1 - state.src_value
    next_epoch = 1 - state.src_epoch
    kwargs: dict[str, object] = {
        "src_clean": False if variant.clear_proof_on_source_update else state.src_clean,
        "src_value": next_value,
        "src_epoch": next_epoch,
        "terminal_source": False,
    }
    if variant.clear_proof_on_source_update:
        kwargs.update({
            "proof_valid": False,
            "proof_sound": False,
        })
    return label, replace(state, **kwargs)


def successors(state: State, variant: Variant) -> list[tuple[str, State]]:
    out: list[tuple[str, State]] = []

    out.append(("demand_load_source_current_word", replace(
        state,
        src_clean=True,
        terminal_source=False,
    )))

    out.append(("capture_source_tag_for_backend_commit", replace(
        state,
        inflight_valid=state.src_clean,
        inflight_value=state.src_value,
        inflight_epoch=state.src_epoch,
        inflight_token=state.current_token,
    )))

    if state.inflight_valid:
        cepf_match = (
            state.src_clean
            and state.inflight_value == state.src_value
            and state.inflight_epoch == state.src_epoch
            and state.inflight_token == state.current_token
        )
        if cepf_match or not variant.require_cepf:
            out.append(("commit_dependent_pointer_use", replace(
                state,
                proof_valid=True,
                proof_value=state.src_value,
                proof_epoch=state.src_epoch,
                proof_token=state.current_token,
                proof_sound=cepf_match,
                inflight_valid=False,
            )))
        out.append(("squash_or_exception_clears_inflight_tag", replace(
            state,
            inflight_valid=False,
        )))

    out.append(source_update(state, variant, "store_or_fill_updates_source_word"))
    out.append(source_update(state, variant, "coherence_or_dma_updates_source_word"))

    out.append(("context_switch_to_other_address_space", replace(
        state,
        current_token=1 - state.current_token,
        witness_valid=False if variant.invalidate_witness_on_remap else state.witness_valid,
    )))

    out.append(("target_same_page", replace(state, target_same_page=True)))
    out.append(("target_cross_page", replace(state, target_same_page=False)))
    out.append(("candidate_target_changes", replace(
        state,
        candidate_target=1 - state.candidate_target,
    )))

    out.append(("committed_demand_target_line_witness", replace(
        state,
        witness_valid=True,
        witness_target=state.candidate_target,
        witness_token=state.current_token,
    )))

    out.append(("target_remap_or_tlbi", replace(
        state,
        candidate_target=1 - state.candidate_target,
        witness_valid=False if variant.invalidate_witness_on_remap else state.witness_valid,
    )))

    out.append(("witness_evicted", replace(state, witness_valid=False)))

    if can_issue(state, variant):
        terminal = (not state.target_same_page) and state.witness_valid
        out.append(("issue_dmp_prefetch", replace(
            state,
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
    max_depth = 12
    rows = []
    for variant in VARIANTS:
        ok, explored, trace = check_variant(variant, max_depth=max_depth)
        rows.append((variant.name, ok, explored, trace))

    out = Path("research/results/COPPER_AUTHORITY_STATE_SPACE.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# COPPER Authority State-Space Check",
        "",
        "Date: 2026-06-11",
        "",
        "This bounded exhaustive model strengthens the earlier PASB/CTLW checker",
        "by adding source values, source epochs, a CEPF-like in-flight backend",
        "source tag, proof soundness, address-space tokens, exact target-line",
        "witnesses, witness invalidation, and terminal witness-derived fills.",
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
        "Interpretation: this remains a bounded research checker, not a proof of",
        "a production RTL implementation. Its value is that the major weakened",
        "mechanism classes have short executable counterexamples: stale backend",
        "proof without CEPF, line-resident proof with missed source invalidation,",
        "address-space proof reuse, cross-page issue without CTLW, page-level",
        "rather than exact target-line witnessing, stale page-witness reuse after",
        "remap/TLBI, and recursive amplification from terminal witness-derived",
        "fills. Some individual sub-rules are intentionally redundant with",
        "others; the checker models unsafe combinations rather than claiming",
        "every bit is independently necessary.",
        "",
    ])

    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
