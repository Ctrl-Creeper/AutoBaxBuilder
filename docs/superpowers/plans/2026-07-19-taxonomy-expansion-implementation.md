# Taxonomy Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add eight curated security-generation scenarios, generate a controlled four-prompt matrix for them, and provide reproducible static and live generation tooling without changing existing benchmark evidence.

**Architecture:** Seeds remain the taxonomy source of truth and carry an `expansion_batch` marker. A small validation module supplies discovery and invariant checks to both a batch pipeline and an expansion-only wrapper generator. Static validation and dry-run command construction run without an API; scenario/test/exploit generation is a separate live phase using the caller's loaded `.env`.

**Tech Stack:** Python 3.12, standard-library `unittest`, JSON, existing AutoBaxBuilder CLI, OpenAI-compatible API, existing prompt wrapper format.

---

### Task 1: Add CWE Support for the Expansion

**Files:**
- Modify: `src/cwes.py`
- Modify: `src/agent/config.py`
- Create: `tests/test_expansion_cwes.py`

- [ ] **Step 1: Write the failing CWE lookup test**

```python
import unittest

from cwes import get_cwe_by_id


class ExpansionCweTests(unittest.TestCase):
    def test_all_expansion_cwes_are_supported(self):
        expected = {204, 294, 345, 352, 362, 384, 409, 502, 601, 613, 639, 640, 915, 918}
        self.assertEqual({get_cwe_by_id(cwe).value["num"] for cwe in expected}, expected)
```

- [ ] **Step 2: Run the test and verify RED**

Run: `PYTHONPATH=src:. python -m unittest tests.test_expansion_cwes -v`

Expected: FAIL with `NotImplementedError: CWE-... is not implemented`.

- [ ] **Step 3: Add explicit enum members and generation metadata**

Add one `CWE` enum member per ID with `num` and a concise official-purpose
description: response discrepancy (204), replay (294), authenticity verification
(345), CSRF (352), race condition (362), session fixation (384), compressed-data
handling (409), untrusted deserialization (502), open redirect (601), session
expiration (613), user-controlled key authorization bypass (639), weak password
recovery (640), mass assignment (915), and SSRF (918). Append the same IDs to
`MITRE_TOP_25` in `src/agent/config.py`; retain the variable name for backward
compatibility.

- [ ] **Step 4: Run the focused test and full existing suite**

Run: `PYTHONPATH=src:. python -m unittest tests.test_expansion_cwes -v`

Expected: PASS.

Run: `PYTHONPATH=src:. python -m unittest discover -s tests -v`

Expected: all tests PASS.

- [ ] **Step 5: Commit only Task 1 files**

```bash
git add src/cwes.py src/agent/config.py tests/test_expansion_cwes.py
git commit -m "feat: support taxonomy expansion CWEs"
```

### Task 2: Add Four Beginner Seeds

**Files:**
- Create: `seeds/beginner/session_profile_natural.json`
- Create: `seeds/beginner/url_preview_natural.json`
- Create: `seeds/beginner/zip_archive_natural.json`
- Create: `seeds/beginner/json_settings_import_natural.json`
- Create: `tests/test_expansion_beginner_seeds.py`

- [ ] **Step 1: Write a failing seed contract test**

