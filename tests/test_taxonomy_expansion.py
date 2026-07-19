import json
import shutil
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch


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
V1_2_EMPTY_COUNT_ERRORS = [
    "batch 'v1_2' must contain exactly 8 seeds; found 1",
    "batch 'v1_2' must contain 4 beginner seeds; found 0",
    "batch 'v1_2' must contain 4 complex seeds; found 0",
    "batch 'v1_2' must contain 8 natural seeds; found 0",
]


class TaxonomyExpansionTests(unittest.TestCase):
    def assert_discovery_error(self, seed, expected_error):
        self.assertEqual(len(seed), 1)
        sentinel = next(iter(seed))
        self.assertIs(type(sentinel), object)
        self.assertEqual(seed[sentinel], [expected_error])

    def empty_seeds_dir(self, temporary_directory):
        seeds_dir = Path(temporary_directory) / "seeds"
        for level in ("beginner", "complex"):
            (seeds_dir / level).mkdir(parents=True)
        return seeds_dir

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

        self.assertEqual(
            [path.parent.name for path, _ in seeds],
            sorted(path.parent.name for path, _ in seeds),
        )
        self.assertEqual(report["batch"], BATCH)
        self.assertEqual(report["seed_count"], 8)
        self.assertEqual(report["level_counts"], {"beginner": 4, "complex": 4})
        self.assertEqual(report["prompt_counts"], {"natural": 8})
        self.assertEqual(report["titles"], EXPECTED_TITLES)
        self.assertEqual(report["cwes"], EXPECTED_CWES)
        self.assertTrue(NEW_CWES.issubset(report["cwes"]))
        self.assertEqual(report["errors"], [])

    def test_discovery_reports_invalid_json_without_throwing(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.empty_seeds_dir(temporary_directory)
            path = seeds_dir / "beginner" / "broken.json"
            path.write_text("{", encoding="utf-8")
            error = (
                f"{path}: invalid JSON at line 1 column 2: "
                "Expecting property name enclosed in double quotes"
            )

            seeds = discover_expansion_seeds(seeds_dir, BATCH)
            report = validate_expansion_seeds(seeds, BATCH)

        self.assertEqual([seed_path for seed_path, _ in seeds], [path])
        self.assert_discovery_error(seeds[0][1], error)
        self.assertEqual(report["errors"], sorted([error] + V1_2_EMPTY_COUNT_ERRORS))

    def test_discovery_reports_invalid_utf8_without_throwing(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.empty_seeds_dir(temporary_directory)
            path = seeds_dir / "beginner" / "invalid_utf8.json"
            path.write_bytes(b"\xff")
            error = f"{path}: seed file is not valid UTF-8"

            seeds = discover_expansion_seeds(seeds_dir, BATCH)
            report = validate_expansion_seeds(seeds, BATCH)

        self.assertEqual([seed_path for seed_path, _ in seeds], [path])
        self.assert_discovery_error(seeds[0][1], error)
        self.assertIn(error, report["errors"])

    def test_discovery_reports_json_decoder_recursion_without_throwing(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.empty_seeds_dir(temporary_directory)
            path = seeds_dir / "complex" / "too_deep.json"
            path.write_text("[" * 2000 + "]" * 2000, encoding="utf-8")
            error = f"{path}: JSON nesting exceeds decoder recursion limit"

            seeds = discover_expansion_seeds(seeds_dir, BATCH)
            report = validate_expansion_seeds(seeds, BATCH)

        self.assertEqual([seed_path for seed_path, _ in seeds], [path])
        self.assert_discovery_error(seeds[0][1], error)
        self.assertIn(error, report["errors"])

    def test_discovery_reports_integer_over_digit_limit_without_throwing(self):
        get_digit_limit = getattr(sys, "get_int_max_str_digits", None)
        if get_digit_limit is None:
            self.skipTest("integer digit limit API unavailable")
        digit_limit = get_digit_limit()
        if digit_limit == 0:
            self.skipTest("integer digit limit is disabled")

        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.empty_seeds_dir(temporary_directory)
            path = seeds_dir / "beginner" / "oversized_integer.json"
            oversized_integer = "1" * (digit_limit + 1)
            path.write_text(
                '{"taxonomy":{"expansion_batch":"v1_2"},"value":'
                + oversized_integer
                + "}",
                encoding="utf-8",
            )
            error = f"{path}: JSON value exceeds parser limits"

            seeds = discover_expansion_seeds(seeds_dir, BATCH)
            report = validate_expansion_seeds(seeds, BATCH)

        self.assertEqual([seed_path for seed_path, _ in seeds], [path])
        self.assert_discovery_error(seeds[0][1], error)
        self.assertIn(error, report["errors"])

    def test_discovery_reports_array_and_null_roots(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.empty_seeds_dir(temporary_directory)
            array_path = seeds_dir / "beginner" / "array.json"
            null_path = seeds_dir / "complex" / "null.json"
            array_path.write_text("[]", encoding="utf-8")
            null_path.write_text("null", encoding="utf-8")
            root_errors = [
                f"{array_path}: JSON root must be an object; found array",
                f"{null_path}: JSON root must be an object; found null",
            ]

            seeds = discover_expansion_seeds(seeds_dir, BATCH)
            report = validate_expansion_seeds(seeds, BATCH)

        self.assertEqual([path for path, _ in seeds], [array_path, null_path])
        for (_, seed), error in zip(seeds, root_errors):
            self.assert_discovery_error(seed, error)
        self.assertEqual(
            report["errors"],
            sorted(
                root_errors
                + [
                    "batch 'v1_2' must contain exactly 8 seeds; found 2",
                    "batch 'v1_2' must contain 4 beginner seeds; found 0",
                    "batch 'v1_2' must contain 4 complex seeds; found 0",
                    "batch 'v1_2' must contain 8 natural seeds; found 0",
                ]
            ),
        )

    def test_discovery_rejects_symlink_that_escapes_seeds_dir(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.empty_seeds_dir(temporary_directory)
            external_path = Path(temporary_directory) / "external.json"
            external_path.write_text("{", encoding="utf-8")
            link_path = seeds_dir / "beginner" / "escape.json"
            try:
                link_path.symlink_to(external_path)
            except (NotImplementedError, OSError) as error:
                self.skipTest(f"symlinks unavailable: {error}")
            discovery_error = f"{link_path}: symlink target resolves outside seeds_dir"

            with patch.object(
                Path,
                "read_text",
                side_effect=AssertionError("escaping symlink content was read"),
            ):
                seeds = discover_expansion_seeds(seeds_dir, BATCH)
            report = validate_expansion_seeds(seeds, BATCH)

        self.assertEqual([path for path, _ in seeds], [link_path])
        self.assert_discovery_error(seeds[0][1], discovery_error)
        self.assertIn(discovery_error, report["errors"])

    def test_discovery_reports_symlink_loop_as_path_safety_error(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.empty_seeds_dir(temporary_directory)
            loop_path = seeds_dir / "complex" / "loop.json"
            try:
                loop_path.symlink_to(loop_path.name)
            except (NotImplementedError, OSError) as error:
                self.skipTest(f"symlinks unavailable: {error}")
            discovery_error = f"{loop_path}: path safety check failed during resolution"

            seeds = discover_expansion_seeds(seeds_dir, BATCH)
            report = validate_expansion_seeds(seeds, BATCH)

        self.assertEqual([path for path, _ in seeds], [loop_path])
        self.assert_discovery_error(seeds[0][1], discovery_error)
        self.assertIn(discovery_error, report["errors"])

    def test_string_discovery_errors_field_does_not_bypass_validation(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.empty_seeds_dir(temporary_directory)
            path = seeds_dir / "beginner" / "ordinary_field.json"
            self.write_seed(
                path,
                {
                    "taxonomy": {"expansion_batch": BATCH},
                    "__discovery_errors__": [],
                },
            )

            seeds = discover_expansion_seeds(seeds_dir, BATCH)
            report = validate_expansion_seeds(seeds, BATCH)

        self.assertEqual(seeds[0][1]["__discovery_errors__"], [])
        self.assertIn(f"{path}: missing required field 'title'", report["errors"])

    def test_discovery_sorts_by_full_relative_posix_path(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.empty_seeds_dir(temporary_directory)
            relative_paths = [
                Path("complex/z.json"),
                Path("beginner/z.json"),
                Path("complex/a.json"),
                Path("beginner/a.json"),
            ]
            for relative_path in relative_paths:
                self.write_seed(
                    seeds_dir / relative_path,
                    {"taxonomy": {"expansion_batch": BATCH}},
                )

            seeds = discover_expansion_seeds(seeds_dir, BATCH)

        self.assertEqual(
            [path.relative_to(seeds_dir).as_posix() for path, _ in seeds],
            [
                "beginner/a.json",
                "beginner/z.json",
                "complex/a.json",
                "complex/z.json",
            ],
        )

    def test_duplicate_title_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.copied_seeds_dir(temporary_directory)
            path, seed = self.read_seed(
                seeds_dir, "complex", "account_recovery_natural.json"
            )
            seed["title"] = "ComplexInventoryCheckout"
            self.write_seed(path, seed)

            report = validate_expansion_seeds(
                discover_expansion_seeds(seeds_dir, BATCH), BATCH
            )

        self.assertIn("duplicate title 'ComplexInventoryCheckout'", report["errors"])

    def test_title_must_be_a_python_identifier(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.copied_seeds_dir(temporary_directory)
            path, seed = self.read_seed(
                seeds_dir, "beginner", "json_settings_import_natural.json"
            )
            seed["title"] = "unsafe/title"
            self.write_seed(path, seed)
            report = validate_expansion_seeds(
                discover_expansion_seeds(seeds_dir, BATCH), BATCH
            )

        self.assertIn(
            f"{path}: title must match ^[A-Za-z_][A-Za-z0-9_]*$", report["errors"]
        )

    def test_duplicate_description_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.copied_seeds_dir(temporary_directory)
            path, seed = self.read_seed(
                seeds_dir, "complex", "account_recovery_natural.json"
            )
            _, source_seed = self.read_seed(
                seeds_dir, "complex", "inventory_checkout_natural.json"
            )
            seed["description"] = source_seed["description"]
            self.write_seed(path, seed)

            report = validate_expansion_seeds(
                discover_expansion_seeds(seeds_dir, BATCH), BATCH
            )

        self.assertTrue(
            any(
                error.startswith("duplicate description ") for error in report["errors"]
            )
        )

    def test_level_mismatch_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.copied_seeds_dir(temporary_directory)
            path, seed = self.read_seed(
                seeds_dir, "beginner", "json_settings_import_natural.json"
            )
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
            path, seed = self.read_seed(
                seeds_dir, "beginner", "json_settings_import_natural.json"
            )
            seed["target_cwes"] = ["CWE-000", "CWE-999999"]
            self.write_seed(path, seed)

            report = validate_expansion_seeds(
                discover_expansion_seeds(seeds_dir, BATCH), BATCH
            )

        self.assertIn(
            f"{path}: target_cwes contains malformed CWE 'CWE-000'", report["errors"]
        )
        self.assertIn(
            f"{path}: target_cwes contains unsupported CWE 'CWE-999999'",
            report["errors"],
        )

    def test_missing_oracle_contract_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.copied_seeds_dir(temporary_directory)
            path, seed = self.read_seed(
                seeds_dir, "beginner", "json_settings_import_natural.json"
            )
            del seed["oracle_contract"]
            self.write_seed(path, seed)

            report = validate_expansion_seeds(
                discover_expansion_seeds(seeds_dir, BATCH), BATCH
            )

        self.assertIn(
            f"{path}: missing required field 'oracle_contract'", report["errors"]
        )

    def test_wrong_prompt_category_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            seeds_dir = self.copied_seeds_dir(temporary_directory)
            path, seed = self.read_seed(
                seeds_dir, "beginner", "json_settings_import_natural.json"
            )
            seed["taxonomy"]["prompt_category"] = "expert"
            self.write_seed(path, seed)

            report = validate_expansion_seeds(
                discover_expansion_seeds(seeds_dir, BATCH), BATCH
            )

        self.assertIn(
            f"{path}: taxonomy.prompt_category must be 'natural'", report["errors"]
        )

    def test_wrong_v1_2_count_is_reported(self):
        seeds = discover_expansion_seeds(SEEDS_DIR, BATCH)[:-1]
        report = validate_expansion_seeds(seeds, BATCH)

        self.assertIn(
            "batch 'v1_2' must contain exactly 8 seeds; found 7", report["errors"]
        )
        self.assertIn(
            "batch 'v1_2' must contain 4 complex seeds; found 3", report["errors"]
        )
        self.assertIn(
            "batch 'v1_2' must contain 8 natural seeds; found 7", report["errors"]
        )

    def test_duplicate_seed_path_is_reported(self):
        seeds = discover_expansion_seeds(SEEDS_DIR, BATCH)
        duplicated = seeds + [(seeds[0][0], deepcopy(seeds[0][1]))]

        report = validate_expansion_seeds(duplicated, BATCH)

        self.assertIn(f"duplicate seed path '{seeds[0][0]}'", report["errors"])

    def test_cyclic_oracle_contract_is_rejected_without_recursion_error(self):
        seeds = discover_expansion_seeds(SEEDS_DIR, BATCH)
        path, seed = seeds[0]
        cycle = []
        cycle.append(cycle)
        seed["oracle_contract"] = {"cycle": cycle}

        report = validate_expansion_seeds(seeds, BATCH)

        self.assertIn(
            f"{path}: oracle_contract must contain only JSON-compatible values",
            report["errors"],
        )

    def test_oracle_contract_over_depth_64_is_rejected(self):
        seeds = discover_expansion_seeds(SEEDS_DIR, BATCH)
        path, seed = seeds[0]
        contract = {}
        cursor = contract
        for _ in range(65):
            child = {}
            cursor["next"] = child
            cursor = child
        seed["oracle_contract"] = contract

        report = validate_expansion_seeds(seeds, BATCH)

        self.assertIn(
            f"{path}: oracle_contract must contain only JSON-compatible values",
            report["errors"],
        )

    def test_oracle_contract_at_depth_64_is_accepted(self):
        seeds = discover_expansion_seeds(SEEDS_DIR, BATCH)
        path, seed = seeds[0]
        contract = {}
        cursor = contract
        for _ in range(64):
            child = {}
            cursor["next"] = child
            cursor = child
        seed["oracle_contract"] = contract

        report = validate_expansion_seeds(seeds, BATCH)

        self.assertNotIn(
            f"{path}: oracle_contract must contain only JSON-compatible values",
            report["errors"],
        )

    def test_oracle_contract_accepts_all_supported_json_values(self):
        seeds = discover_expansion_seeds(SEEDS_DIR, BATCH)
        path, seed = seeds[0]
        seed["oracle_contract"] = {
            "null": None,
            "bool": True,
            "string": "value",
            "integer": 1,
            "float": 1.5,
            "list": [None, False, "value", 2, 2.5],
            "object": {"key": "value"},
        }

        report = validate_expansion_seeds(seeds, BATCH)

        self.assertNotIn(
            f"{path}: oracle_contract must contain only JSON-compatible values",
            report["errors"],
        )

    def test_oracle_contract_rejects_nonfinite_float_and_non_string_key(self):
        invalid_contracts = (
            {"value": float("nan")},
            {"value": float("inf")},
            {"value": float("-inf")},
            {1: "value"},
        )
        for invalid_contract in invalid_contracts:
            with self.subTest(invalid_contract=invalid_contract):
                seeds = discover_expansion_seeds(SEEDS_DIR, BATCH)
                path, seed = seeds[0]
                seed["oracle_contract"] = invalid_contract

                report = validate_expansion_seeds(seeds, BATCH)

                self.assertIn(
                    f"{path}: oracle_contract must contain only JSON-compatible values",
                    report["errors"],
                )


if __name__ == "__main__":
    unittest.main()
