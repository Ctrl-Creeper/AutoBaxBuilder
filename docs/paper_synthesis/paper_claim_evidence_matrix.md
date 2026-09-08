# Paper Claim-Evidence-Estimand Matrix

> **Document status:** synthesis document, not preregistration. It summarizes frozen aggregate
> results, protocols, execution audits, and previously frozen exploratory/structural
> characterization. It creates no new estimand, coding, task-level analysis, subgroup, or outcome.
> Study 3's 53 confirmatory tasks remain closed to task-level inspection.
>
> **Revision 2 (Study-4 behavioural line integrated).** Revision 1 was frozen at the Study-3
> cutoff, commit `1dda9cf5b3abdca8930900fdc8ac0d92234bb3b8`. Revision 2 adds the frozen Study-4B
> selected-subset behavioural follow-up and the Study-4C post-4B exploratory mechanism experiment
> as new claims C13-C16, and restates C6 and C9 in their light. **No Study-1/2/3 confirmatory
> claim is changed by this revision.** No frozen raw or results artifact of any study was rewritten;
> the revision reads only already frozen aggregates. Provenance and the revision-1 hashes are in
> `SYNTHESIS_REVISION_2_STUDY4.md`.

## Frozen headline evidence recovered

### Study 1 - original-spec determination prevalence

- **Population and estimand.** The population is the 864-task eligible SeCodePLT frame; the frozen
  90-task outcome-blind random sample contains 442 cases (237 capability, 205 safety). The headline
  estimand, `theta_saf`, is the case-weighted rate at which the shipped, model-visible original
  specification determines the benchmark's safety-case behavior under Definition D. `theta_cap`
  is the capability-case control. See [Study-1 protocol sections 1, 3, and 5][S1-P].
- **Prevalence.** `theta_saf = 0.7804878049`, with preregistered task-cluster bootstrap 95% interval
  `[0.7039776844, 0.8492082479]`; the two-run measurement-disagreement interval is
  `[0.7707317073, 0.7902439024]`. The control is `theta_cap = 0.6898734177`, bootstrap 95% interval
  `[0.5964491217, 0.7812700321]`, and measurement-disagreement interval
  `[0.6751054852, 0.7046413502]`. These are distinct from Study 3's identification region. See
  [Study-1 results `estimates` and `bootstrap.ci`][S1-R].
- **`security_policy` quote-location bounds.** Among determined safety cases, the lower bound on
  determination surviving deletion of the `security_policy` field is `0.8427672956` in Run 1 and
  `0.7204968944` in Run 2; the conservative both-runs-agree lower bound is `0.7215189873`. Every
  upper bound is `1`. These are single-witness quote-location bounds under the protocol's modularity
  assumption, not unique-source or causal-attribution estimates. See [Study-1 protocol section 3][S1-P]
  and [Study-1 results `security_policy_bounds`][S1-R].
- **Internal reliability.** Raw agreement is `0.9751131222`; task-cluster-aware kappa is
  `0.8688741722`, with task-cluster bootstrap 95% interval
  `[0.7657297389, 0.9684793523]`. This is agreement across independent blinded coding runs, not
  independent human coders. See [Study-1 results `reliability_internal` and
  `bootstrap.ci.kappa_cluster`][S1-R].

### Study 2 - measurement validation

- **Frozen primitive.** Definition D calls a case determined only when an implementer reading only
  the model-visible specification would be obliged to produce the expected behavior, with a
  locatable quoted sentence, at most one inference step, and no premise imported from outside the
  specification, including external security knowledge. See [instrument protocol v2 and frozen
  coder instructions][S2-D].
- **Prospective blinded reliability.** Across 90 prospectively selected tasks and 442 cases, two
  independent blinded coding runs achieved raw agreement `0.9366515837`; primary task-cluster-aware
  kappa `0.8041501516`, 95% interval `[0.7083045269, 0.8930127609]`; descriptive pooled kappa
  `0.8693660411`; and AC1 `0.8771295818`, 95% interval
  `[0.8082193896, 0.9361472439]`. Tie-break rates were `0.1877828054` and `0.2398190045`.
  See [Study-2 results][S2-R] and [interpretation memo section 1][S2-I].
- **Formal boundary.** J3 returned `exists = true` for all 90 tasks in both runs. Its zero
  disagreement is not reliability evidence: it supplied no discriminative support for
  constructibility, made the two J3-negative classes mechanically unreachable, and cannot validate
  the five-class taxonomy. Study 2 validates the J1 determination primitive, not that taxonomy.
  See [interpretation memo sections 1-2 and 5][S2-I].

### Study 3 - constructive separability

- **Conditional population.** A fresh 90-task draw from the frozen 764-task Study-3 frame entered
  the constructive analysis only when two fresh baseline runs both found at least one original-spec
  safety case determined. The **measured-eligibility rule** was fixed before outcomes; eligibility
  itself is a baseline-measurement outcome, and its realized confirmatory denominator is `m = 53`.
  See [Study-3 protocol section 3][S3-P] and [final result summary `population`][S3-R].