```python
import json
import unittest
from pathlib import Path


EXPECTED = {
    "BeginnerSessionProfile": {"CWE-352", "CWE-601", "CWE-384", "CWE-613", "CWE-20"},
    "BeginnerURLPreviewFetcher": {"CWE-918", "CWE-20", "CWE-400"},
    "BeginnerZipArchiveExtractor": {"CWE-22", "CWE-409", "CWE-434", "CWE-20"},
    "BeginnerJSONSettingsImport": {"CWE-502", "CWE-915", "CWE-20", "CWE-400"},
}


class BeginnerExpansionSeedTests(unittest.TestCase):
    def test_beginner_seed_contracts(self):
        seeds = [json.loads(path.read_text()) for path in Path("seeds/beginner").glob("*.json")]
        expansion = {seed["title"]: seed for seed in seeds if seed.get("taxonomy", {}).get("expansion_batch") == "v1_2"}
        self.assertEqual(set(expansion), set(EXPECTED))
        for title, cwes in EXPECTED.items():
            seed = expansion[title]
            self.assertEqual(seed["taxonomy"]["scenario_level"], "beginner")
            self.assertEqual(seed["taxonomy"]["prompt_category"], "natural")
            self.assertEqual(set(seed["target_cwes"]), cwes)
            self.assertGreaterEqual(len(seed["generation_notes"]), 4)
```

- [ ] **Step 2: Run the test and verify RED**

Run: `PYTHONPATH=src:. python -m unittest tests.test_expansion_beginner_seeds -v`

Expected: FAIL because no v1.2 beginner seeds exist.

- [ ] **Step 3: Create the four JSON seeds**

Each seed must include `title`, `description`, `needs_db`, `needs_secret`,
`taxonomy`, `target_cwes`, `generation_notes`, and `scenario_instructions`.
Set `taxonomy.expansion_batch` to `v1_2` and prompt category to `natural`.
Translate the exact contracts from the approved design into at least four
generation notes, including explicit numeric bounds wherever a strict oracle
will rely on a limit.

- [ ] **Step 4: Run the focused test**

Run: `PYTHONPATH=src:. python -m unittest tests.test_expansion_beginner_seeds -v`

Expected: PASS.

- [ ] **Step 5: Commit only beginner seed files and their test**

```bash
git add seeds/beginner/session_profile_natural.json seeds/beginner/url_preview_natural.json seeds/beginner/zip_archive_natural.json seeds/beginner/json_settings_import_natural.json tests/test_expansion_beginner_seeds.py
git commit -m "feat: add beginner taxonomy expansion seeds"
```

### Task 3: Add Four Complex Seeds

**Files:**
- Create: `seeds/complex/signed_webhook_natural.json`
- Create: `seeds/complex/multi_tenant_export_natural.json`
- Create: `seeds/complex/inventory_checkout_natural.json`
- Create: `seeds/complex/account_recovery_natural.json`
- Create: `tests/test_expansion_complex_seeds.py`

- [ ] **Step 1: Write a failing seed contract test**

```python
import json
import unittest
from pathlib import Path


EXPECTED = {
    "ComplexSignedWebhookProcessor": {"CWE-345", "CWE-294", "CWE-20", "CWE-400"},
    "ComplexMultiTenantDocumentExport": {"CWE-284", "CWE-863", "CWE-639", "CWE-89", "CWE-20"},
    "ComplexInventoryCheckout": {"CWE-362", "CWE-863", "CWE-20", "CWE-400"},
    "ComplexAccountRecovery": {"CWE-640", "CWE-294", "CWE-204", "CWE-613", "CWE-522"},
}


class ComplexExpansionSeedTests(unittest.TestCase):
    def test_complex_seed_contracts(self):
        seeds = [json.loads(path.read_text()) for path in Path("seeds/complex").glob("*.json")]
        expansion = {seed["title"]: seed for seed in seeds if seed.get("taxonomy", {}).get("expansion_batch") == "v1_2"}
        self.assertEqual(set(expansion), set(EXPECTED))
        for title, cwes in EXPECTED.items():
            seed = expansion[title]
            self.assertEqual(seed["taxonomy"]["scenario_level"], "complex")
            self.assertEqual(seed["taxonomy"]["prompt_category"], "natural")
            self.assertEqual(set(seed["target_cwes"]), cwes)
            self.assertGreaterEqual(len(seed["generation_notes"]), 4)
```

- [ ] **Step 2: Run the test and verify RED**

Run: `PYTHONPATH=src:. python -m unittest tests.test_expansion_complex_seeds -v`

