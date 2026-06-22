"""Summarize ChampSim JSON results produced for COPPER."""

from __future__ import annotations

import csv
import json
from pathlib import Path


RESULT_DIR = Path("research/results/champsim")
OUT_CSV = RESULT_DIR / "champsim_summary.csv"
OUT_MD = RESULT_DIR / "CHAMPSIM_SUMMARY.md"


def first_counter(node: dict, access_type: str, field: str) -> int:
    return int(node.get(access_type, {}).get(field, [0])[0])


def parse_name(path: Path) -> tuple[str, str]:
    stem = path.stem
    for prefix in ("next_line_w0_", "ip_stride_w0_", "no_w0_"):
        if stem.startswith(prefix):
            return prefix.removesuffix("_w0_"), stem[len(prefix) :]
    raise ValueError(f"Unexpected ChampSim result name: {path.name}")


def summarize(path: Path) -> dict[str, int | float | str]:
    prefetcher, trace = parse_name(path)
    data = json.loads(path.read_text())[0]["roi"]
    core = data["cores"][0]
    l1d = data["cpu0_L1D"]
    llc = data["LLC"]
    dtlb = data["cpu0_DTLB"]

    l1d_access = sum(first_counter(l1d, kind, "hit") + first_counter(l1d, kind, "miss") for kind in ("LOAD", "WRITE", "RFO", "PREFETCH", "TRANSLATION"))
    l1d_miss = sum(first_counter(l1d, kind, "miss") for kind in ("LOAD", "WRITE", "RFO", "PREFETCH", "TRANSLATION"))
    llc_access = sum(first_counter(llc, kind, "hit") + first_counter(llc, kind, "miss") for kind in ("LOAD", "WRITE", "RFO", "PREFETCH", "TRANSLATION"))
    llc_miss = sum(first_counter(llc, kind, "miss") for kind in ("LOAD", "WRITE", "RFO", "PREFETCH", "TRANSLATION"))

    return {
        "prefetcher": prefetcher,
        "trace": trace,
        "ipc": round(core["instructions"] / core["cycles"], 5),
        "instructions": int(core["instructions"]),
        "cycles": int(core["cycles"]),
        "l1d_access": l1d_access,
        "l1d_miss": l1d_miss,
        "l1d_miss_rate": round(l1d_miss / l1d_access, 5) if l1d_access else 0.0,
        "l1d_miss_merge": sum(first_counter(l1d, kind, "miss_merge") for kind in ("LOAD", "WRITE", "RFO", "PREFETCH", "TRANSLATION")),
        "l1d_pf_requested": int(l1d["prefetch requested"]),
        "l1d_pf_issued": int(l1d["prefetch issued"]),
        "l1d_pf_useful": int(l1d["useful prefetch"]),
        "l1d_pf_useless": int(l1d["useless prefetch"]),
        "llc_access": llc_access,
        "llc_miss": llc_miss,
        "dtlb_miss": first_counter(dtlb, "LOAD", "miss"),
    }


def write_markdown(rows: list[dict[str, int | float | str]]) -> None:
    headers = [
        "prefetcher",
        "trace",
        "ipc",
        "l1d_miss_rate",
        "l1d_miss",
        "l1d_pf_requested",
        "l1d_pf_issued",
        "l1d_pf_useful",
        "llc_miss",
    ]
    lines = [
        "# ChampSim zero-warmup synthetic trace summary",
        "",
        "These runs validate ordinary cache/prefetch behavior on stock ChampSim traces. They do not model COPPER provenance tags; COPPER-specific safety results are from the Python trace model and RTL.",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")
    OUT_MD.write_text("\n".join(lines) + "\n")


def main() -> None:
    rows = sorted((summarize(path) for path in RESULT_DIR.glob("*_w0_*.json")), key=lambda r: (str(r["trace"]), str(r["prefetcher"])))
    with OUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    write_markdown(rows)
    print(f"wrote {OUT_CSV}")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
