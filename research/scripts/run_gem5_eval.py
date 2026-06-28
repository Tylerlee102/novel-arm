#!/usr/bin/env python3
"""Import or record gem5 full-system evidence for the COPPER evaluation flow.

This script does not fabricate gem5 data. It promotes gem5 rows only from
existing full-system summary CSVs with matching checksums and clean return
codes. If no such summaries are present, it writes BLOCKED rows with the exact
reason.
"""

from __future__ import annotations

import csv
import hashlib
import math
import os
import platform
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, stdev


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "research" / "results"
LOG_DIR = RESULTS / "logs" / "gem5"
PERF = RESULTS / "gem5_performance.csv"
PREF = RESULTS / "gem5_prefetch_metrics.csv"
TRAFFIC = RESULTS / "gem5_memory_traffic.csv"
VALIDATION = RESULTS / "gem5_validation.csv"
STATS = RESULTS / "gem5_statistical_summary.csv"
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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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
    paths = sorted(
        path
        for path in RESULTS.glob(f"{SUMMARY_PREFIX}*/*_summary.csv")
        if "imported_ci" not in path.parts and "copper_public_artifact_package_20260620" not in path.parts
    )
    if os.environ.get("COPPER_ALLOW_LOCAL_GEM5_SUMMARIES", "").lower() in {"1", "true", "yes"}:
        return paths
    tracked = tracked_result_paths()
    if not tracked:
        return paths
    return [path for path in paths if rel(path) in tracked]