- **Constructive result.** `DS = 47`, `VO = 0`, and `UR = 6`, mutually exclusive and exhaustive,
  with no procedure-invalid candidate and no DS/VO overlap. The L0 **sample identification region**
  for the realized measured-eligible confirmatory sample is `[47/53, 1] =
  [0.8867924528, 1.0]`; it is not a confidence interval or whole-benchmark prevalence interval.
  See [Study-3 protocol sections 1-3 and 7][S3-P], [final result summary][S3-R], and the
  [independent 16/16 arithmetic/contract audit][S3-A].
- **Separate L1 and L2 layers.** The frozen separate Clopper-Pearson 95% endpoint intervals are
  `pi_DS: [0.7697100836, 0.9573036051]` and `pi_VO: [0, 0.0672345463]`. The preregistered L2
  measurement sensitivity reports an either-run DS share of `0.9811320755` versus the confirmatory
  both-runs share `0.8867924528`, with either-agree eligibility count `56` versus both-agree
  `m = 53`. L2 remains sensitivity only and is not a replacement confirmatory classification.
  See [final result summary `L1_separate_endpoint_sampling_intervals` and
  `L2_preregistered_measurement_sensitivity`][S3-R].
- **Execution disclosure.** Writer Run 1 reached `UNREPAIRABLE_FIRST_SUBMISSION` because two
  validator requirements were absent from the writer-visible contract. It is permanently retained
  and classified as `WRITER_INSTRUMENT_CONTRACT_FAILURE`, contributing nothing to DS/VO/UR. Writer
  Run 2 was a fresh, isolated, post-failure instrument-repaired replication on the same 53-task set,
  was accepted on its first submission, and became the sole formal constructive path. The repair
  decision saw mechanical issue codes/counts but no candidate substantive content. See [GAP-6 audit
  sections "Determination" and "Paper disclosure"][S3-G6A], [GAP-6 repair record sections "Run 1
  stands" and "Epistemic status of Writer Run 2"][S3-G6R], and [final execution
  provenance][S3-E].
- **VO limitation.** VO-DEFECT was permanently closed because its independent evidence-production
  and attestation procedure was insufficiently operationalized. Consequently, `VO = 0` means only
  that no obstruction was established by the valid frozen VO procedure; it does not mean no
  obstruction exists. See [final result summary `vo_interpretation`][S3-R].

### CWEval - terminated confirmatory replication

- The replication was preregistered against an independently developed benchmark, then terminated
  before packet construction, coding, or outcome observation. The frozen case interface assumed an
  explicit per-parameter expected behavior, but a census-level outcome-blind AST audit found that
  classes B/C contain 83% of the security-case frame and require semantic interpretation of test-body
  logic. See [CWEval protocol][CW-P], [GAP-2 report sections "The gap" and "Exposure
  ledger"][CW-G2], and [termination amendment][CW-T].
- The only reportable CWEval result is complementary oracle-representation characterization:
  class A `16 files / 32 security cases`, class B `39 / 44`, class C `59 / 110`; 11 files use
  non-literal parameter lists, and one file exposed a counting-method disagreement. No Definition-D
  prevalence was measured, class A was not substituted as a narrowed confirmatory sample, and no
  test-body semantic extractor was invented. See [GAP-2 report][CW-G2] and [termination amendment,
  binding clauses 1-5][CW-T].

### Study 4B - selected-subset behavioural follow-up

- **Population and design.** Not a fresh sample. The population is the frozen Study-3
  demonstrated-separable subset, `DS = 47` tasks, entered in full with no outcome-based selection.
  Each task was presented under the original determining specification `S` and the frozen
  underdetermined `S'`, 4 repeats per condition, 376 generations, one frozen local model and
  decoding policy, randomized condition-to-seed-arm assignment, ITT-style scoring in which
  non-runnable completions score zero. See [Study-4B closure record][S4B-C].
- **Frozen endpoints**, task-equal-weighted over 47 within-task differences with an exact two-sided
  sign-flip test matching the frozen randomization:

  | Endpoint | S | S' | Delta (S - S') | 95% CI | p |
  |---|---:|---:|---:|---:|---:|
  | SecurityPass (primary) | `0.8723` | `0.3670` | `+0.5053` | `[0.3741, 0.6365]` | `4.07e-09` |
  | CapabilityPass (guardrail) | `0.6011` | `0.9521` | `-0.3511` | `[-0.4683, -0.2338]` | `1.34e-07` |
  | Joint (secondary) | `0.5957` | `0.3298` | `+0.2660` | `[0.1051, 0.4268] `| `0.00234` |

- **Capability guardrail: FAILED.** The preregistered equivalence margin was +/-5 pp; the observed
  `Delta_C = -0.3511` with 95% CI `[-0.4683, -0.2338]` lies wholly outside it. This is recorded as a
  failure, not a warning and not a pass, and this synthesis does not soften it.
- **Identification consequence.** Because the guardrail failed, the two conditions differ
  behaviourally in both endpoints at once. The SecurityPass contrast therefore does **not** identify
  the isolated causal effect of removing safety-determining information while functional performance
  is held constant. See [Study-4B closure record, "Frozen interpretation"][S4B-C].
