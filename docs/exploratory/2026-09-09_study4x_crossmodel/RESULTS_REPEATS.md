# Study 4X-CM — repeats 2 and 3, and the pooled 3-repeat analysis

**EXPLORATORY. NOT CONFIRMATORY. NOT A REPLICATION OF STUDY 4B.**
Amendment frozen before generation: `DESIGN_AMENDMENT_1.md`,
SHA-256 `ece341398a06f7f20afc0aa834730ddb90e41502f889fc152984a8bd310617f0`.
Original design unchanged: `DESIGN_FROZEN.md`,
SHA-256 `6632c086578660f80ced3caa09b3e745ae3e8a74d97ddc0f15650f2a4d85552d`.
§5 of the original design (prohibited conclusions) applies verbatim below.

## Execution

| | Repeats 2–3 | Repeat 1 (already frozen) |
|---|---|---|
| Pre-generation gates | **11/11 GO** | 9/9 GO |
| Requests | **188/188** | 94/94 |
| Retried requests | 0 | 0 |
| Finish reasons | `stop` × 188 | `stop` × 94 |
| Completion tokens | 141,353 | 71,897 |
| Empty responses | 0 | 0 |
| Non-runnable | 1 (`Q16-S-R2`, `PROGRAM_NO_RESULT`, scored 0 on all endpoints per ITT) | 0 |
| Oracle preflight | 47/47 | 47/47 |

Repeat 1 was verified byte-intact before the first new call, again before
evaluation, and again before pooling: the three repeat-1 frozen artifacts hash to
their recorded values and `SHA256SUMS_RESPONSES` verifies. No repeat-1 file was
rewritten. New `request_id`s and per-request seeds were checked to be distinct
from repeat 1's and from each other before any call was issued.

Total after the amendment: **282 completions** (3 repeats × 47 tasks × 2 conditions).

## Pooled 3-repeat endpoints (task-equal-weighted, paired over the 47 tasks)

| Endpoint | S | S′ | Δ (S − S′) | 95% CI | sign-flip p |
|---|---:|---:|---:|---:|---:|
| SecurityPass | 0.9716 | 0.4184 | **+0.5532** | [+0.4144, +0.6920] | 4.66e-09 |
| CapabilityPass | 0.8298 | 1.0000 | **−0.1702** | [−0.2657, −0.0748] | 2.44e-04 |
| JointPass | 0.8298 | 0.4184 | **+0.4113** | [+0.2403, +0.5823] | 3.96e-05 |

Task-level difference signs (47 tasks): security 30 positive / 16 zero / 1 negative;
capability 0 positive / 34 zero / 13 negative; joint 26 / 14 / 7.

## Per-repeat estimates

| Repeat | Δ SecurityPass | 95% CI | Δ CapabilityPass | 95% CI | read-out |
|---|---:|---:|---:|---:|---|
| R1 | +0.5532 | [+0.4056, +0.7007] | −0.1702 | [−0.2818, −0.0587] | DIRECTIONAL_REPRODUCTION |
| R2 | +0.5106 | [+0.3501, +0.6711] | −0.2128 | [−0.3342, −0.0913] | DIRECTIONAL_REPRODUCTION |
| R3 | +0.5957 | [+0.4501, +0.7414] | −0.1277 | [−0.2267, −0.0286] | DIRECTIONAL_REPRODUCTION |

## Pre-declared read-outs

- Pooled: **DIRECTIONAL_REPRODUCTION** — both CIs exclude zero, security positive
  and capability negative.
- Stability: **STABLE** — all three repeats analysed alone fall in the same
  category as the pooled estimate.

Both rules were fixed in §3 of the frozen amendment before any repeat-2 or
repeat-3 prompt was sent. The per-repeat spread is visible in the table:
Δ security ranges 0.511–0.596 and Δ capability ranges −0.213 to −0.128 across
repeats, so the direction is reproducible within this model while the magnitude
moves by several points between repeats.

## What this supports

On the frozen DS=47 subset, across three independent repeats, `gpt-5.6-luna`
responded to the S-versus-S′ contrast in the same direction every time: the
determining `S` specification produced markedly higher SecurityPass and lower
CapabilityPass. The single-repeat result was not a sampling artifact of one draw.

## What this does not support

Unchanged from §5 of the frozen design, and the added repeats change none of it:

1. This is **not** a replication of Study 4B and does not confirm, disconfirm, or
   reinterpret any Study-4B or Study-4C result. Different model, different and
   unverifiable serving stack, no matched-control arms.
2. Rates remain **not comparable** to the Ornith-1.5-35B arms; only the direction
   is described. Three repeats sharpen the within-model estimate and do nothing
   for cross-model comparability.
3. Nothing here bears on the Study-4C mechanism question. No matched placebo or
   contract-reinforcement arm was run, so no part of either shift can be assigned
   to a content-specific or to a nonspecific component.
4. Nothing here bears on Study-3 specification-level determination, which is a
   different construct from model pass behaviour.
5. Nothing here generalises beyond DS=47, and nothing enters the paper synthesis,
   the claim/evidence matrix, or any frozen artifact without a separate
   cross-model exploratory label.

## Deviations

1. **Repeat-1 seed derivation did not include the repeat index.** Repeat 1's
   seeds were derived from `(root_seed, ds_task_id, condition)`; the new repeats
   use `(root_seed, ds_task_id, condition, repeat)`. The gate checked that all
   282 seeds are pairwise distinct. Recorded because the derivation string is not
   uniform across repeats.
2. **One non-runnable completion** (`Q16-S-R2`) was scored zero on every endpoint
   under the pre-declared ITT rule rather than dropped.

## Standing constraints honoured

No Study-4B or Study-4C artifact was modified; both freezes were read only for
frozen prompt text and the evaluation oracle, whose hashes were re-verified before
and after evaluation. No repeat was added to the existing 376/752 Ornith-1.5
completions and no post-hoc hypothesis search was run on them. No task-level or
subgroup failure mining was performed here. This remains a separately labelled
cross-model exploratory extension, not a "Study 4D". No further repeats may be
added without another frozen amendment.

## Artifacts

| File | SHA-256 |
|---|---|
| `DESIGN_AMENDMENT_1.md` | `ece341398a06f7f20afc0aa834730ddb90e41502f889fc152984a8bd310617f0` |
| `study4x_repeats.py` | `64961aebb5a461c1f352f0785d537677dfce2317c1543d974198e860320a1839` |
| `study4x_r2r3_gate_report_FROZEN.json` | `8d859c0eaf6d06b7f7a534cac2078f445e16cffae51722e9165af4575d6b5e93` |
| `study4x_r2r3_generation_completion_FROZEN.json` | `31de1e394d52662024c58b6548f2122c273bb008a81b0a279bce657e8f8aad28` |
| `study4x_r2r3_evaluation_FROZEN.json` | `fc3a05dfb522efa97c801d08cc894c33d3af8e101ca6b37b2ca8b780def2e7e2` |
| `study4x_pooled_analysis_FROZEN.json` | `d5136dd90939f2ac7ffc40943e6b13828d25705e44082d4cb87f84ec48874b9c` |

`SHA256SUMS_RESPONSES_R2R3` indexes the 188 new per-call transcripts, which stay
on disk and are quarantined from git. The API key was supplied through the
environment only and appears in no file in this repository.
