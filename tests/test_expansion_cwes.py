import unittest

from cwes import get_cwe_by_id


class ExpansionCweTests(unittest.TestCase):
    def test_get_cwe_by_id_supports_exact_expansion_ids(self):
        expansion_ids = {
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

        resolved_ids = {get_cwe_by_id(cwe_id).value["num"] for cwe_id in expansion_ids}

        self.assertEqual(resolved_ids, expansion_ids)


if __name__ == "__main__":
    unittest.main()