- **Boundary.** Study 4B is a selected-subset follow-up on tasks already demonstrated separable at
  the specification level. It is not a fresh-sample study, is not a replacement for the separately
  closed fresh Study 4 (`0/160` validated pairs, NO-GO before behavioral evaluation, [S4F]), and it
  does not generalize to SeCodePLT.

### Study 4C-EX - post-4B exploratory mechanism experiment

- **Epistemic grade.** Exploratory mechanism experiment **designed after Study 4B and after a
  20-task exploratory mechanism audit of Study-4B completions**. Its placebo authoring was
  negatively conditioned on that audit: candidate style rules were rejected when they could
  plausibly repair previously observed defect modes. It must therefore **not** be described as an
  outcome-naive independent confirmation. See [Study-4C results memo][S4C-R].
- **Design.** Same frozen 47 tasks, four arms - `S'`, `S`, `S_controlled` (`S` plus a constant
  interface-contract block at a single verified anchor), and `S_placebo` (`S` plus a
  length-, structure-, and salience-matched source-layout block with no interface, security, or
  adherence content) - 4 repeats each, 752 fresh generations, no Study-4B completion reused. 36/36
  pre-generation manipulation-validation gates passed before any generation.
- **Frozen four-arm rates**, task-equal-weighted, ITT-style:

  | Arm | SecurityPass | CapabilityPass |
  |---|---:|---:|
  | `S'` | `0.4096` | `0.9415` |
  | `S` | `0.9362` | `0.6383` |
  | `S_controlled` | `0.7660` | `0.5585` |
  | `S_placebo` | `0.8404` | `0.5638` |

- **Frozen contrasts**, paired within task, paired-t 95% CI, `n = 47`:

  | Contrast | Delta | 95% CI |
  |---|---:|---|
  | `Delta_C,mech = C(S_controlled) - C(S_placebo)` | `-0.0053` | `[-0.0939, +0.0833]` |
  | `Delta_C,repair = C(S_controlled) - C(S)` | `-0.0798` | `[-0.1743, +0.0147]` |
  | `Delta_S,preserve = Sec(S_controlled) - Sec(S)` | `-0.1702` | `[-0.2695, -0.0709]` |
  | `Delta_S,generic = Sec(S_placebo) - Sec(S)` | `-0.0957` | `[-0.1580, -0.0335]` |

- **Verdict: `MIXED_OR_INCONCLUSIVE`**, the pre-declared read-out for the observed pattern. The
  interface-contract reinforcement produced no capability recovery relative to the matched placebo
  or relative to `S`, so the content-specific capability-repair hypothesis is not supported. The
  security-preservation manipulation criterion **failed** (`Delta_S,preserve` lies wholly outside
  the -0.05 noninferiority margin), so the arm intended to isolate an intrinsic safety/function
  trade-off did not hold the safety manipulation fixed and that hypothesis is not established
  either. The matched placebo demonstrates a substantial nonspecific added-instruction effect on
  SecurityPass, so the `S_controlled` security loss cannot be interpreted as wholly
  contract-content-specific. **No share or proportion of the total effect is attributed to the
  nonspecific component**, and none is estimable from this design.
- **Binding wording amendment.** `STUDY4C_WORDING_AMENDMENT_1.md` (SHA-256
  `dc58cb1e4c6bda264b050431d0029b84a22b1ab9a7e05af2f7cf5fe4ffde0824`) narrows two phrases in the
  frozen results memo that attributed a share of the SecurityPass effect to the nonspecific
  component. The amendment rewrites no frozen artifact; it fixes the downstream wording used above
  and prohibits any share, fraction, percentage, or ratio for that component.
- **Line status.** The behavioural experiment line is **CLOSED**. No Study 4D, no block revision, no
  added repeats, no task-level or subgroup failure mining, no new mechanism taxonomy, and no
  post-hoc hypothesis search over the frozen 752 completions.

## Claim-evidence matrix

