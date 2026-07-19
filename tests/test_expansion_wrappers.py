import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scripts import audit_taxonomy_expansion as audit
from scripts import generate_taxonomy_expansion_wrappers as generator


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
                    base_path.write_text("SCENARIO = object()\n", encoding="utf-8")

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
        v1_manifest = ROOT / "artifacts" / "factorial_prompt_manifest.json"
        v1_1_manifest = ROOT / "artifacts" / "factorial_prompt_manifest_v1_1.json"
        before = {
            path: path.read_bytes()
            for path in (v1_manifest, v1_1_manifest)
            if path.exists()
        }
        with tempfile.TemporaryDirectory() as directory:
            layout = self.create_layout(Path(directory))
            original_cwd = Path.cwd()
            try:
                os.chdir(Path(directory))
                self.generate(layout)
                report = self.audit(layout)
            finally:
                os.chdir(original_cwd)

        self.assertEqual(report["errors"], [])
        self.assertEqual({path: path.read_bytes() for path in before}, before)

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