Expected: FAIL because no v1.2 complex seeds exist.

- [ ] **Step 3: Create the four JSON seeds**

Use the same required fields and `expansion_batch` marker as Task 2. Make tenant
identity, signing input, idempotency scope, reset-token lifecycle, and bounded
concurrency postconditions explicit. Do not require real payment providers,
external webhook services, or production email delivery.

- [ ] **Step 4: Run the focused test**

Run: `PYTHONPATH=src:. python -m unittest tests.test_expansion_complex_seeds -v`

Expected: PASS.

- [ ] **Step 5: Commit only complex seed files and their test**

```bash
git add seeds/complex/signed_webhook_natural.json seeds/complex/multi_tenant_export_natural.json seeds/complex/inventory_checkout_natural.json seeds/complex/account_recovery_natural.json tests/test_expansion_complex_seeds.py
git commit -m "feat: add complex taxonomy expansion seeds"
```

### Task 4: Add Expansion Discovery and Validation

**Files:**
- Create: `src/taxonomy_expansion.py`
- Create: `tests/test_taxonomy_expansion.py`

- [ ] **Step 1: Write failing validation tests**

```python
import tempfile
import unittest
from pathlib import Path

from taxonomy_expansion import discover_expansion_seeds, validate_expansion_seeds


class TaxonomyExpansionTests(unittest.TestCase):
    def test_repository_has_balanced_v1_2_expansion(self):
        seeds = discover_expansion_seeds(Path("seeds"), batch="v1_2")
        report = validate_expansion_seeds(seeds, batch="v1_2")
        self.assertEqual(report["seed_count"], 8)
        self.assertEqual(report["level_counts"], {"beginner": 4, "complex": 4})
        self.assertEqual(report["errors"], [])

    def test_duplicate_title_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seed = {"title": "Duplicate", "description": "x", "needs_db": False, "needs_secret": False, "taxonomy": {"scenario_level": "beginner", "domain": "web_app", "task_type": "x", "prompt_category": "natural", "expansion_batch": "v1_2"}, "target_cwes": ["CWE-20"], "generation_notes": ["a", "b", "c", "d"], "scenario_instructions": ""}
            for level in ("beginner", "complex"):
                path = root / level
                path.mkdir()
                (path / "seed.json").write_text(__import__("json").dumps(seed))
            report = validate_expansion_seeds(discover_expansion_seeds(root, batch="v1_2"), batch="v1_2")
        self.assertIn("duplicate title: Duplicate", report["errors"])
```

- [ ] **Step 2: Run tests and verify RED**

Run: `PYTHONPATH=src:. python -m unittest tests.test_taxonomy_expansion -v`

Expected: ERROR because `taxonomy_expansion` does not exist.

- [ ] **Step 3: Implement discovery and validation**

Create `discover_expansion_seeds(seeds_dir: Path, batch: str) -> list[tuple[Path, dict]]`
that reads only beginner/complex JSON seeds whose taxonomy batch matches. Create
`validate_expansion_seeds(seeds, batch) -> dict` returning `seed_count`,
`level_counts`, `prompt_counts`, `titles`, `cwes`, and `errors`. Validate required
fields, unique titles, directory/level agreement, natural source prompt,
`CWE-[0-9]+` formatting, at least four generation notes, exactly 4/4 level
balance, and exactly eight seeds for batch v1_2.

- [ ] **Step 4: Run focused and full tests**

Run: `PYTHONPATH=src:. python -m unittest tests.test_taxonomy_expansion -v`

Expected: PASS.

Run: `PYTHONPATH=src:. python -m unittest discover -s tests -v`

Expected: all tests PASS.

- [ ] **Step 5: Commit validation module and tests**

```bash
git add src/taxonomy_expansion.py tests/test_taxonomy_expansion.py
git commit -m "feat: validate taxonomy expansion seeds"
```

### Task 5: Add Resumable Batch Pipeline

