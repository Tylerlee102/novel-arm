#!/usr/bin/env python3
"""Bounded checker for SCOOP slack-only companion prefetch arbitration."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "results" / "SCOOP_COMPANION_STATE_SPACE.md"


@dataclass(frozen=True)
class State:
    last_primary: int
    issued_primary: int
    issued_companion: int
    cycles: int


def choose(policy: str, primary_ready: bool, companion_ready: bool, last_primary: int) -> tuple[str, int]:
    if policy == "scoop":
        if primary_ready:
            return "primary", 1
        if companion_ready:
            return "companion", 0
        return "none", last_primary
    if policy == "companion_first":
        if companion_ready:
            return "companion", 0
        if primary_ready:
            return "primary", 1
        return "none", last_primary
    if policy == "round_robin":
        if primary_ready and companion_ready:
            if last_primary:
                return "companion", 0
            return "primary", 1
        if primary_ready:
            return "primary", 1
        if companion_ready:
            return "companion", 0
        return "none", last_primary
    raise ValueError(policy)


def check(policy: str, depth: int) -> tuple[bool, int, list[str]]:
    start = State(last_primary=0, issued_primary=0, issued_companion=0, cycles=0)
    todo: deque[tuple[State, list[str]]] = deque([(start, [])])
    seen = {start}
    explored = 0
    while todo:
        state, trace = todo.popleft()
        explored += 1
        if state.cycles == depth:
            continue
        for primary_ready in (False, True):
            for companion_ready in (False, True):
                selected, last_primary = choose(
                    policy, primary_ready, companion_ready, state.last_primary
                )
                step = (
                    f"p={int(primary_ready)} c={int(companion_ready)}"
                    f" -> {selected}"
                )
                if primary_ready and selected == "companion":
                    return False, explored, trace + [step]
                next_state = State(
                    last_primary=last_primary,
                    issued_primary=state.issued_primary + (selected == "primary"),
                    issued_companion=state.issued_companion
                    + (selected == "companion"),
                    cycles=state.cycles + 1,
                )
                if next_state not in seen:
                    seen.add(next_state)
                    todo.append((next_state, trace + [step]))
    return True, explored, []


def main() -> None:
    depth = 10
    policies = ["scoop", "companion_first", "round_robin"]
    lines = [
        "# SCOOP Companion Arbitration State-Space Check",
        "",
        "Invariant: when the primary conventional lane has a ready prefetch,",
        "the COPPER companion lane must not issue. COPPER may issue only in",
        "primary slack cycles.",
        "",
        f"Depth: {depth} cycles.",
        "",
        "| Policy | Result | States explored before result | Counterexample |",
        "|---|---:|---:|---|",
    ]
    failures = 0
    for policy in policies:
        ok, explored, trace = check(policy, depth)
        if policy == "scoop":
            failures += 0 if ok else 1
        else:
            failures += 0 if not ok else 1
        lines.append(
            f"| {policy} | {'PASS' if ok else 'FAIL as expected'} | "
            f"{explored} | {'; '.join(trace) if trace else ''} |"
        )
    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            "- SCOOP passes because primary-ready cycles always select the primary lane.",
            "- Companion-first and round-robin variants fail because they can issue COPPER while the conventional primary lane is ready.",
            "",
            f"status={'PASS' if failures == 0 else 'FAIL'}",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
