import contextlib
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
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

            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
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

            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                config.initialize_config(
                    [
                        "--generate_scenarios",
                        "--seed_file",
                        str(Path(directory) / "missing.json"),
                        "--path",
                        str(artifacts),
                    ]
                )


if __name__ == "__main__":
    unittest.main()