| Claim | Estimand | Evidence | Study | Status | Allowed wording | Forbidden stronger wording | Remaining gap |
|---|---|---|---|---|---|---|---|
| **C1. Security-oracle behavior can be determined by model-visible task specifications.** | Definition-D safety-case determination; formally `theta_saf` in the eligible SeCodePLT frame. | Original specifications yielded `theta_saf = 0.7805`, bootstrap 95% `[0.7040, 0.8492]`, measurement-disagreement `[0.7707, 0.7902]` [S1-R]. Definition D requires quoted textual obligation and excludes premises imported from outside the specification [S2-D]. | Study 1 + Study 2 | **SUPPORTED WITH SCOPE LIMITATION** | "In the eligible SeCodePLT frame, model-visible specifications frequently determine the behavior expected by security cases under Definition D." | "Security tests in general reveal their answers"; "the specification causes secure code"; "all security-oracle behavior is leaked." | Formal prevalence outside SeCodePLT; causal model behavior is not measured. |
| **C2. This phenomenon is common in SeCodePLT.** | Case-weighted `theta_saf` over the frozen 864-task eligible frame, estimated from the outcome-blind random sample of 90 tasks/205 safety cases ([S1-P], sections 1, 3, and 5). | Primary two-run mean `0.7805`, task-cluster bootstrap 95% `[0.7040, 0.8492]`; both/either measurement bounds `[0.7707, 0.7902]` [S1-R]. | Study 1 | **SUPPORTED** | "Specification determination was common in the prespecified eligible SeCodePLT population: the estimated safety-case rate was 78.0%." | "78% of all security benchmarks/tasks are leaked"; task-weighted or whole-benchmark claims; causal score-inflation claims. | None for the scoped case-weighted SeCodePLT prevalence claim; external generalization remains open. |
| **C3. Definition D can be measured reproducibly with blinded coding.** | Cross-run reliability of per-case J1/Definition-D labels on the prospective 90-task, 442-case validation sample. | Raw agreement `0.937`; cluster-aware kappa `0.804` `[0.708, 0.893]`; pooled kappa `0.869` descriptive; AC1 `0.877` `[0.808, 0.936]`; tie-break rates `18.8%`/`24.0%` ([S2-R]; [S2-I], section 1). Study 1 independently yielded raw agreement `0.975` and cluster-aware kappa `0.869` `[0.766, 0.968]` on original specifications [S1-R]. | Study 2, corroborated by Study 1 | **SUPPORTED WITH SCOPE LIMITATION** | "Frozen Definition D produced reproducible case labels across independent blinded coding runs on the studied SeCodePLT specification distributions." | "Validated by independent human coders"; "objective"; "error-free"; "J3/the full taxonomy was validated"; automatic transport to other oracle representations. | Human-coder validation, correlated-run error, and transport to other representation types. |
| **C4. Specification determination is not merely an unavoidable consequence of preserving ordinary functional requirements.** | `Sep(t)` under frozen constraint set C, operationalized constructively by DS: a concrete S-prime for which both blinded runs find all capability cases determined and no safety cases determined ([S3-P], sections 1, 2, 4, and 5). | 47 of 53 measured-eligible tasks met the conservative both-runs DS witness rule [S3-R]. | Study 3 | **SUPPORTED WITH SCOPE LIMITATION** | "For most measured-eligible tasks in the confirmatory sample, the security-case determination could be removed while retaining determination of every frozen capability case under Definition D." | "Security requirements can always be removed without functional loss"; preservation beyond the benchmark's frozen capability oracle; whole-frame or cross-benchmark claims. | Six tasks remain unresolved, not inseparable; external and procedure-free population prevalence remains partially identified. |
| **C5. For measured-eligible tasks, determination is frequently constructively removable while preserving capability determination.** | Procedure-inclusive `P(DS)` and partially identified `sigma` over the realized measured-eligible confirmatory sample. | `DS = 47/53 = 0.8868`; L0 sample identification region for `sigma` `[0.8868, 1]`; separate L1 `pi_DS` CP95 `[0.7697, 0.9573]`; L2 either-run share `0.9811` is sensitivity only ([S3-R]; [S3-A]). | Study 3 | **SUPPORTED WITH SCOPE LIMITATION** | "Constructive removal was demonstrated for 47/53 tasks in the realized measured-eligible sample; the sample identification region was `[47/53, 1]`." | "88.7% of SeCodePLT/all tasks are separable"; calling `[47/53,1]` a CI; classifying UR as separable or obstructed; substituting the L2 rate as confirmatory. | The estimand is conditional on measured eligibility and on constraint set C; VO incompleteness leaves the upper endpoint at 1. |
| **C6. Existing security benchmark scores may therefore conflate requirement-following with spontaneous security behaviour.** | No direct behavioral-effect estimand. This is the construct-validity implication of `theta_saf` plus constructive removability, not an estimate of score inflation. | Study 1 shows that many security-case behaviors are already obliged by visible specifications [S1-R]; Study 3 shows that much of that determination is not required to retain the frozen capability contract [S3-R]. Study 4B adds that on the 47 demonstrated-separable tasks one frozen model's pass behaviour was in fact strongly sensitive to the S versus S' condition, but with a simultaneous large capability change, so it supplies no score-inflation magnitude [S4B-C]. | Studies 1-3, with selected-subset behavioural corroboration from Study 4B | **SUPPORTED WITH SCOPE LIMITATION** | "When a security oracle's expected behavior is determined by the visible specification, passing that oracle does not by itself distinguish requirement-following from security behavior supplied without that requirement; this threatens construct interpretation." | "Scores are inflated by X"; "models pass because they copied the specification"; "removing determination lowers scores"; "the benchmark measures only instruction following"; "determination causes +50.5pp security inflation". | The magnitude of any score inflation remains unmeasured: the one available behavioural contrast is confounded by a simultaneous capability change and is restricted to a selected subset. |
| **C7. This is a benchmark-design / construct-validity issue, not merely a defect in the original AutoBaxBuilder pipeline.** | No single confirmatory cross-benchmark prevalence estimand. Evidence combines formal SeCodePLT measurement with explicitly exploratory design-family comparison and CWEval oracle-structure audit. | Formal Studies 1 and 3 establish the issue on SeCodePLT ([S1-R]; [S3-R]). The frozen exploratory comparison found materially different A/B/C patterns across AutoBaxBuilder, upstream BaxBench, and CWEval and explicitly withdrew a family-wide overclaim ([XB-R], sections 1, 4, and 6). CWEval's pre-outcome failure shows representation-level design differences matter [CW-T]. | Studies 1-3 + frozen exploratory cross-benchmark characterization + CWEval GAP-2 | **SUPPORTED WITH SCOPE LIMITATION** | "The construct-validity problem is demonstrable in SeCodePLT and is naturally stated at the benchmark-design level; exploratory comparisons show that its prevalence and mechanism vary by design family." | "The same prevalence holds across benchmarks"; "all automated benchmarks have this flaw"; "CWEval formally replicates SeCodePLT"; causal attribution to automated generation. | A successful preregistered prevalence replication on a structurally compatible independent benchmark. |
| **C8. The measurement instrument does not automatically transport across benchmark oracle representations.** | Interface compatibility: whether the frozen case tuple `S, i, b` can be materialized mechanically without adding a semantic extraction layer. This is a structural gate, not a prevalence estimand. | In CWEval, 83% of security cases fell in representation classes lacking explicit parameter-level expected behavior; the preregistered replication terminated before outcomes ([CW-G2]; [CW-T]). | CWEval terminated replication | **SUPPORTED** | "A preregistered transport attempt showed that Definition D's frozen case interface did not automatically fit CWEval's oracle representation; the gate terminated the arm before outcome observation." | "Definition D cannot be used on CWEval"; "CWEval has high/low determination prevalence"; "replication failed because the effect was absent"; "class A is a confirmatory replication." | A separately developed, prospectively frozen semantic extraction/measurement interface would be required for CWEval prevalence. |
| **C9. Models actually exploit specification determination to obtain higher security scores.** | Counterfactual behavioral effect of removing determination from the visible specification while preserving capability *behaviour*, on model security-pass behaviour. | Study 4B ran the manipulation on the frozen DS=47 subset and found SecurityPass `+0.5053` `[0.3741, 0.6365]` for S over S', but its preregistered capability guardrail **FAILED** (`-0.3511` `[-0.4683, -0.2338]`), so capability behaviour was not held constant and the estimand's identifying condition was not met [S4B-C]. Study 4C attempted to isolate the mechanism and returned `MIXED_OR_INCONCLUSIVE` [S4C-R]. | Study 4B (selected subset) + Study 4C (exploratory) | **UNSUPPORTED AS A CAUSAL CLAIM; BEHAVIOURAL SENSITIVITY DEMONSTRATED ON A SELECTED SUBSET** | "On the frozen 47 demonstrated-separable tasks, model behaviour was strongly sensitive to the S versus S' specification condition; because CapabilityPass also changed substantially, this contrast cannot be interpreted as the isolated causal effect of safety-determining information while functional performance is held constant." | "Models exploit/copy the leaked answer"; "determination inflates scores"; "determination causes +50.5pp security inflation"; "removing it reduces security-pass rates"; "capability was behaviorally held constant"; any magnitude, model-ranking, or SeCodePLT-wide generalization. | The isolated causal estimand is still unmeasured. It requires a manipulation that demonstrably holds capability *behaviour* constant on a fresh prospective sample; the behavioural experiment line is closed without having achieved that. |
| **C10. Removing only SeCodePLT's `security_policy` field would leave much determination intact.** | Partially identified survival fraction among determined safety cases, based on one quoted witness per determined case. | Per-run lower bounds `0.8428` and `0.7205`, both-agree lower bound `0.7215`, all with upper bound `1`, under the modularity assumption ([S1-P], section 3; [S1-R], `security_policy_bounds`). | Study 1 | **SUPPORTED WITH SCOPE LIMITATION** | "The frozen quote-location analysis lower-bounds survival after policy-field deletion at 72.0%-84.3% per run (72.2% both-agree), under its modularity assumption." | "The non-policy fields uniquely cause determination"; "exactly X% survives"; "deleting the field changes model behavior by X%." | Point identification would require a separate blinded coding pass on policy-ablated specifications. |
| **C11. Study 2 validates J1 determination, not J3 or the full five-class taxonomy.** | Reliability/discrimination of the J1 determination judgment, contrasted with the J3 existential constructibility channel and derived taxonomy. | J1 showed prospective blinded run-level reliability; both runs answered J3 true on all 90 tasks, making two classes unreachable and zero J3 disagreement uninformative ([S2-I], sections 1-2). | Study 2 | **SUPPORTED** | "Study 2 validated the J1 measurement primitive; J3 supplied no discriminative validation and was retired in favor of evidence-producing Study-3 procedures." | "J3 was perfectly reliable"; "zero structural/inseparable cases were observed"; "the five-class taxonomy was validated." | A new prospectively validated constructibility instrument would be needed for any renewed J3/taxonomy claim; Study 3 answers a narrower question with witnesses and frozen sufficient certificates. |
| **C12. CWEval contributes structural portability evidence, not Definition-D prevalence.** | Oracle-representation compatibility and structural class counts; no CWEval Definition-D prevalence estimand was realized. | The arm terminated before packets, coding, or outcomes; only the frozen A/B/C oracle-representation counts are reportable ([CW-G2]; [CW-T]). | CWEval terminated replication | **SUPPORTED** | "CWEval contributes complementary oracle-representation characterization and a pre-outcome portability limitation, not a Definition-D prevalence estimate." | Any CWEval determination prevalence, formal prevalence replication result, or direct numerical prevalence comparison with SeCodePLT. | A newly preregistered measurement interface and fresh outcome-blind execution would be required to estimate CWEval prevalence. |
| **C13. On a selected subset of tasks already shown separable at the specification level, one frozen model's pass behaviour was strongly sensitive to the specification condition.** | Paired within-task S-minus-S' contrasts on SecurityPass, CapabilityPass, and their conjunction over the frozen `DS = 47` subset, 4 repeats per condition, ITT-style scoring. | SecurityPass `0.8723` vs `0.3670`, `Delta = +0.5053` `[0.3741, 0.6365]`, `p = 4.07e-09`; CapabilityPass `0.6011` vs `0.9521`, `Delta = -0.3511` `[-0.4683, -0.2338]`, `p = 1.34e-07`; joint `Delta = +0.2660` `[0.1051, 0.4268]`. 376/376 generations, zero retries, zero hard stops [S4B-C]. | Study 4B | **SUPPORTED AS A SELECTED-SUBSET BEHAVIOURAL OBSERVATION, NOT AS AN ISOLATED CAUSAL EFFECT** | "On the frozen 47 demonstrated-separable tasks, model behavior was strongly sensitive to the S versus S' specification condition: the determining S condition substantially increased SecurityPass while substantially reducing CapabilityPass. Because CapabilityPass also changed substantially, the SecurityPass contrast cannot be interpreted as the isolated causal effect of safety-determining information while functional performance is held constant." | Any statement of the first sentence without the second; "S' changes the functional specification itself"; "determination causes +50.5pp security inflation"; "removing safety information alone causes the effect"; "the effect generalizes to SeCodePLT"; "Study 4B rescues or replaces the failed fresh Study 4". | The manipulation moved two endpoints at once; the subset was selected on Study-3 separability; one model, one decoding policy, one benchmark subset. |
| **C14. A matched-control follow-up did not isolate the mechanism underlying the capability shift.** | `Delta_C,mech = C(S_controlled) - C(S_placebo)` as primary, with `Delta_S,preserve = Sec(S_controlled) - Sec(S)` as the frozen manipulation-integrity criterion; four arms over the same 47 tasks, 4 repeats, 752 generations. | `Delta_C,mech = -0.0053` `[-0.0939, +0.0833]`; `Delta_C,repair = -0.0798` `[-0.1743, +0.0147]`; `Delta_S,preserve = -0.1702` `[-0.2695, -0.0709]`, failing the -0.05 noninferiority margin; `Delta_S,generic = -0.0957` `[-0.1580, -0.0335]`. Frozen verdict `MIXED_OR_INCONCLUSIVE` [S4C-R]. | Study 4C-EX (exploratory, designed after Study 4B) | **MIXED / INCONCLUSIVE** | "A matched-control follow-up did not isolate the mechanism underlying the capability shift. Explicit interface-contract reinforcement produced no capability recovery relative to a length- and structure-matched placebo, while both added-instruction conditions reduced SecurityPass relative to S." and "The placebo demonstrates that a substantial nonspecific added-instruction effect was present." | "Study 4C proves an intrinsic safety/function conflict"; "Study 4C proves implementation collateral damage"; "the security loss was mostly/entirely generic"; any share or proportion attributed to the nonspecific component; "Study 4C invalidates Study 3"; describing Study 4C as outcome-naive independent confirmation. | The mechanism is unresolved. The manipulation-integrity criterion failed, so this design cannot adjudicate between an intrinsic trade-off and an implementation-collateral-damage account, and the placebo's own substantive effect is itself unexplained. |
| **C15. The fresh-sample Study 4 is a separate, separately closed study.** | Fresh prospective pipeline yield: count of validated original/blinded specification pairs reaching behavioural evaluation. | `validated_n = 0` of 160 at the `transformation_yield` stage against a preregistered floor of 40 validated pairs; frozen decision `NO-GO` before any behavioural evaluation [S4F]. | Fresh Study 4 (calibration line) | **CLOSED NO-GO** | "A fresh-sample behavioural study was preregistered and stopped at its frozen pipeline-yield gate with 0/160 validated pairs, before any behavioural evaluation." | Presenting Study 4B or 4C as the fresh study, its continuation, or its replacement; reporting any behavioural result for the fresh sample; treating the NO-GO as evidence about model behaviour. | A fresh-sample behavioural estimate does not exist. Obtaining one requires a new constructive pipeline that clears the yield gate. |
| **C16. Study-3 capability preservation and Study-4B CapabilityPass are different constructs, so the guardrail failure does not impugn Study 3.** | Study 3: specification-level capability-case determination under Definition D, judged by blinded coding runs on the specification text. Study 4B: a model's empirical pass rate on the frozen capability unit tests. | Study 3 established, per DS task, that both blinded runs found every frozen capability case determined by the candidate `S'` [S3-R]. Study 4B measured one model's behaviour and found the capability pass rate lower under `S` than `S'` [S4B-C]. The two are measured on different objects by different instruments. | Studies 3 + 4B | **SUPPORTED (definitional distinction, preserved in every frozen closure record)** | "Study-3 capability-determination preservation is a specification-level construct; Study-4B CapabilityPass is a model-performance outcome. A change in the latter does not imply the former was validated incorrectly." | "Study 4B shows Study 3's capability preservation was wrong"; "the Study-4B capability failure invalidates specification-level separability"; "Study 4C invalidates Study 3"; silently merging the two under one word "capability". | Whether a specification that determines every capability case is also *easy* for a model to implement is a separate, unmeasured question. |

