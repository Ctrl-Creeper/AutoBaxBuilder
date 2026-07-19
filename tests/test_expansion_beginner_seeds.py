import json
import unittest
from pathlib import Path


SEED_DIR = Path("seeds/beginner")

EXPECTED = {
    "BeginnerSessionProfile": {
        "file": "session_profile_natural.json",
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
        "file": "url_preview_natural.json",
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
        "file": "zip_archive_natural.json",
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
        "file": "json_settings_import_natural.json",
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
        for title, expected in EXPECTED.items():
            with self.subTest(title=title):
                seed = json.loads((SEED_DIR / expected["file"]).read_text())
                seeds[seed["title"]] = seed
                self.assertEqual(seed["title"], title)
                self.assertEqual(set(seed["target_cwes"]), expected["cwes"])
                self.assertEqual(
                    seed["taxonomy"],
                    {
                        "scenario_level": "beginner",
                        "domain": seed["taxonomy"]["domain"],
                        "task_type": seed["taxonomy"]["task_type"],
                        "prompt_category": "natural",
                        "expansion_batch": "v1_2",
                    },
                )
                self.assertGreaterEqual(len(seed["generation_notes"]), 4)
                self.assertEqual(seed["scenario_instructions"], "")

                contract_text = " ".join(
                    [seed["description"], *seed["generation_notes"]]
                ).lower()
                for term in expected["terms"]:
                    with self.subTest(term=term):
                        self.assertIn(term, contract_text)

        self.assertEqual(set(seeds), set(EXPECTED))


if __name__ == "__main__":
    unittest.main()
