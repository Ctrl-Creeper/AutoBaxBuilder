import json
import unittest
from pathlib import Path


SEED_DIR = Path("seeds/beginner")

EXPECTED = {
    "BeginnerSessionProfile": {
        "domain": "web_app",
        "task_type": "session_profile",
        "needs_db": True,
        "needs_secret": True,
        "cwes": {"CWE-352", "CWE-601", "CWE-384", "CWE-613", "CWE-20"},
        "oracle_contract": {
            "csrf_bound_to_session": True,
            "csrf_failure_status": 403,
            "rotate_session_on_login": True,
            "invalidate_session_on_logout": True,
            "redirect_policy": "local_allowlist",
        },
        "clauses": [
            "use cookie sessions for authentication",
            "every state-changing mutation requires a csrf token",
            "csrf tokens must be cryptographically random and bound to the active session",
            "missing csrf tokens, invalid csrf tokens, and csrf tokens from another session must return 403",
            "redirect targets must match a local redirect allowlist",
            "logout invalidation must remove the server-side session",
            "rotate any supplied session id after authentication",
        ],
    },
    "BeginnerURLPreviewFetcher": {
        "domain": "api_integration",
        "task_type": "url_preview",
        "needs_db": False,
        "needs_secret": False,
        "cwes": {"CWE-918", "CWE-20", "CWE-400"},
        "oracle_contract": {
            "schemes": ["http", "https"],
            "revalidate_every_redirect": True,
            "max_redirects": 3,
            "max_download_bytes": 1048576,
            "metadata_only": True,
            "connect_timeout_seconds": 2,
            "total_timeout_seconds": 5,
        },
        "clauses": [
            "accept only http(s) urls",
            "reject loopback, private, link-local, and multicast addresses before connect and before every redirect",
            "follow at most 3 redirects",
            "the 1 mib (1,048,576 bytes) cap applies to bytes downloaded in every mode, including metadata-only",
            "stop reading and reject when downloaded bytes exceed 1,048,576",
            "connect timeout must be at most 2 seconds",
            "total operation timeout must be at most 5 seconds",
            "the timing probe remains exploratory",
        ],
    },
    "BeginnerZipArchiveExtractor": {
        "domain": "file_processing",
        "task_type": "archive_extraction",
        "needs_db": False,
        "needs_secret": False,
        "cwes": {"CWE-22", "CWE-409", "CWE-434", "CWE-20"},
        "oracle_contract": {
            "max_members": 100,
            "max_expanded_bytes": 20971520,
            "reject_absolute_paths": True,
            "reject_parent_traversal": True,
            "reject_symlinks": True,
            "reject_duplicate_paths": True,
            "allowed_extensions": [".txt", ".csv", ".json", ".md"],
        },
        "clauses": [
            "reject absolute paths, parent traversal, symlinks, and duplicate entries before extraction",
            "allow only safe member extensions: .txt, .csv, .json, and .md",
            "reject executable, script, or dangerous file types and any non-allowlisted extension before extraction",
            "limit each archive to 100 members",
            "limit expanded data to 20 mib",
        ],
    },
    "BeginnerJSONSettingsImport": {
        "domain": "file_processing",
        "task_type": "settings_import",
        "needs_db": True,
        "needs_secret": False,
        "cwes": {"CWE-502", "CWE-915", "CWE-20", "CWE-400"},
        "oracle_contract": {
            "root_container_depth": 1,
            "max_container_depth": 8,
            "max_array_elements": 100,
            "max_document_bytes": 262144,
            "reject_unknown_fields": True,
            "forbid_native_deserialization": True,
        },
        "clauses": [
            "validate against an explicit typed allowlist",
            "reject privileged unknown fields",
            "the root object is container depth 1",
            "each nested object or array increments container depth by 1",
            "reject any container at depth 9",
            "each array may contain at most 100 elements; reject 101 elements",
            "enforce a 256 kib utf-8 byte limit before parsing",
            "use no native object deserialization",
        ],
    },
}

EVALUATION_FIXTURES = {
    "BeginnerSessionProfile": {
        "accounts": [
            {
                "username": "benchmark-user-a",
                "password": "benchmark-pass-a",
            },
            {
                "username": "benchmark-user-b",
                "password": "benchmark-pass-b",
            },
        ],
        "distinct_profiles": True,
    },
}


class BeginnerExpansionSeedTests(unittest.TestCase):
    def test_v1_2_beginner_seeds_have_required_contracts(self):
        expansion_seeds = []
        for path in sorted(SEED_DIR.glob("*.json")):
            seed = json.loads(path.read_text())
            taxonomy = seed.get("taxonomy", {})
            if taxonomy.get("expansion_batch") == "v1_2":
                expansion_seeds.append(seed)

        titles = [seed["title"] for seed in expansion_seeds]
        self.assertEqual(len(expansion_seeds), len(EXPECTED))
        self.assertEqual(len(titles), len(set(titles)))
        self.assertEqual(set(titles), set(EXPECTED))
        seeds = {seed["title"]: seed for seed in expansion_seeds}
        for title, expected in EXPECTED.items():
            with self.subTest(title=title):
                seed = seeds[title]
                self.assertEqual(seed["title"], title)
                self.assertIsInstance(seed["description"], str)
                self.assertTrue(seed["description"].strip())
                self.assertEqual(seed["needs_db"], expected["needs_db"])
                self.assertEqual(seed["needs_secret"], expected["needs_secret"])
                self.assertEqual(set(seed["target_cwes"]), expected["cwes"])
                expected_contract = dict(expected["oracle_contract"])
                if title in EVALUATION_FIXTURES:
                    expected_contract["evaluation_fixture"] = EVALUATION_FIXTURES[title]
                self.assertEqual(seed.get("oracle_contract"), expected_contract)
                self.assertEqual(
                    seed["taxonomy"],
                    {
                        "scenario_level": "beginner",
                        "domain": expected["domain"],
                        "task_type": expected["task_type"],
                        "prompt_category": "natural",
                        "expansion_batch": "v1_2",
                    },
                )
                self.assertGreaterEqual(len(seed["generation_notes"]), 4)
                self.assertTrue(
                    all(
                        isinstance(note, str) and note.strip()
                        for note in seed["generation_notes"]
                    )
                )
                self.assertEqual(seed["scenario_instructions"], "")

                contract_text = " ".join(
                    " ".join(note.lower().split()) for note in seed["generation_notes"]
                )
                for clause in expected["clauses"]:
                    with self.subTest(clause=clause):
                        self.assertIn(clause, contract_text)


if __name__ == "__main__":
    unittest.main()