## Synthesis ruling encoded by the matrix

The frozen evidence directly supports a scoped measurement/construct-validity paper: Definition D
is reproducible across blinded coding runs on the studied material; specification determination is
common in the eligible SeCodePLT frame; and, conditional on measured eligibility, 47 of 53 tasks
have a conservative constructive witness showing that safety determination can be removed while
capability determination is retained. The evidence supports **a threat to score interpretation**.
It does not support the stronger behavioral claim that models exploit the determined information or
that benchmark scores are inflated by a measured amount.

**Revision 2 ruling on the behavioural line.** That stronger estimand was attempted and is still not
established. The fresh-sample study stopped at its pipeline-yield gate (`0/160`, NO-GO). The
selected-subset follow-up, Study 4B, did run: on the frozen 47 demonstrated-separable tasks one
model's behaviour was strongly sensitive to the specification condition, but its preregistered
capability guardrail failed, so the security contrast does not identify the isolated causal effect.
The post-4B exploratory mechanism experiment, Study 4C, did not resolve the mechanism: contract
reinforcement produced no capability recovery against a matched placebo, and the placebo itself
demonstrated a substantial nonspecific added-instruction effect on SecurityPass, so the controlled
arm's security loss cannot be read as wholly contract-content-specific. The behavioural experiment
line is closed.

