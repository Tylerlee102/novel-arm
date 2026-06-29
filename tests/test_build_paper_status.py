from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research" / "scripts"))

import build_paper  # noqa: E402


class BuildPaperStatusTests(unittest.TestCase):
    def test_write_status_drops_stale_pass_rows_with_missing_logs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            results = root / "research" / "results"
            paper = root / "research" / "paper"
            logs = results / "logs" / "paper"
            paper.mkdir(parents=True)
            logs.mkdir(parents=True)
            (paper / "main.pdf").write_bytes(b"%PDF-1.4\n")
            (logs / "build_paper.log").write_text("ok\n", encoding="utf-8")

            out = results / "paper_build_status.csv"
            with out.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(
                    fh,
                    fieldnames=["environment", "status", "pdf_path", "latex_engine", "errors", "warnings", "log_path", "notes"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "environment": "github_actions",
                        "status": "PASS",
                        "pdf_path": "research/paper/main.pdf",
                        "latex_engine": "latexmk",
                        "errors": "0",
                        "warnings": "0",
                        "log_path": "research/paper/main.log",
                        "notes": "stale log path",
                    }
                )

            old_root, old_results, old_out, old_env = build_paper.ROOT, build_paper.RESULTS, build_paper.OUT, build_paper.ENVIRONMENT
            try:
                build_paper.ROOT = root
                build_paper.RESULTS = results
                build_paper.OUT = out
                build_paper.ENVIRONMENT = "local_windows"
                build_paper.write_status(
                    "PASS",
                    "research/paper/main.pdf",
                    "reportlab-fallback",
                    "0",
                    "0",
                    "research/results/logs/paper/build_paper.log",
                    "fresh local row",
                )
            finally:
                build_paper.ROOT, build_paper.RESULTS, build_paper.OUT, build_paper.ENVIRONMENT = (
                    old_root,
                    old_results,
                    old_out,
                    old_env,
                )

            with out.open(newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))

        self.assertEqual(["local_windows"], [row["environment"] for row in rows])
        self.assertEqual("research/results/logs/paper/build_paper.log", rows[0]["log_path"])


if __name__ == "__main__":
    unittest.main()
