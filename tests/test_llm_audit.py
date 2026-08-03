import json
import unittest

from llm_audit import (
    audit_provenance,
    build_audit_report,
    redact_sensitive_text,
    require_code_upload_confirmation,
    parse_review_json,
    select_audit_samples,
)


class LlmAuditTests(unittest.TestCase):
    def setUp(self):
        self.summary = {
            "model": "gpt-5.5",
            "rows": [
                {
                    "scenario_id": "BeginnerUploadGallery__natural",
                    "base_scenario": "BeginnerUploadGallery",
                    "scenario_level": "beginner",
                    "prompt_category": "natural",
                    "samples": [
                        {
                            "sample_index": 0,
                            "repeat": 0,
                            "status": "passed",
                            "test_results": "/tmp/beginner/test_results.json",
                        }
                    ],
                },
                {
                    "scenario_id": "ComplexPaymentTokens__threat_modeling",
                    "base_scenario": "ComplexPaymentTokens",
                    "scenario_level": "complex",
                    "prompt_category": "threat_modeling",
                    "samples": [
                        {
                            "sample_index": 0,
                            "repeat": 0,
                            "status": "passed",
                            "test_results": "/tmp/complex/test_results.json",
                        },
                        {
                            "sample_index": 1,
                            "repeat": 1,
                            "status": "security_failed",
                            "test_results": "/tmp/failed/test_results.json",
                        },
                    ],
                },
            ],
        }
        self.manifest = {
            "BeginnerUploadGallery__natural": {
                "scenario_id": "BeginnerUploadGallery__natural"
            },
            "ComplexPaymentTokens__threat_modeling": {
                "scenario_id": "ComplexPaymentTokens__threat_modeling"
            },
        }

    def test_parse_review_json_accepts_one_bounded_candidate(self):
        review = parse_review_json(
            "```json\n"
            + json.dumps(
                {
                    "verdict": "candidate",
                    "confidence": "medium",
                    "candidate_cwes": [863],
                    "attack_surface": "POST /charges",
                    "evidence": "The owner check is absent before the charge is created.",
                    "suggested_test": "Create victim and attacker, then charge victim token.",
                    "needs_manual_review": True,
                }
            )
            + "\n```"
        )

        self.assertEqual(review["verdict"], "candidate")
        self.assertEqual(review["candidate_cwes"], [863])
        self.assertTrue(review["needs_manual_review"])

    def test_parse_review_json_rejects_a_score_mutating_verdict(self):
        with self.assertRaises(ValueError):
            parse_review_json('{"verdict": "security_failed"}')

    def test_select_audit_samples_defaults_to_complex_passes(self):
        selected = select_audit_samples(
            self.summary,
            self.manifest,
            complex_only=True,
        )

        self.assertEqual(len(selected), 1)
        self.assertEqual(
            selected[0]["scenario_id"], "ComplexPaymentTokens__threat_modeling"
        )
        self.assertEqual(selected[0]["deterministic_status"], "passed")

    def test_report_keeps_deterministic_status_unchanged(self):
        report = build_audit_report(
            generation_model="gpt-5.5",
            auditor_model="audit-model",
            reviews=[
                {
                    "scenario_id": "ComplexPaymentTokens__threat_modeling",
                    "sample_index": 0,
                    "repeat": 0,
                    "deterministic_status": "passed",
                    "audit": {
                        "verdict": "candidate",
                        "confidence": "medium",
                        "candidate_cwes": [863],
                        "attack_surface": "POST /charges",
                        "evidence": "Potential owner check gap.",
                        "suggested_test": "Cross-user charge test.",
                        "needs_manual_review": True,
                    },
                }
            ],
        )

        self.assertEqual(report["reviews"][0]["deterministic_status"], "passed")
        self.assertEqual(report["candidate_count"], 1)

    def test_report_groups_equivalent_candidates_by_route_and_cwe(self):
        base = {
            "base_scenario": "ComplexAPIMockProxy",
            "deterministic_status": "passed",
            "audit": {
                "verdict": "candidate",
                "confidence": "high",
                "candidate_cwes": [522],
                "evidence": "A secret may be preserved in logs.",
                "suggested_test": "Send a marker and inspect logs.",
                "needs_manual_review": True,
            },
        }
        first = {
            **base,
            "scenario_id": "ComplexAPIMockProxy__expert",
            "sample_index": 0,
            "repeat": 0,
            "audit": {
                **base["audit"],
                "attack_surface": "POST /proxy persists headers; GET /logs returns them.",
            },
        }
        second = {
            **base,
            "scenario_id": "ComplexAPIMockProxy__weak_security",
            "sample_index": 1,
            "repeat": 1,
            "audit": {
                **base["audit"],
                "attack_surface": "/proxy stores headers and /logs exposes requestHeaders.",
            },
        }
        third = {
            **base,
            "scenario_id": "ComplexAPIMockProxy__expert",
            "sample_index": 2,
            "repeat": 2,
            "audit": {
                **base["audit"],
                "attack_surface": (
                    "/proxy stores sanitized headers, /logs exposes them to the "
                    "user/profile."
                ),
            },
        }

        report = build_audit_report(
            generation_model="gpt-5.5",
            auditor_model="audit-model",
            reviews=[first, second, third],
        )

        self.assertEqual(report["candidate_count"], 1)
        self.assertEqual(len(report["candidate_groups"][0]["sample_refs"]), 3)

    def test_redact_sensitive_text_replaces_values_but_preserves_context(self):
        redacted, count = redact_sensitive_text(
            'api_key = "sk-real-value"\nAuthorization: Bearer abc.def.ghi\nname = "ok"'
        )

        self.assertEqual(count, 2)
        self.assertIn("api_key", redacted)
        self.assertIn('name = "ok"', redacted)
        self.assertNotIn("sk-real-value", redacted)
        self.assertNotIn("abc.def.ghi", redacted)

    def test_audit_provenance_has_stable_hashes_and_endpoint_host(self):
        provenance = audit_provenance(
            packet={"generated_code": "print('hello')"},
            auditor_model="audit-model",
            base_url="https://audit.example/v1",
        )

        self.assertEqual(provenance["endpoint_host"], "audit.example")
        self.assertEqual(len(provenance["packet_sha256"]), 64)
        self.assertEqual(len(provenance["code_sha256"]), 64)
        self.assertEqual(len(provenance["system_prompt_sha256"]), 64)

    def test_live_audit_requires_explicit_code_upload_confirmation(self):
        with self.assertRaises(PermissionError):
            require_code_upload_confirmation(dry_run=False, allow_code_upload=False)

        require_code_upload_confirmation(dry_run=True, allow_code_upload=False)
        require_code_upload_confirmation(dry_run=False, allow_code_upload=True)


if __name__ == "__main__":
    unittest.main()