The consequence for the paper is narrow and stable: the behavioural line **corroborates that the
specification condition matters to model behaviour on this subset** and **supplies no score-inflation
magnitude and no mechanism**. The scoped construct-validity result from Studies 1-3 stands exactly
as written in revision 1; it never depended on a behavioural estimate.

## Frozen source register

- <a id="S1-P"></a>**S1-P:** `docs/preregistration/2026-08-27_study1_prevalence_protocol.md`,
  sections 1, 3-5; frozen protocol SHA256
  `e4e0833079e68bbb6d4ae14787e38a98d8363518675c5890ec4c7d235f2c5c2b`.
- <a id="S1-R"></a>**S1-R:** `docs/preregistration/2026-08-27_study1_execution/results_study1_prevalence.json`,
  fields `n_tasks`, `n_cases`, `estimates`, `security_policy_bounds`, `reliability_internal`, and
  `bootstrap.ci`; SHA256 `dd13be72a3a4e750032d63cef96d3ab68ab1371e2c665d94a442ccc572e81cfe`.
- <a id="S2-D"></a>**S2-D:**
  `docs/preregistration/2026-08-25_instrument_validation_protocol_v2.md`, frozen v2 protocol
  SHA256 `4ca61b25973be20beec9cad085a7da503d600fdb7f427eb0e4251c3e02eb45da`, and
  `docs/preregistration/2026-08-26_round2_coder_packets/INSTRUCTIONS.md`, "Definition D - case
  determination", SHA256 `8113b8f29ecf98ab539493a54eb491fb11b966d01e093feba87bba719b44c177`.
