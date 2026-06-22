import argparse

from m5.objects import ArmDefaultRelease, VExpress_GEM5_Foundation

from gem5.components.boards.arm_board import ArmBoard
from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import (
    PrivateL1PrivateL2CacheHierarchy,
)
from gem5.components.memory import DualChannelDDR4_2400
from gem5.components.processors.cpu_types import CPUTypes, get_cpu_type_from_str
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA
from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator
from gem5.utils.requires import requires


parser = argparse.ArgumentParser()
parser.add_argument("--cpu", default="atomic", choices=["atomic", "timing"])
parser.add_argument("--max-ticks", type=int, default=None)
parser.add_argument("--kernel-arg", action="append", default=[])
args = parser.parse_args()

requires(isa_required=ISA.ARM)

cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
    l1d_size="16KiB",
    l1i_size="16KiB",
    l2_size="256KiB",
)
memory = DualChannelDDR4_2400(size="2GiB")
processor = SimpleProcessor(
    cpu_type=get_cpu_type_from_str(args.cpu),
    num_cores=2,
    isa=ISA.ARM,
)

board = ArmBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
    release=ArmDefaultRelease(),
    platform=VExpress_GEM5_Foundation(),
)

readfile_script = """#!/bin/bash
set -u
echo COPPER_FS_PROBE_START
uname -a || true
uname -m || true
cat /proc/cpuinfo | head -40 || true
python3 --version || true
echo COPPER_FS_PROBE_DONE
m5 exit
"""

board.set_kernel_disk_workload(
    kernel=obtain_resource("arm64-linux-kernel-6.8.12", resource_version="1.0.0"),
    disk_image=obtain_resource("arm-ubuntu-24.04-img", resource_version="3.0.0"),
    bootloader=obtain_resource("arm64-bootloader-foundation", resource_version="2.0.0"),
    readfile_contents=readfile_script,
    kernel_args=board.get_default_kernel_args() + args.kernel_arg,
)

simulator = Simulator(board=board)
simulator.run(max_ticks=args.max_ticks)
