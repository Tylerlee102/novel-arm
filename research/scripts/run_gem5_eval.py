#!/usr/bin/env python3
"""Import or record gem5 full-system evidence for the COPPER evaluation flow.

This script does not fabricate gem5 data. It promotes gem5 rows only from
existing full-system summary CSVs with matching checksums and clean return
codes. If no such summaries are present, it writes BLOCKED rows with the exact
reason.
"""

from __future__ import annotations

import csv
import os
import platform
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "research" / "results"
LOG_DIR = RESULTS / "logs" / "gem5"
PERF = RESULTS / "gem5_performance.csv"
PREF = RESULTS / "gem5_prefetch_metrics.csv"
TRAFFIC = RESULTS / "gem5_memory_traffic.csv"
SUMMARY_PREFIX = "gem5_arm_ubuntu_fs_"

POLICY_TO_CONFIG = {
    "none": "no_prefetch",
    "stride": "stride",
    "naive": "naive_dmp",
    "dcpt": "dcpt",
    "ampm": "ampm",
    "bop": "bop",
    "indirect": "indirect",
    "isb": "isb",
    "copper": "copper",
    "copper_clpd8k": "copper_clpd8k",
    "copper_clpd16k": "copper_clpd16k",
    "copper_clpd32k": "copper_clpd32k",
    "copper_clpd64k": "copper_clpd64k",
    "copper_clpd64k_peb": "copper_clpd64k_peb",
    "copper_exact16k": "copper_exact16k",
    "copper_exact131k": "copper_exact131k",
    "copper_p131k": "copper_p131k",
    "spp": "spp",
    "spp_copper": "spp_copper",
    "spp_copper_slack": "spp_copper_slack",
    "COPPER CTLW-terminal": "copper_ctlw_terminal",
    "naive DMP + CTLW": "naive_dmp_ctlw",
}

MEASUREMENT_COLUMNS = {
    "policy",
    "roi_ticks",
    "sim_ticks",
    "insts_not_nop",
    "l1d_demand_misses",
    "l1d_demand_accesses",
    "l2_demand_misses",
    "checksum",
    "sha256",
    "rc",
    "pfIssued",
    "pfUseful",
    "pfUnused",
    "pfIdentified",
    "pointerLikeCandidates",
    "learnedProofs",
    "proofEvictions",
    "allowedCandidates",
    "blockedNoProvenance",
    "fillPrefetchTranslated",
    "fillPrefetchTranslationFault",
    "fillPrefetchTranslationUnavailable",
    "targetLineWitnessHits",
    "targetLineWitnessMisses",
    "carriedProvenanceTerminalStops",
    "boundaryFlushes",
    "boundaryAuthorityEntriesDropped",
    "boundaryPrefetchesDropped",
    "tick_delta_vs_none_pct",
    "l1d_miss_delta_vs_none_pct",
}
GROUP_LABEL_COLUMNS = (
    "stats_section_index",
    "secret",
    "seed",
    "poison",
    "transport",
    "strict_tcp",
    "netns_loopback",
    "phase",
    "input_checksum",
)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def current_environment() -> str:
    override = os.environ.get("COPPER_ENVIRONMENT", "").strip()
    if override:
        return override
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        return "github_actions"
    if os.environ.get("CODESPACES", "").lower() == "true":
        return "codespaces"
    if Path("/.dockerenv").exists() or os.environ.get("container"):
        return "docker"
    if platform.system().lower().startswith("win"):
        return "local_windows"
    return "docker"


def msys_runtime_env() -> dict[str, str]:
    env = os.environ.copy()
    runtime_paths = [
        ROOT / "tools" / "msys64" / "ucrt64" / "bin",
        ROOT / "tools" / "msys64" / "usr" / "bin",
    ]
    existing = [str(path) for path in runtime_paths if path.exists()]
    if existing:
        env["PATH"] = os.pathsep.join(existing + [env.get("PATH", "")])
    return env


