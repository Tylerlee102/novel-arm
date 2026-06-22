#!/usr/bin/env python3
"""
Toy model for COPPER: Committed Pointer-Provenance Prefetching.

The model compares three policies for a data-memory-dependent prefetcher (DMP):
  disabled: no data-dependent prefetching
  naive: any pointer-looking cache word can seed a prefetch
  copper_slot: only cache slots that previously fed a committed demand address
               can seed a prefetch, and only within the same protection domain
  copper_value: like copper_slot, but binds provenance to the exact value

This is not a real AArch64 core model. It isolates the proposed invariant:
"no data-at-rest word becomes a DMP prefetch address unless committed execution
has already used that exact word as an address under a matching domain."
"""

from __future__ import annotations

from dataclasses import dataclass
import argparse
from collections import OrderedDict
import copy
import random
from statistics import mean


MISS = 100
HIT = 4
PREFETCH_HIT = 8


@dataclass
class Obj:
    addr: int
    next_addr: int | None
    domain: int
    secret_rewritten: bool = False


@dataclass(frozen=True)
class Workload:
    objects: dict[int, Obj]
    traversals: list[list[int]]
    secret_lines: list[list[int]]
    mutation_sources: list[int]
    user_addrs: list[int]


class DMPPolicy:
    def __init__(
        self,
        name: str,
        cache_lines: int,
        provenance_entries: int,
        value_token_bits: int = 64,
        stream_threshold: int = 32,
    ) -> None:
        self.name = name
        self.cache_lines = cache_lines
        self.provenance_entries = provenance_entries
        self.value_token_bits = value_token_bits
        self.stream_threshold = stream_threshold
        self.cache: OrderedDict[int, None] = OrderedDict()
        self.proven_slots: OrderedDict[tuple[int, int, int], None] = OrderedDict()
        self.proven_values: OrderedDict[tuple[int, int, int, int], None] = OrderedDict()
        self.true_proven_slots: set[tuple[int, int, int]] = set()
        self.true_proven_values: set[tuple[int, int, int, int]] = set()
        self.stream_committed_uses = 0
        self.stream_trained = False
        self.stream_dirty_sources: set[tuple[int, int, int]] = set()
        self.useful_prefetches = 0
        self.cross_domain_prefetches = 0
        self.data_at_rest_prefetches = 0
        self.unproven_value_prefetches = 0
        self.blocked_unproven_values = 0
        self.blocked_permission = 0
        self.total_prefetches = 0
        self.demand_misses = 0
        self.cycles = 0

    def _value_token(self, value: int) -> int:
        if self.value_token_bits >= 64:
            return value
        if self.value_token_bits <= 0:
            return 0
        return value & ((1 << self.value_token_bits) - 1)

    def _remember(
        self,
        table: OrderedDict[tuple[int, ...], None],
        key: tuple[int, ...],
    ) -> None:
        if self.provenance_entries <= 0:
            return
        table[key] = None
        table.move_to_end(key)
        if len(table) > self.provenance_entries:
            table.popitem(last=False)

    def _knows(
        self,
        table: OrderedDict[tuple[int, ...], None],
        key: tuple[int, ...],
    ) -> bool:
        known = key in table
        if known:
            table.move_to_end(key)
        return known

    def _touch(self, addr: int) -> bool:
        hit = addr in self.cache
        if hit:
            self.cache.move_to_end(addr)
        else:
            self.cache[addr] = None
            if len(self.cache) > self.cache_lines:
                self.cache.popitem(last=False)
        return hit

    def coherence_update(self, src_line: int) -> None:
        for table in (self.proven_slots, self.proven_values):
            for key in list(table.keys()):
                if key[0] == src_line:
                    del table[key]
        self.true_proven_slots = {key for key in self.true_proven_slots if key[0] != src_line}
        self.true_proven_values = {key for key in self.true_proven_values if key[0] != src_line}
        self.stream_dirty_sources.add((src_line, 0, 0))

    def source_word_write(self, src_line: int, src_word: int, domain: int) -> None:
        self.coherence_update(src_line)
        self.stream_dirty_sources.add((src_line, src_word, domain))

    def advance_epoch(self) -> None:
        if self.stream_committed_uses >= self.stream_threshold:
            self.stream_trained = True

    def load_line(
        self,
        addr: int,
        requester_domain: int,
        wl: Workload,
        source_addr: int | None = None,
        source_slot: int | None = None,
    ) -> None:
        if self._touch(addr):
            self.cycles += HIT
        else:
            self.cycles += MISS
            self.demand_misses += 1

        source_matches_value = (
            source_addr is not None
            and source_slot is not None
            and source_addr in wl.objects
            and wl.objects[source_addr].next_addr == addr
        )

        if source_matches_value:
            exact_slot = (source_addr, source_slot, requester_domain)
            exact_value = (source_addr, source_slot, addr, requester_domain)
            self.true_proven_slots.add(exact_slot)
            self.true_proven_values.add(exact_value)
            self.stream_committed_uses += 1
            self.stream_dirty_sources.discard((source_addr, source_slot, requester_domain))
            self._remember(self.proven_slots, (source_addr, source_slot, requester_domain))
            self._remember(
                self.proven_values,
                (source_addr, source_slot, self._value_token(addr), requester_domain),
            )

        obj = wl.objects[addr]
        if obj.next_addr is not None:
            self._maybe_prefetch(
                src_addr=addr,
                slot=0,
                candidate=obj.next_addr,
                src_domain=obj.domain,
                requester_domain=requester_domain,
                wl=wl,
                translation_ok=True,
                permission_ok=True,
            )

    def scan_secret_line(self, line_id: int, requester_domain: int, wl: Workload) -> None:
        values = wl.secret_lines[line_id]
        src_domain = requester_domain
        for slot, candidate in enumerate(values):
            self._maybe_prefetch(
                src_addr=-(line_id + 1),
                slot=slot,
                candidate=candidate,
                src_domain=src_domain,
                requester_domain=requester_domain,
                wl=wl,
                translation_ok=True,
                permission_ok=True,
            )

    def _maybe_prefetch(
        self,
        src_addr: int,
        slot: int,
        candidate: int,
        src_domain: int,
        requester_domain: int,
        wl: Workload,
        translation_ok: bool = True,
        permission_ok: bool = True,
    ) -> None:
        if self.name == "disabled":
            return
        if candidate not in wl.objects:
            return

        target_domain = wl.objects[candidate].domain
        allowed = False
        if self.name == "naive":
            allowed = True
        elif self.name == "copper_slot":
            allowed = (
                self._knows(self.proven_slots, (src_addr, slot, requester_domain))
                and src_domain == requester_domain
                and target_domain == requester_domain
            )
        elif self.name == "copper_value":
            allowed = (
                self._knows(
                    self.proven_values,
                    (src_addr, slot, self._value_token(candidate), requester_domain),
                )
                and src_domain == requester_domain
                and target_domain == requester_domain
            )
        elif self.name == "copper_stream":
            allowed = (
                self.stream_trained
                and src_addr >= 0
                and slot == 0
                and (src_addr, slot, requester_domain) not in self.stream_dirty_sources
                and src_domain == requester_domain
                and target_domain == requester_domain
            )
        else:
            raise ValueError(self.name)

        if not allowed:
            if (
                src_addr >= 0
                and src_addr in wl.objects
                and wl.objects[src_addr].secret_rewritten
                and self._knows(self.proven_slots, (src_addr, slot, requester_domain))
                and (src_addr, slot, candidate, requester_domain) not in self.true_proven_values
            ):
                self.blocked_unproven_values += 1
            return

        if not translation_ok or not permission_ok:
            self.blocked_permission += 1
            return

        self.total_prefetches += 1
        if target_domain != requester_domain:
            self.cross_domain_prefetches += 1
        if src_addr < 0:
            self.data_at_rest_prefetches += 1
        elif (
            wl.objects[src_addr].secret_rewritten
            and (src_addr, slot, candidate, requester_domain) not in self.true_proven_values
        ):
            self.unproven_value_prefetches += 1

        if not self._touch(candidate):
            self.cycles += PREFETCH_HIT


