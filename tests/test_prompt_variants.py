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
    SCENARIO_SOURCE = """from scenarios.base import Scenario

SCENARIO = Scenario(
    id='example', api_spec=None, text_spec='', short_app_description='',
    needs_db=False, needs_secret=False, scenario_instructions='',
    functional_tests=[], security_tests=[]
)
"""

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

    def test_loader_rejects_non_substituting_or_extended_format_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            variants_dir = Path(directory)
            template = "\n".join(sorted(PLACEHOLDERS))
            for prompt_id in PROMPTS:
                (variants_dir / f"{prompt_id}.json").write_text(
                    json.dumps({"id": prompt_id, "template": template}),
                    encoding="utf-8",
                )
            for invalid in (
                template + "\n{unknown}",
                template + "\n{scenario_title}",
                template.replace("{text_spec}", "{{text_spec}}"),
                template.replace("{text_spec}", "{text_spec!r}"),
                template.replace("{text_spec}", "{text_spec:20}"),
            ):
                (variants_dir / "natural.json").write_text(
                    json.dumps({"id": "natural", "template": invalid}),
                    encoding="utf-8",
                )
                with self.assertRaises(ValueError):
                    generator.load_prompt_variants(variants_dir)

    def test_strict_scenario_ast_uses_last_direct_assignment_with_all_keywords(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scenario.py"
            for invalid in (
                "SCENARIO = Scenario()\n",
                self.SCENARIO_SOURCE + "SCENARIO = None\n",
                self.SCENARIO_SOURCE.replace("Scenario(", "attacker.Scenario("),
                self.SCENARIO_SOURCE.replace("security_tests=[]", ""),
                self.SCENARIO_SOURCE.replace(
                    "id='example'", "'positional', id='example'"
                ),
                self.SCENARIO_SOURCE.replace("id='example'", "id='a', id='b'"),
                self.SCENARIO_SOURCE.replace(
                    "security_tests=[]", "security_tests=[], attacker=True"
                ),
                self.SCENARIO_SOURCE.replace(
                    "from scenarios.base import Scenario\n\n", ""
                ),
                self.SCENARIO_SOURCE.replace(
                    "from scenarios.base import Scenario",
                    "from attacker import Scenario",
                ),
                self.SCENARIO_SOURCE.replace(
                    "from scenarios.base import Scenario\n\n", ""
                )
                + "\nfrom scenarios.base import Scenario\n",
                self.SCENARIO_SOURCE.replace(
                    "\n\nSCENARIO", "\nScenario = None\n\nSCENARIO"
                ),
                self.SCENARIO_SOURCE.replace(
                    "\n\nSCENARIO", "\ndef Scenario():\n    pass\n\nSCENARIO"
                ),
                self.SCENARIO_SOURCE.replace(
                    "\n\nSCENARIO", "\nclass Scenario:\n    pass\n\nSCENARIO"
                ),
                self.SCENARIO_SOURCE.replace(
                    "\n\nSCENARIO", "\nScenario, other = (None, None)\n\nSCENARIO"
                ),
                self.SCENARIO_SOURCE.replace(
                    "\n\nSCENARIO", "\nfor Scenario in []:\n    pass\n\nSCENARIO"
                ),
                self.SCENARIO_SOURCE.replace(
                    "\n\nSCENARIO",
                    "\nwith open(__file__) as Scenario:\n    pass\n\nSCENARIO",
                ),
                self.SCENARIO_SOURCE.replace(
                    "\n\nSCENARIO", "\ndel Scenario\n\nSCENARIO"
                ),
                self.SCENARIO_SOURCE.replace(
                    "\n\nSCENARIO", "\nif True:\n    Scenario = None\n\nSCENARIO"
                ),
                self.SCENARIO_SOURCE.replace(
                    "\n\nSCENARIO",
                    "\ntry:\n    pass\nexcept Exception as Scenario:\n    pass\n\nSCENARIO",
                ),
                self.SCENARIO_SOURCE.replace(
                    "\n\nSCENARIO",
                    "\n@((Scenario := object()))\ndef helper():\n    pass\n\nSCENARIO",
                ),
                self.SCENARIO_SOURCE.replace(
                    "\n\nSCENARIO",
                    "\ndef helper(value=(Scenario := None)):\n    pass\n\nSCENARIO",
                ),
                self.SCENARIO_SOURCE.replace(
                    "\n\nSCENARIO",
                    "\nclass Helper((Scenario := object())):\n    pass\n\nSCENARIO",
                ),
                self.SCENARIO_SOURCE.replace(
                    "\n\nSCENARIO",
                    "\nclass Helper:\n    global Scenario\n    Scenario = None\n\nSCENARIO",
                ),
                self.SCENARIO_SOURCE.replace(
                    "\n\nSCENARIO",
                    "\nclass Helper:\n    global Scenario\n    del Scenario\n\nSCENARIO",
                ),
                self.SCENARIO_SOURCE.replace(
                    "\n\nSCENARIO",
                    "\n[(Scenario := None) for item in []]\n\nSCENARIO",
                ),
            ):
                path.write_text(invalid, encoding="utf-8")
                self.assertFalse(generator.validate_scenario_source(path)[0])
            path.write_text(self.SCENARIO_SOURCE, encoding="utf-8")
            self.assertTrue(generator.validate_scenario_source(path)[0])
            path.write_text(
                self.SCENARIO_SOURCE.replace(
                    "\n\nSCENARIO",
                    "\nclass Helper:\n    Scenario = None\n    del Scenario\n\nSCENARIO",
                ),
                encoding="utf-8",
            )
            self.assertTrue(generator.validate_scenario_source(path)[0])
            path.write_text(
                self.SCENARIO_SOURCE.replace(
                    "\n\nSCENARIO",
                    "\ndef helper():\n    Scenario = None\n    return [Scenario for Scenario in []]\n\nSCENARIO",
                ),
                encoding="utf-8",
            )
            self.assertTrue(generator.validate_scenario_source(path)[0])
            path.write_text(
                self.SCENARIO_SOURCE.replace(
                    "\n\nSCENARIO",
                    "\nvalues = [Scenario for Scenario in []]\n\nSCENARIO",
                ),
                encoding="utf-8",
            )
            self.assertTrue(generator.validate_scenario_source(path)[0])

    def test_loader_rejects_all_prompt_variant_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            variants_dir = Path(directory) / "variants"
            variants_dir.mkdir()
            external = Path(directory) / "external.json"
            external.write_text(
                json.dumps(
                    {"id": "natural", "template": "\n".join(sorted(PLACEHOLDERS))}
                ),
                encoding="utf-8",
            )
            try:
                (variants_dir / "natural.json").symlink_to(external)
            except OSError as error:
                self.skipTest(f"symlinks unavailable: {error}")
            with self.assertRaisesRegex(ValueError, "symlink"):
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
            base.write_text(self.SCENARIO_SOURCE, encoding="utf-8")
            output_dir = artifacts_dir / "factorial_prompt_scenarios"
            output_dir.mkdir()
            output_sentinel = output_dir / "keep.txt"
            output_sentinel.write_bytes(b"protected output\n")
            manifest_path = artifacts_dir / "factorial_prompt_manifest.json"
            manifest_path.write_bytes(b"protected manifest\n")

            with self.assertRaisesRegex(ValueError, "protected"):
                generator.generate_factorial_prompt_scenarios(
                    seeds_dir=seeds_dir,
                    artifacts_dir=artifacts_dir,
                    prompt_variants_dir=ROOT / "prompt_variants",
                    output_dir=output_dir,
                    manifest_path=manifest_path,
                )

            self.assertEqual(output_sentinel.read_bytes(), b"protected output\n")
            self.assertEqual(manifest_path.read_bytes(), b"protected manifest\n")

    def test_generic_defaults_are_scratch_and_protected_paths_refuse_overwrite(self):
        args = generator.parse_args([])
        self.assertIn("scratch", str(args.output_dir))
        self.assertIn("scratch", str(args.manifest_path))
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
            base.write_text(self.SCENARIO_SOURCE, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "protected"):
                generator.generate_factorial_prompt_scenarios(
                    seeds_dir=seeds_dir,
                    artifacts_dir=artifacts_dir,
                    prompt_variants_dir=ROOT / "prompt_variants",
                    output_dir=artifacts_dir / "factorial_prompt_scenarios",
                    manifest_path=artifacts_dir / "factorial_prompt_manifest.json",
                    overwrite=True,
                )

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
            base.write_text(self.SCENARIO_SOURCE, encoding="utf-8")
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

    def test_generic_rejects_seed_symlink_and_output_input_overlap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seeds_dir = root / "seeds"
            (seeds_dir / "beginner").mkdir(parents=True)
            external = root / "external.json"
            external.write_text(
                json.dumps({"title": "ExampleScenario"}), encoding="utf-8"
            )
            try:
                (seeds_dir / "beginner" / "link.json").symlink_to(external)
            except OSError as error:
                self.skipTest(f"symlinks unavailable: {error}")
            artifacts = root / "artifacts"
            base = artifacts / "ExampleScenario" / "ExampleScenario_iw0.py"
            base.parent.mkdir(parents=True)
            base.write_text(self.SCENARIO_SOURCE, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "symlink"):
                generator.generate_factorial_prompt_scenarios(
                    seeds_dir=seeds_dir,
                    artifacts_dir=artifacts,
                    prompt_variants_dir=ROOT / "prompt_variants",
                    output_dir=seeds_dir / "beginner" / "out",
                    manifest_path=artifacts / "scratch.json",
                    overwrite=True,
                )


if __name__ == "__main__":
    unittest.main()
