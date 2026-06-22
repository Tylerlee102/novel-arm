#!/usr/bin/env python3
"""Trace-driven COPPER policy simulator."""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import csv
from collections import OrderedDict
from pathlib import Path
from statistics import mean


MISS = 100
HIT = 4
PREFETCH_HIT = 8

POLICIES = ("disabled", "naive", "copper_value", "copper_line", "copper_stream")


@dataclass(frozen=True)
class Event:
    cycle: int
    event: str
    stream: int
    domain: int
    addr: int
    src_line: int
    src_word: int
    candidate: int
    src_domain: int
    target_domain: int
    committed: bool
    translation_ok: bool
    permission_ok: bool
    tag: str


class PolicyState:
    def __init__(
        self,
        policy: str,
        cache_lines: int,
        value_entries: int,
        stream_threshold: int,
        dirty_entries: int,
    ) -> None:
        self.policy = policy
        self.cache_lines = cache_lines
        self.value_entries = value_entries
        self.stream_threshold = stream_threshold
        self.dirty_entries = dirty_entries

        self.cache: OrderedDict[int, None] = OrderedDict()
        self.value_table: OrderedDict[tuple[int, int, int, int], None] = OrderedDict()
        self.line_clean: set[tuple[int, int, int]] = set()
        self.true_value: set[tuple[int, int, int, int]] = set()
        self.true_line_clean: set[tuple[int, int, int]] = set()

        self.stream_counts: dict[int, int] = {}
        self.stream_trained: set[int] = set()
        self.stream_dirty: OrderedDict[tuple[int, int, int], None] = OrderedDict()
        self.stream_dirty_overflow = False

        self.cycles = 0
        self.demand_misses = 0
        self.prefetches = 0
        self.data_at_rest_prefetches = 0
        self.cross_domain_prefetches = 0
        self.unproven_value_prefetches = 0
        self.unproven_line_prefetches = 0
        self.blocked_permission = 0
        self.blocked_dirty = 0
        self.blocked_untrained = 0
        self.blocked_unproven = 0
        self.blocked_inconsistent = 0

    def _touch_cache(self, addr: int) -> bool:
        hit = addr in self.cache
        if hit:
            self.cache.move_to_end(addr)
        else:
            self.cache[addr] = None
            if len(self.cache) > self.cache_lines:
                self.cache.popitem(last=False)
        return hit

    def _remember_value(self, key: tuple[int, int, int, int]) -> None:
        if self.value_entries <= 0:
            return
        self.value_table[key] = None
        self.value_table.move_to_end(key)
        if len(self.value_table) > self.value_entries:
            self.value_table.popitem(last=False)

    def _remember_dirty(self, key: tuple[int, int, int]) -> None:
        if key in self.stream_dirty:
            self.stream_dirty.move_to_end(key)
            return
        if self.dirty_entries <= 0 or len(self.stream_dirty) >= self.dirty_entries:
            self.stream_dirty_overflow = True
            return
        self.stream_dirty[key] = None

    def _prove(self, event: Event) -> None:
        if event.src_line < 0 or event.candidate != event.addr:
            return
        line_key = (event.src_line, event.src_word, event.domain)
        value_key = (event.src_line, event.src_word, event.addr, event.domain)
        self.true_line_clean.add(line_key)
        self.true_value.add(value_key)
        self.line_clean.add(line_key)
        self._remember_value(value_key)
        self.stream_dirty.pop(line_key, None)
        self.stream_counts[event.stream] = self.stream_counts.get(event.stream, 0) + 1

    def _dirty_source(self, event: Event) -> None:
        if event.src_line < 0:
            return
        line_key = (event.src_line, event.src_word, event.src_domain)
        # A physical write/coherence event invalidates the word regardless of
        # which protection-domain proof created it. This is conservative and
        # matches the intended line-resident clean-provenance lifecycle.
        self.line_clean = {
            key for key in self.line_clean if key[:2] != (event.src_line, event.src_word)
        }
        self.true_line_clean = {
            key for key in self.true_line_clean if key[:2] != (event.src_line, event.src_word)
        }
        self.true_value = {key for key in self.true_value if key[:2] != (event.src_line, event.src_word)}
        self.value_table = OrderedDict(
            (key, value)
            for key, value in self.value_table.items()
            if key[:2] != (event.src_line, event.src_word)
        )
        self._remember_dirty(line_key)

    def process(self, event: Event) -> None:
        if event.event == "EPOCH":
            for stream, count in self.stream_counts.items():
                if count >= self.stream_threshold:
                    self.stream_trained.add(stream)
            return

        if event.event in ("WRITE", "COH"):
            self._dirty_source(event)
            return

        if event.event == "DEMAND":
            if self._touch_cache(event.addr):
                self.cycles += HIT
            else:
                self.cycles += MISS
                self.demand_misses += 1
            if event.committed:
                self._prove(event)
            return

        if event.event != "DMP":
            raise ValueError(f"unknown event {event.event}")

        self._process_dmp(event)

    def _process_dmp(self, event: Event) -> None:
        if self.policy == "disabled":
            return

        value_key = (event.src_line, event.src_word, event.candidate, event.domain)
        line_key = (event.src_line, event.src_word, event.domain)
        allowed = False
        blocked_by_dirty = False
        blocked_by_untrained = False
        blocked_by_unproven = False

        if self.policy == "naive":
            allowed = True
        elif self.policy == "copper_value":
            allowed = value_key in self.value_table
            blocked_by_unproven = not allowed
        elif self.policy == "copper_line":
            allowed = line_key in self.line_clean and value_key in self.true_value
            blocked_by_unproven = not allowed
        elif self.policy == "copper_stream":
            blocked_by_untrained = event.stream not in self.stream_trained
            blocked_by_dirty = line_key in self.stream_dirty or self.stream_dirty_overflow
            allowed = (
                event.src_line >= 0
                and not blocked_by_untrained
                and not blocked_by_dirty
            )
        else:
            raise ValueError(self.policy)

        if self.policy != "naive" and allowed and event.src_domain != event.target_domain:
            allowed = False
        if self.policy != "naive" and allowed and (not event.translation_ok or not event.permission_ok):
            allowed = False
            self.blocked_permission += 1

        if not allowed:
            self.blocked_dirty += int(blocked_by_dirty)
            self.blocked_untrained += int(blocked_by_untrained)
            self.blocked_unproven += int(blocked_by_unproven)
            return

        self.prefetches += 1
        if "data_at_rest" in event.tag or event.src_line < 0:
            self.data_at_rest_prefetches += 1
        if event.src_domain != event.target_domain:
            self.cross_domain_prefetches += 1
        if value_key not in self.true_value:
            self.unproven_value_prefetches += 1
        if line_key not in self.true_line_clean:
            self.unproven_line_prefetches += 1

        if not self._touch_cache(event.candidate):
            self.cycles += PREFETCH_HIT


