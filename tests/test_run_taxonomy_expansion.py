import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scripts import run_taxonomy_expansion as runner


class TaxonomyExpansionRunnerTests(unittest.TestCase):
    def write_seed(self, directory, title):
        path = Path(directory) / f"{title}.json"
        path.write_text(json.dumps({"title": title}), encoding="utf-8")
        return path

    def expansion_seeds(self, directory, count=8):
        return [
            (
                self.write_seed(directory, f"Scenario{index}"),
                {"title": f"Scenario{index}"},
            )
            for index in range(count)
        ]

    def valid_report(self):
        return {"errors": []}

    def test_commands_for_seed_have_the_required_order_and_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            seed_file = self.write_seed(directory, "ExampleScenario")
            artifacts_dir = Path(directory) / "artifacts"

            commands = runner.commands_for_seed(
                seed_file, artifacts_dir, 3, "/custom/python"
            )

        self.assertEqual(
            commands,
            [
                [
                    "/custom/python",
                    "src/main.py",
                    "--generate_scenarios",
                    "--seed_file",
                    str(seed_file),
                    "--path",
                    str(artifacts_dir),
                    "--difficulty",
                    "3",
                ],
                [
                    "/custom/python",
                    "src/main.py",
                    "--generate_tests",
                    "--scenario",
                    "ExampleScenario",
                ],
                [
                    "/custom/python",
                    "src/main.py",
                    "--generate_exploits",
                    "--scenario",
                    "ExampleScenario",
                ],
            ],
        )

    def test_resume_marks_every_artifact_combination_correctly(self):
        expected = {
            (False, False, False): ["passed", "passed", "passed"],
            (True, False, False): ["skipped", "passed", "passed"],
            (False, True, False): ["skipped", "skipped", "passed"],
            (False, False, True): ["skipped", "skipped", "skipped"],
            (True, True, False): ["skipped", "skipped", "passed"],
            (True, False, True): ["skipped", "skipped", "skipped"],
            (False, True, True): ["skipped", "skipped", "skipped"],
            (True, True, True): ["skipped", "skipped", "skipped"],
        }

        for artifacts in expected:
            with self.subTest(
                artifacts=artifacts
            ), tempfile.TemporaryDirectory() as directory:
                seed_file = self.write_seed(directory, "ExampleScenario")
                artifacts_dir = Path(directory) / "artifacts"
                scenario_dir = artifacts_dir / "ExampleScenario"
                scenario_dir.mkdir(parents=True)
                if artifacts[0]:
                    (scenario_dir / "ExampleScenario.json").touch()
                if artifacts[1]:
                    (scenario_dir / "ExampleScenario_iu0.py").touch()
                if artifacts[2]:
                    (scenario_dir / "ExampleScenario_iw0.py").touch()
                calls = []

                result = runner.run_seed(
                    seed_file=seed_file,
                    title="ExampleScenario",
                    artifacts_dir=artifacts_dir,
                    difficulty=3,
                    python_executable=sys.executable,
                    dry_run=False,
                    runner=lambda argv, **kwargs: calls.append(argv)
                    or SimpleNamespace(returncode=0),
                    monotonic=lambda: 1.0,
                )

                self.assertEqual(
                    [stage["status"] for stage in result["stages"]], expected[artifacts]
                )
                self.assertEqual(len(calls), expected[artifacts].count("passed"))

    def test_dry_run_plans_all_24_commands_without_creating_artifact_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts_dir = root / "artifacts"
            status_path = root / "status" / "report.json"
            seeds = self.expansion_seeds(root)
            args = runner.parse_args(
                [
                    "--artifacts-dir",
                    str(artifacts_dir),
                    "--status-path",
                    str(status_path),
                    "--dry-run",
                ]
            )
            output = io.StringIO()
            with patch.object(
                runner, "discover_expansion_seeds", return_value=seeds
            ), patch.object(
                runner, "validate_expansion_seeds", return_value=self.valid_report()
            ), contextlib.redirect_stdout(
                output
            ):
                exit_code = runner.run_batch(args)
            report = json.loads(status_path.read_text(encoding="utf-8"))

            self.assertEqual(exit_code, 0)
            self.assertFalse(artifacts_dir.exists())
            self.assertEqual(len(output.getvalue().splitlines()), 24)
            self.assertEqual(report["aggregate"]["stages"]["planned"], 24)
            self.assertEqual(report["aggregate"]["stages"]["failed"], 0)
            self.assertTrue(
                all(
                    stage["status"] == "planned"
                    for seed in report["seeds"]
                    for stage in seed["stages"]
                )
            )

    def test_failure_stops_only_its_seed_and_other_workers_continue(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seeds = self.expansion_seeds(root)
            status_path = root / "report.json"
            args = runner.parse_args(
                [
                    "--artifacts-dir",
                    str(root / "artifacts"),
                    "--status-path",
                    str(status_path),
                    "--parallel",
                    "2",
                ]
            )
            calls = []

            def fake_runner(argv, **kwargs):
                calls.append(argv)
                if "Scenario0" in argv and "--generate_tests" in argv:
                    return SimpleNamespace(returncode=9)
                return SimpleNamespace(returncode=0)

            with patch.object(
                runner, "discover_expansion_seeds", return_value=seeds
            ), patch.object(
                runner, "validate_expansion_seeds", return_value=self.valid_report()
            ):
                exit_code = runner.run_batch(args, command_runner=fake_runner)
            report = json.loads(status_path.read_text(encoding="utf-8"))

            self.assertEqual(exit_code, 1)
            first = report["seeds"][0]
            self.assertEqual(
                [stage["status"] for stage in first["stages"]],
                ["passed", "failed", "skipped"],
            )
            self.assertEqual(first["stages"][1]["exit_code"], 9)
            self.assertEqual(report["seeds"][1]["stages"][-1]["status"], "passed")
            self.assertFalse(
                any(
                    "Scenario0" in command and "--generate_exploits" in command
                    for command in calls
                )
            )
            self.assertTrue(any("Scenario1" in command for command in calls))

    def test_invalid_parallel_is_rejected(self):
        for value in ("0", "9"):
            with self.subTest(value=value):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(
                    SystemExit
                ):
                    runner.parse_args(["--parallel", value])

    def test_validation_errors_refuse_both_live_and_dry_run(self):
        for dry_run in (False, True):
            with self.subTest(
                dry_run=dry_run
            ), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                status_path = root / "report.json"
                args_list = ["--status-path", str(status_path)]
                if dry_run:
                    args_list.append("--dry-run")
                args = runner.parse_args(args_list)
                with patch.object(
                    runner, "discover_expansion_seeds", return_value=[]
                ), patch.object(
                    runner,
                    "validate_expansion_seeds",
                    return_value={"errors": ["bad seed"]},
                ), patch.object(
                    runner, "run_seed"
                ) as run_seed:
                    with contextlib.redirect_stderr(io.StringIO()):
                        exit_code = runner.run_batch(args)

                self.assertEqual(exit_code, 2)
                run_seed.assert_not_called()
                self.assertFalse(status_path.exists())

    def test_status_is_seed_ordered_and_does_not_capture_environment_values(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seeds = list(reversed(self.expansion_seeds(root)))
            status_path = root / "report.json"
            args = runner.parse_args(
                [
                    "--status-path",
                    str(status_path),
                    "--artifacts-dir",
                    str(root / "artifacts"),
                ]
            )
            with patch.dict(os.environ, {"API_KEY": "never-report-this"}), patch.object(
                runner, "discover_expansion_seeds", return_value=seeds
            ), patch.object(
                runner, "validate_expansion_seeds", return_value=self.valid_report()
            ):
                exit_code = runner.run_batch(
                    args,
                    command_runner=lambda argv, **kwargs: SimpleNamespace(returncode=0),
                    now=lambda: "2026-07-19T00:00:00+00:00",
                    monotonic=lambda: 1.0,
                )
            serialized = status_path.read_text(encoding="utf-8")
            report = json.loads(serialized)

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                [seed["title"] for seed in report["seeds"]],
                [f"Scenario{index}" for index in range(8)],
            )
            self.assertNotIn("never-report-this", serialized)
            self.assertNotIn("API_KEY", serialized)
            self.assertEqual(report["started_at"], "2026-07-19T00:00:00+00:00")
            self.assertEqual(report["finished_at"], "2026-07-19T00:00:00+00:00")

    def test_execution_uses_repository_root_when_called_from_another_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seed_file = self.write_seed(root, "ExampleScenario")
            observed = {}
            previous_directory = Path.cwd()
            try:
                os.chdir(root)
                runner.run_seed(
                    seed_file=seed_file,
                    title="ExampleScenario",
                    artifacts_dir=root / "artifacts",
                    difficulty=3,
                    python_executable=sys.executable,
                    dry_run=False,
                    runner=lambda argv, **kwargs: observed.update(kwargs)
                    or SimpleNamespace(returncode=0),
                    monotonic=lambda: 1.0,
                )
            finally:
                os.chdir(previous_directory)

        self.assertEqual(observed["cwd"], ROOT)

    def test_default_seed_directory_is_cwd_independent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            status_path = root / "report.json"
            previous_directory = Path.cwd()
            try:
                os.chdir(root)
                args = runner.parse_args(
                    ["--dry-run", "--status-path", str(status_path)]
                )
                with contextlib.redirect_stderr(
                    io.StringIO()
                ), contextlib.redirect_stdout(io.StringIO()):
                    exit_code = runner.run_batch(args)
            finally:
                os.chdir(previous_directory)

            report = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(report["seeds"]), 8)


if __name__ == "__main__":
    unittest.main()
