"""Add registry entries for the probes declared under src/added_probes.

Six v1_2 scenarios reached calibration carrying only the checks the generator
produced. The probes closing that gap were drafted one module per scenario so
several could be written in parallel; each module records which weakened variant
makes each of its probes report, and which CWE it reports. This turns those
declarations into calibration-registry entries rather than having them written
out by hand, which is where a probe/variant mispairing crept in once before.

Entries are added as ``pending``: the declaration says what the probe should do,
and only scripts/run_reference_calibration.py may mark it ``calibrated``.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import added_probes  # noqa: E402


FIXTURES_DIR = Path("fixtures/reference_v1_1")
REGISTRY = Path("artifacts/reference_calibration_v1_2.json")


def fixture_id(scenario: str, filename: str) -> str:
    return f"{scenario}::{filename[:-3]}"


def entries_for(scenario: str, module: object) -> list[dict]:
    variants = getattr(module, "VARIANTS", {})
    pairings = getattr(module, "PAIRINGS", {})
    expected = getattr(module, "EXPECTED_CWES", {})
    positive_only = set(getattr(module, "POSITIVE_EVIDENCE_ONLY", ()))

    secure_path = FIXTURES_DIR / scenario / "secure.py"
    if not secure_path.exists():
        raise SystemExit(f"{scenario}: no secure.py at {secure_path}")

    entries = []
    for check in getattr(module, "CHECKS", ()):
        name = check.__name__
        if name in positive_only:
            # Nothing a single substitution can do makes these report, so they
            # carry no variant. They are recorded so the suite metadata can say
            # the scenario's clean result rests partly on unfalsifiable checks.
            continue
        variant = pairings.get(name)
        if variant is None:
            raise SystemExit(
                f"{scenario}/{name}: no PAIRINGS entry and not listed in "
                f"POSITIVE_EVIDENCE_ONLY"
            )
        if variant not in variants:
            raise SystemExit(
                f"{scenario}/{name}: paired with {variant}, which is not declared "
                f"in VARIANTS"
            )
        cwes = expected.get(name)
        if not cwes:
            raise SystemExit(f"{scenario}/{name}: no EXPECTED_CWES entry")
        variant_path = FIXTURES_DIR / scenario / variant
        if not variant_path.exists():
            raise SystemExit(
                f"{scenario}/{variant}: not materialized -- run "
                f"scripts/build_reference_fixtures.py first"
            )
        entries.append(
            {
                "probe_id": f"{scenario}/{name}",
                "status": "pending",
                "secure_fixture": {
                    "id": fixture_id(scenario, "secure.py"),
                    "path": str(secure_path),
                    "expected_cwes": [],
                },
                "vulnerable_fixture": {
                    "id": fixture_id(scenario, variant),
                    "path": str(variant_path),
                    "expected_cwes": sorted(int(c) for c in cwes),
                },
            }
        )
    return entries


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    known = {probe["probe_id"] for probe in registry["probes"]}

    added = []
    for scenario, module in sorted(added_probes.SCENARIO_MODULES.items()):
        for entry in entries_for(scenario, module):
            if entry["probe_id"] in known:
                continue
            added.append(entry)
            known.add(entry["probe_id"])

    registry["probes"] = sorted(
        registry["probes"] + added, key=lambda probe: probe["probe_id"]
    )
    for entry in added:
        print(f"+ {entry['probe_id']} -> {entry['vulnerable_fixture']['path']}")
    print(f"{len(added)} added, {len(registry['probes'])} total")

    if not args.dry_run:
        args.registry.write_text(
            json.dumps(registry, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
