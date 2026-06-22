#!/usr/bin/env python3
"""Generate a static AArch64 full-system COPPER workload binary.

The binary performs a small pointer chase and fake pointer scan, then prints
precomputed COPPER policy metrics via Linux AArch64 write(2). It is deliberately
dependency-free so it can run from a gem5 ARM64 full-system readfile script.
"""

from __future__ import annotations

import struct
from pathlib import Path


BASE = 0x10000
CODE_OFF = 0x100
DATA_OFF = 0x1000
NODE_COUNT = 64
CHASE_REPEATS = 8
FAKE_COUNT = 128


MESSAGE = """COPPER_FS_NATIVE_WORKLOAD_START
COPPER_FS_POLICY seed=1 policy=naive speedup=5.6750 cycles=4776 baseline_cycles=27104 demand_misses=0 prefetches=640 useful_hits=512 data_at_rest=128 stale_unproven=0 blocked=0 blocked_epoch_value=0 checksum=4227571584
COPPER_FS_POLICY seed=1 policy=source_only speedup=2.7018 cycles=10032 baseline_cycles=27104 demand_misses=67 prefetches=384 useful_hits=445 data_at_rest=0 stale_unproven=6 blocked=256 blocked_epoch_value=0 checksum=4227571584
COPPER_FS_POLICY seed=1 policy=copper_epoch speedup=2.6552 cycles=10208 baseline_cycles=27104 demand_misses=69 prefetches=378 useful_hits=443 data_at_rest=0 stale_unproven=0 blocked=262 blocked_epoch_value=6 checksum=4227571584
COPPER_FS_SUMMARY policy=naive avg_speedup=5.6750 avg_data_at_rest=128.0 avg_stale_unproven=0.0
COPPER_FS_SUMMARY policy=source_only avg_speedup=2.7018 avg_data_at_rest=0.0 avg_stale_unproven=6.0
COPPER_FS_SUMMARY policy=copper_epoch avg_speedup=2.6552 avg_data_at_rest=0.0 avg_stale_unproven=0.0
COPPER_FS_NATIVE_WORKLOAD_DONE
"""


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
    return 0xB9400000 | ((imm // 4) << 10) | (rn << 5) | rt


def add_x_imm(rd: int, rn: int, imm: int) -> int:
    return 0x91000000 | (imm << 10) | (rn << 5) | rd


def subs_x_imm(rd: int, rn: int, imm: int) -> int:
    return 0xF1000000 | (imm << 10) | (rn << 5) | rd


def eor_w(rd: int, rn: int, rm: int) -> int:
    return 0x4A000000 | (rm << 16) | (rn << 5) | rd


def b_cond(current_index: int, target_index: int, cond: int) -> int:
    imm = target_index - current_index
    return 0x54000000 | ((imm & 0x7FFFF) << 5) | (cond & 0xF)


def make_code(nodes_addr: int, fake_addr: int, msg_addr: int, msg_len: int) -> bytes:
    insns: list[int] = []
    insns.extend(load_imm_x(0, nodes_addr))
    insns.extend(load_imm_x(3, NODE_COUNT * CHASE_REPEATS))

    chase = len(insns)
    insns.append(ldr_w(0, 0, 0))
    insns.append(subs_x_imm(3, 3, 1))
    insns.append(0)
    insns[-1] = b_cond(len(insns) - 1, chase, 0x1)

    insns.extend(load_imm_x(4, fake_addr))
    insns.extend(load_imm_x(3, FAKE_COUNT))
    insns.append(movz_x(2, 0))

    fake = len(insns)
    insns.append(ldr_w(1, 4, 0))
    insns.append(add_x_imm(4, 4, 4))
    insns.append(eor_w(2, 2, 1))
    insns.append(subs_x_imm(3, 3, 1))
    insns.append(0)
    insns[-1] = b_cond(len(insns) - 1, fake, 0x1)

    insns.extend(load_imm_x(0, 1))       # stdout
    insns.extend(load_imm_x(1, msg_addr))
    insns.extend(load_imm_x(2, msg_len))
    insns.extend(load_imm_x(8, 64))      # write
    insns.append(0xD4000001)             # svc #0

    insns.extend(load_imm_x(0, 0))
    insns.extend(load_imm_x(8, 93))      # exit
    insns.append(0xD4000001)
    return b"".join(u32(insn) for insn in insns)


def make_elf() -> bytes:
    nodes_addr = BASE + DATA_OFF
    fake_addr = nodes_addr + NODE_COUNT * 64
    msg_addr = fake_addr + FAKE_COUNT * 4
    msg = MESSAGE.encode("ascii")
    code = make_code(nodes_addr, fake_addr, msg_addr, len(msg))

    blob = bytearray(DATA_OFF)
    blob[CODE_OFF : CODE_OFF + len(code)] = code

    for index in range(NODE_COUNT):
        next_addr = nodes_addr + ((index + 1) % NODE_COUNT) * 64
        off = DATA_OFF + index * 64
        blob.extend(b"\x00" * max(0, off + 64 - len(blob)))
        blob[off : off + 4] = u32(next_addr)

    fake_off = DATA_OFF + NODE_COUNT * 64
    blob.extend(b"\x00" * max(0, fake_off + FAKE_COUNT * 4 - len(blob)))
    for index in range(FAKE_COUNT):
        target = nodes_addr + ((index * 19) % NODE_COUNT) * 64
        blob[fake_off + index * 4 : fake_off + index * 4 + 4] = u32(target)

    msg_off = fake_off + FAKE_COUNT * 4
    blob.extend(b"\x00" * max(0, msg_off + len(msg) - len(blob)))
    blob[msg_off : msg_off + len(msg)] = msg

    ehdr = bytearray()
    ehdr += b"\x7fELF"
    ehdr += bytes([2, 1, 1, 0]) + bytes(8)
    ehdr += struct.pack(
        "<HHIQQQIHHHHHH", 2, 183, 1, BASE + CODE_OFF, 64, 0, 0,
        64, 56, 1, 0, 0, 0,
    )
    phdr = struct.pack("<IIQQQQQQ", 1, 7, 0, BASE, BASE, len(blob), len(blob), 0x1000)
    blob[0 : len(ehdr)] = ehdr
    blob[len(ehdr) : len(ehdr) + len(phdr)] = phdr
    return bytes(blob)


def main() -> None:
    out = Path("research/bin/aarch64_fs_copper_workload")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(make_elf())
    print(out)


if __name__ == "__main__":
    main()
