import unittest

from llm_audit_triage import summarize_triage


class LlmAuditTriageTests(unittest.TestCase):
    def test_summarize_triage_calculates_confirmation_and_test_yield(self):
        report = summarize_triage(
            [
                {
                    "fingerprint": "a",
                    "outcome": "confirmed_missing_coverage",
                    "deterministic_test_added": True,
                },
                {
                    "fingerprint": "b",
                    "outcome": "false_positive",
                    "deterministic_test_added": False,
                },
                {
                    "fingerprint": "c",
                    "outcome": "out_of_scope",
                    "deterministic_test_added": False,
                },
                {
                    "fingerprint": "d",
                    "outcome": "needs_specification_change",
                    "deterministic_test_added": False,
                },
            ]
        )

        self.assertEqual(report["reviewed_count"], 4)
        self.assertEqual(report["confirmed_count"], 1)
        self.assertEqual(report["false_positive_count"], 1)
        self.assertEqual(report["confirmation_rate"], 0.25)
        self.assertEqual(report["deterministic_test_yield"], 0.25)

    def test_summarize_triage_rejects_unknown_outcome(self):
        with self.assertRaises(ValueError):
            summarize_triage(
                [
                    {
                        "fingerprint": "a",
                        "outcome": "security_failed",
                        "deterministic_test_added": False,
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