def tracked_result_paths() -> set[str]:
    git = shutil.which("git")
    if not git:
        return set()
    try:
        proc = subprocess.run(
            [git, "-C", str(ROOT), "ls-files", "--", "research/results"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=20,
        )
    except Exception:
        return set()
    if proc.returncode != 0:
        return set()
    return {line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()}


def ignored_local_summary_count() -> int:
    if os.environ.get("COPPER_ALLOW_LOCAL_GEM5_SUMMARIES", "").lower() in {"1", "true", "yes"}:
        return 0
    tracked = tracked_result_paths()
    if not tracked:
        return 0
    all_paths = [
        path
        for path in RESULTS.glob(f"{SUMMARY_PREFIX}*/*_summary.csv")
        if "imported_ci" not in path.parts and "copper_public_artifact_package_20260620" not in path.parts
    ]
    return sum(1 for path in all_paths if rel(path) not in tracked)


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


VALIDATION_FIELDS = [
    "summary_path",
    "summary_sha256",
    "benchmark",
    "input",
    "group_label",
    "status",
    "rows",
    "policies",
    "configs",
    "checksum",
    "checksum_count",
    "rc_values",
    "min_ticks",
    "has_no_prefetch",
    "has_copper",
    "checksum_consistent",
    "return_codes_clean",
    "positive_ticks",
    "notes",
]

STATS_FIELDS = [
    "benchmark",
    "config",
    "metric",
    "evidence_level",
    "status",
    "n",
    "mean",
    "median",
    "std",
    "min",
    "max",
    "ci95_low",
    "ci95_high",
    "source_rows",
    "source_inputs",
    "notes",
]


def validation_row(
    path: Path,
    key: tuple[tuple[str, str], ...],
    rows: list[dict[str, str]],
    status: str,
    notes: str,
) -> dict[str, str]:
    benchmark, input_tag = benchmark_input_from_summary(path)
    policies = sorted({row.get("policy", "") for row in rows})
    configs = sorted({config_from_policy(policy) for policy in policies})
    checksums = sorted({checksum_value(row) for row in rows})
    return_codes = sorted({row.get("rc", "") for row in rows})
    ticks = [fnum(tick_value(row)) for row in rows]
    nonempty_checksums = [value for value in checksums if value]
    return {
        "summary_path": rel(path),
        "summary_sha256": sha256(path),
        "benchmark": benchmark,
        "input": input_tag,
        "group_label": group_label(key).lstrip("_"),
        "status": status,
        "rows": str(len(rows)),
        "policies": ";".join(policies),
        "configs": ";".join(configs),
        "checksum": nonempty_checksums[0] if len(nonempty_checksums) == 1 else "",
        "checksum_count": str(len(nonempty_checksums)),
        "rc_values": ";".join(return_codes),
        "min_ticks": f"{min(ticks):.0f}" if ticks else "0",
        "has_no_prefetch": "yes" if "none" in policies else "no",
        "has_copper": "yes" if any(is_copper_config(config) for config in configs) else "no",
        "checksum_consistent": "yes" if len(nonempty_checksums) == 1 and "" not in checksums else "no",
        "return_codes_clean": "yes" if return_codes == ["0"] else "no",
        "positive_ticks": "yes" if rows and all(value > 0 for value in ticks) else "no",
        "notes": notes,
    }


def validated_summaries() -> tuple[list[tuple[Path, list[dict[str, str]], str, str]], list[str], list[dict[str, str]]]:
    good: list[tuple[Path, list[dict[str, str]], str, str]] = []
    notes: list[str] = []
    validation_rows: list[dict[str, str]] = []
    ignored = ignored_local_summary_count()
    if ignored:
        notes.append(
            f"ignored {ignored} local-only gem5 summary file(s); set COPPER_ALLOW_LOCAL_GEM5_SUMMARIES=1 "
            "to include non-tracked local experiments outside the public CI evidence path"
        )
    for path in summary_paths():
        rows = read_csv(path)
        if not rows:
            notes.append(f"{rel(path)} skipped: empty summary")
            validation_rows.append(validation_row(path, (), [], "SKIPPED", "empty summary"))
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
                note = "no none baseline row"
                notes.append(f"{rel(path)}{group_label(key)} skipped: {note}")
                validation_rows.append(validation_row(path, key, group_rows, "SKIPPED", note))
                continue
            if not any(is_copper_config(config) for config in configs):
                note = "no COPPER policy row"
                notes.append(f"{rel(path)}{group_label(key)} skipped: {note}")
                validation_rows.append(validation_row(path, key, group_rows, "SKIPPED", note))
                continue
            if len(checksums) != 1 or "" in checksums:
                note = "checksum mismatch or missing checksum"
                notes.append(f"{rel(path)}{group_label(key)} skipped: {note}")
                validation_rows.append(validation_row(path, key, group_rows, "SKIPPED", note))
                continue
            if return_codes != {"0"}:
                note = f"nonzero return code(s) {sorted(return_codes)}"
                notes.append(f"{rel(path)}{group_label(key)} skipped: {note}")
                validation_rows.append(validation_row(path, key, group_rows, "SKIPPED", note))
                continue
            if not ticks_ok:
                note = "missing or zero tick count"
                notes.append(f"{rel(path)}{group_label(key)} skipped: {note}")
                validation_rows.append(validation_row(path, key, group_rows, "SKIPPED", note))
                continue
            label = group_label(key)
            good.append((path, group_rows, next(iter(checksums)), label))
            imported_groups += 1
            note = f"imported {len(group_rows)} rows, checksum {next(iter(checksums))}, rc=0"
            notes.append(
                f"{rel(path)}{label} imported: {note}"
            )
            validation_rows.append(validation_row(path, key, group_rows, "PASS", note))
        if not imported_groups:
            notes.append(f"{rel(path)} skipped: no validated comparable COPPER group")
    return good, notes, validation_rows


def import_summaries() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[str]]:
    imported, notes, validation_rows = validated_summaries()
    write_csv(VALIDATION, VALIDATION_FIELDS, validation_rows)
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


