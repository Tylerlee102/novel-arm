import argparse
import base64
from pathlib import Path
import shlex
import textwrap
import zlib

from m5.objects import (
    AMPMPrefetcher,
    ArmDefaultRelease,
    BOPPrefetcher,
    CopperPrefetcher,
    CopperCompanionPrefetcher,
    DCPTPrefetcher,
    IndirectMemoryPrefetcher,
    IrregularStreamBufferPrefetcher,
    L2XBar,
    MultiPrefetcher,
    NULL,
    SignaturePathPrefetcher,
    StridePrefetcher,
    VExpress_GEM5_Foundation,
)

from gem5.components.boards.arm_board import ArmBoard
from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import (
    PrivateL1PrivateL2CacheHierarchy,
)
from gem5.components.cachehierarchies.classic.caches.l1dcache import L1DCache
from gem5.components.cachehierarchies.classic.caches.l1icache import L1ICache
from gem5.components.cachehierarchies.classic.caches.l2cache import L2Cache
from gem5.components.memory import DualChannelDDR4_2400
from gem5.components.processors.cpu_types import get_cpu_type_from_str
from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA
from gem5.resources.resource import (
    BootloaderResource,
    DiskImageResource,
    KernelResource,
    obtain_resource,
)
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
from gem5.utils.requires import requires


ROOT = Path.cwd()


def mix64_host(x):
    x = (x + 0x9E3779B97F4A7C15) & ((1 << 64) - 1)
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & ((1 << 64) - 1)
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & ((1 << 64) - 1)
    return x ^ (x >> 31)


def make_pointer_payload(size, seed):
    payload = bytearray()
    checksum = 0x243F6A8885A308D3
    words = (size + 7) // 8
    for i in range(words):
        x = mix64_host((i << 32) ^ (seed << 7) ^ 0x4F53534C434C49)
        value = 0x00000000400000 + ((x & 0x1FFFFF) << 3)
        checksum ^= mix64_host(value + i)
        payload.extend(value.to_bytes(8, "little"))
    return bytes(payload[:size]), checksum


def make_copper_prefetcher(args, naive: bool):
    return CopperPrefetcher(
        naive=naive,
        pointer_bytes=args.pointer_bytes,
        pointer_alignment=args.pointer_alignment,
        min_addr=args.candidate_min,
        max_addr=args.candidate_max,
        recent_entries=args.recent_entries,
        provenance_entries=args.provenance_entries,
        value_token_bits=args.value_token_bits,
        invalidate_on_evict=False,
        chase_prefetch_fills=(not naive),
        translate_cross_page=True,
        clear_on_stats_reset=args.clear_copper_on_stats_reset,
        line_provenance=args.line_provenance,
        queue_size=args.prefetch_queue_size,
        max_prefetch_requests_with_pending_translation=args.prefetch_queue_size,
        latency=1,
        use_virtual_addresses=True,
        prefetch_on_access=True,
    )


