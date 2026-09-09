# Study 4X-CM — design amendment 2: second model arm `gpt-5.6-sol` (frozen before generation)

Amends `DESIGN_FROZEN.md`
(SHA-256 `6632c086578660f80ced3caa09b3e745ae3e8a74d97ddc0f15650f2a4d85552d`),
which pinned the single model `gpt-5.6-luna`, and stands alongside
`DESIGN_AMENDMENT_1.md`
(SHA-256 `ece341398a06f7f20afc0aa834730ddb90e41502f889fc152984a8bd310617f0`),
which added repeats 2 and 3. Neither file is edited. This amendment is frozen
before any `gpt-5.6-sol` prompt is sent; SHA-256 recorded in
`SHA256SUMS_DESIGN_AMENDMENT_2`.

Everything in the original design that is not restated below carries over
unchanged — in particular §5 (prohibited conclusions), which applies verbatim to
this arm.

**Status: still EXPLORATORY. Still not a replication of Study 4B.** A second
remote model widens the probe; it does not turn it into a confirmatory
cross-model study, and it does not license comparison against the
Ornith-1.5-35B arms.

## 1. What is added

| | |
|---|---|
| Model arm added | `gpt-5.6-sol`, same endpoint `https://ai.bnds.fun/v1` |
| Repeats | 1, 2, 3 (matching the luna arm after amendment 1) |
| New generation calls | 47 × 2 × 3 = **282** |
| Prompts | unchanged frozen projection and per-prompt hashes |
| Config | unchanged: temperature 0.2, top_p 1.0, max_tokens 8192 |
| Evaluation | unchanged frozen SeCodePLT harness and oracle; ITT-style scoring |

Transcripts for this arm are written to `generation_calls_sol/`, a **separate**
directory, because `request_id`s repeat across model arms. No file in
`generation_calls/` is read, written, or overwritten.

The randomization root seed is model-dependent —
`sha256("study4x-crossmodel-v1|" + stimuli_sha256 + "|gpt-5.6-sol")` — so this
arm's per-request seeds differ from the luna arm's by construction. Seeds are
derived as `sha256(root_seed | ds_task_id | condition | "R" + repeat)`, uniform
across all three repeats. Request order is a seeded shuffle of the 282 units.

## 2. Gates (all must pass before the first call in this arm)

Gates 1–9 of the original design are re-run against `gpt-5.6-sol`. Additionally:

10. All six frozen luna-arm artifacts hash to their recorded values, and both
    `SHA256SUMS_RESPONSES` and `SHA256SUMS_RESPONSES_R2R3` verify — the luna arm
    is intact and is not rewritten.
11. `generation_calls_sol/` is empty or absent at the start, and no path in it
    coincides with a luna transcript.

## 3. Read-out declared in advance

The primary read-out is the **pooled 3-repeat** estimate for this arm alone,
using the original §4 rule on the task-equal-weighted mean of the 47 within-task
S − S′ differences. The §3 stability read-out of amendment 1 (STABLE /
UNSTABLE across the three repeats) is reported alongside it.

A **third, descriptive-only** comparison is reported: whether the two model arms
fall in the same §4 category. This is a categorical agreement statement and
nothing more.

- **CONCORDANT** if both arms land in the same §4 category.
- **DISCORDANT** otherwise.

No numeric contrast between the two arms is estimated: no difference of deltas,
no ratio, no test, no pooling of the two models into a single estimate. Both are
single models on an unverifiable serving stack, and n = 2 models supports a
statement about direction agreement and nothing else.

The luna arm's frozen analyses are not restated, revised, or replaced.

## 4. What is still not permitted

No task-level or subgroup failure mining. No post-hoc hypothesis search over any
completion, in this arm, in the luna arm, or in the closed Ornith-1.5 line. No
further model arms or repeats without another frozen amendment. No claim that two
remote models constitute a representative sample of models. No entry into the
paper synthesis, the claim/evidence matrix, or any frozen artifact without a
separate cross-model exploratory label.
