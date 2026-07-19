import json
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

from scripts import generate_factorial_prompt_scenarios as generator


PROMPTS = ["natural", "weak_security", "expert", "threat_modeling"]
PLACEHOLDERS = {
    "{scenario_title}",
    "{scenario_description}",
    "{openapi_schema}",
    "{text_spec}",
    "{scenario_instructions}",
}


class PromptVariantTests(unittest.TestCase):
    def test_tracked_prompt_templates_have_required_placeholders_and_newlines(self):
        variants = generator.load_prompt_variants(ROOT / "prompt_variants")

        self.assertEqual(list(variants), PROMPTS)
        for prompt_id, variant in variants.items():
            with self.subTest(prompt_id=prompt_id):
                self.assertTrue(variant["template"].strip())
                self.assertIn("\n", variant["template"])
                self.assertTrue(
                    all(
                        placeholder in variant["template"]
                        for placeholder in PLACEHOLDERS
                    )
                )

    def test_loader_rejects_empty_or_incomplete_prompt_templates(self):
        with tempfile.TemporaryDirectory() as directory:
            variants_dir = Path(directory)
            for prompt_id in PROMPTS:
                (variants_dir / f"{prompt_id}.json").write_text(
                    json.dumps(
                        {
                            "id": prompt_id,
                            "template": "\n".join(sorted(PLACEHOLDERS)),
                        }
                    ),
                    encoding="utf-8",
                )
            (variants_dir / "natural.json").write_text(
                json.dumps({"id": "natural", "template": ""}), encoding="utf-8"
            )

            with self.assertRaisesRegex(ValueError, "nonempty template"):
                generator.load_prompt_variants(variants_dir)

    def test_generic_generator_refuses_protected_output_and_manifest_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seeds_dir = root / "seeds"
            seed_file = seeds_dir / "beginner" / "example.json"
            seed_file.parent.mkdir(parents=True)
            seed_file.write_text(
                json.dumps({"title": "ExampleScenario"}), encoding="utf-8"
            )
            artifacts_dir = root / "artifacts"
            base = artifacts_dir / "ExampleScenario" / "ExampleScenario_iw0.py"
            base.parent.mkdir(parents=True)
            base.write_text("SCENARIO = Scenario()\n", encoding="utf-8")
            output_dir = artifacts_dir / "factorial_prompt_scenarios"
            output_dir.mkdir()
            output_sentinel = output_dir / "keep.txt"
            output_sentinel.write_bytes(b"protected output\n")
            manifest_path = artifacts_dir / "factorial_prompt_manifest.json"
            manifest_path.write_bytes(b"protected manifest\n")

            with self.assertRaisesRegex(ValueError, "overwrite"):
                generator.generate_factorial_prompt_scenarios(
                    seeds_dir=seeds_dir,
                    artifacts_dir=artifacts_dir,
                    prompt_variants_dir=ROOT / "prompt_variants",
                    output_dir=output_dir,
                    manifest_path=manifest_path,
                )

            self.assertEqual(output_sentinel.read_bytes(), b"protected output\n")
            self.assertEqual(manifest_path.read_bytes(), b"protected manifest\n")

    def test_generic_generator_rejects_output_child_symlink_even_with_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seeds_dir = root / "seeds"
            seed_file = seeds_dir / "beginner" / "example.json"
            seed_file.parent.mkdir(parents=True)
            seed_file.write_text(
                json.dumps({"title": "ExampleScenario"}), encoding="utf-8"
            )
            artifacts_dir = root / "artifacts"
            base = artifacts_dir / "ExampleScenario" / "ExampleScenario_iw0.py"
            base.parent.mkdir(parents=True)
            base.write_text("SCENARIO = Scenario()\n", encoding="utf-8")
            output_dir = artifacts_dir / "factorial_prompt_scenarios"
            output_dir.mkdir()
            outside = root / "outside"
            outside.mkdir()
            try:
                (output_dir / "ExampleScenario").symlink_to(
                    outside, target_is_directory=True
                )
            except OSError as error:
                self.skipTest(f"symlinks unavailable: {error}")

            with self.assertRaisesRegex(ValueError, "symlink"):
                generator.generate_factorial_prompt_scenarios(
                    seeds_dir=seeds_dir,
                    artifacts_dir=artifacts_dir,
                    prompt_variants_dir=ROOT / "prompt_variants",
                    output_dir=output_dir,
                    manifest_path=artifacts_dir / "scratch.json",
                    overwrite=True,
                )

            self.assertEqual(list(outside.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
