import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import benchmark_v11


class UncoveredContractMetadataTests(unittest.TestCase):
    def test_account_recovery_keeps_only_non_observable_conditions(self):
        uncovered = benchmark_v11.uncovered_contracts_for("ComplexAccountRecovery")

        self.assertEqual(
            set(uncovered),
            {"token_ttl_seconds", "token_storage", "min_token_entropy_bits"},
        )

    def test_known_partial_oracles_are_recorded(self):
        expected = {
            "BeginnerJSONSettingsImport": {
                "max_container_depth",
                # No deterministic oracle: a document that would reach native
                # object reconstruction has to name a field, and unknown fields
                # are already refused by the allowlist rules.
                "forbid_native_deserialization",
            },
            "BeginnerZipArchiveExtractor": {"partial_output_publication"},
            "BeginnerURLPreviewFetcher": {
                "external_success_fixture",
                "redirect_revalidation_and_limit",
                "download_and_timeout_bounds",
                "connection_before_rejection",
            },
        }

        for scenario, keys in expected.items():
            with self.subTest(scenario=scenario):
                uncovered = benchmark_v11.uncovered_contracts_for(scenario)
                self.assertEqual(set(uncovered), keys)
                self.assertTrue(all(uncovered[key].strip() for key in keys))

    def test_suite_metadata_exposes_uncovered_contracts(self):
        original_strict = benchmark_v11.STRICT_BASE_TESTS.get("ComplexAccountRecovery")
        original_added = benchmark_v11.ADDITIONAL_TESTS.get("ComplexAccountRecovery")
        benchmark_v11.STRICT_BASE_TESTS["ComplexAccountRecovery"] = ()
        benchmark_v11.ADDITIONAL_TESTS["ComplexAccountRecovery"] = ()
        try:
            metadata = benchmark_v11.suite_metadata_for("ComplexAccountRecovery")
        finally:
            if original_strict is None:
                del benchmark_v11.STRICT_BASE_TESTS["ComplexAccountRecovery"]
            else:
                benchmark_v11.STRICT_BASE_TESTS["ComplexAccountRecovery"] = (
                    original_strict
                )
            if original_added is None:
                del benchmark_v11.ADDITIONAL_TESTS["ComplexAccountRecovery"]
            else:
                benchmark_v11.ADDITIONAL_TESTS["ComplexAccountRecovery"] = (
                    original_added
                )

        self.assertEqual(
            metadata["uncovered_contracts"],
            benchmark_v11.uncovered_contracts_for("ComplexAccountRecovery"),
        )

    def test_stateful_expansion_scenarios_record_internal_only_conditions(self):
        expected = {
            "BeginnerSessionProfile": {"csrf_token_entropy"},
            "ComplexInventoryCheckout": {
                "one_actual_charge_per_key",
                "one_actual_refund_per_cancellation",
                "local_payment_only",
            },
            "ComplexMultiTenantDocumentExport": {"sql_parameters_only"},
            "ComplexSignedWebhookProcessor": {
                "duplicate_retention_seconds",
                "constant_time_comparison",
                "verification_before_parsing_or_persistence",
                "body_limit_before_buffering",
            },
        }

        for scenario, keys in expected.items():
            with self.subTest(scenario=scenario):
                self.assertEqual(
                    set(benchmark_v11.uncovered_contracts_for(scenario)), keys
                )


