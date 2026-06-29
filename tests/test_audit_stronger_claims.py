from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research" / "scripts"))

import audit_stronger_claims as stronger  # noqa: E402


def write_doc(root: Path, text: str) -> Path:
    path = root / "research" / "paper" / "main.tex"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def rows_for(root: Path, text: str) -> tuple[list[dict[str, str]], bool]:
    doc = write_doc(root, text)
    return stronger.audit(root, [doc])


def failing_terms(rows: list[dict[str, str]]) -> set[str]:
    return {row["term"] for row in rows if row["status"] == "FAIL"}


class StrongerClaimAuditTests(unittest.TestCase):
    def run_case(self, text: str) -> tuple[Path, list[dict[str, str]], bool]:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        rows, failed = rows_for(root, text)
        return root, rows, failed

    def test_positive_silicon_proven_fails_without_fabrication_evidence(self) -> None:
        _root, rows, failed = self.run_case("COPPER is silicon-proven.")

        self.assertTrue(failed)
        self.assertIn("silicon-proven", failing_terms(rows))

    def test_negated_asic_signoff_disclaimer_passes(self) -> None:
        _root, rows, failed = self.run_case("This does not claim ASIC signoff.")

        self.assertFalse(failed)
        self.assertTrue(all(row["status"] == "PASS" for row in rows))

    def test_mixed_disclaimer_and_positive_claim_still_fails(self) -> None:
        _root, rows, failed = self.run_case("This does not claim ASIC signoff; COPPER is silicon-proven.")

        self.assertTrue(failed)
        self.assertIn("silicon-proven", failing_terms(rows))
        self.assertFalse(any(row["term"] == "ASIC signoff" and row["status"] == "FAIL" for row in rows))

    def test_measured_power_requires_measured_silicon_pass_row(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = root / "research" / "results" / "lab" / "fpga_tool_power.csv"
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text("tool estimate only\n", encoding="utf-8")
            write_csv(
                root / "research" / "results" / "power_report_index.csv",
                [
                    "evidence_id",
                    "status",
                    "available",
                    "measurement_type",
                    "silicon_measured",
                    "power_mw",
                    "power_report_path",
                ],
                [
                    {
                        "evidence_id": "fpga_tool",
                        "status": "PASS",
                        "available": "yes",
                        "measurement_type": "fpga_tool_estimate",
                        "silicon_measured": "no",
                        "power_mw": "87.0",
                        "power_report_path": "research/results/lab/fpga_tool_power.csv",
                    }
                ],
            )

            rows, failed = rows_for(root, "COPPER reports measured power.")

        self.assertTrue(failed)
        self.assertIn("measured power", failing_terms(rows))

    def test_measured_silicon_power_passes_with_raw_reported_measured_row(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = root / "research" / "results" / "lab" / "rail_power.csv"
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text("time_s,vcore_v,icore_a,power_mw\n0,1.0,0.01,10\n", encoding="utf-8")
            write_csv(
                root / "research" / "results" / "power_report_index.csv",
                [
                    "evidence_id",
                    "status",
                    "available",
                    "measurement_type",
                    "silicon_measured",
                    "power_mw",
                    "power_report_path",
                ],
                [
                    {
                        "evidence_id": "silicon_power",
                        "status": "PASS",
                        "available": "yes",
                        "measurement_type": "measured_silicon",
                        "silicon_measured": "yes",
                        "power_mw": "10.0",
                        "power_report_path": "research/results/lab/rail_power.csv",
                    }
                ],
            )

            rows, failed = rows_for(root, "COPPER reports measured silicon power.")

        self.assertFalse(failed)
        guarded = [row for row in rows if row["term"] in {"measured power", "measured silicon"}]
        self.assertTrue(all(row["status"] == "PASS" for row in guarded))

    def test_case_and_format_variants_are_blocked(self) -> None:
        _root, rows, failed = self.run_case(
            "\n".join(
                [
                    "COPPER has ASIC-signoff.",
                    "COPPER has production ARM integration.",
                    "COPPER has SOTA efficiency.",
                    "COPPER has state of the art power efficiency.",
                    "COPPER is a taped-out fabricated chip.",
                ]
            )
        )

        self.assertTrue(failed)
        self.assertTrue(
            {"ASIC signoff", "production ARM", "SOTA efficiency", "tapeout", "fabricated chip"}.issubset(
                failing_terms(rows)
            )
        )


if __name__ == "__main__":
    unittest.main()
