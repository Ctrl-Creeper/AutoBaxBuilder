# Study 4X-CM — cross-model exploratory extension: results

**EXPLORATORY. NOT CONFIRMATORY. NOT A REPLICATION OF STUDY 4B.**
Design frozen before generation: `DESIGN_FROZEN.md`,
SHA-256 `6632c086578660f80ced3caa09b3e745ae3e8a74d97ddc0f15650f2a4d85552d`.

## Execution

| | |
|---|---|
| Model | `gpt-5.6-luna`, served by the third-party proxy `https://ai.bnds.fun/v1` |
| Pre-generation gates | **9/9 GO** (`study4x_gate_report_FROZEN.json`) |
| Requests | **94/94** completed (47 tasks × {S, S′} × 1 repeat) |
| Retried requests | 0 |
| Finish reasons | `stop` × 94 (no truncation) |
| Completion tokens | 71,897 |
| Empty responses | 0 |
| Non-runnable completions | 0 (all 94 scored `OK` by the runner) |
| Oracle preflight | 47/47 patched references pass both situations |
| Randomization root seed | 11279076677682981486 |

## Endpoints (task-equal-weighted, paired over the 47 tasks)

| Endpoint | S | S′ | Δ (S − S′) | 95% CI | sign-flip p |
|---|---:|---:|---:|---:|---:|
| SecurityPass | 0.9787 | 0.4255 | **+0.5532** | [+0.4056, +0.7007] | 2.98e-08 |
| CapabilityPass | 0.8298 | 1.0000 | **−0.1702** | [−0.2818, −0.0587] | 7.81e-03 |
| JointPass | 0.8298 | 0.4255 | **+0.4043** | [+0.2140, +0.5945] | 3.11e-04 |

Task-level difference signs (47 tasks): security 26 positive / 21 zero / 0 negative;
capability 0 positive / 39 zero / 8 negative; joint 23 / 20 / 4.

## Pre-declared read-out

**DIRECTIONAL_REPRODUCTION** — both CIs exclude zero, security positive and
capability negative, the same two-sided signature Study 4B produced on the local
model. The read-out rule was fixed in §4 of the frozen design before any study
prompt was sent.

## What this supports

On the frozen DS=47 subset, with one repeat, `gpt-5.6-luna` behaved like the
local model in *direction*: the determining `S` specification produced markedly
higher SecurityPass and lower CapabilityPass than `S′`. The S→S′ stimulus
contrast therefore moves this second model's endpoints too.

## What this does not support

Everything in §5 of the frozen design, unchanged. In particular:

1. This is **not** a replication of Study 4B and does not confirm, disconfirm, or
   reinterpret any Study-4B or Study-4C result. Different model, different and
   unverifiable serving stack, one repeat instead of four, no matched-control arms.
2. Rates are **not** comparable to the Ornith-1.5-35B arms — only the direction is
   being described. That `Δ_security` here (+0.5532) sits near the Study-4B value
   is a coincidence of two incomparable measurements, not agreement.
3. Nothing here bears on the Study-4C mechanism question. No matched placebo or
   contract-reinforcement arm was run, so no part of either shift can be assigned
   to a content-specific or to a nonspecific component.
4. Nothing here bears on Study-3 specification-level determination, which is a
   different construct from model pass behaviour.
5. Nothing here generalises beyond DS=47, and nothing enters the paper synthesis,
   the claim/evidence matrix, or any frozen artifact without a separate
   cross-model exploratory label.

With one repeat there is no within-condition variance estimate; the CIs are over
task-level differences only. This is a directional probe.

## Deviations

1. **Post-generation patch to `study4x_run.py`.** The reused helper
   `study4b_execute.write_new_hashfile` writes paths relative to the Study-4B
   directory, so it raised `ValueError` after all 94 responses were already
   written and `study4x_generation_completion_FROZEN.json` was already frozen.
   A directory-local `write_new_hashfile`/`verify_hashfile` pair and an idempotent
   `hashes` stage were added, and the response manifest was written from the
   already-frozen completion record. No generation was re-issued, no response was
   re-read or altered, and no decision rule, endpoint, or read-out was touched.
   The script hash below is post-patch.
2. **No model-weight fingerprint gate.** A remotely served model cannot be
   fingerprinted the way the local MLX model was. Gate 6/7 pin the served model
   ID and a smoke call under the exact generation config instead. The provider
   returned no `system_fingerprint`.

## Standing constraints honoured

No Study-4B or Study-4C artifact was modified; both freezes were read only for
their frozen prompt text and evaluation oracle, whose hashes were re-verified
before and after evaluation. No repeat was added to the existing 376/752
completions and no post-hoc hypothesis search was run on them. This study is not
a "Study 4D" on the closed Ornith-1.5 line; it is a separately labelled
cross-model exploratory extension.

## Artifacts

| File | SHA-256 |
|---|---|
| `DESIGN_FROZEN.md` | `6632c086578660f80ced3caa09b3e745ae3e8a74d97ddc0f15650f2a4d85552d` |
| `study4x_run.py` | `56668d3a4d6668d94266c2588f7605e0bcbfff4394680b8d61c759543e2fd112` |
| `study4x_gate_report_FROZEN.json` | `acbf5e562ecec4db0301e15169443246ed752218eed1d4e0d5e7502369f8b804` |
| `study4x_generation_completion_FROZEN.json` | `b3ca02adee17b125eed4f8e22456bf3e34de8f3c6169041fc8550a7c80afb22d` |
| `study4x_evaluation_FROZEN.json` | `4e88e5b726c11a1df0f1ec09c3f3f552c484624c9b8c016bcf4a738f064fc657` |
| `study4x_analysis_FROZEN.json` | `722827be103a58cd74217d5853c5a8e06708b137046113e4a0a08430c8bb4eeb` |

`SHA256SUMS_RESPONSES` indexes the 94 per-call transcripts, which stay on disk
and are quarantined from git. The API key was supplied through the environment
only and appears in no file in this repository.
