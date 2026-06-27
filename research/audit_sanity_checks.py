#!/usr/bin/env python3
"""Fast audit sanity checks for paper-facing COPPER derived artifacts."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
FIGURES = RESULTS / "figures"

APP_WORKLOADS = [
    "sqlite_medium",
    "sqlite_stress",
    "lua_medium",
    "lua_stress",
    "duktape_medium",
    "duktape_stress",
    "yyjson_medium",
    "yyjson_stress",
    "jsonsqlite_medium",
    "jsonsqlite_stress",
    "cachesvc_small",
    "cachesvc_medium",
]
FIGURE_POLICIES = ["naive", "copper_clpd64k_peb", "spp", "spp_copper_slack"]
PRESSURE_WEIGHTS = {
    "membus_pkt_size_total_delta_vs_none_pct": 0.35,
    "dram_read_reqs_delta_vs_none_pct": 0.30,
    "l2_replacements_delta_vs_none_pct": 0.20,
    "l1d_replacements_delta_vs_none_pct": 0.15,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def as_float(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    return float(value) if value not in {"", "nan"} else 0.0


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def check_app_figure_inputs() -> None:
    rows = read_csv(RESULTS / "copper_prefetch_traffic_overhead_20260616.csv")
    present = {(row["workload"], row["policy"]) for row in rows}
    missing = [
        (workload, policy)
        for workload in APP_WORKLOADS
        for policy in FIGURE_POLICIES
        if (workload, policy) not in present
    ]
    assert_true(not missing, f"missing figure data rows: {missing[:8]}")

    index = (FIGURES / "COPPER_APP_FIGURE_INDEX_20260616.md").read_text(
        encoding="utf-8"
    )
    assert_true("ten public app points" not in index.lower(), "stale ten-point figure text")
    for name in [
        "copper_app_runtime_delta",
        "copper_app_ctlw_reduction",
        "copper_app_bus_overhead",
        "copper_app_full_baseline_runtime",
    ]:
        for suffix in [".png", ".svg"]:
            path = FIGURES / f"{name}{suffix}"
            assert_true(path.exists(), f"missing figure {path}")
            assert_true(path.stat().st_size > 1000, f"suspiciously small figure {path}")


def check_pressure_score_formula() -> None:
    source_rows = read_csv(RESULTS / "copper_prefetch_traffic_overhead_20260616.csv")
    score_rows = read_csv(RESULTS / "copper_energy_pollution_scorecard_20260617.csv")
    source = {(row["workload"], row["policy"]): row for row in source_rows}
    for row in score_rows:
        src = source[(row["workload"], row["policy"])]
        expected = sum(as_float(src, key) * weight for key, weight in PRESSURE_WEIGHTS.items())
        actual = row["pressure_score_base_vs_none_pct"]
        assert_true(
            f"{expected:.3f}" == actual,
            f"pressure score mismatch for {row['workload']} {row['policy']}: {expected} != {actual}",
        )

    weights = read_csv(RESULTS / "copper_energy_pollution_weight_sensitivity_20260617.csv")
    for row in weights:
        total = sum(
            as_float(row, key)
            for key in ["bus_weight", "dram_read_weight", "l2_repl_weight", "l1d_repl_weight"]
        )
        assert_true(abs(total - 1.0) <= 1e-9, f"weights do not sum to one: {row['scenario']}")


def check_dram_roi_section_alignment() -> None:
    score_rows = read_csv(RESULTS / "copper_dram_energy_scorecard_20260618.csv")
    score = {(row["workload"], row["policy"]): int(float(row["sim_ticks"])) for row in score_rows}
    samples = {
        "sqlite_medium": RESULTS / "gem5_arm_ubuntu_fs_sqlite_app" / "sqlite_app_medium_summary.csv",
        "ossltlstcp_process_scale2": RESULTS
        / "gem5_arm_ubuntu_fs_ossltlstcp_app"
        / "ossltlstcp_tcp_netns_process_scale2_summary.csv",
    }
    for workload, path in samples.items():
        for row in read_csv(path):
            policy = row["policy"]
            if (workload, policy) in score:
                assert_true(
                    score[(workload, policy)] == int(float(row["roi_ticks"])),
                    f"DRAM scorecard sim_ticks does not match ROI ticks for {workload} {policy}",
                )


def check_submission_claim_counts() -> None:
    paper = (ROOT / "research" / "COPPER_SUBMISSION_RESTRUCTURED.md").read_text(
        encoding="utf-8"
    )
    assert_true("12-point public app/service matrix" in paper, "missing 12-point matrix claim")
    assert_true("22-point side-effect scorecard" in paper, "missing 22-point scorecard claim")

    artifact_audit = (RESULTS / "COPPER_ARTIFACT_AUDIT_20260616.md").read_text(
        encoding="utf-8"
    )
    match = re.search(r"Passed (\d+)/(\d+) artifact checks", artifact_audit)
    assert_true(bool(match), "artifact audit pass line missing")
    assert_true(match.group(1) == match.group(2), "artifact audit has failing checks")


def main() -> int:
    checks = [
        check_app_figure_inputs,
        check_pressure_score_formula,
        check_dram_roi_section_alignment,
        check_submission_claim_counts,
    ]
    for check in checks:
        check()
        print(f"PASS {check.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
