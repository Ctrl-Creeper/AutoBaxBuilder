# Study 4X-CM — design amendment 1: repeats 2 and 3 (frozen before generation)

Amends `DESIGN_FROZEN.md`
(SHA-256 `6632c086578660f80ced3caa09b3e745ae3e8a74d97ddc0f15650f2a4d85552d`),
which pinned `REPEATS = 1`. That file is **not** edited; this amendment adds two
further repeats and is frozen before any repeat-2 or repeat-3 prompt is sent.
SHA-256 recorded in `SHA256SUMS_DESIGN_AMENDMENT_1`.

Everything in the original design that is not restated below carries over
unchanged — in particular §5 (prohibited conclusions), which applies verbatim to
this amendment and to the pooled analysis.

**Status: still EXPLORATORY. Still not a replication of Study 4B.** Adding
repeats reduces sampling noise within this model; it does not make the arms
comparable to the Ornith-1.5-35B arms, does not address the Study-4C mechanism
question, and does not license any claim beyond DS=47.

## 1. What is added

| | |
|---|---|
| Repeats added | 2 and 3 (repeat 1 is already frozen) |
| New generation calls | 47 × 2 × 2 = **94 per repeat, 188 total** |
| Total after amendment | 282 completions (3 repeats × 47 tasks × 2 conditions) |
| Model, endpoint, config | unchanged: `gpt-5.6-luna`, `https://ai.bnds.fun/v1`, temperature 0.2, top_p 1.0, max_tokens 8192 |
| Prompts | unchanged frozen projection and per-prompt hashes |
| Evaluation | unchanged frozen SeCodePLT harness and oracle; ITT-style scoring |

Per-request seeds for the new repeats are derived as
`sha256(root_seed | ds_task_id | condition | "R" + repeat)`, which includes the
repeat index. Repeat 1's seeds were derived without it; the new seeds are checked
to be distinct from repeat 1's and from each other. Request order within the new
batch is a seeded shuffle of the 188 units.

## 2. Gates (all must pass before the first new call)

Gates 1–9 of the original design are re-run. Additionally:

10. `study4x_generation_completion_FROZEN.json`, `study4x_evaluation_FROZEN.json`
    and `study4x_analysis_FROZEN.json` hash to their recorded values, and
    `SHA256SUMS_RESPONSES` verifies — repeat 1 is intact and is not rewritten.
11. All 94 repeat-1 transcripts are present and no new call collides with an
    existing `request_id`.

## 3. Read-out declared in advance

The primary read-out is the **pooled 3-repeat** estimate, using the original §4
rule applied to the task-equal-weighted mean of the 47 within-task S − S′
differences, where each task's condition mean is now over 3 repeats.

A secondary, pre-declared **stability** read-out is reported alongside it:

- **STABLE** if each of the three repeats, analysed alone, yields the same
  §4 category as the pooled estimate.
- **UNSTABLE** otherwise, in which case the per-repeat categories are reported
  and the pooled estimate is described as noisier than one repeat suggested.

Repeat 1's frozen analysis is not restated, revised, or replaced. The pooled
analysis is a new artifact that reads it.

## 4. What is still not permitted

No task-level or subgroup failure mining. No post-hoc hypothesis search over any
completion, in this study or in the closed Ornith-1.5 line. No further repeats
beyond 3 without another frozen amendment. No entry into the paper synthesis,
the claim/evidence matrix, or any frozen artifact without a separate cross-model
exploratory label.
