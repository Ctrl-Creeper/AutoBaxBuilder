# LLM Passed-Sample Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an opt-in LLM-assisted post-processing audit that reviews deterministic passing samples for likely untested security issues without changing benchmark scores.

**Architecture:** A pure `src/llm_audit.py` module will select completed passing samples, build bounded review packets from scenario metadata, deterministic test results, and generated source, then validate structured LLM responses. A standalone CLI will call the configured OpenAI-compatible endpoint only when not in dry-run mode, save immutable raw reviews, and emit a deduplicated manual-review queue. The existing BaxBench result files and factorial summaries remain unchanged.

**Tech Stack:** Python 3.12, standard-library `json`/`unittest`, OpenAI-compatible Chat Completions API, existing factorial manifest and run layout.

---

### Task 1: Create deterministic audit data model and tests

**Files:**
- Create: `src/llm_audit.py`
- Create: `tests/test_llm_audit.py`

- [ ] **Step 1: Write failing tests for candidate parsing and sample selection**

```python
def test_parse_review_json_rejects_non_candidate_verdict():
    with self.assertRaises(ValueError):
        parse_review_json('{"verdict": "security_failed"}')

def test_select_passed_samples_defaults_to_complex_only():
    records = select_audit_samples(summary, manifest_by_id, complex_only=True)
    self.assertEqual([record["scenario_level"] for record in records], ["complex"])
```

- [ ] **Step 2: Run the focused tests and verify failure**

Run: `PYTHONPATH=src python -m unittest tests.test_llm_audit -v`

Expected: failure because `llm_audit` does not exist.

- [ ] **Step 3: Implement bounded packet construction and schema validation**

```python
VALID_VERDICTS = {"no_candidate", "candidate", "unclear"}
VALID_CONFIDENCE = {"low", "medium", "high"}

def parse_review_json(text: str) -> dict:
    # Strip an optional fenced JSON block, decode JSON, validate fixed fields,
    # and return only the documented audit fields.
```

The module must read code without executing it, retain the deterministic status as `passed`, cap source text by `max_code_chars`, and provide a stable fingerprint for candidate deduplication.

- [ ] **Step 4: Re-run focused tests**

Run: `PYTHONPATH=src python -m unittest tests.test_llm_audit -v`

Expected: all tests pass.

### Task 2: Add the opt-in audit CLI

**Files:**
- Create: `scripts/audit_passed_samples.py`
- Test: `tests/test_llm_audit.py`

- [ ] **Step 1: Write failing dry-run output test**

```python
def test_write_audit_report_keeps_deterministic_status(tmp_path):
    path = write_audit_report(tmp_path, report)
    saved = json.loads(path.read_text())
    self.assertEqual(saved["reviews"][0]["deterministic_status"], "passed")
```

- [ ] **Step 2: Run the focused test and verify failure**

Run: `PYTHONPATH=src python -m unittest tests.test_llm_audit -v`

Expected: failure because the report writer is missing.

- [ ] **Step 3: Implement CLI behavior**

```text
--run-dir                 completed factorial evaluation directory
--manifest                matching factorial manifest
--model                   generation model used in the run
--auditor-model           review model; defaults to AUTOBAX_AUDIT_MODEL then AUTOBAX_MODEL
--include-beginner        opt out of the default complex-only selection
--limit                   cap reviewed samples for cost control
--max-code-chars          cap code sent to the reviewer
--dry-run                 write review packets without an API request
--output-dir              audit artifacts directory
```

The LLM prompt must require one JSON object with a candidate-only verdict. It must state that the response is not a benchmark score, must not claim an exploit without evidence, and must propose at most one deterministic test idea. API errors and malformed responses must be recorded as `audit_error`, never converted into a deterministic failure.

- [ ] **Step 4: Re-run the full audit unit suite**

Run: `PYTHONPATH=src python -m unittest tests.test_llm_audit -v`

Expected: all tests pass.

### Task 3: Add documentation and verification

**Files:**
- Modify: `artifacts/FACTORIAL_EXPERIMENT_REPORT.md`
- Create: `artifacts/LLM_AUDIT_PROTOCOL.md`

- [ ] **Step 1: Document the non-scoring boundary and review workflow**

```text
deterministic passed sample
-> LLM candidate review
-> human triage
-> manually authored deterministic test
-> later suite version
```

The document must prohibit automatic score mutation and automatic test generation/execution from LLM text.

- [ ] **Step 2: Add commands for dry-run and live audit**

```bash
PYTHONPATH=src python scripts/audit_passed_samples.py \
  --run-dir artifacts/eval_runs_factorial_repeats3 \
  --manifest artifacts/factorial_prompt_manifest.json \
  --model gpt-5.5 \
  --dry-run
```

- [ ] **Step 3: Verify code and generated dry-run artifacts**

Run:

```bash
PYTHONPATH=src python -m unittest tests.test_llm_audit -v
python -m py_compile src/llm_audit.py scripts/audit_passed_samples.py
python -m black --check src/llm_audit.py scripts/audit_passed_samples.py tests/test_llm_audit.py
PYTHONPATH=src python scripts/audit_passed_samples.py \
  --run-dir artifacts/eval_runs_factorial_repeats3 \
  --manifest artifacts/factorial_prompt_manifest.json \
  --model gpt-5.5 \
  --dry-run \
  --output-dir artifacts/llm_audit_dry_run
```

Expected: unit tests, compilation, and formatting pass; dry-run report contains only `deterministic_status: passed` records and no external API calls.
