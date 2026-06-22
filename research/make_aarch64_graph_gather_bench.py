#!/usr/bin/env python3
"""Generate a static AArch64 graph-gather workload for gem5 full-system runs."""

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


def u64(value: int) -> bytes:
    return struct.pack("<Q", value & 0xFFFFFFFFFFFFFFFF)


def movz_x(rd: int, imm16: int, shift: int = 0) -> int:
    return 0xD2800000 | ((shift // 16) << 21) | ((imm16 & 0xFFFF) << 5) | rd


def movk_x(rd: int, imm16: int, shift: int) -> int:
    return 0xF2800000 | ((shift // 16) << 21) | ((imm16 & 0xFFFF) << 5) | rd


def load_imm_x(rd: int, value: int) -> list[int]:
    parts = [(value >> shift) & 0xFFFF for shift in (0, 16, 32, 48)]
    insns = [movz_x(rd, parts[0], 0)]
    for index, shift in enumerate((16, 32, 48), start=1):
        if parts[index]:
            insns.append(movk_x(rd, parts[index], shift))
    return insns


def ldr_w(rt: int, rn: int, imm: int = 0) -> int:
    if imm % 4 != 0:
        raise ValueError("AArch64 ldr w immediate must be 4-byte aligned")
    return 0xB9400000 | ((imm // 4) << 10) | (rn << 5) | rt


def add_x_imm(rd: int, rn: int, imm: int) -> int:
    if imm < 0 or imm > 0xFFF:
        raise ValueError("immediate out of range for add_x_imm")
    return 0x91000000 | (imm << 10) | (rn << 5) | rd


def subs_x_imm(rd: int, rn: int, imm: int) -> int:
    if imm < 0 or imm > 0xFFF:
        raise ValueError("immediate out of range for subs_x_imm")
    return 0xF1000000 | (imm << 10) | (rn << 5) | rd


def eor_w(rd: int, rn: int, rm: int) -> int:
    return 0x4A000000 | (rm << 16) | (rn << 5) | rd


def b_cond(current_index: int, target_index: int, cond: int) -> int:
    imm = target_index - current_index
    if imm < -(1 << 18) or imm >= (1 << 18):
        raise ValueError("conditional branch out of range")
    return 0x54000000 | ((imm & 0x7FFFF) << 5) | (cond & 0xF)


def make_edges(node_count: int, degree: int, pattern: str, seed: int) -> list[int]:
    rng = random.Random(seed)
    edges: list[int] = []
    nodes_per_page = 4096 // 64
    for src in range(node_count):
        if pattern == "random":
            targets = [rng.randrange(node_count) for _ in range(degree)]
        elif pattern == "page-permute":
            page_start = (src // nodes_per_page) * nodes_per_page
            page_end = min(node_count, page_start + nodes_per_page)
            local = list(range(page_start, page_end))
            rng.shuffle(local)
            targets = [local[(src + k * 17) % len(local)] for k in range(degree)]
        else:
            raise ValueError(f"unknown pattern {pattern!r}")
        edges.extend(targets)
    rng.shuffle(edges)
    return edges


def make_code(
    nodes_addr: int,
    edges_addr: int,
    fake_addr: int,
    msg_addr: int,
    msg_len: int,
    edge_count: int,
    passes: int,
    fake_count: int,
    gap_ops: int,
) -> bytes:
    insns: list[int] = []

    insns.extend(load_imm_x(6, passes))
    pass_loop = len(insns)
    insns.extend(load_imm_x(4, edges_addr))
    insns.extend(load_imm_x(3, edge_count))

    edge_loop = len(insns)
    insns.append(ldr_w(0, 4, 0))          # w0 = edge target pointer
    insns.append(add_x_imm(4, 4, 4))      # next edge slot
    for k in range(gap_ops):
        insns.append(eor_w(2, 2, 0))
        insns.append(add_x_imm(2, 2, (k & 7) + 1))
    insns.append(ldr_w(1, 0, 4))          # demand use of target node
    insns.append(eor_w(2, 2, 1))
    insns.append(subs_x_imm(3, 3, 1))
    insns.append(0)
    insns[-1] = b_cond(len(insns) - 1, edge_loop, 0x1)

    insns.append(subs_x_imm(6, 6, 1))
    insns.append(0)
    insns[-1] = b_cond(len(insns) - 1, pass_loop, 0x1)

    insns.extend(load_imm_x(4, fake_addr))
    insns.extend(load_imm_x(3, fake_count))
    fake_loop = len(insns)
    insns.append(ldr_w(1, 4, 0))          # pointer-shaped data-at-rest
    insns.append(add_x_imm(4, 4, 4))
    insns.append(eor_w(2, 2, 1))
    insns.append(subs_x_imm(3, 3, 1))
    insns.append(0)
    insns[-1] = b_cond(len(insns) - 1, fake_loop, 0x1)

    insns.extend(load_imm_x(0, 1))        # stdout
    insns.extend(load_imm_x(1, msg_addr))
    insns.extend(load_imm_x(2, msg_len))
    insns.extend(load_imm_x(8, 64))       # write
    insns.append(0xD4000001)              # svc #0

    insns.extend(load_imm_x(0, 0))
    insns.extend(load_imm_x(8, 93))       # exit
    insns.append(0xD4000001)
    return b"".join(u32(insn) for insn in insns)


def make_elf(
    node_count: int,
    degree: int,
    passes: int,
    fake_count: int,
    pattern: str,
    seed: int,
    gap_ops: int,
) -> bytes:
    if node_count <= 0 or degree <= 0 or passes <= 0 or fake_count <= 0:
        raise ValueError("all size parameters must be positive")

    nodes_addr = BASE + DATA_OFF
    edges_addr = nodes_addr + node_count * 64
    edges = make_edges(node_count, degree, pattern, seed)
    edge_count = len(edges)
    fake_addr = edges_addr + edge_count * 4
    msg = (
        "COPPER_GRAPH_GATHER_DONE "
        f"nodes={node_count} degree={degree} passes={passes} "
        f"fake={fake_count} pattern={pattern} seed={seed} gap_ops={gap_ops}\n"
    ).encode("ascii")
    msg_addr = fake_addr + fake_count * 4
    code = make_code(
        nodes_addr,
        edges_addr,
        fake_addr,
        msg_addr,
        len(msg),
        edge_count,
        passes,
        fake_count,
        gap_ops,
    )

    blob = bytearray(DATA_OFF)
    blob[CODE_OFF : CODE_OFF + len(code)] = code

    for index in range(node_count):
        offset = DATA_OFF + index * 64
        blob.extend(b"\x00" * max(0, offset + 64 - len(blob)))
        blob[offset : offset + 4] = u32(nodes_addr + index * 64)
        blob[offset + 4 : offset + 8] = u32((index * 2654435761 + seed) & 0xFFFFFFFF)

    edge_off = DATA_OFF + node_count * 64
    blob.extend(b"\x00" * max(0, edge_off + edge_count * 4 - len(blob)))
    for index, target in enumerate(edges):
        blob[edge_off + index * 4 : edge_off + index * 4 + 4] = u32(
            nodes_addr + target * 64
        )

    fake_off = edge_off + edge_count * 4
    blob.extend(b"\x00" * max(0, fake_off + fake_count * 4 - len(blob)))
    for index in range(fake_count):
        target = (index * 193 + seed * 31) % node_count
        blob[fake_off + index * 4 : fake_off + index * 4 + 4] = u32(
            nodes_addr + target * 64
        )

    msg_off = fake_off + fake_count * 4
    blob.extend(b"\x00" * max(0, msg_off + len(msg) - len(blob)))
    blob[msg_off : msg_off + len(msg)] = msg

    ehdr = bytearray()
    ehdr += b"\x7fELF"
    ehdr += bytes([2, 1, 1, 0]) + bytes(8)
    ehdr += struct.pack(
        "<HHIQQQIHHHHHH",
        2,
        183,
        1,
        BASE + CODE_OFF,
        64,
        0,
        0,
        64,
        56,
        1,
        0,
        0,
        0,
    )
    phdr = struct.pack("<IIQQQQQQ", 1, 7, 0, BASE, BASE, len(blob), len(blob), 0x1000)
    blob[0 : len(ehdr)] = ehdr
    blob[len(ehdr) : len(ehdr) + len(phdr)] = phdr
    return bytes(blob)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("research/bin/aarch64_graph_gather"))
    parser.add_argument("--nodes", type=int, default=4096)
    parser.add_argument("--degree", type=int, default=4)
    parser.add_argument("--passes", type=int, default=4)
    parser.add_argument("--fake-count", type=int, default=4096)
    parser.add_argument("--gap-ops", type=int, default=12)
    parser.add_argument("--pattern", choices=("random", "page-permute"), default="random")
    parser.add_argument("--seed", type=int, default=23)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(
        make_elf(
            args.nodes,
            args.degree,
            args.passes,
            args.fake_count,
            args.pattern,
            args.seed,
            args.gap_ops,
        )
    )
    print(args.output)


if __name__ == "__main__":
    main()
