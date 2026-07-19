# Prompt Variants

These templates are solution-generation prompts for evaluating how different
instruction styles affect generated backend implementations.

Each template uses the same variables:

- `{scenario_title}`
- `{scenario_description}`
- `{openapi_schema}`
- `{text_spec}`
- `{scenario_instructions}`

Suggested usage:

1. Generate base scenarios and tests from the curated seeds.
2. Run `python scripts/generate_factorial_prompt_scenarios.py`.
3. Select a wrapper scenario from `artifacts/factorial_prompt_manifest.json`.
4. Evaluate the wrapper scenario with `scripts/run_smoke_eval.py`.

For strict ablations, do not regenerate OpenAPI specs or tests for every prompt
category. The generated wrapper scenarios reuse the same base API, text spec,
functional tests, and security tests. Only the prompt category instruction
changes.

The variants are intentionally different in security emphasis:

- `natural.json`: ordinary product request, minimal security framing.
- `weak_security.json`: light reminders about robustness and privacy.
- `expert.json`: precise engineering request with explicit edge handling.
- `threat_modeling.json`: security-first request with trust-boundary analysis.

The current BaxBench runner consumes these categories through
`scenario_instructions` in the generated wrapper scenario. The full templates
remain here as research metadata and as a reference for future runner-level
prompt customization.
