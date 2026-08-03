"""The eval runner must refuse to start on settings that empty every sample.

Both settings guarded here have already cost a full sweep, and neither failed
loudly: a missing key and a 60-second generation timeout each produce a run that
exits 0, writes a results file per scenario, and logs nothing unusual -- the
files just contain no results. Checking them before the run is the only point
where the failure is cheap.
"""

import importlib.util
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "run_factorial_smoke_eval", REPO / "scripts" / "run_factorial_smoke_eval.py"
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class PreflightTests(unittest.TestCase):
    def preflight(self, env: dict, env_file_text: str | None = None):
        with TemporaryDirectory() as tmp, patch.dict(os.environ, env, clear=True):
            path = Path(tmp) / ".env"
            if env_file_text is not None:
                path.write_text(env_file_text, encoding="utf-8")
            runner.preflight(path)
            return dict(os.environ)

    def test_missing_key_is_refused(self):
        with self.assertRaises(SystemExit) as caught:
            self.preflight({"OPENAI_TIMEOUT": "1200"})
        self.assertIn("OPENAI_API_KEY", str(caught.exception))

    def test_timeout_below_the_floor_is_refused_even_though_it_is_set(self):
        # The specific trap: .env carries OPENAI_TIMEOUT=60, so a presence check
        # passes and most samples still come back empty.
        with self.assertRaises(SystemExit) as caught:
            self.preflight({"OPENAI_API_KEY": "k", "OPENAI_TIMEOUT": "60"})
        self.assertIn("600", str(caught.exception))

    def test_unset_timeout_is_refused(self):
        with self.assertRaises(SystemExit):
            self.preflight({"OPENAI_API_KEY": "k"})

    def test_env_file_supplies_values_the_shell_did_not_export(self):
        env = self.preflight(
            {}, 'export OPENAI_API_KEY="from-file"\nOPENAI_TIMEOUT=1200\n'
        )
        self.assertEqual(env["OPENAI_API_KEY"], "from-file")

    def test_exported_values_win_over_the_env_file(self):
        env = self.preflight(
            {"OPENAI_API_KEY": "exported", "OPENAI_TIMEOUT": "1200"},
            "export OPENAI_API_KEY=from-file\nexport OPENAI_TIMEOUT=60\n",
        )
        self.assertEqual(env["OPENAI_API_KEY"], "exported")
        self.assertEqual(env["OPENAI_TIMEOUT"], "1200")

    def test_comments_and_blank_lines_are_ignored(self):
        env = self.preflight(
            {}, "# a comment\n\nexport OPENAI_API_KEY=k\nOPENAI_TIMEOUT=1200\n"
        )
        self.assertEqual(env["OPENAI_API_KEY"], "k")

    def test_a_sufficient_timeout_passes(self):
        env = self.preflight({"OPENAI_API_KEY": "k", "OPENAI_TIMEOUT": "1200"})
        self.assertEqual(env["OPENAI_TIMEOUT"], "1200")


if __name__ == "__main__":
    unittest.main()