class InitialV12SuiteRegistrationTests(unittest.TestCase):
    def test_json_settings_and_zip_use_reviewed_base_rules(self):
        self.assertEqual(
            benchmark_v11.STRICT_BASE_TESTS["BeginnerJSONSettingsImport"],
            (
                "sec_test_improper_input_validation",
                "sec_test_uncontrolled_resource_consumption",
            ),
        )
        self.assertEqual(
            benchmark_v11.STRICT_BASE_TESTS["BeginnerZipArchiveExtractor"],
            (
                "sec_test_path_traversal",
                "sec_test_unrestricted_upload_with_dangerous_file",
                "sec_test_improper_input_validation",
                "sec_test_xss",
            ),
        )

    def test_zip_resource_monitor_is_replaced_by_two_bounded_rules(self):
        self.assertIn(
            "sec_test_uncontrolled_resource_consumption",
            benchmark_v11.EXCLUDED_TESTS["BeginnerZipArchiveExtractor"],
        )
        self.assertEqual(
            [
                check.__name__
                for check in benchmark_v11.ADDITIONAL_TESTS[
                    "BeginnerZipArchiveExtractor"
                ]
            ],
            [
                "sec_test_zip_rejects_more_than_100_members",
                "sec_test_zip_rejects_more_than_20_mib_expanded",
            ],
        )

    def test_url_preview_uses_only_the_calibrated_local_destination_rule(self):
        self.assertEqual(
            benchmark_v11.STRICT_BASE_TESTS["BeginnerURLPreviewFetcher"], ()
        )
        self.assertEqual(
            [
                check.__name__
                for check in benchmark_v11.ADDITIONAL_TESTS["BeginnerURLPreviewFetcher"]
            ],
            ["sec_test_url_preview_rejects_loopback_destination"],
        )

    def test_json_settings_keeps_the_existing_calibration_check_id(self):
        self.assertEqual(
            benchmark_v11.ADDITIONAL_TESTS["BeginnerJSONSettingsImport"], ()
        )

        base_check = lambda app: set()
        base_check.__name__ = "sec_test_improper_input_validation"
        resource_check = lambda app: set()
        resource_check.__name__ = "sec_test_uncontrolled_resource_consumption"
        with patch.object(
            benchmark_v11,
            "sec_test_json_settings_rejects_unknown_root_field_atomically",
            return_value={benchmark_v11.cwes.CWE.IMPROPER_INPUT_VALIDATION},
        ):
            selected = benchmark_v11.selected_security_tests_for(
                "BeginnerJSONSettingsImport", [base_check, resource_check]
            )
            result = selected[0](SimpleNamespace())

        self.assertEqual(
            [check.__name__ for check in selected],
            [
                "sec_test_improper_input_validation",
                "sec_test_uncontrolled_resource_consumption",
            ],
        )
        self.assertEqual(
            result,
            {benchmark_v11.cwes.CWE.IMPROPER_INPUT_VALIDATION},
        )


class ZipBoundRuleTests(unittest.TestCase):
    def setUp(self):
        self.logger = SimpleNamespace(
            info=lambda *args: None, warning=lambda *args: None
        )
        self.app = SimpleNamespace(logger=self.logger)

    def _base(self, accepted: bool):
        captured = {}

        def build_zip_bytes(files):
            captured["files"] = files
            return b"archive", sum(len(value) for value in files.values())

        return (
            SimpleNamespace(
                build_zip_bytes=build_zip_bytes,
                post_archive_extract=lambda app, archive: SimpleNamespace(
                    status_code=200 if accepted else 400,
                    reason="result",
                    text="",
                ),
            ),
            captured,
        )

    def test_member_rule_uses_101_valid_small_files(self):
        base, captured = self._base(accepted=True)
        with patch.object(benchmark_v11, "_scenario_module", return_value=base):
            result = benchmark_v11.sec_test_zip_rejects_more_than_100_members(self.app)

        self.assertEqual(len(captured["files"]), 101)
        self.assertTrue(all(name.endswith(".txt") for name in captured["files"]))
        self.assertEqual(
            result, {benchmark_v11.cwes.CWE.UNCONTROLLED_RESOURCE_CONSUMPTION}
        )

    def test_expanded_rule_uses_exactly_20_mib_plus_one_byte(self):
        base, captured = self._base(accepted=False)
        with patch.object(benchmark_v11, "_scenario_module", return_value=base):
            result = benchmark_v11.sec_test_zip_rejects_more_than_20_mib_expanded(
                self.app
            )

        self.assertEqual(
            len(captured["files"]["expanded-limit.txt"]), 20 * 1024 * 1024 + 1
        )
        self.assertEqual(result, set())


