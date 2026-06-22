#!/usr/bin/env python3
"""Summarize corrected full-system AArch64 GAPBS-mini gem5 runs."""

from __future__ import annotations

import csv
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = ROOT / "research" / "results"
OUT_DIR = RESULT_ROOT / "gem5_arm_ubuntu_fs_gapbs_mini_large"
CSV_OUT = OUT_DIR / "gapbs_mini_large_fs_summary.csv"
MD_OUT = OUT_DIR / "GAPBS_MINI_LARGE_FS_SUMMARY.md"

RUNS = {
    "none": RESULT_ROOT / "gem5_arm_ubuntu_fs_gapbs_mini_large_timing_none",
    "stride": RESULT_ROOT / "gem5_arm_ubuntu_fs_gapbs_mini_large_timing_stride",
    "naive DMP + CTLW": RESULT_ROOT / "gem5_arm_ubuntu_fs_gapbs_mini_large_timing_naive",
    "COPPER CTLW-terminal": RESULT_ROOT / "gem5_arm_ubuntu_fs_gapbs_mini_large_timing_copper",
}

STAT_RE = re.compile(r"^(\S+)\s+([-+0-9.eEinfnan]+)\s+#")


def first_stats_section(path: Path) -> dict[str, float]:
    stats: dict[str, float] = {}
    in_section = False
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if raw.startswith("---------- Begin Simulation Statistics ----------"):
            in_section = True
            continue
        if raw.startswith("---------- End Simulation Statistics"):
            break
        if not in_section:
            continue
        match = STAT_RE.match(raw)
        if not match:
            continue
        key, value = match.groups()
        if value.lower() == "nan":
            continue
        stats[key] = float(value)
    return stats


def terminal_markers(path: Path) -> tuple[str, bool, bool, bool]:
    text = path.read_text(encoding="utf-8", errors="replace")
    checksum = ""
    for line in text.splitlines():
        if "AARCH64_GAPBS_MINI_DONE checksum=" in line:
            checksum = line.rsplit("=", 1)[-1].strip()
    return (
        checksum,
        "COPPER_FS_HOST_SWITCH_TO_TIMING" in text,
        "COPPER_FS_NATIVE_A64_DONE rc=0" in text,
        "COPPER_FS_WORKEND" in text,
    )


def stat_sum(stats: dict[str, float], suffix: str) -> int:
    return int(sum(value for key, value in stats.items() if key.endswith(suffix)))


def stat_sum_contains(stats: dict[str, float], needle: str) -> int:
    return int(sum(value for key, value in stats.items() if needle in key))


def stat_sum_contains_all(stats: dict[str, float], needles: list[str]) -> int:
    return int(
        sum(value for key, value in stats.items() if all(needle in key for needle in needles))
    )


def stat_sum_contains_suffix(stats: dict[str, float], needle: str, suffix: str) -> int:
    return int(
        sum(value for key, value in stats.items() if needle in key and key.endswith(suffix))
    )


def prefetch_sum(stats: dict[str, float], name: str) -> int:
    return stat_sum(stats, f".prefetcher.{name}")


def read_row(policy: str, run_dir: Path) -> dict[str, object]:
    stats = first_stats_section(run_dir / "stats.txt")
    checksum, _switched_stdout, rc0, workend = terminal_markers(run_dir / "board.terminal")
    timing_roi_stats = any("processor.switch" in key for key in stats)
    return {
        "policy": policy,
        "roi_ticks": int(stats["simTicks"]),
        "sim_insts": int(stats["simInsts"]),
        "l1d_demand_misses": stat_sum_contains_suffix(
            stats, ".l1d-cache-", ".demandMisses::total"
        ),
        "l1d_overall_misses": stat_sum_contains_suffix(
            stats, ".l1d-cache-", ".overallMisses::total"
        ),
        "l1d_accesses": stat_sum_contains_suffix(
            stats, ".l1d-cache-", ".overallAccesses::total"
        ),
        "l2_data_misses": stat_sum_contains_all(
            stats, [".l2-cache-", ".overallMisses::", ".core.data"]
        ),
        "pf_issued": prefetch_sum(stats, "pfIssued"),
        "pf_useful": prefetch_sum(stats, "pfUseful"),
        "pf_identified": prefetch_sum(stats, "pfIdentified"),
        "pointer_like": prefetch_sum(stats, "pointerLikeCandidates"),
        "learned": prefetch_sum(stats, "learnedProofs"),
        "allowed": prefetch_sum(stats, "allowedCandidates"),
        "blocked": prefetch_sum(stats, "blockedNoProvenance"),
        "ctlw_hits": prefetch_sum(stats, "targetLineWitnessHits"),
        "ctlw_misses": prefetch_sum(stats, "targetLineWitnessMisses"),
        "terminal_stops": prefetch_sum(stats, "carriedProvenanceTerminalStops"),
        "translation_unavailable": prefetch_sum(stats, "fillPrefetchTranslationUnavailable"),
        "translation_faults": prefetch_sum(stats, "fillPrefetchTranslationFault"),
        "checksum": checksum,
        "timing_roi_stats": timing_roi_stats,
        "native_rc0": rc0,
        "workend": workend,
        "result_dir": run_dir.name,
    }


