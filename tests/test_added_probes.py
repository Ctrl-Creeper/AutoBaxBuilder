"""Every per-scenario probe module must be internally consistent.

The registry entries for these probes are generated from what the modules
declare, so a probe missing its pairing, or paired with a variant that was never
declared, becomes a registry defect rather than an import error. That has
already happened once by hand -- a probe was registered against a variant it
does not report on -- so the constraints are checked here instead of only at
generation time.
"""

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import added_probes  # noqa: E402
import benchmark_v11  # noqa: E402

FIXTURES = REPO / "fixtures" / "reference_v1_1"


class AddedProbeModuleTests(unittest.TestCase):
    def modules(self):
        self.assertTrue(
            added_probes.SCENARIO_MODULES,
            "no probe modules loaded -- src/added_probes is empty or failed to import",
        )
        return sorted(added_probes.SCENARIO_MODULES.items())

    def test_every_check_is_paired_or_declared_unfalsifiable(self):
        for scenario, module in self.modules():
            pairings = getattr(module, "PAIRINGS", {})
            positive_only = set(getattr(module, "POSITIVE_EVIDENCE_ONLY", ()))
            for check in getattr(module, "CHECKS", ()):
                with self.subTest(scenario=scenario, probe=check.__name__):
                    self.assertTrue(
                        check.__name__ in pairings
                        or check.__name__ in positive_only,
                        "a probe with no variant and no positive-evidence-only "
                        "declaration cannot be calibrated, and its silence would "
                        "be read as a pass",
                    )

    def test_pairings_name_declared_variants_that_exist_on_disk(self):
        for scenario, module in self.modules():
            variants = getattr(module, "VARIANTS", {})
            for probe, filename in getattr(module, "PAIRINGS", {}).items():
                with self.subTest(scenario=scenario, probe=probe):
                    self.assertIn(filename, variants)
                    self.assertTrue((FIXTURES / scenario / filename).exists())

    def test_paired_probes_declare_the_cwes_they_must_report(self):
        for scenario, module in self.modules():
            expected = getattr(module, "EXPECTED_CWES", {})
            for probe in getattr(module, "PAIRINGS", {}):
                with self.subTest(scenario=scenario, probe=probe):
                    self.assertTrue(expected.get(probe))

    def test_unfalsifiable_probes_carry_no_variant(self):
        for scenario, module in self.modules():
            pairings = getattr(module, "PAIRINGS", {})
            for probe in getattr(module, "POSITIVE_EVIDENCE_ONLY", ()):
                with self.subTest(scenario=scenario, probe=probe):
                    self.assertNotIn(probe, pairings)

    def test_declared_names_match_actual_probe_functions(self):
        for scenario, module in self.modules():
            names = {check.__name__ for check in getattr(module, "CHECKS", ())}
            declared = (
                set(getattr(module, "PAIRINGS", {}))
                | set(getattr(module, "EXPECTED_CWES", {}))
                | set(getattr(module, "POSITIVE_EVIDENCE_ONLY", ()))
            )
            with self.subTest(scenario=scenario):
                self.assertEqual(declared - names, set())

    def test_unpaired_variants_belong_to_an_unfalsifiable_probe(self):
        """An unpaired variant is only meaningful next to such a probe.

        It is then the weakened implementation the rule is about, kept to show
        that the probe stays silent even against it -- which is the evidence for
        the positive-evidence-only claim. Without such a probe in the module it
        is a fixture nothing reads.
        """
        for scenario, module in self.modules():
            paired = set(getattr(module, "PAIRINGS", {}).values())
            unfalsifiable = getattr(module, "POSITIVE_EVIDENCE_ONLY", ())
            for filename in getattr(module, "VARIANTS", {}):
                if filename in paired:
                    continue
                with self.subTest(scenario=scenario, variant=filename):
                    self.assertTrue(unfalsifiable)

    def test_added_probes_reach_the_curated_suite(self):
        for scenario, module in self.modules():
            suite = {
                test.__name__
                for test in benchmark_v11.additional_security_tests_for(scenario)
            }
            for check in getattr(module, "CHECKS", ()):
                with self.subTest(scenario=scenario, probe=check.__name__):
                    self.assertIn(check.__name__, suite)


if __name__ == "__main__":
    unittest.main()
