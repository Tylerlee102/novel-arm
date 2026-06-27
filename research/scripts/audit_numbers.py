#!/usr/bin/env python3
"""Check that paper numbers are traceable to generated evidence files."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "research" / "paper" / "main.tex"
RESULTS = ROOT / "research" / "results"
OUT = RESULTS / "number_audit.csv"
NUMBER = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?(?:x|%|K|M|ns|KiB|W)?")


def evidence_numbers() -> set[str]:
    nums: set[str] = set()
    for path in RESULTS.glob("*.csv"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in NUMBER.findall(text):
            nums.add(match)
            nums.add(match.rstrip("x%KM"))
    return nums


def main() -> int:
    text = PAPER.read_text(encoding="utf-8") if PAPER.exists() else ""
    source_nums = evidence_numbers()
    rows = []
    for match in NUMBER.finditer(text):
        token = match.group(0)
        bare = token.rstrip("x%KM")
        if bare in {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"}:
            continue
        if token in source_nums or bare in source_nums:
            continue
        line = text.count("\n", 0, match.start()) + 1
        rows.append({"status": "FAIL", "number": token, "line": line, "source": "not found in generated CSVs"})
    if not rows:
        rows.append({"status": "PASS", "number": "", "line": "", "source": "All material numeric tokens are traceable or absent."})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["status", "number", "line", "source"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 1 if any(row["status"] == "FAIL" for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
