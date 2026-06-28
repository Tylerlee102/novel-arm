#!/usr/bin/env python3
"""Record local raw gem5 rerun provenance without promoting broad claims."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "gem5_raw_rerun_manifest.csv"


@dataclass(frozen=True)
class RawRerunSpec:
    tag: str
    run_prefix: str
    summary_path: Path
    terminal_result: str
    policies: tuple[str, ...]
    notes: str


COMMON_RERUN_POLICIES = ("none", "naive", "copper_clpd64k_peb", "spp", "spp_copper_slack")


SPECS = (
    RawRerunSpec(
        tag="codex_raw_smoke",
        run_prefix="gem5_arm_ubuntu_fs_cachesvc_codex_raw_smoke_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_cachesvc_app" / "cachesvc_codex_raw_smoke_summary.csv",
        terminal_result="CACHESVC_COPPER_RESULT",
        policies=("none", "copper_clpd64k_peb"),
        notes=(
            "Fresh local raw gem5 ARM full-system cache-service smoke rerun. "
            "This proves the smoke path is runnable in this local environment; "
            "it is not a full workload/config matrix or clone-local CI proof."
        ),
    ),
    RawRerunSpec(
        tag="codex_raw_smoke_seed8",
        run_prefix="gem5_arm_ubuntu_fs_cachesvc_codex_raw_smoke_seed8_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_cachesvc_app" / "cachesvc_codex_raw_smoke_seed8_summary.csv",
        terminal_result="CACHESVC_COPPER_RESULT",
        policies=("none", "copper_clpd64k_peb"),
        notes=(
            "Fresh local raw gem5 ARM full-system cache-service seed-8 rerun. "
            "Together with codex_raw_smoke, this provides repeated raw samples for "
            "the no-prefetch and COPPER smoke comparison; it is not the full final "
            "workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="codex_raw_zlib_tiny",
        run_prefix="gem5_arm_ubuntu_fs_zlib_codex_raw_zlib_tiny_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_zlib_app" / "zlib_codex_raw_zlib_tiny_summary.csv",
        terminal_result="ZLIB_COPPER_RESULT",
        policies=("none", "stride", "naive", "copper_clpd64k_peb", "dcpt", "spp", "ampm", "spp_copper_slack"),
        notes=(
            "Fresh local raw gem5 ARM full-system zlib compression-library rerun. "
            "This proves another public benchmark family is runnable in this local environment; "
            "it is not a full workload/config matrix or clone-local CI proof."
        ),
    ),
    RawRerunSpec(
        tag="codex_raw_zlib_tiny_seed12",
        run_prefix="gem5_arm_ubuntu_fs_zlib_codex_raw_zlib_tiny_seed12_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_zlib_app" / "zlib_codex_raw_zlib_tiny_seed12_summary.csv",
        terminal_result="ZLIB_COPPER_RESULT",
        policies=("none", "stride", "naive", "copper_clpd64k_peb", "dcpt", "spp", "ampm", "spp_copper_slack"),
        notes=(
            "Fresh local raw gem5 ARM full-system zlib compression-library seed-12 rerun. "
            "Together with codex_raw_zlib_tiny, this provides repeated raw samples for "
            "one public benchmark-family policy matrix; it is not the full final "
            "workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="zstd_tiny_existing",
        run_prefix="gem5_arm_ubuntu_fs_zstd_zstd_tiny_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_zstd_app" / "zstd_zstd_tiny_summary.csv",
        terminal_result="ZSTD_COPPER_RESULT",
        policies=("none", "naive", "copper_clpd64k_peb", "spp", "spp_copper_slack"),
        notes=(
            "Existing local raw gem5 ARM full-system zstd compression-library run "
            "with retained stats and terminal logs. This adds another public benchmark "
            "family to the raw provenance ledger; it is not a clone-local CI proof or "
            "full workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="zstd_tiny_existing_seed1",
        run_prefix="gem5_arm_ubuntu_fs_zstd_zstd_seed1_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_zstd_app" / "zstd_zstd_seed1_summary.csv",
        terminal_result="ZSTD_COPPER_RESULT",
        policies=("none", "naive", "copper_clpd64k_peb", "spp", "spp_copper_slack"),
        notes=(
            "Existing local raw gem5 ARM full-system zstd compression-library seed-1 "
            "run with retained stats and terminal logs. Together with zstd_tiny_existing, "
            "this provides repeated local raw samples for another public benchmark "
            "family; it is not the full final workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="duktape_medium_existing",
        run_prefix="gem5_arm_ubuntu_fs_duktape_app_medium_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_duktape_app" / "duktape_app_medium_summary.csv",
        terminal_result="DUKTAPE_COPPER_RESULT",
        policies=("none", "naive", "copper_clpd64k_peb", "spp", "spp_copper_slack"),
        notes=(
            "Existing local raw gem5 ARM full-system Duktape JavaScript-runtime medium run "
            "with retained stats and terminal logs. This adds another public benchmark "
            "family to the raw provenance ledger; it is not a clone-local CI proof or "
            "full workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="duktape_medium_existing_seed1",
        run_prefix="gem5_arm_ubuntu_fs_duktape_app_medium_seed1_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_duktape_app" / "duktape_app_medium_seed1_summary.csv",
        terminal_result="DUKTAPE_COPPER_RESULT",
        policies=("none", "naive", "copper_clpd64k_peb", "spp", "spp_copper_slack"),
        notes=(
            "Existing local raw gem5 ARM full-system Duktape JavaScript-runtime medium seed-1 "
            "run with retained stats and terminal logs. Together with the medium base and seed-2 "
            "runs, this provides repeated local raw samples; it is not the full final "
            "workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="duktape_medium_existing_seed2",
        run_prefix="gem5_arm_ubuntu_fs_duktape_app_medium_seed2_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_duktape_app" / "duktape_app_medium_seed2_summary.csv",
        terminal_result="DUKTAPE_COPPER_RESULT",
        policies=("none", "naive", "copper_clpd64k_peb", "spp", "spp_copper_slack"),
        notes=(
            "Existing local raw gem5 ARM full-system Duktape JavaScript-runtime medium seed-2 "
            "run with retained stats and terminal logs. Together with the medium base and seed-1 "
            "runs, this provides repeated local raw samples; it is not the full final "
            "workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="duktape_stress_existing",
        run_prefix="gem5_arm_ubuntu_fs_duktape_app_stress_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_duktape_app" / "duktape_app_stress_summary.csv",
        terminal_result="DUKTAPE_COPPER_RESULT",
        policies=("none", "naive", "copper_clpd64k_peb", "spp", "spp_copper_slack"),
        notes=(
            "Existing local raw gem5 ARM full-system Duktape JavaScript-runtime stress run "
            "with retained stats and terminal logs. This records the repeated-policy subset "
            "for stress input provenance; it is not a clone-local CI proof or full "
            "workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="duktape_stress_existing_seed1",
        run_prefix="gem5_arm_ubuntu_fs_duktape_app_stress_seed1_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_duktape_app" / "duktape_app_stress_seed1_summary.csv",
        terminal_result="DUKTAPE_COPPER_RESULT",
        policies=("none", "naive", "copper_clpd64k_peb", "spp", "spp_copper_slack"),
        notes=(
            "Existing local raw gem5 ARM full-system Duktape JavaScript-runtime stress seed-1 "
            "run with retained stats and terminal logs. Together with duktape_stress_existing, "
            "this provides repeated local raw samples; it is not the full final "
            "workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="lua_medium_existing",
        run_prefix="gem5_arm_ubuntu_fs_lua_app_medium_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_medium_summary.csv",
        terminal_result="LUA_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system Lua interpreter medium run "
            "with retained stats and terminal logs. This adds another public benchmark "
            "family to the raw provenance ledger; it is not a clone-local CI proof or "
            "full workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="lua_medium_existing_seed1",
        run_prefix="gem5_arm_ubuntu_fs_lua_app_medium_seed1_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_medium_seed1_summary.csv",
        terminal_result="LUA_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system Lua interpreter medium seed-1 run "
            "with retained stats and terminal logs. Together with the medium base and "
            "seed-2 runs, this provides repeated local raw samples; it is not the full "
            "final workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="lua_medium_existing_seed2",
        run_prefix="gem5_arm_ubuntu_fs_lua_app_medium_seed2_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_medium_seed2_summary.csv",
        terminal_result="LUA_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system Lua interpreter medium seed-2 run "
            "with retained stats and terminal logs. Together with the medium base and "
            "seed-1 runs, this provides repeated local raw samples; it is not the full "
            "final workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="lua_small_existing",
        run_prefix="gem5_arm_ubuntu_fs_lua_app_small_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_small_summary.csv",
        terminal_result="LUA_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system Lua interpreter small run "
            "with retained stats and terminal logs. This records the repeated-policy "
            "subset for small input provenance; it is not a clone-local CI proof or "
            "full workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="lua_small_existing_seed1",
        run_prefix="gem5_arm_ubuntu_fs_lua_app_small_seed1_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_small_seed1_summary.csv",
        terminal_result="LUA_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system Lua interpreter small seed-1 run "
            "with retained stats and terminal logs. Together with the small base and "
            "seed-2 runs, this provides repeated local raw samples; it is not the full "
            "final workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="lua_small_existing_seed2",
        run_prefix="gem5_arm_ubuntu_fs_lua_app_small_seed2_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_small_seed2_summary.csv",
        terminal_result="LUA_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system Lua interpreter small seed-2 run "
            "with retained stats and terminal logs. Together with the small base and "
            "seed-1 runs, this provides repeated local raw samples; it is not the full "
            "final workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="lua_stress_existing",
        run_prefix="gem5_arm_ubuntu_fs_lua_app_stress_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_stress_summary.csv",
        terminal_result="LUA_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system Lua interpreter stress run "
            "with retained stats and terminal logs. This records the repeated-policy "
            "subset for stress input provenance; it is not a clone-local CI proof or "
            "full workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="lua_stress_existing_seed1",
        run_prefix="gem5_arm_ubuntu_fs_lua_app_stress_seed1_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_lua_app" / "lua_app_stress_seed1_summary.csv",
        terminal_result="LUA_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system Lua interpreter stress seed-1 run "
            "with retained stats and terminal logs. Together with lua_stress_existing, "
            "this provides repeated local raw samples; it is not the full final "
            "workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="sqlite_medium_existing",
        run_prefix="gem5_arm_ubuntu_fs_sqlite_app_medium_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_sqlite_app" / "sqlite_app_medium_summary.csv",
        terminal_result="SQLITE_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system SQLite database medium run "
            "with retained stats and terminal logs. This adds another public benchmark "
            "family to the raw provenance ledger; it is not a clone-local CI proof or "
            "full workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="sqlite_medium_existing_seed1",
        run_prefix="gem5_arm_ubuntu_fs_sqlite_app_medium_seed1_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_sqlite_app" / "sqlite_app_medium_seed1_summary.csv",
        terminal_result="SQLITE_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system SQLite database medium seed-1 run "
            "with retained stats and terminal logs. Together with the medium base and "
            "seed-2 runs, this provides repeated local raw samples; it is not the full "
            "final workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="sqlite_medium_existing_seed2",
        run_prefix="gem5_arm_ubuntu_fs_sqlite_app_medium_seed2_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_sqlite_app" / "sqlite_app_medium_seed2_summary.csv",
        terminal_result="SQLITE_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system SQLite database medium seed-2 run "
            "with retained stats and terminal logs. Together with the medium base and "
            "seed-1 runs, this provides repeated local raw samples; it is not the full "
            "final workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="sqlite_stress_existing",
        run_prefix="gem5_arm_ubuntu_fs_sqlite_app_stress_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_sqlite_app" / "sqlite_app_stress_summary.csv",
        terminal_result="SQLITE_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system SQLite database stress run "
            "with retained stats and terminal logs. This records the repeated-policy "
            "subset for stress input provenance; it is not a clone-local CI proof or "
            "full workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="sqlite_stress_existing_seed1",
        run_prefix="gem5_arm_ubuntu_fs_sqlite_app_stress_seed1_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_sqlite_app" / "sqlite_app_stress_seed1_summary.csv",
        terminal_result="SQLITE_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system SQLite database stress seed-1 run "
            "with retained stats and terminal logs. Together with sqlite_stress_existing, "
            "this provides repeated local raw samples; it is not the full final "
            "workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="jsonsqlite_medium_existing",
        run_prefix="gem5_arm_ubuntu_fs_jsonsqlite_app_medium_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_jsonsqlite_app" / "jsonsqlite_app_medium_summary.csv",
        terminal_result="JSONSQLITE_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system combined JSON/SQLite medium run "
            "with retained stats and terminal logs. This adds another public benchmark "
            "family to the raw provenance ledger; it is not a clone-local CI proof or "
            "full workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="jsonsqlite_medium_existing_seed1",
        run_prefix="gem5_arm_ubuntu_fs_jsonsqlite_medium_seed1_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_jsonsqlite_app" / "jsonsqlite_medium_seed1_summary.csv",
        terminal_result="JSONSQLITE_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system combined JSON/SQLite medium seed-1 run "
            "with retained stats and terminal logs. Together with jsonsqlite_medium_existing, "
            "this provides repeated local raw samples; it is not the full final "
            "workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="jsonsqlite_stress_existing",
        run_prefix="gem5_arm_ubuntu_fs_jsonsqlite_app_stress_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_jsonsqlite_app" / "jsonsqlite_app_stress_summary.csv",
        terminal_result="JSONSQLITE_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system combined JSON/SQLite stress run "
            "with retained stats and terminal logs. This records the repeated-policy "
            "subset for stress input provenance; it is not a clone-local CI proof or "
            "full workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="jsonsqlite_stress_existing_seed1",
        run_prefix="gem5_arm_ubuntu_fs_jsonsqlite_stress_seed1_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_jsonsqlite_app" / "jsonsqlite_stress_seed1_summary.csv",
        terminal_result="JSONSQLITE_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system combined JSON/SQLite stress seed-1 run "
            "with retained stats and terminal logs. Together with jsonsqlite_stress_existing, "
            "this provides repeated local raw samples; it is not the full final "
            "workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="yyjson_medium_existing",
        run_prefix="gem5_arm_ubuntu_fs_yyjson_app_medium_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_yyjson_app" / "yyjson_app_medium_summary.csv",
        terminal_result="YYJSON_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system yyjson parser medium run "
            "with retained stats and terminal logs. This adds another public benchmark "
            "family to the raw provenance ledger; it is not a clone-local CI proof or "
            "full workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="yyjson_medium_existing_seed3",
        run_prefix="gem5_arm_ubuntu_fs_yyjson_app_medium_seed3_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_yyjson_app" / "yyjson_app_medium_seed3_summary.csv",
        terminal_result="YYJSON_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system yyjson parser medium seed-3 run "
            "with retained stats and terminal logs. Together with yyjson_medium_existing, "
            "this provides repeated local raw samples; it is not the full final "
            "workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="yyjson_stress_existing",
        run_prefix="gem5_arm_ubuntu_fs_yyjson_app_stress_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_yyjson_app" / "yyjson_app_stress_summary.csv",
        terminal_result="YYJSON_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system yyjson parser stress run "
            "with retained stats and terminal logs. This records the repeated-policy "
            "subset for stress input provenance; it is not a clone-local CI proof or "
            "full workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="yyjson_stress_existing_seed3",
        run_prefix="gem5_arm_ubuntu_fs_yyjson_app_stress_seed3_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_yyjson_app" / "yyjson_app_stress_seed3_summary.csv",
        terminal_result="YYJSON_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system yyjson parser stress seed-3 run "
            "with retained stats and terminal logs. Together with yyjson_stress_existing, "
            "this provides repeated local raw samples; it is not the full final "
            "workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="pcre2_smoke_existing",
        run_prefix="gem5_arm_ubuntu_fs_pcre2_pcre2_smoke_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_pcre2_app" / "pcre2_pcre2_smoke_summary.csv",
        terminal_result="PCRE2_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system PCRE2 regular-expression smoke run "
            "with retained stats and terminal logs. This adds another public benchmark "
            "family to the raw provenance ledger; it is not a clone-local CI proof or "
            "full workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="pcre2_smoke_existing_seed1",
        run_prefix="gem5_arm_ubuntu_fs_pcre2_pcre2_seed1_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_pcre2_app" / "pcre2_pcre2_seed1_summary.csv",
        terminal_result="PCRE2_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system PCRE2 regular-expression seed-1 run "
            "with retained stats and terminal logs. Together with pcre2_smoke_existing, "
            "this provides repeated local raw samples; it is not the full final "
            "workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="osslspeed_smoke_existing",
        run_prefix="gem5_arm_ubuntu_fs_osslspeed_app_smoke_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_osslspeed_app" / "osslspeed_app_smoke_summary.csv",
        terminal_result="OPENSSL_SPEEDLIKE_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system OpenSSL speed-like smoke run "
            "with retained stats and terminal logs. This adds another public benchmark "
            "family to the raw provenance ledger; it is not a clone-local CI proof or "
            "full workload/config matrix."
        ),
    ),
    RawRerunSpec(
        tag="osslspeed_smoke_existing_seed1",
        run_prefix="gem5_arm_ubuntu_fs_osslspeed_app_smoke_seed1_",
        summary_path=RESULTS / "gem5_arm_ubuntu_fs_osslspeed_app" / "osslspeed_app_smoke_seed1_summary.csv",
        terminal_result="OPENSSL_SPEEDLIKE_COPPER_RESULT",
        policies=COMMON_RERUN_POLICIES,
        notes=(
            "Existing local raw gem5 ARM full-system OpenSSL speed-like smoke seed-1 run "
            "with retained stats and terminal logs. Together with osslspeed_smoke_existing, "
            "this provides repeated local raw samples; it is not the full final "
            "workload/config matrix."
        ),
    ),
)


FIELDS = [
    "tag",
    "policy",
    "status",
    "environment",
    "gem5_version",
    "gem5_started",
    "command_line",
    "output_dir",
    "stats_path",
    "terminal_path",
    "host_stdout",
    "host_stderr",
    "summary_path",
    "summary_checksum",
    "rc",
    "roi_ticks",
    "instructions",
    "l1d_demand_misses",
    "notes",
]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def first_match(pattern: str, text: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def terminal_info(path: Path, result_token: str) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    result = re.search(
        rf"{re.escape(result_token)}\s+(?P<body>.*?)checksum=(?P<checksum>0x[0-9a-fA-F]+)",
        text,
    )
    checksum = result.group("checksum") if result else ""
    rc = first_match(r"COPPER_FS_NATIVE_A64_DONE rc=(\d+)", text)
    return checksum, rc


def row_for(spec: RawRerunSpec, policy: str, summary_by_policy: dict[str, dict[str, str]]) -> dict[str, str]:
    run_dir = RESULTS / f"{spec.run_prefix}{policy}"
    host_stdout = run_dir.with_suffix(".host.out")
    host_stderr = run_dir.with_suffix(".host.err")
    stats = run_dir / "stats.txt"
    terminal = run_dir / "board.terminal"
    host_text = host_stdout.read_text(encoding="utf-8", errors="replace") if host_stdout.exists() else ""
    checksum, rc = terminal_info(terminal, spec.terminal_result)
    summary = summary_by_policy.get(policy, {})
    status = "PASS" if stats.exists() and stats.stat().st_size > 0 and rc == "0" and checksum else "BLOCKED"
    return {
        "tag": spec.tag,
        "policy": policy,
        "status": status,
        "environment": "local_windows",
        "gem5_version": first_match(r"gem5 version\s+([^\r\n]+)", host_text),
        "gem5_started": first_match(r"gem5 started\s+([^\r\n]+)", host_text),
        "command_line": first_match(r"command line:\s+([^\r\n]+)", host_text),
        "output_dir": rel(run_dir),
        "stats_path": rel(stats) if stats.exists() else "",
        "terminal_path": rel(terminal) if terminal.exists() else "",
        "host_stdout": rel(host_stdout) if host_stdout.exists() else "",
        "host_stderr": rel(host_stderr) if host_stderr.exists() else "",
        "summary_path": rel(spec.summary_path) if spec.summary_path.exists() else "",
        "summary_checksum": summary.get("checksum", checksum),
        "rc": summary.get("rc", rc),
        "roi_ticks": summary.get("roi_ticks", ""),
        "instructions": summary.get("insts_not_nop", ""),
        "l1d_demand_misses": summary.get("l1d_demand_misses", ""),
        "notes": spec.notes,
    }


def main() -> int:
    rows = []
    for spec in SPECS:
        summary_by_policy = {row.get("policy", ""): row for row in read_csv(spec.summary_path)}
        rows.extend(row_for(spec, policy, summary_by_policy) for policy in spec.policies)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {rel(OUT)}")
    return 0 if all(row["status"] == "PASS" for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