- <a id="S2-R"></a>**S2-R:** `docs/preregistration/2026-08-26_round2_coder_packets/results_pre_adjudication.json`,
  aggregate reliability fields only; SHA256
  `17300bb140cdce38a1d2e38f06adef57775ce7a172f88b5acfef55c18a68427a`.
- <a id="S2-I"></a>**S2-I:** `docs/preregistration/2026-08-26_round2_interpretation_memo.md`,
  sections 1-2 and 5; SHA256
  `8aef7785f7a484279111eaf87e957dbffa242574a87eeb8d43543701a0339c3c`.
- <a id="S3-P"></a>**S3-P:** `docs/preregistration/2026-08-28_study3_constructive_separability_protocol.md`,
  sections 1-8; SHA256
  `548addbd9277dbe901b8e1e599fdf3a6d4ef97e286610dbecc40bf1f5f5f81d7`.
- <a id="S3-R"></a>**S3-R:** `docs/preregistration/2026-08-28_study3_execution/FINAL_STUDY3_RESULT_SUMMARY.json`,
  all aggregate sections; SHA256
  `affc40415afc43246d5c3036e36d1faa03a87fe9ade59b9952c34e375a2b6234`.
- <a id="S3-A"></a>**S3-A:** `docs/preregistration/2026-08-28_study3_execution/FINAL_STUDY3_ARITHMETIC_CONTRACT_AUDIT.json`,
  aggregate checks and observed aggregates only; SHA256
  `932743f0e4d585afb5d908fead737c27454563e9c1f365039bf92c3858d49859`.
