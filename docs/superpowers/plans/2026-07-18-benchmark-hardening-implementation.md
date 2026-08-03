# Benchmark Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement audit safeguards, calibration tracking, a valid OrderManagement authorization scenario, and human-triage metrics.

**Architecture:** Keep LLM auditing post-processing only, represent calibration and triage as versioned JSON artifacts, and build v1.2 OrderManagement as a new scenario rather than editing v1.0/v1.1 evidence. Docker/API-dependent commands remain separate from static and unit verification.

**Tech Stack:** Python 3.12, standard-library `unittest`, OpenAI-compatible API, FastAPI scenario artifacts, JSON/Markdown reports.

---

### Task 1: LLM audit privacy and provenance

**Files:**
- Modify: `src/llm_audit.py`
- Modify: `scripts/audit_passed_samples.py`
- Modify: `tests/test_llm_audit.py`

- [x] Add failing tests for secret redaction, packet hashing, and live-call opt-in.
- [x] Implement `redact_sensitive_text`, packet/code/prompt hashes, and endpoint-host metadata.
- [x] Require `--allow-code-upload` for non-dry-run execution before constructing an API client.
- [x] Verify with `python -m unittest tests.test_llm_audit -v` and a dry-run against existing results.

### Task 2: Calibration registry and verifier

**Files:**
- Create: `artifacts/reference_calibration_v1_1.json`
- Create: `scripts/verify_reference_calibration.py`
- Create: `tests/test_reference_calibration.py`

- [x] Add a failing test proving incomplete fixture records are not calibrated.
- [x] Implement schema validation and a Markdown/JSON verifier report.
- [x] Populate every strict v1.1 probe with secure/vulnerable fixture contracts and `pending` status.
- [x] Verify the pending registry reports zero calibrated probes rather than a false success.

Fixture implementation and Docker execution remain a separate pending campaign.

### Task 3: OrderManagement v1.2 ownership contract

**Files:**
- Create: `seeds/complex/order_management_authorized_v1_2.json`
- Create: `scripts/generate_order_management_v1_2.py`
- Create: `tests/test_order_management_v1_2.py`
- Modify: `seeds/README.md`

- [x] Add tests that require user/auth/owner fields and two-user authorization probes in generated output.
- [x] Generate a standalone v1.2 scenario artifact from the seed; retain v1.0 and v1.1 files untouched.
- [x] Verify generated Python compiles and metadata declares CWE-284/CWE-863 as strict-oracle targets.

### Task 4: Human triage and metrics

**Files:**
- Create: `scripts/summarize_llm_audit_triage.py`
- Create: `tests/test_llm_audit_triage.py`
- Modify: `artifacts/LLM_AUDIT_PROTOCOL.md`

- [x] Add a failing test for confirmation and false-positive rate calculations.
- [x] Implement JSONL/JSON triage ingestion, outcome validation, and metrics report generation.
- [x] Document the triage template and prohibition on retroactive score changes.
- [x] Verify all unit tests, compilation, formatting, and dry-run artifacts.

### Task 5: Runtime campaign gates

**Files:**
- Modify: `artifacts/REFERENCE_CALIBRATION_V1_1.md`
- Modify: `artifacts/FACTORIAL_EXPERIMENT_REPORT.md`

- [x] Document Docker-required reference fixture execution and a five-sample live-audit gate.
- [x] Check Docker availability and report missing fixture implementations without treating the pending registry as a benchmark result.
- [x] Run live LLM audit with `--limit 5 --allow-code-upload` only after static safeguards verify.
