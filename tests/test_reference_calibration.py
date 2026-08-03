import unittest

from reference_calibration import summarize_calibration


class ReferenceCalibrationTests(unittest.TestCase):
    def test_pending_probe_is_not_reported_as_calibrated(self):
        summary = summarize_calibration(
            {
                "probes": [
                    {
                        "probe_id": "Example/sec_test_input",
                        "status": "pending",
                        "secure_fixture": {"id": "secure", "expected_cwes": []},
                        "vulnerable_fixture": {
                            "id": "vulnerable",
                            "expected_cwes": [20],
                        },
                        "runs": [],
                    }
                ]
            }
        )

        self.assertEqual(summary["calibrated_count"], 0)
        self.assertEqual(summary["pending_count"], 1)
        self.assertEqual(summary["invalid_count"], 0)

    def test_calibrated_probe_requires_secure_and_vulnerable_evidence(self):
        summary = summarize_calibration(
            {
                "probes": [
                    {
                        "probe_id": "Example/sec_test_input",
                        "status": "calibrated",
                        "secure_fixture": {"id": "secure", "expected_cwes": []},
                        "vulnerable_fixture": {
                            "id": "vulnerable",
                            "expected_cwes": [20],
                        },
                        "runs": [
                            {"fixture_id": "secure", "observed_cwes": []},
                            {"fixture_id": "vulnerable", "observed_cwes": [20]},
                        ],
                    }
                ]
            }
        )

        self.assertEqual(summary["calibrated_count"], 1)
        self.assertEqual(summary["invalid_count"], 0)

    def test_claimed_calibration_with_missing_vulnerable_evidence_is_invalid(self):
        summary = summarize_calibration(
            {
                "probes": [
                    {
                        "probe_id": "Example/sec_test_input",
                        "status": "calibrated",
                        "secure_fixture": {"id": "secure", "expected_cwes": []},
                        "vulnerable_fixture": {
                            "id": "vulnerable",
                            "expected_cwes": [20],
                        },
                        "runs": [{"fixture_id": "secure", "observed_cwes": []}],
                    }
                ]
            }
        )

        self.assertEqual(summary["calibrated_count"], 0)
        self.assertEqual(summary["invalid_count"], 1)


if __name__ == "__main__":
    unittest.main()