def metric_float(value: str) -> float | None:
    if value in {"", "NA", None}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def write_statistical_summary(
    perf_rows: list[dict[str, str]],
    pref_rows: list[dict[str, str]],
    traffic_rows: list[dict[str, str]],
) -> None:
    prefetch_index = {
        (row["benchmark"], row["input"], row["seed"], row["config"]): row for row in pref_rows
    }
    traffic_index = {
        (row["benchmark"], row["input"], row["seed"], row["config"]): row for row in traffic_rows
    }
    values: dict[tuple[str, str, str, str], list[tuple[float, str]]] = defaultdict(list)
    for row in perf_rows:
        key = (row["benchmark"], row["input"], row["seed"], row["config"])
        source_id = f"{row['input']}|seed={row['seed']}"
        for metric in (
            "cycles",
            "ipc",
            "cache_misses",
            "speedup_vs_no_prefetch",
            "speedup_vs_best_baseline",
        ):
            val = metric_float(row.get(metric, ""))
            if val is not None:
                values[(row["benchmark"], row["config"], row["evidence_level"], metric)].append((val, source_id))
        pref = prefetch_index.get(key, {})
        for metric in ("coverage", "accuracy", "lateness_rate", "queue_drops"):
            val = metric_float(pref.get(metric, ""))
            if val is not None:
                values[(row["benchmark"], row["config"], row["evidence_level"], metric)].append((val, source_id))
        traffic = traffic_index.get(key, {})
        for metric in ("traffic_overhead_pct", "bandwidth_pressure_metric"):
            val = metric_float(traffic.get(metric, ""))
            if val is not None:
                values[(row["benchmark"], row["config"], row["evidence_level"], metric)].append((val, source_id))

    summary_rows: list[dict[str, str]] = []
    for (benchmark, config, evidence_level, metric), samples in sorted(values.items()):
        vals = [sample[0] for sample in samples]
        sources = sorted({sample[1] for sample in samples})
        n = len(vals)
        avg = mean(vals)
        sd = stdev(vals) if n > 1 else 0.0
        ci = 1.96 * sd / math.sqrt(n) if n > 1 else 0.0
        summary_rows.append(
            {
                "benchmark": benchmark,
                "config": config,
                "metric": metric,
                "evidence_level": evidence_level,
                "status": "PASS" if n > 1 else "SINGLE_SAMPLE",
                "n": str(n),
                "mean": f"{avg:.6f}",
                "median": f"{median(vals):.6f}",
                "std": f"{sd:.6f}",
                "min": f"{min(vals):.6f}",
                "max": f"{max(vals):.6f}",
                "ci95_low": f"{avg - ci:.6f}",
                "ci95_high": f"{avg + ci:.6f}",
                "source_rows": str(len(samples)),
                "source_inputs": str(len(sources)),
                "notes": (
                    "Imported gem5 ARM-system summary statistics across validated public summary rows; "
                    "n counts imported benchmark/input/seed samples, regressions are retained, and this "
                    "is not a fresh clone-local raw gem5 rerun."
                ),
            }
        )
    write_csv(STATS, STATS_FIELDS, summary_rows)


def write_blocked(note: str, gem5: str = "") -> None:
    log_path = LOG_DIR / "gem5_availability.log"
    log_path.write_text(note + "\n", encoding="utf-8")
    write_csv(
        VALIDATION,
        VALIDATION_FIELDS,
        [
            {
                "summary_path": "",
                "summary_sha256": "",
                "benchmark": "ALL",
                "input": "NA",
                "group_label": "",
                "status": "BLOCKED",
                "rows": "0",
                "policies": "",
                "configs": "",
                "checksum": "",
                "checksum_count": "0",
                "rc_values": "",
                "min_ticks": "0",
                "has_no_prefetch": "no",
                "has_copper": "no",
                "checksum_consistent": "no",
                "return_codes_clean": "no",
                "positive_ticks": "no",
                "notes": note,
            }
        ],
    )
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
    write_csv(
        STATS,
        STATS_FIELDS,
        [
            {
                "benchmark": "ALL",
                "config": "NA",
                "metric": "NA",
                "evidence_level": "gem5",
                "status": "BLOCKED",
                "n": "0",
                "mean": "NA",
                "median": "NA",
                "std": "NA",
                "min": "NA",
                "max": "NA",
                "ci95_low": "NA",
                "ci95_high": "NA",
                "source_rows": "0",
                "source_inputs": "0",
                "notes": note,
            }
        ],
    )


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    perf_rows, pref_rows, traffic_rows, import_notes = import_summaries()
    log_path = LOG_DIR / "gem5_import.log"
    if perf_rows:
        log_path.write_text("\n".join(import_notes) + "\n", encoding="utf-8")
        write_statistical_summary(perf_rows, pref_rows, traffic_rows)
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
            f"wrote {rel(PERF)}, {rel(PREF)}, {rel(TRAFFIC)}, and {rel(STATS)} "
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
    print(f"wrote {rel(PERF)}, {rel(PREF)}, {rel(TRAFFIC)}, and {rel(STATS)} with BLOCKED gem5 rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
