import ast
import asyncio
import importlib.util
import io
import json
import posixpath
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import benchmark_v11

FIXTURES_DIR = ROOT / "fixtures" / "reference_v1_1"
REGISTRY = ROOT / "artifacts" / "reference_calibration_v1_1.json"
V12_REGISTRY = ROOT / "artifacts" / "reference_calibration_v1_2.json"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = _load(
    "build_reference_fixtures", ROOT / "scripts" / "build_reference_fixtures.py"
)
runner = _load(
    "run_reference_calibration", ROOT / "scripts" / "run_reference_calibration.py"
)
verifier = _load(
    "verify_reference_calibration",
    ROOT / "scripts" / "verify_reference_calibration.py",
)


class BuildFixturesTests(unittest.TestCase):
    def _fixtures_dir(self, temporary_directory: str, old: str) -> Path:
        fixtures_dir = Path(temporary_directory)
        (fixtures_dir / "Scenario").mkdir(parents=True)
        (fixtures_dir / "Scenario" / "secure.py").write_text(
            "guard_a\nguard_b\nguard_a\n", encoding="utf-8"
        )
        (fixtures_dir / "variants.py").write_text(
            "VARIANTS = {'Scenario': {'vulnerable.py': "
            f"({old!r}, 'weakened', 'note')}}}}\n".replace("}}}}", "}}"),
            encoding="utf-8",
        )
        return fixtures_dir

    def test_single_match_is_substituted_and_annotated(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixtures_dir = self._fixtures_dir(temporary_directory, "guard_b")
            written = build.build(fixtures_dir)

            self.assertEqual([path.name for path in written], ["vulnerable.py"])
            generated = written[0].read_text(encoding="utf-8")
            self.assertIn("Weakening: note", generated)
            self.assertIn("weakened", generated)
            self.assertNotIn("guard_b", generated)

    def test_ambiguous_fragment_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixtures_dir = self._fixtures_dir(temporary_directory, "guard_a")
            with self.assertRaises(SystemExit) as raised:
                build.build(fixtures_dir)
            self.assertIn("matches 2 times", str(raised.exception))

    def test_absent_fragment_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixtures_dir = self._fixtures_dir(temporary_directory, "guard_missing")
            with self.assertRaises(SystemExit) as raised:
                build.build(fixtures_dir)
            self.assertIn("matches 0 times", str(raised.exception))

    def test_repository_variants_apply_cleanly(self):
        for scenario, variants in build.load_variants(FIXTURES_DIR).items():
            secure = (FIXTURES_DIR / scenario / "secure.py").read_text(encoding="utf-8")
            for filename, (old, _new, _note) in variants.items():
                with self.subTest(scenario=scenario, filename=filename):
                    self.assertEqual(secure.count(old), 1)

    def test_variant_output_cannot_escape_fixture_directory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            fixtures_dir = root / "fixtures"
            (fixtures_dir / "Scenario").mkdir(parents=True)
            (fixtures_dir / "Scenario" / "secure.py").write_text(
                "value = 1\n", encoding="utf-8"
            )
            (fixtures_dir / "variants.py").write_text(
                "VARIANTS = {'Scenario': {'../outside.py': "
                "('value = 1', 'value = 2', 'note')}}\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(SystemExit, "plain Python filename"):
                build.build(fixtures_dir)

            self.assertFalse((fixtures_dir / "outside.py").exists())

    def test_invalid_python_variant_is_rejected_before_write(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixtures_dir = Path(temporary_directory)
            (fixtures_dir / "Scenario").mkdir(parents=True)
            (fixtures_dir / "Scenario" / "secure.py").write_text(
                "value = 1\n", encoding="utf-8"
            )
            (fixtures_dir / "variants.py").write_text(
                "VARIANTS = {'Scenario': {'generated.py': "
                "('value = 1', 'value =', 'note')}}\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(SystemExit, "invalid Python"):
                build.build(fixtures_dir)

            self.assertFalse((fixtures_dir / "Scenario" / "generated.py").exists())


class ObservedCwesTests(unittest.TestCase):
    def test_reports_probe_findings(self):
        results = {"sec_test_x": {"status": "failed", "cwes": "22, 20"}}
        self.assertEqual(runner.observed_cwes(results, "sec_test_x", "f"), [20, 22])

    def test_passing_probe_reports_nothing(self):
        results = {"sec_test_x": {"status": "passed", "cwes": ""}}
        self.assertEqual(runner.observed_cwes(results, "sec_test_x", "f"), [])

    # FixtureRunError rather than SystemExit: the sweep records the reason
    # against this probe and keeps the results it has already collected.
    def test_exception_is_not_read_as_a_clean_result(self):
        results = {"sec_test_x": {"status": "exception", "cwes": ""}}
        with self.assertRaises(runner.FixtureRunError):
            runner.observed_cwes(results, "sec_test_x", "f")

    def test_missing_probe_is_rejected(self):
        with self.assertRaises(runner.FixtureRunError):
            runner.observed_cwes({}, "sec_test_x", "f")


class CalibrationLayoutTests(unittest.TestCase):
    def test_v11_registry_uses_unchanged_default_layout(self):
        layout = runner.calibration_layout({"probes": []})

        self.assertEqual(
            runner.scenario_file("Scenario", layout),
            Path("artifacts/factorial_prompt_scenarios_v1_1")
            / "Scenario"
            / "Scenario__natural__v1_1.py",
        )
        self.assertEqual(
            layout["runs_dir"], Path("artifacts/reference_calibration_runs")
        )

    def test_v12_registry_selects_expansion_layout(self):
        registry = {
            "calibration": {
                "scenario_dir": "artifacts/factorial_prompt_scenarios_expansion_v1_2",
                "scenario_id_template": "{base_scenario}__natural",
                "runs_dir": "artifacts/reference_calibration_runs_v1_2",
            },
            "probes": [],
        }

        layout = runner.calibration_layout(registry)

        self.assertEqual(
            runner.scenario_file("Scenario", layout),
            Path("artifacts/factorial_prompt_scenarios_expansion_v1_2")
            / "Scenario"
            / "Scenario__natural.py",
        )
        self.assertEqual(
            layout["runs_dir"], Path("artifacts/reference_calibration_runs_v1_2")
        )

    def test_registry_layout_rejects_path_escape(self):
        registry = {
            "calibration": {
                "scenario_dir": "../outside",
                "scenario_id_template": "{base_scenario}__natural",
                "runs_dir": "artifacts/reference_calibration_runs_v1_2",
            },
            "probes": [],
        }

        with self.assertRaisesRegex(SystemExit, "scenario_dir"):
            runner.calibration_layout(registry)


class CalibrationReportTests(unittest.TestCase):
    def test_v11_report_heading_is_preserved(self):
        registry = {"benchmark_version": "taxonomy_security_generation_set_v1_1"}

        self.assertEqual(
            verifier.report_heading(registry),
            "# Reference Calibration v1.1 Report",
        )

    def test_v12_report_heading_uses_registry_version(self):
        registry = {"benchmark_version": "taxonomy_expansion_v1_2"}

        self.assertEqual(
            verifier.report_heading(registry),
            "# Reference Calibration v1.2 Report",
        )


class ZipReferenceTests(unittest.TestCase):
    class HttpError(Exception):
        def __init__(self, status_code: int, detail: str):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    @classmethod
    def setUpClass(cls):
        path = FIXTURES_DIR / "BeginnerZipArchiveExtractor" / "secure.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        wanted = {
            "archive_entries",
            "require_member_count",
            "require_unique_paths",
        }
        definitions = [
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in wanted
        ]
        namespace = {
            "HTTPException": cls.HttpError,
            "MAX_MEMBERS": 100,
            "io": io,
            "posixpath": posixpath,
            "zipfile": zipfile,
        }
        exec(
            compile(ast.Module(definitions, type_ignores=[]), str(path), "exec"),
            namespace,
        )
        cls.helpers = namespace
        cls.tree = tree

    def test_member_limit_counts_directory_entries(self):
        payload = io.BytesIO()
        with zipfile.ZipFile(payload, "w") as archive:
            for index in range(101):
                archive.writestr(f"directory-{index}/", b"")

        entries = self.helpers["archive_entries"](payload.getvalue())

        self.assertEqual(len(entries), 101)
        with self.assertRaises(self.HttpError):
            self.helpers["require_member_count"](entries)

    def test_duplicate_check_canonicalizes_equivalent_paths(self):
        entries = [
            zipfile.ZipInfo("docs/readme.txt"),
            zipfile.ZipInfo("docs//readme.txt"),
        ]

        with self.assertRaises(self.HttpError):
            self.helpers["require_unique_paths"](entries)

    def test_extraction_route_cleans_up_on_any_standard_exception(self):
        route = next(
            node
            for node in self.tree.body
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "extract_archive"
        )
        handlers = [
            handler
            for node in ast.walk(route)
            if isinstance(node, ast.Try)
            for handler in node.handlers
        ]

        self.assertTrue(
            any(
                isinstance(handler.type, ast.Name) and handler.type.id == "Exception"
                for handler in handlers
            )
        )


class JsonMediaTypeReferenceTests(unittest.TestCase):
    class HttpError(Exception):
        def __init__(self, status_code: int, detail: str):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    class Request:
        def __init__(self, content_type: str, body: object):
            self.headers = {"content-type": content_type}
            self._body = body

        async def json(self):
            return self._body

    def _json_body_function(self, scenario: str):
        path = FIXTURES_DIR / scenario / "secure.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        function = next(
            node
            for node in tree.body
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == "json_object_body"
        )
        namespace = {
            "HTTPException": self.HttpError,
            "Request": self.Request,
        }
        exec(
            compile(ast.Module([function], type_ignores=[]), str(path), "exec"),
            namespace,
        )
        return namespace["json_object_body"]

    def test_json_routes_reject_a_non_json_media_type(self):
        for scenario in ("BeginnerSessionProfile", "ComplexAccountRecovery"):
            with self.subTest(scenario=scenario):
                parse_body = self._json_body_function(scenario)
                request = self.Request("text/plain", {"field": "value"})

                with self.assertRaises(self.HttpError) as raised:
                    asyncio.run(parse_body(request))

                self.assertEqual(raised.exception.status_code, 415)

    def test_json_routes_accept_parameters_on_application_json(self):
        for scenario in ("BeginnerSessionProfile", "ComplexAccountRecovery"):
            with self.subTest(scenario=scenario):
                parse_body = self._json_body_function(scenario)
                request = self.Request(
                    "application/json; charset=utf-8", {"field": "value"}
                )

                self.assertEqual(
                    asyncio.run(parse_body(request)),
                    {"field": "value"},
                )


class EvaluationFixtureReferenceTests(unittest.TestCase):
    def _source(self, scenario: str) -> str:
        return (FIXTURES_DIR / scenario / "secure.py").read_text(encoding="utf-8")

    def _string_constants(self, scenario: str) -> set[str]:
        tree = ast.parse(self._source(scenario))
        return {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }

    def test_session_profile_uses_the_declared_accounts(self):
        constants = self._string_constants("BeginnerSessionProfile")
        for value in (
            "benchmark-user-a",
            "benchmark-pass-a",
            "benchmark-user-b",
            "benchmark-pass-b",
        ):
            with self.subTest(value=value):
                self.assertIn(value, constants)

    def test_account_recovery_exposes_the_declared_lifecycle_fixture(self):
        source = self._source("ComplexAccountRecovery")
        for value in (
            "benchmark-existing@example.test",
            "benchmark-missing@example.test",
            "benchmark-session-a",
            "/test/reset-deliveries",
            "/test/sessions/{session_id}",
        ):
            with self.subTest(value=value):
                self.assertIn(value, source)

    def test_multi_tenant_reference_uses_declared_subjects_and_secret(self):
        source = self._source("ComplexMultiTenantDocumentExport")
        for value in (
            # Required, not defaulted: a reference that invents a secret when
            # the variable is unset would verify signatures against a value no
            # probe can produce, and every signed request would fail as if the
            # implementation were wrong.
            'os.environ["APP_SECRET"]',
            "benchmark-acme-member",
            "benchmark-acme-admin",
            "benchmark-globex-member",
            "11111111-1111-4111-8111-111111111101",
            "11111111-1111-4111-8111-111111111102",
            "22222222-2222-4222-8222-222222222201",
        ):
            with self.subTest(value=value):
                self.assertIn(value, source)


class RegistryTests(unittest.TestCase):
    def test_every_declared_fixture_source_exists(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        for probe in registry["probes"]:
            for key in ("secure_fixture", "vulnerable_fixture"):
                path = ROOT / probe[key]["path"]
                with self.subTest(probe=probe["probe_id"], fixture=key):
                    self.assertTrue(path.exists(), f"missing {path}")

    def test_v12_registry_uses_the_expansion_layout(self):
        registry = json.loads(V12_REGISTRY.read_text(encoding="utf-8"))

        self.assertEqual(registry["benchmark_version"], "taxonomy_expansion_v1_2")
        self.assertEqual(
            registry["calibration"],
            {
                "scenario_dir": "artifacts/factorial_prompt_scenarios_expansion_v1_2",
                "scenario_id_template": "{base_scenario}__natural",
                "runs_dir": "artifacts/reference_calibration_runs_v1_2",
            },
        )

    def test_calibration_report_default_prefix_is_versioned(self):
        self.assertEqual(
            verifier.default_output_prefix(
                {"benchmark_version": "taxonomy_expansion_v1_2"}
            ),
            Path("artifacts/REFERENCE_CALIBRATION_V1_2_REPORT"),
        )
        self.assertEqual(
            verifier.default_output_prefix(
                {"benchmark_version": "taxonomy_security_generation_set_v1_1"}
            ),
            Path("artifacts/REFERENCE_CALIBRATION_V1_1_REPORT"),
        )

    def test_v12_registry_matches_current_json_and_zip_suite(self):
        registry = json.loads(V12_REGISTRY.read_text(encoding="utf-8"))
        registered = {
            probe["probe_id"]
            for probe in registry["probes"]
            if probe["probe_id"].split("/", 1)[0]
            in {"BeginnerJSONSettingsImport", "BeginnerZipArchiveExtractor"}
        }
        expected = set()
        for scenario in (
            "BeginnerJSONSettingsImport",
            "BeginnerZipArchiveExtractor",
        ):
            # The curated suite, not ADDITIONAL_TESTS: probes drafted per
            # scenario live under src/added_probes and reach the suite through
            # this accessor. A probe no substitution can make report carries no
            # variant, so it has nothing to register.
            unfalsifiable = set(benchmark_v11.positive_evidence_only_for(scenario))
            names = list(benchmark_v11.STRICT_BASE_TESTS[scenario]) + [
                check.__name__
                for check in benchmark_v11.additional_security_tests_for(scenario)
                if check.__name__ not in unfalsifiable
            ]
            expected.update(f"{scenario}/{name}" for name in names)

        self.assertEqual(registered, expected)

    def test_every_v12_declared_fixture_source_exists(self):
        registry = json.loads(V12_REGISTRY.read_text(encoding="utf-8"))
        for probe in registry["probes"]:
            for key in ("secure_fixture", "vulnerable_fixture"):
                path = ROOT / probe[key]["path"]
                with self.subTest(probe=probe["probe_id"], fixture=key):
                    self.assertTrue(path.exists(), f"missing {path}")


if __name__ == "__main__":
    unittest.main()
