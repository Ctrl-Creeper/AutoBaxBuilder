import json
import py_compile
import tempfile
import unittest
from pathlib import Path

from scripts.generate_order_management_v1_2 import write_order_management_v1_2


class OrderManagementV12Tests(unittest.TestCase):
    def test_seed_declares_identity_and_authorization_targets(self):
        seed = json.loads(
            Path("seeds/complex/order_management_authorized_v1_2.json").read_text()
        )

        self.assertTrue(seed["needs_secret"])
        self.assertEqual(seed["target_cwes"], ["CWE-284", "CWE-863", "CWE-20"])
        self.assertIn("owner", seed["description"].lower())

    def test_generated_scenario_has_two_user_authorization_probes(self):
        with tempfile.TemporaryDirectory() as directory:
            output = write_order_management_v1_2(Path(directory))
            source = output.read_text()
            py_compile.compile(str(output), doraise=True)

        self.assertIn("POST /users", source)
        self.assertIn("Authorization", source)
        self.assertIn("ownerId", source)
        self.assertIn("sec_test_improper_access_control", source)
        self.assertIn("sec_test_incorrect_authorization", source)
        self.assertIn("attacker", source)


if __name__ == "__main__":
    unittest.main()