class CopperFSCacheHierarchy(PrivateL1PrivateL2CacheHierarchy):
    def __init__(self, *hier_args, copper_args, **hier_kwargs):
        super().__init__(*hier_args, **hier_kwargs)
        object.__setattr__(self, "_copper_args", copper_args)

    def _make_l1d_prefetcher(self, core_obj):
        copper_args = self._copper_args
        kind = copper_args.prefetcher
        if kind == "none":
            return NULL
        if kind == "stride":
            return StridePrefetcher(
                degree=1,
                latency=1,
                prefetch_on_access=True,
                use_virtual_addresses=False,
            )
        if kind == "bop":
            return BOPPrefetcher(
                latency=1,
                queue_size=copper_args.prefetch_queue_size,
            )
        if kind == "spp":
            return SignaturePathPrefetcher(
                latency=1,
                queue_size=copper_args.prefetch_queue_size,
            )
        if kind == "spp_copper":
            spp = SignaturePathPrefetcher(
                latency=1,
                queue_size=copper_args.prefetch_queue_size,
            )
            copper = make_copper_prefetcher(copper_args, naive=False)
            copper.registerMMU(core_obj.mmu)
            return MultiPrefetcher(prefetchers=[spp, copper])
        if kind == "spp_copper_slack":
            spp = SignaturePathPrefetcher(
                latency=1,
                queue_size=copper_args.prefetch_queue_size,
            )
            copper = make_copper_prefetcher(copper_args, naive=False)
            copper.registerMMU(core_obj.mmu)
            return CopperCompanionPrefetcher(primary=spp, companion=copper)
        if kind == "dcpt":
            return DCPTPrefetcher(
                latency=1,
                queue_size=copper_args.prefetch_queue_size,
            )
        if kind == "ampm":
            return AMPMPrefetcher(
                latency=1,
                queue_size=copper_args.prefetch_queue_size,
            )
        if kind == "indirect":
            return IndirectMemoryPrefetcher(
                latency=1,
                queue_size=copper_args.prefetch_queue_size,
            )
        if kind == "isb":
            return IrregularStreamBufferPrefetcher(
                latency=1,
                queue_size=copper_args.prefetch_queue_size,
            )
        if kind == "naive":
            pf = make_copper_prefetcher(copper_args, naive=True)
        elif kind == "copper":
            pf = make_copper_prefetcher(copper_args, naive=False)
        else:
            raise ValueError(kind)
        pf.registerMMU(core_obj.mmu)
        return pf

    def incorporate_cache(self, board):
        board.connect_system_port(self.membus.cpu_side_ports)

        for _, port in board.get_mem_ports():
            self.membus.mem_side_ports = port

        self.l2buses = [
            L2XBar() for _ in range(board.get_processor().get_num_cores())
        ]

        processor = board.get_processor()
        for i, core in enumerate(processor.get_cores()):
            core_obj = core.get_simobject()
            if self._copper_args.switch_roi_to_timing:
                core_obj_for_mmu = processor._switchable_cores[
                    processor._switch_key
                ][i].get_simobject()
            else:
                core_obj_for_mmu = core_obj
            l2_node = self.add_root_child(
                f"l2-cache-{i}", L2Cache(size=self._l2_size)
            )
            l1i_node = l2_node.add_child(
                f"l1i-cache-{i}", L1ICache(size=self._l1i_size)
            )
            l1d_node = l2_node.add_child(
                f"l1d-cache-{i}", L1DCache(size=self._l1d_size)
            )

            l1i_node.cache.prefetcher = NULL
            l2_node.cache.prefetcher = NULL
            l1d_node.cache.prefetcher = self._make_l1d_prefetcher(
                core_obj_for_mmu
            )

            self.l2buses[i].mem_side_ports = l2_node.cache.cpu_side
            self.membus.cpu_side_ports = l2_node.cache.mem_side

            l1i_node.cache.mem_side = self.l2buses[i].cpu_side_ports
            l1d_node.cache.mem_side = self.l2buses[i].cpu_side_ports

            core.connect_icache(l1i_node.cache.cpu_side)
            core.connect_dcache(l1d_node.cache.cpu_side)

            self._connect_table_walker(i, core)

            if board.get_processor().get_isa() == ISA.X86:
                int_req_port = self.membus.mem_side_ports
                int_resp_port = self.membus.cpu_side_ports
                core.connect_interrupt(int_req_port, int_resp_port)
            else:
                core.connect_interrupt()

        if board.has_coherent_io():
            self._setup_io_cache(board)


