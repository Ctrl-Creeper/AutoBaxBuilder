# Paper architecture v1

**Document type:** frozen-artifact synthesis, not a preregistration.  
**Revision:** 2. Revision 1 was frozen at commit `1dda9cf5b3abdca8930900fdc8ac0d92234bb3b8`.  
**Evidence cutoff:** Study 3 final freeze `8c39ad48f90f1369bf8729b3585cb17079349042`, extended by
the frozen Study-4B closure and the frozen Study-4C-EX closure.  
**Scope:** no new data, no task-level reanalysis. Sections 1-5 are unchanged in substance from
revision 1; the behavioural line is confined to the new section 6.

## Central thesis and claim boundary

Within SeCodePLT, model-visible task specifications frequently determine the security-oracle
behaviour that the benchmark later scores. Determination is measurable with a prospectively frozen,
quotation-grounded instrument, and much of it is constructively removable for the realized
measured-eligible confirmatory sample while preserving capability determination. Consequently, a
security score on such cases cannot by itself distinguish spontaneous security behaviour from
compliance with an explicit requirement. This is a construct-validity threat, not a demonstrated
estimate of score inflation.

The paper does **not** claim that all security benchmarks have this prevalence, that every task is
separable, that no obstruction exists, or that models actually exploit the determining information.

A behavioural follow-up line was executed after the Studies 1-3 freeze and is reported in section 6.
It changes the claim boundary in one direction only: it shows that the specification condition
matters to one frozen model's behaviour on a selected subset, and it still supplies **no**
score-inflation magnitude and **no** identified mechanism. Nothing in section 6 revises the
central thesis or any Studies 1-3 claim.

## 1. Motivation and construct problem

Frame the measurement problem using the distinction between ordinary functional specification
following and the security capability a security benchmark is intended to isolate. If the
model-visible specification already obliges the exact security-oracle behaviour, passing the test
is compatible with both constructs. The benchmark response is therefore not diagnostic between
them.

Use the previously frozen AutoBaxBuilder/BaxBench/CWEval/PurpleLlama structural work only as
motivation and complementary characterization. It must not be presented as a common Definition-D
prevalence estimate across benchmarks.

**Primary contribution introduced here:** a claim-evidence discipline that separates (a) existence
and prevalence of determination, (b) reproducibility of its measurement, (c) constructive
removability, and (d) the unmeasured causal consequence for model scores.

## 2. Definition and measurement

Introduce Definition D at the case level:

> A specification `S` determines behaviour `b` at input `i` when a competent implementer reading
> only `S`, without the test suite, would be obliged to produce `b`; any alternative would contradict
> an identifiable sentence of `S`.

Both frozen restrictions are load-bearing: a determined judgment requires a locatable quotation,
and reaching the behaviour permits at most one inferential step with no external knowledge.

Place **Study 2** here as the prospective validation of J1, and only J1:

- 90 tasks and 442 cases; two independent blinded coding runs;
- raw agreement `0.937`;
- primary task-cluster-aware kappa `0.804`, 95% CI `[0.708, 0.893]`;
- pooled kappa `0.869` is descriptive only;
- AC1 `0.877`, 95% interval `[0.808, 0.936]`, is sensitivity only;
- tie-break rates were `18.8%` and `24.0%`.

The text must say **independent blinded coding runs**, not independent human coders. Shared model or
prompt lineage leaves correlated error possible.

The J3 failure belongs in the main text: both runs returned the existential answer `true` for all
90 tasks. A constant response supplies no discriminative reliability evidence. Study 2 therefore
validated the Definition-D/J1 measurement primitive, not constructibility annotation or the earlier
five-class taxonomy.

Put full prompts, schemas, cluster-bootstrap mechanics, pooled-kappa rationale, ICCs, quote
concordance, and disagreement diagnostics in the appendix.

## 3. Original-specification prevalence

Place **Study 1** here. Its estimand is case-weighted determination in the eligible SeCodePLT frame
of 864 tasks, measured on a frozen random sample of 90 tasks containing 442 cases (237 capability,
205 safety). `S_t` is the benchmark's shipped model-visible prompt with
`include_security_policy=True`.

Headline estimates:

| Estimand | Two-run mean | Measurement-disagreement interval | Task-cluster bootstrap 95% CI |
|---|---:|---:|---:|
| `theta_saf` | `0.7805` | `[0.7707, 0.7902]` | `[0.7040, 0.8492]` |
| `theta_cap` | `0.6899` | `[0.6751, 0.7046]` | `[0.5964, 0.7813]` |

