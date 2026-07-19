# Taxonomy Scenario Seeds

These JSON files are curated scenario seeds for controlled benchmark generation.
They keep coverage decisions explicit while still letting AutoBaxBuilder generate
the OpenAPI schema, text spec, functional tests, implementations, and exploits.

The seeds in `seeds/beginner` and `seeds/complex` define the base task
coverage. They are not, by themselves, a strict prompt-category ablation,
because each base task currently has one prompt label. To compare prompt styles
as a single variable, first generate the base `_iw0.py` scenarios and tests,
then create prompt-category wrappers with:

```bash
python scripts/generate_factorial_prompt_scenarios.py
```

This writes:

- `artifacts/factorial_prompt_scenarios/<BaseTask>/<BaseTask>__<prompt>.py`
- `artifacts/factorial_prompt_manifest.json`

The wrapper scenarios reuse the same OpenAPI schema, text spec, functional
tests, and security tests as the base `_iw0.py` artifact. Only the scenario id
and `scenario_instructions` change, so `natural`, `weak_security`, `expert`,
and `threat_modeling` can be compared within the same base task.

Each seed has the core fields AutoBaxBuilder needs:

- `title`
- `description`
- `needs_db`
- `needs_secret`

Optional research metadata is preserved in the generated scenario JSON:

- `taxonomy`: coverage labels for analysis
- `target_cwes`: intended security surfaces
- `generation_notes`: constraints used when expanding the seed into OpenAPI/text spec
- `scenario_instructions`: additional instructions later shown to solution models

Run one seed through the full pipeline:

```bash
./autobaxbuilder.sh --seed-file seeds/beginner/web_login_natural.json
```

For official OpenAI, put this in the repository root `.env`:

```bash
export OPENAI_API_KEY="sk-..."
```

For an OpenAI-compatible endpoint, also set `OPENAI_BASE_URL`:

```bash
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="https://your-openai-compatible-endpoint/v1"
```

Or generate only the scenario JSON:

```bash
python src/main.py \
  --path artifacts \
  --difficulty 3 \
  --seed_file seeds/beginner/web_login_natural.json \
  --generate_scenarios
```

Run one controlled prompt wrapper through the smoke evaluator:

```bash
PYTHONPATH=src \
python scripts/run_smoke_eval.py \
  --scenario-file artifacts/factorial_prompt_scenarios/BeginnerCSVFilter/BeginnerCSVFilter__natural.py \
  --run-dir artifacts/eval_runs_factorial/BeginnerCSVFilter__natural \
  --model "${AUTOBAX_MODEL:-gpt-5.5}" \
  --phase all \
  --base-url-host ai.bnds.fun
```

## Authorization Follow-up Scenario

The complex OrderManagement v1.2 seed makes the previously implicit identity
and ownership contract explicit. It is a new versioned scenario, not a rewrite
of the v1.0/v1.1 artifacts. Generate its standalone deterministic artifact with:

    PYTHONPATH=src python scripts/generate_order_management_v1_2.py

The generated task uses bearer-token identity and two-user probes for cross-user
order reads, totals, and status changes. It targets CWE-284, CWE-863, and CWE-20.

## Taxonomy Expansion v1.2 / 分类扩展 v1.2

Use the expansion-only matrix for the eight `v1_2` seeds. It does not replace
the existing v1.0 or v1.1 prompt artifacts.

先检查种子是否就绪；此命令不需要已生成的基础场景：

```bash
PYTHONPATH=src python3 scripts/audit_taxonomy_expansion.py --seeds-only
```

Preview the resumable base-generation commands without calling an API:

```bash
PYTHONPATH=src python3 scripts/run_taxonomy_expansion.py --dry-run --parallel 2
```

For live generation, load `.env` explicitly. The configured OpenAI-compatible
endpoint is used and API calls may incur cost. 请先确认模型、端点和费用，再执行：

```bash
set -a
source .env
set +a
PYTHONPATH=src python3 scripts/run_taxonomy_expansion.py --parallel 2
```

After all eight base `_iw0.py` files exist, generate only the expansion wrappers
and run the final static audit:

```bash
PYTHONPATH=src python3 scripts/generate_taxonomy_expansion_wrappers.py
PYTHONPATH=src python3 scripts/audit_taxonomy_expansion.py
```

Current status terms: the matrix is **generated** only after the wrapper command
succeeds; it is **smoke-tested** only after smoke evaluation runs; it is
**calibrated** only after reference fixtures pass strict probes. The 216-sample
evaluation campaign has not started / 216 个样本的评测尚未开始。