def make_workload(
    rng: random.Random,
    lists: int,
    length: int,
    secret_lines: int,
    secret_slots: int,
    cross_domain_secret_rate: float,
    rewrite_fraction: float,
) -> Workload:
    objects: dict[int, Obj] = {}
    traversals: list[list[int]] = []
    next_addr = 0x1000

    for domain in (0, 1):
        for _ in range(lists):
            chain = []
            for _ in range(length):
                chain.append(next_addr)
                next_addr += 0x40
            for i, addr in enumerate(chain):
                nxt = chain[i + 1] if i + 1 < len(chain) else None
                objects[addr] = Obj(addr=addr, next_addr=nxt, domain=domain)
            if domain == 0:
                traversals.append(chain)

    user_addrs = [addr for addr, obj in objects.items() if obj.domain == 0]
    kernel_addrs = [addr for addr, obj in objects.items() if obj.domain == 1]
    secrets: list[list[int]] = []
    for _ in range(secret_lines):
        line = []
        for _ in range(secret_slots):
            if rng.random() < cross_domain_secret_rate:
                line.append(rng.choice(kernel_addrs))
            else:
                line.append(rng.choice(user_addrs))
        secrets.append(line)

    mutable_sources = [addr for chain in traversals for addr in chain[:-1]]
    mutation_count = max(0, int(len(mutable_sources) * rewrite_fraction))
    mutation_sources = rng.sample(mutable_sources, mutation_count) if mutation_count else []

    return Workload(
        objects=objects,
        traversals=traversals,
        secret_lines=secrets,
        mutation_sources=mutation_sources,
        user_addrs=user_addrs,
    )


