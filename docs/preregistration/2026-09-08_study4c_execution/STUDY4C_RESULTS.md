# Study 4C-EX — four-arm mechanism experiment, results

**Exploratory / mechanism-confirmation experiment designed after Study 4B.**
Not a Study-4B preregistered analysis. The Study-4B confirmatory result and its
**FAILED** capability guardrail are unchanged. Fresh Study 4 remains separately
closed at 0/160 → NO-GO.

**Permanent design limitation, frozen and not to be removed or weakened:**
S_placebo candidate authoring was negatively conditioned on knowledge from the
prior 20-task exploratory mechanism audit, because several candidate style rules
were rejected when they could plausibly repair previously observed defect modes.
Study 4C is therefore a mechanism experiment designed after Study 4B and **must
not be described as outcome-naive independent confirmation.**

## 1. Pre-generation gates

All 36 checks passed; outcome **GO**. Full record in
`study4c_validation_FROZEN.json` (sha `8e136ae8d7c8c408…`).

| Group | Result |
|---|---|
| Frozen inputs (stimuli, both blocks, design memo hashes) | 5/5 pass |
| G1 / D / P2 — constant diff, identical hash and length across 47 | 4/4 pass |
| P1 — same anchor, exactly once in all 47 | 2/2 pass |
| G2 / P3 — invertibility and additivity, both arms | 4/4 pass |
| A / G5 — determination fields present and byte-identical, nothing removed | 3/3 pass |
| B / P7 / G3 — oracle and task-token leakage | 2/2 pass |
| C / G4 — contract block purely referential, 6 bullets | 2/2 pass |
| P4 / P5 / P6 / P9 — placebo adds no interface, security, or adherence content | 5/5 pass |
| P8 — length match (163 vs 164 tokens; 844 vs 792 bytes) | 2/2 pass |
| G7 — model, tokenizer, served model, config, concurrency, oracle provenance, context | 7/7 pass |

Materialised prompt-token means: S′ 333.7, S 312.9, S_controlled 475.9,
S_placebo 476.9. The two added blocks are matched to within 1.0 token on the
realised stimuli.

**Two judgement calls, both recorded in the validation artifact rather than
resolved silently.**

1. *Gate A execution.* The frozen Study-3 determination instrument is a human
   coding instrument and was not re-run with human coders. Gate A was discharged
   structurally: S is preserved byte-exact as a contiguous additive subsequence
   of both derived arms, all eight determination-bearing fields are present in
   all 47 prompts, nothing is removed or reordered, and the inserted blocks add
   no task-specific token (B/P7) and no new functional content (C). Recorded as
   a deviation from the literal wording of validation A/G5.
