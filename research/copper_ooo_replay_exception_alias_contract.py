#!/usr/bin/env python3
"""Bounded replay/exception/alias contract checker for COPPER ROPL.

ROPL here means Retirement-Only Provenance Latching: a backend may latch a
COPPER source proof only when the dependent memory operation reaches retirement
with a live source tag that survived replay, squash, exception, alias, memory
ordering, and target permission checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "results" / "COPPER_OOO_REPLAY_EXCEPTION_ALIAS_CONTRACT.md"


@dataclass(frozen=True)
class State:
    src_executed: bool = False
    src_retired: bool = False
    src_exception: bool = False
    dep_executed: bool = False
    dep_retired: bool = False
    dep_exception: bool = False
    tag_live: bool = False
    tag_stale: bool = False
    tag_replay_gen: int = 0
    dep_replay_gen: int = 0
    tag_squash_epoch: int = 0
    squash_epoch: int = 0
    tag_alias_gen: int = 0
    alias_gen: int = 0
    order_violation: bool = False
    target_ok: bool = True
    perm_ok: bool = True
    proof_created: bool = False


@dataclass(frozen=True)
class Variant:
    name: str
    proof_at_execute: bool = False
    require_source_retired: bool = True
    require_exception_clear: bool = True
    require_replay_generation: bool = True
    require_squash_epoch: bool = True
    require_alias_generation: bool = True
    require_order_clear: bool = True
    require_translation_permission: bool = True


FULL = Variant("FULL_ROPL_CONTRACT")
VARIANTS = [
    FULL,
    Variant("BUG_EXECUTE_STAGE_PROOF", proof_at_execute=True, require_source_retired=False),
    Variant("BUG_SOURCE_NOT_RETIRED", require_source_retired=False),
    Variant("BUG_NO_EXCEPTION_QUARANTINE", require_exception_clear=False),
    Variant("BUG_NO_REPLAY_GENERATION", require_replay_generation=False),
    Variant("BUG_NO_SQUASH_EPOCH", require_squash_epoch=False),
    Variant("BUG_NO_ALIAS_GENERATION", require_alias_generation=False),
    Variant("BUG_NO_ORDER_VIOLATION_CLEAR", require_order_clear=False),
    Variant("BUG_NO_TRANSLATION_PERMISSION_GATE", require_translation_permission=False),
]


def sound_authority(state: State, at_commit: bool) -> bool:
    return (
        at_commit
        and state.src_executed
        and state.src_retired
        and not state.src_exception
        and state.dep_executed
        and not state.dep_retired
        and not state.dep_exception
        and state.tag_live
        and not state.tag_stale
        and state.tag_replay_gen == state.dep_replay_gen
        and state.tag_squash_epoch == state.squash_epoch
        and state.tag_alias_gen == state.alias_gen
        and not state.order_violation
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

    if not state.tag_live or state.tag_stale:
        return False
    if variant.require_source_retired and not state.src_retired:
        return False
    if variant.require_exception_clear and (state.src_exception or state.dep_exception):
        return False
    if variant.require_replay_generation and state.tag_replay_gen != state.dep_replay_gen:
        return False
    if variant.require_squash_epoch and state.tag_squash_epoch != state.squash_epoch:
        return False
    if variant.require_alias_generation and state.tag_alias_gen != state.alias_gen:
        return False
    if variant.require_order_clear and state.order_violation:
        return False
    if variant.require_translation_permission and (not state.target_ok or not state.perm_ok):
        return False
    return True


def replace(state: State, **kwargs: object) -> State:
    return State(**{**state.__dict__, **kwargs})


def actions(state: State, variant: Variant) -> list[tuple[str, State, bool, str, State]]:
    out: list[tuple[str, State, bool, str, State]] = []

    def add(
        name: str,
        next_state: State,
        stage: str = "none",
        proof_state: State | None = None,
    ) -> None:
        candidate = proof_state if proof_state is not None else next_state
        proof = variant_allows_proof(candidate, variant, stage)
        if proof:
            next_state = replace(next_state, proof_created=True)
        out.append((name, next_state, proof, stage, candidate))

    if not state.src_executed:
        add(
            "execute_source_capture_ropl_tag",
            replace(
                state,
                src_executed=True,
                tag_live=True,
                tag_stale=False,
                tag_replay_gen=state.dep_replay_gen,
                tag_squash_epoch=state.squash_epoch,
                tag_alias_gen=state.alias_gen,
            ),
        )

    if state.src_executed and not state.src_retired and not state.src_exception:
        add("retire_source_load", replace(state, src_retired=True))

    if state.src_executed and not state.src_retired and not state.src_exception:
        add("source_exception_before_retire", replace(state, src_exception=True))

    if state.tag_live and not state.dep_executed:
        add("execute_dependent_memory", replace(state, dep_executed=True), stage="execute")

    if state.dep_executed and not state.dep_retired:
        add(
            "retire_dependent_memory",
            replace(state, dep_retired=True),
            stage="commit",
            proof_state=state,
        )

    if state.dep_executed and not state.dep_retired and not state.dep_exception:
        add("dependent_exception_before_retire", replace(state, dep_exception=True))

    if state.dep_executed and not state.dep_retired:
        add(
            "dependent_replay",
            replace(state, dep_executed=False, dep_replay_gen=state.dep_replay_gen ^ 1),
        )

    if state.tag_live:
        add("backend_squash_epoch_advance", replace(state, squash_epoch=state.squash_epoch ^ 1))

    if state.tag_live:
        add("same_line_store_alias_kill", replace(state, alias_gen=state.alias_gen ^ 1))

    if state.dep_executed and not state.dep_retired:
        add("memory_order_violation", replace(state, order_violation=True))

    if state.target_ok:
        add("target_translation_fault", replace(state, target_ok=False))

    if state.perm_ok:
        add("target_permission_fault", replace(state, perm_ok=False))

    return out


def check_variant(variant: Variant, depth: int = 8) -> dict[str, object]:
    start = State()
    frontier: list[tuple[State, tuple[str, ...]]] = [(start, ())]
    seen = {start}
    legal = 0
    unsafe = 0
    first_legal: tuple[str, ...] | None = None
    first_unsafe: tuple[str, ...] | None = None

    while frontier:
        state, trace = frontier.pop(0)
        if len(trace) >= depth:
            continue
        for name, nxt, proof, stage, proof_state in actions(state, variant):
            next_trace = trace + (name,)
            if proof:
                if sound_authority(proof_state, stage == "commit"):
                    legal += 1
                    if first_legal is None:
                        first_legal = next_trace
                else:
                    unsafe += 1
                    if first_unsafe is None:
                        first_unsafe = next_trace
            if nxt not in seen:
                seen.add(nxt)
                frontier.append((nxt, next_trace))

    return {
        "unique_states": len(seen),
        "legal_proofs": legal,
        "unsafe_proofs": unsafe,
        "first_legal": first_legal,
        "first_unsafe": first_unsafe,
    }


def trace_text(trace: tuple[str, ...] | None) -> str:
    return "-" if trace is None else " -> ".join(trace)


def main() -> None:
    results = {variant.name: check_variant(variant) for variant in VARIANTS}
    full = results[FULL.name]
    weakened_fail = all(results[v.name]["unsafe_proofs"] for v in VARIANTS if v is not FULL)
    status = (
        "PASS"
        if full["unsafe_proofs"] == 0 and full["legal_proofs"] and weakened_fail
        else "FAIL"
    )
    lines = [
        "# COPPER ROPL Replay/Exception/Alias Contract",
        "",
        "Date: 2026-06-19",
        "",
        "ROPL means Retirement-Only Provenance Latching. It is the backend rule",
        "that COPPER source proofs are latched only at dependent-memory retirement",
        "after replay, squash, exception, alias, memory-order, translation, and",
        "permission hazards have been quarantined. This is a bounded public model,",
        "not a proprietary ARM backend.",
        "",
        "Sound ROPL invariant:",
        "",
        "- the dependent memory operation is at retirement, not execute",
        "- the source load is older, executed, retired, and exception-free",
        "- the dependent memory operation is exception-free",
        "- the carried source tag is live and not stale",
        "- replay generation, squash epoch, and same-line alias generation still match",
        "- no memory-order violation is pending",
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
            f"- Full ROPL contract status: {status}.",
            "- The full contract has reachable legal proof creation and zero bounded unsafe proof creations.",
            "- Every weakened variant has a short counterexample, so the replay/exception/alias checks are not cosmetic.",
            "- This closes a paper-facing integration ambiguity, but it is still not an end-to-end proof of a production ARM load-store queue.",
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
