import json
import re
import unittest
from pathlib import Path

import agent.templates as templates
import agent.templates_format as templates_format
from generate_exploit_specific_instructions import INSTRUCTION_TEMPLATE
from scripts.generate_factorial_prompt_scenarios import (
    PROMPT_CATEGORY_INSTRUCTIONS,
)


ROOT = Path(__file__).resolve().parents[1]
DENYLIST = (
    "ex" + "ploit",
    "pay" + "load",
    "adver" + "sarial",
    "weapon" + "ize",
    "att" + "ack",
    "by" + "pass",
    "proof" + "-of-concept",
    "vulner" + "ability",
    "penetra" + "tion",
    "injec" + "tion",
    "thre" + "at",
    "malic" + "ious",
    "offen" + "sive",
    "ct" + "f",
)
DENIED_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(term) + r"\w*" for term in DENYLIST) + r")\b",
    re.IGNORECASE,
)

MODEL_PROMPT_NAMES = (
    "find_exploits_in_scenario",
    "find_exploits_in_code",
    "exploit_specific_instructions",
    "generate_exploit_strategy",
    "compliance_exploit_strategy",
    "generate_exploit_code",
    "iterate_green",
    "iterate_red",
    "flip_impl_vulnerable",
    "flip_impl_secure",
    "fix_sec_code",
    "generate_scenario",
    "generate_fewshot_strategies_from_code",
    "sec_tool_signatures",
    "cwe_list",
)


class PromptTerminologyTests(unittest.TestCase):
    def assert_neutral(self, label: str, text: str):
        match = DENIED_PATTERN.search(text)
        self.assertIsNone(match, f"{label} contains a non-neutral term")

    def test_controlled_prompt_variants_use_quality_engineering_language(self):
        for path in sorted((ROOT / "prompt_variants").glob("*.json")):
            variant = json.loads(path.read_text(encoding="utf-8"))
            self.assert_neutral(str(path), variant["description"])
            self.assert_neutral(str(path), variant["template"])
        for prompt_id, instructions in PROMPT_CATEGORY_INSTRUCTIONS.items():
            self.assert_neutral(prompt_id, instructions)

    def test_model_instruction_templates_use_neutral_language(self):
        for module in (templates, templates_format):
            for name, value in vars(module).items():
                if not name.startswith("_") and isinstance(value, str):
                    self.assert_neutral(f"{module.__name__}.{name}", value)
        for name in MODEL_PROMPT_NAMES:
            self.assert_neutral(name, getattr(templates, name))
        self.assert_neutral(
            "strategy output format", templates_format.exploit_strategy_format
        )
        self.assert_neutral("test code format", templates_format.sec_code_format)
        self.assert_neutral("small-example summary", INSTRUCTION_TEMPLATE)

    def test_seed_generation_context_uses_neutral_language(self):
        for level in ("beginner", "complex"):
            for path in sorted((ROOT / "seeds" / level).glob("*.json")):
                seed = json.loads(path.read_text(encoding="utf-8"))
                if seed.get("taxonomy", {}).get("expansion_batch") != "v1_2":
                    continue
                context = json.dumps(
                    {
                        "description": seed["description"],
                        "generation_notes": seed["generation_notes"],
                        "oracle_contract": seed["oracle_contract"],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                self.assert_neutral(str(path), context)

    def test_evaluation_fixture_rules_are_explicit_in_generation_prompts(self):
        self.assertIn("evaluation_fixture", templates.generate_openapi)
        self.assertIn("evaluation_fixture", templates.generate_text_spec)
        self.assertIn("Do not invent credentials", templates.functional_tests_specs)
        self.assertIn("declared evaluation fixture", templates.functional_tests_code)


if __name__ == "__main__":
    unittest.main()
