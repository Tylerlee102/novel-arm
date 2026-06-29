from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))

import build_copper_public_artifact_manifest as manifest  # noqa: E402


class PublicArtifactManifestTests(unittest.TestCase):
    def test_missing_optional_external_evidence_uses_pinned_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            research = root / "research"
            results = research / "results"
            research.mkdir(parents=True)
            results.mkdir(parents=True)
            optional = results / "large_optional.saif"
            seed = research / "seed.md"
            seed.write_text("seed\n", encoding="utf-8")

            old_values = {
                "ROOT": manifest.ROOT,
                "RESEARCH": manifest.RESEARCH,
                "RESULTS": manifest.RESULTS,
                "SEED_DOCS": manifest.SEED_DOCS,
                "EXPLICIT_EVIDENCE": manifest.EXPLICIT_EVIDENCE,
                "SELF_OUTPUTS": manifest.SELF_OUTPUTS,
                "SELF_OUTPUT_DIRS": manifest.SELF_OUTPUT_DIRS,
                "OPTIONAL_EXTERNAL_EVIDENCE": manifest.OPTIONAL_EXTERNAL_EVIDENCE,
            }
            try:
                manifest.ROOT = root
                manifest.RESEARCH = research
                manifest.RESULTS = results
                manifest.SEED_DOCS = [seed]
                manifest.EXPLICIT_EVIDENCE = [optional]
                manifest.SELF_OUTPUTS = set()
                manifest.SELF_OUTPUT_DIRS = set()
                manifest.OPTIONAL_EXTERNAL_EVIDENCE = {
                    optional.resolve(): {
                        "artifact_class": "heavy_raw_evidence",
                        "size": 123,
                        "sha256": "a" * 64,
                        "package_recommendation": "external-store-with-hash",
                    }
                }

                entries, missing, _skipped = manifest.collect_entries()
            finally:
                for key, value in old_values.items():
                    setattr(manifest, key, value)

        optional_entries = [entry for entry in entries if entry.rel == "research/results/large_optional.saif"]
        self.assertFalse(missing)
        self.assertEqual(1, len(optional_entries))
        self.assertEqual("external-store-with-hash", optional_entries[0].package_recommendation)
        self.assertEqual("a" * 64, optional_entries[0].sha256)

    def test_missing_generated_package_directory_is_not_a_manifest_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            research = root / "research"
            results = research / "results"
            research.mkdir(parents=True)
            results.mkdir(parents=True)
            package_dir = results / "copper_public_artifact_package_20260620"
            seed = research / "seed.md"
            seed.write_text("`research/results/copper_public_artifact_package_20260620`\n", encoding="utf-8")

            old_values = {
                "ROOT": manifest.ROOT,
                "RESEARCH": manifest.RESEARCH,
                "RESULTS": manifest.RESULTS,
                "SEED_DOCS": manifest.SEED_DOCS,
                "EXPLICIT_EVIDENCE": manifest.EXPLICIT_EVIDENCE,
                "SELF_OUTPUTS": manifest.SELF_OUTPUTS,
                "SELF_OUTPUT_DIRS": manifest.SELF_OUTPUT_DIRS,
                "OPTIONAL_EXTERNAL_EVIDENCE": manifest.OPTIONAL_EXTERNAL_EVIDENCE,
            }
            try:
                manifest.ROOT = root
                manifest.RESEARCH = research
                manifest.RESULTS = results
                manifest.SEED_DOCS = [seed]
                manifest.EXPLICIT_EVIDENCE = []
                manifest.SELF_OUTPUTS = set()
                manifest.SELF_OUTPUT_DIRS = {package_dir.resolve()}
                manifest.OPTIONAL_EXTERNAL_EVIDENCE = {}

                entries, missing, _skipped = manifest.collect_entries()
            finally:
                for key, value in old_values.items():
                    setattr(manifest, key, value)

        self.assertFalse(missing)
        self.assertFalse(any(entry.rel == "research/results/copper_public_artifact_package_20260620" for entry in entries))


if __name__ == "__main__":
    unittest.main()
