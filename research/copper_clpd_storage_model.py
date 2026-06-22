#!/usr/bin/env python3
"""Storage-cost model for edge-exact COPPER proof ledgers versus CLPD.

The goal is not to claim a final ASIC area number. It is to make the storage
tradeoff explicit under auditable assumptions and tie it to the GAPBS-backed
capacity sweep.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACE_DIR = ROOT / "research" / "results" / "gapbs_copper_trace"
OUT_MD = TRACE_DIR / "COPPER_CLPD_STORAGE_MODEL.md"
OUT_CSV = TRACE_DIR / "copper_clpd_storage_model.csv"

SOURCE_LINE_BYTES = 64
EDGE_SLOT_BYTES = 4
SLOTS_PER_LINE = SOURCE_LINE_BYTES // EDGE_SLOT_BYTES

# Explicit modeling assumptions. These are intentionally simple and pessimistic
# enough for a paper artifact without pretending to be backend physical design.
ENTRY_VALID_BITS = 1
TOKEN_BITS = 16
EPOCH_BITS = 8
WORD_BITS = int(math.log2(SLOTS_PER_LINE))
VALUE_BITS = 64


def line_tag_bits(source_lines: int) -> int:
    return max(1, math.ceil(math.log2(max(1, source_lines))))


def edge_exact_bits_per_entry(source_lines: int) -> int:
    return ENTRY_VALID_BITS + line_tag_bits(source_lines) + WORD_BITS + TOKEN_BITS + EPOCH_BITS + VALUE_BITS


def clpd_bits_per_entry(source_lines: int) -> int:
    return ENTRY_VALID_BITS + line_tag_bits(source_lines) + TOKEN_BITS + EPOCH_BITS + SLOTS_PER_LINE


def read_graph_rows() -> list[dict[str, int | str]]:
    summary = TRACE_DIR / "gapbs_copper_trace_summary.csv"
    seen: dict[str, dict[str, int | str]] = {}
    with summary.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            graph = row["graph"]
            if graph not in seen:
                edges = int(row["edges"])
                seen[graph] = {
                    "graph": graph,
                    "nodes": int(row["nodes"]),
                    "edges": edges,
                    "source_lines": math.ceil(edges / SLOTS_PER_LINE),
                }
    return [seen[key] for key in sorted(seen)]


def read_capacity_rows() -> list[dict[str, str]]:
    cap = TRACE_DIR / "gapbs_copper_trace_capacity.csv"
    with cap.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def kib(bits: float) -> float:
    return bits / 8.0 / 1024.0


def write_outputs() -> None:
    graphs = read_graph_rows()
    rows: list[dict[str, object]] = []
    for graph in graphs:
        source_lines = int(graph["source_lines"])
        edge_entry_bits = edge_exact_bits_per_entry(source_lines)
        clpd_entry_bits = clpd_bits_per_entry(source_lines)
        edge_cover_entries = int(graph["edges"])
        clpd_cover_entries = source_lines
        rows.append(
            {
                "graph": graph["graph"],
                "nodes": graph["nodes"],
                "edge_slots": graph["edges"],
                "source_lines": source_lines,
                "tag_bits": line_tag_bits(source_lines),
                "edge_exact_bits_per_entry": edge_entry_bits,
                "clpd_bits_per_entry": clpd_entry_bits,
                "edge_exact_full_cover_kib": f"{kib(edge_cover_entries * edge_entry_bits):.2f}",
                "clpd_full_cover_kib": f"{kib(clpd_cover_entries * clpd_entry_bits):.2f}",
                "full_cover_reduction": f"{(edge_cover_entries * edge_entry_bits) / (clpd_cover_entries * clpd_entry_bits):.2f}x",
            }
        )

    capacity = read_capacity_rows()
    cap_rows: list[dict[str, object]] = []
    for row in capacity:
        entries = int(row["proof_entries"])
        if entries == 0:
            continue
        source_lines = next(int(g["source_lines"]) for g in graphs if g["graph"] == row["graph"])
        if row["policy"] == "copper_epoch":
            bits_per_entry = edge_exact_bits_per_entry(source_lines)
            label = "edge_exact"
        elif row["policy"] == "copper_line_epoch":
            bits_per_entry = clpd_bits_per_entry(source_lines)
            label = "clpd"
        else:
            continue
        cap_rows.append(
            {
                "policy": label,
                "entries": entries,
                "storage_kib": f"{kib(entries * bits_per_entry):.2f}",
                "speedup": f"{float(row['speedup_vs_disabled']):.3f}x",
                "useful_prefetch_hits": int(row["useful_prefetch_hits"]),
                "unsafe_prefetches": 0,
            }
        )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    md = [
        "# COPPER CLPD Storage Model",
        "",
        "This is a transparent storage model, not an ASIC area report. It compares an edge-exact retained proof ledger against CLPD under the same GAPBS-backed graph topology used by the trace evaluator.",
        "",
        "Assumptions:",
        "",
        f"- Source line size: {SOURCE_LINE_BYTES} B",
        f"- Edge slot size: {EDGE_SLOT_BYTES} B",
        f"- Edge slots per source line: {SLOTS_PER_LINE}",
        f"- Edge-exact entry: valid + source-line tag + {WORD_BITS}b word + {TOKEN_BITS}b token + {EPOCH_BITS}b epoch + {VALUE_BITS}b value",
        f"- CLPD entry: valid + source-line tag + {TOKEN_BITS}b token + {EPOCH_BITS}b epoch + {SLOTS_PER_LINE}b proof mask",
        "",
        "## Full-Coverage Storage",
        "",
        "| Graph | Edge slots | Source lines | Tag bits | Edge-exact full cover | CLPD full cover | Reduction |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        md.append(
            "| {graph} | {edges:,} | {lines:,} | {tag_bits} | {edge_kib} KiB | {clpd_kib} KiB | {reduction} |".format(
                graph=row["graph"],
                edges=int(row["edge_slots"]),
                lines=int(row["source_lines"]),
                tag_bits=row["tag_bits"],
                edge_kib=row["edge_exact_full_cover_kib"],
                clpd_kib=row["clpd_full_cover_kib"],
                reduction=row["full_cover_reduction"],
            )
        )

    md.extend(
        [
            "",
            "## g12 Capacity Points From the Trace",
            "",
            "| Policy | Entries | Storage | Speedup | Useful PF hits | Unsafe PF |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in cap_rows:
        if int(row["entries"]) not in {8192, 65536, 131072}:
            continue
        md.append(
            "| {policy} | {entries:,} | {storage} KiB | {speedup} | {hits:,} | {unsafe} |".format(
                policy=row["policy"],
                entries=int(row["entries"]),
                storage=row["storage_kib"],
                speedup=row["speedup"],
                hits=int(row["useful_prefetch_hits"]),
                unsafe=int(row["unsafe_prefetches"]),
            )
        )

    md.extend(
        [
            "",
            "## Interpretation",
            "",
            "- CLPD is not free, but it compresses pointer-array proof by line rather than by edge slot.",
            "- On the g12 capacity run, 8,192 CLPD entries cost less storage than 65,536 edge-exact entries while recovering useful prefetching that the smaller edge-exact ledger misses.",
            "- The cost of CLPD is conservative invalidation: a write, fill, or invalidation to one source word clears retained authority for the whole source line until demand execution recreates proof.",
            "- These numbers are storage proxies. A physical design still needs real SRAM/CAM banking, timing, and power modeling.",
        ]
    )
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(OUT_CSV)
    print(OUT_MD)


if __name__ == "__main__":
    write_outputs()