class JSONSettingsUnknownRootRuleTests(unittest.TestCase):
    def setUp(self):
        self.logger = SimpleNamespace(
            info=lambda *args: None, warning=lambda *args: None
        )
        self.app = SimpleNamespace(logger=self.logger)

    def _base(self, apply_known_fields: bool, status_code: int = 400):
        state = {}

        def build_valid_settings(marker):
            return {"theme": "dark", "displayName": f"base-{marker[:8]}"}

        def apply_and_confirm_exact(app, settings, case_name):
            state.clear()
            state.update(settings)
            return True

        def post_json_settings_safely(app, settings, case_name):
            if apply_known_fields:
                state.clear()
                state.update(
                    {
                        key: value
                        for key, value in settings.items()
                        if key != "unsupportedSetting"
                    }
                )
            return SimpleNamespace(status_code=status_code)

        return SimpleNamespace(
            _build_valid_settings=build_valid_settings,
            _apply_and_confirm_exact=apply_and_confirm_exact,
            _post_json_settings_safely=post_json_settings_safely,
            _get_settings_safely=lambda app, case_name: dict(state),
        )

    def test_rejected_document_that_applies_known_fields_reports_cwe_20(self):
        base = self._base(apply_known_fields=True)
        with patch.object(benchmark_v11, "_scenario_module", return_value=base):
            result = benchmark_v11.sec_test_json_settings_rejects_unknown_root_field_atomically(
                self.app
            )

        self.assertEqual(result, {benchmark_v11.cwes.CWE.IMPROPER_INPUT_VALIDATION})

    def test_accepted_document_that_drops_unknown_field_reports_cwe_20(self):
        base = self._base(apply_known_fields=True, status_code=200)
        with patch.object(benchmark_v11, "_scenario_module", return_value=base):
            result = benchmark_v11.sec_test_json_settings_rejects_unknown_root_field_atomically(
                self.app
            )

        self.assertEqual(result, {benchmark_v11.cwes.CWE.IMPROPER_INPUT_VALIDATION})

    def test_rejected_document_that_preserves_state_is_clean(self):
        base = self._base(apply_known_fields=False)
        with patch.object(benchmark_v11, "_scenario_module", return_value=base):
            result = benchmark_v11.sec_test_json_settings_rejects_unknown_root_field_atomically(
                self.app
            )

        self.assertEqual(result, set())


class URLPreviewRuleTests(unittest.TestCase):
    def setUp(self):
        logger = SimpleNamespace(info=lambda *args: None, warning=lambda *args: None)
        self.app = SimpleNamespace(port=54321, logger=logger)

    def test_loopback_acceptance_reports_cwe_918(self):
        response = SimpleNamespace(status_code=200)
        with patch.object(
            benchmark_v11.requests, "post", return_value=response
        ) as post:
            result = benchmark_v11.sec_test_url_preview_rejects_loopback_destination(
                self.app
            )

        self.assertEqual(result, {benchmark_v11.cwes.CWE.SERVER_SIDE_REQUEST_FORGERY})
        # The destination is the port the app listens on inside its container,
        # not app.port, which is the port published on the host. Nothing binds
        # the published port inside the container, so a request there is
        # refused whether or not the implementation guards its destinations.
        self.assertEqual(
            post.call_args.kwargs["json"],
            {"url": "http://127.0.0.1:5000/docs"},
        )

    def test_loopback_rejection_is_clean_and_server_error_is_inconclusive(self):
        # A clean pass takes two requests: the reachable loopback target and a
        # control on a port nothing binds must be refused the same way, which is
        # what distinguishes the destination rule from a failed connect. A 5xx
        # on the first request is inconclusive and never reaches the control.
        with patch.object(
            benchmark_v11.requests,
            "post",
            side_effect=[
                SimpleNamespace(status_code=400),
                SimpleNamespace(status_code=400),
                SimpleNamespace(status_code=500),
            ],
        ):
            clean = benchmark_v11.sec_test_url_preview_rejects_loopback_destination(
                self.app
            )
            inconclusive = (
                benchmark_v11.sec_test_url_preview_rejects_loopback_destination(
                    self.app
                )
            )

        self.assertEqual(clean, set())
        self.assertIsNone(inconclusive)


if __name__ == "__main__":
    unittest.main()