def read_trace(path: Path) -> list[Event]:
    events = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            events.append(
                Event(
                    cycle=int(raw["cycle"]),
                    event=raw["event"],
                    stream=int(raw["stream"]),
                    domain=int(raw["domain"]),
                    addr=int(raw["addr"]),
                    src_line=int(raw["src_line"]),
                    src_word=int(raw["src_word"]),
                    candidate=int(raw["candidate"]),
                    src_domain=int(raw["src_domain"]),
                    target_domain=int(raw["target_domain"]),
                    committed=bool(int(raw["committed"])),
                    translation_ok=bool(int(raw["translation_ok"])),
                    permission_ok=bool(int(raw["permission_ok"])),
                    tag=raw["tag"],
                )
            )
    return events


def run_policy(
    events: list[Event],
    policy: str,
    cache_lines: int,
    value_entries: int,
    stream_threshold: int,
    dirty_entries: int,
) -> PolicyState:
    state = PolicyState(policy, cache_lines, value_entries, stream_threshold, dirty_entries)
    for event in events:
        state.process(event)
    return state


def summarize(states: list[PolicyState]) -> None:
    disabled_cycles = next(state.cycles for state in states if state.policy == "disabled")
    print(
        "policy,speedup,cycles,demand_misses,prefetches,data_at_rest,cross_domain,"
        "unproven_value,unproven_line,blocked_dirty,blocked_untrained,blocked_unproven,blocked_permission"
    )
    for state in states:
        print(
            f"{state.policy},{disabled_cycles / state.cycles if state.cycles else 0.0:.4f},"
            f"{state.cycles},{state.demand_misses},{state.prefetches},"
            f"{state.data_at_rest_prefetches},{state.cross_domain_prefetches},"
            f"{state.unproven_value_prefetches},{state.unproven_line_prefetches},"
            f"{state.blocked_dirty},{state.blocked_untrained},{state.blocked_unproven},"
            f"{state.blocked_permission}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument("--cache-lines", type=int, default=128)
    parser.add_argument("--value-entries", type=int, default=1024)
    parser.add_argument("--stream-threshold", type=int, default=32)
    parser.add_argument("--dirty-entries", type=int, default=512)
    args = parser.parse_args()

    events = read_trace(args.trace)
    states = [
        run_policy(
            events,
            policy,
            args.cache_lines,
            args.value_entries,
            args.stream_threshold,
            args.dirty_entries,
        )
        for policy in POLICIES
    ]
    summarize(states)


if __name__ == "__main__":
    main()