def runnable_gem5() -> tuple[str, str]:
    candidates: list[Path | str] = []
    for name in ("gem5.opt", "gem5.fast", "gem5"):
        path = shutil.which(name)
        if path:
            candidates.append(path)
    candidates.extend(
        path
        for path in (
            ROOT / "external" / "gem5" / "build" / "ARM" / "gem5.fast.exe",
            ROOT / "external" / "gem5" / "build" / "ARM" / "gem5.opt.exe",
            ROOT / "external" / "gem5" / "build" / "ARM" / "gem5.opt",
        )
        if path.exists()
    )
    for candidate in candidates:
        try:
            proc = subprocess.run(
                [str(candidate), "--help"],
                cwd=ROOT,
                env=msys_runtime_env(),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=20,
            )
        except Exception as exc:
            last_error = f"{candidate} was found but could not run: {exc}"
            continue
        if proc.returncode == 0 and "gem5" in proc.stdout.lower():
            return str(candidate), "runnable gem5 binary responded to --help"
        last_error = f"{candidate} returned exit {proc.returncode}: {proc.stdout.strip()[:240]}"
    return "", locals().get("last_error", "gem5/gem5.opt not found on PATH or under external/gem5.")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def fnum(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def inum(value: str) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def ratio(numer: float, denom: float) -> str:
    if denom <= 0:
        return "NA"
    return f"{numer / denom:.6f}"


def pct_delta(value: float, baseline: float) -> str:
    if baseline <= 0:
        return "NA"
    return f"{((value - baseline) / baseline * 100.0):.6f}"


def speedup(baseline_ticks: float, ticks: float) -> str:
    if ticks <= 0 or baseline_ticks <= 0:
        return "NA"
    return f"{baseline_ticks / ticks:.6f}"


def benchmark_input_from_summary(path: Path) -> tuple[str, str]:
    parent = path.parent.name
    benchmark = parent[len(SUMMARY_PREFIX) :] if parent.startswith(SUMMARY_PREFIX) else parent
    tag = path.stem
    suffix = "_summary"
    if tag.endswith(suffix):
        tag = tag[: -len(suffix)]
    return benchmark, tag


def summary_paths() -> list[Path]:
    return sorted(
        path
        for path in RESULTS.glob(f"{SUMMARY_PREFIX}*/*_summary.csv")
        if "imported_ci" not in path.parts and "copper_public_artifact_package_20260620" not in path.parts
    )


def config_from_policy(policy: str) -> str:
    if policy in POLICY_TO_CONFIG:
        return POLICY_TO_CONFIG[policy]
    return policy.strip().lower().replace(" ", "_").replace("+", "plus")


def is_copper_config(config: str) -> bool:
    return "copper" in config.lower()


def tick_value(row: dict[str, str]) -> str:
    return row.get("roi_ticks", "") or row.get("sim_ticks", "")


def checksum_value(row: dict[str, str]) -> str:
    return row.get("checksum", "") or row.get("sha256", "")


def group_key(row: dict[str, str]) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (key, value)
            for key, value in row.items()
            if key not in MEASUREMENT_COLUMNS and value not in {"", "NA"}
        )
    )


def group_label(key: tuple[tuple[str, str], ...]) -> str:
    by_key = dict(key)
    parts = []
    for column in GROUP_LABEL_COLUMNS:
        value = by_key.get(column)
        if value not in {None, "", "NA"}:
            clean = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in value)
            parts.append(f"{column}{clean[:24]}")
    return "__" + "__".join(parts) if parts else ""


def validated_summaries() -> tuple[list[tuple[Path, list[dict[str, str]], str, str]], list[str]]:
    good: list[tuple[Path, list[dict[str, str]], str, str]] = []
    notes: list[str] = []
    for path in summary_paths():
        rows = read_csv(path)
        if not rows:
            notes.append(f"{rel(path)} skipped: empty summary")
            continue
        groups: dict[tuple[tuple[str, str], ...], list[dict[str, str]]] = {}
        for row in rows:
            groups.setdefault(group_key(row), []).append(row)
        imported_groups = 0
        for key, group_rows in sorted(groups.items(), key=lambda item: item[0]):
            policies = {row.get("policy", "") for row in group_rows}
            configs = {config_from_policy(policy) for policy in policies}
            checksums = {checksum_value(row) for row in group_rows}
            return_codes = {row.get("rc", "") for row in group_rows}
            ticks_ok = all(fnum(tick_value(row)) > 0 for row in group_rows)
            if "none" not in policies:
                notes.append(f"{rel(path)}{group_label(key)} skipped: no none baseline row")
                continue
            if not any(is_copper_config(config) for config in configs):
                notes.append(f"{rel(path)}{group_label(key)} skipped: no COPPER policy row")
                continue
            if len(checksums) != 1 or "" in checksums:
                notes.append(f"{rel(path)}{group_label(key)} skipped: checksum mismatch or missing checksum")
                continue
            if return_codes != {"0"}:
                notes.append(f"{rel(path)}{group_label(key)} skipped: nonzero return code(s) {sorted(return_codes)}")
                continue
            if not ticks_ok:
                notes.append(f"{rel(path)}{group_label(key)} skipped: missing or zero tick count")
                continue
            label = group_label(key)
            good.append((path, group_rows, next(iter(checksums)), label))
            imported_groups += 1
            notes.append(
                f"{rel(path)}{label} imported: {len(group_rows)} rows, "
                f"checksum {next(iter(checksums))}, rc=0"
            )
        if not imported_groups:
            notes.append(f"{rel(path)} skipped: no validated comparable COPPER group")
    return good, notes


