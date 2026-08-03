# Benchmark Hardening Design

## Goal

Strengthen the AutoBaxBuilder security benchmark so that deterministic test
results, LLM-assisted coverage review, and future reference calibration remain
separate, reproducible, and safe to operate.

## Scope

This work has four components:

1. Harden the optional LLM candidate audit before it can upload generated code.
2. Add a machine-readable calibration registry and verifier for secure and
   vulnerable reference fixtures.
3. Create an OrderManagement v1.2 scenario with an explicit identity and
   ownership contract so CWE-284 and CWE-863 have a valid oracle.
4. Add human-triage records and aggregate audit-quality metrics.

The work does not reinterpret prior v1.0/v1.1 results, automatically alter
scores, or automatically execute LLM-proposed tests.

## Component Boundaries

### LLM Audit Hardening

`src/llm_audit.py` remains a pure artifact-processing module. Before a live
call, it requires an explicit `--allow-code-upload` flag, redacts common secret
patterns, labels code as untrusted data in the prompt, records prompt/packet/
code hashes, and records endpoint host without storing credentials.

### Calibration Registry

`artifacts/reference_calibration_v1_1.json` is the source of truth for each
strict v1.1 probe. A verifier checks that every probe has a secure and
vulnerable fixture declaration plus recorded expected outcomes. Fixture
execution is a separate Docker-dependent stage; pending fixtures cannot make a
suite appear calibrated.

### OrderManagement v1.2

The v1.2 seed/spec adds users, bearer authentication, `ownerId`, and explicit
rules for cross-user list/read/status-change behavior. Its security tests use a
two-user setup and prove both owner success and attacker denial before treating
a cross-user success as CWE-284 or CWE-863.

### Human Triage

An auditable JSON review file records a human outcome for every LLM candidate:
`confirmed_missing_coverage`, `false_positive`, `out_of_scope`, or
`needs_specification_change`. A summary tool calculates candidate count,
confirmation rate, false-positive rate, and deterministic-test yield.

## Data Flow

```text
deterministic passed sample
-> redacted bounded packet + provenance hashes
-> optional LLM candidate review
-> human triage record
-> manually authored test + reference calibration
-> future suite version
```

No arrow in this flow writes to an existing BaxBench result or changes an
existing deterministic status.

## Acceptance Criteria

- A live audit without `--allow-code-upload` exits before an API call.
- Audit reports include redaction count, packet hash, code hash, prompt hash,
  auditor model, and endpoint host.
- Calibration verification reports pending fixtures separately from completed
  calibration and cannot report a suite as calibrated when records are absent.
- The OrderManagement v1.2 scenario has an explicit authentication and owner
  contract plus two-user positive/negative authorization probes.
- Triage metrics only use human-reviewed candidates and never affect benchmark
  pass/security-fail counts.