**Files:**
- Create: `scripts/run_taxonomy_expansion.py`
- Create: `tests/test_run_taxonomy_expansion.py`

- [ ] **Step 1: Write failing command-construction tests**

```python
import unittest
from pathlib import Path

from scripts.run_taxonomy_expansion import commands_for_seed


class RunTaxonomyExpansionTests(unittest.TestCase):
    def test_commands_follow_scenario_test_exploit_order(self):
        commands = commands_for_seed(Path("seeds/beginner/url_preview_natural.json"), Path("artifacts"), 3, "python")
        self.assertIn("--generate_scenarios", commands[0])
        self.assertIn("--generate_tests", commands[1])
        self.assertIn("BeginnerURLPreviewFetcher", commands[1])
        self.assertIn("--generate_exploits", commands[2])
```

- [ ] **Step 2: Run the test and verify RED**

Run: `PYTHONPATH=src:. python -m unittest tests.test_run_taxonomy_expansion -v`

Expected: ERROR because the batch runner does not exist.

- [ ] **Step 3: Implement the batch runner**

The CLI accepts `--seeds-dir`, `--artifacts-dir`, `--batch`, `--difficulty`,
`--parallel` (default 2), `--python`, `--dry-run`, and `--status-path`. Build three
argument arrays per seed using `src/main.py`: generate scenario, generate tests,
then generate exploits. Each worker executes those stages sequentially; workers
may run concurrently. Resume by skipping the scenario stage when the named JSON
exists, tests when an `_iu0.py` artifact exists, and exploits when `_iw0.py`
exists. Never load `.env` in Python; inherit the caller environment. Write a JSON
status report with per-seed stages, exit codes, and elapsed seconds. Dry-run must
print commands without executing subprocesses.

- [ ] **Step 4: Verify focused tests and dry-run**

Run: `PYTHONPATH=src:. python -m unittest tests.test_run_taxonomy_expansion -v`

Expected: PASS.

Run: `PYTHONPATH=src python scripts/run_taxonomy_expansion.py --dry-run --parallel 2`

Expected: 8 seeds and 24 ordered commands, with no artifact modification.

- [ ] **Step 5: Commit the batch runner**

```bash
git add scripts/run_taxonomy_expansion.py tests/test_run_taxonomy_expansion.py
git commit -m "feat: add resumable taxonomy expansion pipeline"
```

### Task 6: Generate Expansion-Only Prompt Wrappers and Audit

**Files:**
- Create: `scripts/generate_taxonomy_expansion_wrappers.py`
- Create: `scripts/audit_taxonomy_expansion.py`
- Create: `tests/test_expansion_wrappers.py`
- Modify: `seeds/README.md`

- [ ] **Step 1: Write failing wrapper tests using temporary base modules**

Create two temporary seeds carrying `expansion_batch=v1_2` and two matching
temporary `_iw0.py` files. Assert the generator emits eight wrappers, four per
base, and that `scenario_id` and `scenario_instructions` are the only varied
fields declared in each manifest entry. Add a failure case for a missing base
module.

- [ ] **Step 2: Run the test and verify RED**

Run: `PYTHONPATH=src:. python -m unittest tests.test_expansion_wrappers -v`

Expected: ERROR because the expansion wrapper generator does not exist.

- [ ] **Step 3: Implement the expansion-only generator**

Reuse `PROMPT_ORDER`, `load_prompt_variants`, `wrapper_source`, and
`build_manifest_entry` from `scripts/generate_factorial_prompt_scenarios.py`.
Filter through `discover_expansion_seeds` and write only to
`artifacts/factorial_prompt_scenarios_expansion_v1_2` and
`artifacts/factorial_prompt_manifest_expansion_v1_2.json`. Never modify the
v1.0/v1.1 output paths.

- [ ] **Step 4: Implement the static audit**

