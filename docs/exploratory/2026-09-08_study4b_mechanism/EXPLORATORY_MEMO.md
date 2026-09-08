# POST-HOC EXPLORATORY MECHANISM ANALYSIS — Study 4B

**This is not a confirmatory analysis.** Every number below is post-hoc and
descriptive. It does not revise, reinterpret, or soften the frozen Study-4B
confirmatory result, and it introduces no new p-values, no new endpoints, and no
new generations.

Frozen inputs (read-only): `study4b_generation_completion_FROZEN.json`,
`study4b_evaluation_FROZEN.json`, `study4b_analysis_FROZEN.json`,
`study4b_ds47_stimuli_SEALED.json`, `STUDY4B_CLOSURE_MANIFEST.json`. Hashes in
`EXPLORATORY_MANIFEST.json`. Taxonomy frozen before any completion was inspected:
`TAXONOMY_FROZEN.md`, SHA-256 `ff7e546f951ad5f6…`.

## Confirmatory result, unchanged

| Endpoint | S | S' | Delta | 95% CI | p |
|---|---:|---:|---:|---:|---:|
| SecurityPass | 0.8723 | 0.3670 | +0.5053 | [0.3741, 0.6365] | 4.07e-09 |
| CapabilityPass | 0.6011 | 0.9521 | −0.3511 | [−0.4683, −0.2338] | 1.34e-07 |
| Joint | 0.5957 | 0.3298 | +0.2660 | [0.1051, 0.4268] | 0.0023 |

Capability guardrail: **FAILED**. Frozen interpretation stands as written in
`STUDY4B_CLOSURE.md`.

## Deviation from the requested procedure

Behavioural-strategy coding was done by a frozen mechanical classifier applied to
**all 376** completions, rather than by hand-coding a blinded sample. The
classifier receives only the code string and the target function name — it cannot
condition on treatment or outcome because those are not in scope at classification
time. This is stronger blinding and full coverage; the cost is that the categories
are syntactic proxies, not semantic judgements. Flagging it for your call.

## 1. Program length and executability

| | S | S' |
|---|---:|---:|
| Completion tokens (mean / median) | 398.2 / 267.5 | 129.2 / 74.0 |
| Extracted code lines (mean) | 39.8 | 12.7 |
| Response characters (mean) | 1711 | 544 |
| Truncated at 8192 | 1 | 0 |
| Non-runnable | 7 (3.72%) | 0 (0%) |

Capability delta, all completions (frozen ITT): **−0.3511**.
Capability delta, runnable completions only (descriptive, not ITT): **−0.3209**.

**Non-executability does not account for the capability gap.** Non-runnable
completions are 3.7% of the S arm, so they can shift the capability contrast by at
most ~3.7 pp; dropping them moves it from −35.1 pp to −32.1 pp. Truncation is a
single completion and is negligible. This explanation is refuted, not merely
weakened.

The runnable-only figure is reported strictly as a mechanism description. It
conditions on a post-treatment variable and cannot replace the frozen ITT-style
estimate.

## 2. Specification complexity

| | S | S' |
|---|---:|---:|
| Prompt characters (mean / median) | 1422 / 1312 | 1434 / 1335 |
| Prompt tokens (mean / median) | 324.9 / 283 | 345.7 / 335 |
| Field markers (mean) | 8.17 | 7.09 |

**The two specifications are of near-identical size**; S' is marginally *longer*
in tokens and carries about one fewer field marker. So the 3× divergence in
completion length is not a downstream consequence of a larger or denser prompt.
It is a behavioural response to a specification of the same size.

Association between completion length and outcomes (all 376 completions):
r = **−0.294** with CapabilityPass, r = **+0.077** with SecurityPass.

Rates by within-condition completion-length quartile:

| Quartile (median tokens) | S security | S capability | S' security | S' capability |
|---|---:|---:|---:|---:|
| Q1 | 0.936 (102) | 0.830 | 0.404 (36) | 1.000 |
| Q2 | 0.872 (223) | 0.511 | 0.106 (58) | 1.000 |
| Q3 | 0.915 (338) | 0.596 | 0.511 (111) | 0.979 |
| Q4 | 0.766 (611) | 0.468 | 0.447 (263) | 0.830 |

Within S, longer completions are associated with lower capability while security
stays high. Within S', capability is at ceiling regardless of length. Association
only — length is itself an outcome of the manipulation, not a manipulated
variable.

## 3. Behavioural strategy (frozen taxonomy)

Category rates, mechanically coded, condition-blind:

| Category | S | S' |
|---|---:|---:|
| restrictive_rejection | 0.872 | 0.537 |
| added_validation | 0.771 | 0.532 |
| sanitization_filtering | 0.207 | 0.117 |
| extra_exception_handling | 0.255 | 0.239 |
| refusal_or_noop | 0.000 | 0.000 |
| unrelated_implementation_divergence | 0.000 | 0.000 |
| unparseable | 0.005 | 0.000 |

