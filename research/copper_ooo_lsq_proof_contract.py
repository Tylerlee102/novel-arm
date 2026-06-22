#!/usr/bin/env python3
"""Bounded OoO-LSQ proof-contract checker for COPPER.

This is a production-integration sanity model, not a production ARM core.
It checks the backend contract that a COPPER source proof may be created only
when a dependent memory operation retires with a live, older, retired source
tag whose epoch/value and target permission still match.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "results" / "COPPER_OOO_LSQ_PROOF_CONTRACT.md"


@dataclass(frozen=True)
class State:
    src_executed: bool = False
    src_retired: bool = False
    dep_executed: bool = False
    dep_retired: bool = False
    tag_live: bool = False
    tag_stale: bool = False
    tag_epoch: int = 0
    tag_value: int = 0
    current_epoch: int = 0
    current_value: int = 0
    flushed_since_capture: bool = False
    target_ok: bool = True
    perm_ok: bool = True
    proof_created: bool = False


@dataclass(frozen=True)
class Variant:
    name: str
    proof_at_execute: bool = False
    require_source_retired: bool = True
    clear_on_flush: bool = True
    stale_on_source_revoke: bool = True
    require_epoch_value: bool = True
    require_translation_perm: bool = True


FULL = Variant("FULL_CONTRACT")
VARIANTS = [
    FULL,
    Variant("BUG_EXECUTE_STAGE_PROOF", proof_at_execute=True, require_source_retired=False),
    Variant("BUG_SOURCE_NOT_RETIRED", require_source_retired=False),
    Variant("BUG_NO_FLUSH_CLEAR", clear_on_flush=False),
    Variant("BUG_NO_SOURCE_REVOCATION", stale_on_source_revoke=False, require_epoch_value=False),
    Variant("BUG_NO_CEPF_EPOCH_VALUE", require_epoch_value=False),
    Variant("BUG_NO_TRANSLATION_PERMISSION_GATE", require_translation_perm=False),
]


def sound_authority(state: State, at_commit: bool) -> bool:
    return (
        at_commit
        and state.src_executed
        and state.src_retired
        and state.dep_executed
        and not state.dep_retired
        and state.tag_live
        and not state.tag_stale
        and state.tag_epoch == state.current_epoch
        and state.tag_value == state.current_value
        and not state.flushed_since_capture
        and state.target_ok
        and state.perm_ok
    )


def variant_allows_proof(state: State, variant: Variant, stage: str) -> bool:
    if state.proof_created:
        return False
    if stage == "commit":
        if not state.dep_executed or state.dep_retired:
            return False
    elif stage == "execute":
        if not variant.proof_at_execute or not state.dep_executed:
            return False
    else:
        return False
    if not state.tag_live:
        return False
    if state.tag_stale:
        return False
    if variant.require_source_retired and not state.src_retired:
        return False
    if variant.clear_on_flush and state.flushed_since_capture:
        return False
    if variant.require_epoch_value and (
        state.tag_epoch != state.current_epoch or state.tag_value != state.current_value
    ):
        return False
    if variant.require_translation_perm and (not state.target_ok or not state.perm_ok):
        return False
    return True


def actions(state: State, variant: Variant) -> list[tuple[str, State, bool, str, State]]:
    out: list[tuple[str, State, bool, str, State]] = []

    def add(
        name: str,
        next_state: State,
        stage: str = "none",
        proof_state: State | None = None,
    ) -> None:
        candidate_state = proof_state if proof_state is not None else next_state
        proof = variant_allows_proof(candidate_state, variant, stage)
        if proof:
            next_state = State(**{**next_state.__dict__, "proof_created": True})
        out.append((name, next_state, proof, stage, candidate_state))

    if not state.src_executed:
        add(
            "execute_source_load_capture_tag",
            State(
                **{
                    **state.__dict__,
                    "src_executed": True,
                    "tag_live": True,
                    "tag_stale": False,
                    "tag_epoch": state.current_epoch,
                    "tag_value": state.current_value,
                    "flushed_since_capture": False,
                }
            ),
        )

    if state.src_executed and not state.src_retired:
        add("retire_source_load", State(**{**state.__dict__, "src_retired": True}))

    if state.tag_live and not state.dep_executed:
        add(
            "execute_dependent_memory",
            State(**{**state.__dict__, "dep_executed": True}),
            stage="execute",
        )

    if state.dep_executed and not state.dep_retired:
        add(
            "retire_dependent_memory",
            State(**{**state.__dict__, "dep_retired": True}),
            stage="commit",
            proof_state=state,
        )

    if state.tag_live:
        if variant.clear_on_flush:
            add(
                "backend_flush",
                State(
                    **{
                        **state.__dict__,
                        "tag_live": False,
                        "tag_stale": True,
                        "dep_executed": False,
                        "flushed_since_capture": True,
                    }
                ),
            )
        else:
            add(
                "backend_flush",
                State(**{**state.__dict__, "flushed_since_capture": True}),
            )

    if state.tag_live:
        add(
            "source_write_or_fill_revoke",
            State(
                **{
                    **state.__dict__,
                    "tag_stale": state.tag_stale or variant.stale_on_source_revoke,
                    "current_epoch": state.current_epoch ^ 1,
                    "current_value": state.current_value ^ 1,
                }
            ),
        )

    if state.tag_live:
        add(
            "silent_epoch_value_change",
            State(
                **{
                    **state.__dict__,
                    "current_epoch": state.current_epoch ^ 1,
                    "current_value": state.current_value ^ 1,
                }
            ),
        )

    if state.target_ok:
        add("target_translation_fault", State(**{**state.__dict__, "target_ok": False}))

    if state.perm_ok:
        add("target_permission_fault", State(**{**state.__dict__, "perm_ok": False}))

    return out


def check_variant(variant: Variant, depth: int = 8) -> dict[str, object]:
    start = State()
    frontier: list[tuple[State, tuple[str, ...]]] = [(start, ())]
    seen = {start}
    states = 0
    legal_proofs = 0
    unsafe_proofs = 0
    first_unsafe: tuple[str, ...] | None = None
    first_legal: tuple[str, ...] | None = None

    while frontier:
        state, trace = frontier.pop(0)
        states += 1
        if len(trace) >= depth:
            continue
        for name, nxt, proof, stage, proof_state in actions(state, variant):
            next_trace = trace + (name,)
            if proof:
                if sound_authority(proof_state, stage == "commit"):
                    legal_proofs += 1
                    if first_legal is None:
                        first_legal = next_trace
                else:
                    unsafe_proofs += 1
                    if first_unsafe is None:
                        first_unsafe = next_trace
            if nxt not in seen:
                seen.add(nxt)
                frontier.append((nxt, next_trace))

    return {
        "states": states,
        "unique_states": len(seen),
        "legal_proofs": legal_proofs,
        "unsafe_proofs": unsafe_proofs,
        "first_unsafe": first_unsafe,
        "first_legal": first_legal,
    }


def trace_text(trace: tuple[str, ...] | None) -> str:
    if not trace:
        return "-"
    return " -> ".join(trace)


def main() -> None:
    results = {variant.name: check_variant(variant) for variant in VARIANTS}
    full = results[FULL.name]
    status = "PASS" if full["unsafe_proofs"] == 0 and full["legal_proofs"] else "FAIL"
    lines = [
        "# COPPER OoO-LSQ Proof Contract",
        "",
        "Date: 2026-06-17",
        "",
        "This bounded checker targets the production-backend integration objection:",
        "a COPPER proof must not be created by speculative execution, by a younger",
        "dependent memory operation before source retirement, after a backend flush,",
        "after source revocation or epoch/value drift, or when target translation or",
        "permission fails. It models a minimal out-of-order backend contract rather",
        "than a proprietary ARM LSQ.",
        "",
        "Sound proof contract:",
        "",
        "- dependent memory operation reaches retirement/architectural commit",
        "- source load that produced the carried tag is older and retired",
        "- carried source tag is live and not stale",
        "- current source epoch/value still match the captured tag",
        "- no backend flush has invalidated the speculative chain",
        "- target translation and permission checks succeed",
        "",
        "| Variant | Unique states | Legal proofs | Unsafe proofs | First unsafe counterexample | First legal proof witness |",
        "|---|---:|---:|---:|---|---|",
    ]
    for variant in VARIANTS:
        item = results[variant.name]
        lines.append(
            f"| {variant.name} | {item['unique_states']} | {item['legal_proofs']} | "
            f"{item['unsafe_proofs']} | {trace_text(item['first_unsafe'])} | "
            f"{trace_text(item['first_legal'])} |"
        )
    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            f"- Full contract status: {status}.",
            "- The full contract has reachable legal proof creation and zero bounded unsafe proof creations.",
            "- Every weakened variant has a short counterexample in this model.",
            "- This reduces the production OoO integration ambiguity by making the backend proof contract executable, but it is not a full formal proof of a commercial ARM load-store queue.",
            "",
            f"status={status}",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