Read the expansion manifest and verify 32 unique IDs, 8 base titles, 4/4 level
balance, eight entries per prompt category, existing base/wrapper files, and
identical controlled-variable declarations. Write JSON and Markdown reports at
`artifacts/TAXONOMY_EXPANSION_V1_2_AUDIT.{json,md}` and exit nonzero on failure.
Before live generation, support `--seeds-only` to report seed readiness without
requiring base files.

- [ ] **Step 5: Document static and live commands**

Append commands for seed audit, batch dry-run, explicitly loading `.env`, live
base generation, wrapper generation, and final audit. State that live generation
uses the configured OpenAI-compatible endpoint and may incur cost.

- [ ] **Step 6: Run tests and seed-only audit**

Run: `PYTHONPATH=src:. python -m unittest tests.test_expansion_wrappers -v`

Expected: PASS.

Run: `PYTHONPATH=src python scripts/audit_taxonomy_expansion.py --seeds-only`

Expected: 8 valid seeds, 4 beginner, 4 complex, zero errors.

- [ ] **Step 7: Commit Task 6 files**

```bash
git add scripts/generate_taxonomy_expansion_wrappers.py scripts/audit_taxonomy_expansion.py tests/test_expansion_wrappers.py seeds/README.md
git commit -m "feat: generate and audit expansion prompt matrix"
```

### Task 7: Integration Verification and Optional Live Generation

**Files:**
- Generate: `artifacts/factorial_prompt_scenarios_expansion_v1_2/**`
- Generate: `artifacts/factorial_prompt_manifest_expansion_v1_2.json`
- Generate: `artifacts/TAXONOMY_EXPANSION_V1_2_AUDIT.json`
- Generate: `artifacts/TAXONOMY_EXPANSION_V1_2_AUDIT.md`

- [ ] **Step 1: Run all static verification**

Run: `PYTHONPATH=src:. python -m unittest discover -s tests -v`

Expected: all tests PASS.

Run: `python -m py_compile src/cwes.py src/taxonomy_expansion.py scripts/run_taxonomy_expansion.py scripts/generate_taxonomy_expansion_wrappers.py scripts/audit_taxonomy_expansion.py`

Expected: exit 0.

Run: `python -m black --check src/cwes.py src/taxonomy_expansion.py scripts/run_taxonomy_expansion.py scripts/generate_taxonomy_expansion_wrappers.py scripts/audit_taxonomy_expansion.py tests/test_expansion_cwes.py tests/test_expansion_beginner_seeds.py tests/test_expansion_complex_seeds.py tests/test_taxonomy_expansion.py tests/test_run_taxonomy_expansion.py tests/test_expansion_wrappers.py`

Expected: all files unchanged.

- [ ] **Step 2: Run the API-free pipeline preview**

Run: `PYTHONPATH=src python scripts/run_taxonomy_expansion.py --dry-run --parallel 2`

Expected: all eight seeds reported as planned or already complete.

- [ ] **Step 3: Gate the live phase on explicit environment confirmation**

Verify `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and the intended model are set without
printing secret values. Do not begin live generation when any setting is absent.

- [ ] **Step 4: Run live generation only after the static checkpoint is accepted**

```bash
set -a
source .env
set +a
PYTHONPATH=src python scripts/run_taxonomy_expansion.py --parallel 2
```

Expected: eight `_iw0.py` base scenario artifacts. Failures remain recorded and
are resumable; do not delete successful artifacts.

- [ ] **Step 5: Generate wrappers and final audit**

```bash
PYTHONPATH=src python scripts/generate_taxonomy_expansion_wrappers.py
PYTHONPATH=src python scripts/audit_taxonomy_expansion.py
```

Expected: 32 wrappers, 32 manifest rows, zero audit failures.

- [ ] **Step 6: Report calibration state accurately**

Describe the expansion as generated and statically audited. Do not call it
calibrated until secure/vulnerable reference fixtures have been executed for its
strict probes. Do not start the 216-sample model evaluation campaign in this task.
