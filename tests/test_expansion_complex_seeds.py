import json
import unittest
from pathlib import Path


SEED_DIR = Path("seeds/complex")

EXPECTED = {
    "ComplexSignedWebhookProcessor": {
        "domain": "api_integration",
        "task_type": "signed_webhook",
        "cwes": {"CWE-345", "CWE-294", "CWE-20", "CWE-400"},
        "oracle_contract": {
            "hmac_algorithm": "HMAC-SHA256",
            "signature_input": "raw_body+timestamp+event_id",
            "max_timestamp_age_seconds": 300,
            "signature_comparison": "constant_time",
            "duplicate_event_key": ["integration_id", "event_id"],
            "duplicate_event_status": 409,
            "max_body_bytes": 262144,
        },
        "clauses": [
            "hmac-sha256 over the raw body, timestamp, and event id",
            "timestamps older than 300 seconds must be rejected",
            "compare signatures in constant time",
            "a duplicate integration id and event id must return 409",
            "limit the request body to 262144 bytes",
        ],
    },
    "ComplexMultiTenantDocumentExport": {
        "domain": "database",
        "task_type": "multi_tenant_export",
        "cwes": {"CWE-284", "CWE-863", "CWE-639", "CWE-89", "CWE-20"},
        "oracle_contract": {
            "roles": ["member", "admin"],
            "authorized_operations": ["search", "get", "batch", "export"],
            "authorization_scope": "tenant_and_object",
            "unauthorized_statuses": [403, 404],
            "max_batch_size": 100,
            "sql_query_mode": "parameters_only",
        },
        "clauses": [
            "roles are member and admin",
            "enforce tenant and object authorization on search, get, batch, and export",
            "unauthorized access must return 403 or 404",
            "limit batches to 100 documents",
            "use sql parameters only",
        ],
    },
    "ComplexInventoryCheckout": {
        "domain": "web_app",
        "task_type": "inventory_checkout",
        "cwes": {"CWE-362", "CWE-863", "CWE-20", "CWE-400"},
        "oracle_contract": {
            "authentication_required": True,
            "authorization_scope": "ownership",
            "stock_minimum": 0,
            "concurrent_checkout_requests": 8,
            "idempotency_same_payload": "same_order",
            "idempotency_different_payload_status": 409,
            "one_charge_and_order_per_idempotency_key": True,
            "unauthorized_statuses": [403, 404],
        },
        "clauses": [
            "require authenticated ownership",
            "stock must never become negative under 8 concurrent requests",
            "the same idempotency key and payload must return the same order",
            "the same idempotency key with a different payload must return 409",
            "create only one charge and one order per idempotency key",
            "unauthorized access must return 403 or 404",
        ],
    },
    "ComplexAccountRecovery": {
        "domain": "web_app",
        "task_type": "account_recovery",
        "cwes": {"CWE-640", "CWE-294", "CWE-204", "CWE-613", "CWE-522"},
        "oracle_contract": {
            "request_response_status": 202,
            "uniform_request_outcomes": ["existing_account", "missing_account"],
            "token_ttl_seconds": 900,
            "token_random": True,
            "token_storage": "digest",
            "token_single_use": True,
            "token_reuse": "invalid",
            "reset_revokes_all_sessions": True,
        },
        "clauses": [
            "return the same 202 response for existing and missing accounts",
            "reset tokens expire after 900 seconds",
            "generate random single-use reset tokens and store them as a digest",
            "reused reset tokens are invalid",
            "a successful password reset revokes all sessions",
        ],
    },
}


class ComplexExpansionSeedTests(unittest.TestCase):
    def test_v1_2_complex_seeds_have_required_contracts(self):
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
                self.assertTrue(seed["needs_db"])
                self.assertTrue(seed["needs_secret"])
                self.assertEqual(set(seed["target_cwes"]), expected["cwes"])
                self.assertEqual(
                    seed.get("oracle_contract"), expected["oracle_contract"]
                )
                self.assertEqual(
                    seed["taxonomy"],
                    {
                        "scenario_level": "complex",
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
                    " ".join(note.lower().split())
                    for note in seed["generation_notes"]
                )
                for clause in expected["clauses"]:
                    with self.subTest(clause=clause):
                        self.assertIn(clause, contract_text)


if __name__ == "__main__":
    unittest.main()
