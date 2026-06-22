#!/usr/bin/env python3
"""Storage proxy tied to the ROI-bracketed heap-pointer full-system sweep."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROI_DIR = ROOT / "research" / "results" / "gem5_arm_ubuntu_fs_heap_roi"
IN_CSV = ROI_DIR / "heap_pointer_roi_n32768_p16_f4_fs_summary.csv"
OUT_CSV = ROI_DIR / "heap_pointer_roi_storage_proxy.csv"
OUT_MD = ROI_DIR / "HEAP_POINTER_ROI_STORAGE_PROXY.md"


# A transparent retained-state proxy, not an SRAM compiler or ASIC area number.
VALID_BITS = 1
LINE_TAG_BITS = 42      # 48-bit VA/PA line number after 64 B line offset.
WORD_BITS = 3           # 8-byte pointers in a 64 B line.
WORD_MASK_BITS = 8
DOMAIN_BITS = 24        # ASID/VMID/TTBR-domain digest class.
CONTEXT_BITS = 9        # small core/requestor/context/secure class proxy.
LINE_EPOCH_BITS = 8
VALUE_TOKEN_BITS = 48   # Matches the gem5 exact-proof sensitivity setting.


EXACT_BITS_PER_ENTRY = (
    VALID_BITS
    + LINE_TAG_BITS
    + WORD_BITS
    + DOMAIN_BITS
    + CONTEXT_BITS
    + VALUE_TOKEN_BITS
)

CLPD_BITS_PER_ENTRY = (
    VALID_BITS
    + LINE_TAG_BITS
    + DOMAIN_BITS
    + CONTEXT_BITS
    + LINE_EPOCH_BITS
    + WORD_MASK_BITS
)


POLICY_ENTRIES = {
    "copper_exact16k": ("exact", 16_384, EXACT_BITS_PER_ENTRY),
    "copper_exact131k": ("exact", 131_072, EXACT_BITS_PER_ENTRY),
    "copper_clpd8k": ("clpd", 8_192, CLPD_BITS_PER_ENTRY),
    "copper_clpd16k": ("clpd", 16_384, CLPD_BITS_PER_ENTRY),
    "copper_clpd32k": ("clpd", 32_768, CLPD_BITS_PER_ENTRY),
    "copper_clpd64k": ("clpd", 65_536, CLPD_BITS_PER_ENTRY),
}


def kib(bits: int) -> float:
    return bits / 8.0 / 1024.0


def main() -> None:
    with IN_CSV.open(newline="", encoding="utf-8") as fh:
        source_rows = list(csv.DictReader(fh))

    rows: list[dict[str, str]] = []
    for row in source_rows:
        policy = row["policy"]
        if policy not in POLICY_ENTRIES:
            continue
        kind, entries, bits_per_entry = POLICY_ENTRIES[policy]
        total_bits = entries * bits_per_entry
        rows.append(
            {
                "policy": policy,
                "kind": kind,
                "entries": str(entries),
                "bits_per_entry": str(bits_per_entry),
                "storage_kib": f"{kib(total_bits):.2f}",
                "tick_delta_vs_none_pct": row["tick_delta_vs_none_pct"],
                "pfIssued": row["pfIssued"],
                "proofEvictions": row["proofEvictions"],
                "targetLineWitnessMisses": row["targetLineWitnessMisses"],
                "fillPrefetchTranslationFault": row["fillPrefetchTranslationFault"],
            }
        )

    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    exact131 = next(row for row in rows if row["policy"] == "copper_exact131k")
    clpd64 = next(row for row in rows if row["policy"] == "copper_clpd64k")
    storage_reduction = (
        float(exact131["storage_kib"]) / float(clpd64["storage_kib"])
    )

    lines = [
        "# Heap ROI Storage Proxy",
        "",
        "This proxy converts the ROI capacity sweep into retained proof-state cost.",
        "It is not an SRAM compiler, FPGA utilization report, or ASIC physical",
        "design estimate. Its purpose is to make the architectural storage tradeoff",
        "explicit under fixed assumptions.",
        "",
        "Assumptions:",
        "",
        f"- Exact proof entry bits: {EXACT_BITS_PER_ENTRY}",
        f"- CLPD entry bits: {CLPD_BITS_PER_ENTRY}",
        f"- Line tag bits: {LINE_TAG_BITS}",
        f"- Domain/token digest bits: {DOMAIN_BITS}",
        f"- Context/requestor/security bits: {CONTEXT_BITS}",
        f"- Exact value-token bits: {VALUE_TOKEN_BITS}",
        f"- CLPD line epoch bits: {LINE_EPOCH_BITS}",
        f"- CLPD 64 B line mask bits for 8-byte words: {WORD_MASK_BITS}",
        "",
        "| Policy | Kind | Entries | Bits/entry | Storage | ROI delta | PF issued | Proof evictions | CTLW misses | Translation faults |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {policy} | {kind} | {entries} | {bits_per_entry} | {storage_kib} KiB | "
            "{tick_delta_vs_none_pct}% | {pfIssued} | {proofEvictions} | "
            "{targetLineWitnessMisses} | {fillPrefetchTranslationFault} |".format(**row)
        )

    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            f"- CLPD-64K uses {storage_reduction:.2f}x less retained proof storage than exact-131K under this proxy.",
            "- CLPD-64K is the first measured point with zero CLPD proof evictions in the ROI sweep.",
            "- Exact-131K and CLPD-64K both remove CTLW misses and translation faults in this workload, but CLPD does so with line-mask authority rather than value-exact source-word entries.",
            "- The storage proxy should be replaced with SRAM/CAM banking and timing before claiming production area or power.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(OUT_MD)
    print(OUT_CSV)


if __name__ == "__main__":
    main()
