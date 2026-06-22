#!/usr/bin/env python3
"""Generate a tiny static AArch64 Linux ELF pointer benchmark for gem5 SE."""

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


def make_code(nodes_addr: int, fake_addr: int, chase_iters: int,
              fake_count: int) -> bytes:
    insns: list[int] = []
    insns.extend(load_imm_x(0, nodes_addr))
    insns.extend(load_imm_x(3, chase_iters))

    chase_index = len(insns)
    insns.append(ldr_w(0, 0, 0))             # x0 = *(uint32_t *)x0
    insns.append(subs_x_imm(3, 3, 1))        # --iters, set flags
    insns.append(0)                          # b.ne chase
    insns[-1] = b_cond(len(insns) - 1, chase_index, 0x1)

    insns.extend(load_imm_x(4, fake_addr))
    insns.extend(load_imm_x(3, fake_count))
    insns.append(movz_x(2, 0))

    fake_index = len(insns)
    insns.append(ldr_w(1, 4, 0))             # w1 = *fake
    insns.append(add_x_imm(4, 4, 4))         # fake += 4
    insns.append(eor_w(2, 2, 1))             # consume the value
    insns.append(subs_x_imm(3, 3, 1))
    insns.append(0)                          # b.ne fake
    insns[-1] = b_cond(len(insns) - 1, fake_index, 0x1)

    insns.append(movz_x(0, 0))               # exit status
    insns.append(movz_x(8, 93))              # Linux AArch64 exit syscall
    insns.append(0xD4000001)                 # svc #0
    return b"".join(u32(insn) for insn in insns)


def make_elf(
    node_count: int,
    chase_repeats: int,
    fake_count: int,
    pattern: str,
    seed: int,
) -> bytes:
    if fake_count <= 0:
        raise ValueError("fake_count must be positive")

    code_addr = BASE + CODE_OFF
    nodes_addr = BASE + DATA_OFF
    fake_addr = nodes_addr + node_count * 64
    chase_iters = node_count * chase_repeats
    next_indices = make_next_indices(node_count, pattern, seed)
    code = make_code(nodes_addr, fake_addr, chase_iters, fake_count)

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

    ehdr = bytearray()
    ehdr += b"\x7fELF"
    ehdr += bytes([2, 1, 1, 0]) + bytes(8)  # ELF64, little-endian
    ehdr += struct.pack("<HHIQQQIHHHHHH", 2, 183, 1, code_addr, 64, 0, 0,
                        64, 56, 1, 0, 0, 0)
    phdr = struct.pack("<IIQQQQQQ", 1, 7, 0, BASE, BASE, len(blob),
                       len(blob), 0x1000)
    blob[0 : len(ehdr)] = ehdr
    blob[len(ehdr) : len(ehdr) + len(phdr)] = phdr
    return bytes(blob)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("research/bin/aarch64_pointer_bench"))
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
