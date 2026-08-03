"""A scenario wrapper must assemble exactly the probes the suite declares.

Reference calibration checks the probes: silent against a correct implementation,
reporting against one weakened at a single place. It calls those functions
directly. The evaluation reaches them through a scenario wrapper, and **the
wrapper's assembly is a layer calibration never sees.**

The v1_2 wrappers were briefly built this way -- ``security_tests`` bound to the
raw pre-curation list -- which would have run probes the curation had removed and
skipped every probe it added, while exiting 0 with complete artifacts and
plausible-looking rates. It was caught before those results were used, but only
by reading a generated wrapper by hand.

These tests make each post-curation wrapper set prove that its ``security_tests``
expression routes through the curated accessors and names its own scenario.
"""

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import benchmark_v11  # noqa: E402

# Post-curation wrapper sets only. artifacts/factorial_prompt_scenarios holds the
# v1.0 wrappers, which predate benchmark_v11 and pass the raw generated list by
# design -- asserting over them would flag the baseline as defective.
WRAPPER_DIRS = (
    ROOT / "artifacts" / "factorial_prompt_scenarios_v1_1",
    ROOT / "artifacts" / "factorial_prompt_scenarios_expansion_v1_2",
)


def wrapper_files() -> list[Path]:
    files = []
    for directory in WRAPPER_DIRS:
        if directory.exists():
            files.extend(sorted(directory.glob("*/*.py")))
    return [p for p in files if not p.name.startswith("_")]


def assembled_expression(path: Path) -> ast.expr | None:
    """The expression a wrapper assigns to ``security_tests=``."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg == "security_tests":
                    return keyword.value
    return None


def assembled_source(path: Path) -> str:
    expression = assembled_expression(path)
    return ast.unparse(expression) if expression is not None else ""


def passes_raw_list(path: Path) -> bool:
    """Whether the wrapper hands the pre-curation list straight to the scenario.

    Tested on the expression itself, not by substring: a correct wrapper passes
    ``_base.security_tests`` *into* ``selected_security_tests_for`` as the list to
    filter, so the name legitimately appears in a curated wrapper too.
    """
    expression = assembled_expression(path)
    return (
        isinstance(expression, ast.Attribute)
        and expression.attr == "security_tests"
        and isinstance(expression.value, ast.Name)
        and expression.value.id == "_base"
    )


class WrapperSuiteAssemblyTests(unittest.TestCase):
    def setUp(self):
        self.wrappers = wrapper_files()
        if not self.wrappers:
            self.skipTest("no generated scenario wrappers present")

    def test_no_wrapper_uses_the_raw_pre_curation_list(self):
        offenders = [
            p.relative_to(ROOT)
            for p in self.wrappers
            if passes_raw_list(p)
        ]
        self.assertEqual(
            offenders,
            [],
            "these wrappers bypass curation: excluded probes would run and added "
            "probes would not. This is the defect that invalidated the v1.1 run.",
        )

    def test_every_wrapper_routes_through_the_curated_accessors(self):
        for path in self.wrappers:
            with self.subTest(wrapper=str(path.relative_to(ROOT))):
                source = assembled_source(path)
                self.assertIn("selected_security_tests_for", source)
                self.assertIn("additional_security_tests_for", source)

    def test_added_probes_are_reachable_for_every_declared_scenario(self):
        """The other half of the same failure: added probes that never run.

        A wrapper can route through the accessors and still contribute nothing if
        the scenario name it passes does not match a declared one -- the accessor
        would return an empty list and the wrapper would look correct.
        """
        declared = set(benchmark_v11.STRICT_BASE_TESTS)
        for path in self.wrappers:
            scenario = path.parent.name
            if scenario not in declared:
                continue
            with self.subTest(scenario=scenario):
                source = assembled_source(path)
                self.assertIn(
                    repr(scenario).strip("'\""),
                    source,
                    "the wrapper must name its own scenario, or the accessors "
                    "return an empty list and the curation silently applies to "
                    "nothing",
                )

    def test_declared_suite_is_never_empty_for_a_curated_scenario(self):
        for scenario in sorted(benchmark_v11.STRICT_BASE_TESTS):
            with self.subTest(scenario=scenario):
                metadata = benchmark_v11.suite_metadata_for(scenario)
                total = len(metadata["strict_base_tests"]) + len(
                    metadata["added_variant_tests"]
                )
                self.assertGreater(
                    total,
                    0,
                    "a scenario with no probes cannot fail, and its clean result "
                    "would be reported as a pass",
                )


if __name__ == "__main__":
    unittest.main()