parser = argparse.ArgumentParser()
parser.add_argument("--cpu", default="atomic", choices=["atomic", "timing"])
parser.add_argument("--switch-roi-to-timing", action="store_true")
parser.add_argument("--max-ticks", type=int, default=None)
parser.add_argument("--kernel-arg", action="append", default=[])
parser.add_argument("--nodes", type=int, default=512)
parser.add_argument("--degree", type=int, default=4)
parser.add_argument("--passes", type=int, default=4)
parser.add_argument("--seeds", type=int, default=3)
parser.add_argument("--run-native", action="store_true")
parser.add_argument("--native-only", action="store_true")
parser.add_argument("--tiny-guest", action="store_true")
parser.add_argument(
    "--prefetcher",
    choices=[
        "none",
        "stride",
        "bop",
        "spp",
        "spp_copper",
        "spp_copper_slack",
        "dcpt",
        "ampm",
        "indirect",
        "isb",
        "naive",
        "copper",
    ],
    default="stride",
)
parser.add_argument("--candidate-min", type=lambda x: int(x, 0), default=0x10000)
parser.add_argument("--candidate-max", type=lambda x: int(x, 0), default=0x13000)
parser.add_argument("--pointer-bytes", type=int, default=4)
parser.add_argument("--pointer-alignment", type=int, default=4)
parser.add_argument("--recent-entries", type=int, default=4096)
parser.add_argument("--provenance-entries", type=int, default=16384)
parser.add_argument("--value-token-bits", type=int, default=32)
parser.add_argument("--prefetch-queue-size", type=int, default=64)
parser.add_argument("--line-provenance", action="store_true")
parser.add_argument("--clear-copper-on-stats-reset", action="store_true")
parser.add_argument(
    "--resource-dir",
    type=Path,
    default=ROOT / "tools" / "msys64" / "home" / "tyboy" / ".cache" / "gem5",
)
parser.add_argument("--kernel-path", type=Path, default=None)
parser.add_argument("--disk-image-path", type=Path, default=None)
parser.add_argument("--bootloader-path", type=Path, default=None)
parser.add_argument(
    "--native-binary",
    type=Path,
    default=ROOT / "research" / "bin" / "aarch64_pointer_bench_small",
)
parser.add_argument("--native-arg", action="append", default=[])
parser.add_argument("--native-after-arg", action="append", default=[])
parser.add_argument(
    "--native-shell-command",
    default="",
    help="Guest shell script to execute as the native ROI after installing /tmp/aarch64_native_workload.",
)
parser.add_argument(
    "--native-shell-command-file",
    type=Path,
    default=None,
    help="Host file containing the guest shell script to execute as the native ROI.",
)
parser.add_argument(
    "--native-pre-command",
    action="append",
    default=[],
    help="Shell command(s) to run in the guest after installing the native binary and before the native ROI.",
)
parser.add_argument(
    "--native-pre-command-file",
    type=Path,
    action="append",
    default=[],
    help="Host file(s) containing guest shell command blocks to run before the native ROI.",
)
parser.add_argument("--native-self-roi", action="store_true")
parser.add_argument(
    "--native-preload-pointer-file",
    action="store_true",
    help="Create a deterministic pointer-shaped guest input file before native ROI.",
)
parser.add_argument("--native-preload-path", default="/tmp/copper_native_input.bin")
parser.add_argument("--native-preload-bytes", type=int, default=262144)
parser.add_argument("--native-preload-seed", type=int, default=0)
parser.add_argument("--official-gapbs-suite", action="store_true")
parser.add_argument("--official-gapbs-scale", type=int, default=10)
parser.add_argument("--official-gapbs-degree", type=int, default=8)
parser.add_argument(
    "--official-gapbs-kernels",
    nargs="+",
    choices=["bfs", "cc", "pr", "sssp", "bc", "tc"],
    default=["bfs", "cc", "pr", "sssp"],
)
parser.add_argument("--olden-suite", action="store_true")
parser.add_argument(
    "--olden-bin-dir",
    type=Path,
    default=ROOT / "research" / "bin" / "olden_aarch64",
)
parser.add_argument(
    "--olden-kernels",
    nargs="+",
    choices=["treeadd", "bisort", "mst", "health"],
    default=["treeadd", "bisort", "mst", "health"],
)
parser.add_argument(
    "--olden-size",
    choices=["small", "medium"],
    default="small",
    help="Input-size preset for the Olden full-system suite.",
)
args = parser.parse_args()
if args.native_shell_command_file is not None:
    if args.native_shell_command:
        raise SystemExit(
            "--native-shell-command and --native-shell-command-file are mutually exclusive"
        )
    args.native_shell_command = args.native_shell_command_file.read_text(
        encoding="utf-8"
    )
for native_pre_command_file in args.native_pre_command_file:
    args.native_pre_command.append(
        native_pre_command_file.read_text(encoding="utf-8")
    )

requires(isa_required=ISA.ARM)