def import_summaries() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[str]]:
    imported, notes = validated_summaries()
    perf_rows: list[dict[str, str]] = []
    pref_rows: list[dict[str, str]] = []
    traffic_rows: list[dict[str, str]] = []
    env = current_environment()
    for path, rows, checksum, label in imported:
        benchmark, input_tag_base = benchmark_input_from_summary(path)
        input_tag = input_tag_base + label
        by_policy = {row.get("policy", ""): row for row in rows}
        none = by_policy["none"]
        none_ticks = fnum(tick_value(none))
        none_misses = fnum(none.get("l1d_demand_misses", "0"))
        baseline_ticks = [
            fnum(tick_value(row))
            for row in rows
            if not is_copper_config(config_from_policy(row.get("policy", "")))
            and fnum(tick_value(row)) > 0
        ]
        best_baseline_ticks = min(baseline_ticks) if baseline_ticks else none_ticks
        for row in rows:
            policy = row.get("policy", "")
            config = config_from_policy(policy)
            ticks = fnum(tick_value(row))
            insts = fnum(row.get("insts_not_nop", "0"))
            misses = fnum(row.get("l1d_demand_misses", "0"))
            issued = fnum(row.get("pfIssued", "0"))
            useful = fnum(row.get("pfUseful", "0"))
            useless = max(issued - useful, 0.0)
            late = fnum(row.get("targetLineWitnessMisses", "0"))
            drops = fnum(row.get("boundaryAuthorityEntriesDropped", "0")) + fnum(row.get("blockedNoProvenance", "0"))
            log_path = rel(path)
            common = {
                "benchmark": benchmark,
                "input": input_tag,
                "seed": row.get("seed", "NA") or "NA",
                "config": config,
                "evidence_level": "gem5_full_system",
                "simulator": "gem5 ARM full-system imported summary",
                "log_path": log_path,
                "notes": (
                    f"Imported from {rel(path)}; checksum={checksum}; policy={policy}; "
                    "rc=0 for every row in this summary. The cycles field records gem5 ROI ticks "
                    "from roi_ticks when present, otherwise sim_ticks."
                ),
            }
            perf_rows.append(
                {
                    **common,
                    "cycles": str(inum(tick_value(row))),
                    "instructions": str(inum(row.get("insts_not_nop", "0"))),
                    "ipc": ratio(insts, ticks),
                    "cache_misses": str(inum(row.get("l1d_demand_misses", "0"))),
                    "memory_stalls": "NA",
                    "speedup_vs_no_prefetch": speedup(none_ticks, ticks),
                    "speedup_vs_best_baseline": speedup(best_baseline_ticks, ticks),
                    "status": "PASS",
                }
            )
            pref_rows.append(
                {
                    **common,
                    "prefetches_issued": str(inum(row.get("pfIssued", "0"))),
                    "useful_prefetches": str(inum(row.get("pfUseful", "0"))),
                    "useless_prefetches": str(inum(useless)),
                    "late_prefetches": str(inum(late)),
                    "queue_drops": str(inum(drops)),
                    "coverage": ratio(useful, none_misses),
                    "accuracy": ratio(useful, issued),
                    "lateness_rate": ratio(late, issued),
                }
            )
            demand = misses
            total = demand + issued
            traffic_rows.append(
                {
                    **common,
                    "demand_loads": str(inum(demand)),
                    "prefetch_loads": str(inum(issued)),
                    "total_memory_requests": str(inum(total)),
                    "traffic_overhead_pct": pct_delta(total, none_misses),
                    "bandwidth_pressure_metric": ratio(total, none_misses),
                }
            )
    return perf_rows, pref_rows, traffic_rows, notes


