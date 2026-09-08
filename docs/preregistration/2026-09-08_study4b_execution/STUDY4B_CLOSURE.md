# Study 4B — Confirmatory Closure Record

Status: **CLOSED**. Scope: Study-3 frozen demonstrated-separable subset (DS = 47) only.

Closure manifest: `STUDY4B_CLOSURE_MANIFEST.json`
Machine verification: `python3 study4b_close.py verify`

## Execution record

| Item | Value |
|---|---|
| Generations completed | 376/376 |
| Retries | 0 |
| Transport failures | 0 |
| Empty completions | 0 |
| Non-runnable completions | 7 (S = 7, S' = 0) |
| Non-runnable scoring | zero on security, capability, and joint endpoints |
| Max-token truncations | 1 (S = 1, S' = 0) |
| Oracle preflight | 47/47 |
| Hard stops | none |
| Procedural deviations | none |

## Frozen endpoint table

Task-equal-weighted, 47 within-task differences, exact two-sided sign-flip test
matching the frozen condition-to-seed-arm randomization.

| Endpoint | S | S' | Delta (S - S') | 95% CI | task-diff SD | p |
|---|---:|---:|---:|---:|---:|---:|
| SecurityPass (primary) | 0.8723 | 0.3670 | +0.5053 | [0.3741, 0.6365] | 0.4469 | 4.07454e-09 |
| CapabilityPass (guardrail) | 0.6011 | 0.9521 | -0.3511 | [-0.4683, -0.2338] | 0.3993 | 1.3411e-07 |
| Joint Security AND Capability (secondary) | 0.5957 | 0.3298 | +0.2660 | [0.1051, 0.4268] | 0.5477 | 0.00234317 |

## Capability guardrail

**FAILED.** Preregistered equivalence margin was +/-5 pp. Observed
Delta_C = -0.3511, 95% CI
[-0.4683, -0.2338].
This is recorded as a failure, not a warning and not a pass.

## Frozen interpretation

Allowed:

> On the 47 frozen Study-3 demonstrated-separable tasks, the model was substantially more likely to pass the security oracle under the original determining specification than under the frozen underdetermined specification.

> However, the specification manipulation also produced a large capability-performance difference, despite capability determination having been preserved at the specification level. Therefore the observed security contrast cannot be interpreted as an isolated causal effect of removing safety-determining information while holding functional behavior constant.

Not allowed:

- determination causes +50.5pp security score inflation
- removing safety information alone causes the effect
- capability was behaviorally held constant
- the effect generalizes to SeCodePLT
- Study 4B rescues or replaces the failed fresh Study 4
- Study 3 was invalidated by the capability guardrail failure

Preserved distinction:

> Study-3 capability-determination preservation is a specification-level construct; Study-4B CapabilityPass is a model-performance outcome. A change in the latter does not imply the former was validated incorrectly.

## Study boundaries

Fresh-sample Study 4 remains a separate, separately closed study:
`0/160 validated pairs; NO-GO before behavioral evaluation`
(`docs/preregistration/2026-09-07_study4_calibration_execution/`).
Study 4B is not its continuation or replacement.

Studies 1-3 and `docs/paper_synthesis/` are unmodified by this line.

## Not performed at closure

Subgroup analysis, task-level failure analysis, completion-content taxonomy,
and explanation mining were not performed in the confirmatory line. Any later
exploratory work is separately labelled and may not alter the block above.

## Frozen artifact hashes

| Artifact | SHA-256 |
|---|---|
| `study4b_analysis_FROZEN.json` | `5fd37dd6ec0e35370090f8ecb42a955e0fb3e33872356e3b9ef085c42b546cdd` |
| `study4b_ds47_stimuli_SEALED.json` | `81ac8389d213998b95ad71fbfa431f3d6863a8371b9f04af0ebb5e790d7c84ef` |
| `study4b_evaluation_FROZEN.json` | `fba90188d0a10424bf60da8706717cd825f972708c18e6dc04c8cc222310a10b` |
| `study4b_execute.py` | `4e1a8af4e434a1a3bed1c498b33c94a9927b7abbc06436d0711c35e958f07d9a` |
| `study4b_execution_manifest_FROZEN.json` | `6dd078ae8b15523528ea1757f2269bf083f0945265972033faa8e3d1aa19b3ac` |
| `study4b_generation_completion_FROZEN.json` | `113f92a74ff2ecde1279c1b3f32d1d703d95a898669e4a31fac9972776db8bf1` |
| `study4b_generation_stimuli_FROZEN.json` | `f9373797e618e444b16568a71c9230694f2f9786c7122680830177e5a6ac7f23` |
| `study4b_prepare.py` | `c36e10b4745180157faa0686e29c912ce89af4985e70ff1f493ece55ff0fd84e` |
| `study4b_readiness_manifest.json` | `30b98c43abbb12e9d7eb4d9dfcff2e6a1c144c1c0d167ef59a741c3335e5edcd` |
| `study4b_request_schedule_FROZEN.json` | `d5de92dc3925aa283183ea0fa5937af934ccb609931fa7408bab8c0c40abad93` |
| `test_study4b_execute.py` | `479f936a37e657151c2737d08815df8f7e80a65b94a991e74bfb218768e29318` |
| `test_study4b_prepare.py` | `06236c2df6b44c2648fe98edaefc8a941079cad83050f649a5a6df70b0a53850` |

Sealed stimuli (`study4b_ds47_stimuli_SEALED.json`,
`study4b_generation_stimuli_FROZEN.json`) and `generation_calls/` carry the
frozen hidden tests/oracle and full specification prompts. They stay on disk and
enter git as checksums only, matching the Study-3 convention. Frozen response
set: `07392d665a72bfc56f97367c52a6abfa59d19292479231bf129718ff46fa35d6`.
