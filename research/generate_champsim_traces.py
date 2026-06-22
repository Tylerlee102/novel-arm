"""Generate small deterministic ChampSim input traces for COPPER evaluation.

ChampSim's default trace record is 64 bytes:
  uint64 ip;
  uint8 is_branch;
  uint8 branch_taken;
  uint8 destination_registers[2];
  uint8 source_registers[4];
  uint64 destination_memory[2];
  uint64 source_memory[4];

These traces are not intended to prove COPPER's provenance invariant. Stock
ChampSim traces do not carry committed pointer values or security domains.
They are useful for checking memory-system behavior and for comparing ordinary
prefetch baselines on shapes that resemble the COPPER Python traces.
"""

from __future__ import annotations

import argparse
import csv
import random
import struct
from pathlib import Path


RECORD = struct.Struct("<QBB2B4B2Q4Q")
ZERO_REGS2 = (0, 0)
ZERO_REGS4 = (0, 0, 0, 0)
ZERO_DMEM = (0, 0)
ZERO_SMEM = (0, 0, 0, 0)


def pack_instr(
    ip: int,
    *,
    is_branch: int = 0,
    branch_taken: int = 0,
    dst_regs: tuple[int, int] = ZERO_REGS2,
    src_regs: tuple[int, int, int, int] = ZERO_REGS4,
    dst_mem: tuple[int, int] = ZERO_DMEM,
    src_mem: tuple[int, int, int, int] = ZERO_SMEM,
) -> bytes:
    return RECORD.pack(ip, is_branch, branch_taken, *dst_regs, *src_regs, *dst_mem, *src_mem)


def sequential_scan(count: int) -> tuple[list[bytes], list[dict[str, int | str]]]:
    trace: list[bytes] = []
    events: list[dict[str, int | str]] = []
    base = 0x1000_0000
    ip_base = 0x4000_0000
    for i in range(count):
        addr = base + i * 64
        ip = ip_base + (i % 8) * 4
        trace.append(pack_instr(ip, dst_regs=(1, 0), src_mem=(addr, 0, 0, 0)))
        events.append({"kind": "seq_load", "ip": ip, "addr": addr})
        if i % 16 == 15:
            branch_ip = ip_base + 0x80
            trace.append(pack_instr(branch_ip, is_branch=1, branch_taken=1, dst_regs=(26, 0), src_regs=(26, 0, 0, 0)))
            events.append({"kind": "loop_branch", "ip": branch_ip, "addr": 0})
    return trace, events


def pointer_chase(count: int, seed: int) -> tuple[list[bytes], list[dict[str, int | str]]]:
    rng = random.Random(seed)
    node_count = max(256, count // 4)
    nodes = [0x2000_0000 + i * 128 for i in range(node_count)]
    order = list(range(node_count))
    rng.shuffle(order)

    trace: list[bytes] = []
    events: list[dict[str, int | str]] = []
    ip_load_next = 0x5000_0010
    ip_load_payload = 0x5000_0020
    ip_store_accum = 0x5000_0030
    ip_branch = 0x5000_0040
    scratch = 0x3000_0000

    for i in range(count):
        node = nodes[order[i % node_count]]
        next_node = nodes[order[(i + 1) % node_count]]
        payload = next_node + 64
        trace.append(pack_instr(ip_load_next, dst_regs=(1, 0), src_mem=(node, 0, 0, 0)))
        events.append({"kind": "ptr_load", "ip": ip_load_next, "addr": node})
        trace.append(pack_instr(ip_load_payload, dst_regs=(2, 0), src_regs=(1, 0, 0, 0), src_mem=(payload, 0, 0, 0)))
        events.append({"kind": "payload_load", "ip": ip_load_payload, "addr": payload})
        if i % 5 == 0:
            store_addr = scratch + ((i // 5) % 1024) * 64
            trace.append(pack_instr(ip_store_accum, src_regs=(2, 0, 0, 0), dst_mem=(store_addr, 0)))
            events.append({"kind": "store", "ip": ip_store_accum, "addr": store_addr})
        if i % 8 == 7:
            trace.append(pack_instr(ip_branch, is_branch=1, branch_taken=1, dst_regs=(26, 0), src_regs=(26, 0, 0, 0)))
            events.append({"kind": "loop_branch", "ip": ip_branch, "addr": 0})
    return trace, events


def adversarial_shape(count: int, seed: int) -> tuple[list[bytes], list[dict[str, int | str]]]:
    rng = random.Random(seed)
    trace: list[bytes] = []
    events: list[dict[str, int | str]] = []
    public_base = 0x4000_0000
    secret_base = 0x7000_0000
    ip_public_load = 0x6000_0010
    ip_secret_store = 0x6000_0020
    ip_use_pointer = 0x6000_0030
    ip_branch = 0x6000_0040

    for i in range(count):
        pub = public_base + (i % 2048) * 64
        secret = secret_base + rng.randrange(0, 4096) * 64
        trace.append(pack_instr(ip_public_load, dst_regs=(1, 0), src_mem=(pub, 0, 0, 0)))
        events.append({"kind": "public_ptr_load", "ip": ip_public_load, "addr": pub})
        if i % 3 == 0:
            trace.append(pack_instr(ip_secret_store, src_regs=(1, 0, 0, 0), dst_mem=(pub, 0)))
            events.append({"kind": "secret_overwrite_shape", "ip": ip_secret_store, "addr": pub})
        trace.append(pack_instr(ip_use_pointer, dst_regs=(2, 0), src_regs=(1, 0, 0, 0), src_mem=(secret, 0, 0, 0)))
        events.append({"kind": "dependent_load_shape", "ip": ip_use_pointer, "addr": secret})
        if i % 8 == 7:
            trace.append(pack_instr(ip_branch, is_branch=1, branch_taken=1, dst_regs=(26, 0), src_regs=(26, 0, 0, 0)))
            events.append({"kind": "loop_branch", "ip": ip_branch, "addr": 0})
    return trace, events


def write_trace(name: str, trace: list[bytes], events: list[dict[str, int | str]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    trace_path = out_dir / f"{name}.champsimtrace"
    csv_path = out_dir / f"{name}.manifest.csv"
    trace_path.write_bytes(b"".join(trace))
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["kind", "ip", "addr"])
        writer.writeheader()
        writer.writerows(events)
    print(f"{name}: {len(trace)} records, {trace_path.stat().st_size} bytes, manifest {csv_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("research/traces/champsim"))
    parser.add_argument("--count", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    generators = {
        "sequential_scan": sequential_scan(args.count),
        "pointer_chase": pointer_chase(args.count, args.seed),
        "adversarial_shape": adversarial_shape(args.count, args.seed),
    }
    for name, (trace, events) in generators.items():
        write_trace(name, trace, events, args.out_dir)


if __name__ == "__main__":
    main()
