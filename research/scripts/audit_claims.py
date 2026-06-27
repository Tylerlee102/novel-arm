#!/usr/bin/env python3
"""Fail on unsupported conference-paper claim language."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "research" / "paper" / "main.tex"
OUT = ROOT / "research" / "results" / "claim_audit.csv"

FORBIDDEN = [
    "first",
    "novel",
    "guarantee",
    "always",
    "never",
    "optimal",
    "negligible",
    "low overhead",
    "state-of-the-art",
    "beats",
    "outperforms",
    "full-system",
    "silicon-ready",
    "industrial-ready",
]
ALLOW_CONTEXT = re.compile(r"do not claim|does not claim|not claim|not a claim|no claim|does not support", re.I)


def main() -> int:
    text = PAPER.read_text(encoding="utf-8") if PAPER.exists() else ""
    rows = []
    for lineno, line in enumerate(text.splitlines(), 1):
        lower = line.lower()
        for term in FORBIDDEN:
            if term in lower and not ALLOW_CONTEXT.search(line):
                rows.append({"status": "FAIL", "term": term, "line": lineno, "context": line.strip()})
    if not rows:
        rows.append({"status": "PASS", "term": "", "line": "", "context": "No unsupported forbidden language found."})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["status", "term", "line", "context"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 1 if any(row["status"] == "FAIL" for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