2. *Gate B prose collisions.* Four bare English words in the contract block —
   `remove`, `name`, `value`, `signature` — also occur as dict keys or enum
   values inside the frozen oracle code of six tasks (Q04, Q20, Q29, Q38, Q49).
   Each is used in the block as ordinary prose ("function name and signature
   documented above", "return type and value semantics", "do not … remove any
   security requirement"); none is an expected return value, expected exception,
   or domain constant, and both blocks are byte-identical across all 47 tasks, so
   none can carry task-specific information. They are enumerated by name and task
   in the validation record as declared prose collisions. Residual leakage after
   that enumeration: **empty for both blocks**. The blocks were not modified.

## 2. Generation integrity

**752/752 completed.** No hard stop, no deviation from the frozen schedule.

| | |
|---|---|
| Requests | 752 / 752 |
| Returned model | `Ornith-1.5-35B-A3B-Abliterated-MLX-4bit`, single value, no drift |
| `system_fingerprint` | absent on all responses (server returns none), no drift |
| Transport attempts | 752 (one per request); requests with retry: **0** |
| Content present | 752 / 752 |
| `finish_reason=length` | 3 (S_controlled 2, S_placebo 1) |
| Completion tokens | 224,024 total |
| Wall clock | ≈ 28 min generation, ≈ 12 min evaluation |
| Manual repair of completions | none |

Randomization executed as frozen: root seed
`11683815625601713154` from `sha256(stimuli|block_ctrl|block_placebo)`, four
repeat blocks of 188 units each independently shuffled, FIFO, concurrency 2.
Arm × run-quartile balance exact at 47 per cell.

Runtime configuration was compared section-by-section against the frozen
Study-4B server settings; every section is identical except the per-run auth key.

## 3. Hashes

| Artifact | SHA-256 |
|---|---|
| `BLOCK_S_CONTROLLED.txt` | `43d721af6d4e6efda4d483d1ce19a775cb5ff59eb116edfe9b4f7b78da67e0ab` |
| `BLOCK_S_PLACEBO.txt` | `45fe8319bad04b70e8d72060f9129b13fffb05bf00d09caea25562e6da38c997` |
| `DESIGN_MEMO.md` (rev 2) | `7b9766a7768eeee658746b66599cd6a0db301fc09de0ae388064200f96e09f70` |
| `study4c_validation_FROZEN.json` | `8e136ae8d7c8c4081f3ccb99912c6ec52c0b6bd5c93ea5a2f21c60e1883b36e7` |
| `study4c_generation_stimuli_FROZEN.json` | `f0268033011ef143fa4ed3238bfe5c9b07475cbe271050e085a36d0ad0185698` |
| `study4c_request_schedule_FROZEN.json` | `eb3ab7e7e6c628643e773e80e686682641c2ac0a6c88ca2869725fa306ba8d54` |
| `study4c_execution_manifest_FROZEN.json` | `ed725a2685960bd5d205aefac0d4cbe07f6093bb18c8212a8dcd09ee1c1c6c0d` |
| `study4c_generation_completion_FROZEN.json` | `e56d1820b95bbea015c14c526e873609bb7af30e7bc5e6352cda97a4ac8efdbd` |
| response set | `e96d075387dad51e0714bf04c9f0494f26091042746a4a6618ea3c8988c3b3be` |
| `study4c_evaluation_FROZEN.json` | `ba8d6a89b92f9fd232bb2eb6b93f96809e8fae8febffa02ea7bbeba5ca6c0bbf` |
| `study4c_analysis_FROZEN.json` | `48778c565b521485f99e4a81f9a45d07a811f903d0f8aef28b76d84a41d47203` |

## 4. Four-arm rates

Task-equal-weighted across 47 tasks, 4 repeats per cell, ITT-style
(non-runnable = zero). Frozen SeCodePLT oracle; 47/47 patched-reference
preflight passed.

| Arm | SecurityPass | CapabilityPass | Joint |
|---|---:|---:|---:|
| S′ | 0.4096 | 0.9415 | 0.3936 |
| S | 0.9362 | 0.6383 | 0.6330 |
| S_controlled | 0.7660 | 0.5585 | 0.5213 |
| S_placebo | 0.8404 | 0.5638 | 0.5532 |

Non-runnable completions: S_controlled 6, S_placebo 5, S 1, S′ 0 (12 / 752).

## 5. Contrasts

Paired within task, paired-t 95% CI, n = 47.

| Contrast | Δ | 95% CI | SD |
|---|---:|---|---:|
| **Δ_C,mech** = C(S_controlled) − C(S_placebo) | **−0.0053** | [−0.0939, +0.0833] | 0.302 |
| **Δ_S,mech** = Sec(S_controlled) − Sec(S_placebo) | **−0.0745** | [−0.1909, +0.0420] | 0.397 |
| **Δ_S,preserve** = Sec(S_controlled) − Sec(S) | **−0.1702** | [−0.2695, −0.0709] | 0.338 |
| Δ_C,repair = C(S_controlled) − C(S) | −0.0798 | [−0.1743, +0.0147] | 0.322 |
| Δ_C,generic = C(S_placebo) − C(S) | −0.0745 | [−0.1493, +0.0004] | 0.255 |
| Δ_S,generic = Sec(S_placebo) − Sec(S) | −0.0957 | [−0.1580, −0.0335] | 0.212 |
| Reference: Sec(S) − Sec(S′) | +0.5266 | [+0.3930, +0.6602] | 0.455 |
| Reference: C(S) − C(S′) | −0.3032 | [−0.4197, −0.1867] | 0.397 |

Algebraic identity holds exactly: Δ_C,repair − Δ_C,mech − Δ_C,generic =
−1.4 × 10⁻¹⁷. This is arithmetic, not a mediation decomposition.

Within-run capability gap G = C(S′) − C(S) = 0.3032.

Reference arms reproduce the Study-4B behavioural pattern in this sample
(Study 4B: security +0.5053, capability −0.3511).

## 6. Pre-declared read-out

| Criterion | Threshold | Observed | Met |
|---|---|---|---|
| Substantial capability recovery | Δ_C,mech ≥ 0.152 and CI lower > 0.0758 and Δ ≥ 0.10 | −0.0053, lower −0.0939 | **no** |
| Security noninferior | lower bound of Δ_S,preserve and Δ_S,mech > −0.05 | −0.2695 and −0.1909 | **no** |
| H1 pattern (mech CI upper < 0.25·G) | upper < +0.0758 | +0.0833 | **no** (narrowly) |
| Generic effect within ±0.05 | CI inside ±0.05 | [−0.1493, +0.0004] | **no** |

**Interpretation: MIXED.** Recorded in `study4c_analysis_FROZEN.json` as
`MIXED_OR_INCONCLUSIVE`. This is the pre-declared outcome for this pattern, not
a fallback: two of the three mixed-triggers fired — security changed
substantially under the controlled block, and the placebo produced an unexpected
substantive effect of its own.

## 7. Narrowest conclusion the data support

Adding a constant instruction block to S at the frozen anchor **degraded
SecurityPass**, and it did so whether the block reinforced the interface contract
(−0.170, CI [−0.270, −0.071]) or governed only source layout (−0.096, CI
[−0.158, −0.034]). Reinforcing the interface contract produced **no detectable
capability recovery** relative to the length- and salience-matched placebo
(−0.005, CI [−0.094, +0.083]), and none relative to S itself.

Consequently:

- **H2 (implementation collateral damage) is not supported by this experiment.**
  The intervention designed to remove interface/return/exception deviations
  recovered no capability.
- **H1 is not established either.** Its read-out required security to be
  preserved; security was not preserved, so the arm that was supposed to isolate
  an intrinsic trade-off did not hold the safety manipulation fixed. The H1
  capability criterion also missed narrowly (CI upper +0.0833 against a +0.0758
  threshold).
- **The manipulation did not hold.** The security loss is the dominant result,
  and it is largely generic: more than half of it is reproduced by the placebo,
  which contains no security content whatsoever. Appending *any* additional
  constant instruction block at that anchor diluted the model's compliance with
  the safety requirement.

The four-arm design earned its cost precisely here. A three-arm design would
have observed S_controlled security 0.766 vs S 0.936 and attributed it to the
interface-contract content; the placebo shows that most of the drop is a generic
added-instruction effect.

What this does **not** establish: that safety and capability do not trade off;
that interface deviations are not part of the Study-4B capability loss; that a
differently-worded or differently-placed contract block would behave the same
way. The experiment tested one constant block at one anchor with one model, and
its manipulation-integrity criterion failed.

## 8. Deviations and hard stops

- **Hard stops during execution: none.** 752/752 generated, 752/752 evaluated.
- **One aborted freeze attempt before any model call**, recorded in
  `STUDY4C_FREEZE_ABORT_1.json`: the shared Study-4B hashfile writer resolved
  artifact paths relative to the Study-4B directory. Zero model calls had been
  made; partial freeze artifacts were deleted and the freeze re-run after the
  writer was localised. The blocks, the gates, and the seed derivation were
  unchanged by this.
- **Gate A discharged structurally rather than by re-running the human Study-3
  determination instrument** (§1, item 1).
- **Gate B implemented over task-specific code identifiers and test literals,
  with four bare English prose words enumerated as declared collisions** (§1,
  item 2). The blocks were not modified.
- Nothing was stopped, changed, or re-run on the basis of interim results. No
  repeats, blocks, samples, model settings, or analysis choices were altered
  after the freeze. No completion was manually repaired.
- No task-level, subgroup, or post-hoc mechanism mining was performed.
