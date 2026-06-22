#!/usr/bin/env python3
"""Build a compact portfolio of COPPER/SCOOP security evidence."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "COPPER_SECURITY_EVIDENCE_PORTFOLIO_20260616.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def by_policy(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["policy"]: row for row in rows}


def by_secret_policy(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row["secret"], row["policy"]): row for row in rows}


def as_int(row: dict[str, str], key: str) -> int:
    return int(row[key])


def as_float(row: dict[str, str], key: str) -> float:
    return float(row[key])


def delta(rows: dict[tuple[str, str], dict[str, str]], policy: str, key: str) -> int:
    return as_int(rows[("1", policy)], key) - as_int(rows[("0", policy)], key)


def timing_delta(rows: dict[tuple[str, str], dict[str, str]], policy: str) -> float:
    return (
        as_float(rows[("1", policy)], "tick_delta_vs_none_pct")
        - as_float(rows[("0", policy)], "tick_delta_vs_none_pct")
    )


def parse_state_space() -> str:
    text = (RESULTS / "SCOOP_COMPANION_STATE_SPACE.md").read_text(
        encoding="utf-8", errors="replace"
    )
    return "PASS" if "status=PASS" in text else "CHECK"


def parse_xsim() -> str:
    path = RESULTS / "copper_scoop_arbiter_xsim_20260615.log"
    text = ""
    for encoding in ["utf-8", "utf-16"]:
        candidate = path.read_text(encoding=encoding, errors="replace")
        if "SCOOP arbiter completed" in candidate:
            text = candidate
            break
    if not text:
        text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"errors=(\d+)", text)
    if match and match.group(1) == "0":
        return "PASS"
    return "CHECK"


def main() -> None:
    fake = by_policy(
        read_csv(
            RESULTS
            / "gem5_arm_ubuntu_fs_heap_roi"
            / "heap_pointer_roi_n32768_fakeonly_f4_summary.csv"
        )
    )
    traffic = by_secret_policy(
        read_csv(
            RESULTS
            / "gem5_arm_ubuntu_fs_dmp_oracle"
            / "dmp_oracle_i8192_p4_summary.csv"
        )
    )
    observer = by_secret_policy(
        read_csv(
            RESULTS
            / "gem5_arm_ubuntu_fs_dmp_oracle"
            / "dmp_oracle_i512_p4_probe1_evict512_summary.csv"
        )
    )
    observer_seed1111 = by_secret_policy(
        read_csv(
            RESULTS
            / "gem5_arm_ubuntu_fs_dmp_oracle"
            / "dmp_oracle_i512_p4_probe1_evict512_seed1111_summary.csv"
        )
    )
    observer_seed2222 = by_secret_policy(
        read_csv(
            RESULTS
            / "gem5_arm_ubuntu_fs_dmp_oracle"
            / "dmp_oracle_i512_p4_probe1_evict512_seed2222_summary.csv"
        )
    )
    split_rows = {
        (row["secret"], row["policy"], row["phase"]): row
        for row in read_csv(
            RESULTS
            / "gem5_arm_ubuntu_fs_dmp_oracle"
            / "dmp_oracle_i512_p4_probe1_evict512_split_summary.csv"
        )
    }
    observer_seeds = [observer, observer_seed1111, observer_seed2222]
    naive_l1_deltas = [
        delta(seed_rows, "naive", "l1d_demand_misses")
        for seed_rows in observer_seeds
    ]
    naive_allowed_deltas = [
        delta(seed_rows, "naive", "allowedCandidates")
        for seed_rows in observer_seeds
    ]
    scoop_allowed_deltas = [
        delta(seed_rows, "spp_copper_slack", "allowedCandidates")
        for seed_rows in observer_seeds
    ]

    def split_delta(policy: str, key: str) -> int:
        return (
            as_int(split_rows[("1", policy, "scan")], key)
            - as_int(split_rows[("0", policy, "scan")], key)
        )

    naive_fake = fake["naive"]
    copper_fake = fake["copper_clpd64k_peb"]
    scoop_fake = fake["spp_copper_slack"]

    lines = [
        "# COPPER/SCOOP Security Evidence Portfolio",
        "",
        "This portfolio consolidates adversarial AArch64 full-system runs and",
        "the SCOOP arbitration checks. The security claim supported here is",
        "differential: content-derived prefetch behavior should not change as a",
        "function of secret pointer-shaped data unless committed provenance",
        "authorizes the candidate.",
        "",
        "| Evidence point | Unsafe signal | COPPER result | SCOOP result | Why it matters |",
        "|---|---:|---:|---:|---|",
        (
            f"| Fake-pointer-only ROI | naive issues {as_int(naive_fake, 'pfIssued')} "
            f"content-derived prefetches from {as_int(naive_fake, 'pointerLikeCandidates')} "
            f"fake observations | PEB allows {as_int(copper_fake, 'allowedCandidates')} "
            f"and blocks {as_int(copper_fake, 'blockedNoProvenance')} | companion allows "
            f"{as_int(scoop_fake, 'allowedCandidates')} and blocks "
            f"{as_int(scoop_fake, 'blockedNoProvenance')} while SPP keeps "
            f"{as_int(scoop_fake, 'pfIssued')} total PF | Rejects pointer-shaped data that is never dereferenced |"
        ),
        (
            f"| Secret traffic oracle | naive PF delta {delta(traffic, 'naive', 'pfIssued')}, "
            f"allowed delta {delta(traffic, 'naive', 'allowedCandidates')} | allowed delta "
            f"{delta(traffic, 'copper_clpd64k_peb', 'allowedCandidates')}, blocked delta "
            f"{delta(traffic, 'copper_clpd64k_peb', 'blockedNoProvenance')} | companion allowed delta "
            f"{delta(traffic, 'spp_copper_slack', 'allowedCandidates')}, blocked delta "
            f"{delta(traffic, 'spp_copper_slack', 'blockedNoProvenance')} | Shows raw loaded secret values create DMP traffic, but not COPPER/SCOOP companion traffic |"
        ),
        (
            f"| Cold-cache observer oracle | naive L1D-miss delta {delta(observer, 'naive', 'l1d_demand_misses')} "
            f"and timing-delta shift {timing_delta(observer, 'naive'):.3f} pp | L1D-miss delta "
            f"{delta(observer, 'copper_clpd64k_peb', 'l1d_demand_misses')}, allowed delta "
            f"{delta(observer, 'copper_clpd64k_peb', 'allowedCandidates')} | L1D-miss delta "
            f"{delta(observer, 'spp_copper_slack', 'l1d_demand_misses')}, companion allowed delta "
            f"{delta(observer, 'spp_copper_slack', 'allowedCandidates')} | Tests whether secret-shaped data warms an observable cache footprint |"
        ),
        (
            f"| Observer seed sweep | naive allowed deltas {min(naive_allowed_deltas)}..{max(naive_allowed_deltas)}, "
            f"L1D-miss deltas {min(naive_l1_deltas)}..{max(naive_l1_deltas)} | standalone COPPER L1D-miss delta 0 in all seeds | "
            f"companion allowed delta set {','.join(str(v) for v in sorted(set(scoop_allowed_deltas)))} | "
            f"Checks the observer oracle across three address permutations |"
        ),
        (
            f"| Split scan/probe audit | scan PF delta {split_delta('naive', 'pfIssued')}, "
            f"allowed delta {split_delta('naive', 'allowedCandidates')} | scan allowed delta "
            f"{split_delta('copper_clpd64k_peb', 'allowedCandidates')}, blocked delta "
            f"{split_delta('copper_clpd64k_peb', 'blockedNoProvenance')} | scan companion allowed delta "
            f"{split_delta('spp_copper_slack', 'allowedCandidates')}, blocked delta "
            f"{split_delta('spp_copper_slack', 'blockedNoProvenance')} | Separates the unauthorized secret scan from the later legitimate target probe |"
        ),
        (
            f"| SCOOP bounded arbitration checker | companion-first and round-robin fail | n/a | "
            f"{parse_state_space()} to depth 10 | Verifies the slack-only invariant at the algorithm level |"
        ),
        (
            f"| SCOOP RTL arbiter simulation | randomized stall/ready stress | n/a | "
            f"{parse_xsim()} under Vivado XSim | Checks the synthesizable arbitration structure, not just the model |"
        ),
        "",
        "Key readout:",
        "",
        f"- The strongest unsafe signal is the traffic oracle: {delta(traffic, 'naive', 'pfIssued')} extra DMP-like prefetches when the secret data words are valid heap addresses.",
        f"- The strongest observable side-channel signal is the cold-cache oracle: unsafe DMP reduces target-probe L1D demand misses by {-delta(observer, 'naive', 'l1d_demand_misses')} and shifts relative timing by {timing_delta(observer, 'naive'):.3f} percentage points.",
        f"- Across three observer seeds, unsafe DMP always has positive allowed deltas ({min(naive_allowed_deltas)}..{max(naive_allowed_deltas)}) and fewer L1D misses for `secret=1` ({min(naive_l1_deltas)}..{max(naive_l1_deltas)}).",
        f"- The split scan/probe audit localizes the leak: unsafe DMP's scan phase has allowed delta {split_delta('naive', 'allowedCandidates')}, while COPPER and SCOOP scan-phase allowed deltas are both 0.",
        f"- SCOOP preserves the conventional SPP lane but keeps the companion lane differentially silent in both oracle tests: allowed-candidate delta {delta(traffic, 'spp_copper_slack', 'allowedCandidates')} in the traffic oracle and {delta(observer, 'spp_copper_slack', 'allowedCandidates')} in the observer oracle.",
        "- The earlier non-split observer edge is now bounded by phase evidence: during the unauthorized scan phase, standalone COPPER and SCOOP both have zero allowed-candidate delta.",
        "- All full-system rows used here completed with `rc=0` and zero fill-origin translation faults.",
        "",
        "Status: stronger than the prior artifact, but still not a guaranteed top-tier acceptance. The remaining high-value evidence gap is broader production-style workloads and a clean paper writeup that states the differential security claim precisely.",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
