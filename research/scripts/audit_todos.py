#!/usr/bin/env python3
"""Ensure the final LaTeX paper body has no TODO-style placeholders."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "research" / "paper" / "main.tex"
OUT = ROOT / "research" / "results" / "todo_audit.csv"
PATTERN = re.compile(r"TODO|FIXME|placeholder|fill later", re.I)


def main() -> int:
    text = PAPER.read_text(encoding="utf-8") if PAPER.exists() else ""
    rows = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if PATTERN.search(line):
            rows.append({"status": "FAIL", "line": lineno, "context": line.strip()})
    if not rows:
        rows.append({"status": "PASS", "line": "", "context": "No TODO/FIXME/placeholder text found in paper."})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["status", "line", "context"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 1 if any(row["status"] == "FAIL" for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
