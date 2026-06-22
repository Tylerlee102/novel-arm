#!/usr/bin/env python3
"""Summarize direct secret-bit DMP-oracle full-system experiments."""

from __future__ import annotations

import csv
import math
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "gem5_arm_ubuntu_fs_dmp_oracle"

ITEMS = int(os.environ.get("ITEMS", "8192"))
PASSES = int(os.environ.get("PASSES", "4"))
PROBE_TARGETS = int(os.environ.get("PROBE_TARGETS", "0"))
PROBE_PASSES = int(os.environ.get("PROBE_PASSES", "1"))
EVICT_KB = int(os.environ.get("EVICT_KB", "0"))
POLICIES = os.environ.get(
    "POLICY_LIST", "none naive copper_clpd64k_peb spp spp_copper_slack"
).split()

COUNTERS = [
    "pfIssued",
    "pfUseful",
    "pointerLikeCandidates",
    "learnedProofs",
    "proofEvictions",
    "allowedCandidates",
    "blockedNoProvenance",
    "fillPrefetchTranslated",
    "fillPrefetchTranslationFault",
    "targetLineWitnessHits",
    "targetLineWitnessMisses",
    "carriedProvenanceTerminalStops",
    "boundaryFlushes",
    "boundaryAuthorityEntriesDropped",
    "boundaryPrefetchesDropped",
]


def tag(secret: int) -> str:
    if f"TAG_SECRET{secret}" in os.environ:
        return os.environ[f"TAG_SECRET{secret}"]
    if PROBE_TARGETS:
        return f"i{ITEMS}_p{PASSES}_probe{PROBE_PASSES}_evict{EVICT_KB}_secret{secret}"
    return f"i{ITEMS}_p{PASSES}_secret{secret}"


def first_stats(path: Path) -> dict[str, float]:
    text = path.read_text(encoding="utf-8", errors="replace")
    begin = text.index("---------- Begin Simulation Statistics ----------")
    end = text.index("---------- End Simulation Statistics", begin)
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
    return stats


def sum_matching(stats: dict[str, float], suffix: str, contains: str | None = None) -> int:
    return int(
        sum(
            value
            for key, value in stats.items()
            if key.endswith(suffix)
            and (contains is None or contains in key)
            and not math.isnan(value)
        )
    )


def sum_prefetch_counter(stats: dict[str, float], counter: str) -> int:
    matches = [
        (key, value)
        for key, value in stats.items()
        if key.endswith(f".{counter}")
        and ".prefetcher" in key
        and not math.isnan(value)
    ]
    child_matches = [
        value
        for key, value in matches
        if ".prefetchers" in key
        or ".primary." in key
        or ".companion." in key
    ]
    if child_matches:
        return int(sum(child_matches))
    return int(sum(value for _, value in matches))