guest_source = (
    ROOT / "research" / ("fs_copper_tiny_guest.py" if args.tiny_guest else "fs_copper_graph_guest.py")
)
guest_py = guest_source.read_text(
    encoding="utf-8"
)
guest_b64 = base64.b64encode(zlib.compress(guest_py.encode("utf-8"), 9)).decode(
    "ascii"
)
guest_b64 = "\n".join(textwrap.wrap(guest_b64, 76))

native_b64 = ""
if args.native_only:
    args.run_native = True
if args.official_gapbs_suite:
    args.run_native = True
    args.native_only = True
if args.olden_suite:
    args.run_native = True
    args.native_only = True

if args.run_native and not args.official_gapbs_suite and not args.olden_suite:
    native_b64 = base64.b64encode(args.native_binary.read_bytes()).decode("ascii")
    native_b64 = "\n".join(textwrap.wrap(native_b64, 76))

cache_hierarchy = CopperFSCacheHierarchy(
    l1d_size="16KiB",
    l1i_size="16KiB",
    l2_size="256KiB",
    copper_args=args,
)
memory = DualChannelDDR4_2400(size="2GiB")
if args.switch_roi_to_timing:
    processor = SimpleSwitchableProcessor(
        starting_core_type=get_cpu_type_from_str("atomic"),
        switch_core_type=get_cpu_type_from_str("timing"),
        num_cores=2,
        isa=ISA.ARM,
    )
else:
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

