import argparse
import os

import m5
from m5.objects import *


class L1Cache(Cache):
    assoc = 2
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 8
    tgts_per_mshr = 20

    def connect_bus(self, bus):
        self.mem_side = bus.cpu_side_ports


class L1ICache(L1Cache):
    def connect_cpu(self, cpu):
        self.cpu_side = cpu.icache_port


class L1DCache(L1Cache):
    def connect_cpu(self, cpu):
        self.cpu_side = cpu.dcache_port


class L2Cache(Cache):
    assoc = 8
    tag_latency = 20
    data_latency = 20
    response_latency = 20
    mshrs = 20
    tgts_per_mshr = 12

    def connect_cpu_bus(self, bus):
        self.cpu_side = bus.mem_side_ports

    def connect_mem_bus(self, bus):
        self.mem_side = bus.cpu_side_ports


def make_prefetcher(kind, min_addr, max_addr):
    if kind == "none":
        return None
    if kind == "stride":
        return StridePrefetcher(
            degree=1,
            latency=1,
            prefetch_on_access=True,
            use_virtual_addresses=False,
        )
    if kind == "naive":
        return CopperPrefetcher(
            naive=True,
            pointer_bytes=4,
            pointer_alignment=4,
            min_addr=min_addr,
            max_addr=max_addr,
            invalidate_on_evict=False,
            chase_prefetch_fills=False,
            translate_cross_page=True,
            queue_size=64,
            max_prefetch_requests_with_pending_translation=64,
            latency=1,
            use_virtual_addresses=True,
        )
    if kind == "copper":
        return CopperPrefetcher(
            naive=False,
            pointer_bytes=4,
            pointer_alignment=4,
            min_addr=min_addr,
            max_addr=max_addr,
            recent_entries=4096,
            provenance_entries=16384,
            value_token_bits=32,
            invalidate_on_evict=False,
            chase_prefetch_fills=True,
            translate_cross_page=True,
            queue_size=64,
            max_prefetch_requests_with_pending_translation=64,
            latency=1,
            use_virtual_addresses=True,
        )
    raise ValueError(kind)


def make_cpu(kind):
    if kind == "timing":
        return ArmTimingSimpleCPU()
    if kind == "minor":
        return ArmMinorCPU()
    if kind == "o3":
        return ArmO3CPU()
    raise ValueError(kind)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", default="research/bin/arm32_pointer_bench")
    parser.add_argument("--prefetcher", choices=("none", "stride", "naive", "copper"), default="none")
    parser.add_argument("--cpu-model", choices=("timing", "minor", "o3"), default="timing")
    parser.add_argument("--l1d-size", default="8KiB")
    parser.add_argument("--l1i-size", default="16KiB")
    parser.add_argument("--l2-size", default="256KiB")
    parser.add_argument("--candidate-min", type=lambda x: int(x, 0), default=0x11000)
    parser.add_argument("--candidate-max", type=lambda x: int(x, 0), default=0x90FC0)
    args = parser.parse_args()

    binary = os.path.abspath(args.binary)

    system = System()
    system.clk_domain = SrcClockDomain()
    system.clk_domain.clock = "1GHz"
    system.clk_domain.voltage_domain = VoltageDomain()
    system.mem_mode = "timing"
    system.mem_ranges = [AddrRange("512MiB")]

    system.cpu = make_cpu(args.cpu_model)
    system.cpu.icache = L1ICache(size=args.l1i_size)
    system.cpu.dcache = L1DCache(size=args.l1d_size)

    prefetcher = make_prefetcher(args.prefetcher, args.candidate_min, args.candidate_max)
    if prefetcher is not None:
        system.cpu.dcache.prefetcher = prefetcher
        if getattr(prefetcher, "use_virtual_addresses", False):
            prefetcher.registerMMU(system.cpu.mmu)

    system.cpu.icache.connect_cpu(system.cpu)
    system.cpu.dcache.connect_cpu(system.cpu)

    system.l2bus = L2XBar()
    system.cpu.icache.connect_bus(system.l2bus)
    system.cpu.dcache.connect_bus(system.l2bus)

    system.l2cache = L2Cache(size=args.l2_size)
    system.l2cache.connect_cpu_bus(system.l2bus)

    system.membus = SystemXBar()
    system.l2cache.connect_mem_bus(system.membus)

    system.cpu.createInterruptController()
    system.system_port = system.membus.cpu_side_ports

    system.mem_ctrl = MemCtrl()
    system.mem_ctrl.dram = DDR3_1600_8x8()
    system.mem_ctrl.dram.range = system.mem_ranges[0]
    system.mem_ctrl.port = system.membus.mem_side_ports

    system.workload = SEWorkload.init_compatible(binary)
    process = Process()
    process.cmd = [binary]
    system.cpu.workload = process
    system.cpu.createThreads()

    root = Root(full_system=False, system=system)
    m5.instantiate()

    print(
        f"Beginning COPPER gem5 run: cpu={args.cpu_model} "
        f"prefetcher={args.prefetcher}"
    )
    exit_event = m5.simulate()
    print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")


if __name__ in ("__m5_main__", "__main__"):
    main()