def terminal_info(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(
        r"DMP_ORACLE_RESULT items=(\d+) passes=(\d+) secret=(\d+) "
        r"(?:probe_targets=(\d+) probe_passes=(\d+) evict_kb=(\d+) "
        r"(?:reset_after_evict=(\d+) )?(?:split_probe_stats=(\d+) )?)?"
        r"seed=(0x[0-9a-fA-F]+) sample0=(0x[0-9a-fA-F]+) "
        r"sample1=(0x[0-9a-fA-F]+) checksum=(0x[0-9a-fA-F]+)",
        text,
    )
    info: dict[str, str] = {}
    if match:
        info.update(
            {
                "items": match.group(1),
                "passes": match.group(2),
                "secret": match.group(3),
                "probe_targets": match.group(4) or "",
                "probe_passes": match.group(5) or "",
                "evict_kb": match.group(6) or "",
                "reset_after_evict": match.group(7) or "",
                "split_probe_stats": match.group(8) or "",
                "seed": match.group(9),
                "sample0": match.group(10),
                "sample1": match.group(11),
                "checksum": match.group(12),
            }
        )
    done = re.search(r"COPPER_FS_NATIVE_A64_DONE rc=(\d+)", text)
    if done:
        info["rc"] = done.group(1)
    return info


def summarize() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for secret in [0, 1]:
        this_tag = tag(secret)
        for policy in POLICIES:
            run_dir = RESULTS / f"gem5_arm_ubuntu_fs_dmp_oracle_{this_tag}_{policy}"
            stats = first_stats(run_dir / "stats.txt")
            info = terminal_info(run_dir / "board.terminal")
            row: dict[str, str] = {
                "secret": str(secret),
                "policy": policy,
                "roi_ticks": str(int(stats.get("simTicks", 0))),
                "insts_not_nop": str(
                    sum_matching(
                        stats,
                        ".core.commitStats0.numInstsNotNOP",
                        "board.processor.switch",
                    )
                ),
                "l1d_demand_misses": str(
                    sum_matching(
                        stats,
                        ".demandMisses::total",
                        "board.cache_hierarchy.l1d-cache-",
                    )
                ),
                "items": info.get("items", ""),
                "passes": info.get("passes", ""),
                "probe_targets": info.get("probe_targets", ""),
                "probe_passes": info.get("probe_passes", ""),
                "evict_kb": info.get("evict_kb", ""),
                "reset_after_evict": info.get("reset_after_evict", ""),
                "seed": info.get("seed", ""),
                "sample0": info.get("sample0", ""),
                "sample1": info.get("sample1", ""),
                "checksum": info.get("checksum", ""),
                "rc": info.get("rc", ""),
            }
            for counter in COUNTERS:
                row[counter] = str(sum_prefetch_counter(stats, counter))
            rows.append(row)

    base_by_secret = {
        row["secret"]: int(row["roi_ticks"])
        for row in rows
        if row["policy"] == "none"
    }
    for row in rows:
        base_ticks = base_by_secret[row["secret"]]
        row["tick_delta_vs_none_pct"] = (
            f"{((int(row['roi_ticks']) / base_ticks) - 1.0) * 100.0:.3f}"
        )
    return rows


def as_int(row: dict[str, str], key: str) -> int:
    return int(row[key])


def leakage_delta(by_key: dict[tuple[str, str], dict[str, str]], policy: str, counter: str) -> int:
    return as_int(by_key[("1", policy)], counter) - as_int(by_key[("0", policy)], counter)


def tick_delta_delta(by_key: dict[tuple[str, str], dict[str, str]], policy: str) -> float:
    return (
        float(by_key[("1", policy)]["tick_delta_vs_none_pct"])
        - float(by_key[("0", policy)]["tick_delta_vs_none_pct"])
    )


def write_outputs(rows: list[dict[str, str]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    suffix = os.environ.get(
        "SUMMARY_SUFFIX",
        (
            f"i{ITEMS}_p{PASSES}_probe{PROBE_PASSES}_evict{EVICT_KB}"
            if PROBE_TARGETS
            else f"i{ITEMS}_p{PASSES}"
        ),
    )
    csv_path = OUT / f"dmp_oracle_{suffix}_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    by_key = {(row["secret"], row["policy"]): row for row in rows}
    naive_s0 = by_key.get(("0", "naive"))
    naive_s1 = by_key.get(("1", "naive"))
    copper_s1 = by_key.get(("1", "copper_clpd64k_peb"))
    scoop_s1 = by_key.get(("1", "spp_copper_slack"))

    lines = [
        "# Direct Secret-Bit DMP-Oracle Full-System Probe",
        "",
        "The AArch64 binary scans ordinary 64-bit data words inside the measured",
        "region and never architecturally dereferences those words as pointers.",
        "`secret=1` fills the words with heap addresses; `secret=0` fills them",
        "with high-bit non-candidate values. A content-directed prefetcher that",
        "uses raw load data can therefore create secret-dependent memory traffic.",
        "",
        (
            f"Configuration: `items={ITEMS}`, `passes={PASSES}`, "
            f"`probe_targets={PROBE_TARGETS}`, `probe_passes={PROBE_PASSES}`, "
            f"`evict_kb={EVICT_KB}`, ARM64 full-system ROI."
        ),
        "",
        "| Secret | Policy | ROI ticks | Delta vs none | L1D misses | PF issued | PF useful | Pointer-like | Learned proofs | Proof evictions | Allowed | Blocked no provenance | Translated PF | Translation faults | CTLW hits | CTLW misses | Boundary authority drops | Boundary PF drops | Checksum | rc |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for row in rows:
        lines.append(
            "| {secret} | {policy} | {roi_ticks} | {tick_delta_vs_none_pct}% | "
            "{l1d_demand_misses} | {pfIssued} | {pfUseful} | "
            "{pointerLikeCandidates} | {learnedProofs} | {proofEvictions} | "
            "{allowedCandidates} | {blockedNoProvenance} | "
            "{fillPrefetchTranslated} | {fillPrefetchTranslationFault} | "
            "{targetLineWitnessHits} | {targetLineWitnessMisses} | "
            "{boundaryAuthorityEntriesDropped} | {boundaryPrefetchesDropped} | "
            "{checksum} | {rc} |".format(**row)
        )

    lines.extend(["", "Oracle deltas (`secret=1 minus secret=0`):", ""])
    lines.append("| Policy | PF issued delta | Pointer-like delta | Allowed delta | Blocked delta | L1D miss delta | Timing-delta delta | CTLW miss delta |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for policy in POLICIES:
        if ("0", policy) not in by_key or ("1", policy) not in by_key:
            continue
        lines.append(
            f"| {policy} | "
            f"{leakage_delta(by_key, policy, 'pfIssued')} | "
            f"{leakage_delta(by_key, policy, 'pointerLikeCandidates')} | "
            f"{leakage_delta(by_key, policy, 'allowedCandidates')} | "
            f"{leakage_delta(by_key, policy, 'blockedNoProvenance')} | "
            f"{leakage_delta(by_key, policy, 'l1d_demand_misses')} | "
            f"{tick_delta_delta(by_key, policy):.3f} pp | "
            f"{leakage_delta(by_key, policy, 'targetLineWitnessMisses')} |"
        )

    if naive_s0 and naive_s1 and copper_s1 and scoop_s1:
        naive_pf_delta = as_int(naive_s1, "pfIssued") - as_int(naive_s0, "pfIssued")
        naive_allowed_delta = (
            as_int(naive_s1, "allowedCandidates") -
            as_int(naive_s0, "allowedCandidates")
        )
        naive_l1_delta = (
            as_int(naive_s1, "l1d_demand_misses")
            - as_int(naive_s0, "l1d_demand_misses")
        )
        copper_block_rate = (
            as_int(copper_s1, "blockedNoProvenance")
            / max(as_int(copper_s1, "pointerLikeCandidates"), 1)
        ) * 100.0
        copper_allowed_delta = (
            as_int(copper_s1, "allowedCandidates")
            - as_int(by_key[("0", "copper_clpd64k_peb")], "allowedCandidates")
        )
        copper_l1_delta = (
            as_int(copper_s1, "l1d_demand_misses")
            - as_int(by_key[("0", "copper_clpd64k_peb")], "l1d_demand_misses")
        )
        scoop_block_rate = (
            as_int(scoop_s1, "blockedNoProvenance")
            / max(as_int(scoop_s1, "pointerLikeCandidates"), 1)
        ) * 100.0
        scoop_allowed_delta = (
            as_int(scoop_s1, "allowedCandidates")
            - as_int(by_key[("0", "spp_copper_slack")], "allowedCandidates")
        )
        scoop_l1_delta = (
            as_int(scoop_s1, "l1d_demand_misses")
            - as_int(by_key[("0", "spp_copper_slack")], "l1d_demand_misses")
        )
        lines.extend(
            [
                "",
                "Interpretation:",
                "",
                f"- Unsafe naive DMP has a secret-dependent prefetch delta of {naive_pf_delta} issued prefetches and {naive_allowed_delta} allowed candidates.",
                (
                    f"- With target probing enabled, unsafe naive DMP changes the observer-phase cache footprint by {naive_l1_delta} L1D demand misses and shifts policy timing by {tick_delta_delta(by_key, 'naive'):.3f} percentage points between secrets."
                    if PROBE_TARGETS
                    else "- In this traffic-only oracle, the workload intentionally does not probe target lines after the secret scan."
                ),
                f"- COPPER with a provenance epoch boundary blocks {copper_block_rate:.3f}% of secret=1 pointer-like observations; its allowed-candidate delta is {copper_allowed_delta}, its L1D-miss delta is {copper_l1_delta}, and it records {as_int(copper_s1, 'fillPrefetchTranslationFault')} translation faults.",
                f"- SCOOP retains the conventional stream lane while its COPPER companion blocks {scoop_block_rate:.3f}% of secret=1 content-derived observations; its companion allowed-candidate delta is {scoop_allowed_delta}, its L1D-miss delta is {scoop_l1_delta}, and it records {as_int(scoop_s1, 'fillPrefetchTranslationFault')} translation faults.",
                "- Matching `rc=0` rows show the tested policies preserved architectural completion; differing checksums across secrets are expected because the data values differ.",
            ]
        )

    md_path = OUT / f"DMP_ORACLE_{suffix.upper()}_SUMMARY.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(md_path)
    print(csv_path)


def main() -> None:
    write_outputs(summarize())


if __name__ == "__main__":
    main()
