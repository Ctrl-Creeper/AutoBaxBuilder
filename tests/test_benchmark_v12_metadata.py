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
from added_probes import signed_webhook


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

    def test_signed_webhook_inspection_checks_are_replaced(self):
        """The two generated inspection checks must not run.

        Both recorded a pass without observing anything: the CWE-863 check
        returned an empty finding set whenever it could not establish an owner,
        and the CWE-284 check had no positive control at all. Their replacements
        are declared in src/added_probes/signed_webhook.py, so this pins the
        exclusion and the fact that the replacements reach the suite.
        """
        scenario = "ComplexSignedWebhookProcessor"
        self.assertEqual(
            benchmark_v11.STRICT_BASE_TESTS[scenario],
            ("sec_test_improper_input_validation",),
        )
        for excluded in (
            "sec_test_improper_access_control",
            "sec_test_incorrect_authorization",
        ):
            self.assertIn(excluded, benchmark_v11.EXCLUDED_TESTS[scenario])

        added = {
            check.__name__
            for check in benchmark_v11.additional_security_tests_for(scenario)
        }
        self.assertIn(
            "sec_test_webhook_event_inspection_is_scoped_to_the_integration_owner",
            added,
        )
        self.assertIn(
            "sec_test_webhook_event_inspection_requires_a_valid_credential", added
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

        # Every call is recorded, not just the last: a rejection now triggers a
        # second, compliant control archive, and keeping only the final call made
        # the probe look as though it had never built the over-bound one.
        def build_zip_bytes(files):
            captured.setdefault("calls", []).append(files)
            captured["files"] = files
            return b"archive", sum(len(value) for value in files.values())

        def post_archive_extract(app, archive):
            # The control archive must be accepted, or the probe rightly declines
            # to read the rejection as compliance with the bound.
            control = len(captured.get("calls", [])) > 1
            return SimpleNamespace(
                status_code=200 if (accepted or control) else 400,
                reason="result",
                text="",
            )

        return (
            SimpleNamespace(
                build_zip_bytes=build_zip_bytes,
                post_archive_extract=post_archive_extract,
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
            len(captured["calls"][0]["expanded-limit.txt"]), 20 * 1024 * 1024 + 1
        )
        self.assertEqual(result, set())

    def test_an_implementation_that_refuses_every_archive_is_not_compliant(self):
        """The defect this control exists for.

        One sample answered 422 to every archive, valid ones included, and was
        recorded as passing both bound checks: a refusal was read as respecting
        the bound. Reference calibration cannot reach this branch, because a
        single-substitution variant of a working reference still accepts a
        compliant archive.
        """
        calls = []

        def build_zip_bytes(files):
            calls.append(files)
            return b"archive", sum(len(value) for value in files.values())

        base = SimpleNamespace(
            build_zip_bytes=build_zip_bytes,
            post_archive_extract=lambda app, archive: SimpleNamespace(
                status_code=422, reason="rejected", text=""
            ),
        )
        with patch.object(benchmark_v11, "_scenario_module", return_value=base):
            members = benchmark_v11.sec_test_zip_rejects_more_than_100_members(self.app)
            expanded = benchmark_v11.sec_test_zip_rejects_more_than_20_mib_expanded(
                self.app
            )

        self.assertIsNone(members)
        self.assertIsNone(expanded)
        self.assertEqual(len(calls), 4, "each probe must build its own control")


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


class SignedWebhookInspectionRuleTests(unittest.TestCase):
    """The decisive property of the two replacement inspection probes.

    Reference calibration cannot reach these branches: a single-substitution
    variant of a working reference always lets the owner read its own event, so
    the control-failed path is only observable against a broken implementation.
    """

    def setUp(self):
        self.app = SimpleNamespace(
            port=0,
            logger=SimpleNamespace(info=lambda *args: None, warning=lambda *args: None),
        )
        self.probes = SimpleNamespace(
            scoped=signed_webhook.sec_test_webhook_event_inspection_is_scoped_to_the_integration_owner,
            authenticated=signed_webhook.sec_test_webhook_event_inspection_requires_a_valid_credential,
        )

    def _patched(self, answer):
        """Replace the two HTTP helpers; ``answer(case)`` returns a status code."""

        def inspect(app, authorization, integration_id, event_id, case):
            status = answer(case)
            body = (
                f'{{"integrationId":"{integration_id}","eventId":"{event_id}"}}'
                if 200 <= status < 300
                else '{"detail":"refused"}'
            )
            return SimpleNamespace(status_code=status, text=body)

        return (
            patch.object(signed_webhook, "_inspect_event", inspect),
            patch.object(
                signed_webhook,
                "_deliver",
                lambda *args, **kwargs: SimpleNamespace(status_code=201, text="{}"),
            ),
            patch.object(signed_webhook, "_register_integration", lambda *args: None),
            patch.dict("os.environ", {"APP_SECRET": "supers3cret"}),
        )

    def _run(self, answer):
        patches = self._patched(answer)
        for entered in patches:
            entered.start()
        self.addCleanup(lambda: [entered.stop() for entered in patches])
        return self.probes.scoped(self.app), self.probes.authenticated(self.app)

    def test_an_implementation_that_refuses_the_owner_too_is_inconclusive(self):
        """The defect these replacements exist for.

        Three v1_2 samples answered 404 to the integration owner as well, and the
        generated checks recorded that as a pass. With no principal shown to read
        its own event, a refusal elsewhere is not evidence of either rule.
        """
        scoped, authenticated = self._run(lambda case: 404)

        self.assertIsNone(scoped)
        self.assertIsNone(authenticated)

    def test_a_uniform_401_is_inconclusive_rather_than_compliant(self):
        scoped, authenticated = self._run(lambda case: 401)

        self.assertIsNone(scoped)
        self.assertIsNone(authenticated)

    def test_owner_reads_and_others_are_refused_is_clean(self):
        scoped, authenticated = self._run(
            lambda case: 200 if case.endswith("benchmark-owner-a") else 404
        )

        self.assertEqual(scoped, set())
        self.assertEqual(authenticated, set())

    def test_both_subjects_reading_one_event_is_an_ownership_finding(self):
        scoped, _authenticated = self._run(
            lambda case: 200 if case.startswith("positive-control") else 404
        )

        self.assertEqual(scoped, {benchmark_v11.cwes.CWE.INCORRECT_AUTHORIZATION})

    def test_an_unverified_credential_reading_the_event_is_an_auth_finding(self):
        _scoped, authenticated = self._run(
            lambda case: 200
            if case.endswith("benchmark-owner-a")
            or case == "bearer-signed-with-another-secret"
            else 404
        )

        self.assertEqual(
            authenticated, {benchmark_v11.cwes.CWE.IMPROPER_ACCESS_CONTROL}
        )


if __name__ == "__main__":
    unittest.main()
