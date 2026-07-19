import sys
import unittest
from types import ModuleType
from unittest.mock import patch

from cwes import get_cwe_by_id


models = ModuleType("models")
models.get_model = lambda *args, **kwargs: object()
with patch.dict(sys.modules, {"models": models}):
    from agent.config import MITRE_TOP_25


EXPANSION_IDS = {
    204,
    294,
    345,
    352,
    362,
    384,
    409,
    502,
    601,
    613,
    639,
    640,
    915,
    918,
}


class ExpansionCweTests(unittest.TestCase):
    def test_get_cwe_by_id_supports_exact_expansion_ids(self):
        resolved_ids = {
            get_cwe_by_id(cwe_id).value["num"] for cwe_id in EXPANSION_IDS
        }

        self.assertEqual(resolved_ids, EXPANSION_IDS)

    def test_expansion_ids_are_configured(self):
        self.assertTrue(EXPANSION_IDS.issubset(MITRE_TOP_25))

    def test_expansion_cwes_have_descriptions(self):
        for cwe_id in EXPANSION_IDS:
            with self.subTest(cwe_id=cwe_id):
                self.assertTrue(get_cwe_by_id(cwe_id).value["desc"].strip())

    def test_defining_description_scope_is_preserved(self):
        descriptions = {
            cwe_id: get_cwe_by_id(cwe_id).value["desc"].lower()
            for cwe_id in (204, 639, 915)
        }

        self.assertIn("internal state information", descriptions[204])
        self.assertIn("another user's data or record", descriptions[639])
        self.assertIn("multiple attributes, properties, or fields", descriptions[915])


if __name__ == "__main__":
    unittest.main()