def fmt_int(value: object) -> str:
    return f"{int(value):,}"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [read_row(policy, run_dir) for policy, run_dir in RUNS.items()]
    baseline = int(rows[0]["roi_ticks"])
    for row in rows:
        ticks = int(row["roi_ticks"])
        row["vs_none_pct"] = 100.0 * (ticks / baseline - 1.0)

    with CSV_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    checksums = sorted({str(row["checksum"]) for row in rows})
    md = [
        "# Corrected Full-System ARM64 GAPBS-Mini Large Summary",
        "",
        "This summary parses the first gem5 statistics section from timing-mode full-system ARM64 runs. The harness boots Linux, switches from atomic boot to timing mode at `m5 workbegin`, resets stats immediately before the native AArch64 graph binary, dumps stats immediately after return, and records `m5 workend`.",
        "",
        "## Workload",
        "",
        "- Native binary: `research/bin/aarch64_gapbs_mini_suite_fs`",
        "- Source: `research/aarch64_gapbs_mini_suite.c`",
        "- Compile-time size: 1024 vertices, degree 8, 3 passes, 2048 fake pointer-shaped words",
        "- Candidate window: `0x220000..0x245000`",
        f"- Guest checksum set: {', '.join(checksums)}",
        "",
        "## ROI Results",
        "",
        "| Policy | ROI ticks | vs none | Insts | L1D misses | PF issued | PF useful | Pointer-like | Learned | Allowed | Blocked | CTLW hits | CTLW misses | Terminal stops | Xlate unavailable | Xlate faults |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        md.append(
            "| "
            + " | ".join(
                [
                    str(row["policy"]),
                    fmt_int(row["roi_ticks"]),
                    f"{float(row['vs_none_pct']):+.3f}%",
                    fmt_int(row["sim_insts"]),
                    fmt_int(row["l1d_demand_misses"]),
                    fmt_int(row["pf_issued"]),
                    fmt_int(row["pf_useful"]),
                    fmt_int(row["pointer_like"]),
                    fmt_int(row["learned"]),
                    fmt_int(row["allowed"]),
                    fmt_int(row["blocked"]),
                    fmt_int(row["ctlw_hits"]),
                    fmt_int(row["ctlw_misses"]),
                    fmt_int(row["terminal_stops"]),
                    fmt_int(row["translation_unavailable"]),
                    fmt_int(row["translation_faults"]),
                ]
            )
            + " |"
        )
    md.extend(
        [
            "",
            "## Validity Checks",
            "",
            "| Policy | Checksum | Timing ROI stats | Native rc=0 | Workend |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for row in rows:
        md.append(
            f"| {row['policy']} | {row['checksum']} | {row['timing_roi_stats']} | {row['native_rc0']} | {row['workend']} |"
        )
    md.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The larger mini-suite is a full-system ARM64 Linux execution of a freestanding GAPBS-inspired graph binary, not official C++ GAPBS.",
            "- The corrected timing-mode run is the usable comparison; earlier `gem5_arm_ubuntu_fs_gapbs_mini_large_*` directories without `_timing_` were checksum-only harness probes and should not be used for prefetch conclusions.",
            "- This table should be interpreted as full-system safety/control evidence. A real official GAPBS or SPEC-style AArch64 application remains the stronger external-validity target.",
            "",
        ]
    )
    MD_OUT.write_text("\n".join(md), encoding="utf-8")
    print(CSV_OUT)
    print(MD_OUT)


if __name__ == "__main__":
    main()
