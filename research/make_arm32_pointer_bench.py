#!/usr/bin/env python3
"""Generate a tiny static ARM32 Linux ELF pointer benchmark for gem5 SE mode."""

from __future__ import annotations

import argparse
import random
import struct
from pathlib import Path


BASE = 0x10000
CODE_OFF = 0x100
DATA_OFF = 0x1000


def u32(value: int) -> bytes:
    return struct.pack("<I", value & 0xFFFFFFFF)


def make_next_indices(node_count: int, pattern: str, seed: int) -> list[int]:
    if node_count <= 0:
        raise ValueError("node_count must be positive")

    if pattern == "sequential":
        return [(index + 1) % node_count for index in range(node_count)]

    rng = random.Random(seed)
    if pattern == "random":
        order = list(range(node_count))
        rng.shuffle(order)
    elif pattern == "page-permute":
        order = []
        nodes_per_page = 4096 // 64
        for start in range(0, node_count, nodes_per_page):
            group = list(range(start, min(start + nodes_per_page, node_count)))
            rng.shuffle(group)
            order.extend(group)
    else:
        raise ValueError(f"unknown pattern {pattern!r}")

    nexts = [0] * node_count
    for position, node in enumerate(order):
        nexts[node] = order[(position + 1) % len(order)]
    return nexts


def make_elf(
    node_count: int,
    chase_repeats: int,
    fake_count: int,
    pattern: str,
    seed: int,
) -> bytes:
    if fake_count <= 0:
        raise ValueError("fake_count must be positive; the hand-coded loop expects at least one word")

    code_addr = BASE + CODE_OFF
    nodes_addr = BASE + DATA_OFF
    fake_addr = nodes_addr + node_count * 64
    chase_iters = node_count * chase_repeats
    next_indices = make_next_indices(node_count, pattern, seed)

    instructions = [
        0xE59F4030,  # ldr r4, [pc, #0x30] ; nodes
        0xE59F5030,  # ldr r5, [pc, #0x30] ; chase iterations
        0xE5944000,  # chase: ldr r4, [r4]
        0xE2555001,  # subs r5, r5, #1
        0x1AFFFFFC,  # bne chase
        0xE59F6024,  # ldr r6, [pc, #0x24] ; fake pointer array
        0xE59F5024,  # ldr r5, [pc, #0x24] ; fake count
        0xE4961004,  # fake: ldr r1, [r6], #4
        0xE0200001,  # eor r0, r0, r1
        0xE2555001,  # subs r5, r5, #1
        0x1AFFFFFB,  # bne fake
        0xE3A07001,  # mov r7, #1
        0xE3A00000,  # mov r0, #0
        0xEF000000,  # svc #0
        nodes_addr,
        chase_iters,
        fake_addr,
        fake_count,
    ]

    code = b"".join(u32(i) for i in instructions)
    blob = bytearray(DATA_OFF)
    blob[CODE_OFF : CODE_OFF + len(code)] = code

    for index in range(node_count):
        next_addr = nodes_addr + next_indices[index] * 64
        offset = DATA_OFF + index * 64
        blob.extend(b"\x00" * max(0, offset + 64 - len(blob)))
        blob[offset : offset + 4] = u32(next_addr)

    fake_off = DATA_OFF + node_count * 64
    blob.extend(b"\x00" * max(0, fake_off + fake_count * 4 - len(blob)))
    for index in range(fake_count):
        target = nodes_addr + ((index * 17) % node_count) * 64
        blob[fake_off + index * 4 : fake_off + index * 4 + 4] = u32(target)

    entry = code_addr
    phoff = 52
    filesz = len(blob)
    ehdr = bytearray()
    ehdr += b"\x7fELF"
    ehdr += bytes([1, 1, 1, 0]) + bytes(8)
    ehdr += struct.pack(
        "<HHIIIIIHHHHHH",
        2,          # ET_EXEC
        40,         # EM_ARM
        1,          # EV_CURRENT
        entry,
        phoff,
        0,
        0x04000002, # EABI v4, executable
        52,
        32,
        1,
        0,
        0,
        0,
    )
    phdr = struct.pack(
        "<IIIIIIII",
        1,       # PT_LOAD
        0,
        BASE,
        BASE,
        filesz,
        filesz,
        7,       # R/W/X for code plus in-segment data
        0x1000,
    )
    blob[0 : len(ehdr)] = ehdr
    blob[len(ehdr) : len(ehdr) + len(phdr)] = phdr
    return bytes(blob)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("research/bin/arm32_pointer_bench"))
    parser.add_argument("--nodes", type=int, default=8192)
    parser.add_argument("--chase-repeats", type=int, default=4)
    parser.add_argument("--fake-count", type=int, default=4096)
    parser.add_argument(
        "--pattern",
        choices=("sequential", "page-permute", "random"),
        default="sequential",
    )
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(
        make_elf(
            args.nodes,
            args.chase_repeats,
            args.fake_count,
            args.pattern,
            args.seed,
        )
    )
    print(args.output)


if __name__ == "__main__":
    main()
