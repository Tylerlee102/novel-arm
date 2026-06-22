#!/usr/bin/env python3
"""Generate trace files for COPPER trace-driven evaluation."""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


FIELDS = [
    "cycle",
    "event",
    "stream",
    "domain",
    "addr",
    "src_line",
    "src_word",
    "candidate",
    "src_domain",
    "target_domain",
    "committed",
    "translation_ok",
    "permission_ok",
    "tag",
]


def row(
    cycle: int,
    event: str,
    stream: int = 0,
    domain: int = 0,
    addr: int = 0,
    src_line: int = -1,
    src_word: int = 0,
    candidate: int = 0,
    src_domain: int = 0,
    target_domain: int = 0,
    committed: int = 1,
    translation_ok: int = 1,
    permission_ok: int = 1,
    tag: str = "",
) -> dict[str, int | str]:
    return {
        "cycle": cycle,
        "event": event,
        "stream": stream,
        "domain": domain,
        "addr": addr,
        "src_line": src_line,
        "src_word": src_word,
        "candidate": candidate,
        "src_domain": src_domain,
        "target_domain": target_domain,
        "committed": committed,
        "translation_ok": translation_ok,
        "permission_ok": permission_ok,
        "tag": tag,
    }


def write_trace(path: Path, rows: list[dict[str, int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def make_synthetic(args: argparse.Namespace) -> list[dict[str, int | str]]:
    rng = random.Random(args.seed)
    rows: list[dict[str, int | str]] = []
    cycle = 0
    next_addr = 0x1000
    chains: list[list[int]] = []
    objects: dict[int, tuple[int | None, int]] = {}

    for domain in (0, 1):
        for _ in range(args.lists):
            chain = []
            for _ in range(args.length):
                chain.append(next_addr)
                next_addr += 0x40
            for i, addr in enumerate(chain):
                nxt = chain[i + 1] if i + 1 < len(chain) else None
                objects[addr] = (nxt, domain)
            if domain == 0:
                chains.append(chain)

    user_addrs = [addr for addr, (_, domain) in objects.items() if domain == 0]
    kernel_addrs = [addr for addr, (_, domain) in objects.items() if domain == 1]
    secret_lines: list[list[int]] = []
    for _ in range(args.secret_lines):
        values = []
        for _ in range(args.secret_slots):
            if rng.random() < args.cross_domain_secret_rate:
                values.append(rng.choice(kernel_addrs))
            else:
                values.append(rng.choice(user_addrs))
        secret_lines.append(values)

    mutable_sources = [addr for chain in chains for addr in chain[:-1]]
    mutation_count = int(len(mutable_sources) * args.rewrite_fraction)
    rewritten = set(rng.sample(mutable_sources, mutation_count)) if mutation_count else set()
    rewritten_values: dict[int, int] = {}

    for repeat in range(args.repeats):
        rows.append(row(cycle, "EPOCH", tag=f"repeat_{repeat}"))
        cycle += 1

        if repeat == 1:
            for src in sorted(rewritten):
                old, domain = objects[src]
                candidates = [addr for addr in user_addrs if addr != old]
                new_value = candidates[(src // 0x40) % len(candidates)]
                rewritten_values[src] = new_value
                rows.append(
                    row(
                        cycle,
                        "WRITE",
                        stream=0,
                        domain=domain,
                        src_line=src,
                        src_word=0,
                        src_domain=domain,
                        tag="rewrite_secret_like",
                    )
                )
                cycle += 1

        for line_id, values in enumerate(secret_lines):
            for slot, candidate in enumerate(values):
                _, target_domain = objects[candidate]
                rows.append(
                    row(
                        cycle,
                        "DMP",
                        stream=99,
                        domain=0,
                        src_line=-(line_id + 1),
                        src_word=slot,
                        candidate=candidate,
                        src_domain=0,
                        target_domain=target_domain,
                        tag="data_at_rest_secret",
                    )
                )
                cycle += 1

        for stream, chain in enumerate(chains):
            for index, addr in enumerate(chain):
                rows.append(row(cycle, "DEMAND", stream=stream, domain=0, addr=addr, tag="node_load"))
                cycle += 1

                nxt, _ = objects[addr]
                if nxt is None:
                    continue

                candidate = rewritten_values.get(addr, nxt)
                dmp_tag = "stale_rewrite" if addr in rewritten_values else "stream_pointer"
                rows.append(
                    row(
                        cycle,
                        "DMP",
                        stream=stream,
                        domain=0,
                        src_line=addr,
                        src_word=0,
                        candidate=candidate,
                        src_domain=0,
                        target_domain=0,
                        tag=dmp_tag,
                    )
                )
                cycle += 1

                source_still_matches = addr not in rewritten_values
                rows.append(
                    row(
                        cycle,
                        "DEMAND",
                        stream=stream,
                        domain=0,
                        addr=nxt,
                        src_line=addr if source_still_matches else -1,
                        src_word=0,
                        candidate=nxt,
                        src_domain=0,
                        target_domain=0,
                        committed=1 if source_still_matches else 0,
                        tag="committed_pointer_use" if source_still_matches else "post_rewrite_old_path",
                    )
                )
                cycle += 1

    return rows


def make_adversarial(args: argparse.Namespace) -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    cycle = 0

    rows.append(row(cycle, "EPOCH", tag="start"))
    cycle += 1
    rows.append(row(cycle, "DMP", stream=7, src_line=-1, src_word=0, candidate=0x2000, target_domain=1, tag="data_at_rest_secret"))
    cycle += 1
    rows.append(row(cycle, "DMP", stream=0, src_line=0x1000, src_word=0, candidate=0x1040, src_domain=0, target_domain=0, tag="untrained_first_use"))
    cycle += 1

    for i in range(args.train_threshold):
        src = 0x1000 + i * 0x40
        target = src + 0x40
        rows.append(row(cycle, "DEMAND", stream=0, domain=0, addr=target, src_line=src, src_word=0, candidate=target, tag="committed_pointer_use"))
        cycle += 1
    rows.append(row(cycle, "EPOCH", tag="trained"))
    cycle += 1

    rows.append(row(cycle, "DMP", stream=0, src_line=0x1000, src_word=0, candidate=0x1040, src_domain=0, target_domain=0, tag="clean_after_proof"))
    cycle += 1
    rows.append(row(cycle, "WRITE", stream=0, src_line=0x1000, src_word=0, src_domain=0, tag="rewrite_secret_like"))
    cycle += 1
    rows.append(row(cycle, "DMP", stream=0, src_line=0x1000, src_word=0, candidate=0x1880, src_domain=0, target_domain=0, tag="stale_rewrite"))
    cycle += 1
    rows.append(row(cycle, "DMP", stream=0, src_line=0x1100, src_word=0, candidate=0x2080, src_domain=0, target_domain=1, tag="cross_domain"))
    cycle += 1
    rows.append(row(cycle, "DMP", stream=0, src_line=0x1100, src_word=0, candidate=0x1140, src_domain=0, target_domain=0, translation_ok=0, tag="translation_fail"))
    cycle += 1
    rows.append(row(cycle, "DMP", stream=0, src_line=0x1100, src_word=0, candidate=0x1140, src_domain=0, target_domain=0, permission_ok=0, tag="permission_fail"))

    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("research/traces/synthetic.csv"))
    parser.add_argument("--scenario", choices=("synthetic", "adversarial"), default="synthetic")
    parser.add_argument("--seed", type=int, default=2027)
    parser.add_argument("--lists", type=int, default=16)
    parser.add_argument("--length", type=int, default=32)
    parser.add_argument("--secret-lines", type=int, default=128)
    parser.add_argument("--secret-slots", type=int, default=4)
    parser.add_argument("--cross-domain-secret-rate", type=float, default=0.5)
    parser.add_argument("--rewrite-fraction", type=float, default=0.05)
    parser.add_argument("--repeats", type=int, default=4)
    parser.add_argument("--train-threshold", type=int, default=32)
    args = parser.parse_args()

    rows = make_synthetic(args) if args.scenario == "synthetic" else make_adversarial(args)
    write_trace(args.out, rows)
    print(f"wrote {len(rows)} events to {args.out}")


if __name__ == "__main__":
    main()
