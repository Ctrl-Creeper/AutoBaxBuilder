"""Per-scenario added probes, kept one module per scenario.

Six v1_2 scenarios reached calibration carrying only the checks the generator
produced. A coverage sweep of the v1.1 scenarios had previously raised their
probe count from 18 to 61, and nothing equivalent had been applied here, so a
clean result from those six meant little. Each module below supplies the missing
probes for one scenario.

A module declares two names:

    VARIANTS: dict[str, tuple[str, str, str]]
        variant filename -> (old fragment, new fragment, note), same contract as
        fixtures/reference_v1_1/variants.py -- the old fragment must occur
        exactly once in that scenario's secure.py.

    CHECKS: tuple[Callable, ...]
        the added probe functions, in the style of src/benchmark_v11.py.

Splitting per scenario is what let six agents draft in parallel without writing
to one shared file.
"""

import importlib
import pkgutil

SCENARIO_MODULES: dict[str, object] = {}


def _load() -> None:
    for info in pkgutil.iter_modules(__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{__name__}.{info.name}")
        scenario = getattr(module, "SCENARIO", None)
        if scenario:
            SCENARIO_MODULES[scenario] = module


_load()


def variants_for(scenario: str) -> dict:
    module = SCENARIO_MODULES.get(scenario)
    return dict(getattr(module, "VARIANTS", {})) if module else {}


def checks_for(scenario: str) -> tuple:
    module = SCENARIO_MODULES.get(scenario)
    return tuple(getattr(module, "CHECKS", ())) if module else ()


def all_variants() -> dict[str, dict]:
    return {name: variants_for(name) for name in SCENARIO_MODULES}
