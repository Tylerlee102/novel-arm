"""Summarize local GAPBS runs."""

from __future__ import annotations

import csv
import re
from pathlib import Path


RESULT_DIR = Path("research/results/gapbs")
OUT_CSV = RESULT_DIR / "gapbs_summary.csv"
OUT_MD = RESULT_DIR / "GAPBS_SUMMARY.md"

NAME_RE = re.compile(r"(?P<kernel>[a-z_]+)_g(?P<scale>\d+)_n(?P<trials>\d+)(?:_i(?P<iters>\d+))?\.txt")


def grab_float(text: str, label: str) -> float:
    match = re.search(rf"{re.escape(label)}:\s+([0-9.]+)", text)
    return float(match.group(1)) if match else 0.0


def grab_graph(text: str) -> tuple[int, int, int]:
    match = re.search(r"Graph has\s+(\d+)\s+nodes and\s+(\d+)\s+undirected edges for degree:\s+(\d+)", text)
    if not match:
        return 0, 0, 0
    return tuple(map(int, match.groups()))


def summarize(path: Path) -> dict[str, int | float | str]:
    match = NAME_RE.fullmatch(path.name)
    if not match:
        raise ValueError(f"Unexpected GAPBS result name: {path.name}")
    text = path.read_text(errors="replace")
    nodes, edges, degree = grab_graph(text)
    return {
        "kernel": match.group("kernel"),
        "scale": int(match.group("scale")),
        "trials": int(match.group("trials")),
        "nodes": nodes,
        "edges": edges,
        "degree": degree,
        "generate_s": grab_float(text, "Generate Time"),
        "build_s": grab_float(text, "Build Time"),
        "avg_trial_s": grab_float(text, "Average Time"),
        "verification": "PASS" if "Verification:           PASS" in text and "Verification:           FAIL" not in text else "FAIL",
    }


def write_markdown(rows: list[dict[str, int | float | str]]) -> None:
    headers = ["kernel", "scale", "trials", "nodes", "edges", "avg_trial_s", "verification"]
    lines = [
        "# GAPBS local run summary",
        "",
        "Runs used generated Kronecker graphs, OpenMP enabled, and verification enabled. These are workload sanity checks, not full GAP benchmark-suite submissions.",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")
    OUT_MD.write_text("\n".join(lines) + "\n")


def main() -> None:
    rows = sorted((summarize(path) for path in RESULT_DIR.glob("*_g*.txt")), key=lambda r: (int(r["scale"]), str(r["kernel"])))
    with OUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    write_markdown(rows)
    print(f"wrote {OUT_CSV}")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
