import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEED_DIR = ROOT / "seeds" / "complex"

EXPECTED = {
    "ComplexSignedWebhookProcessor": {
        "domain": "api_integration",
        "task_type": "signed_webhook",
        "cwes": {"CWE-345", "CWE-294", "CWE-20", "CWE-400"},
        "oracle_contract": {
            "hmac_algorithm": "HMAC-SHA256",
            "signature_input": "raw_body+timestamp+event_id",
            "max_absolute_timestamp_skew_seconds": 300,
            "signature_comparison": "constant_time",
            "duplicate_event_key": ["integration_id", "event_id"],
            "duplicate_retention_seconds": 86400,
            "duplicate_event_status": 409,
            "max_body_bytes": 262144,
            "inspection_requires_auth": True,
            "inspection_scope": "integration_owner",
            "unauthorized_inspection_status": "403_or_404",
        },
        "clauses": [
            "hmac-sha256 over the raw body, timestamp, and event id",
            "reject timestamps more than 300 seconds old or more than 300 seconds in the future",
            "compare signatures in constant time",
            "retain integration id and event id duplicate records for 86400 seconds",
            "a duplicate within the retention window must return 409",
            "limit the request body to 262144 bytes",
            "event inspection requires authentication",
            "only the integration owner can inspect accepted events",
            "non-owner event inspection must return 403 or 404",
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
            "race_probe": {
                "initial_stock": 4,
                "concurrent_requests": 8,
                "authenticated_users": 1,
                "unique_idempotency_keys": 8,
                "same_sku": True,
                "quantity_per_request": 1,
                "expected_successful_orders": 4,
                "expected_charges": 4,
                "expected_rejections": 4,
                "expected_final_stock": 0,
                "insufficient_stock_status": 409,
            },
            "idempotency_scope": "authenticated_user",
            "idempotency_same_payload": "same_order",
            "idempotency_different_payload_status": 409,
            "cross_user_idempotency_behavior": "independent",
            "cross_user_order_disclosure": False,
            "one_charge_and_order_per_idempotency_key": True,
            "max_line_items_per_checkout": 50,
            "quantity_min": 1,
            "quantity_max": 100,
            "owner_can_cancel_pending_order": True,
            "non_owner_read_or_cancel": "403_or_404",
            "cancellation_restores_stock_once": True,
            "cancellation_refunds_once": True,
        },
        "clauses": [
            "require authenticated ownership",
            "all 8 concurrent requests are by the same authenticated user, target the same sku, and each uses a unique idempotency key",
            "with initial stock 4, 8 concurrent requests for quantity 1 must produce exactly 4 successful orders, 4 charges, 4 rejections with status 409, and final stock 0",
            "scope idempotency keys to the authenticated user",
            "the same key and same payload must return the same order",
            "the same key with a different payload must return 409",
            "the same key used by different authenticated users is independent and must never return another user's order",
            "create only one charge and one order per idempotency key",
            "allow at most 50 line items per checkout",
            "each quantity must be between 1 and 100",
            "the owner can cancel a pending order",
            "non-owner read or cancellation must return 403 or 404",
            "cancellation restores stock once and cannot refund or restore twice",
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
            "token_generator": "cryptographically_secure",
            "min_token_entropy_bits": 256,
            "token_encoding": "url_safe",
            "token_storage": "digest",
            "token_single_use": True,
            "token_reuse": "invalid",
            "reset_revokes_all_sessions": True,
        },
        "clauses": [
            "return the same 202 response for existing and missing accounts",
            "reset tokens expire after 900 seconds",
            "use a csprng to generate at least 32 random bytes before url-safe encoding each reset token",
            "store reset tokens as digests and make them single-use",
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
