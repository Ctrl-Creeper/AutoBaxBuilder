# Study 4X-CM — second model arm `gpt-5.6-sol`, repeats 1–3

**EXPLORATORY. NOT CONFIRMATORY. NOT A REPLICATION OF STUDY 4B.**
Amendment frozen before generation: `DESIGN_AMENDMENT_2.md`,
SHA-256 `79d3f57951f61e0f01b36a7a88e6e18c9c35372739340e56bf8bde1d5be20271`.
Original design and amendment 1 unchanged
(`6632c086…`, `ece34139…`). §5 of the original design applies verbatim below.

## Execution

| | `gpt-5.6-sol` | `gpt-5.6-luna` (already frozen) |
|---|---|---|
| Pre-generation gates | **11/11 GO** | 9/9 then 11/11 GO |
| Requests | **282/282** | 282/282 |
| Retried requests | 0 | 0 |
| Finish reasons | `stop` × 282 | `stop` × 282 |
| Completion tokens | 264,369 | 213,250 |
| Empty responses | 0 | 0 |
| Non-runnable | **0** | 1 (`Q16-S-R2`) |
| Oracle preflight | 47/47 | 47/47 |

The luna arm was verified byte-intact before the first sol call, again before
evaluation, and again before analysis: all six frozen luna artifacts hash to
their recorded values and both response indices verify. Sol transcripts were
written to the separate `generation_calls_sol/` directory; no luna transcript was
read or written. This arm's root seed is model-dependent, so its per-request
seeds differ from the luna arm's by construction.

## Pooled 3-repeat endpoints (task-equal-weighted, paired over the 47 tasks)

| Endpoint | S | S′ | Δ (S − S′) | 95% CI | sign-flip p |
|---|---:|---:|---:|---:|---:|
| SecurityPass | 0.9787 | 0.4610 | **+0.5177** | [+0.3612, +0.6742] | 2.38e-07 |
| CapabilityPass | 0.8440 | 1.0000 | **−0.1560** | [−0.2598, −0.0523] | 7.81e-03 |
| JointPass | 0.8440 | 0.4610 | **+0.3830** | [+0.1960, +0.5700] | 2.97e-04 |

Task-level difference signs (47 tasks): security 27 positive / 19 zero / 1 negative;
capability 0 positive / 39 zero / 8 negative; joint 24 / 18 / 5.

## Per-repeat estimates

| Repeat | Δ SecurityPass | 95% CI | Δ CapabilityPass | 95% CI | read-out |
|---|---:|---:|---:|---:|---|
| R1 | +0.5106 | [+0.3501, +0.6711] | −0.1489 | [−0.2546, −0.0433] | DIRECTIONAL_REPRODUCTION |
| R2 | +0.5106 | [+0.3501, +0.6711] | −0.1489 | [−0.2546, −0.0433] | DIRECTIONAL_REPRODUCTION |
| R3 | +0.5319 | [+0.3717, +0.6922] | −0.1702 | [−0.2818, −0.0587] | DIRECTIONAL_REPRODUCTION |

**R1 and R2 produce identical endpoint estimates. This was checked and is a
coincidence, not repeated or cached responses.** Only 13 of 94 (task, condition)
cells have byte-identical extracted code across R1 and R2, but 90 of 94 have
identical (SecurityPass, CapabilityPass) outcomes, and the four differing cells
cancel at the task-equal-weighted level. For reference, the luna arm's
cross-repeat code identity is comparable (12/94, 11/94, 14/94), so the sol arm is
not behaving more deterministically at the generation level.

## Pre-declared read-outs

- Pooled, this arm: **DIRECTIONAL_REPRODUCTION**.
- Stability across repeats: **STABLE** — R1, R2, R3 each fall in the same
  category alone.
- Cross-arm categorical agreement: **CONCORDANT** — the luna arm's pooled
  read-out is also DIRECTIONAL_REPRODUCTION.

All three rules were fixed in the frozen amendments before any prompt was sent.

## What this supports

On the frozen DS=47 subset, a second remote model responded to the S-versus-S′
contrast in the same direction as the first, in every one of three repeats: the
determining `S` specification produced markedly higher SecurityPass and lower
CapabilityPass. Two remote models now agree in direction.

## What this does not support

Unchanged from §5 of the frozen design, and a second model arm changes none of it:

1. This is **not** a replication of Study 4B and does not confirm, disconfirm, or
   reinterpret any Study-4B or Study-4C result.
2. Rates remain **not comparable** to the Ornith-1.5-35B arms; only direction is
   described.
3. **No numeric contrast between the two model arms is estimated** — no difference
   of deltas, no ratio, no test, no pooling of the two models into one estimate.
   That the two arms' deltas are numerically close is not evidence that they agree
   in magnitude; both are single models on an unverifiable serving stack, and the
   only claim made is categorical direction agreement.
4. Two models served by the same third-party proxy are **not** a representative
   sample of models. They may share a family, a serving configuration, or a system
   prompt; none of that is verifiable from outside. CONCORDANT here is weaker
   evidence of generality than two independently served models would be.
5. Nothing here bears on the Study-4C mechanism question. No matched placebo or
   contract-reinforcement arm was run in either arm.
6. Nothing here bears on Study-3 specification-level determination, which is a
   different construct from model pass behaviour.
7. Nothing here generalises beyond DS=47, and nothing enters the paper synthesis,
   the claim/evidence matrix, or any frozen artifact without a separate
   cross-model exploratory label.

## Deviations

None. All 282 calls completed on first attempt, all completions were runnable,
and no gate or integrity check failed.

## Standing constraints honoured

No Study-4B or Study-4C artifact was modified; both freezes were read only for
frozen prompt text and the evaluation oracle, whose hashes were re-verified before
and after evaluation. The luna arm was not rewritten. No repeat was added to the
existing 376/752 Ornith-1.5 completions and no post-hoc hypothesis search was run
on them. No task-level or subgroup failure mining was performed. The
cross-repeat code-identity check above is an integrity check on response
freshness, not outcome mining: it inspects only response hashes, not task
identities or failure content. No further model arms or repeats may be added
without another frozen amendment.

## Artifacts

| File | SHA-256 |
|---|---|
| `DESIGN_AMENDMENT_2.md` | `79d3f57951f61e0f01b36a7a88e6e18c9c35372739340e56bf8bde1d5be20271` |
| `study4x_sol.py` | `cdacdee94ef77e79cdd2e32008fd4bb210c257b26e0721923c32a7cf05b1102b` |
| `study4x_sol_gate_report_FROZEN.json` | `b4a85031b58e3a343162e6c447e0b1c6900d174c21da3866259d5050d285ed4b` |
| `study4x_sol_generation_completion_FROZEN.json` | `8e73fb64baebdd8545b3488df0d95e2108443f1b98d8d47172c36bb5a7259852` |
| `study4x_sol_evaluation_FROZEN.json` | `a6e63879e367839235f2c5a2a2b40ad711bc7acf2c0cd7f84f5e921149bab687` |
| `study4x_sol_analysis_FROZEN.json` | `88518a98184931f63a94daeea8d686b6fd92b151a67bcc05fff653a499da8fb0` |

`SHA256SUMS_RESPONSES_SOL` indexes the 282 sol transcripts, which stay on disk and
are quarantined from git. The API key was supplied through the environment only
and appears in no file in this repository.