def simulate(
    policy_name: str,
    wl: Workload,
    repeats: int,
    cache_lines: int,
    provenance_entries: int,
    value_token_bits: int,
    stream_threshold: int,
) -> DMPPolicy:
    policy = DMPPolicy(
        policy_name,
        cache_lines,
        provenance_entries,
        value_token_bits,
        stream_threshold,
    )
    for repeat in range(repeats):
        policy.advance_epoch()
        if repeat == 1:
            for src in wl.mutation_sources:
                if policy.name == "copper_stream":
                    policy.source_word_write(src, 0, 0)
                old = wl.objects[src].next_addr
                candidates = [addr for addr in wl.user_addrs if addr != old]
                wl.objects[src].next_addr = candidates[(src // 0x40) % len(candidates)]
                wl.objects[src].secret_rewritten = True
        for line_id in range(len(wl.secret_lines)):
            policy.scan_secret_line(line_id, requester_domain=0, wl=wl)
        for chain in wl.traversals:
            prev = None
            for index, addr in enumerate(chain):
                policy.load_line(
                    addr,
                    requester_domain=0,
                    wl=wl,
                    source_addr=prev,
                    source_slot=0 if prev is not None and index > 0 else None,
                )
                prev = addr
    return policy


def trial(rng: random.Random, args: argparse.Namespace) -> dict[str, DMPPolicy]:
    wl = make_workload(
        rng,
        args.lists,
        args.length,
        args.secret_lines,
        args.secret_slots,
        args.cross_domain_secret_rate,
        args.rewrite_fraction,
    )
    return {
        name: simulate(
            name,
            copy.deepcopy(wl),
            args.repeats,
            args.cache_lines,
            args.provenance_entries,
            args.value_token_bits,
            args.stream_threshold,
        )
        for name in ("disabled", "naive", "copper_slot", "copper_value", "copper_stream")
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=31)
    parser.add_argument("--lists", type=int, default=16)
    parser.add_argument("--length", type=int, default=32)
    parser.add_argument("--secret-lines", type=int, default=128)
    parser.add_argument("--secret-slots", type=int, default=4)
    parser.add_argument("--cross-domain-secret-rate", type=float, default=0.5)
    parser.add_argument("--repeats", type=int, default=4)
    parser.add_argument("--cache-lines", type=int, default=128)
    parser.add_argument("--rewrite-fraction", type=float, default=0.05)
    parser.add_argument("--provenance-entries", type=int, default=1024)
    parser.add_argument("--value-token-bits", type=int, default=64)
    parser.add_argument("--stream-threshold", type=int, default=32)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    names = ("disabled", "naive", "copper_slot", "copper_value", "copper_stream")
    summaries: dict[str, list[DMPPolicy]] = {name: [] for name in names}
    for _ in range(args.trials):
        result = trial(rng, args)
        for name, policy in result.items():
            summaries[name].append(policy)

    disabled_cycles = mean(p.cycles for p in summaries["disabled"])
    print("COPPER DMP toy simulation")
    for name in names:
        policies = summaries[name]
        cycles = mean(p.cycles for p in policies)
        cross_domain = mean(p.cross_domain_prefetches for p in policies)
        data_at_rest = mean(p.data_at_rest_prefetches for p in policies)
        prefetches = mean(p.total_prefetches for p in policies)
        misses = mean(p.demand_misses for p in policies)
        unproven = mean(p.unproven_value_prefetches for p in policies)
        blocked = mean(p.blocked_unproven_values for p in policies)
        blocked_permission = mean(p.blocked_permission for p in policies)
        print(
            f"{name}: cycles={cycles:.1f}, speedup_vs_disabled={disabled_cycles / cycles:.3f}, "
            f"demand_misses={misses:.1f}, prefetches={prefetches:.1f}, "
            f"data_at_rest_prefetches={data_at_rest:.1f}, cross_domain_prefetches={cross_domain:.1f}, "
            f"unproven_value_prefetches={unproven:.1f}, blocked_unproven_values={blocked:.1f}, "
            f"blocked_permission={blocked_permission:.1f}"
        )


if __name__ == "__main__":
    main()
