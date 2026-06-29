#!/usr/bin/env python3
"""Run a McPAT sensitivity pass from measured COPPER gem5 ROI stats.

This is intentionally a relative, fixed-architecture power sensitivity pass.
It does not claim calibrated silicon power.  It feeds measured ROI activity
into one AArch64-style proxy core/cache XML so policy-to-policy comparisons
share identical static assumptions.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
MCPAT_DIR = ROOT / "external" / "gem5" / "ext" / "mcpat"
MCPAT_EXE = ROOT / "external" / "gem5" / "build" / "mcpat" / "mcpat.exe"
MCPAT_TEMPLATE = MCPAT_DIR / "regression" / "test-0" / "power_region0.xml"
OUT_DIR = RESULTS / "mcpat_copper_sensitivity_20260618"
OUT_CSV = RESULTS / "copper_mcpat_sensitivity_20260618.csv"
OUT_MD = RESULTS / "COPPER_MCPAT_SENSITIVITY_20260618.md"

WORKLOADS = {
    "sqlite_medium": "sqlite_app_medium",
    "sqlite_stress": "sqlite_app_stress",
    "lua_medium": "lua_app_medium",
    "lua_stress": "lua_app_stress",
    "duktape_medium": "duktape_app_medium",
    "duktape_stress": "duktape_app_stress",
    "yyjson_medium": "yyjson_app_medium",
    "yyjson_stress": "yyjson_app_stress",
    "jsonsqlite_medium": "jsonsqlite_app_medium",
    "jsonsqlite_stress": "jsonsqlite_app_stress",
    "cachesvc_small": "cachesvc_app_small",
    "cachesvc_medium": "cachesvc_app_medium_key",
    "tlssvc_small": "tlssvc_app_smoke",
    "ossltlsbio_small": "ossltlsbio_app_smoke",
    "osslsha_small": "osslsha_app_smoke",
    "osslcrypto_small": "osslcrypto_app_smoke",
    "pcre2_smoke": "pcre2_pcre2_smoke",
    "pcre2_seed1": "pcre2_pcre2_seed1",
    "libxml2_tiny": "libxml2_xml_tiny_full",
    "libarchive_tiny": "libarchive_tar_tiny_full",
    "zstd_tiny": "zstd_zstd_tiny",
    "zstd_seed1": "zstd_zstd_seed1",
    "zlib_tiny": "zlib_zlib_tiny",
    "zlib_seed1": "zlib_zlib_seed1",
    "ossltlstcp_process_scale2": "ossltlstcp_tcp_netns_process_scale2",
    "ossltlstcp_process_scale3": "ossltlstcp_tcp_netns_process_scale3",
}
POLICIES = ["none", "naive", "copper_clpd64k_peb", "spp", "spp_copper_slack"]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def parse_stats_sections(path: Path) -> list[dict[str, float]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    sections: list[dict[str, float]] = []
    marker = "---------- Begin Simulation Statistics ----------"
    end_marker = "---------- End Simulation Statistics"
    start = 0
    while True:
        try:
            begin = text.index(marker, start)
            end = text.index(end_marker, begin)
        except ValueError:
            break
        stats: dict[str, float] = {}
        for line in text[begin:end].splitlines():
            if not line or line.startswith("-"):
                continue
            parts = line.split("#", 1)[0].split()
            if len(parts) < 2:
                continue
            try:
                stats[parts[0]] = float(parts[1])
            except ValueError:
                stats[parts[0]] = math.nan
        sections.append(stats)
        start = end + len(end_marker)
    return sections


def parse_config(path: Path) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    current: dict[str, str] | None = None
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = {}
            sections[line[1:-1]] = current
        elif current is not None and "=" in line:
            key, value = line.split("=", 1)
            current[key.strip()] = value.strip()
    return sections


def run_dir(tag: str, policy: str) -> Path:
    return RESULTS / f"gem5_arm_ubuntu_fs_{tag}_{policy}"


def sum_re(stats: dict[str, float], pattern: str) -> float:
    regex = re.compile(pattern)
    return sum(
        value
        for key, value in stats.items()
        if regex.search(key) and not math.isnan(value)
    )


def sum_committed_type(stats: dict[str, float], prefixes: tuple[str, ...]) -> float:
    total = 0.0
    for key, value in stats.items():
        if ".core.commitStats0.committedInstType::" not in key or math.isnan(value):
            continue
        inst_type = key.rsplit("::", 1)[-1]
        if inst_type == "total":
            continue
        if inst_type.startswith(prefixes):
            total += value
    return total


def first_float(stats: dict[str, float], key: str, default: float = 0.0) -> float:
    value = stats.get(key, default)
    return default if math.isnan(value) else value


def set_entry(component: ET.Element, kind: str, name: str, value: int | float | str) -> None:
    text = str(int(value)) if isinstance(value, float) and value.is_integer() else str(value)
    for child in component.findall(kind):
        if child.get("name") == name:
            child.set("value", text)
            return
    ET.SubElement(component, kind, {"name": name, "value": text})


def find_component(root: ET.Element, component_id: str) -> ET.Element:
    for component in root.iter("component"):
        if component.get("id") == component_id:
            return component
    raise KeyError(f"missing component id {component_id}")


def get_cache_config(
    config: dict[str, dict[str, str]], section: str, default_size: int, default_assoc: int
) -> dict[str, int]:
    values = config.get(section, {})
    return {
        "size": int(values.get("size", default_size)),
        "assoc": int(values.get("assoc", default_assoc)),
        "latency": max(
            1,
            int(values.get("data_latency", values.get("tag_latency", "1"))),
        ),
        "mshrs": int(values.get("mshrs", "8")),
        "write_buffers": int(values.get("write_buffers", "8")),
    }


def workload_activity(workload: str, tag: str, policy: str) -> dict[str, float | int | str]:
    directory = run_dir(tag, policy)
    sections = parse_stats_sections(directory / "stats.txt")
    if not sections:
        raise RuntimeError(f"no stats sections in {directory / 'stats.txt'}")
    stats = sections[0]
    config = parse_config(directory / "config.ini")
    clock_period_ticks = int(config.get("board.clk_domain", {}).get("clock", "333"))
    clock_mhz = max(1, int(round(1_000_000.0 / clock_period_ticks)))
    sim_ticks = int(first_float(stats, "simTicks"))
    roi_cycles = max(1, int(round(sim_ticks / clock_period_ticks)))

    committed = sum_re(stats, r"^board\.processor\.switch\d+\.core\.commitStats0\.numInsts$")
    committed_not_nop = sum_re(
        stats, r"^board\.processor\.switch\d+\.core\.commitStats0\.numInstsNotNOP$"
    )
    loads = sum_re(stats, r"^board\.processor\.switch\d+\.core\.commitStats0\.numLoadInsts$")
    stores = sum_re(stats, r"^board\.processor\.switch\d+\.core\.commitStats0\.numStoreInsts$")
    fp = sum_re(stats, r"^board\.processor\.switch\d+\.core\.commitStats0\.numFpInsts$")
    branches = sum_re(stats, r"^board\.processor\.switch\d+\.core\.fetchStats0\.numBranches$")
    simd = sum_committed_type(stats, ("Simd", "Float"))
    mul = sum_committed_type(stats, ("IntMult", "IntDiv"))
    int_insts = max(0.0, committed - fp)
    ialu = max(0.0, committed - loads - stores - branches - fp - simd - mul)

    l1d_read_access = sum_re(
        stats, r"^board\.cache_hierarchy\.l1d-cache-\d+\.ReadReq\.accesses::total$"
    )
    l1d_write_access = sum_re(
        stats, r"^board\.cache_hierarchy\.l1d-cache-\d+\.WriteReq\.accesses::total$"
    )
    l1d_read_miss = sum_re(
        stats, r"^board\.cache_hierarchy\.l1d-cache-\d+\.ReadReq\.misses::total$"
    )
    l1d_write_miss = sum_re(
        stats, r"^board\.cache_hierarchy\.l1d-cache-\d+\.WriteReq\.misses::total$"
    )
    l1i_read_access = sum_re(
        stats, r"^board\.cache_hierarchy\.l1i-cache-\d+\.ReadReq\.accesses::total$"
    )
    l1i_read_miss = sum_re(
        stats, r"^board\.cache_hierarchy\.l1i-cache-\d+\.ReadReq\.misses::total$"
    )

    l2_read_access = sum_re(
        stats,
        r"^board\.cache_hierarchy\.l2-cache-\d+\.(ReadReq|ReadSharedReq|ReadExReq)\.accesses::total$",
    )
    l2_read_miss = sum_re(
        stats,
        r"^board\.cache_hierarchy\.l2-cache-\d+\.(ReadReq|ReadSharedReq|ReadExReq)\.misses::total$",
    )
    l2_write_access = sum_re(
        stats,
        r"^board\.cache_hierarchy\.l2-cache-\d+\.(UpgradeReq|WritebackClean|WritebackDirty)\.accesses::total$",
    )
    l2_write_miss = sum_re(
        stats, r"^board\.cache_hierarchy\.l2-cache-\d+\.UpgradeReq\.misses::total$"
    )

    itlb_access = sum_re(
        stats, r"^board\.processor\.switch\d+\.core\.mmu\.itb\.instAccesses$"
    )
    itlb_miss = sum_re(stats, r"^board\.processor\.switch\d+\.core\.mmu\.itb\.misses$")
    dtlb_read_access = sum_re(
        stats, r"^board\.processor\.switch\d+\.core\.mmu\.dtb\.readAccesses$"
    )
    dtlb_read_miss = sum_re(
        stats, r"^board\.processor\.switch\d+\.core\.mmu\.dtb\.readMisses$"
    )

    return {
        "workload": workload,
        "policy": policy,
        "run_dir": rel(directory),
        "sim_ticks": sim_ticks,
        "roi_cycles": roi_cycles,
        "clock_mhz": clock_mhz,
        "committed": int(committed),
        "committed_not_nop": int(committed_not_nop),
        "loads": int(loads),
        "stores": int(stores),
        "branches": int(branches),
        "int_insts": int(int_insts),
        "fp_insts": int(fp),
        "simd_like": int(simd),
        "mul_like": int(mul),
        "ialu_like": int(ialu),
        "l1d_read_access": int(l1d_read_access),
        "l1d_write_access": int(l1d_write_access),
        "l1d_read_miss": int(l1d_read_miss),
        "l1d_write_miss": int(l1d_write_miss),
        "l1i_read_access": int(l1i_read_access),
        "l1i_read_miss": int(l1i_read_miss),
        "l2_read_access": int(l2_read_access),
        "l2_write_access": int(l2_write_access),
        "l2_read_miss": int(l2_read_miss),
        "l2_write_miss": int(l2_write_miss),
        "itlb_access": int(itlb_access),
        "itlb_miss": int(itlb_miss),
        "dtlb_read_access": int(dtlb_read_access),
        "dtlb_read_miss": int(dtlb_read_miss),
        "l1d_config": get_cache_config(config, "board.cache_hierarchy.l1d-cache-0", 16384, 8),
        "l1i_config": get_cache_config(config, "board.cache_hierarchy.l1i-cache-0", 16384, 8),
        "l2_config": get_cache_config(config, "board.cache_hierarchy.l2-cache-0", 262144, 16),
    }


def build_xml(activity: dict[str, float | int | str], core_model: str, out_xml: Path) -> None:
    template_text = MCPAT_TEMPLATE.read_text(encoding="utf-8", errors="replace")
    # The bundled McPAT regression XML has a few legacy `name="x"value="y"`
    # joins that McPAT's own parser tolerates but Python's stricter parser
    # rejects. Normalize those joins before writing generated XML.
    template_text = template_text.replace('"value=', '" value=')
    root = ET.fromstring(template_text)
    tree = ET.ElementTree(root)
    system = find_component(root, "system")
    core = find_component(root, "system.core0")
    icache = find_component(root, "system.core0.icache")
    dcache = find_component(root, "system.core0.dcache")
    itlb = find_component(root, "system.core0.itlb")
    dtlb = find_component(root, "system.core0.dtlb")
    btb = find_component(root, "system.core0.btargetbuf")
    l2 = find_component(root, "system.L20")

    clock_mhz = int(activity["clock_mhz"])
    roi_cycles = int(activity["roi_cycles"])
    committed = int(activity["committed"])
    committed_not_nop = int(activity["committed_not_nop"])
    fp_insts = int(activity["fp_insts"])
    int_insts = max(0, committed - fp_insts)
    branches = int(activity["branches"])
    loads = int(activity["loads"])
    stores = int(activity["stores"])
    ialu = int(activity["ialu_like"])
    fpu = int(activity["fp_insts"]) + int(activity["simd_like"])
    mul = int(activity["mul_like"])

    for name, value in [
        ("target_core_clockrate", clock_mhz),
        ("machine_bits", 64),
        ("virtual_address_width", 64),
        ("physical_address_width", 40),
    ]:
        set_entry(system, "param", name, value)
    set_entry(system, "stat", "total_cycles", roi_cycles)

    for name, value in [
        ("clock_rate", clock_mhz),
        ("x86", 0),
        ("instruction_length", 32),
        ("opcode_width", 11),
        ("number_hardware_threads", 1),
    ]:
        set_entry(core, "param", name, value)
    if core_model == "inorder_proxy":
        for name, value in [
            ("machine_type", 1),
            ("fetch_width", 1),
            ("decode_width", 1),
            ("issue_width", 1),
            ("peak_issue_width", 1),
            ("commit_width", 1),
            ("fp_issue_width", 1),
            ("ROB_size", 1),
            ("instruction_window_size", 1),
            ("fp_instruction_window_size", 1),
            ("load_buffer_size", 16),
            ("store_buffer_size", 16),
        ]:
            set_entry(core, "param", name, value)
    else:
        set_entry(core, "param", "machine_type", 0)

    core_stats = {
        "total_instructions": committed,
        "int_instructions": int_insts,
        "fp_instructions": fp_insts,
        "branch_instructions": branches,
        "branch_mispredictions": 0,
        "load_instructions": loads,
        "store_instructions": stores,
        "committed_instructions": committed,
        "committed_int_instructions": max(0, committed - fp_insts),
        "committed_fp_instructions": fp_insts,
        "pipeline_duty_cycle": 1,
        "total_cycles": roi_cycles,
        "ROB_reads": committed,
        "ROB_writes": committed,
        "rename_reads": committed,
        "rename_writes": committed,
        "fp_rename_reads": max(1, fp_insts),
        "fp_rename_writes": max(1, fp_insts),
        "inst_window_reads": max(1, int_insts),
        "inst_window_writes": max(1, int_insts),
        "inst_window_wakeup_accesses": max(1, int_insts),
        "fp_inst_window_reads": max(1, fp_insts),
        "fp_inst_window_writes": max(1, fp_insts),
        "fp_inst_window_wakeup_accesses": max(1, fp_insts),
        "int_regfile_reads": max(1, int_insts * 2),
        "float_regfile_reads": max(1, fp_insts * 2),
        "int_regfile_writes": max(1, int_insts),
        "float_regfile_writes": max(1, fp_insts),
        "function_calls": 0,
        "context_switches": 0,
        "ialu_accesses": max(1, ialu),
        "fpu_accesses": max(1, fpu),
        "mul_accesses": max(1, mul),
        "cdb_alu_accesses": max(1, ialu),
        "cdb_mul_accesses": max(1, mul),
        "cdb_fpu_accesses": max(1, fpu),
    }
    for unit in [
        "IFU",
        "LSU",
        "MemManU_I",
        "MemManU_D",
        "ALU",
        "MUL",
        "FPU",
        "ALU_cdb",
        "MUL_cdb",
        "FPU_cdb",
    ]:
        core_stats[f"{unit}_duty_cycle"] = 1
    for name, value in core_stats.items():
        set_entry(core, "stat", name, value)

    cache_params = [
        (icache, activity["l1i_config"], "system.core0.icache"),
        (dcache, activity["l1d_config"], "system.core0.dcache"),
        (l2, activity["l2_config"], "system.L20"),
    ]
    for component, config, component_id in cache_params:
        assert isinstance(config, dict)
        set_entry(component, "param", "size", config["size"])
        set_entry(component, "param", "assoc", config["assoc"])
        set_entry(component, "param", "block_size", 64)
        set_entry(component, "param", "latency", config["latency"])
        set_entry(component, "param", "throughput", config["latency"])
        set_entry(component, "param", "miss_buffer_size", config["mshrs"])
        set_entry(component, "param", "prefetch_buffer_size", max(2, config["mshrs"] // 2))
        set_entry(component, "param", "writeback_buffer_size", config["write_buffers"])
        if component_id == "system.L20":
            set_entry(component, "param", "clockrate", clock_mhz)

    set_entry(icache, "stat", "read_accesses", max(1, int(activity["l1i_read_access"])))
    set_entry(icache, "stat", "read_misses", int(activity["l1i_read_miss"]))
    set_entry(icache, "stat", "conflicts", 0)
    set_entry(icache, "stat", "duty_cycle", 1)

    set_entry(dcache, "stat", "read_accesses", max(1, int(activity["l1d_read_access"])))
    set_entry(dcache, "stat", "write_accesses", max(1, int(activity["l1d_write_access"])))
    set_entry(dcache, "stat", "read_misses", int(activity["l1d_read_miss"]))
    set_entry(dcache, "stat", "write_misses", int(activity["l1d_write_miss"]))
    set_entry(dcache, "stat", "conflicts", 0)
    set_entry(dcache, "stat", "duty_cycle", 1)

    set_entry(l2, "stat", "read_accesses", max(1, int(activity["l2_read_access"])))
    set_entry(l2, "stat", "write_accesses", max(1, int(activity["l2_write_access"])))
    set_entry(l2, "stat", "read_misses", int(activity["l2_read_miss"]))
    set_entry(l2, "stat", "write_misses", int(activity["l2_write_miss"]))
    set_entry(l2, "stat", "conflicts", 0)
    set_entry(l2, "stat", "duty_cycle", 1)

    set_entry(itlb, "stat", "total_accesses", max(1, int(activity["itlb_access"])))
    set_entry(itlb, "stat", "total_misses", int(activity["itlb_miss"]))
    set_entry(itlb, "stat", "conflicts", 0)
    set_entry(dtlb, "stat", "read_accesses", max(1, int(activity["dtlb_read_access"])))
    set_entry(dtlb, "stat", "read_misses", int(activity["dtlb_read_miss"]))
    set_entry(dtlb, "stat", "conflicts", 0)
    set_entry(btb, "stat", "read_accesses", max(1, branches))
    set_entry(btb, "stat", "write_accesses", max(1, branches // 8))

    out_xml.parent.mkdir(parents=True, exist_ok=True)
    tree.write(out_xml, encoding="utf-8", xml_declaration=True)


def parse_mcpat_output(text: str) -> dict[str, float]:
    metrics: dict[str, float] = {}
    current: str | None = None
    wanted = {
        "System": "system",
        "Core 0": "core",
        "L2 Cache": "l2",
        "Data Cache": "l1d",
        "Instruction Cache": "l1i",
    }
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.endswith(":"):
            name = stripped[:-1]
            if name in wanted:
                current = wanted[name]
            continue
        if current is None or "=" not in stripped:
            continue
        left, right = stripped.split("=", 1)
        key = re.sub(r"[^a-z0-9]+", "_", left.strip().lower()).strip("_")
        value_text = right.strip().split()[0]
        try:
            metrics[f"{current}_{key}"] = float(value_text)
        except ValueError:
            pass
    return metrics


def run_mcpat(xml_path: Path, out_path: Path, timeout_s: int) -> tuple[str, dict[str, float]]:
    env = os.environ.copy()
    env["PATH"] = (
        str(ROOT / "tools" / "msys64" / "ucrt64" / "bin")
        + os.pathsep
        + str(ROOT / "tools" / "msys64" / "usr" / "bin")
        + os.pathsep
        + env.get("PATH", "")
    )
    proc = subprocess.run(
        [
            str(MCPAT_EXE),
            "-infile",
            str(xml_path),
            "-print_level",
            "1",
            "-opt_for_clk",
            "0",
        ],
        cwd=str(MCPAT_DIR),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=timeout_s,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        proc.stdout + "\n--- stderr ---\n" + proc.stderr,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        return f"mcpat_return_{proc.returncode}", {}
    return "ok", parse_mcpat_output(proc.stdout)


def nonphysical_metric_keys(metrics: dict[str, float]) -> list[str]:
    checked = [
        "system_runtime_dynamic_power",
        "system_runtime_dynamic_energy",
        "system_total_runtime_energy",
        "core_runtime_dynamic_power",
    ]
    bad: list[str] = []
    for key in checked:
        value = metrics.get(key)
        if value is None or not math.isfinite(value) or value < 0.0 or value >= 1.0e20:
            bad.append(key)
    return bad


def pct_delta(value: float, base: float) -> float:
    return ((value / base) - 1.0) * 100.0 if base else 0.0


def row_for(workload: str, tag: str, policy: str, core_model: str, timeout_s: int) -> dict[str, str]:
    activity = workload_activity(workload, tag, policy)
    stem = f"{workload}_{policy}_{core_model}"
    xml_path = OUT_DIR / "xml" / f"{stem}.xml"
    out_path = OUT_DIR / "mcpat_out" / f"{stem}.txt"
    build_xml(activity, core_model, xml_path)
    status, metrics = run_mcpat(xml_path, out_path, timeout_s)
    bad_metrics = nonphysical_metric_keys(metrics) if status == "ok" else []
    if bad_metrics:
        status = "nonphysical_mcpat_proxy"
    row: dict[str, str] = {
        "workload": workload,
        "tag": tag,
        "policy": policy,
        "core_model": core_model,
        "status": status,
        "xml": rel(xml_path),
        "mcpat_output": rel(out_path),
    }
    if bad_metrics:
        row["error"] = "nonphysical metrics: " + ",".join(bad_metrics)
    for key, value in activity.items():
        if isinstance(value, (str, int, float)):
            row[key] = str(value)
    if not bad_metrics:
        for key, value in sorted(metrics.items()):
            row[f"mcpat_{key}"] = f"{value:.12g}"
    return row


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def write_outputs(rows: list[dict[str, str]]) -> None:
    by_workload: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        by_workload[row["workload"]][row["policy"]] = row

    delta_fields = [
        "mcpat_system_runtime_dynamic_power",
        "mcpat_system_runtime_dynamic_energy",
        "mcpat_system_total_runtime_energy",
        "mcpat_core_runtime_dynamic_power",
        "mcpat_l2_runtime_dynamic_power",
        "sim_ticks",
        "l1d_read_miss",
        "l2_read_miss",
    ]
    for workload, policies in by_workload.items():
        base = policies.get("none")
        if not base:
            continue
        for row in policies.values():
            for field in delta_fields:
                if field not in row or field not in base:
                    continue
                try:
                    row[f"{field}_delta_vs_none_pct"] = f"{pct_delta(float(row[field]), float(base[field])):.3f}"
                except ValueError:
                    pass

    all_fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in all_fields:
                all_fields.append(key)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=all_fields)
        writer.writeheader()
        writer.writerows(rows)

    ok_rows = [row for row in rows if row["status"] == "ok"]
    invalid_rows = [row for row in rows if row["status"] != "ok"]
    policies = [policy for policy in POLICIES if any(row["policy"] == policy for row in ok_rows)]
    lines = [
        "# COPPER McPAT Sensitivity Scorecard",
        "",
        "Scope: relative McPAT sensitivity from measured gem5 AArch64 ROI stats. The XML uses one fixed AArch64-style proxy core/cache model and changes only measured activity counters: cycles, committed instructions, cache/TLB accesses, and cache misses. This is not calibrated silicon power and does not include detailed COPPER metadata-table switching power.",
        "",
        f"Generated rows: {len(rows)}; successful McPAT rows: {len(ok_rows)}.",
        f"Invalid/nonphysical McPAT rows excluded from means: {len(invalid_rows)}.",
        "",
        "## Mean Delta vs None",
        "",
        "| Policy | Workloads | Runtime delta | McPAT total-energy delta | McPAT dynamic-energy delta | McPAT runtime-power delta | L1D miss delta | L2 read-miss delta |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for policy in policies:
        if policy == "none":
            continue
        subset = [row for row in ok_rows if row["policy"] == policy]
        lines.append(
            "| {policy} | {count} | {runtime:.3f}% | {total:.3f}% | {dyn:.3f}% | {power:.3f}% | {l1d:.3f}% | {l2:.3f}% |".format(
                policy=policy,
                count=len(subset),
                runtime=mean([float(row.get("sim_ticks_delta_vs_none_pct", "nan")) for row in subset if "sim_ticks_delta_vs_none_pct" in row]),
                total=mean([float(row.get("mcpat_system_total_runtime_energy_delta_vs_none_pct", "nan")) for row in subset if "mcpat_system_total_runtime_energy_delta_vs_none_pct" in row]),
                dyn=mean([float(row.get("mcpat_system_runtime_dynamic_energy_delta_vs_none_pct", "nan")) for row in subset if "mcpat_system_runtime_dynamic_energy_delta_vs_none_pct" in row]),
                power=mean([float(row.get("mcpat_system_runtime_dynamic_power_delta_vs_none_pct", "nan")) for row in subset if "mcpat_system_runtime_dynamic_power_delta_vs_none_pct" in row]),
                l1d=mean([float(row.get("l1d_read_miss_delta_vs_none_pct", "nan")) for row in subset if "l1d_read_miss_delta_vs_none_pct" in row]),
                l2=mean([float(row.get("l2_read_miss_delta_vs_none_pct", "nan")) for row in subset if "l2_read_miss_delta_vs_none_pct" in row]),
            )
        )

    def pairwise(label: str, lhs: str, rhs: str, field: str) -> str:
        diffs = []
        wins = 0
        total = 0
        for workload, policies_for_workload in by_workload.items():
            left = policies_for_workload.get(lhs)
            right = policies_for_workload.get(rhs)
            if not left or not right or left.get("status") != "ok" or right.get("status") != "ok":
                continue
            if field not in left or field not in right:
                continue
            lval = float(left[field])
            rval = float(right[field])
            diff = pct_delta(lval, rval)
            diffs.append(diff)
            total += 1
            if lval <= rval:
                wins += 1
        return f"- {label}: {lhs} <= {rhs} on {wins}/{total}; mean delta {mean(diffs):.3f}%."

    lines.extend(
        [
            "",
            "## Pairwise Checks",
            "",
            pairwise(
                "McPAT total runtime energy",
                "copper_clpd64k_peb",
                "naive",
                "mcpat_system_total_runtime_energy",
            ),
            pairwise(
                "McPAT runtime dynamic energy",
                "copper_clpd64k_peb",
                "naive",
                "mcpat_system_runtime_dynamic_energy",
            ),
            pairwise(
                "McPAT total runtime energy",
                "spp_copper_slack",
                "spp",
                "mcpat_system_total_runtime_energy",
            ),
            pairwise(
                "McPAT runtime dynamic energy",
                "spp_copper_slack",
                "spp",
                "mcpat_system_runtime_dynamic_energy",
            ),
            "",
            "## Per-Workload McPAT Total-Energy Delta",
            "",
            "| Workload | Naive | COPPER | SPP | SPP+COPPER slack |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for workload in sorted(by_workload):
        policies_for_workload = by_workload[workload]
        if policies_for_workload.get("none", {}).get("status") != "ok":
            continue
        lines.append(
            "| {workload} | {naive} | {copper} | {spp} | {slack} |".format(
                workload=workload,
                naive=policies_for_workload.get("naive", {}).get("mcpat_system_total_runtime_energy_delta_vs_none_pct", "") + "%",
                copper=policies_for_workload.get("copper_clpd64k_peb", {}).get("mcpat_system_total_runtime_energy_delta_vs_none_pct", "") + "%",
                spp=policies_for_workload.get("spp", {}).get("mcpat_system_total_runtime_energy_delta_vs_none_pct", "") + "%",
                slack=policies_for_workload.get("spp_copper_slack", {}).get("mcpat_system_total_runtime_energy_delta_vs_none_pct", "") + "%",
            )
        )

    lines.extend(
        [
            "",
            "## Caveats",
            "",
            "- The McPAT XML is a fixed proxy and is used for relative sensitivity only.",
            "- The gem5 CPU model is TimingSimple-style; the McPAT core model is therefore an architectural proxy rather than a matched implementation.",
            "- COPPER metadata table, proof-table, and comparator switching are not separately modeled here; those remain RTL/Vivado or CACTI/RTL-power work.",
            "- Rows where McPAT emits nonphysical sentinel-scale energy/power values are marked invalid and excluded from aggregate means.",
            "- This scorecard is useful as a reviewer-facing sanity check that measured COPPER traffic does not obviously erase the energy story.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--core-model", choices=["ooo_proxy", "inorder_proxy"], default="ooo_proxy")
    parser.add_argument("--workloads", nargs="*", default=list(WORKLOADS))
    parser.add_argument("--policies", nargs="*", default=POLICIES)
    parser.add_argument("--timeout-s", type=int, default=90)
    args = parser.parse_args()

    if not MCPAT_EXE.exists():
        raise SystemExit(f"McPAT executable not found: {MCPAT_EXE}")
    rows = []
    for workload in args.workloads:
        tag = WORKLOADS[workload]
        for policy in args.policies:
            rows.append(row_for(workload, tag, policy, args.core_model, args.timeout_s))
    write_outputs(rows)
    print(f"wrote {OUT_CSV}")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