native_block = ""
if args.official_gapbs_suite:
    workbegin = ""
    if args.switch_roi_to_timing:
        workbegin = "echo COPPER_FS_WORKBEGIN\nm5 workbegin 0 0 || true\n"
    suite_dir = ROOT / "research" / "bin" / "gapbs_aarch64_official"
    suite_args = {
        "bfs": ["-g", str(args.official_gapbs_scale), "-k", str(args.official_gapbs_degree), "-n", "1", "-r", "1"],
        "cc": ["-g", str(args.official_gapbs_scale), "-k", str(args.official_gapbs_degree), "-n", "1"],
        "pr": ["-g", str(args.official_gapbs_scale), "-k", str(args.official_gapbs_degree), "-n", "1", "-i", "2"],
        "sssp": ["-g", str(args.official_gapbs_scale), "-k", str(args.official_gapbs_degree), "-n", "1", "-r", "1", "-d", "2"],
        "bc": ["-g", str(args.official_gapbs_scale), "-k", str(args.official_gapbs_degree), "-n", "1", "-i", "1", "-r", "1"],
        "tc": ["-g", str(args.official_gapbs_scale), "-k", str(args.official_gapbs_degree), "-n", "1"],
    }
    suite_jobs = [
        (label, suite_dir / label, suite_args[label])
        for label in args.official_gapbs_kernels
    ]
    decode_blocks = []
    run_blocks = []
    for label, binary, job_args in suite_jobs:
        payload = base64.b64encode(binary.read_bytes()).decode("ascii")
        payload = "\n".join(textwrap.wrap(payload, 76))
        guest_path = f"/tmp/gapbs_{label}"
        decode_blocks.append(
            f"""cat > {guest_path}.b64 <<'B64_{label}'
{payload}
B64_{label}
base64 -d {guest_path}.b64 > {guest_path}
chmod +x {guest_path}
"""
        )
        arg_text = " ".join(shlex.quote(item) for item in job_args)
        run_blocks.append(
            f"""echo COPPER_FS_NATIVE_JOB_START {label}
m5 resetstats || true
job_rc=0
{guest_path} {arg_text} || job_rc=$?
echo COPPER_FS_NATIVE_JOB_DONE {label} rc=${{job_rc}}
m5 dumpstats || true
"""
        )
    native_block = f"""
{''.join(decode_blocks)}
{workbegin}\
{''.join(run_blocks)}
"""
elif args.olden_suite:
    workbegin = ""
    if args.switch_roi_to_timing:
        workbegin = "echo COPPER_FS_WORKBEGIN\nm5 workbegin 0 0 || true\n"
    suite_dir = args.olden_bin_dir
    olden_presets = {
        "small": {
            "treeadd": ["16", "1"],
            "bisort": ["4096", "1", "0"],
            "mst": ["512"],
            "health": ["4", "60", "7"],
        },
        "medium": {
            "treeadd": ["17", "1"],
            "bisort": ["8192", "1", "0"],
            "mst": ["768"],
            "health": ["5", "80", "7"],
        },
    }
    suite_args = olden_presets[args.olden_size]
    suite_jobs = [
        (label, suite_dir / label, suite_args[label])
        for label in args.olden_kernels
    ]
    decode_blocks = []
    run_blocks = []
    for label, binary, job_args in suite_jobs:
        payload = base64.b64encode(binary.read_bytes()).decode("ascii")
        payload = "\n".join(textwrap.wrap(payload, 76))
        guest_path = f"/tmp/olden_{label}"
        decode_blocks.append(
            f"""cat > {guest_path}.b64 <<'B64_OLDEN_{label}'
{payload}
B64_OLDEN_{label}
base64 -d {guest_path}.b64 > {guest_path}
chmod +x {guest_path}
"""
        )
        arg_text = " ".join(shlex.quote(item) for item in job_args)
        run_blocks.append(
            f"""echo COPPER_FS_NATIVE_JOB_START olden_{label}
m5 resetstats || true
job_rc=0
{guest_path} {arg_text} || job_rc=$?
echo COPPER_FS_NATIVE_JOB_DONE olden_{label} rc=${{job_rc}}
m5 dumpstats || true
"""
        )
    native_block = f"""
{''.join(decode_blocks)}
{workbegin}\
{''.join(run_blocks)}
"""
elif args.run_native:
    native_args = " ".join(shlex.quote(str(item)) for item in args.native_arg)
    native_after_args = " ".join(
        shlex.quote(str(item)) for item in args.native_after_arg
    )
    native_pre_command_block = ""
    if args.native_pre_command:
        native_pre_command_block = (
            "echo COPPER_FS_NATIVE_PRE_COMMAND_START\n"
            + "\n".join(str(item) for item in args.native_pre_command)
            + "\necho COPPER_FS_NATIVE_PRE_COMMAND_DONE\n"
        )
    preload_block = ""
    if args.native_preload_pointer_file:
        preload_path = shlex.quote(args.native_preload_path)
        preload_payload, preload_checksum = make_pointer_payload(
            args.native_preload_bytes, args.native_preload_seed
        )
        preload_b64 = base64.b64encode(preload_payload).decode("ascii")
        preload_b64 = "\n".join(textwrap.wrap(preload_b64, 76))
        preload_block = f"""echo COPPER_FS_NATIVE_PRELOAD_START
cat > /tmp/copper_native_input.b64 <<'B64_PRELOAD'
{preload_b64}
B64_PRELOAD
base64 -d /tmp/copper_native_input.b64 > {preload_path}
echo COPPER_FS_NATIVE_PRELOAD_DONE path={preload_path} bytes={args.native_preload_bytes} seed={args.native_preload_seed} checksum=0x{preload_checksum:016x}
ls -l {preload_path} || true
"""
    workbegin = ""
    if args.switch_roi_to_timing and not args.native_self_roi:
        workbegin = "echo COPPER_FS_WORKBEGIN\nm5 workbegin 0 0 || true\n"
    shell_stats = ""
    if not args.native_self_roi:
        shell_stats = """echo COPPER_FS_NATIVE_ROI_RESET
m5 resetstats || true
"""
    if args.native_shell_command:
        native_run_block = f"""cat > /tmp/copper_native_shell_roi.sh <<'COPPER_NATIVE_SHELL_ROI'
{args.native_shell_command}
COPPER_NATIVE_SHELL_ROI
chmod +x /tmp/copper_native_shell_roi.sh
/tmp/copper_native_shell_roi.sh || native_rc=$?
"""
    else:
        native_run_block = f"""/tmp/aarch64_native_workload {native_args} || native_rc=$?
"""
    native_block = f"""
cat > /tmp/aarch64_native.b64 <<'B64'
{native_b64}
B64
base64 -d /tmp/aarch64_native.b64 > /tmp/aarch64_native_workload
chmod +x /tmp/aarch64_native_workload
native_rc=0
{preload_block}\
{native_pre_command_block}\
{workbegin}\
{shell_stats}\
echo COPPER_FS_NATIVE_A64_START
{native_run_block}\
echo COPPER_FS_NATIVE_A64_DONE rc=${{native_rc}}
if [ -n "{native_after_args}" ]; then
  native_after_rc=0
  echo COPPER_FS_NATIVE_AFTER_A64_START
  /tmp/aarch64_native_workload {native_after_args} || native_after_rc=$?
  echo COPPER_FS_NATIVE_AFTER_A64_DONE rc=${{native_after_rc}}
fi
"""

