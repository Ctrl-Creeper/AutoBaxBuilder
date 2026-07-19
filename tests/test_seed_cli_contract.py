import contextlib
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

models_stub = types.ModuleType("models")
models_stub.__path__ = [str(SRC / "models")]
models_stub.get_model = lambda *args, **kwargs: object()
sys.modules["models"] = models_stub

from agent import config
from agent import generate_scenarios


class SeedCliContractTests(unittest.TestCase):
    def setUp(self):
        self.original_initialized = config._initialized
        self.original_args = config.args
        self.original_scenario_folder_path = config.scenario_folder_path
        config._initialized = False
        config.args = None
        config.scenario_folder_path = None

    def tearDown(self):
        config._initialized = self.original_initialized
        config.args = self.original_args
        config.scenario_folder_path = self.original_scenario_folder_path

    def write_seed(self, directory):
        path = Path(directory) / "seed.json"
        seed = {
            "title": "SeedScenario",
            "description": "Preserve this seed metadata.",
            "needs_db": True,
            "needs_secret": False,
            "taxonomy": {"domain": "storage", "task_type": "import"},
            "target_cwes": ["CWE-20", "CWE-400"],
            "oracle_contract": {"max_items": 20},
        }
        path.write_text(json.dumps(seed), encoding="utf-8")
        return path, seed

    def test_seed_cli_accepts_scenario_generation_and_loads_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts = root / "artifacts"
            artifacts.mkdir()
            seed_path, seed = self.write_seed(root)

            parsed = config.initialize_config(
                [
                    "--generate_scenarios",
                    "--seed_file",
                    str(seed_path),
                    "--path",
                    str(artifacts),
                ]
            )
            with patch.object(generate_scenarios, "args", parsed):
                loaded = generate_scenarios.load_scenario_seed(str(seed_path))

        self.assertEqual(parsed.seed_file, str(seed_path))
        self.assertEqual(loaded["title"], seed["title"])
        self.assertEqual(loaded["taxonomy"], seed["taxonomy"])
        self.assertEqual(loaded["target_cwes"], seed["target_cwes"])
        self.assertEqual(loaded["oracle_contract"], seed["oracle_contract"])

    def test_seed_file_is_rejected_outside_scenario_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts = root / "artifacts"
            artifacts.mkdir()
            seed_path, _ = self.write_seed(root)

            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ):
                config.initialize_config(
                    [
                        "--generate_exploits",
                        "--scenario",
                        "Ignored",
                        "--seed_file",
                        str(seed_path),
                        "--path",
                        str(artifacts),
                    ]
                )

    def test_missing_seed_file_is_rejected_before_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            artifacts = Path(directory) / "artifacts"
            artifacts.mkdir()

            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ):
                config.initialize_config(
                    [
                        "--generate_scenarios",
                        "--seed_file",
                        str(Path(directory) / "missing.json"),
                        "--path",
                        str(artifacts),
                    ]
                )

    def test_seed_generation_prompt_includes_full_account_recovery_contract(self):
        seed_path = ROOT / "seeds" / "complex" / "account_recovery_natural.json"
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        with patch.object(generate_scenarios, "args", SimpleNamespace(difficulty=3)):
            loaded = generate_scenarios.load_scenario_seed(str(seed_path))

        prompt = loaded["_generation_description"]
        self.assertEqual(loaded["description"], seed["description"])
        self.assertIn("CWE-640", prompt)
        self.assertIn("900", prompt)
        self.assertIn("single-use", prompt)
        self.assertIn("digest", prompt)
        self.assertIn("CSPRNG", prompt)
        self.assertIn('"token_ttl_seconds": 900', prompt)

    def test_seed_save_restores_public_description_after_prompt_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts = root / "artifacts"
            artifacts.mkdir()
            seed_path, seed = self.write_seed(root)
            observed_descriptions = []
            specs = types.ModuleType("agent.generate_scenario_specs")

            def generate_openapi(scenario):
                observed_descriptions.append(scenario["description"])
                return {"openapi": "3.0.0"}

            def generate_text_spec(scenario):
                observed_descriptions.append(scenario["description"])
                return "text spec"

            specs.generate_openapi = generate_openapi
            specs.generate_text_spec = generate_text_spec
            generation_args = SimpleNamespace(
                seed_file=str(seed_path), path=str(artifacts), difficulty=3
            )
            with patch.dict(
                sys.modules, {"agent.generate_scenario_specs": specs}
            ), patch.object(generate_scenarios, "args", generation_args):
                generate_scenarios.generate_scenarios()

            saved = json.loads(
                (artifacts / "SeedScenario" / "SeedScenario.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertTrue(all("Target CWEs:" in value for value in observed_descriptions))
        self.assertEqual(saved["description"], seed["description"])


if __name__ == "__main__":
    unittest.main()