Study 1's internal reliability on original specifications was raw agreement `0.9751` and
task-cluster-aware kappa `0.8689`, with bootstrap 95% CI `[0.7657, 0.9685]`.

The `security_policy` quote-location analysis is partial identification, not source attribution.
Among determined safety cases, the lower bound on survival after removing only the
`security_policy` field was `0.8428` in run 1 and `0.7205` in run 2; the conservative both-agree
variant was `0.7215`. Equivalently, that switch could remove at most `0.1572` and `0.2795` of the
respective runs' determined safety cases. Quotes locate one witness; they do not prove a unique
cause or carrier.

Keep the case-weighted estimand explicit. Do not rewrite `theta_saf` as the share of tasks, the
whole benchmark, or benchmarks in general.

## 4. Constructive separability

Place **Study 3** here as an evidence-producing procedure, not an annotation exercise. Its
population is the realized measured-eligible confirmatory sample. A task is demonstrated separable
(DS) only when both blinded verification runs find that the produced candidate specification
determines every capability case and no safety case. Verified obstruction (VO) requires a valid
frozen sufficient certificate; all other states are unresolved (UR).

Frozen result:

- measured-eligible confirmatory `m = 53`;
- `DS = 47`, `VO = 0`, `UR = 6`, procedure-invalid `= 0`;
- L0 sample identification region `[47/53, 1] = [0.8868, 1]`;
- separate L1 Clopper-Pearson 95% endpoint intervals: `pi_DS [0.7697, 0.9573]` and
  `pi_VO [0, 0.0672]`;
- preregistered L2 measurement sensitivity: both-runs DS share `0.8868`, either-run DS share
  `0.9811`; both-agree eligibility `53`, either-agree sensitivity count `56`.

L0 identification uncertainty, L1 sampling uncertainty, and L2 measurement sensitivity must remain
visually and verbally separate. The 88.7% figure is conditional on measured eligibility and is not
a prevalence estimate for the full benchmark.

Disclose the execution history in the main text: Writer Run 1 ended in a frozen
`WRITER_INSTRUMENT_CONTRACT_FAILURE`; the bounded repair was frozen without using candidate
substance; fresh Run 2 returned `ACCEPT_FIRST_RUN2` and became the sole formal constructive path.
Give the full GAP-6/GAP-8 manifests and interface audit in the appendix.

Also disclose in the main text that VO-DEFECT was permanently closed because the frozen instrument
lacked a sufficiently operationalized independent evidence-production and attestation procedure.
`VO = 0` therefore means that no obstruction was established by the valid frozen VO procedure, not
that no obstruction exists. Detailed VO audit history belongs in the appendix.

## 5. Cross-benchmark portability and limitations

Report the **CWEval preregistered replication** as attempted and terminated before outcome
observation. The frozen case object could not be mechanically recovered across the frame because
83% of security cases used oracle representations requiring a new, unfrozen semantic extraction
layer. No CWEval Definition-D prevalence may be reported.

Allowed complementary characterization includes the frozen A/B/C oracle-representation counts
(16/39/59 files and 32/44/110 security cases) and the earlier structural classifier record, clearly
labelled as representation structure rather than specification leakage. The termination supports
one claim: the measurement interface does not automatically transport across oracle
representations. It does not show that CWEval has more, less, or equal determination.

Collect the remaining limitations here: formal prevalence is SeCodePLT-only; coding runs are not
human coders; Study 3 is conditional on measured eligibility; its upper endpoint is uninformative
because no valid VO certificate was established; and the constructive writer procedure provides a
lower bound rather than an exhaustive search.

Put detailed CWEval exposure ledgers, frame construction, termination gates, and other benchmarks'
structural tables in the appendix.

## 6. Behavioural follow-up on a selected subset

This section reports the behavioural line and must be read as a corroborating follow-up, not as the
paper's identification strategy. It has three parts, in this order.

### 6.1 Fresh-sample Study 4: preregistered, stopped at its yield gate

Report first, so that the selected-subset work is not mistaken for it. A fresh-sample behavioural
study was preregistered and stopped at its frozen pipeline-yield gate with `0/160` validated
original/blinded specification pairs, before any behavioural evaluation. Frozen decision: `NO-GO`.
It is a separate, separately closed study. Studies 4B and 4C are neither its continuation nor its
replacement, and no fresh-sample behavioural estimate exists.

