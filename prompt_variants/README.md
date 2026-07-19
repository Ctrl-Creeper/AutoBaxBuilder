# Controlled Prompt Variants

The four tracked JSON files define the fixed prompt-category order used by the
controlled wrapper matrix:

1. `natural`
2. `weak_security`
3. `expert`
4. `threat_modeling`

Every template contains the same scenario placeholders and real decoded
newlines. `scripts/generate_factorial_prompt_scenarios.py` validates these
requirements before it writes a wrapper.

The generic factorial generator is a scratch-only utility. It refuses a
nonempty output directory or an existing manifest unless `--overwrite` is
explicitly passed. Never point it at the protected v1 or v1.1 evidence paths.

For the tracked v1.2 expansion workflow, use only the expansion-specific
commands documented in `seeds/README.md`:

```bash
PYTHONPATH=src python3 scripts/generate_taxonomy_expansion_wrappers.py
PYTHONPATH=src python3 scripts/audit_taxonomy_expansion.py
```
