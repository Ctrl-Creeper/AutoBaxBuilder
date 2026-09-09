# Study 4X-CM — cross-model exploratory extension (design, frozen before generation)

**Status: EXPLORATORY. Not confirmatory. Not part of the frozen Study-4B/4C record.**
**Not a "Study 4D".** The closed Ornith-1.5 behavioural line is untouched: no
Study-4B/4C artifact is read for anything but its frozen prompt text, no repeat
is added to the existing 376/752 completions, and no post-hoc hypothesis search
is run on them.

Frozen: 2026-09-09, before any study prompt was sent to the remote endpoint.
SHA-256 of this file is recorded in `SHA256SUMS_DESIGN` and referenced by the
gate report. Nothing below may be changed after the first generation call.

## 1. Question

Does the S-versus-S′ specification contrast that moved this benchmark's
endpoints on one local model reproduce on a different, remotely served model?

This asks whether the *stimulus* contrast does anything on another model. It is
**not** a replication of Study 4B (different model, different serving stack,
one repeat instead of four, no matched-control arms) and it cannot confirm,
disconfirm, or reinterpret any Study-4B or Study-4C result.

## 2. Design

| | |
|---|---|
| Tasks | the frozen DS=47 demonstrated-separable subset |
| Conditions | `S`, `Sprime` (2 arms) |
| Repeats | 1 |
| Generation calls | 47 × 2 × 1 = **94** |
| Model | `gpt-5.6-luna` |
| Serving | third-party OpenAI-compatible proxy at `https://ai.bnds.fun/v1` |
| Endpoints | SecurityPass, CapabilityPass, JointPass |
| Estimand | task-equal-weighted mean of the 47 within-task S − S′ differences |
| Interval | paired-t 95% CI over the 47 task differences |
| p-value | exact two-sided task-level sign-flip test (descriptive here) |
| Scoring | ITT-style: non-runnable / unparseable completion scores 0 on every endpoint |

Prompts are read from the frozen, oracle-free Study-4C prompt projection
`study4c_generation_stimuli_FROZEN.json`
(SHA-256 `f0268033011ef143fa4ed3238bfe5c9b07475cbe271050e085a36d0ad0185698`),
columns `S` and `Sprime`, each row's per-prompt SHA-256 re-verified at run time.
No new prompt text is authored for this study.

Request order is a seeded shuffle of the 94 units; the root seed is
`sha256("study4x-crossmodel-v1|" + stimuli_sha256 + "|gpt-5.6-luna")`. Order has
no carried state — it is recorded for auditability, not for inference.

Generation config: `temperature 0.2`, `top_p 1.0`, `max_tokens 8192`, `stream false`,
plus a per-request derived `seed`. These are the *nominal* values Study 4B used.
The provider's sampler, quantization, system prompt, and routing are unknown and
unverifiable; identical nominal parameters do **not** make the arms comparable
to the Ornith-1.5-35B arms.

## 3. Pre-generation gates (all must pass; any failure is a hard stop)

1. `study4c_generation_stimuli_FROZEN.json` hashes to the value pinned above.
2. All 47 rows carry both `S` and `Sprime`, and every prompt's SHA-256 matches
   its recorded per-prompt hash.
3. The prompt projection declares `contains_hidden_tests_or_oracle == false`,
   and no prompt contains an oracle/unittest marker.
4. `study4b_ds47_stimuli_SEALED.json` hashes to
   `81ac8389d213998b95ad71fbfa431f3d6863a8371b9f04af0ebb5e790d7c84ef`
   (the evaluation oracle; used only at evaluation time).
5. Study-3 frozen oracle provenance verifies (`study4b_prepare.verify_sources`).
6. `GET /v1/models` lists `gpt-5.6-luna`.
7. A smoke `POST /v1/chat/completions` with the exact generation config and a
   **non-study** prompt returns `model == "gpt-5.6-luna"` and a usable choice.
8. The API key is present in the environment only. It is process-local and is
   never written to any file in this repository.
9. No Study-4B or Study-4C artifact is opened for writing at any stage.

The gate report is frozen to `study4x_gate_report_FROZEN.json` before the first
study prompt is sent.

## 4. Read-out declared in advance

- **Directional reproduction** if the SecurityPass difference is positive with a
  95% CI excluding 0 *and* the CapabilityPass difference is negative with a 95%
  CI excluding 0 — the same two-sided signature Study 4B produced.
- **Partial** if exactly one endpoint's CI excludes 0 in the Study-4B direction.
- **No reproduction** if neither CI excludes 0.
- **Opposite** if a CI excludes 0 in the direction opposite to Study 4B.

Whatever the outcome, the conclusion is limited to: *this stimulus contrast did
/ did not move this model's endpoints on this subset, under one repeat.*

## 5. Prohibited conclusions

No output of this study may state or imply that it:

1. replicates, confirms, or fails to replicate Study 4B;
2. generalises to SeCodePLT, to models in general, or to tasks outside DS=47;
3. bears on the Study-4C mechanism question, or on any share of the SecurityPass
   effect attributable to a nonspecific added-instruction component;
4. bears on Study-3 specification-level determination, which is a different
   construct from model pass behaviour;
5. is comparable to the Ornith-1.5-35B arms at the level of rates rather than
   direction;
6. may enter the paper synthesis, the claim/evidence matrix, or any frozen
   artifact without a separate cross-model exploratory label.

One repeat gives no within-condition variance estimate. With 94 completions and
an unverifiable serving stack, this study is a directional probe and nothing more.

## 6. Quarantine

Same convention as Studies 4B and 4C: materialized prompts and per-call
transcripts stay on disk and enter git only as checksums. The API key is
process-local and appears in no committed file.
