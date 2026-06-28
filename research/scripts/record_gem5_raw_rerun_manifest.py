#!/usr/bin/env python3
"""Record local raw gem5 rerun provenance without promoting broad claims."""

from __future__ import annotations

import csv
import hashlib
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
AUTO_POLICIES = tuple(
    sorted(
        {
            "spp_copper_slack",
            "copper_clpd64k_peb",
            "copper_clpd64k",
            "copper_exact131k",
            "copper_exact16k",
            "copper_clpd64k_rerun",
            "copper_clpd32k",
            "copper_clpd16k",
            "copper_clpd8k",
            "copper_proof131k",
            "copper_ctlw_terminal",
            "copper_ctlw",
            "copper_ctw",
            "copper_tpw",
            "spp_copper",
            "none_retry",
            "indirect",
            "copper",
            "naive",
            "none",
            "stride",
            "dcpt",
            "isb",
            "spp",
            "ampm",
            "bop",
        },
        key=len,
        reverse=True,
    )
)


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
    "stats_size_bytes",
    "stats_sha256",
    "terminal_path",
    "terminal_sha256",
    "host_stdout",
    "host_stdout_sha256",
    "host_stderr",
    "host_stderr_sha256",
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


def sha256(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def size_bytes(path: Path) -> str:
    return str(path.stat().st_size) if path.exists() and path.is_file() else ""


def public_command_line(command: str) -> str:
    if not command:
        return ""
    root_win = str(ROOT)
    root_posix = root_win.replace("\\", "/")
    replacements = {
        root_win: ".",
        root_posix: ".",
    }
    if len(root_posix) > 2 and root_posix[1] == ":":
        replacements[f"/{root_posix[0].lower()}/{root_posix[3:]}"] = "."
    cleaned = command
    for needle, replacement in replacements.items():
        cleaned = cleaned.replace(needle, replacement)
    return cleaned


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


def generic_terminal_info(path: Path) -> tuple[str, str, str]:
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    checksum = first_match(r"checksum=([0-9a-fA-Fx]+)", text)
    rc = first_match(r"COPPER_FS_NATIVE_A64_DONE rc=(\d+)", text)
    if rc:
        return checksum, rc, "COPPER_FS_NATIVE_A64_DONE"
    job_rcs = re.findall(r"COPPER_FS_NATIVE_JOB_DONE[^\r\n]*\brc=(\d+)", text)
    if job_rcs and "COPPER_FS_RUNSCRIPT_DONE" in text:
        failures = [value for value in job_rcs if value != "0"]
        return checksum, failures[0] if failures else "0", "COPPER_FS_NATIVE_JOB_DONE"
    return checksum, "", ""


def stats_value(path: Path, name: str) -> str:
    if not path.exists():
        return ""
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = line.split()
            if len(parts) >= 2 and parts[0] == name:
                return parts[1]
    return ""


def stats_sum(path: Path, includes: tuple[str, ...]) -> str:
    total = 0
    found = False
    if not path.exists():
        return ""
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = line.split()
            if len(parts) < 2:
                continue
            stat = parts[0]
            if all(token in stat for token in includes):
                try:
                    total += int(float(parts[1]))
                except ValueError:
                    continue
                found = True
    return str(total) if found else ""


def detect_policy(run_dir: Path) -> tuple[str, str] | None:
    name = run_dir.name
    if not name.startswith("gem5_arm_ubuntu_fs_"):
        return None
    stem = name.removeprefix("gem5_arm_ubuntu_fs_")
    for policy in AUTO_POLICIES:
        suffix = f"_{policy}"
        if stem.endswith(suffix):
            tag = stem[: -len(suffix)]
            if tag:
                return tag, policy
    return None


def auto_discovered_rows(existing_output_dirs: set[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for run_dir in sorted(RESULTS.glob("gem5_arm_ubuntu_fs_*")):
        if not run_dir.is_dir():
            continue
        if rel(run_dir) in existing_output_dirs:
            continue
        detected = detect_policy(run_dir)
        if not detected:
            continue
        tag, policy = detected
        stats = run_dir / "stats.txt"
        terminal = run_dir / "board.terminal"
        host_stdout = run_dir.with_suffix(".host.out")
        host_stderr = run_dir.with_suffix(".host.err")
        if not stats.exists() or stats.stat().st_size == 0 or not terminal.exists():
            continue
        checksum, rc, completion = generic_terminal_info(terminal)
        if rc != "0":
            continue
        host_text = host_stdout.read_text(encoding="utf-8", errors="replace") if host_stdout.exists() else ""
        checksum_note = (
            "terminal checksum"
            if checksum
            else "terminal/stat SHA-256 hashes; this workload did not print a workload checksum"
        )
        rows.append(
            {
                "tag": tag,
                "policy": policy,
                "status": "PASS",
                "environment": "local_windows",
                "gem5_version": first_match(r"gem5 version\s+([^\r\n]+)", host_text),
                "gem5_started": first_match(r"gem5 started\s+([^\r\n]+)", host_text),
                "command_line": public_command_line(first_match(r"command line:\s+([^\r\n]+)", host_text)),
                "output_dir": rel(run_dir),
                "stats_path": rel(stats),
                "stats_size_bytes": size_bytes(stats),
                "stats_sha256": sha256(stats),
                "terminal_path": rel(terminal),
                "terminal_sha256": sha256(terminal),
                "host_stdout": rel(host_stdout) if host_stdout.exists() else "",
                "host_stdout_sha256": sha256(host_stdout),
                "host_stderr": rel(host_stderr) if host_stderr.exists() else "",
                "host_stderr_sha256": sha256(host_stderr),
                "summary_path": "",
                "summary_checksum": checksum,
                "rc": rc,
                "roi_ticks": stats_value(stats, "simTicks"),
                "instructions": stats_sum(stats, ("commitStats0.numInstsNotNOP",)),
                "l1d_demand_misses": stats_sum(stats, ("l1d-cache-", "demandMisses::total")),
                "notes": (
                    "Auto-discovered retained local raw gem5 ARM full-system run with "
                    f"nonempty stats, {completion} rc=0, and {checksum_note}. "
                    "This broadens raw-run provenance only; it is not a clone-local "
                    "CI proof or a complete top-tier workload/config matrix by itself."
                ),
            }
        )
    return rows


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
        "command_line": public_command_line(first_match(r"command line:\s+([^\r\n]+)", host_text)),
        "output_dir": rel(run_dir),
        "stats_path": rel(stats) if stats.exists() else "",
        "stats_size_bytes": size_bytes(stats),
        "stats_sha256": sha256(stats),
        "terminal_path": rel(terminal) if terminal.exists() else "",
        "terminal_sha256": sha256(terminal),
        "host_stdout": rel(host_stdout) if host_stdout.exists() else "",
        "host_stdout_sha256": sha256(host_stdout),
        "host_stderr": rel(host_stderr) if host_stderr.exists() else "",
        "host_stderr_sha256": sha256(host_stderr),
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
    rows.extend(auto_discovered_rows({row["output_dir"] for row in rows if row.get("output_dir")}))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {rel(OUT)}")
    return 0 if all(row["status"] == "PASS" for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