- <a id="S3-E"></a>**S3-E:** `docs/preregistration/2026-08-28_study3_execution/FINAL_STUDY3_EXECUTION_PROVENANCE.json`,
  startup provenance, scorer execution, and VO-DEFECT disposition; SHA256
  `d38d8226d44936e40df38252c8c5ac5a63b8fe7273defd2720c20f41d789c0`.
- <a id="S3-G6A"></a>**S3-G6A:** `docs/preregistration/2026-08-28_study3_execution/GAP6_writer_instrument_contract_audit.md`,
  sections "Determination" and "Paper disclosure"; SHA256
  `a5ac01698990a04a6a9cd6d67dd6bc54d851f19de0a951172c91d7ea2f9a167c`.
- <a id="S3-G6R"></a>**S3-G6R:** `docs/preregistration/2026-08-28_study3_execution/GAP6_REPAIR_RECORD.md`,
  sections "Run 1 stands" and "Epistemic status of Writer Run 2"; SHA256
  `a52fc7ee3704ae265dfc37dac860487969c848f91f3a43ba5f4146d1675b8dca`.
- <a id="CW-P"></a>**CW-P:** `docs/preregistration/2026-08-28_cweval_replication/cweval_replication_protocol.md`,
  sections 1-5; SHA256
  `76d19809b161f13bd0af6ca1f197fd6bdc8859d03a955a8353727b0536c14ea7`.
- <a id="CW-G2"></a>**CW-G2:** `docs/preregistration/2026-08-28_cweval_replication/GAP2_case_unit_report.md`,
  sections "The gap", "Exposure ledger", and "What this blocks and what it does not"; SHA256
  `35443e03cf60cbe2dd83c78dab28c506ff65928e66ca61ae95654e3592699308`.
- <a id="CW-T"></a>**CW-T:** `docs/preregistration/2026-08-28_cweval_replication/AMENDMENT_1_gap2_termination.md`,
  "Ruling", "Fixed rationale", "Binding clauses", and "Effect on the paper"; SHA256
  `fec1aa081de064074c46ef113b4a2c1325970ae3c673e11d0fa1bc5911a30cdc`.
- <a id="S4B-C"></a>**S4B-C:** `docs/preregistration/2026-09-08_study4b_execution/STUDY4B_CLOSURE.md`,
  execution record, frozen endpoint table, capability guardrail, frozen interpretation, study
  boundaries, and preserved distinction; SHA256
  `769e1077d1e0f78b97235c0c4c0c7d5a36a9edfc17990b556dc934ed5d3f8162`. Aggregate endpoints also in
  `study4b_analysis_FROZEN.json`, SHA256
  `5fd37dd6ec0e35370090f8ecb42a955e0fb3e33872356e3b9ef085c42b546cdd`, and
  `STUDY4B_CLOSURE_MANIFEST.json`, SHA256
  `f1a330a1edd1fcadafd84e83c23f8dd166b4ebfedc3c51a468a064920c1eed88`.
- <a id="S4C-R"></a>**S4C-R:** `docs/preregistration/2026-09-08_study4c_execution/STUDY4C_RESULTS.md`,
  all sections; SHA256 `3a5f130d7dceab2e36b6f0c5ef1d7d98174132621144bc9f6bb721ee8e3c8b04`.
  Aggregate contrasts in `study4c_analysis_FROZEN.json`, SHA256
  `48778c565b521485f99e4a81f9a45d07a811f903d0f8aef28b76d84a41d47203`; closure record in
  `STUDY4C_CLOSURE_MANIFEST.json`, SHA256
  `5dfc0b08146803aa2a959c87fb5ba36eed04ae42ffaa4c91720253f7c719efa7`. Exploratory grade and the
  frozen placebo-authoring disclosure are stated in both.
- <a id="S4F"></a>**S4F:** `docs/preregistration/2026-09-07_study4_calibration_execution/CALIBRATION_HARD_STOP.json`,
  fields `decision`, `stage`, `reason`, `validated_n`; SHA256
  `4f274f2d5de96ff489010d6f158a6bbed7c3e13f57dc533a6e4cdd0834dc9a3f`. Frozen calibration protocol
  `CALIBRATION_FREEZE.md`, SHA256
  `1db83857369c78145bdb3ad317f1088d03cea0b29f8c951b5047e67929350f50`.
- <a id="XB-R"></a>**XB-R:** `docs/preregistration/2026-08-06_cross_benchmark/RESULT_CROSS_BENCHMARK_2026-08-06.md`,
  sections 1, 4, and 6; frozen exploratory characterization, SHA256
  `e2a227694d08fbcd81cf0db9817fb8cbe0caa760f3587cbac4f21e2160ecee7d`.

[S1-P]: #s1-p
[S1-R]: #s1-r
[S2-D]: #s2-d
[S2-R]: #s2-r
[S2-I]: #s2-i
[S3-P]: #s3-p
[S3-R]: #s3-r
[S3-A]: #s3-a
[S3-E]: #s3-e
[S3-G6A]: #s3-g6a
[S3-G6R]: #s3-g6r
[CW-P]: #cw-p
[CW-G2]: #cw-g2
[CW-T]: #cw-t
[XB-R]: #xb-r
[S4B-C]: #s4b-c
[S4C-R]: #s4c-r
[S4F]: #s4f
