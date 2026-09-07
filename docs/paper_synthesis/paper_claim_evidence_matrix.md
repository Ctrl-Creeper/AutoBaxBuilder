# Paper Claim-Evidence-Estimand Matrix

> **Document status:** synthesis document, not preregistration. It summarizes frozen aggregate
> results, protocols, execution audits, and previously frozen exploratory/structural
> characterization. It creates no new estimand, coding, task-level analysis, subgroup, or outcome.
> Study 3's 53 confirmatory tasks remain closed to task-level inspection.

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

## Claim-evidence matrix

| Claim | Estimand | Evidence | Study | Status | Allowed wording | Forbidden stronger wording | Remaining gap |
|---|---|---|---|---|---|---|---|
| **C1. Security-oracle behavior can be determined by model-visible task specifications.** | Definition-D safety-case determination; formally `theta_saf` in the eligible SeCodePLT frame. | Original specifications yielded `theta_saf = 0.7805`, bootstrap 95% `[0.7040, 0.8492]`, measurement-disagreement `[0.7707, 0.7902]` [S1-R]. Definition D requires quoted textual obligation and excludes premises imported from outside the specification [S2-D]. | Study 1 + Study 2 | **SUPPORTED WITH SCOPE LIMITATION** | "In the eligible SeCodePLT frame, model-visible specifications frequently determine the behavior expected by security cases under Definition D." | "Security tests in general reveal their answers"; "the specification causes secure code"; "all security-oracle behavior is leaked." | Formal prevalence outside SeCodePLT; causal model behavior is not measured. |
| **C2. This phenomenon is common in SeCodePLT.** | Case-weighted `theta_saf` over the frozen 864-task eligible frame, estimated from the outcome-blind random sample of 90 tasks/205 safety cases ([S1-P], sections 1, 3, and 5). | Primary two-run mean `0.7805`, task-cluster bootstrap 95% `[0.7040, 0.8492]`; both/either measurement bounds `[0.7707, 0.7902]` [S1-R]. | Study 1 | **SUPPORTED** | "Specification determination was common in the prespecified eligible SeCodePLT population: the estimated safety-case rate was 78.0%." | "78% of all security benchmarks/tasks are leaked"; task-weighted or whole-benchmark claims; causal score-inflation claims. | None for the scoped case-weighted SeCodePLT prevalence claim; external generalization remains open. |
| **C3. Definition D can be measured reproducibly with blinded coding.** | Cross-run reliability of per-case J1/Definition-D labels on the prospective 90-task, 442-case validation sample. | Raw agreement `0.937`; cluster-aware kappa `0.804` `[0.708, 0.893]`; pooled kappa `0.869` descriptive; AC1 `0.877` `[0.808, 0.936]`; tie-break rates `18.8%`/`24.0%` ([S2-R]; [S2-I], section 1). Study 1 independently yielded raw agreement `0.975` and cluster-aware kappa `0.869` `[0.766, 0.968]` on original specifications [S1-R]. | Study 2, corroborated by Study 1 | **SUPPORTED WITH SCOPE LIMITATION** | "Frozen Definition D produced reproducible case labels across independent blinded coding runs on the studied SeCodePLT specification distributions." | "Validated by independent human coders"; "objective"; "error-free"; "J3/the full taxonomy was validated"; automatic transport to other oracle representations. | Human-coder validation, correlated-run error, and transport to other representation types. |
| **C4. Specification determination is not merely an unavoidable consequence of preserving ordinary functional requirements.** | `Sep(t)` under frozen constraint set C, operationalized constructively by DS: a concrete S-prime for which both blinded runs find all capability cases determined and no safety cases determined ([S3-P], sections 1, 2, 4, and 5). | 47 of 53 measured-eligible tasks met the conservative both-runs DS witness rule [S3-R]. | Study 3 | **SUPPORTED WITH SCOPE LIMITATION** | "For most measured-eligible tasks in the confirmatory sample, the security-case determination could be removed while retaining determination of every frozen capability case under Definition D." | "Security requirements can always be removed without functional loss"; preservation beyond the benchmark's frozen capability oracle; whole-frame or cross-benchmark claims. | Six tasks remain unresolved, not inseparable; external and procedure-free population prevalence remains partially identified. |
| **C5. For measured-eligible tasks, determination is frequently constructively removable while preserving capability determination.** | Procedure-inclusive `P(DS)` and partially identified `sigma` over the realized measured-eligible confirmatory sample. | `DS = 47/53 = 0.8868`; L0 sample identification region for `sigma` `[0.8868, 1]`; separate L1 `pi_DS` CP95 `[0.7697, 0.9573]`; L2 either-run share `0.9811` is sensitivity only ([S3-R]; [S3-A]). | Study 3 | **SUPPORTED WITH SCOPE LIMITATION** | "Constructive removal was demonstrated for 47/53 tasks in the realized measured-eligible sample; the sample identification region was `[47/53, 1]`." | "88.7% of SeCodePLT/all tasks are separable"; calling `[47/53,1]` a CI; classifying UR as separable or obstructed; substituting the L2 rate as confirmatory. | The estimand is conditional on measured eligibility and on constraint set C; VO incompleteness leaves the upper endpoint at 1. |
| **C6. Existing security benchmark scores may therefore conflate requirement-following with spontaneous security behavior.** | No direct behavioral-effect estimand. This is the construct-validity implication of `theta_saf` plus constructive removability, not an estimate of score inflation. | Study 1 shows that many security-case behaviors are already obliged by visible specifications [S1-R]; Study 3 shows that much of that determination is not required to retain the frozen capability contract [S3-R]. | Studies 1-3 | **SUPPORTED WITH SCOPE LIMITATION** | "When a security oracle's expected behavior is determined by the visible specification, passing that oracle does not by itself distinguish requirement-following from security behavior supplied without that requirement; this threatens construct interpretation." | "Scores are inflated by X"; "models pass because they copied the specification"; "removing determination lowers scores"; "the benchmark measures only instruction following." | A randomized model-behavior manipulation is needed to estimate whether, and by how much, models exploit determination. |
| **C7. This is a benchmark-design / construct-validity issue, not merely a defect in the original AutoBaxBuilder pipeline.** | No single confirmatory cross-benchmark prevalence estimand. Evidence combines formal SeCodePLT measurement with explicitly exploratory design-family comparison and CWEval oracle-structure audit. | Formal Studies 1 and 3 establish the issue on SeCodePLT ([S1-R]; [S3-R]). The frozen exploratory comparison found materially different A/B/C patterns across AutoBaxBuilder, upstream BaxBench, and CWEval and explicitly withdrew a family-wide overclaim ([XB-R], sections 1, 4, and 6). CWEval's pre-outcome failure shows representation-level design differences matter [CW-T]. | Studies 1-3 + frozen exploratory cross-benchmark characterization + CWEval GAP-2 | **SUPPORTED WITH SCOPE LIMITATION** | "The construct-validity problem is demonstrable in SeCodePLT and is naturally stated at the benchmark-design level; exploratory comparisons show that its prevalence and mechanism vary by design family." | "The same prevalence holds across benchmarks"; "all automated benchmarks have this flaw"; "CWEval formally replicates SeCodePLT"; causal attribution to automated generation. | A successful preregistered prevalence replication on a structurally compatible independent benchmark. |
| **C8. The measurement instrument does not automatically transport across benchmark oracle representations.** | Interface compatibility: whether the frozen case tuple `S, i, b` can be materialized mechanically without adding a semantic extraction layer. This is a structural gate, not a prevalence estimand. | In CWEval, 83% of security cases fell in representation classes lacking explicit parameter-level expected behavior; the preregistered replication terminated before outcomes ([CW-G2]; [CW-T]). | CWEval terminated replication | **SUPPORTED** | "A preregistered transport attempt showed that Definition D's frozen case interface did not automatically fit CWEval's oracle representation; the gate terminated the arm before outcome observation." | "Definition D cannot be used on CWEval"; "CWEval has high/low determination prevalence"; "replication failed because the effect was absent"; "class A is a confirmatory replication." | A separately developed, prospectively frozen semantic extraction/measurement interface would be required for CWEval prevalence. |
| **C9. Models actually exploit specification determination to obtain higher security scores.** | Counterfactual behavioral effect of removing determination from the visible specification while preserving capability, on model security-pass behavior. | None of Studies 1-3 runs a model-evaluation API or compares model pass behavior under original S versus S-prime; Study-3 protocol section 8 explicitly excludes model API evaluation [S3-P]. | Not measured; candidate Study 4 | **UNSUPPORTED / REQUIRES STUDY 4** | "The present studies identify and manipulate the measurement information structure, but do not estimate whether models use that information or how much it changes scores." | "Models exploit/copy the leaked answer"; "determination inflates scores"; "removing it reduces security-pass rates"; any magnitude or model-ranking claim. | A frozen causal model-evaluation study comparing behavior under original and determination-removed specifications while checking capability preservation. |
| **C10. Removing only SeCodePLT's `security_policy` field would leave much determination intact.** | Partially identified survival fraction among determined safety cases, based on one quoted witness per determined case. | Per-run lower bounds `0.8428` and `0.7205`, both-agree lower bound `0.7215`, all with upper bound `1`, under the modularity assumption ([S1-P], section 3; [S1-R], `security_policy_bounds`). | Study 1 | **SUPPORTED WITH SCOPE LIMITATION** | "The frozen quote-location analysis lower-bounds survival after policy-field deletion at 72.0%-84.3% per run (72.2% both-agree), under its modularity assumption." | "The non-policy fields uniquely cause determination"; "exactly X% survives"; "deleting the field changes model behavior by X%." | Point identification would require a separate blinded coding pass on policy-ablated specifications. |
| **C11. Study 2 validates J1 determination, not J3 or the full five-class taxonomy.** | Reliability/discrimination of the J1 determination judgment, contrasted with the J3 existential constructibility channel and derived taxonomy. | J1 showed prospective blinded run-level reliability; both runs answered J3 true on all 90 tasks, making two classes unreachable and zero J3 disagreement uninformative ([S2-I], sections 1-2). | Study 2 | **SUPPORTED** | "Study 2 validated the J1 measurement primitive; J3 supplied no discriminative validation and was retired in favor of evidence-producing Study-3 procedures." | "J3 was perfectly reliable"; "zero structural/inseparable cases were observed"; "the five-class taxonomy was validated." | A new prospectively validated constructibility instrument would be needed for any renewed J3/taxonomy claim; Study 3 answers a narrower question with witnesses and frozen sufficient certificates. |
| **C12. CWEval contributes structural portability evidence, not Definition-D prevalence.** | Oracle-representation compatibility and structural class counts; no CWEval Definition-D prevalence estimand was realized. | The arm terminated before packets, coding, or outcomes; only the frozen A/B/C oracle-representation counts are reportable ([CW-G2]; [CW-T]). | CWEval terminated replication | **SUPPORTED** | "CWEval contributes complementary oracle-representation characterization and a pre-outcome portability limitation, not a Definition-D prevalence estimate." | Any CWEval determination prevalence, formal prevalence replication result, or direct numerical prevalence comparison with SeCodePLT. | A newly preregistered measurement interface and fresh outcome-blind execution would be required to estimate CWEval prevalence. |

## Synthesis ruling encoded by the matrix

The frozen evidence directly supports a scoped measurement/construct-validity paper: Definition D
is reproducible across blinded coding runs on the studied material; specification determination is
common in the eligible SeCodePLT frame; and, conditional on measured eligibility, 47 of 53 tasks
have a conservative constructive witness showing that safety determination can be removed while
capability determination is retained. The evidence supports **a threat to score interpretation**.
It does not support the stronger behavioral claim that models exploit the determined information or
that benchmark scores are inflated by a measured amount. That stronger estimand is the clean
scientific role for a possible Study 4, not a prerequisite for stating the scoped construct-validity
result already established.

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