AST counts (mean): `if` 4.54 vs 1.96; `raise` 2.05 vs 1.03; `return` 3.26 vs 2.09;
`try` 0.31 vs 0.26.

Outcome association for the largest-moving category, pooled across conditions:

| restrictive_rejection | n | security | capability |
|---|---:|---:|---:|
| absent | 111 | 0.468 | 0.982 |
| present | 265 | 0.683 | 0.691 |

Completions containing a rejection path are associated with **higher security and
lower capability**; completions without one are associated with the reverse. A
single behavioural shift — guard-and-reject density — is associated with both
halves of the confirmatory result. Consistent with a possible mechanism; this is
not a mediation claim and no mediation analysis was run.

Note that `extra_exception_handling` barely moves (0.255 vs 0.239). The shift is
specifically in guarding and rejecting, not in defensive coding generally.

## 4. Effect concentration

Distribution of the 47 task-level security differences: median **0.50**, IQR
**[0.00, 1.00]**, range [−0.25, 1.00]. Positive **32**, zero **13**, negative
**2**.

Leave-one-task-out range for the headline: **[0.4946, 0.5217]**.
Top-5 tasks contribute 21.1% of the total; excluding them the mean is **0.446**.
Top-10 contribute 42.1%.

**The effect is not driven by a small number of tasks.** No single task moves the
estimate by more than ~1.6 pp, and removing the five largest contributors still
leaves +44.6 pp.

## 5. Capability–security trade-off

Task-level sign pattern of the S→S' change (47 tasks):

| Cell | n |
|---|---:|
| security up / capability down | 20 |
| security up / capability flat | 12 |
| security flat / capability flat | 8 |
| security flat / capability down | 4 |
| security down / capability down | 2 |
| security flat / capability up | 1 |

Descriptive conditioning on the post-treatment capability outcome:

| Condition | security given capability pass | security given capability fail | n capability fail |
|---|---:|---:|---:|
| S | 0.991 (n=113) | 0.693 | 75 |
| S' | 0.346 (n=179) | 0.778 | 9 |

The most informative row: **among completions that pass the capability tests,
security is 0.991 under S and 0.346 under S'.** The security contrast is therefore
not simply an artifact of S producing broken programs — it persists, and widens,
among programs that are functionally correct by the frozen oracle. This is a
conditioning on a post-treatment variable across two differently-sized surviving
populations (113 vs 179) and is subject to collider bias; it is descriptive
evidence, not an estimate.

## Strongest plausible explanations

1. **Guard-and-reject shift.** Under S the model writes substantially more
   validation and rejection logic (87.2% vs 53.7% of completions; 2.3× the `if`
   density). This is associated with passing the safety oracle and with failing
   capability tests. It is the single description consistent with both endpoint
   movements and with the length divergence at constant prompt size.
2. **Two distinct programs, not one program plus a bug.** With zero refusals, zero
   unrelated implementations, and 3.7% non-executability, the arms differ by
   behavioural strategy, not by generation failure.

## Explanations the data contradict

- The capability gap is caused by non-runnable output — **refuted** (≤3.7 pp of a
  35.1 pp gap).
- The capability gap is caused by truncation — **refuted** (1 completion).
- The completion-length divergence follows from a longer or denser S prompt —
  **refuted** (S' prompts are marginally longer).
- The security effect is carried by a few tasks — **refuted** (LOO range 2.7 pp
  wide; 32/47 tasks positive).
- Under S the model refuses or writes something unrelated — **refuted** (0 and 0).
- The security effect is entirely an artifact of S producing broken code —
  **not supported**; the gap is larger among capability-passing completions.

## What remains indistinguishable

- **Over-restriction versus test strictness.** Whether S completions genuinely
  reject legitimate inputs, or whether the frozen capability tests penalise
  defensive-but-acceptable behaviour, produces the same signature here.
  Separating them requires per-task oracle semantics — task-level failure mining,
  which was not performed and would need its own design.
- **Which property of the transformation matters.** Study 4B moves one bundled
  variable. Whether removing safety-determining information specifically, or some
  co-varying property of the S' rewrite, produced the shift cannot be answered by
  this design.
- **Length as cause versus symptom.** Completion length is associated with lower
  capability, but length is itself an outcome. Nothing here distinguishes "longer
  code breaks capability" from "both reflect a defensive-coding mode."
- **Whether the guard-and-reject shift is on the causal path.** Establishing that
  would require an independent design that manipulates it. No mediation claim is
  made or supported.

## Preserved distinction

Study-3 capability-determination preservation is a specification-level construct.
Study-4B CapabilityPass is a model-performance outcome. The behavioural divergence
documented above is a fact about how this model responded to the two
specifications; it does not indicate that Study-3's specification-level validation
was performed incorrectly.

## Scope

Fresh-sample Study 4 remains separately closed at 0/160 → NO-GO before behavioral
evaluation. Nothing here extends to SeCodePLT generally, to other models, or to
tasks outside the frozen DS=47 subset.