### 6.2 Study 4B: selected-subset behavioural follow-up

Population: the frozen Study-3 demonstrated-separable subset, `DS = 47`, entered in full with no
outcome-based selection. Design: paired `S` versus `S'`, 4 repeats per condition, 376 generations,
one frozen local model and decoding policy, randomized condition-to-seed-arm assignment, ITT-style
scoring with non-runnable completions scored zero. Execution: 376/376, zero retries, zero hard
stops, 47/47 oracle preflight.

| Endpoint | S | S' | Delta (S - S') | 95% CI | p |
|---|---:|---:|---:|---:|---:|
| SecurityPass (primary) | `0.8723` | `0.3670` | `+0.5053` | `[0.3741, 0.6365]` | `4.07e-09` |
| CapabilityPass (guardrail) | `0.6011` | `0.9521` | `-0.3511` | `[-0.4683, -0.2338]` | `1.34e-07` |
| Joint (secondary) | `0.5957` | `0.3298` | `+0.2660` | `[0.1051, 0.4268]` | `0.00234` |

The preregistered capability guardrail, an equivalence margin of +/-5 pp, **FAILED**. Report it as a
failure in the main text, in the same table, not in a footnote.

The allowed reading and its mandatory qualifier must appear together, in this order and in the same
paragraph:

> On the frozen 47 demonstrated-separable tasks, model behavior was strongly sensitive to the S
> versus S' specification condition: the determining S condition substantially increased
> SecurityPass while substantially reducing CapabilityPass.

> Because CapabilityPass also changed substantially, the SecurityPass contrast cannot be interpreted
> as the isolated causal effect of safety-determining information while functional performance is
> held constant.

Never print the first sentence without the second.

### 6.3 Study 4C-EX: post-4B exploratory mechanism experiment

Label its grade explicitly wherever it appears. Study 4C was designed **after** Study 4B and after a
20-task exploratory audit of Study-4B completions, and its placebo authoring was negatively
conditioned on that audit: candidate style rules were rejected when they could plausibly repair
previously observed defect modes. It must not be described as outcome-naive independent
confirmation.

Design: the same 47 tasks under four arms - `S'`, `S`, `S_controlled` (`S` plus a constant
interface-contract block at a single verified anchor), `S_placebo` (`S` plus a length-, structure-,
and salience-matched source-layout block carrying no interface, security, or adherence content) - 4
repeats each, 752 fresh generations, no Study-4B completion reused, 36/36 pre-generation
manipulation-validation gates passed before any generation.

| Arm | SecurityPass | CapabilityPass |
|---|---:|---:|
| `S'` | `0.4096` | `0.9415` |
| `S` | `0.9362` | `0.6383` |
| `S_controlled` | `0.7660` | `0.5585` |
| `S_placebo` | `0.8404` | `0.5638` |

| Contrast | Delta | 95% CI |
|---|---:|---|
| `Delta_C,mech` (primary) | `-0.0053` | `[-0.0939, +0.0833]` |
| `Delta_C,repair` | `-0.0798` | `[-0.1743, +0.0147]` |
| `Delta_S,preserve` (manipulation integrity) | `-0.1702` | `[-0.2695, -0.0709]` |
| `Delta_S,generic` | `-0.0957` | `[-0.1580, -0.0335]` |

Frozen verdict: `MIXED_OR_INCONCLUSIVE`. The allowed reading:

> A matched-control follow-up did not isolate the mechanism underlying the capability shift.
> Explicit interface-contract reinforcement produced no capability recovery relative to a length-
> and structure-matched placebo, while both added-instruction conditions reduced SecurityPass
> relative to S.

> The placebo demonstrates that a substantial nonspecific added-instruction effect was present.

State the consequence in exactly this narrowed form:

> The matched placebo demonstrates a substantial nonspecific added-instruction effect on
> SecurityPass, so the S_controlled security loss cannot be interpreted as wholly
> contract-content-specific.

Do not estimate what share of the effect is nonspecific. That quantity is not identified by this
design and must not appear as a fraction, a percentage, or the words "mostly" or "largely".

### 6.4 Preserved construct distinction

Keep this distinction in the main text wherever the capability guardrail failure is mentioned:

