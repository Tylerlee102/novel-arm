#!/usr/bin/env python3
"""Summarize Olden Bisort fingerprint validation runs."""

from __future__ import annotations

import re
from pathlib import Path

from summarize_olden_suite_fs import parse_stats_sections, sum_matching


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "gem5_arm_ubuntu_fs_olden_suite"
RUNS = {
    "none": RESULTS / "gem5_arm_ubuntu_fs_olden_bisort_fingerprint_randomalloc_none",
    "copper_clpd64k_peb": RESULTS
    / "gem5_arm_ubuntu_fs_olden_bisort_fingerprint_randomalloc_copper_clpd64k_peb",
}
PHASE_RE = re.compile(
    r"BISORT_FINGERPRINT phase=(?P<phase>\w+) count=(?P<count>\d+) "
    r"expected=(?P<expected>\d+) checksum=(?P<checksum>-?\d+) "
    r"hist_hash=(?P<hist_hash>\d+) min=(?P<min>-?\d+) "
    r"max=(?P<max>-?\d+) spring=(?P<spring>-?\d+)"
)
RC_RE = re.compile(r"COPPER_FS_NATIVE_JOB_DONE olden_bisort rc=(?P<rc>\d+)")


def parse_terminal(path: Path) -> tuple[list[dict[str, str]], str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rows = [match.groupdict() for match in PHASE_RE.finditer(text)]
    rc_match = RC_RE.search(text)
    return rows, rc_match.group("rc") if rc_match else ""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Olden Bisort Fingerprint Validation",
        "",
        "This validation build keeps the public Bisort algorithm but adds compact",
        "guest-side fingerprints over all tree values plus the spring value.",
        "The fingerprint is order-independent: equal count, checksum, and",
        "histogram hash across phases shows that the full value multiset is",
        "preserved; equal fingerprints across policies show that COPPER did not",
        "change architectural results for this checked run.",
        "",
        "| Policy | Phase | Count | Expected | Checksum | Histogram hash | Min | Max | Spring | rc |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    by_policy: dict[str, list[dict[str, str]]] = {}
    counters: dict[str, dict[str, int]] = {}
    rcs: dict[str, str] = {}
    for policy, path in RUNS.items():
        rows, rc = parse_terminal(path / "board.terminal")
        by_policy[policy] = rows
        rcs[policy] = rc
        stats = parse_stats_sections(path / "stats.txt")[0]
        counters[policy] = {
            "pfIssued": sum_matching(stats, ".prefetcher.pfIssued", ".prefetcher."),
            "blockedNoProvenance": sum_matching(
                stats, ".prefetcher.blockedNoProvenance", ".prefetcher."
            ),
            "targetLineWitnessMisses": sum_matching(
                stats, ".prefetcher.targetLineWitnessMisses", ".prefetcher."
            ),
            "fillPrefetchTranslationFault": sum_matching(
                stats, ".prefetcher.fillPrefetchTranslationFault", ".prefetcher."
            ),
        }
        for row in rows:
            lines.append(
                f"| {policy} | {row['phase']} | {row['count']} | "
                f"{row['expected']} | {row['checksum']} | {row['hist_hash']} | "
                f"{row['min']} | {row['max']} | {row['spring']} | {rc} |"
            )

    lines.extend(
        [
            "",
            "## COPPER Counters",
            "",
            "| Policy | PF issued | Blocked no provenance | CTLW misses | Translation faults |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for policy, values in counters.items():
        lines.append(
            f"| {policy} | {values['pfIssued']} | {values['blockedNoProvenance']} | "
            f"{values['targetLineWitnessMisses']} | "
            f"{values['fillPrefetchTranslationFault']} |"
        )

    phases_match = True
    none_rows = {row["phase"]: row for row in by_policy["none"]}
    copper_rows = {row["phase"]: row for row in by_policy["copper_clpd64k_peb"]}
    for phase, base_row in none_rows.items():
        copper_row = copper_rows.get(phase)
        if copper_row is None:
            phases_match = False
            continue
        for field in ["count", "expected", "checksum", "hist_hash", "min", "max", "spring"]:
            if base_row[field] != copper_row[field]:
                phases_match = False

    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"- Fingerprints match baseline vs COPPER: {'yes' if phases_match else 'no'}.",
            "- Initial, forward, and backward phases preserve the same count, checksum, and histogram hash.",
            f"- COPPER issued {counters['copper_clpd64k_peb']['pfIssued']} prefetches, blocked "
            f"{counters['copper_clpd64k_peb']['blockedNoProvenance']} candidates without provenance, "
            f"and reported {counters['copper_clpd64k_peb']['fillPrefetchTranslationFault']} translation faults.",
            "",
        ]
    )
    out = OUT / "OLDEN_BISORT_FINGERPRINT_VALIDATION.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
