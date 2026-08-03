# Factorial Prompt Scenarios Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a controlled `base_task × prompt_category` scenario matrix so prompt style can be evaluated as a single variable.

**Architecture:** Reuse already generated `_iw0.py` scenario artifacts as immutable base scenarios. Generate lightweight wrapper scenario files that import each base scenario, preserve its API/text spec/tests, and change only the scenario id plus `scenario_instructions` associated with one prompt category.

**Tech Stack:** Python stdlib JSON/pathlib/importlib, existing BaxBench `Scenario` dataclass, existing `prompt_variants/*.json`, existing `seeds/**/*.json` taxonomy metadata.

---

### Task 1: Add Factorial Wrapper Generator

**Files:**
- Create: `scripts/generate_factorial_prompt_scenarios.py`

- [ ] Implement a script that discovers base seeds, maps each seed title to `artifacts/<title>/<title>_iw0.py`, loads the four prompt variant JSON files, and writes wrapper scenario files under `artifacts/factorial_prompt_scenarios/<title>/<title>__<prompt_category>.py`.
- [ ] Wrapper files must import the base scenario by module name from its original artifact directory so multiprocessing can still pickle/import test functions.
- [ ] Wrapper files must instantiate `Scenario` with the base API spec, text spec, app description, tests, db/secret flags, and packages, changing only `id` and `scenario_instructions`.
- [ ] Write `artifacts/factorial_prompt_manifest.json` with 40 entries and per-entry taxonomy labels.

### Task 2: Document Controlled Evaluation Usage

**Files:**
- Modify: `seeds/README.md`
- Modify or create: `prompt_variants/README.md`

- [ ] Explain that `seeds/beginner` and `seeds/complex` are base task coverage seeds.
- [ ] Explain that strict prompt-category comparison should use generated wrapper scenarios, not regenerated seeds, because wrappers reuse the same tests.
- [ ] Include commands to generate the matrix and run one wrapper scenario with `scripts/run_smoke_eval.py`.

### Task 3: Generate and Verify Matrix

**Files:**
- Generated: `artifacts/factorial_prompt_scenarios/**.py`
- Generated: `artifacts/factorial_prompt_manifest.json`

- [ ] Run the generator.
- [ ] Verify there are 40 manifest entries.
- [ ] Compile all generated wrapper scenario files.
- [ ] Import at least one wrapper and confirm it points to the same number of functional/security tests as its base scenario.