def write_blocked(note: str, gem5: str = "") -> None:
    log_path = LOG_DIR / "gem5_availability.log"
    log_path.write_text(note + "\n", encoding="utf-8")
    common = {
        "benchmark": "ALL",
        "input": "NA",
        "seed": "NA",
        "config": "NA",
        "evidence_level": "gem5",
        "simulator": gem5 or "gem5_unavailable",
        "log_path": rel(log_path),
        "notes": note,
    }
    write_csv(
        PERF,
        [
            "benchmark",
            "input",
            "seed",
            "config",
            "evidence_level",
            "simulator",
            "cycles",
            "instructions",
            "ipc",
            "cache_misses",
            "memory_stalls",
            "speedup_vs_no_prefetch",
            "speedup_vs_best_baseline",
            "status",
            "log_path",
            "notes",
        ],
        [{**common, "cycles": "NA", "instructions": "NA", "ipc": "NA", "cache_misses": "NA", "memory_stalls": "NA", "speedup_vs_no_prefetch": "NA", "speedup_vs_best_baseline": "NA", "status": "BLOCKED"}],
    )
    write_csv(
        PREF,
        [
            "benchmark",
            "input",
            "seed",
            "config",
            "evidence_level",
            "simulator",
            "prefetches_issued",
            "useful_prefetches",
            "useless_prefetches",
            "late_prefetches",
            "queue_drops",
            "coverage",
            "accuracy",
            "lateness_rate",
            "log_path",
            "notes",
        ],
        [{**common, "prefetches_issued": "NA", "useful_prefetches": "NA", "useless_prefetches": "NA", "late_prefetches": "NA", "queue_drops": "NA", "coverage": "NA", "accuracy": "NA", "lateness_rate": "NA"}],
    )
    write_csv(
        TRAFFIC,
        [
            "benchmark",
            "input",
            "seed",
            "config",
            "evidence_level",
            "simulator",
            "demand_loads",
            "prefetch_loads",
            "total_memory_requests",
            "traffic_overhead_pct",
            "bandwidth_pressure_metric",
            "log_path",
            "notes",
        ],
        [{**common, "demand_loads": "NA", "prefetch_loads": "NA", "total_memory_requests": "NA", "traffic_overhead_pct": "NA", "bandwidth_pressure_metric": "NA"}],
    )


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    perf_rows, pref_rows, traffic_rows, import_notes = import_summaries()
    log_path = LOG_DIR / "gem5_import.log"
    if perf_rows:
        log_path.write_text("\n".join(import_notes) + "\n", encoding="utf-8")
        write_csv(
            PERF,
            [
                "benchmark",
                "input",
                "seed",
                "config",
                "evidence_level",
                "simulator",
                "cycles",
                "instructions",
                "ipc",
                "cache_misses",
                "memory_stalls",
                "speedup_vs_no_prefetch",
                "speedup_vs_best_baseline",
                "status",
                "log_path",
                "notes",
            ],
            perf_rows,
        )
        write_csv(
            PREF,
            [
                "benchmark",
                "input",
                "seed",
                "config",
                "evidence_level",
                "simulator",
                "prefetches_issued",
                "useful_prefetches",
                "useless_prefetches",
                "late_prefetches",
                "queue_drops",
                "coverage",
                "accuracy",
                "lateness_rate",
                "log_path",
                "notes",
            ],
            pref_rows,
        )
        write_csv(
            TRAFFIC,
            [
                "benchmark",
                "input",
                "seed",
                "config",
                "evidence_level",
                "simulator",
                "demand_loads",
                "prefetch_loads",
                "total_memory_requests",
                "traffic_overhead_pct",
                "bandwidth_pressure_metric",
                "log_path",
                "notes",
            ],
            traffic_rows,
        )
        print(
            f"wrote {rel(PERF)}, {rel(PREF)}, and {rel(TRAFFIC)} "
            f"from {len(perf_rows)} imported gem5 full-system rows"
        )
        return 0

    gem5, note = runnable_gem5()
    if gem5:
        note = (
            "Runnable gem5 was found, but no validated full-system summary CSVs were present "
            "under research/results/gem5_arm_ubuntu_fs_* with a no-prefetch baseline, a COPPER row, "
            "matching checksum, clean return codes, and positive tick counts. No performance rows "
            "are promoted."
        )
    write_blocked(note, gem5)
    print(f"wrote {rel(PERF)}, {rel(PREF)}, and {rel(TRAFFIC)} with BLOCKED gem5 rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
