import ast
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scripts import audit_taxonomy_expansion as audit
from scripts import generate_taxonomy_expansion_wrappers as generator
from scripts.generate_factorial_prompt_scenarios import (
    PROMPT_CATEGORY_INSTRUCTIONS,
    PROMPT_ORDER,
    load_prompt_variants,
    wrapper_source,
)


PROMPT_VARIANTS = ROOT / "prompt_variants"
PROMPTS = ("natural", "weak_security", "expert", "threat_modeling")


class ExpansionWrapperTests(unittest.TestCase):
    def create_layout(self, root: Path, *, write_bases: bool = True) -> dict[str, Path]:
        seeds_dir = root / "seeds"
        artifacts_dir = root / "artifacts"
        output_dir = artifacts_dir / "factorial_prompt_scenarios_expansion_v1_2"
        manifest_path = artifacts_dir / "factorial_prompt_manifest_expansion_v1_2.json"
        audit_json_path = artifacts_dir / "TAXONOMY_EXPANSION_V1_2_AUDIT.json"
        audit_markdown_path = artifacts_dir / "TAXONOMY_EXPANSION_V1_2_AUDIT.md"

        for level in ("beginner", "complex"):
            (seeds_dir / level).mkdir(parents=True)
            for index in range(4):
                title = f"{level.title()}Scenario{index}"
                seed = {
                    "title": title,
                    "description": f"{level} expansion scenario {index}",
                    "needs_db": level == "complex",
                    "needs_secret": level == "complex",
                    "taxonomy": {
                        "scenario_level": level,
                        "domain": "web_app",
                        "task_type": f"task_{index}",
                        "prompt_category": "natural",
                        "expansion_batch": "v1_2",
                    },
                    "target_cwes": ["CWE-20"],
                    "generation_notes": ["one", "two", "three", "four"],
                    "scenario_instructions": "",
                    "oracle_contract": {"case": index, "level": level},
                }
                (seeds_dir / level / f"{title}.json").write_text(
                    json.dumps(seed, indent=2) + "\n", encoding="utf-8"
                )
                if write_bases:
                    base_path = artifacts_dir / title / f"{title}_iw0.py"
                    base_path.parent.mkdir(parents=True, exist_ok=True)
                    base_path.write_text(
                        "SCENARIO = Scenario(id='x', api_spec=None, text_spec='', "
                        "short_app_description='', needs_db=False, needs_secret=False, "
                        "scenario_instructions='', functional_tests=[], security_tests=[])\n",
                        encoding="utf-8",
                    )

        return {
            "seeds_dir": seeds_dir,
            "artifacts_dir": artifacts_dir,
            "output_dir": output_dir,
            "manifest_path": manifest_path,
            "audit_json_path": audit_json_path,
            "audit_markdown_path": audit_markdown_path,
        }

    def generate(self, layout: dict[str, Path]) -> list[dict]:
        return generator.generate_expansion_wrappers(
            seeds_dir=layout["seeds_dir"],
            artifacts_dir=layout["artifacts_dir"],
            prompt_variants_dir=PROMPT_VARIANTS,
            output_dir=layout["output_dir"],
            manifest_path=layout["manifest_path"],
        )

    def audit(self, layout: dict[str, Path], *, seeds_only: bool = False) -> dict:
        return audit.audit_taxonomy_expansion(
            seeds_dir=layout["seeds_dir"],
            artifacts_dir=layout["artifacts_dir"],
            prompt_variants_dir=PROMPT_VARIANTS,
            output_dir=layout["output_dir"],
            manifest_path=layout["manifest_path"],
            audit_json_path=layout["audit_json_path"],
            audit_markdown_path=layout["audit_markdown_path"],
            seeds_only=seeds_only,
        )

    def manifest_file(self, layout: dict[str, Path], entry: dict, key: str) -> Path:
        return layout["manifest_path"].parent / entry[key]

    def write_wrapper(self, layout: dict[str, Path], entry: dict, source: str) -> None:
        path = self.manifest_file(layout, entry, "variant_scenario_file")
        path.write_text(source, encoding="utf-8")
        entry["wrapper_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()

    def test_generates_complete_matrix_and_audits_cleanly(self):
        with tempfile.TemporaryDirectory() as directory:
            layout = self.create_layout(Path(directory))
            entries = self.generate(layout)
            report = self.audit(layout)

            self.assertEqual(len(entries), 32)
            self.assertEqual(len(json.loads(layout["manifest_path"].read_text())), 32)
            self.assertEqual(report["errors"], [])
            self.assertEqual(
                report["seed_report"]["level_counts"], {"beginner": 4, "complex": 4}
            )
            for entry in entries:
                self.assertEqual(entry["benchmark_version"], "taxonomy_expansion_v1_2")
                self.assertEqual(entry["expansion_batch"], "v1_2")
                self.assertEqual(
                    entry["varied_variables"], ["scenario_id", "scenario_instructions"]
                )
                self.assertIn("base_scenario_sha256", entry)
                self.assertIn("wrapper_sha256", entry)

            for title in {entry["base_scenario"] for entry in entries}:
                wrappers = sorted((layout["output_dir"] / title).glob("*.py"))
                self.assertEqual(len(wrappers), 4)
                self.assertEqual(
                    {path.stem.rsplit("__", 1)[1] for path in wrappers}, set(PROMPTS)
                )

    def test_generator_rejects_missing_or_invalid_base_without_output(self):
        with tempfile.TemporaryDirectory() as directory:
            layout = self.create_layout(Path(directory), write_bases=False)
            with self.assertRaisesRegex(ValueError, "Missing base scenario"):
                self.generate(layout)
            self.assertFalse(layout["output_dir"].exists())
            self.assertFalse(layout["manifest_path"].exists())

            layout = self.create_layout(Path(directory) / "invalid")
            base = next(layout["artifacts_dir"].glob("*/*_iw0.py"))
            base.write_text("not valid python", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid Python"):
                self.generate(layout)

            for invalid_source in ("SCENARIO = None\n", "SCENARIO = object()\n"):
                base.write_text(invalid_source, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Scenario"):
                    self.generate(layout)

    def test_generator_rejects_output_that_contains_artifacts_and_preserves_bases(self):
        with tempfile.TemporaryDirectory() as directory:
            layout = self.create_layout(Path(directory))
            before = {
                path: path.read_bytes()
                for path in layout["artifacts_dir"].glob("*/*_iw0.py")
            }
            with self.assertRaisesRegex(ValueError, "protected input root"):
                generator.generate_expansion_wrappers(
                    seeds_dir=layout["seeds_dir"],
                    artifacts_dir=layout["artifacts_dir"],
                    prompt_variants_dir=PROMPT_VARIANTS,
                    output_dir=layout["artifacts_dir"],
                    manifest_path=layout["manifest_path"],
                )
            self.assertEqual({path: path.read_bytes() for path in before}, before)

    def test_manifest_and_wrapper_sources_are_root_independent_and_relative(self):
        with tempfile.TemporaryDirectory() as directory:
            first = self.create_layout(Path(directory) / "first")
            second = self.create_layout(Path(directory) / "second")
            self.generate(first)
            self.generate(second)

            self.assertEqual(
                first["manifest_path"].read_bytes(),
                second["manifest_path"].read_bytes(),
            )
            first_wrappers = {
                path.relative_to(first["output_dir"]): path.read_bytes()
                for path in first["output_dir"].rglob("*.py")
            }
            second_wrappers = {
                path.relative_to(second["output_dir"]): path.read_bytes()
                for path in second["output_dir"].rglob("*.py")
            }
            self.assertEqual(first_wrappers, second_wrappers)
            manifest = json.loads(first["manifest_path"].read_text())
            for entry in manifest:
                for key in (
                    "base_seed_file",
                    "base_scenario_file",
                    "variant_scenario_file",
                ):
                    self.assertFalse(Path(entry[key]).is_absolute())
                    self.assertNotIn("\\", entry[key])
            wrapper = next(first["output_dir"].rglob("*.py"))
            source = wrapper.read_text(encoding="utf-8")
            tree = ast.parse(source)
            assignment = next(
                node
                for node in tree.body
                if isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "_BASE_SCENARIO_DIR"
                    for target in node.targets
                )
            )
            relative_base = next(
                node.value
                for node in ast.walk(assignment.value)
                if isinstance(node, ast.Constant) and isinstance(node.value, str)
            )
            self.assertTrue((wrapper.parent / relative_base).resolve().is_dir())
            self.assertEqual(self.audit(first)["errors"], [])

    def test_transaction_failure_preserves_prior_output_and_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            layout = self.create_layout(Path(directory))
            self.generate(layout)
            before_manifest = layout["manifest_path"].read_bytes()
            before_output = {
                path.relative_to(layout["output_dir"]): path.read_bytes()
                for path in layout["output_dir"].rglob("*")
                if path.is_file()
            }
            original_write = generator._write_text_atomically
            calls = 0

            def fail_second_stage_write(path, text):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected stage write failure")
                original_write(path, text)

            with patch.object(
                generator, "_write_text_atomically", side_effect=fail_second_stage_write
            ), self.assertRaisesRegex(OSError, "injected"):
                self.generate(layout)

            self.assertEqual(layout["manifest_path"].read_bytes(), before_manifest)
            self.assertEqual(
                {
                    path.relative_to(layout["output_dir"]): path.read_bytes()
                    for path in layout["output_dir"].rglob("*")
                    if path.is_file()
                },
                before_output,
            )
            self.assertEqual(
                list(
                    layout["output_dir"].parent.glob(
                        ".factorial_prompt_scenarios_expansion_v1_2.staging-*"
                    )
                ),
                [],
            )

    def test_generator_rejects_output_symlink_and_audit_rejects_stale_wrapper(self):
        with tempfile.TemporaryDirectory() as directory:
            layout = self.create_layout(Path(directory))
            outside = Path(directory) / "outside"
            outside.mkdir()
            layout["output_dir"].mkdir()
            link = layout["output_dir"] / "BeginnerScenario0"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"symlinks unavailable: {error}")
            with self.assertRaisesRegex(ValueError, "symlink"):
                self.generate(layout)

        with tempfile.TemporaryDirectory() as directory:
            layout = self.create_layout(Path(directory))
            self.generate(layout)
            (layout["output_dir"] / "stale.py").write_text(
                "SCENARIO = Scenario()\n", encoding="utf-8"
            )
            self.assertTrue(self.audit(layout)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            layout = self.create_layout(Path(directory))
            self.generate(layout)
            next(layout["output_dir"].rglob("*.py")).unlink()
            self.assertTrue(self.audit(layout)["errors"])

    def test_audit_survives_manifest_path_symlink_loop_and_writes_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            layout = self.create_layout(Path(directory))
            entries = self.generate(layout)
            loop = layout["manifest_path"].parent / "loop"
            try:
                loop.symlink_to(loop.name)
            except OSError as error:
                self.skipTest(f"symlinks unavailable: {error}")
            entries[0]["base_scenario_file"] = "loop/base.py"
            layout["manifest_path"].write_text(json.dumps(entries), encoding="utf-8")
            report = self.audit(layout)

            self.assertTrue(report["errors"])
            self.assertTrue(layout["audit_json_path"].is_file())
            self.assertTrue(layout["audit_markdown_path"].is_file())

    def test_audit_detects_hash_extra_row_metadata_drift_and_path_escape(self):
        cases = {
            "hash": lambda entries, layout: entries[0].__setitem__(
                "wrapper_sha256", "0" * 64
            ),
            "extra": lambda entries, layout: entries.append(dict(entries[0])),
            "metadata": lambda entries, layout: entries[0].__setitem__(
                "target_cwes", ["CWE-22"]
            ),
            "escape": lambda entries, layout: entries[0].__setitem__(
                "variant_scenario_file",
                str(layout["artifacts_dir"].parent / "escape.py"),
            ),
        }
        for name, mutate in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                layout = self.create_layout(Path(directory))
                entries = self.generate(layout)
                mutate(entries, layout)
                layout["manifest_path"].write_text(
                    json.dumps(entries), encoding="utf-8"
                )
                report = self.audit(layout)
                self.assertTrue(report["errors"])

    def test_seed_only_audit_works_without_base_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            layout = {
                "seeds_dir": ROOT / "seeds",
                "artifacts_dir": root / "no-artifacts",
                "output_dir": root / "no-artifacts/wrappers",
                "manifest_path": root / "no-artifacts/manifest.json",
                "audit_json_path": root / "audit.json",
                "audit_markdown_path": root / "audit.md",
            }
            report = self.audit(layout, seeds_only=True)

        self.assertEqual(report["errors"], [])
        self.assertEqual(report["seed_report"]["seed_count"], 8)

    def test_generator_is_cwd_independent_and_does_not_touch_v1_manifests(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            layout = self.create_layout(project)
            sentinels = {
                layout["artifacts_dir"]
                / "factorial_prompt_manifest.json": b"v1 sentinel\n",
                layout["artifacts_dir"]
                / "factorial_prompt_manifest_v1_1.json": b"v1_1 sentinel\n",
            }
            before = {}
            for path, contents in sentinels.items():
                path.write_bytes(contents)
                before[path] = (
                    contents,
                    hashlib.sha256(contents).hexdigest(),
                    path.stat().st_ino,
                )
            original_cwd = Path.cwd()
            try:
                os.chdir(Path(directory))
                self.generate(layout)
                report = self.audit(layout)
                self.assertEqual(report["errors"], [])
                for path, (contents, digest, inode) in before.items():
                    self.assertEqual(path.read_bytes(), contents)
                    self.assertEqual(
                        hashlib.sha256(path.read_bytes()).hexdigest(), digest
                    )
                    self.assertEqual(path.stat().st_ino, inode)
            finally:
                os.chdir(original_cwd)

    def test_audit_detects_semantic_base_and_wrapper_mutations(self):
        cases = (
            ("corrupt base Python", self._corrupt_base_python),
            ("base missing SCENARIO", self._base_without_scenario),
            ("corrupt wrapper Python", self._corrupt_wrapper_python),
            ("wrapper missing SCENARIO", self._wrapper_without_scenario),
            ("wrong scenario id", self._wrong_scenario_id),
            ("wrong scenario instructions", self._wrong_scenario_instructions),
            ("wrong intended base import", self._wrong_base_import),
        )
        for name, mutate in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                layout = self.create_layout(Path(directory))
                entries = self.generate(layout)
                mutate(layout, entries)
                layout["manifest_path"].write_text(
                    json.dumps(entries), encoding="utf-8"
                )
                report = self.audit(layout)
                self.assertTrue(report["errors"])

    def test_audit_reports_wrapper_source_scenario_id_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            layout = self.create_layout(Path(directory))
            entries = self.generate(layout)
            entry = self._entry_for_prompt(entries)
            self.write_wrapper(
                layout,
                entry,
                wrapper_source(
                    base_title=entry["base_scenario"],
                    base_module_name=f"{entry['base_scenario']}_iw0",
                    base_relative_path="../unused",
                    scenario_id="IncorrectScenario__natural",
                    scenario_instructions=PROMPT_CATEGORY_INSTRUCTIONS[
                        entry["prompt_category"]
                    ],
                ),
            )
            layout["manifest_path"].write_text(json.dumps(entries), encoding="utf-8")
            report = self.audit(layout)

        self.assertIn(
            "manifest row 0 wrapper SCENARIO id does not match expected id",
            report["errors"],
        )

    def _entry_for_prompt(
        self, entries: list[dict], prompt_id: str = "natural"
    ) -> dict:
        return next(entry for entry in entries if entry["prompt_category"] == prompt_id)

    def _corrupt_base_python(
        self, layout: dict[str, Path], entries: list[dict]
    ) -> None:
        entry = self._entry_for_prompt(entries)
        self.manifest_file(layout, entry, "base_scenario_file").write_text(
            "not valid Python", encoding="utf-8"
        )

    def _base_without_scenario(
        self, layout: dict[str, Path], entries: list[dict]
    ) -> None:
        entry = self._entry_for_prompt(entries)
        self.manifest_file(layout, entry, "base_scenario_file").write_text(
            "value = 1\n", encoding="utf-8"
        )

    def _corrupt_wrapper_python(
        self, layout: dict[str, Path], entries: list[dict]
    ) -> None:
        entry = self._entry_for_prompt(entries)
        self.write_wrapper(layout, entry, "not valid Python")

    def _wrapper_without_scenario(
        self, layout: dict[str, Path], entries: list[dict]
    ) -> None:
        entry = self._entry_for_prompt(entries)
        self.write_wrapper(layout, entry, "value = 1\n")

    def _wrong_scenario_id(self, layout: dict[str, Path], entries: list[dict]) -> None:
        entry = self._entry_for_prompt(entries)
        entry["scenario_id"] = "IncorrectScenario__natural"

    def _wrong_scenario_instructions(
        self, layout: dict[str, Path], entries: list[dict]
    ) -> None:
        entry = self._entry_for_prompt(entries, "weak_security")
        self.write_wrapper(
            layout,
            entry,
            wrapper_source(
                base_title=entry["base_scenario"],
                base_module_name=f"{entry['base_scenario']}_iw0",
                base_relative_path="../unused",
                scenario_id=entry["scenario_id"],
                scenario_instructions="incorrect instructions",
            ),
        )

    def _wrong_base_import(self, layout: dict[str, Path], entries: list[dict]) -> None:
        entry = self._entry_for_prompt(entries)
        self.write_wrapper(
            layout,
            entry,
            wrapper_source(
                base_title=entry["base_scenario"],
                base_module_name=f"{entry['base_scenario']}_incorrect",
                base_relative_path="../unused",
                scenario_id=entry["scenario_id"],
                scenario_instructions=PROMPT_CATEGORY_INSTRUCTIONS[
                    entry["prompt_category"]
                ],
            ),
        )

    def test_prompt_variant_dependency_has_expected_order_and_helpers(self):
        self.assertEqual(PROMPT_ORDER, list(PROMPTS))
        variants = load_prompt_variants(PROMPT_VARIANTS)
        self.assertEqual(list(variants), list(PROMPTS))
        source = wrapper_source(
            base_title="ExampleScenario",
            base_module_name="ExampleScenario_iw0",
            base_relative_path="../ExampleScenario",
            scenario_id="ExampleScenario__natural",
            scenario_instructions="",
        )
        self.assertIn("import importlib", source)
        self.assertIn("ExampleScenario_iw0", source)
        with tempfile.TemporaryDirectory() as directory:
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT)
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from pathlib import Path; "
                    "from scripts.generate_factorial_prompt_scenarios import "
                    "PROMPT_ORDER, load_prompt_variants, wrapper_source; "
                    "assert PROMPT_ORDER == ['natural', 'weak_security', 'expert', "
                    "'threat_modeling']; "
                    "assert list(load_prompt_variants(Path(__import__('sys').argv[1]))) "
                    "== PROMPT_ORDER; "
                    "assert 'ExampleScenario_iw0' in wrapper_source("
                    "base_title='ExampleScenario', "
                    "base_module_name='ExampleScenario_iw0', "
                    "base_relative_path='../ExampleScenario', "
                    "scenario_id='ExampleScenario__natural', "
                    "scenario_instructions='')",
                    str(PROMPT_VARIANTS),
                ],
                cwd=directory,
                env=environment,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_seed_only_cli_is_cwd_independent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/audit_taxonomy_expansion.py"),
                    "--seeds-only",
                    "--artifacts-dir",
                    str(root / "no-artifacts"),
                    "--audit-json-path",
                    str(root / "audit.json"),
                    "--audit-markdown-path",
                    str(root / "audit.md"),
                ],
                cwd=root,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