> Study-3 capability-determination preservation is a specification-level construct; Study-4B
> CapabilityPass is a model-performance outcome. A change in the latter does not imply the former
> was validated incorrectly.

The two are measured on different objects by different instruments: blinded Definition-D coding of
specification text versus a model's pass rate on the frozen capability unit tests. The guardrail
failure therefore does not invalidate Study 3 or specification-level separability, and neither does
Study 4C.

### 6.5 Behavioural-line limitations

Add to the limitations in section 5: the behavioural line covers one model, one decoding policy, and
a subset selected on Study-3 separability; its single confirmatory contrast moved two endpoints at
once, so no isolated causal effect is identified; the mechanism experiment is exploratory, was
designed after the result it investigates, failed its own manipulation-integrity criterion, and left
an unexplained nonspecific added-instruction effect; and the behavioural experiment line is closed
without a fresh-sample estimate.

## 7. Discussion and implications

The defensible implication is methodological: benchmark designers should state whether security
tests are intended to measure compliance with disclosed requirements, spontaneous security
behaviour under underspecified requirements, or both. Where the intended construct requires the
second, model-visible oracle-determining text is a source of construct contamination. Definition-D
audits and constructively blinded specifications provide concrete diagnostics and repair artifacts.

Close by separating the unanswered behavioral question: Studies 1-3 do not estimate how much
model security-pass rates change when determination is removed, and the behavioural line in section
6 did not supply that estimate either. A fresh-sample study stopped at its yield gate; the
selected-subset follow-up moved two endpoints at once; and the mechanism experiment was
inconclusive. The isolated causal estimand therefore remains the highest-priority future test, and
it is still not necessary for the scoped measurement-validity claim established here.

## 8. Abstract and conclusion claim wording (draft)

The strongest wording the frozen evidence permits, for the abstract and the conclusion:

> Model-visible task specifications in SeCodePLT frequently determine the behaviour that the
> benchmark's security cases score: on a frozen outcome-blind random sample the case-weighted
> safety-case determination rate was 78.0% (task-cluster bootstrap 95% CI [70.4%, 84.9%]) under a
> prospectively frozen, quotation-grounded instrument whose labels were reproducible across
> independent blinded coding runs (cluster-aware kappa 0.804, 95% CI [0.708, 0.893]). For 47 of the
> 53 tasks in the realized measured-eligible confirmatory sample, that safety determination was
> constructively removed while every frozen capability case remained determined, giving a sample
> identification region of [47/53, 1]. A security score on such cases therefore cannot by itself
> distinguish compliance with a disclosed requirement from security behaviour supplied without one.
> In a behavioural follow-up on those 47 tasks, one frozen model's pass behaviour was strongly
> sensitive to the specification condition, substantially increasing SecurityPass and substantially
> reducing CapabilityPass; because both endpoints moved, that contrast does not identify the
> isolated causal effect of safety-determining information, and a matched-control follow-up did not
> isolate the mechanism. We therefore report a construct-validity threat with a demonstrated
> behavioural sensitivity, not an estimate of score inflation.

Every clause above is traceable to a frozen aggregate. Do not add a magnitude for score inflation,
a mechanism attribution, a cross-benchmark prevalence, or a claim that the model exploits the
determining text.

## Evidence anchors

- `docs/preregistration/2026-08-27_study1_prevalence_protocol.md`
- `docs/preregistration/2026-08-27_study1_execution/results_study1_prevalence.json`
- `docs/preregistration/2026-08-25_instrument_validation_protocol_v2.md`
- `docs/preregistration/2026-08-26_round2_interpretation_memo.md`
- `docs/preregistration/2026-08-28_study3_execution/FINAL_STUDY3_RESULT_SUMMARY.json`
- `docs/preregistration/2026-08-28_study3_execution/GAP6_REPAIR_RECORD.md`
- `docs/preregistration/2026-08-28_study3_execution/VO_STRUCT_EXECUTABILITY_AUDIT.md`
- `docs/preregistration/2026-08-28_cweval_replication/AMENDMENT_1_gap2_termination.md`
- `docs/preregistration/2026-09-07_study4_calibration_execution/CALIBRATION_HARD_STOP.json`
- `docs/preregistration/2026-09-08_study4b_execution/STUDY4B_CLOSURE.md`
- `docs/preregistration/2026-09-08_study4c_execution/STUDY4C_RESULTS.md`

