import json
import shutil
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from taxonomy_expansion import discover_expansion_seeds, validate_expansion_seeds


SEEDS_DIR = ROOT / "seeds"
BATCH = "v1_2"
EXPECTED_TITLES = [
    "BeginnerJSONSettingsImport",
    "BeginnerSessionProfile",
    "BeginnerURLPreviewFetcher",
    "BeginnerZipArchiveExtractor",
    "ComplexAccountRecovery",
    "ComplexInventoryCheckout",
    "ComplexMultiTenantDocumentExport",
    "ComplexSignedWebhookProcessor",
]
EXPECTED_CWES = [
    "CWE-20",
    "CWE-22",
    "CWE-89",
    "CWE-204",
    "CWE-284",
    "CWE-294",
    "CWE-345",
    "CWE-352",
    "CWE-362",
    "CWE-384",
    "CWE-400",
    "CWE-409",
    "CWE-434",
    "CWE-502",
    "CWE-522",
    "CWE-601",
    "CWE-613",
    "CWE-639",
    "CWE-640",
    "CWE-863",
    "CWE-915",
    "CWE-918",
]
NEW_CWES = {
    "CWE-204",
    "CWE-294",
    "CWE-345",
    "CWE-352",
    "CWE-362",
    "CWE-384",
    "CWE-409",
    "CWE-502",
    "CWE-601",
    "CWE-613",
    "CWE-639",
    "CWE-640",
    "CWE-915",
    "CWE-918",
}


class TaxonomyExpansionTests(unittest.TestCase):
    def copied_seeds_dir(self, temporary_directory):
        destination = Path(temporary_directory) / "seeds"
        shutil.copytree(SEEDS_DIR, destination)
        return destination

    def read_seed(self, seeds_dir, level, filename):
        path = seeds_dir / level / filename
        return path, json.loads(path.read_text())

    def write_seed(self, path, seed):
        path.write_text(json.dumps(seed, indent=2) + "\n")

    def test_repository_batch_report_is_complete_and_valid(self):
        seeds = discover_expansion_seeds(SEEDS_DIR, BATCH)
        report = validate_expansion_seeds(seeds, BATCH)

        self.assertEqual([path.parent.name for path, _ in seeds], sorted(path.parent.name for path, _ in seeds))
        self.assertEqual(report["batch"], BATCH)
        self.assertEqual(report["seed_count"], 8)
        self.assertEqual(report["level_counts"], {"beginner": 4, "complex": 4})
        self.assertEqual(report["prompt_counts"], {"natural": 8})
        self.assertEqual(report["titles"], EXPECTED_TITLES)
        self.assertEqual(report["cwes"], EXPECTED_CWES)
        self.assertTrue(NEW_CWES.issubset(report["cwes"]))
        self.assertEqual(report["errors"], [])

    def test_duplicate_title_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.copied_seeds_dir(temporary_directory)
            path, seed = self.read_seed(seeds_dir, "complex", "account_recovery_natural.json")
            seed["title"] = "ComplexInventoryCheckout"
            self.write_seed(path, seed)

            report = validate_expansion_seeds(
                discover_expansion_seeds(seeds_dir, BATCH), BATCH
            )

        self.assertIn("duplicate title 'ComplexInventoryCheckout'", report["errors"])

    def test_duplicate_description_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.copied_seeds_dir(temporary_directory)
            path, seed = self.read_seed(seeds_dir, "complex", "account_recovery_natural.json")
            _, source_seed = self.read_seed(
                seeds_dir, "complex", "inventory_checkout_natural.json"
            )
            seed["description"] = source_seed["description"]
            self.write_seed(path, seed)

            report = validate_expansion_seeds(
                discover_expansion_seeds(seeds_dir, BATCH), BATCH
            )

        self.assertTrue(
            any(error.startswith("duplicate description ") for error in report["errors"])
        )

    def test_level_mismatch_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.copied_seeds_dir(temporary_directory)
            path, seed = self.read_seed(seeds_dir, "beginner", "json_settings_import_natural.json")
            seed["taxonomy"]["scenario_level"] = "complex"
            self.write_seed(path, seed)

            report = validate_expansion_seeds(
                discover_expansion_seeds(seeds_dir, BATCH), BATCH
            )

        self.assertIn(
            f"{path}: taxonomy.scenario_level 'complex' does not match parent level 'beginner'",
            report["errors"],
        )

    def test_unsupported_and_malformed_cwes_are_reported(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.copied_seeds_dir(temporary_directory)
            path, seed = self.read_seed(seeds_dir, "beginner", "json_settings_import_natural.json")
            seed["target_cwes"] = ["CWE-000", "CWE-999999"]
            self.write_seed(path, seed)

            report = validate_expansion_seeds(
                discover_expansion_seeds(seeds_dir, BATCH), BATCH
            )

        self.assertIn(f"{path}: target_cwes contains malformed CWE 'CWE-000'", report["errors"])
        self.assertIn(f"{path}: target_cwes contains unsupported CWE 'CWE-999999'", report["errors"])

    def test_missing_oracle_contract_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.copied_seeds_dir(temporary_directory)
            path, seed = self.read_seed(seeds_dir, "beginner", "json_settings_import_natural.json")
            del seed["oracle_contract"]
            self.write_seed(path, seed)

            report = validate_expansion_seeds(
                discover_expansion_seeds(seeds_dir, BATCH), BATCH
            )

        self.assertIn(f"{path}: missing required field 'oracle_contract'", report["errors"])

    def test_wrong_prompt_category_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.copied_seeds_dir(temporary_directory)
            path, seed = self.read_seed(seeds_dir, "beginner", "json_settings_import_natural.json")
            seed["taxonomy"]["prompt_category"] = "expert"
            self.write_seed(path, seed)

            report = validate_expansion_seeds(
                discover_expansion_seeds(seeds_dir, BATCH), BATCH
            )

        self.assertIn(f"{path}: taxonomy.prompt_category must be 'natural'", report["errors"])

    def test_wrong_v1_2_count_is_reported(self):
        seeds = discover_expansion_seeds(SEEDS_DIR, BATCH)[:-1]
        report = validate_expansion_seeds(seeds, BATCH)

        self.assertIn("batch 'v1_2' must contain exactly 8 seeds; found 7", report["errors"])
        self.assertIn("batch 'v1_2' must contain 4 complex seeds; found 3", report["errors"])
        self.assertIn("batch 'v1_2' must contain 8 natural seeds; found 7", report["errors"])

    def test_duplicate_seed_path_is_reported(self):
        seeds = discover_expansion_seeds(SEEDS_DIR, BATCH)
        duplicated = seeds + [(seeds[0][0], deepcopy(seeds[0][1]))]

        report = validate_expansion_seeds(duplicated, BATCH)

        self.assertIn(f"duplicate seed path '{seeds[0][0]}'", report["errors"])


if __name__ == "__main__":
    unittest.main()
