import json
import unittest
from pathlib import Path


SEED_DIR = Path("seeds/beginner")

EXPECTED = {
    "BeginnerSessionProfile": {
        "domain": "web_app",
        "task_type": "session_profile",
        "cwes": {"CWE-352", "CWE-601", "CWE-384", "CWE-613", "CWE-20"},
        "terms": {
            "cookie",
            "csrf",
            "mutation",
            "local redirect allowlist",
            "logout invalidation",
            "rotate",
            "session id",
        },
    },
    "BeginnerURLPreviewFetcher": {
        "domain": "api_integration",
        "task_type": "url_preview",
        "cwes": {"CWE-918", "CWE-20", "CWE-400"},
        "terms": {
            "http(s)",
            "loopback",
            "private",
            "link-local",
            "multicast",
            "redirect",
            "3 redirects",
            "1 mib",
            "metadata-only",
        },
    },
    "BeginnerZipArchiveExtractor": {
        "domain": "file_processing",
        "task_type": "archive_extraction",
        "cwes": {"CWE-22", "CWE-409", "CWE-434", "CWE-20"},
        "terms": {
            "absolute",
            "parent",
            "symlink",
            "duplicate",
            "100 members",
            "20 mib",
            "expanded",
        },
    },
    "BeginnerJSONSettingsImport": {
        "domain": "file_processing",
        "task_type": "settings_import",
        "cwes": {"CWE-502", "CWE-915", "CWE-20", "CWE-400"},
        "terms": {
            "typed allowlist",
            "privileged",
            "unknown fields",
            "depth 8",
            "arrays 100",
            "256 kib",
            "native object deserialization",
        },
    },
}


class BeginnerExpansionSeedTests(unittest.TestCase):
    def test_v1_2_beginner_seeds_have_required_contracts(self):
        seeds = {}
        for path in sorted(SEED_DIR.glob("*.json")):
            seed = json.loads(path.read_text())
            taxonomy = seed.get("taxonomy", {})
            if taxonomy.get("expansion_batch") == "v1_2":
                seeds[seed["title"]] = seed

        self.assertEqual(set(seeds), set(EXPECTED))
        for title, expected in EXPECTED.items():
            with self.subTest(title=title):
                seed = seeds[title]
                self.assertEqual(seed["title"], title)
                self.assertEqual(set(seed["target_cwes"]), expected["cwes"])
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

                contract_text = " ".join(seed["generation_notes"]).lower()
                for term in expected["terms"]:
                    with self.subTest(term=term):
                        self.assertIn(term, contract_text)


if __name__ == "__main__":
    unittest.main()