if args.native_only:
    guest_block = "echo COPPER_FS_GUEST_PY_SKIPPED\n"
elif args.tiny_guest:
    guest_block = f"""echo COPPER_FS_GUEST_PY_START
python3 - <<'PYGUEST'
{guest_py}
PYGUEST
"""
else:
    guest_block = f"""echo COPPER_FS_GUEST_PY_START
python3 - <<'PYGUEST'
import base64
import sys
import zlib
sys.argv = [
    'fs_copper_graph_guest.py',
    '--nodes', '{args.nodes}',
    '--degree', '{args.degree}',
    '--passes', '{args.passes}',
    '--seeds', '{args.seeds}',
]
payload = \"\"\"{guest_b64}\"\"\"
exec(zlib.decompress(base64.b64decode(payload)).decode('utf-8'))
PYGUEST
"""

roi_reset_block = ""
if not args.native_only:
    roi_reset_block = """echo COPPER_FS_ROI_RESET
m5 resetstats || true
"""

workend_block = ""
if args.switch_roi_to_timing and not args.native_self_roi:
    workend_block = "echo COPPER_FS_WORKEND\nm5 workend 0 0 || true\n"

readfile_script = f"""#!/bin/bash
set -u
echo COPPER_FS_RUNSCRIPT_START
uname -a || true
uname -m || true
{roi_reset_block}
{guest_block}
{native_block}
echo COPPER_FS_ROI_DUMP
m5 dumpstats || true
{workend_block}\
echo COPPER_FS_RUNSCRIPT_DONE
m5 exit
"""

kernel_path = args.kernel_path or (
    args.resource_dir / "arm64-linux-kernel-6.8.12-1.0.0"
)
disk_image_path = args.disk_image_path or (
    args.resource_dir / "arm-ubuntu-24.04-img-3.0.0"
)
bootloader_path = args.bootloader_path or (
    args.resource_dir / "arm64-bootloader-foundation-2.0.0"
)

if kernel_path.exists() and disk_image_path.exists() and bootloader_path.exists():
    kernel_resource = KernelResource(local_path=str(kernel_path))
    disk_resource = DiskImageResource(
        local_path=str(disk_image_path), root_partition="2"
    )
    bootloader_resource = BootloaderResource(local_path=str(bootloader_path))
else:
    kernel_resource = obtain_resource(
        "arm64-linux-kernel-6.8.12", resource_version="1.0.0"
    )
    disk_resource = obtain_resource(
        "arm-ubuntu-24.04-img", resource_version="3.0.0"
    )
    bootloader_resource = obtain_resource(
        "arm64-bootloader-foundation", resource_version="2.0.0"
    )

board.set_kernel_disk_workload(
    kernel=kernel_resource,
    disk_image=disk_resource,
    bootloader=bootloader_resource,
    readfile_contents=readfile_script,
    kernel_args=board.get_default_kernel_args() + args.kernel_arg,
)

on_exit_event = None
if args.switch_roi_to_timing:
    def handle_workbegin():
        switched = False
        while True:
            if not switched:
                print("COPPER_FS_HOST_SWITCH_TO_TIMING")
                processor.switch()
                switched = True
            yield False

    def handle_workend():
        while True:
            print("COPPER_FS_HOST_WORKEND")
            yield False

    on_exit_event = {
        ExitEvent.WORKBEGIN: handle_workbegin(),
        ExitEvent.WORKEND: handle_workend(),
    }

simulator = Simulator(board=board, on_exit_event=on_exit_event)
simulator.run(max_ticks=args.max_ticks)
